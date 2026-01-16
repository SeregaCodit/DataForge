from dataclasses import dataclass
from const_utils.default_values import DefaultValues as defaults

@dataclass
class HelpStrings:
    move: str = "move files from source directory to target directory"
    src: str = "source directory"
    dst: str = "destination directory"
    pattern: str = r"Default - " + str(defaults.pattern) + ". Do actions only with files that match pattern"
    repeat: str = "Should task will be repeated after finishing"
    sleep: str = (
        "Default - " + str(defaults.sleep) + ". Time in seconds that script will sleep if no files for task in source"
        " directory"
    )