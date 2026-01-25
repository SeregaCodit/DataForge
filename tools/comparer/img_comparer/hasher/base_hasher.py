from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Tuple, Dict, List, Set
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np

from logger.logger import LoggerConfigurator
from const_utils.default_values import DefaultValues


class BaseHasher(ABC):
    """a base hasher class"""
    def __init__(
        self,
        hash_type: str = DefaultValues.dhash,
        core_size: Union[Tuple[int, int], int] = DefaultValues.core_size,
        threshold: int = DefaultValues.hash_threshold,
        log_path: Path = DefaultValues.log_path,
    ):
        """

        :param hash_type: type of hash algorithm to use
        :param core_size: size of resizing image in algorithm, hash_size will be square of this value.
            biggest core size makes details at image more important. So with equal threshold with different core size
            same images can be duplicates or not duplicates
        :param threshold: threshold in percentage for hemming distance. Files that have lower hemming distance will be
            considered duplicates.
        :param log_path: path to log file
        """
        self.hash_type = hash_type
        self.core_size = core_size
        self.threshold = threshold
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None,
            log_level=DefaultValues.log_level
        )
    @staticmethod
    @abstractmethod
    def compute_hash(image_path: Path, core_size: int = DefaultValues.core_size) -> np.ndarray:
        pass

    @staticmethod
    def calculate_distance(hash1: np.ndarray, hash2: np.ndarray) -> int:
        """calculate hemming distance between two image hashes"""
        hemming_distance = np.count_nonzero(hash1 != hash2)
        return int(hemming_distance)

    def get_hashmap(self, image_paths: Tuple[Path]) -> Dict[Path, np.ndarray]:
        """
        :param image_paths: list of images paths
        creating a dict with image path's and their hashes
        """
        self.logger.info(f"Building hashmap in parallel using {DefaultValues.max_workers} workers for {len(image_paths)} images...")


        hash_func = partial(self.__class__.compute_hash, core_size=self.core_size)

        with ProcessPoolExecutor(max_workers=DefaultValues.max_workers) as executor:
            hashes = list(executor.map(hash_func, image_paths))
        hash_map = dict(zip(image_paths, hashes))
        self.logger.info(
            f"Got hashmap for {len(image_paths)} images...")
        return hash_map

    def find_duplicates(self, hashmap: Dict[Path, np.ndarray]) -> List[Path]:
        """
        :param hashmap: a has_map of all files in the source_directory
        comparing all files via each with each principe in hashmap by hemming distance
        """
        self.logger.info(f"Finding duplicates in {len(hashmap)} images...")
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
                if hemming_distance < self.threshold:
                    self.logger.info(f"duplicate {unique_image} -> {candidate_image}, hemming distance: {hemming_distance}")
                    duplicates.add(candidate_image)
        self.logger.info(f"Found {len(duplicates)} duplicate images")
        return list(duplicates)

    @property
    def core_size(self) -> int:
        return self._core_size

    @core_size.setter
    def core_size(self, value: Union[Tuple[int, int], int, float, str]) -> None:
        """
        stups hash size, converts into int type
        :param value: size of hash. Using for resizing an image
        """
        if isinstance(value, int):
            self._core_size = value
        elif isinstance(value, (float, str)):
            try:
                self._core_size = int(value)
            except TypeError:
                self.logger.error(f"hash size must be int, got {type(value)}")
                raise TypeError(f"hash size must be int, got {type(value)}")
        elif isinstance(value, tuple):
            self._core_size = value[0] if value[0] >= 0 else value[1]
        else:
            self.logger.error(f"hash size must be int or tuple, got {type(value)}")
            raise TypeError(f"hash size must be int or tuple, got {type(value)}")

    @property
    def threshold(self) -> int:
        return self._threshold

    @threshold.setter
    def threshold(self, value: Union[float, int]) -> None:
        """
        setting a threshold value in percentage. If value is not float type - trying to convert it to float.
        :param value: float or int minimal value in percents that means an image is not a duplicate of comparing image
        """

        try:
            value = int(value)
        except TypeError:
            self.logger.error(f"threshold must be float, got {type(value)}")
            raise TypeError(f"threshold must be float, got {type(value)}")
        except ValueError:
            self.logger.error(f"threshold must be real number, got {type(value)}")
            raise TypeError(f"threshold must be float, got {type(value)}")

        if 0 > value > DefaultValues.max_percentage:
            self.logger.error(f"threshold must be between 0 and 100, got {value}")
            raise ValueError(f"threshold must be between 0 and 100, got {type(value)}")

        hash_sqr = self.core_size * self.core_size
        self._threshold = int(hash_sqr * (value / DefaultValues.max_percentage))



