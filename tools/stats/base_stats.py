from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Optional, Tuple, Dict, Union, List

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from umap import UMAP

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
    Abstract base class for dataset feature extraction and analysis.

    This class defines the interface for reading different annotation formats
    (YOLO, VOC) and provides a high-performance pipeline for feature extraction.
    It supports incremental caching, multi-process execution, and UMAP
    dimensionality reduction for visual manifold analysis.
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
        Initializes the analytical engine with specific formats and IO tools.

        Args:
            source_format (str): Annotation format identifier (e.g., 'yolo', 'voc').
            log_level (str): Minimum logging level. Defaults to 'INFO'.
            log_path (Optional[Path]): Directory for log files.
            settings (Optional[AppSettings]): Application-wide settings.
            cache_io (Optional[CacheIO]): Component for Parquet-based caching.
            img_path (Optional[Union[Path, str]]): Path to the dataset images.
            extensions (Optional[Tuple[str, ...]]): Valid image file extensions.
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
        """
        Initializes a static worker with shared data for multiprocessing.

        Args:
            images (Dict[str, str]): A dictionary mapping image stems to absolute paths.
        """
        pass

    @staticmethod
    @abstractmethod
    def _analyze_worker(
            file_path: Path,
            reader: BaseReader,
            margin_threshold: int = 5,
            class_mapping: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """
        Processes a single annotation file to extract features.

        Args:
            file_path (Path): Path to the annotation file.
            reader (BaseReader): Annotation reader instance.
            margin_threshold (int): Pixel margin for boundary analysis.
            class_mapping (Optional[Dict[str, str]]): Map of class IDs to names.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, where each dict represents
                features of one detected object.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_umap_features(df: pd.DataFrame) -> List[str]:
        """
        Defines the list of numeric features to be used for UMAP projection.

        Args:
            df (pd.DataFrame): The extracted feature matrix.

        Returns:
            List[str]: List of column names for dimensionality reduction.
        """
        pass

    def get_features(
            self,
            file_paths: Tuple[Path, ...],
            class_mapping: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Orchestrates feature extraction using incremental caching and parallel processing.

        This method checks the modification time (mtime) of each file. It only
        processes new or changed files, significantly reducing execution time
        for large datasets.

        Args:
            file_paths (Tuple[Path, ...]): List of annotation files to process.
            class_mapping (Optional[Dict[str, str]]): Class ID to name mapping.

        Returns:
            pd.DataFrame: A complete feature matrix including UMAP coordinates
                and outlier flags.
        """
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
                self.logger.info(f"computing UMAP coordinates for the entire dataset with {self.n_jobs} workers")
                features = self.get_umap_features(df_final)
                df_final = self.compute_umap_coords(df=df_final, features=features)
            if files_for_task or (len(df_cached) != len(df_final)):
                self.cache_io.save(df_final, cache_file)
                self.logger.info(f"Cache updated at {cache_file} with {len(df_final)} records")

        return df_final


    def compute_umap_coords(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """
        Performs dimensionality reduction to visualize the dataset manifold.

        Uses StandardScaler for normalization and UMAP to project high-dimensional
        features into a 2D space. Results are saved as 'umap_x' and 'umap_y' columns.

        Args:
            df (pd.DataFrame): The feature matrix.
            features (List[str]): Columns to be used for reduction.

        Returns:
            pd.DataFrame: DataFrame with added UMAP coordinates.
        """

        x_data = df[features].fillna(0)
        x_data = x_data.loc[:, x_data.var() > 0]

        if x_data.shape[1] < 2:
            return df

        x_scaled = StandardScaler().fit_transform(x_data)
        n_neighbors = int(np.clip(len(x_data) * 0.1, a_min=15, a_max=50))
        reducer = UMAP(n_neighbors=n_neighbors, min_dist=0.1, n_components=2, n_jobs=self.n_jobs)
        embedding = reducer.fit_transform(x_scaled)

        df['umap_x'] = embedding[:, 0]
        df['umap_y'] = embedding[:, 1]

        return df

    def set_class_mapping(self, file_paths: Tuple[Path]) -> Dict[str, str]:
        """
        Identifies and loads the class name mapping from a definition file.

        Specifically looks for 'classes.txt' in the source directory (YOLO standard).

        Args:
            file_paths (Tuple[Path]): List of files in the source directory.

        Returns:
            Dict[str, str]: A dictionary mapping class IDs to human-readable names.
        """
        classes_file = next((path for path in file_paths if path.name == "classes.txt"), None)
        if classes_file is None:
            self.logger.warning(
                f"No classes file found at {file_paths[0].parent}, class names will be taken from annotations as is"
            )

        classes_mapping = self.reader.read(classes_file)
        self.logger.info(f"Class mapping loaded with {len(classes_mapping)} entries")
        classes_mapping = {value: key for key, value in classes_mapping.items()}
        return classes_mapping

