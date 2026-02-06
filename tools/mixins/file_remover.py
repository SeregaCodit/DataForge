from pathlib import Path
from typing import Union, List, Tuple

from logger.logger_protocol import LoggerProtocol


class FileRemoverMixin:
    """A helper class to delete files from the system."""
    def remove_all(self, filepaths: Union[List[Path], Tuple[Path], Path]) -> None:
        """Deletes all the files in the given iterable or path.

        Args:
            filepaths (Union[List[Path], Tuple[Path], Path]): A list of paths,
                a tuple of paths, or a single path to delete.

        Raises:
            TypeError: If the input is not a list, tuple, or Path.
        """
        if isinstance(filepaths, (list, tuple)):
            for path in filepaths:
                self.remove_file(path)

        elif isinstance(filepaths, Path):
            self.remove_file(filepaths)

        else:
            raise TypeError(f'filepaths should be a list or a tuple or a Path, not {type(filepaths)}')


    def remove_file(self: LoggerProtocol, path: Path) -> bool:
        """Deletes one file from the system.

        Args:
            path (Path): The path of the file to delete.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        if not path.is_file():
            self.logger.warning(f"{path} is not a file")
        try:
            path.unlink(missing_ok=True)
            self.logger.info(f"{path} removed")
            return True
        except FileNotFoundError:
            self.logger.warning(f"{path} file not exists, skipping")
            return False
