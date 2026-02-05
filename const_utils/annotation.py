# from dataclasses import dataclass
# from pathlib import Path
# from typing import Tuple, Dict, Optional
#
# from logger.log_level_mapping import LevelMapping
# from logger.logger import LoggerConfigurator
#
#
# class ObjectAnnotation:
#     def __init__(self, log_level: str = LevelMapping.debug, log_path: Optional[Path] = None,  **kwargs):
#         self.imsize: Tuple[int, int] = kwargs.get("imsize")
#         self.name: str = kwargs.get("name")
#         self.pose: str = kwargs.get("pose", 'Unspecified')
#         self.truncated: int = kwargs.get("truncated", 0)
#         self.difficult: int = kwargs.get("difficult", 0)
#         self.bndbox: Dict[str, int] = kwargs.get("bndbox", {})
#         self.width: int = None
#         self.height: int = None
#         self.x_center: int = None
#         self.y_center: int = None
#         self.area: int = None
#         self.aspect_ratio: int = None
#         self.relative_area: float = None
#
#         self.logger = LoggerConfigurator.setup(
#             name=self.__class__.__name__,
#             log_level=log_level,
#             log_path=Path(log_path) / f"{self.__class__.__name__}.log" if log_path else None
#         )
#
#     @property
#     def area(self) -> int:
#         return self._area
#
#     @area.setter
#     def area(self, value: int) -> None:
#         if isinstance(value, int):
#             self._area = value
#         else:
#             try:
#                 self._area = int(float(value))
#             except TypeError as e:
#                 error_text = f"Area must be an integer, got {value}"
#                 self.logger.warning(error_text)
#                 raise TypeError(e)
#
#     @property
#     def width(self) -> int:
#         return self._width
#
#
