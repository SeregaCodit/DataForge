from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple


class BaseWriter(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def write(self, data: List[str], file_path: Path) -> dict:
        pass
