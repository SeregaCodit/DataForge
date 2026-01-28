import multiprocessing
from abc import ABC, abstractmethod
from linecache import cache
from pathlib import Path
from typing import Union, Tuple, Dict, List, Set, Optional
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator
# from const_utils.default_values import DefaultValues
from tools.cache import CacheIO


class BaseHasher(ABC):

    def __init__(
        self,
        settings: AppSettings,
        cache_io: Optional[CacheIO] = None
    ):
        """
        :param settings: settings from defaults and cli
        :param cache_io: a class for loading and saving cache
        Find duplicates in source dir. For faster work with remote data used hashmaps.
        """
        self.settings = settings
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(self.settings.log_path) / f"{self.__class__.__name__}.log" if self.settings.log_path else None,
            log_level=self.settings.log_level
        )

        self.hash_type = self.settings.method
        self.core_size = self.settings.core_size
        self.threshold = self.settings.hash_threshold
        self.cache_io = cache_io or CacheIO(self.settings)
        self.n_jobs = self.settings.n_jobs

    @staticmethod
    @abstractmethod
    def compute_hash(image_path: Path, core_size: int) -> np.ndarray:
        pass

    def validate_hash_map(
            self,
            image_paths: Tuple[Path],
            hash_map: Dict[Path, np.ndarray]
    ) -> Tuple[bool, Dict[Path, np.ndarray]]:
        """
        :param image_paths: tuple of images paths
        :param hash_map: current hash map

        compares current hash map with all images paths. If there is no difference - returns True and hash map.
        Else: check for missing paths in hash map and for obsolete paths in hash map. Updates hash map deleting
        obsolete paths and adding missing paths in hash map. Return False and hash map.
        """
        paths_set = set(image_paths)
        cached_set = set(hash_map.keys())

        missing_paths = tuple(paths_set - cached_set)
        obsolete_paths = cached_set - paths_set

        if not missing_paths and not obsolete_paths:
            self.logger.info(f"Cache matches disk 1:1 ({len(hash_map)} items).")
            return True, hash_map

        valid_cache = {path: hash_data for path, hash_data in hash_map.items() if path in paths_set}

        if missing_paths:
            self.logger.info(f"Syncing cache: calculating {len(missing_paths)} new images...")
            new_hashes = self.update_hashes(missing_paths)
            for path, hash_data in zip(missing_paths, new_hashes):
                if hash_data is not None:
                    valid_cache[path] = hash_data

        return False, valid_cache

    def update_hashes(self, image_paths: Tuple[Path, ...]) -> list:
        """
        :param image_paths: tuple of images paths
        Updating and returns a generated hash list for image_paths using multiprocessing
        """
        hash_func = partial(self.__class__.compute_hash, core_size=self.core_size)

        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            hashes = list(executor.map(hash_func, image_paths))

        return hashes

    def get_hashmap(self, image_paths: Tuple[Path]) -> Dict[Path, np.ndarray]:
        """
        :param image_paths: list of images paths
        creating a dict with image path's and their hashes
        """
        if not image_paths:
            return {}

        image_count = len(image_paths)
        filename = self.cache_io.generate_cache_filename(
            image_paths[0].parent.resolve(),
            hash_type=self.hash_type,
            core_size=self.core_size,
            cache_name=self.settings.cache_name
        )

        cache_file_name = self.settings.cache_file_path / filename
        cache_file_name.parent.mkdir(parents=True, exist_ok=True)

        hash_map = self.cache_io.load(cache_file_name)

        if hash_map:
            is_valid, valid_hash_map = self.validate_hash_map(image_paths, hash_map)
            if is_valid:
                return hash_map
            else:
                self.cache_io.save(valid_hash_map, cache_file_name)
                self.logger.info(f"Hash map updated: {len(valid_hash_map)} total valid hashes.")
                return valid_hash_map

        self.logger.info(f"Building hashmap in parallel using {self.n_jobs} workers for {image_count} images...")

        hashes = self.update_hashes(image_paths)
        hash_map = {
            path: h for path, h in zip(image_paths, hashes)
            if h is not None
        }

        self.logger.info(f"Successfully hashed {len(hash_map)} out of {image_count} images")
        self.cache_io.save(hash_map, cache_file_name)
        return hash_map

    def find_duplicates(self, hashmap: Dict[Path, np.ndarray]) -> List[Path]:
        """
        :param hashmap: a has_map of all files in the source_directory
        comparing all files via each with each principe in hashmap by hemming distance
        """

        if not hashmap:
            return []

        self.logger.info(f"Vectorizing comparison for {len(hashmap)} images...")

        paths: List[Path] = list(hashmap.keys())
        try:
            matrix = np.array(list(hashmap.values()), dtype=bool)
        except ValueError as e:
            self.logger.error("Failed to create matrix. Some hashes have different lengths!")
            raise e

        duplicates_indices: Set[int] = set()

        for index in range(len(paths)):
            if index in duplicates_indices:
                continue

            current_hash = matrix[index]
            hamming_distances = np.count_nonzero(matrix != current_hash, axis=1)
            matches = np.where(hamming_distances <= self.threshold)[0]

            for match_idx in matches:
                if match_idx > index:
                    duplicates_indices.add(int(match_idx))

        result = [paths[idx] for idx in duplicates_indices]
        self.logger.info(f"Vectorized search finished. Found {len(result)} duplicates.")
        return result

    @property
    def core_size(self) -> int:
        return self._core_size

    @core_size.setter
    def core_size(self, value: Union[Tuple[int, int], int, float, str]) -> None:
        """Sets core size and triggers threshold bits recalculation"""
        try:
            if isinstance(value, tuple):
                new_size = int(value[0]) if value[0] > 0 else int(value[1])
            else:
                new_size = int(float(value))

            self._core_size = new_size

            if hasattr(self, '_threshold_pct'):
                self._recalculate_threshold_bits(self._threshold_pct)

        except (ValueError, TypeError, IndexError) as e:
            self.logger.error(f"Invalid core_size type: {type(value)}. Using default.")
            raise TypeError(f"core_size must be convertible to int") from e

    @property
    def threshold(self) -> int:
        """Returns distance threshold in BITS (used in find_duplicates)"""
        return self._threshold

    @threshold.setter
    def threshold(self, value: Union[float, int, str]) -> None:
        """Sets threshold as PERCENTAGE and calculates bits"""
        try:
            pct_value = float(value)
        except (ValueError, TypeError) as e:
            self.logger.error(f"Threshold must be a number, got {type(value)}")
            raise ValueError(f"Invalid threshold value: {value}") from e

        if not (0 <= pct_value <= self.settings.max_percentage):
            self.logger.error(f"Threshold percentage out of range [0-100]: {pct_value}")
            raise ValueError(f"Threshold must be between 0 and 100")

        self._threshold_pct = pct_value
        self._recalculate_threshold_bits(pct_value)

    def _recalculate_threshold_bits(self, percentage: float) -> None:
        """Internal helper to calculate bits based on current core_size"""
        hash_sqr = self.core_size * self.core_size
        self._threshold = int(hash_sqr * (percentage / self.settings.max_percentage))
        self.logger.debug(f"Threshold recalculated: {percentage}% of {hash_sqr} bits = {self._threshold} bits")

    @property
    def n_jobs(self) -> int:
        return self._n_jobs

    @n_jobs.setter
    def n_jobs(self, value: Union[int, float, str]) -> None:
        """
            safe setting n_jobs
        """
        # check types and try to int
        if not isinstance(value, int):
            try:
                value = int(float(value))
            except TypeError:
                self.logger.error(f"n_jobs must be int, got {type(value)}")
                raise TypeError(f"n_jobs must be int, got {type(value)}")
            except ValueError:
                self.logger.error(f"n_jobs must be real number, got {type(value)}")
                raise ValueError(f"n_jobs must be real number, got {type(value)}")

        # check cores and control that n_jobs can be set
        cores = multiprocessing.cpu_count()

        if value <= 1:
            self.logger.warning(f"n_jobs must be greater than 1, got {value}")
            value = 1
        elif 1 < cores <= value:
            self.logger.warning(f"n_jobs must be less than {cores}, got {value}")
            value = cores - 1
        elif cores == 1 and value != 1:
            value = 1

        self._n_jobs = value
        self.logger.info(f"n_jobs set to {value}")