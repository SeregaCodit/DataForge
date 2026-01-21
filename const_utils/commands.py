from dataclasses import dataclass

@dataclass
class Commands:
    """Command names"""
    move: str = "move"
    slice: str = "slice"