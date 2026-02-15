from pathlib import Path
from typing import Iterable

import cv2



class YoloToDict:
    @staticmethod
    def to_voc_dict(annotations: Iterable, correspond_img: str, class_mapping: dict) -> dict:
        image = cv2.imread(correspond_img)

        if image is None:
            return {}

        img_height, img_width, im_depth = image.shape
        correspond_img = Path(correspond_img)
        im_path = correspond_img.resolve()
        im_dir = correspond_img.parent.stem
        im_name = correspond_img.name

        objects = []

        for annotation in annotations:
            class_id, *coords = annotation.split(" ")
            class_name = class_mapping.get(class_id, f"object_{class_id}")
            obj_xcenter, obj_ycenter, obj_width, obj_height = map(float, coords)
            # ----- bbox transformation -----
            xmin = round(((obj_xcenter - obj_width / 2) * img_width))
            ymin = round((obj_ycenter - obj_height / 2) * img_height)
            xmax = round((obj_xcenter + obj_width / 2) * img_width)
            ymax = round((obj_ycenter + obj_height / 2) * img_height)
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
                "bndbox": {
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
        return converted_dict