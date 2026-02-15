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
    High-performance visualization service.
    Follows a 'Dumb Renderer' pattern: receives prepared data and draws it.
    """

    @staticmethod
    def _save_and_close(fig, destination: Union[Path, str, PdfPages], filename: str):
        """Handles polymorphic saving to either PDF or PNG."""
        if isinstance(destination, PdfPages):
            destination.savefig(fig)
        else:
            save_path = Path(destination) / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)


    @staticmethod
    def plot_class_distribution(df: pd.DataFrame, destination: Union[Path, str, PdfPages]) -> None:
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
            features: List[str],
            class_col: str,
            destination: Union[Path, str, PdfPages],
            figsize: Tuple[int, int] = (14, 12),
            n_jobs: int = 1,
    ) -> None:
        """
        Generates a unified UMAP plot for the entire dataset.
        Better than t-SNE for identifying gaps and clusters for balancing.
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