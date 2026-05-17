from typing import List

import numpy as np
import pandas as pd


def get_feature_cols(df: pd.DataFrame, exclude_list: List[str], outlier_marker: str = "outlier") -> List[str]:
    """
    Selects relevant numeric columns for dimensionality reduction (UMAP).

    Filters out metadata (paths, timestamps), categorical data,
    and outlier flags to ensure UMAP focuses on geometric and
    content-based manifold analysis.

    Args:
        df (pd.DataFrame): The complete feature matrix.
        exclude_list (List[str]): A list of column names to exclude from the feature set.
        outlier_marker (str): A substring to identify outlier columns.

    Returns:
        List[str]: A list of numeric column names suitable for projection.
    """
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c not in exclude_list and not c.startswith(outlier_marker)]
    return feature_cols