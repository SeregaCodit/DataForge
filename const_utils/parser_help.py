from dataclasses import dataclass
from logger.log_level_mapping import LevelMapping


@dataclass
class HelpStrings:
    """Help strings for commands and arguments"""
    move: str = "move files from source directory to target directory"
    delete: str = "delete files that match patterns from source directory"
    slice: str = "slice video files to images from the source directory to the target directory"
    src: str = "source directory"
    dst: str = "destination directory"
    pattern: str = r"Do actions only with files that match pattern"
    repeat: str = "Should task will be repeated after finishing"
    sleep: str = "Time in seconds that script will sleep if no files for task in source directory"
    step_sec: str = "time interval in seconds between each step"
    type: str = "destination type of file"
    remove: str = "remove files after processing"
    log_path: str = "path to log directory"
    log_level: str = f"A level of logging matches mapping: {str(LevelMapping.mapping())}"
    datatype: str = "Type of data. Currently this parameter only supports 'image'"
    method: str = "Default: dhash. A method of comparing images. It's can be ['phash, dhash, ahash, cnn]"
    threshold: str = ("A minimal difference between files that means the files"
                      f" have a different information. Using Hemming distance for *hash methods")
    core_size: str = ("The size at which the image will be resized to square. This means that the actual hash size "
                      "will be equal to the square of the kernel size. Biggest core size makes details at image more"
                      " important. So with equal threshold with different core size same images can be duplicates or "
                      "not duplicates"
    )
    n_jobs: str = "A count of workers for CPU Bound tasks like a hashmap building"
    cache_name: str = ("A cache file name. If you don't set this parameter cache name will be generated automatically "
                       "with next signature: <cache_{path_hash}_d{folder_name}{hash_type}s{core_size}.pkl>")
    a_suffix: str = "A suffix pattern for annotations"
    a_source: str = ("A source directory to annotations. If None - that means annotations are in the same folder with"
                     " images")
    destination_type: str = "A type of destination annotation format"
    img_path: str = "Path to dataset images directory"
    extensions: str = ("A tuple of file extensions that will be used as pattern for building file whitelists for "
                       "converting from yolo to other formats")
    margin: str = ("A threshold value of margin from any image border. If any side of object bbox cloaser that this"
                   "value to image boarder - object will be defined as truncated")
    report_path: str = "A path to directory where reports will be stored"