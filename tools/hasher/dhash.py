from pathlib import Path
from typing import Union, Tuple

import cv2
import numpy as np

from tools.hasher.base_hasher import BaseHasher

class DHash(BaseHasher):
    """dHash compare algorithm"""
    def __init__(
            self,
            image_dir: Path,
            hash_size: Union[Tuple[int, int], int] = 16
    ):
        super().__init__(image_dir)
        self.hash_size = hash_size

    def compute_hash(self, image_path: Path) -> Union[np.ndarray, None]:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            return None

        resized_image = cv2.resize(image, (self.hash_size + 1, self.hash_size), interpolation=cv2.INTER_AREA)
        # лівий піксель яскравіший за правий — True, інакше False
        gradient_difference = resized_image[:, 1:] > resized_image[:, :-1]

        return gradient_difference.flatten()


    @property
    def hash_size(self) -> int:
        return self._hash_size

    @hash_size.setter
    def hash_size(self, value: Union[Tuple[int, int], int]) -> None:
        if isinstance(value, int):
            self._hash_size = value
        elif isinstance(value, tuple):
            self._hash_size = value[0] if value[0] <= 0 else value[1]
        else:
            self.logger.error(f"hash size must be int or tuple, got {type(value)}")
            raise TypeError(f"hash size must be int or tuple, got {type(value)}")

