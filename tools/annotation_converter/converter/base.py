from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from logger.log_level_mapping import LevelMapping
from logger.logger import LoggerConfigurator
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.reader.voc import XMLReader


class BaseConverter(ABC):
    def __init__(self, log_level: str = LevelMapping.debug, log_path: Optional[Path] = None):

        self._reader: Optional[BaseReader] = None
        self.reader_mapping = {
            ".xml": XMLReader,
        }

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=log_level,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )
        

    @abstractmethod
    def read(self, source_path: str) -> str:
        pass

    @abstractmethod
    def convert(self, file_path: Path) -> str:
        pass
    
    @property
    def reader(self) -> BaseReader:
        return self._reader
    
    @reader.setter
    def reader(self, reader: BaseReader) -> None:
        self._reader = reader