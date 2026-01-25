import argparse
from pathlib import Path
from typing import List

from const_utils.arguments import Arguments
from const_utils.copmarer import Constants
from const_utils.default_values import DefaultValues
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from file_operations.file_remover import FileRemoverMixin
from tools.comparer.img_comparer.img_comparer import ImageComparer


class DedupOperation(FileOperation, FileRemoverMixin):
    def __init__(self, **kwargs):
        """
        find duplicate files in source folder
        :param kwargs: params from CLI
        """
        super().__init__(**kwargs)
        self.mapping = {
            Constants.image: ImageComparer
        }

        self.filetype = kwargs.get("filetype", DefaultValues.image)
        self.action = kwargs.get("action", DefaultValues.action)
        self.method = kwargs.get("method", DefaultValues.dhash)
        self.remove = kwargs.get("remove", DefaultValues.remove)
        self.comparer: ImageComparer = self.mapping[self.filetype](
            method_name=self.method,
            log_path = self.log_path,
            threshold_percentage=int(kwargs.get("threshold", DefaultValues.hash_threshold)),
            core_size = int(kwargs.get("core_size", DefaultValues.core_size))
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
            Arguments.remove, Arguments.rm,
            help=HelpStrings.remove,
            action="store_true"
        )
        parser.add_argument(
            Arguments.core_size,
            help=HelpStrings.core_size,
            default=DefaultValues.core_size
        )


    def do_task(self):
        """
        find duplicate files in source folder, ask user to delete them if remove
        """
        duplicates = self.comparer.compare(self.files_for_task)
        self.logger.info(f"Found {len(duplicates)} duplicates in {len(self.files_for_task)} files")

        if len(duplicates) > 0 and self.confirm_removing():
                self._remove_all(duplicates)

    def confirm_removing(self) -> bool:
        """check if user wants to remove duplicates"""
        if not self.remove:
            user_choice = input("for deleting founded duplicate files type 'delete': ")
            return user_choice.lower() in DefaultValues.confirm_choice
        return True
