import argparse

from typing import Any, Union

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.annotation_converter.converter.base import BaseConverter
from tools.annotation_converter.converter.voc_yolo_converter import VocYOLOConverter
from tools.annotation_converter.converter.yolo_voc_converter import YoloVocConverter


class ConvertAnnotationsOperation(FileOperation):
    def __init__(self, settings: AppSettings, **kwargs):
        """Sets up the tool to change annotation formats.

        Args:
            settings (AppSettings): The default settings for the app.
            **kwargs (dict): Extra options for the task. It includes:
                pattern: The starting format (like 'voc' or 'yolo').
                destination_type: The new format you want.
                img_path: Where the images are located.
                n_jobs: How many tasks to run at the same time.
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
        """Adds the necessary options to the command line tool.

        Args:
            settings (AppSettings): The main settings for the app.
            parser (argparse.ArgumentParser): The tool that reads command line options.
        """
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
        """Starts the conversion of the annotation files"""
        self.converter.convert(self.files_for_task, self.target_directory, self.n_jobs)
