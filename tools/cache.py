import hashlib
import pickle
from pathlib import Path
from typing import Union, Dict, BinaryIO, Optional
import numpy as np

from const_utils.default_values import AppSettings
from file_operations.file_remover import FileRemoverMixin
from logger.logger import LoggerConfigurator
from logger.logger_protocol import LoggerProtocol


class CacheIO:
    SUFFIX = ".pkl"
    def __init__(self, settings: AppSettings):
        """
        saving and reading cache files for faster loading data
        """
        self.settings = settings
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(self.settings.log_path) / f"{self.__class__.__name__}.log",
            log_level=self.settings.log_level
        )


    def load(self: LoggerProtocol, cache_file) -> Dict[Path, np.ndarray]:
        """loading cache file"""
        try:
            self.logger.info(f"Loading cache file {cache_file}")
            with open(cache_file, "rb") as file:
                return pickle.load(file)

        except FileNotFoundError:
            self.logger.warning(f"Cache file {cache_file} does not exist")
            return {}
        except EOFError:
            self.logger.warning(f"Cache file {cache_file} is damaged. Deleting cache file")
            return {}

    def save(self: LoggerProtocol, hash_map: Dict[Path, np.ndarray], cache_file: Path) -> None:
        """save hashmap to cache file"""
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Saving cache file {cache_file}")

        with open(cache_file, 'wb') as file:
            pickle.dump(hash_map, file)

        self.logger.info(f"Cache file {cache_file} saved")

    @classmethod
    def generate_cache_filename(cls, source_path: Path, hash_type: str, core_size: int, cache_name: Optional[Path]) -> str:
        """generate cache filename from source_path """
        suffix = f"{hash_type}_s{core_size}{cls.SUFFIX}"
        if cache_name is None:
            abs_path = str(source_path.resolve())
            path_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
            folder_name = str(source_path.name.replace(' ', '_').strip("."))[:30]
            return f"cache_{path_hash}_d{folder_name}{suffix}"
        else:
            cache_name = str(cache_name).replace(" ", "_").strip(".")
            if cache_name.endswith(cls.SUFFIX):
                cache_name = cache_name[:-len(cls.SUFFIX)]

            cache_name = f"{cache_name}_{suffix}"
            return cache_name
