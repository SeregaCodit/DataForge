from pathlib import Path
from typing import List, Tuple

from tools.annotation_converter.writer.base import BaseWriter


class YoloWriter(BaseWriter):

    def write(self, data: List[str], file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as file:
            file.writelines(f"{line}\n" for line in data if line)
