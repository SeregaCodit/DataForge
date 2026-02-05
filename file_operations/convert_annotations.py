import argparse
from abc import ABC
from pathlib import Path
from typing import Any, Union

from const_utils.arguments import Arguments
from const_utils.commands import Commands
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.annotation_converter.converter.base import BaseConverter
from tools.annotation_converter.converter.voc_yolo_converter import VocYOLOConverter
from tools.annotation_converter.converter.yolo_voc_converter import YoloVocConverter


class ConvertAnnotationsOperation(FileOperation):
    def __init__(self, settings: AppSettings, **kwargs):
        """
        Converts annotation formats from pattern to destination. You Can use only one value of pattern at the time
        Params:
            pattern: in this command pattern - must be a format ttype (e.g. yolo, voc)
            destination_type: format type convert to
            n_jobs: how many workers to run, max workers can be your CPU count minus 1 for system stability
        """
        super().__init__(settings, **kwargs)
        self.destination_type = kwargs.get('destination_type')
        self.img_path = kwargs.get('img_path')
        self.converter_mapping = {
            ("voc", "yolo") : VocYOLOConverter,
            ("yolo", "voc"): YoloVocConverter
        }

        mapping_key = (self.pattern[0], self.destination_type)
        self.converter: Union[BaseConverter.__subclasses__()] = self.converter_mapping[mapping_key](
            source_format=mapping_key[0],
            dest_format=mapping_key[1],
            extensions=kwargs.get('ext', self.settings.extensions),
            img_path=self.img_path,
            labels_path=self.source_directory
        )
        self.pattern = self.converter.source_suffix
        self.n_jobs = kwargs.get('n_jobs', 1)


    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.dst,
            default=None,
            help=HelpStrings.dst
        )
        parser.add_argument(
            Arguments.img_path,
            default=None,
            help=HelpStrings.img_path
        )
        parser.add_argument(
            Arguments.destination_type,
            help=HelpStrings.destination_type
        )
        parser.add_argument(
            Arguments.n_jobs,
            default=settings.n_jobs,
            help=HelpStrings.n_jobs
        )
        parser.add_argument(
            Arguments.extensions,
            nargs="+",
            help=HelpStrings.extensions,
            default=settings.extensions
        )


    def do_task(self):
        self.converter.convert(self.files_for_task, self.target_directory, self.n_jobs)



