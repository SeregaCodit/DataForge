from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import List, Dict, Set, Tuple, Union

import numpy as np

from tools.annotation_converter.converter.base import BaseConverter
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.writer.base import BaseWriter


class VocYOLOConverter(BaseConverter):
    """
        A high-performance converter for dataset annotations from Pascal VOC (.xml) to YOLO (.txt).

        This class implements a two-phase parallel processing pipeline:
        1. Discovery Phase: Scans all files to build a consistent class mapping.
        2. Execution Phase: Performs the actual coordinate normalization and saves the files.

        Attributes:
            CLASSES_FILE (str): The name of the output file containing the list of YOLO classes.
            tolerance (int): Precision of the coordinates in the resulting YOLO files.
            objects (list): A list of unique class names found during the discovery phase.
            class_mapping (Dict[str, int]): A dictionary mapping class names to their YOLO IDs.
        """
    CLASSES_FILE = "classes.txt"
    def __init__(self, source_format, dest_format, tolerance: int = 6, **kwargs):
        """
        Initializes the VOC to YOLO converter.

        Args:
            source_format (str): The extension of source files (e.g., '.xml').
            dest_format (str): The extension of destination files (e.g., '.txt').
            tolerance (int): Number of decimal places for coordinates. Defaults to 6.
            **kwargs (dict): Additional parameters passed to the BaseConverter.
        """
        super().__init__(source_format, dest_format, **kwargs)

        self.tolerance = tolerance
        self.objects: list = list()
        self.class_mapping: Dict[str, int] = dict()


    @staticmethod
    def _get_classes_worker(annotation_paths: Path, reader: BaseReader) -> Set[str]:
        """
        Multiprocessing worker for the Discovery Phase.

        Reads a single annotation file and extracts all unique object names.

        Args:
           annotation_paths (Path): Path to the XML annotation file.
           reader (BaseReader): The reader instance used to parse XML data.

        Returns:
           Set[str]: A set of unique class names found in the file.
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
        Multiprocessing worker for the Execution Phase.

        Performs the core logic: reads XML, calculates YOLO-normalized coordinates
        (center_x, center_y, width, height), and saves the resulting text file.

        Args:
           file_path (Path): Path to the source XML file.
           destination_path (Path): Directory where the output file will be saved.
           reader (BaseReader): Reader instance for XML parsing.
           writer (BaseWriter): Writer instance for saving YOLO data.
           class_mapping (Dict[str, int]): Map of class names to their integer IDs.
           tolerance (int): Precision for rounding coordinates.
           suffix (str): The file extension for the output file.

        Returns:
           bool: True if the file was successfully processed and saved.
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
        Orchestrates the batch conversion process using multiple processes.

        Phase 1: Scans all files in parallel to create a unified 'classes.txt'.
        Phase 2: Converts coordinates and saves files in parallel.

        Args:
            file_paths (Tuple[Path, ...]): Collection of source annotation files.
            target_path (Path): Directory path for the converted output.
            n_jobs (int): Number of parallel workers to use. Defaults to 1.
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
        """int: The number of decimal places for YOLO coordinates."""
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value: Union[int, float, str]) -> None:
        """
        Sets the coordinate precision. Handles conversion from float or string if needed.

        Args:
            value Union[int, float, str]: The precision value.

        Raises:
            TypeError: If the value cannot be converted to an integer.
        """
        if isinstance(value, int):
            self._tolerance = value
        else:
            try:
                self._tolerance = int(float(value))
            except TypeError as e:
                msg = f"Can`t convert {value} to int from type {type(value)})\n{e}"
                self.logger.warning(msg)
                raise TypeError(msg)
