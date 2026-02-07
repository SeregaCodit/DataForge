import json
import multiprocessing

from typing import Union, Tuple, Optional, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

from const_utils.copmarer import Constants
from logger.log_level_mapping import LevelMapping


class AppSettings(BaseSettings):
    """
    Centralized configuration management for the DataForge toolkit.

    This class defines all the parameters used by the application, including
    file paths, hashing settings, and execution intervals. It uses Pydantic v2
    to automatically validate types, enforce value limits, and load
    configuration from JSON files or environment variables.

    Attributes:
        max_percentage (int): Constant used for percentage calculations (default: 100).
        remove (bool): If True, source files will be deleted after processing.
        pattern (Tuple[str, ...]): Patterns used to find specific files.
        repeat (bool): If True, the operation runs in a continuous loop.
        sleep (Union[int, bool]): Seconds to wait between operation cycles.
        suffix (str): The file extension used for output files.
        step_sec (float): Time interval in seconds for video slicing.
        log_path (Path): Directory where log files are stored.
        log_level (str): Verbosity level of the logger (e.g., INFO, DEBUG).
        filetype (str): The category of files being processed (e.g., image).
        method (str): The algorithm name for hashing or comparison.
        hash_threshold (int): Distance threshold for identifying duplicates (0-100).
        confirm_choice (tuple): Keywords used to confirm interactive deletion.
        core_size (int): Resolution for hashing; must be a power of 2.
        n_jobs (int): Number of parallel workers; capped by system CPU count.
        cache_file_path (Path): Directory for storing persistent hash caches.
        cache_name (Optional[Path]): Custom name for the cache file.
        a_suffix (Tuple[str, ...]): File patterns specific to annotations.
        a_source (Optional[Path]): Directory where annotation files are located.
        destination_type (Optional[str]): Target format for annotation conversion.
        extensions (Tuple[str, ...]): Supported image file extensions.
    """
    max_percentage: int = 100
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        extra="ignore",
        validate_assignment=True
    )

    remove: bool = Field(default=False)
    pattern: Tuple[str, ...] = Field(default_factory=tuple)
    repeat: bool = Field(default=False)
    sleep: Union[int, bool] = Field(default=60, ge=0)
    suffix: str = Field(default=".jpg")
    step_sec: float = Field(default=1.0, ge=0.1)
    log_path: Path = Field(default=Path("./log"))
    log_level: str = Field(default=LevelMapping.info)
    filetype: str = Field(default=Constants.image)
    method: str = Field(default=Constants.dhash)
    hash_threshold: int = Field(default=10, ge=0, le=100)
    confirm_choice: tuple = Field(default=("delete",))
    core_size: int = Field(default=8, ge=8)
    n_jobs: int = Field(default=2, ge=1, le=multiprocessing.cpu_count())
    cache_file_path: Path = Field(default=Path("./cache"))
    cache_name: Optional[Path] = Field(default=None)
    a_suffix: Tuple[str, ...] = Field(default_factory=tuple)
    a_source: Optional[Path] = Field(default=None)
    destination_type: Optional[str] = Field(default=None)
    extensions: Tuple[str, ...] = Field(default=(".jpg", ".jpeg,", ".png"))


    @field_validator('core_size')
    @classmethod
    def check_power_of_two(cls, value: int) -> int:
        """
        Validates that the core_size is a power of 2.

        Args:
            value (int): The value to check.

        Returns:
            int: The validated value.

        Raises:
            ValueError: If the value is not a power of 2 (e.g., 8, 16, 32).
        """
        if value <= 0 or (value & (value - 1) != 0):
            raise ValueError(f"core_size must be a power of 2 (e.g., 8, 16, 32, 64...), got {value}")
        return value


    @field_validator("log_path", "cache_file_path", "a_source", mode='before')
    @classmethod
    def ensure_path(cls, value: Union[str, Path]) -> Path:
        """
        Converts string input into a Path object before type validation.

        Args:
            value (Union[str, Path]): The raw path input.

        Returns:
            Path: An initialized Path object.
        """
        if isinstance(value, str):
            return Path(value)
        return value


    @field_validator("n_jobs")
    @classmethod
    def ensure_n_jobs(cls, value: Union[int, str]) -> int:
        """
        Ensures the number of parallel jobs is within safe system limits.

        It prevents setting n_jobs to 0 and caps it at (CPU count - 1) to
        keep the operating system responsive.

        Args:
            value (Union[int, str]): Requested number of workers.

        Returns:
            int: A safe, adjusted number of workers.
        """
        if not isinstance(value, int):
            return int(float(value))
        elif value >= multiprocessing.cpu_count():
            return multiprocessing.cpu_count() - 1
        elif value < 1:
            return 1
        else:
            return value


    @field_validator("extensions")
    @classmethod
    def ensure_extensions(cls, value: Union[str, List[str]]) -> Tuple[str, ...]:
        """
        Ensures that file extensions are stored as a tuple of strings.

        Args:
            value (Union[str, List[str]]): Input extension data.

        Returns:
            Tuple[str, ...]: A tuple of extension strings.

        Raises:
            TypeError: If the input cannot be converted to a tuple.
        """
        if isinstance(value, tuple):
            return value
        else:
            try:
                return tuple(value)
            except TypeError as e:
                raise TypeError(e)


    @classmethod
    def load_config(cls, config_path: Path = Constants.config_file) -> "AppSettings":
        """
        Factory method to create a settings object from a JSON file.

        It attempts to read the specified JSON file. If the file is missing
        or corrupted, it falls back to the default values defined in the class.

        Args:
            config_path (Path): Path to the config.json file.

        Returns:
            AppSettings: An initialized and validated settings instance.
        """
        data = {}

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                print(f"Warning: {config_path} is corrupted. Using defaults.")

        return cls(**data)
