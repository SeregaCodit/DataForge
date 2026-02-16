import multiprocessing
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Tuple, Dict, List, Set, Optional
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np
import pandas as pd

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator
from tools.cache import CacheIO


class BaseHasher(ABC):
    """
    Abstract base class for image hashing strategies in DataForge.

    This class provides the core logic for generating image hashes in parallel,
    managing incremental caching, and performing fast duplicate detection using
    vectorized NumPy operations.

    Attributes:
        settings (AppSettings): Global configuration for paths and parameters.
        logger (logging.Logger): Logger instance for hashing operations.
        hash_type (str): The name of the hashing algorithm (e.g., 'dhash').
        core_size (int): The resolution used for image resizing.
        threshold (int): The distance threshold in bits for duplicate detection.
        cache_io (CacheIO): Tool for saving and loading hash data from disk.
        n_jobs (int): Number of parallel processes for hash computation.
    """
    def __init__(
        self,
        settings: AppSettings,
        cache_io: Optional[CacheIO] = None
    ):
        """
        Initializes the hasher with project settings and cache handler.

        Args:
            settings (AppSettings): Configuration containing defaults and CLI arguments.
            cache_io (Optional[CacheIO]): Instance for cache persistence.
                If None, a new CacheIO instance is created.
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
        """
        Abstract method to calculate a hash for a single image.

        Args:
            image_path (Path): Path to the image file.
            core_size (int): Resolution for resizing before hashing.

        Returns:
            np.ndarray: A 1D boolean array representing the image hash.
        """
        pass


    def validate_hash_map(
            self,
            image_paths: Tuple[Path],
            hash_map: Dict[Path, np.ndarray]
    ) -> Tuple[bool, Dict[Path, np.ndarray]]:
        """
        Synchronizes the loaded cache with the current files in the directory.

        It removes hashes for files that no longer exist and triggers
        re-calculation for new files found on the disk.

        Args:
            image_paths (Tuple[Path]): Current list of image paths from the folder.
            hash_map (Dict[Path, np.ndarray]): The hash map loaded from cache.

        Returns:
            Tuple[bool, Dict[Path, np.ndarray]]: A tuple containing a sync
                status (True if matches 1:1) and the updated hash map.
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
        Computes hashes for a list of images using multiple CPU cores.

        Args:
            image_paths (Tuple[Path, ...]): List of images that need new hashes.

        Returns:
            list: A list of generated NumPy arrays (hashes).
        """
        hash_func = partial(self.__class__.compute_hash, core_size=self.core_size)

        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            hashes = list(executor.map(hash_func, image_paths))

        return hashes


    @staticmethod
    def _df_to_hash_map(df: pd.DataFrame) -> Dict[Path, np.ndarray]:
        """Internal helper: Converts Parquet DataFrame back to Hashing format."""
        if df.empty:
            return {}
        data = {
            Path(row['path']): np.array(row['hash'], dtype=bool)
            for _, row in df.iterrows()
        }
        return data


    def get_hashmap(self, image_paths: Tuple[Path]) -> Dict[Path, np.ndarray]:
        """
        Orchestrates the process of obtaining hashes for the entire directory.

        It attempts to load data from cache, validates it against the current
        files, and computes any missing hashes in parallel.

        Args:
            image_paths (Tuple[Path]): All image paths to be processed.

        Returns:
            Dict[Path, np.ndarray]: A complete dictionary of paths and their hashes.
        """
        if not image_paths:
            return {}

        image_count = len(image_paths)
        filename = self.cache_io.generate_cache_filename(
            image_paths[0].parent.resolve(),
            cache_name=self.settings.cache_name,
            hash_type=self.hash_type,
            core_size=self.core_size,

        )

        cache_file_name = self.settings.cache_file_path / filename
        cache_file_name.parent.mkdir(parents=True, exist_ok=True)
        df = self.cache_io.load(cache_file_name)

        hash_map  = self._df_to_hash_map(df)

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
        Finds similar images using vectorized Hamming distance comparison.

        This method converts the hash map into a matrix and compares all
        images against each other. It optimizes the search by skipping
        already identified duplicates.

        Args:
            hashmap (Dict[Path, np.ndarray]): Dictionary of paths and hashes.

        Returns:
            List[Path]: A list of file paths identified as duplicates.

        Raises:
            ValueError: If hashes in the map have different lengths.
        """
        if not hashmap:
            return []

        self.logger.info(f"Vectorizing comparison for {len(hashmap)} images...")
        paths: List[Path] = list(hashmap.keys())

        try:
            matrix = np.array(list(hashmap.values()), dtype=bool)
        except ValueError as e:
            msg = "Failed to create matrix. Some hashes have different lengths!"
            self.logger.error(msg)
            raise ValueError(msg)

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
        """int: The resolution used for resizing images before hashing."""
        return self._core_size

    @core_size.setter
    def core_size(self, value: Union[Tuple[int, int], int, float, str]) -> None:
        """
        Sets the core size and updates the bit-based threshold accordingly.

        Args:
            value: The new size value (int, float, str, or tuple).

        Raises:
            TypeError: If the value cannot be converted to an integer.
        """
        try:
            if isinstance(value, tuple):
                new_size = int(value[0]) if value[0] > 0 else int(value[1])
            else:
                new_size = int(float(value))

            self._core_size = new_size

            if hasattr(self, '_threshold_pct'):
                self._recalculate_threshold_bits(self._threshold_pct)

        except (ValueError, TypeError, IndexError) as e:
            msg = f"Invalid core_size type: {type(value)}. Using default."
            self.logger.error(msg)
            raise TypeError(msg)

    @property
    def threshold(self) -> int:
        """int: The current distance threshold measured in bits."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: Union[float, int, str]) -> None:
        """
        Sets the threshold as a percentage and converts it into bits.

        Args:
            value: Minimal percentage difference to consider images as unique.

        Raises:
            ValueError: If the percentage is not between 0 and 100.
        """
        try:
            pct_value = float(value)
        except (ValueError, TypeError) as e:
            msg = f"Threshold must be a number, got {type(value)}"
            self.logger.error(msg)
            raise ValueError(msg)

        if not (0 <= pct_value <= self.settings.max_percentage):
            msg = f"Threshold percentage out of range [0-100]: {pct_value}"
            self.logger.error(msg)
            raise ValueError(msg)

        self._threshold_pct = pct_value
        self._recalculate_threshold_bits(pct_value)

    def _recalculate_threshold_bits(self, percentage: float) -> None:
        """
        Internal helper to convert a percentage threshold into absolute bits.

        Args:
            percentage (float): The threshold percentage (0-100).
        """
        hash_sqr = self.core_size * self.core_size
        self._threshold = int(hash_sqr * (percentage / self.settings.max_percentage))
        self.logger.debug(f"Threshold recalculated: {percentage}% of {hash_sqr} bits = {self._threshold} bits")

    @property
    def n_jobs(self) -> int:
        """int: The number of parallel worker processes."""
        return self._n_jobs

    @n_jobs.setter
    def n_jobs(self, value: Union[int, float, str]) -> None:
        """
        Safely sets the number of workers based on the system's CPU count.

        It ensures at least 1 worker is used and caps the value to
        (CPU count - 1) to keep the system responsive.
        """
        if not isinstance(value, int):
            try:
                value = int(float(value))
            except TypeError:
                msg = f"n_jobs must be int, got {type(value)}"
                self.logger.error(msg)
                raise TypeError(msg)
            except ValueError:
                msg = f"n_jobs must be real number, got {type(value)}"
                self.logger.error(msg)
                raise ValueError(msg)

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
