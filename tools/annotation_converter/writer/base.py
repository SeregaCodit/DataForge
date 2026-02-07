from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union


class BaseWriter(ABC):
    """
    Abstract base class for all data writers in DataForge.

    This class defines the standard interface for saving processed annotation
    data into various file formats (such as YOLO .txt or Pascal VOC .xml).
    Specific writer implementations must provide their own 'write' logic.
    """
    def __init__(self):
        """ Initializes the base writer instance. """
        pass


    @abstractmethod
    def write(self, data: Union[tuple, list, dict, str], file_path: Path) -> None:
        """
        Writes data to the specified file path.

        Args:
            data (Union[tuple, list, dict, str]): The content to be written (can be a list, dictionary, or string
                depending on the specific writer).
            file_path (Path): The target path where the file will be saved.

        Raises:
            IOError: If the file cannot be written to the disk.
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass
