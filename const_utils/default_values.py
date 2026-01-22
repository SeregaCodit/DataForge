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