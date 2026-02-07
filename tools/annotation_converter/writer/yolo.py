from pathlib import Path
from typing import List

from tools.annotation_converter.writer.base import BaseWriter


class YoloWriter(BaseWriter):
    """
    A writer class for saving annotations in the YOLO text format (.txt).

    This class takes a list of processed annotation strings and saves them
    into a text file. It ensures that each object is written on a new line
    and handles the creation of necessary directories.
    """
    def write(self, data: List[str], file_path: Path) -> None:
        """
        Writes a list of strings to a YOLO-formatted text file.

        This method automatically creates any missing parent directories.
        It filters out empty lines and adds a newline character after
        each record.

        Args:
            data (List[str]): A list of strings, where each string represents
                an object (class_id, x_center, y_center, width, height).
            file_path (Path): The target file path where the annotation
                will be saved.

        Returns:
            None: This method does not return any value.

        Raises:
            IOError: If there is a problem creating the directory or writing
                the file.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as file:
            file.writelines(f"{line}\n" for line in data if line)
