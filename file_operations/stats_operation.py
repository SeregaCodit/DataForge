import argparse
from pathlib import Path
from typing import Union, Dict, Tuple

import pandas as pd

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.stats.base_stats import BaseStats
from tools.stats.voc_stats import VOCStats
from tools.stats.yolo_stats import YoloStats


class StatsOperation(FileOperation):
    """
    This class show dataset information such as number of files object
    distribution, areas distribution etc. It can be used to get
    insights about the dataset before training a model.
    It can also be used to identify potential issues with the dataset,
    such as class or base features imbalance.
    """

    def __init__(self, settings: AppSettings, **kwargs):
        """Initializes the StatsOperation with settings and specific arguments."""
        super().__init__(settings, **kwargs)
        self.extensions = kwargs.get("ext", self.settings.extensions)
        self.img_path = kwargs.get('img_path')
        self.target_format: Union[str, None] = kwargs.get('target_format', self.settings.destination_type)
        self.stats_mapping: Dict[str, BaseStats.__subclasses__()] = {
            "yolo": YoloStats,
            "voc": VOCStats
        }
        self.stats_method: BaseStats = self.stats_mapping[self.target_format](
            settings=self.settings,
            source_format =self.target_format,
            img_path=self.img_path,
            extentions=self.extensions
        )

    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.destination_type,
            help=HelpStrings.destination_type,
        )
        parser.add_argument(
            Arguments.img_path,
            help=HelpStrings.img_path,
            default=None,
        )
        parser.add_argument(
            Arguments.n_jobs,
            help=HelpStrings.n_jobs,
            default=settings.n_jobs
        )
        parser.add_argument(
            Arguments.margin,
            help=HelpStrings.margin,
            default=settings.margin_threshold,
        )
        parser.add_argument(
            Arguments.report_path,
            help=HelpStrings.report_path,
            default=settings.report_path
        )


    def do_task(self):
        """
        This method should implement the logic to calculate and display the statistics of the dataset.
         It can include:
            - Counting the number of files in each class.
            - Calculating the distribution of object areas, positions etc.
            - Identifying any class imbalance issues.
            - Providing insights about the dataset that can help in model training and evaluation.
        """

        df = self.stats_method.get_features(file_paths=self.files_for_task)

        if df.empty:
            self.logger.warning(f"No annotations found in {self.src}")
            return

        self.logger.info(f"Found {len(self.files_for_task)} annotations in {self.src}")

        self._show_stats(df=df)

    @property
    def img_path(self) -> Path:
        """Path: Returns the directory path where images are stored."""
        return self._img_path

    @img_path.setter
    def img_path(self, img_path: Union[Path, str, None]) -> None:
        """
        Sets the directory for images and validates the input.

        Args:
        img_path (Union[Path, str, None]): Path to annotated images folder.
            If None, it uses YOLO annotations same path .

        Raises:
        TypeError: If the provided path is not a string or Path object.
        """
        if isinstance(img_path, Path):
            self._img_path = img_path
        elif isinstance(img_path, str):
            self._img_path = Path(img_path)
        elif img_path is None:
            self._img_path = self.source_directory
            self.logger.warning(f"Dataset images path is not defined. Set same annotations path: {self.source_directory}")
        else:
            msg = f"img_path must be Path or str, not {type(img_path)}"
            self.logger.error(msg)
            raise TypeError(msg)

    @property
    def extensions(self) -> Tuple[str, ...]:
        """Tuple[str, ...]: Returns the supported image file extensions."""
        return self._extensions

    @extensions.setter
    def extensions(self, value: Tuple[str, ...]) -> None:
        """
        Sets the valid image extensions for the converter.

        Args:
            value (Tuple[str, ...]): A tuple of extension strings (e.g., ('.jpg',)).

        Raises:
            TypeError: If the input cannot be converted into a tuple.
        """
        if isinstance(value, tuple):
            self._extensions = value
        else:
            try:
                self._extensions = tuple(value)
            except TypeError as e:
                msg = f"extensions must be convertable into tuple, got {type(value)}"
                self.logger.error(msg)
                raise TypeError(msg)
    def _show_stats(self, df: pd.DataFrame) -> None:
        """
        Displays a technical dataset report using DataFrame keys directly.
        """
        total_images = df['path'].nunique()
        total_objects = len(df)

        if total_objects == 0:
            self.logger.warning("Dataset is empty. Nothing to analyze.")
            return

        # Обчислюємо щільність об'єктів
        objs_per_img = df.groupby('path').size()
        avg_density = objs_per_img.mean()
        std_density = objs_per_img.std()

        report = [
            "\n" + "=" * 65,
            " DATASET INTELLIGENCE REPORT: " + self.target_format.upper(),
            "=" * 65,
            f"total_images:      {total_images}",
            f"total_objects:     {total_objects}",
            f"objs_per_image:    {avg_density:.2f} ± {std_density:.2f}",
            "-" * 65,
            " CLASS_NAME DISTRIBUTION:",
        ]

        # 1. Розподіл класів
        class_counts = df['class_name'].value_counts()
        for name, count in class_counts.items():
            share = (count / total_objects) * 100
            report.append(f"  - {name:<18}: {count:>8} ({share:>6.2f}%)")

        # 2. Геометрична статистика
        report.append("\n OBJECT_AREA STATISTICS (Pixels):")
        area_stats = df['object_area']
        report.append(f"  - median:           {int(area_stats.median())}")
        report.append(f"  - mean_std:         {int(area_stats.mean())} ± {int(area_stats.std())}")
        report.append(f"  - min_max_range:    {int(area_stats.min())} to {int(area_stats.max())}")

        # 3. Просторова аналітика (Автоматичний вивід ключів)
        report.append("\n SPATIAL DISTRIBUTION (Flags sum):")
        spatial_keys = [
            'object_in_center', 'object_in_top_side', 'object_in_bottom_side',
            'object_in_left_side', 'object_in_right_side'
        ]
        for key in spatial_keys:
            if key in df.columns:
                count = df[key].sum()
                share = (count / total_objects) * 100
                report.append(f"  - {key:<22}: {count:>8} ({share:>6.1f}%)")

        # 4. Розподіл обрізаних країв (Автоматичний вивід ключів)
        report.append("\n TRUNCATED BORDERS (Flags sum):")
        trunc_keys = [
            'truncated_top', 'truncated_bottom', 'truncated_left', 'truncated_right'
        ]
        for key in trunc_keys:
            if key in df.columns:
                count = df[key].sum()
                share = (count / total_objects) * 100
                report.append(f"  - {key:<22}: {count:>8} ({share:>6.1f}%)")

        # 5. Цілісність та викиди
        report.append("\n DATA_INTEGRITY & OUTLIERS:")

        # Правило 3-х сигм
        upper_limit = area_stats.mean() + 3 * area_stats.std()
        outliers_count = (area_stats > upper_limit).sum()

        # Об'єкти, що мають хоча б один прапорець truncated
        trunc_any = df[trunc_keys].any(axis=1).sum()

        report.append(f"  - any_truncated_total : {trunc_any:>8} ({(trunc_any / total_objects) * 100:>6.1f}%)")
        report.append(f"  - potential_outliers  : {outliers_count:>8} [area > {int(upper_limit)} px]")
        report.append(f"  - has_neighbors_count : {df[df['has_neighbors'] == 1]['path'].nunique():>8} images")

        report.append("=" * 65 + "\n")

        self.logger.info("\n".join(report))