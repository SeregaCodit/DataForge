import argparse
import time

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Union, Optional

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator


class FileOperation(ABC):
    """Abstract class for file operations"""
    def __init__(self, settings: AppSettings, **kwargs):
        self.settings: AppSettings = settings
        self.command: str = kwargs.get("command", "operation")
        self.sleep: float = kwargs.get('sleep', settings.sleep)
        self.repeat: bool = kwargs.get('repeat', settings.repeat)
        self.files_for_task: Tuple[Union[Path]] = tuple()
        self.pattern: tuple = kwargs.get('pattern', settings.pattern)
        self.src: str = kwargs.get('src', '')
        self.dst: str = kwargs.get('dst', '')
        self.source_directory = Path(self.src)
        self.target_directory = self.dst
        self.stop: bool = False

        # -----логування-----
        log_file = self.command
        log_level = kwargs.get("log_level", settings.log_level)
        self.log_path = kwargs.get("log_path", settings.log_path)

        self.logger = LoggerConfigurator.setup(
            name=self.__class__.__name__,
            log_level=log_level,
            log_path=Path(self.log_path) / f"{log_file}.log" if self.log_path else None
        )
        self.logger.info(f"Started with parameters: {kwargs}")


    def get_files(self, source_directory: Path, pattern: Union[Tuple[str], Tuple[str, ...]]) -> Tuple[Path]:
        """Get files from source directory that match a set of patterns"""
        files = set()

        for p in pattern:
            current_pattern_files = source_directory.glob(f"*{p}*")
            files.update(current_pattern_files)

        files_for_task = tuple(files)
        self.logger.debug(f"Total files_for_task: {len(files_for_task)}")
        return files_for_task

    def check_source_directory(self) -> None:
        """Check if source directory is valid"""
        if not self.source_directory.exists():
            # print(f"[ERROR] Source path '{self.src}' does not exist.")
            self.logger.error(f"Source path '{self.src}' does not exist.")
            raise FileNotFoundError(f"Source path '{self.src}' does not exist.")

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
                self.files_for_task = self.get_files(source_directory=self.source_directory, pattern=self.pattern)

                if len(self.files_for_task) == 0 and self.repeat:
                    self.logger.info(f"No files found for task'{self.pattern}'. Wait for {self.sleep} seconds...")
                    time.sleep(self.sleep)
                    continue

                self.do_task()

            except KeyboardInterrupt:
                self.stop = True
                self.logger.info(f"Ctrl+C pressed, stopping...")

            if self.stop or not self.repeat:
                self.logger.info(f"Finished\n{'-' * 10}\n")
                break

    @staticmethod
    @abstractmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
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

    @property
    def target_directory(self):
        return self._target_directory

    @target_directory.setter
    def target_directory(self, value: Union[Path, str, None]) -> None:
        if value is None:
            self._target_directory = self.source_directory
        elif isinstance(value, Path):
            self._target_directory = value
        elif isinstance(value, str):
            self._target_directory = Path(value)
        else:
            self.logger.error(f"Target directory '{value}' is not valid. Got type '{type(value)}'")
            raise TypeError(f"Target directory '{value}' is not valid. Got type '{type(value)}'")