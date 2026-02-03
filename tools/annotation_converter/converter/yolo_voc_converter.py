from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import List, Dict, Set, Tuple

import numpy as np

from tools.annotation_converter.converter.base import BaseConverter
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.writer.base import BaseWriter


class YoloVocConverter(BaseConverter):
    TARGET_FORMAT = ".txt"
    DESTINATION_FORMAT = ".xml"

    def __init__(self):
        """
        Convert annotations from YOLO (.txt format) to VOC (.xml format)
        """
        super().__init__()
        self.reader = self.reader_mapping[self.TARGET_FORMAT]()
        self.writer = self.writer_mapping[self.DESTINATION_FORMAT]()
        self.objects: list = list()
        self.class_mapping: Dict[str, int] = dict()

    def convert(self, file_paths: Tuple[Path], target_path: Path, n_jobs: int = 1) -> None:
        print(file_paths)
        pass