import sys
from pathlib import Path

from const_utils.arguments import Arguments
from const_utils.commands import Commands
from fileManager import FileManager


MAPPING = {
    Commands.slice: [
        "fileManager.py",
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
        "-p", ".jpg", ".png",
        "-r",
        "-s", "30"
    ],
    Commands.dedup: [
        "fileManager.py",
        "dedup",
        # "./media/imgs/",
        "/mnt/qnap/Staff/Naumenko/NotTheSkynet/img_dataset/",
        # "/home/pivden/PycharmProjects/yoloTrainer/saved_imgs/",
        "-p", ".jpg", ".png",
        "--filetype", "image",
        "--threshold", "10",
    ]
}

if __name__ == "__main__":
    MAPPING[Commands.dedup].append(Arguments.core_size)
    MAPPING[Commands.dedup].append("16")


    sys.argv = MAPPING[Commands.dedup]
    app = FileManager()
    app.execute()