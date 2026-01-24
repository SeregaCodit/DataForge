from dataclasses import dataclass
from const_utils.default_values import DefaultValues as defaults, DefaultValues
from logger.log_level_mapping import LevelMapping


@dataclass
class HelpStrings:
    """Help strings for commands and arguments"""
    move: str = "move files from source directory to target directory"
    delete: str = "delete files that match patterns from source directory"
    slice: str = "slice video files to images from the source directory to the target directory"
    src: str = "source directory"
    dst: str = "destination directory"
    pattern: str = r"Default - " + str(defaults.pattern) + ". Do actions only with files that match pattern"
    repeat: str = "Should task will be repeated after finishing"
    sleep: str = (
        "Default - " + str(defaults.sleep) + ". Time in seconds that script will sleep if no files for task in source"
        " directory"
    )
    step_sec: str = "time interval in seconds between each step"
    type: str = "destination type of file"
    remove: str = "remove files after processing"
    log_path: str = f"Default: {defaults.log_path} path to log directory"
    log_level: str = f"Default: {defaults.log_level}. A level of logging matches mapping: {str(LevelMapping.mapping())}"
    filetype: str = "Type of file. Currently this parameter only supports 'image'"
    method: str = "Default: dhash. A method of comparing images. It's can be ['phash, dhash, ahash, cnn]"
    action: str = (f"Default: {DefaultValues.action}.\n"
                   f"copy: copying non duplicates to destination directory, all files stay in same directory"
                   f"delete: deleting duplicates from source directory. All non duplicates files will be stay in same directory")
    threshold: str = (f"Default: {DefaultValues.hash_threshold}. A minimal difference between files that means the files"
                      f" have a different information. Using Hemming distance for *hash methods")