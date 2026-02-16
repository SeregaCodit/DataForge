import argparse
import time

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Union, Optional

from const_utils.default_values import AppSettings
from logger.logger import LoggerConfigurator


class FileOperation(ABC):
    """
    Abstract base class for all file operations.

    This class provides a common structure for tasks like moving, deleting,
    or processing files. It manages configuration, directory validation,
    logging, and the main execution loop.

    Attributes:
        settings (AppSettings): The global settings object with default values.
        command (str): Name of the operation being executed.
        sleep (float): Time in seconds to wait between cycles if 'repeat' is True.
        repeat (bool): If True, the operation runs in a continuous loop.
        files_for_task (Tuple[Path]): A collection of files found for processing.
        pattern (tuple): File extensions or keywords to match files for processing.
        source_directory (Path): The directory to search for files for processing.
        target_directory (Path): The directory where results are saved.
        stop (bool): A flag to stop the execution loop.
        logger (logging.Logger): Logger instance for the specific operation.
    """
    def __init__(self, settings: AppSettings, **kwargs):
        """
        Initializes the operation with settings and specific arguments.

        Args:
            settings (AppSettings): Global configuration instance.
            **kwargs (dict): Arguments from the command line, such as 'src', 'dst',
                'command', and 'log_path'.
        """
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
        """
        Scans the source directory for files that match the given patterns.

        Args:
            source_directory (Path): The folder to search in.
            pattern (Union[Tuple[str], Tuple[str, ...]]): A tuple of strings
                to match filenames (e.g., ('.jpg', '.png')).

        Returns:
            Tuple[Path]: A tuple containing Path objects of the found files.
        """
        files = set()

        for p in pattern:
            current_pattern_files = source_directory.glob(f"*{p}*")
            files.update(current_pattern_files)

        files_for_task = tuple(file.resolve() for file in files)
        self.logger.debug(f"Total files_for_task: {len(files_for_task)}")
        return files_for_task


    def check_source_directory(self) -> None:
        """
        Validates that the source directory exists on the file system.

        Raises:
            FileNotFoundError: If the source path does not exist.
        """
        if not self.source_directory.exists():
            msg = f"Source path '{self.src}' does not exist."
            self.logger.error(msg)
            raise FileNotFoundError(msg)


    def check_directories(self) -> None:
        """
        Checks the source directory and ensures the target directory exists.

        If the target directory is missing, it creates it automatically with all parents.
        """
        self.check_source_directory()
        self.target_directory.mkdir(parents=True, exist_ok=True)


    def run(self) -> None:
        """
        Starts the main execution lifecycle of the operation.

        This method handles the directory checks and enters a loop if 'repeat'
        is enabled. It calls 'do_task' for the actual work and handles
        KeyboardInterrupt for safe stopping.
        """
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
        """
        Abstract method to define specific CLI arguments for the operation.

        Args:
            settings (AppSettings): To provide default values for arguments.
            parser (argparse.ArgumentParser): The subparser for the command.
        """
        pass

    @abstractmethod
    def do_task(self):
        """Abstract method where the main logic of the operation is implemented."""
        pass

    @property
    def sleep(self):
        """float: Returns the sleep interval in seconds."""
        return self._sleep

    @sleep.setter
    def sleep(self, value):
        """Sets the sleep interval and ensures it is an integer."""
        self._sleep = int(float(value))

    @property
    def pattern(self):
        """tuple: Returns the file matching patterns."""
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        """Sets the pattern. Converts a single string into a tuple if necessary."""
        if isinstance(value, str):
            self._pattern = (value, )
        else:
            self._pattern = value

    @property
    def stop(self) -> bool:
        """bool: Returns the status of the stop flag."""
        return self.__stop

    @stop.setter
    def stop(self, value):
        """Sets the stop flag status."""
        self.__stop = value

    @property
    def target_directory(self):
        """Path: Returns the directory where results are processed."""
        return self._target_directory

    @target_directory.setter
    def target_directory(self, value: Union[Path, str, None]) -> None:
        """
        Sets the target directory and converts strings to Path objects.

        If no value is provided (None), the source directory is used as the target.

        Args:
            value (Union[Path, str, None]): The path to the target folder.

        Raises:
            TypeError: If the value type is not Path, str, or None.
        """
        if value is None:
            self._target_directory = self.source_directory
        elif isinstance(value, Path):
            self._target_directory = value
        elif isinstance(value, str):
            self._target_directory = Path(value)
        else:
            msg = f"Target directory '{value}' is not valid. Got type '{type(value)}'"
            self.logger.error(msg)
            raise TypeError(msg)