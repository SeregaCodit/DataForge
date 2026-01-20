from dataclasses import dataclass

@dataclass
class Commands:
    move: str = "move"
    slice: str = "slice"