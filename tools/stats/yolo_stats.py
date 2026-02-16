from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from const_utils.stats_constansts import ImageStatsKeys
from services.convertion_utils import to_voc_dict
from tools.annotation_converter.reader.base import BaseReader
from tools.stats.base_stats import BaseStats
from tools.stats.extractor import FeatureExtractor
from tools.stats.image_analyzer import ImageContentAnalyzer


class YoloStats(BaseStats):
    """
    Concrete analyzer for datasets in YOLO (.txt) format.

    This class processes YOLO annotations by converting them into a temporary
    dictionary format compatible with the common FeatureExtractor. It handles
    multiprocessing logic and fuses geometric data with pixel-level metrics.
    """

    # Shared lookup map for image paths across worker processes
    _worker_image_map = {}


    @classmethod
    def _init_worker(cls, image_dict: Dict[str, str]):
        """
        Initializes a worker process with a shared image map.

        This method ensures each parallel worker has access to the full
        list of image paths during the analysis.

        Args:
            image_dict (Dict[str, str]): Map of image stems to their absolute paths.
        """
        cls._worker_image_map = image_dict


    @staticmethod
    def get_umap_features(df: pd.DataFrame) -> List[str]:
        """
        Identifies numeric columns suitable for UMAP dimensionality reduction.

        Filters out non-numeric data, identifiers, and outlier-specific columns
        to prepare a clean input for the UMAP manifold generator.

        Args:
            df (pd.DataFrame): The main dataset feature matrix.

        Returns:
            List[str]: A list of selected column names for UMAP processing.
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


    @staticmethod
    def _analyze_worker(
            file_path: Path,
            reader: BaseReader,
            margin_threshold: int = 5,
            class_mapping: Optional[Dict[str, str]] = None

    ) -> List[Dict[str, str]]:
        """
        Processes a single YOLO text file and extracts combined features.

        The worker follows these steps:
            1. Reads the raw YOLO annotation file.
            2. Converts normalized YOLO coordinates into an internal dictionary.
            3. Extracts geometric features (area, sectors, truncation).
            4. Performs image content analysis (brightness, contrast, etc.).
            5. Merges all metrics into a final feature list.

        Args:
            file_path (Path): Path to the .txt YOLO annotation file.
            reader (BaseReader): TXT reader instance to parse YOLO data.
            margin_threshold (int): Distance from edges to detect object truncation.
            class_mapping (Optional[Dict[str, str]]): Map to translate class IDs to names.

        Returns:
            List[Dict[str, Any]]: A list of feature dictionaries for all objects
                in the file. Returns an empty list if any step fails.
        """
        try:
            annotation_data = reader.read(file_path)


            if not annotation_data:
                return []
            correspond_img_str = YoloStats._worker_image_map.get(file_path.stem)

            if correspond_img_str is None:
                return []


            converted_dict = to_voc_dict(
                annotations=annotation_data,
                class_mapping=class_mapping,
                correspond_img=correspond_img_str
            )

            annotation = converted_dict.get("annotation", {})
            stat_data = FeatureExtractor.extract_features(file_path, annotation, margin_threshold)
            pixel_data = ImageContentAnalyzer.analyze_metrics(correspond_img_str)

            for obj in stat_data:
                obj.update(pixel_data)
                obj.update({ImageStatsKeys.im_path: correspond_img_str})

            return stat_data
        except Exception as e:
            return []