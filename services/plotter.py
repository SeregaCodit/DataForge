import matplotlib

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Union, Tuple, List, Optional
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE

from const_utils.stats_constansts import ImageStatsKeys

matplotlib.set_loglevel("WARNING")


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
    def plot_dataset_manifold(df: pd.DataFrame, features: List[str], class_col: str,
                              destination: Union[Path, str, PdfPages]) -> None:
        # Balanced sampling
        subset = df.sample(frac=1, random_state=42).groupby(class_col).head(1000)
        if len(subset) < 10: return

        x_data = subset[features].fillna(0)
        x_data = x_data.loc[:, x_data.var() > 0]
        if x_data.shape[1] < 2: return

        x_scaled = StandardScaler().fit_transform(x_data)
        tsne = TSNE(n_components=2, perplexity=min(30, len(subset) - 1), random_state=42, init='pca',
                    learning_rate='auto')
        x_2d = tsne.fit_transform(x_scaled)

        fig, ax = plt.subplots(figsize=(12, 10))

        num_colors = df[ImageStatsKeys.class_name].nunique()
        sns.scatterplot(
            x=x_2d[:, 0],
            y=x_2d[:, 1],
            hue=subset[class_col],
            palette=sns.color_palette("husl", num_colors),
            edgecolor='black',  # Тонка обводка
            linewidth=0.5,  # Товщина обводки
            s=60,
            alpha=0.7,
            ax=ax
        )
        ax.set_title("Global Dataset Manifold (t-SNE)", fontsize=16)
        ax.grid(True, linestyle='--', alpha=0.3)
        fig.tight_layout()
        StatsPlotter._save_and_close(fig, destination, "dataset_manifold.png")