from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Dict, Tuple, Union

import cv2
import xmltodict

from tools.annotation_converter.converter.base import BaseConverter
from tools.annotation_converter.reader.base import BaseReader
from tools.annotation_converter.writer.base import BaseWriter


class YoloVocConverter(BaseConverter):
    """
    A converter that transforms dataset annotations from YOLO (.txt) to Pascal VOC (.xml).

    This class uses multiprocessing to handle large datasets efficiently. It links
    text labels with their corresponding images to calculate absolute pixel coordinates.

    Attributes:
        CLASSES_FILE (str): Standard name for the file containing class names.
    """
    CLASSES_FILE = "classes.txt"
    _worker_image_map = {}
    def __init__(
            self,
            source_format: str,
            dest_format: str,
            extensions: Tuple[str, ...],
            **kwargs
    ):
        """
        Initializes the converter with specific formats and directory paths.

        Args:
            source_format (str): The format of source files (e.g., '.txt').
            dest_format (str): The format of output files (e.g., '.xml').
            extensions (Tuple[str, ...]): Supported image extensions (e.g., '.jpg', '.png').
            **kwargs: Additional parameters like 'img_path' or 'labels_path'.
        """
        super().__init__(source_format, dest_format, **kwargs)
        self.extensions: Tuple[str, ...] = extensions
        self.labels_path: Path = kwargs.get("labels_path", None)
        self.img_path: Path = kwargs.get("img_path", None)
        self.objects: list = list()
        self.object_mapping: Dict[str, str] = dict()

    @classmethod
    def _init_worker(cls, image_dict: Dict[str, str]):
        """
        Prepares a worker process by storing a shared image map in the class memory.

        Args:
            image_dict (Dict[str, str]): A dictionary mapping image names to their paths.
        """
        cls._worker_image_map = image_dict

    @staticmethod
    def _convert_worker(
            file_path: Path,
            destination_path: Path,
            reader: BaseReader,
            writer: BaseWriter,
            class_mapping: Dict[str, str],
            suffix: str
    ) -> bool:
        """
        The main logic for converting one YOLO file to one VOC XML file.

        It reads the YOLO data, finds the matching image to get its dimensions,
        recalculates coordinates into pixel values, and saves the final XML.

        Args:
            file_path (Path): Path to the source YOLO annotation file.
            destination_path (Path): Directory where the .xml file will be saved.
            reader (BaseReader): Tool to read the source file data.
            writer (BaseWriter): Tool to write the resulting XML data.
            class_mapping (Dict[str, str]): Mapping of class IDs to string names.
            suffix (str): Extension for the output file.

        Returns:
            bool: True if the conversion was successful, False otherwise.
        """

        yolo_annotations = reader.read(file_path).keys()

        if not yolo_annotations:
            return False

        objects = list()
        # ----- correspond image information -----
        correspond_img_str = YoloVocConverter._worker_image_map.get(file_path.stem)

        if correspond_img_str is None:
            return False

        img_height, img_width, im_depth = cv2.imread(correspond_img_str).shape
        correspond_img = Path(correspond_img_str)
        im_path = correspond_img.resolve()
        im_dir = correspond_img.parent.stem
        im_name = correspond_img.name

        for annotation in yolo_annotations:
            class_id, *coords = annotation.split(" ")
            class_name = class_mapping.get(class_id, f"object_{class_id}")
            obj_xcenter, obj_ycenter, obj_width, obj_height = map(float, coords)
            # ----- bbox transformation -----
            xmin = round(((obj_xcenter - obj_width / 2) * img_width))
            ymin = round((obj_ycenter - obj_height / 2) * img_height)
            xmax = round((obj_xcenter + obj_width / 2) * img_width)
            ymax= round((obj_ycenter + obj_height / 2) * img_height)
            voc_object = {
                "name": class_name,
                "pose": "Unspecified",
                "truncated": int(
                    any([
                        xmin <= 0,
                        ymin <= 0,
                        xmax >= img_width,
                        ymax >= img_height,
                    ])
                ),
                "difficult": 0,
                "bndbox":{
                    "xmin": xmin,
                    "ymin": ymin,
                    "xmax": xmax,
                    "ymax": ymax
                }
            }
            objects.append(voc_object)

        converted_dict = {
            "annotation": {
                "folder": im_dir,
                "filename": im_name,
                "path": im_path,
                "source": {
                    "database": "Unknown"
                },
                "size": {
                    "width": img_width,
                    "height": img_height,
                    "depth": im_depth
                },
                "segmented": 0,
                "object": objects if len(objects) > 1 else objects[0]
            }
        }
        try:
            xml = xmltodict.unparse(converted_dict, pretty=True)
            annotation_path = Path(destination_path / f"{file_path.stem}{suffix}")
            writer.write(data=xml, file_path=annotation_path)
        except Exception:
            return False
        return True

    def convert(self, file_paths: Tuple[Path], target_path: Path, n_jobs: int = 1) -> None:
        """
        Batch converts multiple YOLO files into VOC format using parallel processing.

        This method prepares the class names, builds a fast image lookup table,
        and manages the process pool for the conversion task.

        Args:
            file_paths (Tuple[Path]): List of paths to the annotation files.
            target_path (Path): Directory where converted files will be stored.
            n_jobs (int): Number of parallel workers to use. Defaults to 1.
        """
        target_path.mkdir(exist_ok=True, parents=True)
        classes_file = next((path for path in file_paths if path.name == self.CLASSES_FILE), None)
        if classes_file is None:
            self.logger.error(
                f"No classes file found at {target_path}, all classes will be annotated as 'object_<id>'"
            )
        file_paths = tuple(f for f in file_paths if f.name != self.CLASSES_FILE)
        count_to_convert = len(file_paths)
        self.logger.info(
            f"Starting converting from YOLO format to VOC format for {count_to_convert} files, with {n_jobs} workers"
        )
        self.object_mapping = self.reader.read(classes_file)
        self.object_mapping = {value: key for key, value in self.object_mapping.items()}
        images = {img.stem: str(img.resolve()) for img in self.img_path.iterdir() if img.suffix.lower() in self.extensions}

        convert_func = partial(
            self.__class__._convert_worker,
            destination_path=target_path,
            reader=self.reader,
            writer=self.writer,
            class_mapping=self.object_mapping,
            suffix=self.dest_suffix
        )

        with ProcessPoolExecutor(
                max_workers=n_jobs,
                initializer=self.__class__._init_worker,
                initargs=(images,)
        ) as executor:
            converted_results = executor.map(convert_func, file_paths)
            converted_count = sum(converted_results)

        self.logger.info(f"Converted {converted_count}/{count_to_convert} annotations from YOLO to VOC")


    @property
    def img_path(self) -> Path:
        """Path: Returns the directory path where images are stored."""
        return self._img_path

    @img_path.setter
    def img_path(self, img_path: Union[Path, str, None]) -> None:
        """
        Sets the directory for images and validates the input.

        Args:
        img_path (Union[Path, str, None]): Path to annotated images folder.
            If None, it uses YOLO annotations same path .

        Raises:
        TypeError: If the provided path is not a string or Path object.
        """
        if isinstance(img_path, Path):
            self._img_path = img_path
        elif isinstance(img_path, str):
            self._img_path = Path(img_path)
        elif img_path is None :
            self._img_path = self.labels_path
            self.logger.warning(f"Dataset images path is not defined. Set same annotations path: {self.labels_path}")
        else:
            msg = f"img_path must be Path or str, not {type(img_path)}"
            self.logger.error(msg)
            raise TypeError(msg)

    @property
    def extensions(self) -> Tuple[str, ...]:
        """Tuple[str, ...]: Returns the supported image file extensions."""
        return self._extensions

    @extensions.setter
    def extensions(self, value: Tuple[str, ...]) -> None:
        """
        Sets the valid image extensions for the converter.

        Args:
            value (Tuple[str, ...]): A tuple of extension strings (e.g., ('.jpg',)).

        Raises:
            TypeError: If the input cannot be converted into a tuple.
        """
        if isinstance(value, tuple):
            self._extensions = value
        else:
            try:
                self._extensions = tuple(value)
            except TypeError as e:
                msg = f"extensions must be convertable into tuple, got {type(value)}"
                self.logger.error(msg)
                raise TypeError(msg)
