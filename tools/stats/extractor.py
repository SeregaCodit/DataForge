from pathlib import Path
from typing import List, Dict, Any, Union

from const_utils.stats_constansts import ImageStatsKeys
from const_utils.xml_names import XMLNames


class FeatureExtractor:
    """
    Extracts geometric and spatial characteristics from raw annotation data.

    This class processes bounding box coordinates to calculate technical
    metrics such as relative area, aspect ratio, and spatial positioning.
    It identifies which part of the image an object occupies and detects
    if an object is cut off (truncated) at the image boundaries.
    """
    @staticmethod
    def extract_features(filepath: Union[Path, str], data: dict, margin_threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Calculates geometric and spatial features for all objects in an image.

        The method divides the image into sectors based on the center point
        to determine object orientation (e.g., top-left, center, bottom-side).

        Args:
            filepath (Union[Path, str]): Path to the annotation file, used as a unique ID.
            data (dict): Dictionary containing image dimensions and object bounding boxes.
            margin_threshold (int): Distance in pixels from the edge to consider
                an object as 'truncated'. Defaults to 5.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                contains features for a single object. Returns an empty list
                if image dimensions are invalid (<= 0).
        """
        if not isinstance(filepath, str):
            filepath = str(filepath)
        try:
            has_neighbors = 1
            image_data = data.get(XMLNames.size, {})

            im_width = int(image_data.get(XMLNames.width, 0))
            im_height = int(image_data.get(XMLNames.height, 0))

            if any([im_width <= 0, im_height <= 0]):
                return []

            im_depth = int(image_data.get(XMLNames.depth, 0))
            im_area = im_width * im_height
            img_center_x = im_width / 2
            img_center_y = im_height / 2
            annotated_objects = data.get(XMLNames.object, [])

            if isinstance(annotated_objects, dict):
                annotated_objects = [annotated_objects]
                has_neighbors = 0

            result = []
            objects_count = len(annotated_objects)

            for obj in annotated_objects:
                bbox = obj.get(XMLNames.bndbox)

                xmax = int(bbox.get(XMLNames.xmax, 0))
                ymax = int(bbox.get(XMLNames.ymax, 0))
                xmin = int(bbox.get(XMLNames.xmin, 0))
                ymin = int(bbox.get(XMLNames.ymin, 0))

                width = xmax - xmin
                height = ymax - ymin
                area = width * height
                relative_area = area / im_area

                # if bbox corners in all four image quarters
                in_center = 1 if all([
                    xmin <= img_center_x <= xmax,
                    ymin <= img_center_y <= ymax
                ]) else 0
                # if object on im_center_y coord but has right offset
                in_right_side = 1 if all([
                    ymin < img_center_y < ymax,
                    xmin > img_center_x
                ]) else 0
                # if object on im_center_y coord but has left offset
                in_left_side = 1 if all([
                    ymin < img_center_y < ymax,
                    xmax < img_center_x
                ]) else 0
                # if object on im_center_x coord but has top offset
                in_top_side = 1 if all([
                    xmin < img_center_x < xmax,
                    ymax < img_center_y
                ]) else 0
                # if object on im_center_x coord but has bottom offset
                in_bottom_side = 1 if all([
                    xmin < img_center_x < xmax,
                    ymin > img_center_y
                ]) else 0
                # object absolutely in top left quarter
                in_left_top = 1 if all([
                    xmax < img_center_x,
                    ymax < img_center_y
                ]) else 0
                # object absolutely in top right quarter
                in_right_top = 1 if all([
                    xmin > img_center_x,
                    ymax > img_center_y
                ]) else 0
                # object absolutely in left bottom quarter
                in_left_bottom = 1 if all([
                    xmax < img_center_x,
                    ymin > img_center_y
                ]) else 0
                # object absolutely in right bottom quarter
                in_right_bottom = 1 if all([
                    xmin > img_center_x,
                    ymin > img_center_y
                ]) else 0

                truncated_left = 1 if xmin < margin_threshold else 0
                truncated_right = 1 if xmax > (im_width - margin_threshold) else 0
                truncated_top = 1 if ymin < margin_threshold else 0
                truncated_bottom = 1 if ymax > (im_height - margin_threshold) else 0

                full_size = 1 if all([
                    truncated_left,
                    truncated_right,
                    truncated_top,
                    truncated_bottom]) else 0

                object_data = {
                    ImageStatsKeys.path: filepath,
                    ImageStatsKeys.class_name: obj.get(XMLNames.name, "unfilled"),
                    ImageStatsKeys.objects_count: objects_count,
                    ImageStatsKeys.im_width: im_width,
                    ImageStatsKeys.im_height: im_height,
                    ImageStatsKeys.im_depth: im_depth,
                    ImageStatsKeys.has_neighbors: has_neighbors,
                    ImageStatsKeys.object_width: width,
                    ImageStatsKeys.object_height: height,
                    ImageStatsKeys.object_aspect_ratio: width / height if height > 0 else 0,
                    ImageStatsKeys.object_area: area,
                    ImageStatsKeys.object_relative_area: relative_area,
                    ImageStatsKeys.object_in_center: in_center,
                    ImageStatsKeys.object_in_right_side: in_right_side,
                    ImageStatsKeys.object_in_left_side: in_left_side,
                    ImageStatsKeys.object_in_top_side: in_top_side,
                    ImageStatsKeys.object_in_bottom_side: in_bottom_side,
                    ImageStatsKeys.object_in_left_top: in_left_top,
                    ImageStatsKeys.object_in_right_top: in_right_top,
                    ImageStatsKeys.object_in_left_bottom: in_left_bottom,
                    ImageStatsKeys.object_in_right_bottom: in_right_bottom,
                    ImageStatsKeys.full_size: full_size,
                    ImageStatsKeys.truncated_left: truncated_left,
                    ImageStatsKeys.truncated_right: truncated_right,
                    ImageStatsKeys.truncated_top: truncated_top,
                    ImageStatsKeys.truncated_bottom: truncated_bottom
                }

                result.append(object_data)
        except ZeroDivisionError:
            return []
        return result
