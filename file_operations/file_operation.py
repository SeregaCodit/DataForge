import argparse
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Union


class FileOperation(ABC):
    """Abstract class for file operations"""
    def __init__(self, **kwargs):
        self.sleep: float = kwargs.get('sleep', 60)
        self.repeat: bool = kwargs.get('repeat', False)
        self.files_for_task: Tuple[Union[Path]] = tuple()
        self.pattern: tuple = kwargs.get('pattern', ())
        self.src: str = kwargs.get('src', '')
        self.dst: str = kwargs.get('dst', '')

        # for key, value in kwargs.items():
        #     setattr(self, key, value)

        self.source_directory = Path(self.src)
        self.target_directory = Path(self.dst)
        self.stop: bool = False

    def get_files(self) -> None:
        """Get files from source directory that match a set of patterns"""
        files = set()

        for p in self.pattern:
            current_pattern_files = self.source_directory.glob(f"*{p}*")
            files.update(current_pattern_files)

        self.files_for_task = tuple(files)

    def check_source_directory(self) -> None:
        """Check if source directory is valid"""
        if not self.source_directory.exists():
            print(f"[ERROR] Source path '{self.src}' does not exist.")
            raise FileNotFoundError

    def check_directories(self) -> None:
        """Check if source directory is valid and if target directory exists.
        If target directory does not exist - create it."""
        self.check_source_directory()
        self.target_directory.mkdir(parents=True, exist_ok=True)


    def run(self) -> None:
        """Run the file operation"""
        self.check_directories()
        while True:
            try:
                self.get_files()

                if len(self.files_for_task) == 0:
                    print(f"[!] No files found in {self.source_directory}. Waiting {self.sleep} seconds.", end="\n",
                          flush=True)
                    time.sleep(self.sleep)
                    continue

                self.do_task()

            except KeyboardInterrupt:
                self.stop = True
                print("\nCtrl+C pressed, stopping move.")

            if self.stop or not self.repeat:
                break

    @staticmethod
    @abstractmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add specific arguments for operation"""
        pass

    @abstractmethod
    def do_task(self):
        """Abstract method to do a task of a file operation"""
        pass

    @property
    def sleep(self):
        return self._sleep

    @sleep.setter
    def sleep(self, value):
        self._sleep = int(value)

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        if isinstance(value, str):
            self._pattern = (value, )
        else:
            self._pattern = value

    @property
    def stop(self) -> bool:
        return self.__stop

    @stop.setter
    def stop(self, value):
        self.__stop = value
