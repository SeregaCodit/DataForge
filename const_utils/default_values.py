import json
import multiprocessing

from typing import Union, Tuple, Optional, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

from const_utils.copmarer import Constants
from logger.log_level_mapping import LevelMapping


class AppSettings(BaseSettings):
    max_percentage: int = 100


    model_config = SettingsConfigDict(
        env_prefix="APP_",
        # json_file=Constants.config_file,
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
        if value <= 0 or (value & (value - 1) != 0):
            raise ValueError(f"core_size must be a power of 2 (e.g., 8, 16, 32, 64...), got {value}")
        return value

    @field_validator("log_path", "cache_file_path", "a_source", mode='before')
    @classmethod
    def ensure_path(cls, value: Union[str, Path]) -> Path:
        if isinstance(value, str):
            return Path(value)
        return value

    @field_validator("n_jobs")
    @classmethod
    def ensure_n_jobs(cls, value: Union[int, str]) -> int:
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
        if isinstance(value, tuple):
            return value
        else:
            try:
                return tuple(value)
            except TypeError as e:
                raise TypeError(e)

    @classmethod
    def load_config(cls, config_path: Path = Constants.config_file) -> "AppSettings":

        data = {}

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                print(f"Warning: {config_path} is corrupted. Using defaults.")

        return cls(**data)
