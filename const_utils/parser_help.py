from dataclasses import dataclass
from const_utils.default_values import DefaultValues as defaults

@dataclass
class HelpStrings:
    """Help strings for commands and arguments"""
    move: str = "move files from source directory to target directory"
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