import os
from pathlib import Path
from typing import Union


def generate_directory_name(src: Union[Path, str]) -> Path:
    """
    Generates a new incremental directory path based on existing numeric folders.

    This function scans the source directory for subdirectories named with
    integers, finds the highest number, and increments it by one to create
    a name for the next folder. It is primarily used for versioning reports.

    Args:
        src (Union[Path, str]): The parent directory to scan for existing folders.

    Returns:
        Path: The absolute path for the new incremental directory.

    Raises:
        TypeError: If 'src' is not a Path or a string object.
        ValueError: If no numeric directories exist or if the last directory
            name cannot be converted to an integer.
    """
    if not isinstance(src, Path):
        try:
            src = Path(src)
        except TypeError:
            raise TypeError(f"src must be a Path or str object, got {type(src)}")

    existing_directories = [int(p) for p in os.listdir(src) if (src / p).is_dir()]

    if not existing_directories:
        dir_name = 1
    else:
        try:
            dir_name = int(sorted(existing_directories)[-1]) + 1
        except (ValueError, IndexError):
            dir_name = 1

    report_path = src / str(dir_name)
    return report_path.resolve()