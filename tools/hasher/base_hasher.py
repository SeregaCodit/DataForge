from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Tuple, Dict, List, Set

import numpy as np

from const_utils.default_values import DefaultValues


class BaseHasher(ABC):
    """a base hasher class"""
    def __init__(
            self,
            image_dir: Path,
            kernel_size: Union[Tuple[int, int], int] = (16, 16),
            hash_type: str = DefaultValues.dhash,
            threshold: float = 0.1
    ):
        self.hash_type = hash_type
        self.image_dir = image_dir
        self.kernel_size = kernel_size
        self.threshold = threshold

    @abstractmethod
    def compute_hash(self, image_path: Path) -> np.ndarray:
        pass

    @staticmethod
    def calculate_distance(hash1: np.ndarray, hash2: np.ndarray) -> int:
        """calculate hemming distance between two image hashes"""
        hemming_distance = np.count_nonzero(hash1 != hash2)
        return int(hemming_distance)

    def get_hashmap(self, image_paths: List[Path]) -> Dict[Path, np.ndarray]:
        """
        :param image_paths: list of images paths
        creating a dict with image path's and their hashes
        """
        hash_map: Dict[Path, np.ndarray] = {}
        for path in image_paths:
            if path.is_file():
                _hash = self.compute_hash(path)
                hash_map[path] = _hash
        return hash_map

    def find_duplicates(self, hashmap: Dict[Path, np.ndarray]) -> List[Path]:
        """
        :param hashmap: a has_map of all files in the source_directory
        comparing all files via each with each principe in hashmap by hemming distance
        """
        duplicates: Set[Path] = set()
        paths: List[Path] = list(hashmap.keys())

        #вважаємо поточний файл унікальним
        for unique_index in range(len(paths)):
            unique_image = paths[unique_index]
            if unique_image in duplicates:
                continue
            # вважаємо наступні файли кандидатами на дубль
            for candidate_index in range(unique_index + 1, len(paths)):
                candidate_image = paths[candidate_index]
                if candidate_image in duplicates:
                    continue

                hemming_distance = self.calculate_distance(hashmap[unique_image], hashmap[candidate_image])
                if hemming_distance > self.threshold:
                    duplicates.add(candidate_image)
        return list(duplicates)

    @property
    def kernel_size(self) -> Tuple[int, int]:
        return self.__kernel_size

    @kernel_size.setter
    def kernel_size(self, kernel_size: Union[Tuple[int, int], int]) -> None:
        if isinstance(kernel_size, int):
            self.__kernel_size = (kernel_size, kernel_size)
        else:
            self.__kernel_size = kernel_size

