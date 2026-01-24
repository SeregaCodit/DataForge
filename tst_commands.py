import sys
from pathlib import Path

from const_utils.commands import Commands
from fileManager import FileManager

script_path = Path(__file__).parent / "fileManager.py"

MAPPING = {
    Commands.slice: [
        str(script_path),
        "slice",
        "./media/",
        "./media/imgs/",
        "-p", ".mp4", ".MP4",
        "-t", ".jpg",
        # "-r",
        "-s", "60",
        "-step", "1",
    ],
    Commands.delete: [
        "fileManager.py",
        "delete",
        "./media/imgs_new/",
        "-p", ".jpg",
    ],
    Commands.move: [
        "fileManager.py",
        "move",
        "./media/imgs/",
        "./media/imgs_new/",
        "-p", ".jpg",
        "-r",
        "-s", "30"
    ],
    Commands.dedup: [
        "fileManager.py",
        "dedup",
        "./media/imgs/",
        "-p", ".jpg", ".png",
        "--filetype", "image",
        "--threshold", "10",
    ]
}

if __name__ == "__main__":
    sys.argv = MAPPING[Commands.dedup]
    app = FileManager()
    app.execute()