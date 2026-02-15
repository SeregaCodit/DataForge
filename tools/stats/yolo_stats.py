from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from const_utils.stats_constansts import ImageStatsKeys
from services.yolo_to_dict import YoloToDict
from tools.annotation_converter.reader.base import BaseReader
from tools.stats.base_stats import BaseStats
from tools.stats.extractor import FeatureExtractor
from tools.stats.image_analyzer import ImageContentAnalyzer


class YoloStats(BaseStats):
    _worker_image_map = {}


    @classmethod
    def _init_worker(cls, image_dict: Dict[str, str]):
        """
        Prepares a worker process by storing a shared image map in the class memory.

        Args:
            image_dict (Dict[str, str]): A dictionary mapping image names to their paths.
        """
        cls._worker_image_map = image_dict

    @staticmethod
    def get_umap_features(df: pd.DataFrame) -> List[str]:
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
        Processes a single VOC XML file to extract object features.

        Args:
            file_path (Path): Path to the .xml annotation file.
            reader (BaseReader): An instance of XMLReader to parse the file.
            margin_threshold (int): Distance from the image edge to detect truncation.
            class_mapping (Optional[Dict[str, str]]): Optional mapping to rename classes.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing features
                for each object found in the XML. Returns an empty list
                if the file is invalid.
        """
        try:
            annotation_data = reader.read(file_path)


            if not annotation_data:
                return []
            correspond_img_str = YoloStats._worker_image_map.get(file_path.stem)

            if correspond_img_str is None:
                return []


            converted_dict = YoloToDict.to_voc_dict(
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