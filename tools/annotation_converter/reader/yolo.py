from pathlib import Path

from tools.annotation_converter.reader.base import BaseReader

class TXTReader(BaseReader):
    """
    A reader class for parsing YOLO-style text files (.txt).

    This class reads raw text data from YOLO annotations or class list files
    and transforms the content into a dictionary format suitable for
    DataForge processing.
    """

    def read(self, file_path: Path) -> dict:
        """
        Reads a YOLO text file and converts its lines into a dictionary.

        Each non-empty line in the file becomes a key in the dictionary,
        and its line position (index as a string) becomes the corresponding value.

        Args:
            file_path (Path): The path to the source .txt annotation file.

        Returns:
            dict: A dictionary where keys are text lines and values are their
                string indices.

        Raises:
            FileNotFoundError: If the .txt file cannot be found at the given path.
        """
        with open(file_path, "r") as file:
            text = file.read()

        data = {key: str(value) for value, key in enumerate(text.split("\n")) if key}
        return data