from pathlib import Path
from typing import Union, List, Optional

from imagededup.methods import PHash, AHash, DHash, CNN

from const_utils.copmarer import Constants
from logger.logger import LoggerConfigurator



class ImageComparer:
    """Abstract class for comparing images"""
    def __init__(self, method_name: str = Constants.phash, log_path: Union[Path, None] = None):
        super().__init__()
        self.method_mapping = {
            Constants.phash: PHash,
            Constants.dhash: DHash,
            Constants.ahash: AHash,
            Constants.cnn: CNN
        }
        self.method = self.method_mapping[method_name]()
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )
        self.outfile = Path(log_path) / f"{self.__class__.__name__}.json" if log_path else None

    def compare_files(self, image_dir: Path, threshold: int = 10) -> list:
        duplicates = self.method.find_duplicates_to_remove(
            image_dir=image_dir,
            max_distance_threshold=threshold,
            outfile=self.outfile
        )
        self.logger.info(f"Duplicates: [{len(duplicates)}] {duplicates}")
        return duplicates