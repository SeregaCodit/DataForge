from pathlib import Path

import cv2

class VideoSlicer:
    """slicing video file and saving it to target directory"""
    @staticmethod
    def slice(source_file: Path, target_dir: Path, suffix: str = ".jpg", step: float = 1):
        cap = cv2.VideoCapture(str(source_file))

        if not cap.isOpened():
            print(f"Cannot open {source_file}")
            return 0

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

        return img_counter


