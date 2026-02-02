from pathlib import Path
from typing import List

from tools.annotation_converter.writer.base import BaseWriter


class YoloWriter(BaseWriter):
    """Implements writing annotation files for YOLO format"""
    def write(self, data: List[str], file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as file:
            file.writelines(f"{line}\n" for line in data if line)
