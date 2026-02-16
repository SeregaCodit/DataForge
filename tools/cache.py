import hashlib
from pathlib import Path
from typing import Dict, Optional, Union, Any
import numpy as np
import pandas as pd

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator
from logger.logger_protocol import LoggerProtocol


class CacheIO:
    """
    Handles high-performance data persistence using Apache Parquet.

    This class provides methods to save and load complex data structures like
    image hash maps or pandas DataFrames. It optimizes I/O performance
    and ensures data integrity across different operations.

    Attributes:
        SUFFIX (str): The standard file extension for cache files (.parquet).
        settings (AppSettings): Global configuration instance.
        logger (logging.Logger): Logger instance for tracking I/O operations.
    """
    SUFFIX = ".parquet"

    def __init__(self, settings: AppSettings):
        """
        Initializes CacheIO with the provided application settings.

        Args:
            settings (AppSettings): Application configuration for paths and logging.
        """
        self.settings = settings
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(self.settings.log_path) / f"{self.__class__.__name__}.log",
            log_level=self.settings.log_level
        )


    def load(self: LoggerProtocol, cache_file: Path) -> pd.DataFrame:
        """
        Loads data from a parquet cache file into a DataFrame.

        Args:
            cache_file (Path): The path to the .parquet file.

        Returns:
            pd.DataFrame: The loaded data or an empty DataFrame if the file
                is missing or corrupted.
        """
        if not cache_file.exists():
            self.logger.warning(f"Cache file {cache_file} does not exist")
            return pd.DataFrame()

        try:
            self.logger.info(f"Loading cache file {cache_file}")
            df = pd.read_parquet(cache_file)

            return df
        except Exception as e:
            self.logger.error(f"Cache file {cache_file.name} is corrupted: {e}. Deleting.")
            cache_file.unlink(missing_ok=True)
            return pd.DataFrame()


    def save(self: LoggerProtocol, data_map: Union[Dict[Path, np.ndarray], pd.DataFrame], cache_file: Path) -> None:
        """
        Saves a dictionary of hashes or a pandas DataFrame to a parquet file.

        Args:
            data_map (Union[Dict[Path, np.ndarray], pd.DataFrame]): Data to store.
            cache_file (Path): Target path for the cache file.

        Raises:
            TypeError: If the data_map is not a dictionary or a DataFrame.
        """
        empty_msg = "data_map is empty, skipping saving cache data"

        if isinstance(data_map, dict):
            if not data_map:
                self.logger.warning(empty_msg)
                return
            data = [
                {'path': str(p), 'hash': h.tolist()}
                for p, h in data_map.items()
            ]
            df = pd.DataFrame(data)

        elif isinstance(data_map, pd.DataFrame):
            if data_map.empty:
                self.logger.warning(empty_msg)
                return
            df = data_map
        else:
            msg = f"data_map must be either a dictionary or a DataFrame, got {type(data_map)}"
            self.logger.warning(msg)
            raise TypeError(msg)

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Saving {len(data_map)} hashes to {cache_file.name}")

        try:
            df.to_parquet(cache_file, engine="pyarrow", compression="snappy", index=False)
            self.logger.info(f"Cache saved successfully to {cache_file}.")
        except Exception as e:
            self.logger.error(f"Critical error saving cache: {e}")


    @classmethod
    def generate_cache_filename(cls, source_path: Path, cache_name: Optional[Union[str, Path]], **kwargs: Any) -> str:
        """
        Generates a unique, versioned filename for the cache.

        Args:
            source_path (Path): The directory path being processed.
            cache_name (Optional[Union[str, Path]]): A custom name for the file.
            **kwargs (dict): Key-value pairs to include in the versioning (e.g., core_size=16).

        Returns:
            str: A stable and unique filename string.
        """
        param_suffix = "".join([f"_{key}_{value}" for key, value in kwargs.items()])
        full_suffix = f"{param_suffix}{cls.SUFFIX}"

        if cache_name is None:

            abs_path = str(source_path.resolve())
            path_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
            folder_name = str(source_path.name.replace(' ', '_').strip("."))[:30]
            return f"cache_{path_hash}_{folder_name}{full_suffix}"
        else:
            cache_name = str(cache_name).replace(" ", "_").strip(".")
            if cache_name.endswith(cls.SUFFIX):
                cache_name = cache_name[:-len(cls.SUFFIX)]

            cache_name = f"{cache_name}_{full_suffix}"
            return cache_name
