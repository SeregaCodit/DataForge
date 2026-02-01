from pathlib import Path

from const_utils.default_values import AppSettings
from tools.annotation_converter.converter.base import BaseConverter


class VocYOLOConverter(BaseConverter):
    TARGET_FORMAT = ".xml"
    DESTINATION_FORMAT = ".txt"
    def __init__(self, tolerance: int = 6):
        super().__init__()

        self.tolerance = tolerance
        self.reader = self.reader_mapping[self.TARGET_FORMAT]()
        self.object_mapping: dict = {}
        self.objects: list = list()


    def read(self, source: str) -> str:
        pass


    def convert(self, file_path: Path) -> list:
        data = self.reader.read(file_path)
        converted_objects = list()

        if data is not None:
            annotated_objects  = data["annotation"]["object"]

            if not isinstance(annotated_objects, list):
                annotated_objects = [annotated_objects]

            for obj in annotated_objects:
                # saving objectnames for classes.txt
                if obj["name"] not in self.objects:
                    self.objects.append(obj["name"])

                # calculate yolo format cords
                xmin = int(obj["bndbox"]["xmin"])
                ymin = int(obj["bndbox"]["ymin"])
                xmax = int(obj["bndbox"]["xmax"])
                ymax = int(obj["bndbox"]["ymax"])

                img_width, img_height = map(int, list(data["annotation"]["size"].values())[:2])
                width = ((xmax - xmin) / img_width)
                height = (ymax - ymin) / img_height
                x_center = (xmin + xmax) / 2 / img_width
                y_center = (ymin + ymax) / 2 / img_height

                width, height, x_center, y_center = map(lambda x: round(x, self.tolerance), [width, height, x_center, y_center])

                converted_objects.append(
                    dict(
                        name=obj["name"],
                        width=width,
                        height=height,
                        x_center=x_center,
                        y_center=y_center,
                    )
                )

        return converted_objects

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