from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import List, Dict, Set, Tuple

import numpy as np

from tools.annotation_converter.converter.base import BaseConverter
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.writer.base import BaseWriter


class VocYOLOConverter(BaseConverter):
    CLASSES_FILE = "classes.txt"
    def __init__(self, source_format, dest_format, tolerance: int = 6, **kwargs):
        """
        :param tolerance: an int value that determines to which decimal place to round a converted in YOLO
            format coordinates. By default, it is 6 in YOLO format.
        :type tolerance: int
        """
        super().__init__(source_format, dest_format, **kwargs)

        self.tolerance = tolerance
        self.objects: list = list()
        self.class_mapping: Dict[str, int] = dict()

    @staticmethod
    def _get_classes_worker(annotation_paths: Path, reader: BaseReader) -> Set[str]:
        """
        :param annotation_paths: paths to annotation files
        :type annotation_paths: Path
        :param reader: reader object for parsing annotations
        :type reader: BaseReader
        :return: a set with all object classes found in annotations
        """
        try:
            data = reader.read(annotation_paths)
            annotation = data.get("annotation", {})
            objects = annotation.get("object", list())
            if not isinstance(objects, list):
                objects = [objects]
            return {obj["name"] for obj in objects}
        except Exception:
            return set()

    @staticmethod
    def _convert_worker(
            file_path: Path,
            destination_path: Path,
            reader: BaseReader,
            writer: BaseWriter,
            class_mapping: Dict[str, int],
            tolerance: int,
            suffix: str
    ) -> bool:
        """
        pipline for parsing annotations, recalculating annotated objects data to YOLO format and savin it in
            destination path

        :param file_path: path to annotation file
        :type file_path: Path
        :param destination_path: path to output annotation file
        :type destination_path: Path
        :param reader: reader object for parsing annotations
        :type reader: BaseReader
        :param writer: writer object for writing converted annotation files
        :type writer: BaseWriter
        :param class_mapping: mapping from class name to class id
        :type class_mapping: Dict[str, int]
        :param tolerance: an int value that determines to which decimal place to round a converted in YOLO
            format coordinates.
        :type tolerance: int
        :param suffix: suffix to add to filename
        :type suffix: str
        :return: True if a file was successfully converted, else returns False

        """
        data = reader.read(file_path)

        if data.get("annotation") is None:
            return False

        annotation = data["annotation"]

        try:
            img_width = int(annotation["size"]["width"])
            img_height = int(annotation["size"]["height"])

            if img_width == 0 or img_height == 0:
                raise ValueError(f"Image size is zero in annotation {file_path}!")
        except (KeyError, ValueError, TypeError):
            return False

        annotated_objects = annotation.get("object", list())

        # reader using xmltodict that returns a dict if there is just one object, if more - returns a list
        if not isinstance(annotated_objects, list):
            annotated_objects = [annotated_objects]

        converted_objects: List[str] = list()

        for obj in annotated_objects:
            try:
                # saving objectnames for classes.txt
                name = obj["name"]

                if name not in class_mapping:
                    continue
                class_id = class_mapping[name]

                # calculate yolo format cords
                bbox = obj["bndbox"]
                xmin, ymin, xmax, ymax = (
                    float(bbox["xmin"]), float(bbox["ymin"]),
                    float(bbox["xmax"]), float(bbox["ymax"])
                )

                width = ((xmax - xmin) / img_width)
                height = (ymax - ymin) / img_height
                x_center = (xmin + xmax) / 2 / img_width
                y_center = (ymin + ymax) / 2 / img_height

                x_center, y_center, width, height = map(lambda x: np.clip(x, 0, 1),
                                                        [x_center, y_center, width, height])

                row = (f"{class_id} "
                       f"{x_center:.{tolerance}f} "
                       f"{y_center:.{tolerance}f} "
                       f"{width:.{tolerance}f} "
                       f"{height:.{tolerance}f}")
                converted_objects.append(row)

            except (KeyError, ValueError, TypeError):
                continue

        converted_path = destination_path / f"{file_path.stem}{suffix}"
        writer.write(converted_objects, converted_path)
        return True

    def convert(self, file_paths: Tuple[Path], target_path: Path, n_jobs: int = 1) -> None:
        """
        discover classes of annotated objects and writes them in classes file.
        Run multiprocessing conversion and writing pipline

        :param file_paths: list of annotation files
        :type file_paths: Tuple[Path]
        :param target_path: path to output annotation file directory
        :type target_path: Path
        :param n_jobs: number of workers
        :type n_jobs: int
        :return None
        """
        count_to_convert = len(file_paths)

        if count_to_convert > 0:
            target_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Start converting {count_to_convert} annotations with {n_jobs} workers...")

        classes_func = partial(self._get_classes_worker, reader=self.reader)
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            classes = list(executor.map(classes_func, file_paths))

        self.objects = sorted(set().union(*classes))
        class_mapping = {name: i for i, name in enumerate(self.objects)}
        self.logger.info(f"Unified class mapping created: {len(self.objects)} classes")

        worker_func = partial(
            self._convert_worker,
            destination_path=target_path,
            reader=self.reader,
            writer=self.writer,
            class_mapping=class_mapping,
            tolerance=self.tolerance,
            suffix=self.dest_suffix
        )

        self.logger.info(f"converting {count_to_convert} annotations with {n_jobs} workers...")
        converted_count = 0
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            converted_results = executor.map(worker_func, file_paths)
            converted_count = sum(converted_results)

        self.logger.info(f"Converted {converted_count}/{count_to_convert} annotations and saved in {target_path}")

        self.writer.write(self.objects, target_path / self.CLASSES_FILE)
        self.logger.info(f"Saved {self.CLASSES_FILE} in {target_path}")


    @property
    def tolerance(self) -> int:
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value: int):
        if isinstance(value, int):
            self._tolerance = value
        else:
            try:
                self._tolerance = int(float(value))
            except TypeError as e:
                self.logger.warning(f"Can`t convert {value} to int from type {type(value)})\n{e}")
                raise TypeError(e)
