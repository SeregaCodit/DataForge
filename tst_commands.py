import sys
from pathlib import Path

from fileManager import FileManager

script_path = Path(__file__).parent / "fileManager.py"


if __name__ == "__main__":
    # sys.path.append(str(Path(__file__).parent / "fileManager"))
    # Емулюємо введення в терміналі:
    # -----SLICE-----
    # sys.argv = [
    #     str(script_path),
    #     "slice",
    #     "./media/",
    #     "./media/imgs/",
    #     "-p", ".mp4", ".MP4",
    #     "-t", ".jpg",
    #     # "-r",
    #     "-s", "60",
    #     "-step", "1",
    # ]

    # -----SLICE WITH DELETING-----
    # sys.argv = [
    #     "fileManager.py",
    #     "slice",
    #     "./media/imgs/",
    #     "./media/imgs/",
    #     "-p", ".mp4", ".MP4",
    #     "-t", ".jpg",
    #     # "-r",
    #     "-rm",
    #     "-s", "60",
    #     "-step", "1",
    # ]

    # #-----MOVE-----
    # sys.argv = [
    #     "fileManager.py",
    #     "move",
    #     "./media/imgs/",
    #     "./media/imgs_new/",
    #     "-p", ".jpg",
    #     "-r",
    #     "-s", "30"
    # ]
    # -----DELETE-----
    # sys.argv = [
    #     "fileManager.py",
    #     "delete",
    #     "./media/imgs_new/",
    #     "-p", ".jpg",
    #-----DEDUP-----
    sys.argv = [
        "fileManager.py",
        "dedup",
        "./media/imgs/",
        # "./media/imgs_new/",
        "-p", ".jpg", ".png",
        "--filetype", "image",
        "--threshold", "10",
        "-rm"
    ]
    app = FileManager()
    app.execute()