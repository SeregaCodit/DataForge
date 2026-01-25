from pathlib import Path
from typing import Union

import cv2
import numpy as np

from tools.comparer.img_comparer.hasher.base_hasher import BaseHasher

class DHash(BaseHasher):
    """dHash compare algorithm"""

    def compute_hash(self, image_path: Path) -> Union[np.ndarray, None]:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            return None

        resized_image = cv2.resize(image, (self.core_size + 1, self.core_size), interpolation=cv2.INTER_AREA)
        # лівий піксель яскравіший за правий — True, інакше False
        gradient_difference = resized_image[:, 1:] > resized_image[:, :-1]

        return gradient_difference.flatten()




