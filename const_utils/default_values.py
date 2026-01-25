from dataclasses import dataclass
from pathlib import Path
from typing import Union

from logger.log_level_mapping import LevelMapping


@dataclass
class DefaultValues:
    """Default values of positional arguments"""
    remove = False
    pattern: tuple = ()
    sleep: Union[int, bool] = 60
    type: str = ".jpg"
    step_sec: float = 600
    log_path: Path = Path("./log")
    log_level: str = LevelMapping.info
    image: str = "image"
    phash: str = "phash"
    ahash: str = "ahash"
    dhash: str = "dhash"
    cnn: str = "cnn"
    action: str = "copy"
    hash_threshold: str = 10
    max_percentage: int = 100
    confirm_choice: tuple = ("delete", "вудуеу", "yes", "y", "true", "t", "1")
    core_size: int = 16
    max_workers: int = 4