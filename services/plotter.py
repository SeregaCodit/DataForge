import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Union, Tuple, List, Optional
from matplotlib.backends.backend_pdf import PdfPages

from const_utils.stats_constansts import ImageStatsKeys


class StatsPlotter:
    """
    Service for generating technical visualizations and reports.

    This class follows the 'Dumb Renderer' pattern: it receives pre-calculated
    data and focuses only on high-quality plotting. It supports various
    chart types, including distribution bars, heatmaps, and UMAP projections.
    """

    @staticmethod
    def _save_and_close(fig, destination: Union[Path, str, PdfPages], filename: str):
        """
        Handles polymorphic saving logic for plot figures.

        Saves the figure to either  multi-page PDF document or a standalone
        PNG file based on the destination type.

        Args:
            fig (plt.Figure): The Matplotlib figure object to save.
            destination (Union[Path, str, PdfPages]): Target storage.
                Can be a directory path or an active PdfPages object.
            filename (str): Name of the file (used only for PNG output).
        """
        if isinstance(destination, PdfPages):
            destination.savefig(fig)
        else:
            save_path = Path(destination) / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)


    @staticmethod
    def plot_class_distribution(df: pd.DataFrame, destination: Union[Path, str, PdfPages]) -> None:
        """
        Creates a bar chart showing the number of objects per class.

        Args:
            df (pd.DataFrame): The dataset feature matrix.
            destination (Union[Path, str, PdfPages]): Output target.
        """
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.countplot(
            data=df,
            x=ImageStatsKeys.class_name,
            order=df[ImageStatsKeys.class_name].value_counts().index,
            ax=ax,
            hue=ImageStatsKeys.class_name,
            palette='viridis',
            legend=False
        )
        ax.set_title("Class Distribution (Object Counts)", fontsize=16)

        for p in ax.patches:
            ax.annotate(f'{int(p.get_height())}', (p.get_x() + 0.3, p.get_height() + 10))

        fig.tight_layout()
        StatsPlotter._save_and_close(fig, destination, "class_distribution.png")


    @staticmethod
    def plot_geometry_analysis(df: pd.DataFrame, destination: Union[Path, str, PdfPages]) -> None:
        """
        Visualizes object size and aspect ratio distributions.

        Generates boxplots for area (on a log scale) and violin plots
        for shape proportions to help identify geometric outliers.

        Args:
            df (pd.DataFrame): The dataset feature matrix.
            destination (Union[Path, str, PdfPages]): Output target.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        sns.boxplot(
            data=df,
            x=ImageStatsKeys.class_name,
            y='object_area',
            ax=axes[0],
            hue=ImageStatsKeys.class_name,
            palette='magma',
            legend=False
        )
        axes[0].set_title("Object Area Distribution (Log Scale)")
        axes[0].set_yscale('log')

        sns.violinplot(
            data=df,
            x=ImageStatsKeys.class_name,
            y='object_aspect_ratio',
            ax=axes[1],
            hue=ImageStatsKeys.class_name,
            palette='coolwarm',
            legend=False
        )
        axes[1].set_title("Aspect Ratio Distribution (W/H)")

        fig.suptitle("Geometric Analysis & Outlier Detection", fontsize=18)
        fig.tight_layout(rect=(0, 0.03, 1, 0.95))
        StatsPlotter._save_and_close(fig, destination, "geometry_analysis.png")

    @staticmethod
    def plot_spatial_heatmap(
            grid: List[List[int]],
            title: str,
            destination: Union[Path, str, PdfPages],
            filename: str
    ) -> None:
        """
        Generates a 3x3 density heatmap for object spatial placement.

        Visualizes how objects are distributed across the image quadrants
        (Top-Left, Center, Bottom-Right, etc.).

        Args:
            grid (List[List[int]]): 3x3 matrix containing object counts.
            title (str): Title for the heatmap plot.
            destination (Union[Path, str, PdfPages]): Output target.
            filename (str): Name of the output image.
        """
        fig, ax = plt.subplots(figsize=(8, 7))
        sns.heatmap(grid, annot=True, fmt="d", cmap="YlGnBu", ax=ax,
                    xticklabels=['Left', 'Center', 'Right'],
                    yticklabels=['Top', 'Middle', 'Bottom'])
        ax.set_title(title, fontsize=15)
        fig.tight_layout()
        StatsPlotter._save_and_close(fig, destination, filename)

    @staticmethod
    def plot_correlation_matrix(
            corr_matrix: pd.DataFrame,
            title: str,
            destination: Union[Path, str, PdfPages],
            filename: str,
            figsize: Tuple[int, int] = (12, 10),
            annot_size: int = 7
    ) -> None:
        """
        Plots a feature relationship matrix (Correlation Heatmap).

        Useful for identifying strongly linked features
        and potential feature redundancy in the dataset.

        Args:
            corr_matrix (pd.DataFrame): Calculated correlation matrix.
            title (str): Title for the chart.
            destination (Union[Path, str, PdfPages]): Output target.
            filename (str): Output filename.
            figsize (Tuple[int, int]): Size of the figure. Defaults to (12, 10).
            annot_size (int): Font size for annotations. Defaults to 7.
        """
        fig, ax = plt.subplots(figsize=figsize)

        is_square = corr_matrix.shape[0] == corr_matrix.shape[1]
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool)) if is_square else None

        sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            fmt=".2f",
            cmap='coolwarm',
            center=0,
            square=is_square,
            ax=ax,
            annot_kws={"size": annot_size},
            cbar_kws={"shrink": .8}
        )

        plt.xticks(rotation=45, ha='right', fontsize=annot_size + 2)
        plt.yticks(fontsize=annot_size + 2)
        ax.set_title(title, fontsize=16, pad=20)
        fig.tight_layout()
        StatsPlotter._save_and_close(fig, destination, filename)



    @staticmethod
    def plot_dataset_manifold(
            df: pd.DataFrame,
            class_col: str,
            destination: Union[Path, str, PdfPages],
            figsize: Tuple[int, int] = (14, 12),
    ) -> None:
        """
        Visualizes the high-dimensional data structure using UMAP.

        Creates a 2D scatter plot (manifold) that helps identify dataset
        clusters, representation gaps, and informative overlaps between classes.

        Args:
            df (pd.DataFrame): The feature matrix containing 'umap_x' and 'umap_y'.
            class_col (str): Column name for class labels (used for color-coding).
            destination (Union[Path, str, PdfPages]): Output target.
            figsize (Tuple[int, int]): Figure size. Defaults to (14, 12).
        """

        samples_per_class = 2000
        subset = df.sample(frac=1, random_state=42).groupby(class_col).head(samples_per_class)

        if len(subset) < 10:
            return

        fig, ax = plt.subplots(figsize=figsize)

        num_colors = len(subset[class_col].unique())

        sns.scatterplot(
            x=df["umap_x"],
            y=df["umap_y"],
            hue=subset[class_col],
            style=subset[class_col],
            palette=sns.color_palette("husl", num_colors),
            edgecolor='black',
            linewidth=0.5,
            s=60,
            alpha=0.6,
            ax=ax,
            legend='full'
        )

        ax.set_title("DataForge: Global Dataset Manifold (UMAP Projection)", fontsize=16, pad=20)
        ax.legend(title="Classes", bbox_to_anchor=(1.02, 1), loc='upper left')
        ax.grid(True, linestyle='--', alpha=0.3)

        fig.tight_layout()
        StatsPlotter._save_and_close(fig, destination, "dataset_manifold_umap.png")