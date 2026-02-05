from pathlib import Path

from tools.annotation_converter.reader.base import BaseReader

class TXTReader(BaseReader):
    """Parse yolo annotations (.txt format) Returns a dict of annotation data"""

    def read(self, file_path: Path) -> dict:
        """
        Params:
            file_path: Path - path to .txt yolo annotation file

        """
        with open(file_path, "r") as file:
            text = file.read()

        data = {key: str(value) for value, key in enumerate(text.split("\n")) if key}
        return data