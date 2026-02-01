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


    def do_task(self):
        for file_path in self.files_for_task:
            if file_path.is_file():
                converted_objects = self.converter.convert(file_path=file_path)
                converted_file_path = self.target_directory / (file_path.stem + self.converter.DESTINATION_FORMAT)

                self.logger.info(
                    f"Converted {file_path} to {converted_file_path}"
                )



