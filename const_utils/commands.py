from dataclasses import dataclass

@dataclass
class Commands:
    """Command names"""
    move: str = "move"
    slice: str = "slice"
    delete: str = "delete"
    dedup: str = "dedup"
    clean_annotations: str = "clean-annotations"
    convert_annotations: str = "convert-annotations"
    stats: str = "stats"
    augment: str = "augment"