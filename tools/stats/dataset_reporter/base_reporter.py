from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List

import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator


class BaseDatasetReporter(ABC):
    """
    Abstract base class for dataset reporting and visualization.

    This class provides a shared interface and utility methods for creating
    technical reports. It handles console output formatting, shared logging,
    and calculation of dataset health metrics such as 'sweet spots'
    (statistical ranges free of outliers).
    """
    line: str = "=" * 75

    def __init__(self, settings: AppSettings):
        """
        Initializes the reporter with global settings and logging.

        Args:
            settings (AppSettings): Global configuration containing paths,
                log levels, and report schemas.
        """
        self.settings: AppSettings = settings
        self.log_path: Path = settings.log_path
        log_level = settings.log_level
        self.schema = self.settings.img_dataset_report_schema
        self.report_path = self.settings.report_path
        self.report_path.mkdir(parents=True, exist_ok=True)

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=log_level,
            log_path=Path(self.log_path) / f"{self.__class__.__name__}.log" if self.log_path else None
        )

    @abstractmethod
    def show_console_report(self, df: pd.DataFrame, target_format: str) -> None:
        """
        Prints a detailed technical report to the console.

        Args:
            df (pd.DataFrame): The feature matrix of the dataset.
            target_format (str): Annotation format identifier (e.g., 'yolo').
        """
        pass

    @abstractmethod
    def generate_visual_report(self, df: pd.DataFrame, destination: Union[Path, str, PdfPages], features: List[str]) -> None:
        """
        Generates visual analytics (plots, heatmaps, manifolds).

        Args:
            df (pd.DataFrame): The feature matrix of the dataset.
            destination (Union[Path, str, PdfPages]): Output target for the visual assets.
            features (List[str]): Numeric columns used for visual correlation and manifold analysis.
        """
        pass


    def _render_section(self, df: Union[pd.DataFrame, pd.Series], section: dict, total_objects: int) -> List[str]:
        """
        Formats a specific data category (numeric or binary) for the report text.

        This method calculates statistical summaries (mean, median, std) for numeric
        columns and identifies 'sweet spots' using the Interquartile Range (IQR) method.
        For binary columns, it calculates frequency and percentage.

        Args:
            df (Union[pd.DataFrame, pd.Series]): Data slice for a specific class or dataset.
            section (dict): Configuration dictionary defining the title, columns, and type.
            total_objects (int): Total count used for calculating percentages in binary sections.

        Returns:
            List[str]: A list of formatted strings ready for console or text file output.
        """
        title = section["title"]
        cols = [col for col in section["columns"] if col in df.columns]

        if not cols:
            self.logger.warning(f"No valid columns found for section '{title}' in the DataFrame.")
            return []

        lines = [f"\n [{title}]"]

        if section["type"] == "numeric":
            stats = df[cols].describe().T
            for col in cols:
                row = stats.loc[col]
                outlier_col = f"outlier_{col}"
                outliers_count = df[outlier_col].sum()

                iqr = row["75%"] - row["25%"]
                min_limit = np.clip(row["25%"] - 1.5 * iqr, a_min=0, a_max=None)
                max_limit = row["75%"] + 1.5 * iqr

                lines.append(
                    f"  - {col:<25}:"
                    f" med {row['50%']:>10.2f} |"
                    f" avg {row['mean']:>10.2f}, std {row['std']:<10.2f} |"
                    f" min {row['min']:>10.2f}, max {row['max']:>10.2f}  |"
                    f" outliers: {int(outliers_count):<4} |"
                    f"{min_limit:10.2f} < sweet spot < {max_limit:10.2f} "
                )
        elif section["type"] == "binary":
            sums = df[cols].sum()
            for col in cols:
                count = int(sums[col])
                share = (count / total_objects) * 100
                lines.append(f"  - {col:<25}: {count:>10} ({share:>6.1f}%)")
        else:
            self.logger.warning(f"Unknown section type '{section['type']}' for section '{title}'. Skipping.")

        return lines


    @property
    def report_path(self) -> Path:
        """Path: The directory where generated reports are stored."""
        return self._report_path

    @report_path.setter
    def report_path(self, value: Union[Path, str]):
        """
         Sets and validates the reporting output directory.

         Args:
             value (Union[Path, str]): Path to the report folder.

         Raises:
             TypeError: If the value is not a string or a Path object.
         """
        if not isinstance(value, Path):
            try:
                value = Path(value)
            except TypeError:
                msg = f"Invalid type for report_path: expected Path or str, got {type(value)}"
                self.logger.error(msg)
                raise TypeError(msg)
        self._report_path = value