from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import pandas as pd
from mkdocs.config.config_options import Optional

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator
from tools.cache import CacheIO


class BaseAugmenter(ABC):
    def __init__(self, settings: AppSettings, cache_io: Optional[CacheIO] = None):
        self.settings = settings
        self.cache_io = cache_io or CacheIO(settings)

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=self.settings.log_level,
            log_path=Path(self.settings.log_path) / f"{self.__class__.__name__}.log" if self.settings.log_path else None
        )


    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info(f"Starting augmentation with method {self.settings.augment_method}")
        self.logger.debug(f"Initial data shape: {df.shape}")

        data_gaps = self.get_data_gaps(df)
        self.logger.debug(f"Identified data gaps: {data_gaps.shape}")

        candidates = self.select_candidates(data_gaps)
        self.logger.debug(f"Selected candidates for augmentation: {candidates.shape}")

        augmented_samples = self.generate_samples(candidates)
        self.logger.debug(f"Generated augmented samples: {augmented_samples.shape}")

        augmented_df = pd.concat([df, augmented_samples], ignore_index=True)
        self.logger.info(f"Augmentation completed. Final data shape: {augmented_df.shape}")

        return augmented_df


    @abstractmethod
    def get_data_gaps(self, df: pd.DataFrame, bins: int) -> pd.DataFrame:
        pass


    @abstractmethod
    def select_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


    @abstractmethod
    def generate_samples(self, df: pd.DataFrame, gaps: List, donors: pd.DataFrame, n_samples: int) -> pd.DataFrame:
        pass

