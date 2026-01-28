from dataclasses import dataclass
from pathlib import Path


@dataclass
class Constants:
    image: str = "image"
    phash: str = "phash"
    dhash: str = "dhash"
    ahash: str = "ahash"
    cnn: str = "cnn"
    config_file = Path("config.json").resolve()