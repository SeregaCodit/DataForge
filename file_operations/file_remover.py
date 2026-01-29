from pathlib import Path
from typing import Union, List, Tuple

from logger.logger_protocol import LoggerProtocol


class FileRemoverMixin:
    """internal helper for file removing functionality"""
    def _remove_all(self, filepaths: Union[List[Path], Tuple[Path], Path]) -> None:
        """deletes all received files"""
        if isinstance(filepaths, (list, tuple)):
            for path in filepaths:
                self._remove_file(path)

        elif isinstance(filepaths, Path):
            self._remove_file(filepaths)

        else:
            raise TypeError(f'filepaths should be a list or a tuple or a Path, not {type(filepaths)}')


    def _remove_file(self: LoggerProtocol, path: Path) -> bool:
        """deletes one received file. Returns True or False if file was successfully removed or not"""
        if not path.is_file():
            self.logger.warning(f"{path} is not a file")
        try:
            path.unlink(missing_ok=True)
            self.logger.info(f"{path} removed")
            return True
        except FileNotFoundError:
            self.logger.warning(f"{path} file not exists, skipping")
            return False
