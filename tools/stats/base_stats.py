from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Optional, Tuple, Dict, Union, List

import pandas as pd

from const_utils.default_values import AppSettings
from const_utils.stats_constansts import ImageStatsKeys
from logger.log_level_mapping import LevelMapping
from logger.logger import LoggerConfigurator
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.reader.voc import XMLReader
from tools.annotation_converter.reader.yolo import TXTReader
from tools.cache import CacheIO
from services.outlier_detector import OutlierDetector


class BaseStats(ABC):
    """
    Base stats class. Based on the source format, defines reader classes for processing data, defines default
        source annotation file suffixes
    """
    TASK: str = "stats"

    def __init__(
            self,
            source_format: str,
            log_level: str = LevelMapping.debug,
            log_path: Optional[Path] = None,
            settings: Optional[AppSettings] = None,
            cache_io: Optional[CacheIO] = None,
            img_path: Optional[Union[Path, str]] = None,
            extensions: Optional[Tuple[str, ...]] = None,
    ):
        """
        Initialize the stats class.

        Args:
            source_format (str): The format of source annotation (e.g., 'yolo').
            log_level: (str): The lowest logging level print to (e.g., 'debug').
            **kwargs (dict): Additional parameters like 'img_path' or 'labels_path'.
        """

        self.reader_mapping = {
            ".xml": XMLReader,
            ".txt": TXTReader
        }

        self.suffix_mapping = {
            "voc": ".xml",
            "yolo": ".txt"
        }

        self.settings = settings
        self.extensions = extensions
        self.img_path = img_path
        self.margin_threshold: int = self.settings.margin_threshold
        self.reader = self.reader_mapping.get(source_format, None)
        self.source_suffix = self.suffix_mapping.get(source_format)
        self.reader = self.reader_mapping[self.source_suffix]()
        self.cache_io = cache_io or CacheIO(self.settings)
        self.n_jobs = self.settings.n_jobs
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=log_level,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )

    @classmethod
    @abstractmethod
    def _init_worker(cls, images: Dict[str, str]) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _analyze_worker(
            file_path: Path,
            reader: BaseReader,
            margin_threshold: int = 5,
            class_mapping: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        pass

    def get_features(
            self,
            file_paths: Tuple[Path, ...],
            class_mapping: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:

        if not file_paths:
            return pd.DataFrame()

        cache_file = self.settings.cache_file_path / self.cache_io.generate_cache_filename(
            source_path=file_paths[0].parent,
            cache_name=self.settings.cache_name,
            format=self.source_suffix,
            task=self.TASK
        )

        df_cached = self.cache_io.load(cache_file)

        if df_cached.empty:
            df_final = pd.DataFrame()
            files_for_task = file_paths
        else:
            current_files_state = [
                {ImageStatsKeys.path: str(path.resolve()), ImageStatsKeys.mtime: path.stat().st_mtime}
                                   for path in file_paths
            ]
            df_disk = pd.DataFrame(current_files_state)
            merged = df_disk.merge(
                df_cached[[ImageStatsKeys.path, ImageStatsKeys.mtime]].drop_duplicates(),
                how="left",
                on=ImageStatsKeys.path,
                suffixes=["", "_old"]
            )

            to_update_mask = (
                    (merged[f"{ImageStatsKeys.mtime}_old"].isna()) |
                    (merged[ImageStatsKeys.mtime] != merged[f"{ImageStatsKeys.mtime}_old"]))
            files_for_task = [Path(p) for p in merged.loc[to_update_mask, ImageStatsKeys.path]]
            df_final = df_cached[df_cached[ImageStatsKeys.path].isin(df_disk[~to_update_mask][ImageStatsKeys.path])]

        if files_for_task:
            self.logger.info(f"Incremental update: processing {len(files_for_task)} files with {self.n_jobs} workers")
            images = {img.stem: str(img.resolve()) for img in self.img_path.iterdir() if
                      img.suffix.lower() in self.extensions}

            worker_func = partial(
                self._analyze_worker,
                reader=self.reader,
                margin_threshold=self.margin_threshold,
                class_mapping=class_mapping)

            with ProcessPoolExecutor(
                    max_workers=self.n_jobs,
                    initializer=self.__class__._init_worker,
                    initargs=(images,)
            ) as executor:
                results = list(executor.map(worker_func, files_for_task))

            new_data = [item for sublist in results for item in sublist]

            if new_data:
                df_new = pd.DataFrame(new_data)
                mtime_map = {str(path): path.stat().st_mtime for path in files_for_task}
                df_new[ImageStatsKeys.mtime] = df_new[ImageStatsKeys.path].map(mtime_map)
                df_final = pd.concat([df_final, df_new], ignore_index=True)
                df_final.reset_index(drop=True, inplace=True)

                numeric_cols = []
                for section in self.settings.img_dataset_report_schema:
                    if section["type"] == "numeric":
                        numeric_cols.extend(section["columns"])


                df_final = OutlierDetector.mark_outliers(df_final, numeric_cols)

            if files_for_task or (len(df_cached) != len(df_final)):
                self.cache_io.save(df_final, cache_file)

        return df_final
