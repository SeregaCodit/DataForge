import sys
from pathlib import Path

from const_utils.arguments import Arguments
from const_utils.commands import Commands
from data_forge import DataForge


MAPPING = {
    Commands.slice: [
        "data_forge.py",
        "slice",
        "./media/",
        "--dst", "./media/imgs/",
        "-p", ".mp4", ".MP4",
        "-t", ".jpg",
        # "-r",
        "-s", "60",
        "-step", "1",
    ],
    Commands.delete: [
        "data_forge.py",
        "delete",
        "./media/imgs_new/",
        "-p", ".jpg",
    ],
    Commands.move: [
        "data_forge.py",
        "move",
        "./media/imgs/",
        "--dst", "./media/imgs_new/",
        "-p", ".jpg", ".png",
        "-r",
        "-s", "30"
    ],
    Commands.dedup: [
        "data_forge.py",
        "dedup",
        "./media/imgs/",
        # "/mnt/qnap/Staff/Naumenko/NotTheSkynet/img_dataset/",
        # "/home/pivden/PycharmProjects/yoloTrainer/saved_imgs/",
        "-p", ".jpg", ".png",
        "--filetype", "image",
        "--threshold", "10",
        "--cache_name", "test1"
    ],
    Commands.convert_annotations: [
        "data_forge.py",
        "convert-annotations",
        "./media/annotated/",
        "--dst", "./media/yolo_anns/",
        "-p", "yolo",
        "--img_path", "./media/annotated/", # only for converting from yolo format
        "--destination-type", "voc"
    ]
}

if __name__ == "__main__":
    MAPPING[Commands.dedup].append(Arguments.core_size)
    MAPPING[Commands.dedup].append("16")


    sys.argv = MAPPING[Commands.convert_annotations]
    app = DataForge()
    app.execute()