import argparse

from const_utils.arguments import Arguments
from const_utils.copmarer import Constants
from const_utils.default_values import DefaultValues
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.comparer.img_comparer.img_comparer import ImageComparer


class CompareOperation(FileOperation):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mapping = {
            Constants.image: ImageComparer
        }

        self.filetype = kwargs.get(Arguments.filetype, DefaultValues.image)
        self.threshold = kwargs.get(Arguments.threshold, DefaultValues.hash_threshold)
        self.action = kwargs.get(Arguments.action, DefaultValues.action)
        self.method = kwargs.get(Arguments.method, DefaultValues.dhash)
        self.comparer = self.mapping[self.filetype](
            method_name=self.method,
            log_path = self.log_path
        )

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.threshold,
            help=HelpStrings.threshold,
            default=DefaultValues.hash_threshold
        )
        parser.add_argument(
            Arguments.filetype,
            help=HelpStrings.filetype,
            default=DefaultValues.image
        )
        parser.add_argument(
            Arguments.method, Arguments.m,
            help=HelpStrings.method,
            default=DefaultValues.dhash
        )
        parser.add_argument(
            Arguments.action. Arguments.a,
            help=HelpStrings.action,
            default=DefaultValues.action
        )

    def do_task(self):
        self.comparer.compare_files(image_dir=self.source_directory, threshold=self.threshold)


