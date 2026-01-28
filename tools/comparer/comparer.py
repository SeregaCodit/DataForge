# from abc import ABC, abstractmethod
# from email.mime import image
# from pathlib import Path
# from typing import Union, List
#
# from const_utils.copmarer import Constants
# from const_utils.default_values import DefaultValues
# from logger.logger import LoggerConfigurator
# from tools.comparer.img_comparer.img_comparer import ImageComparer
#
#
# class Comparer(ABC):
#     """Abstract class for comparing files"""
#     def __init__(self):
#         self.logger = LoggerConfigurator.setup(
#             name=self.__class__.__name__,
#             log_path=DefaultValues.log_path,
#             log_level=DefaultValues.log_level
#         )
#
#
#     @abstractmethod
#     def compare_files(self, files: Union[Path, List[Path]], threshold: int, outfile: Path) -> dict:
#         """return a dict with duplicates """
#         pass
