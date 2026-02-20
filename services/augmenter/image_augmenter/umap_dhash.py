from typing import List
from sklearn.neighbors import NearestNeighbors, KNeighborsRegressor

import numpy as np
import pandas as pd

from const_utils.default_values import AppSettings
from services.augmenter.image_augmenter.image_augmenter import ImageAugmenter
from services.feature_cols import get_feature_cols
from tools.stats.base_stats import BaseStats
from tools.stats.voc_stats import VOCStats


class UmapDhashAugmenter(ImageAugmenter):
    def __init__(self, settings: AppSettings):
        super().__init__(settings)
        self.consensus_hash = None

    def get_data_gaps(self, df: pd.DataFrame, bins: int) -> pd.DataFrame:
        self.logger.info(f"Getting data gaps for class {df['class_name'].unique()[0]}")

        x_med = df["umap_x"].median()
        y_med = df["umap_y"].median()

        x_iqr = df["umap_x"].quantile(0.75) - df["umap_x"].quantile(0.25)
        y_iqr = df["umap_y"].quantile(0.75) - df["umap_y"].quantile(0.25)

        x_lower_bound = x_med - 1.5 * x_iqr
        x_upper_bound = x_med + 1.5 * x_iqr
        y_lower_bound = y_med - 1.5 * y_iqr
        y_upper_bound = y_med + 1.5 * y_iqr

        counts, x_edges, y_edges = np.histogram2d(
            df["umap_x"], df["umap_y"],
            bins=bins,
            range=[[x_lower_bound, x_upper_bound], [y_lower_bound, y_upper_bound]]
        )

        average_density = counts[counts > 0].mean()
        gap_threshold = average_density * 0.1

        gap_indices = np.argwhere(counts < gap_threshold)

        x_step = (x_upper_bound - x_lower_bound) / bins
        y_step = (y_upper_bound - y_lower_bound) / bins

        gap_cords = []
        for x_idx, y_idx in gap_indices:
            gap_x = x_lower_bound + (x_idx * 0.5) * x_step
            gap_y = y_lower_bound + (y_idx * 0.5) * y_step
            gap_cords.append((gap_x, gap_y))

        gap_cords = np.array(gap_cords)

        nn = NearestNeighbors(n_neighbors=1).fit(df[["umap_x", "umap_y"]].values)
        distances, _ = nn.kneighbors(gap_cords)

        max_dist = x_step * 2
        valid_gaps_mask = distances.flatten() < max_dist
        target_gaps = gap_cords[valid_gaps_mask]

        self.logger.info(f"Filtered {len(gap_indices)} gaps down to {len(target_gaps)} boundary zones.")


        feature_cols = get_feature_cols(df=df, exclude_list=self.settings.image_df_exclude_columns)
        model = KNeighborsRegressor(n_neighbors=5, weights='distance')
        model.fit(df[["umap_x", "umap_y"]].values, df[feature_cols].values)

        gap_recipes = model.predict(target_gaps)

        gaps_df = pd.DataFrame(target_gaps, columns=["target_umap_x", "target_umap_y"])
        gaps_df[feature_cols] = gap_recipes
        return gaps_df



    def select_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.get_unique_objects(df=df)
        df["is_candidate"] = False

        for class_name in df["class_name"].unique():
            mask = df["class_name"] == class_name
            class_scores = df.loc[mask, "uniqueness_score"]

            q1 = class_scores.quantile(0.25)
            q3 = class_scores.quantile(0.75)
            iqr = q3 - q1

            upper_bound = q3 + 1.5 * iqr

            df.loc[mask, "is_candidate"] = class_scores > upper_bound

        total_candidates = df["is_candidate"].sum()
        self.logger.info(f"Selected {total_candidates} candidates")
        return df





    def generate_samples(self, df: pd.DataFrame, gaps: List, donors: pd.DataFrame, n_samples: int) -> pd.DataFrame:
        pass
