from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
import pandas as pd

from const_utils.stats_constansts import ImageStatsKeys
from tools.annotation_converter.reader.base import BaseReader
from tools.stats.base_stats import BaseStats
from tools.stats.extractor import FeatureExtractor
from tools.stats.image_analyzer import ImageContentAnalyzer


class VOCStats(BaseStats):
    """
    Concrete analyzer for datasets in Pascal VOC (XML) format.

    This class implements the processing logic for XML annotation files.
    It coordinates data reading, geometric feature extraction, and
    pixel-level image analysis to build a comprehensive feature matrix.
    """
    _worker_image_map = {}

    @staticmethod
    def get_umap_features(df: pd.DataFrame) -> List[str]:
        """
        Selects relevant numeric columns for dimensionality reduction (UMAP).

        Filters out metadata (paths, timestamps), categorical data,
        and outlier flags to ensure UMAP focuses on geometric and
        content-based manifold analysis.

        Args:
            df (pd.DataFrame): The complete feature matrix.

        Returns:
            List[str]: A list of numeric column names suitable for projection.
        """
        exclude = {
            ImageStatsKeys.class_name,
            ImageStatsKeys.path,
            ImageStatsKeys.mtime,
            ImageStatsKeys.has_neighbors,
            ImageStatsKeys.full_size,
            ImageStatsKeys.objects_count
        }

        numeric_features = [c for c in df.select_dtypes(include=[np.number]).columns
                            if c not in exclude and not c.startswith('outlier')]

        return numeric_features

    @classmethod
    def _init_worker(cls, image_dict: Dict[str, str]):
        """
        Initializes a worker process with a shared image lookup map.

        This method is called once per worker process during the startup
        of the ProcessPoolExecutor to provide fast access to image paths.

        Args:
            image_dict (Dict[str, str]): Map of image stems to their absolute paths.
        """
        cls._worker_image_map = image_dict

    @staticmethod
    def _analyze_worker(
            file_path: Path,
            reader: BaseReader,
            margin_threshold: int = 5,
            class_mapping: Optional[Dict[str, str]] = None

    ) -> List[Dict[str, str]]:
        """
         Parses a single VOC XML file and merges geometric data with pixel metrics.

         The workflow includes:
             1. Parsing XML to get object coordinates.
             2. Calculating geometric features (area, aspect ratio, etc.).
             3. Analyzing image content (brightness, contrast, blur).
             4. Fusing both data sources into a single record.

         Args:
             file_path (Path): Path to the .xml annotation file.
             reader (BaseReader): XML parser instance.
             margin_threshold (int): Margin for truncation detection.
             class_mapping (Optional[Dict[str, str]]): ID-to-name mapping.

         Returns:
             List[Dict[str, str]]: A list of fused feature dictionaries
                 for each object. Returns an empty list on failure.
         """
        try:
            annotation_data = reader.read(file_path).get("annotation")

            if not annotation_data:
                return []
            correspond_img_str = VOCStats._worker_image_map.get(file_path.stem)
            stat_data = FeatureExtractor.extract_features(file_path, annotation_data, margin_threshold)
            pixel_data = ImageContentAnalyzer.analyze_metrics(correspond_img_str)

            for obj in stat_data:
                obj.update(pixel_data)
                obj.update({ImageStatsKeys.im_path: correspond_img_str})

            return stat_data
        except Exception as e:
            return []
