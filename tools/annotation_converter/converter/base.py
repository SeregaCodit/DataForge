from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from logger.log_level_mapping import LevelMapping
from logger.logger import LoggerConfigurator
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.reader.voc import XMLReader
from tools.annotation_converter.reader.yolo import TXTReader
from tools.annotation_converter.writer.base import BaseWriter
from tools.annotation_converter.writer.voc import XMLWriter
from tools.annotation_converter.writer.yolo import YoloWriter


class BaseConverter(ABC):
    """
    Base converter class. Based on the source and destination formats, defines reader and writer classes for
        processing data, defines default source and destination annotation file suffixes

    """
    def __init__(
            self,
            source_format: str,
            dest_format: str,
            log_level: str = LevelMapping.debug,
            log_path: Optional[Path] = None,
            **kwargs
    ):

        self.reader_mapping = {
            ".xml": XMLReader,
            ".txt": TXTReader
        }

        self.writer_mapping = {
            ".txt": YoloWriter,
            ".xml": XMLWriter
        }

        self.suffix_mapping = {
            "voc": ".xml",
            "yolo": ".txt"
        }

        self.source_suffix = self.suffix_mapping.get(source_format)
        self.dest_suffix = self.suffix_mapping.get(dest_format)
        self.reader = self.reader_mapping[self.source_suffix]()
        self.writer = self.writer_mapping[self.dest_suffix]()

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=log_level,
            log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
        )


    @abstractmethod
    def convert(self, file_paths: Tuple[Path], target_path: Path, n_jobs: int = 1) -> None:
        pass
    
    @property
    def reader(self) -> BaseReader:
        return self._reader
    
    @reader.setter
    def reader(self, reader: BaseReader) -> None:
        self._reader = reader

    @property
    def writer(self) -> BaseWriter:
        return self._writer

    @writer.setter
    def writer(self, writer: BaseWriter) -> None:
        self._writer = writer