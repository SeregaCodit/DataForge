from dataclasses import dataclass
from typing import Union


@dataclass
class DefaultValues:
    """Default values of positional arguments"""
    pattern: tuple = ()
    sleep: Union[int, bool] = 60
    type: str = ".jpg"