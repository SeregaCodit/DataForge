import argparse
import os
from pathlib import Path
from typing import Union, Dict, Tuple

import numpy as np
import pandas as pd

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from services.folder_namer import FolderNamer
from tools.stats.base_stats import BaseStats
from tools.stats.dataset_reporter.base_reporter import BaseDatasetReporter
from tools.stats.dataset_reporter.image_reporter import ImageDatasetReporter
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

        self.reporter_mapping: Dict[str, Union[BaseDatasetReporter.__subclasses__()]] = {
            "image": ImageDatasetReporter
        }

        self.reporter: BaseDatasetReporter = self.reporter_mapping.get(self.settings.datatype)(
            settings=self.settings
        )
        self.stats_method: BaseStats = self.stats_mapping[self.target_format](
            settings=self.settings,
            source_format =self.target_format,
            img_path=self.img_path,
            extensions=self.extensions
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

        self.reporter.show_console_report(df=df, target_format=self.target_format)

        report_path = FolderNamer.next_name(src=self.settings.report_path)
        self.reporter.generate_visual_report(df=df, destination=report_path)

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