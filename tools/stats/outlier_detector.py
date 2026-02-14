from typing import List

import numpy as np
import pandas as pd

from const_utils.stats_constansts import ImageStatsKeys


class OutlierDetector:
    """
    Service for statistical anomaly detection in datasets.

    This class provides methods to identify outliers using the 3-sigma rule
    (Standard Deviation). It can process features globally or per-class
    to ensure high accuracy in diverse datasets.
    """
    @staticmethod
    def mark_outliers(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Identifies and marks outliers for specified columns in a DataFrame.

        The method calculates iqr for each column.
        Values outside the range [q1 - 1.5 * iqr, q3 + 1.5 * iqr] are marked as 1.
        Columns starting with 'object_' are analyzed within each class group.
        Other columns are analyzed globally.

        Args:
            df (pd.DataFrame): The input feature matrix.
            columns (List[str]): List of numeric column names to analyze.

        Returns:
            pd.DataFrame: The original DataFrame with additional binary
                columns: 'outlier_<col_name>' and 'outlier_any'.
        """
        outlier_marker: str = "outlier_"
        if df.empty:
            return df

        df = df.copy()
        
        for col in columns:

            if col not in df.columns:
                continue

            outlier_column_name = f"{outlier_marker}{col}"

            class_group = df.groupby(ImageStatsKeys.class_name)[col]
            stats: pd.DataFrame = class_group.quantile([0.25, 0.75]).unstack()
            stats.columns = ["q1", "q3"]
            stats["iqr"] = stats["q3"] - stats["q1"]
            stats["upper_limit"] = stats["q3"] + 1.5 * stats["iqr"]
            stats["lower_limit"] = np.clip(stats["q1"] - 1.5 * stats["iqr"], a_min=0, a_max=None)

            upper_bounds = df[ImageStatsKeys.class_name].map(stats["upper_limit"])
            lower_bounds = df[ImageStatsKeys.class_name].map(stats["lower_limit"])
            df[outlier_column_name] = ((df[col] < lower_bounds) | (df[col] > upper_bounds)).astype("int8")

        outlier_cols = [col for col in df.columns if col. startswith(outlier_marker)]
        df["outlier_any"] = df[outlier_cols].any(axis=1).astype("int8")
        return df