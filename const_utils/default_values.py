from dataclasses import dataclass
from typing import Union


@dataclass
class DefaultValues:
    pattern: tuple = ()
    sleep: Union[int, bool] = 60