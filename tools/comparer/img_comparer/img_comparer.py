from pathlib import Path
from typing import Union, List
from const_utils.copmarer import Constants
from logger.logger import LoggerConfigurator
from tools.comparer.comparer import Comparer


class ImageComparer(Comparer):
    """Abstract class for comparing images"""
    def __init__(self, method_name: str = Constants.phash, log_path: Union[Path, None] = None):
        super().__init__()
        self.method_mapping = {
            Constants.phash: ...,
            Constants.dhash: ...,
            Constants.ahash: ...,
            Constants.cnn: ...
        }
        self.method = self.method_mapping[method_name]
        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )

    def compare_files(self, files: Union[Path, List[Path]], threshold: int, outfile: Path) -> dict:
        pass