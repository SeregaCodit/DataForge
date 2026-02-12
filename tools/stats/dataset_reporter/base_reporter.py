from abc import ABC
from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd
from jinja2.nodes import List

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator


class BaseDatasetReporter(ABC):
    def __init__(self, settings: AppSettings, **kwargs):
        self.settings: AppSettings = settings
        self.log_path: Path = kwargs.get("log_path", settings.log_path)
        log_file = kwargs.get("log_file", self.__class__.__name__)
        log_level = kwargs.get("log_level", settings.log_level)
        self.schema = self.settings.img_dataset_report_schema
        self.report_path = self.settings.report_path
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=log_level,
            log_path=Path(self.log_path) / f"{log_file}.log" if self.log_path else None
        )

    def render_section(self, df: pd.DataFrame, section_name: str):
        pass

    @property
    def report_path(self) -> Path:
        return self._report_path

    @report_path.setter
    def report_path(self, value: Union[Path, str]):
        if not isinstance(value, Path):
            try:
                value = Path(value)
            except TypeError:
                msg = f"Invalid type for report_path: expected Path or str, got {type(value)}"
                self.logger.error(msg)
                raise TypeError(msg)
        self._report_path = value