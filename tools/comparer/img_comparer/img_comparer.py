from pathlib import Path
from typing import Union, List, Optional, Tuple

from const_utils.copmarer import Constants
from logger.logger import LoggerConfigurator
from tools.hasher.dhash import DHash



class ImageComparer:
    def __init__(
            self,
            method_name: str = Constants.phash,
            log_path: Union[Path, None] = None
    ):
        super().__init__()
        self.method_mapping = {
            Constants.dhash: DHash,
        }

        self.method = self.method_mapping[method_name]()

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )

    def compare(self, file_paths: Tuple[Path]):
        hash_map = self.method.get_hashmap(file_paths)
        duplicates = self.method.find_duplicates(hash_map)
        return duplicates
