from abc import ABC, abstractmethod
from pathlib import Path


class BaseReader(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def read(self, file_path: Path) -> dict:
        pass