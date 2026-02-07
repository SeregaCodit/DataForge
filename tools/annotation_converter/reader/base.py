from abc import ABC, abstractmethod
from pathlib import Path


class BaseReader(ABC):
    """
    Abstract base class for all data readers in DataForge.

    This class defines the standard interface for reading and parsing
    annotation files of different formats (such as XML for Pascal VOC
    or TXT for YOLO). Every specific reader must implement the 'read' method.
    """
    def __init__(self):
        """ Initializes the base reader instance. """
        pass

    @abstractmethod
    def read(self, file_path: Path) -> dict:
        """
        Reads an annotation file and converts its content into a dictionary.

        Args:
            file_path (Path): The path to the source file to be read.

        Returns:
            dict: A dictionary containing the structured data from the file.

        Raises:
            FileNotFoundError: If the file does not exist at the specified path.
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass