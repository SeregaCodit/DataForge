from typing import Dict, Any

import pandas as pd

from const_utils.default_values import AppSettings
from tools.stats.dataset_reporter.base_reporter import BaseDatasetReporter


class ImageDatasetReporter(BaseDatasetReporter):

    def show_console_report(self, df: pd.DataFrame, target_format: str) -> None:
        total_objects = len(df)
        total_annota = df['image_name'].nunique()

