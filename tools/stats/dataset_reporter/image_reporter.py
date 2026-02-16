from pathlib import Path
from typing import Union, List

import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from const_utils.stats_constansts import ImageStatsKeys
from tools.stats.dataset_reporter.base_reporter import BaseDatasetReporter
from services.plotter import StatsPlotter


class ImageDatasetReporter(BaseDatasetReporter):
    """
    Implementation of BaseDatasetReporter for Computer Vision datasets.

    This class orchestrates the complete reporting pipeline. It aggregates
    geometric and pixel-level features to generate structured console logs,
    spatial heatmaps, correlation matrices, and UMAP manifold projections.
    """
    def generate_visual_report(
            self,
            df: pd.DataFrame,
            features: List[str],
            destination: Union[Path, PdfPages]
    ):
        """
        Orchestrates the visual analytics pipeline to create technical plots.

        The pipeline includes:
            1. Class distribution bar charts.
            2. Geometric analysis (Area boxplots and Aspect Ratio violin plots).
            3. Dataset Bias Matrix (Correlation between classes and features).
            4. Per-class Spatial Density heatmaps (3x3 grid).
            5. Per-class internal feature correlation matrices.
            6. Global UMAP manifold projection.

        Args:
            df (pd.DataFrame): The extracted feature matrix.
            features (List[str]): List of numeric columns for correlation and manifold analysis.
            destination (Union[Path, PdfPages]): Output target (directory or PDF document).
        """
        self.logger.info("Starting visual analytics pipeline...")
        class_col = ImageStatsKeys.class_name

        # class distribution
        StatsPlotter.plot_class_distribution(df, destination)

        # boxplots for geometric features
        StatsPlotter.plot_geometry_analysis(df, destination)

        # correlation bias between classes and features
        class_dummies = pd.get_dummies(df[class_col], prefix='class').astype(int)
        df_combined = pd.concat([df[features], class_dummies], axis=1)
        full_corr = df_combined.corr()

        class_cols = [c for c in full_corr.columns if c.startswith('class_')]
        bias_matrix = full_corr.loc[class_cols, features]

        StatsPlotter.plot_correlation_matrix(
            bias_matrix, "Dataset Bias: Classes vs Features",
            destination, "corr_bias.png", annot_size=7
        )

        # heatpaps for spatial distribution of objects
        all_class_corrs = df.groupby(class_col)[features].corr()

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

        # UMAP manifold projection
        StatsPlotter.plot_dataset_manifold(df, features, class_col, destination, n_jobs=self.settings.n_jobs)

    def show_console_report(self, df: pd.DataFrame, target_format: str) -> None:
        """
        Aggregates dataset statistics and prints a structured technical summary.

        Provides insights into object density, image quality metrics, and
        detailed per-class geometry and spatial bias.

        Args:
            df (pd.DataFrame): The extracted feature matrix.
            target_format (str): The annotation format (e.g., 'yolo', 'voc').
        """
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

