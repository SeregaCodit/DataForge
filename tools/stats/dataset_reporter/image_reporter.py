from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from const_utils.stats_constansts import ImageStatsKeys
from tools.stats.dataset_reporter.base_reporter import BaseDatasetReporter
from services.plotter import StatsPlotter


class ImageDatasetReporter(BaseDatasetReporter):
    def generate_visual_report(self, df: pd.DataFrame, destination: Union[Path, PdfPages]):
        self.logger.info("Starting visual analytics pipeline...")
        # TODO split this function to multiple srp functions
        class_col = ImageStatsKeys.class_name

        # 1. Підготовка списку числових фіч
        exclude = {
            class_col,
            ImageStatsKeys.path,
            ImageStatsKeys.mtime,
            ImageStatsKeys.has_neighbors,
            ImageStatsKeys.full_size,
            ImageStatsKeys.objects_count
        }

        numeric_features = [c for c in df.select_dtypes(include=[np.number]).columns
                            if c not in exclude and not c.startswith('outlier')]

        # --- ГРАФІК 1: Розподіл класів ---
        StatsPlotter.plot_class_distribution(df, destination)

        # --- ГРАФІК 2: Геометричний аналіз (Boxplots) ---
        StatsPlotter.plot_geometry_analysis(df, destination)

        # --- ГРАФІК 3: Аналіз зміщення (Class vs Features) ---
        # Створюємо One-Hot Encoding для класів
        class_dummies = pd.get_dummies(df[class_col], prefix='class').astype(int)
        df_combined = pd.concat([df[numeric_features], class_dummies], axis=1)
        full_corr = df_combined.corr()

        class_cols = [c for c in full_corr.columns if c.startswith('class_')]
        bias_matrix = full_corr.loc[class_cols, numeric_features]

        StatsPlotter.plot_correlation_matrix(
            bias_matrix, "Dataset Bias: Classes vs Features",
            destination, "corr_bias.png", annot_size=7
        )

        # --- ГРАФІКИ 4: Теплокарти та Внутрішня кореляція (Per Class) ---
        all_class_corrs = df.groupby(class_col)[numeric_features].corr()

        for name in sorted(df[class_col].unique()):
            class_df = df[df[ImageStatsKeys.class_name] == name]

            # Теплокарта 3х3
            grid = [
                [class_df['object_in_left_top'].sum(), class_df['object_in_top_side'].sum(),
                 class_df['object_in_right_top'].sum()],
                [class_df['object_in_left_side'].sum(), class_df['object_in_center'].sum(),
                 class_df['object_in_right_side'].sum()],
                [class_df['object_in_left_bottom'].sum(), class_df['object_in_bottom_side'].sum(),
                 class_df['object_in_right_bottom'].sum()]
            ]
            StatsPlotter.plot_spatial_heatmap(grid, f"Spatial Density: {name.upper()}", destination, f"heat_{name}.png")

            # Внутрішня кореляція фіч
            c_matrix = all_class_corrs.loc[name].dropna(how='all', axis=0).dropna(how='all', axis=1)
            if c_matrix.shape[0] >= 2:
                StatsPlotter.plot_correlation_matrix(c_matrix, f"Feature Correlation | {name}", destination,
                                                     f"corr_{name}.png")

        # --- ГРАФІК 5: t-SNE Manifold ---
        StatsPlotter.plot_dataset_manifold(df, numeric_features, class_col, destination)

    def show_console_report(self, df: pd.DataFrame, target_format: str) -> None:
        total_objects = len(df)
        total_annotations = df[ImageStatsKeys.im_path].nunique()
        objects_per_image = df.groupby(ImageStatsKeys.im_path).size()
        average_density = objects_per_image.mean()
        std_density = objects_per_image.std()

        report_rows = [
            "\n" + self.line,
            f"DATASET REPORT FOR {target_format.upper()}",
            self.line,
            f"Total images             :  {total_annotations}",
            f"Total annotated objects  :  {total_objects}",
            f"Objects per image (avg)  :  {average_density:.2f}",
            f"Density deviation (std)  :  {std_density:.2f}"
        ]

        for section in self.settings.img_dataset_report_schema:
            if "IMAGE QUALITY" in section["title"]:
                report_rows.extend(self._render_section(df, section, total_objects))

        for object_name in sorted(df['class_name'].unique()):
            cls_df = df[df['class_name'] == object_name]
            cls_count = len(cls_df)

            report_rows.append(f"\n >>> CLASS: {object_name} ({(cls_count / total_objects) * 100:.1f}%)")

            for section in self.settings.img_dataset_report_schema:
                report_rows.extend(self._render_section(cls_df, section, cls_count))

            report_rows.append(self.line + "\n")
        self.logger.info("\n".join(report_rows))

