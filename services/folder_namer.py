import os
from pathlib import Path
from typing import Union


class FolderNamer:
    @staticmethod
    def next_name(src: Union[Path, str]) -> Path:

        if not isinstance(src, Path):
            src = Path(src)

        dir_count = [1 for p in os.listdir(src) if (src / p).is_dir()]
        dir_name = len(dir_count) + 1
        report_path = src / str(dir_name)
        return report_path.resolve()