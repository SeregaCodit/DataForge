import argparse
from abc import ABC
from pathlib import Path

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.annotation_converter.converter.voc_yolo_converter import VocYOLOConverter


class ConvertAnnotationsOperation(FileOperation):
    def __init__(self, settings: AppSettings, **kwargs):
        super().__init__(settings, **kwargs)
        self.destination_type = kwargs.get('destination_type')
        self.converter_mapping = {
            (".xml", "yolo") : VocYOLOConverter
        }
        self.converter = self.converter_mapping[(self.pattern[0], self.destination_type)]()
        self.n_jobs = kwargs.get('n_jobs', 1)


    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.dst,
            default=None,
            help=HelpStrings.dst
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


    def do_task(self):
        self.converter.convert(self.files_for_task, self.target_directory, self.n_jobs)



