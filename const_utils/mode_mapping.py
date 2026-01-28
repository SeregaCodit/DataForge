from dataclasses import dataclass

@dataclass
class ModeMapping:
    image: str = "image"
    phash: str = "phash"
    ahash: str = "ahash"
    dhash: str = "dhash"
    cnn: str = "cnn"