from pathlib import Path
from typing import Dict

import cv2
import numpy as np

from const_utils.stats_constansts import ImageStatsKeys


class ImageContentAnalyzer:
    """
    Provides utility methods to analyze image quality and pixel data.

    This class extracts physical metrics from images, such as brightness,
    contrast, and sharpness (blur score), which are essential for
    understanding the quality of a computer vision dataset.
    """

    @staticmethod
    def analyze_metrics(img_path: str) -> Dict[str, float]:
        """
        Calculates brightness, contrast, and blur score for an image file.

        The method performs the following steps:
        1. Reads the image from the disk in BGR format.
        2. Converts the image to grayscale.
        3. Computes the mean (brightness), standard deviation (contrast),
           and Laplacian variance (blur score).

        Args:
            img_path (Path): The file system path to the image.

        Returns:
            Dict[str, float]: A dictionary containing calculated metrics.
                Returns an empty dictionary if the image cannot be read.
        """
        try:
            image = cv2.imread(str(img_path))
        except Exception:
            return {}

        if image is None:
            return {}

        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        data = {
            ImageStatsKeys.im_brightness: round(float(np.mean(image_gray)), 2),
            ImageStatsKeys.im_contrast: round(float(np.std(image_gray)), 2),
            ImageStatsKeys.im_blur_score: round(float(cv2.Laplacian(image_gray, cv2.CV_64F).var()), 2)
        }
        return data