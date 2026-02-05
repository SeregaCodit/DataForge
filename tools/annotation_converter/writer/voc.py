from pathlib import Path
from typing import List

from tools.annotation_converter.writer.base import BaseWriter

class XMLWriter(BaseWriter):
    """
        writes .xml annotations for Pascal VOC dataset.
    """

    def write(self, data: str, file_path: Path) -> dict:
        """
        writes .xml annotation file for Pascal VOC dataset to file_path.
            Params:
                data: str - a string with xml annotation data
                file_path: Path - path to annotation file
        """
        with open(file_path, "w") as file:
            file.write(data)