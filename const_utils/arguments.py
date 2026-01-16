from dataclasses import dataclass

@dataclass
class Arguments:
    src: str = "src"
    dst: str = "dst"
    pattern: str = "--pattern"
    p: str = "-p"
    repeat: str = "--repeat"
    r: str = "-r"
    sleep: str = "--sleep"
    s: str = "-s"