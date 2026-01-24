from pathlib import Path
from typing import Union, List, Optional, Tuple

from const_utils.copmarer import Constants
from logger.logger import LoggerConfigurator
from tools.hasher.dhash import DHash



class ImageComparer:
    def __init__(
            self,
            method_name: str = Constants.phash,
            log_path: Union[Path, None] = None,
            threshold_percentage: float = 10,
    ):
        """
        An orchestrator for comparing two images using principial different algorithms.
        :param method_name: duplicate search method name
        :param log_path: path to log file
        :param threshold_percentage: percentage of duplicate hash value to consider as duplicate
        """
        super().__init__()
        self.method_mapping = {
            Constants.dhash: DHash,
        }

        self.method = self.method_mapping[method_name](
            hash_size=16,
            threshold=threshold_percentage
        )

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )

    def compare(self, file_paths: Tuple[Path]):
        """
        compare files via each-with-each method
        :param file_paths: paths of files to be compared
        :return: matches that satisfy threshold condition
        """
        hash_map = self.method.get_hashmap(file_paths)
        matches = self.method.find_duplicates(hash_map)
        return matches
