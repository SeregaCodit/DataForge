from pathlib import Path

from tools.annotation_converter.reader.base import BaseReader

class TXTReader(BaseReader):
    """Parse yolo annotations (.txt format) Returns a dict of annotation data"""

    def build_class_map(self, classes_file: Path) -> dict:
        """
        Build a map of class names and corresponding class ids
            Params:
                classes_file: Path - a path to classes.txt file
        """
        pass

    def read(self, file_path: Path) -> dict:
        """
        Params:
            file_path: Path - path to .txt yolo annotation file

        """
        with open(file_path, "r") as file:
            text = file.read()

        data = {}
        return data