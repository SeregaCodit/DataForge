from pathlib import Path
from typing import Union, Tuple

from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator
from tools.comparer.img_comparer.hasher.dhash import DHash



class ImageComparer:
    def __init__(
            self,
            # method_name: str = Constants.phash,
            # log_path: Union[Path, None] = None,
            # threshold_percentage: int = DefaultValues.hash_threshold,
            # core_size: int = DefaultValues.core_size,
            # n_jobs: int = DefaultValues.n_jobs,
            settings: AppSettings,
    ):
        """
        An orchestrator for comparing two images using principial different algorithms.
        :param settings: settings object, includes default and user's params
        """
        super().__init__()
        self.settings = settings

        self.method_mapping = {
            Constants.dhash: DHash,
        }

        self.method = self.method_mapping[self.settings.method](
            settings=self.settings,
        )

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(self.settings.log_path) / f"{self.__class__.__name__}.log" if self.settings.log_path else None,
            log_level=self.settings.log_level
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
