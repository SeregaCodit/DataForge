from pathlib import Path
import cv2

class VideoSlicer:
    """slicing video file and saving it to target directory"""
    def __init__(self):
        self.__sliced: bool = False


    def slice(self, source_file: Path, target_dir: Path, suffix: str = ".jpg", step: float = 1) -> tuple:
        """
        slicing video file and saving it to target directory
        :param source_file: path to video file
        :param target_dir: target dir where sliced images from video file will be saved
        :param suffix: a suffix to add to image filename
        :param step: time step for saving image in seconds
        :return: count of images saved in target_dir
        """
        cap = cv2.VideoCapture(str(source_file))

        if not cap.isOpened():
            return self.sliced, 0

        fps = cap.get(cv2.CAP_PROP_FPS)
        step_frames = int(fps * step)
        img_counter = 0
        frame_id = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            if frame_id % step_frames == 0:
                new_filename = f"{source_file.stem}_{img_counter}{suffix}"
                file_path = target_dir / new_filename
                cv2.imwrite(str(file_path), frame)
                img_counter += 1

            frame_id += 1

        cap.release()
        self.__sliced = True
        return self.sliced, img_counter

    @property
    def sliced(self) -> bool:
        return self.__sliced
