import argparse
from const_utils.arguments import Arguments
from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
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

        self.filetype = kwargs.get("filetype", self.settings.filetype)
        self.method = kwargs.get("method", self.settings.method)
        self.remove = kwargs.get("remove", self.settings.remove)
        self.comparer: ImageComparer = self.mapping[self.filetype](self.settings)

    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.threshold,
            help=HelpStrings.threshold,
            default=settings.hash_threshold
        )
        parser.add_argument(
            Arguments.filetype,
            help=HelpStrings.filetype,
            default=settings.filetype
        )
        parser.add_argument(
            Arguments.method, Arguments.m,
            help=HelpStrings.method,
            default=settings.method
        )
        parser.add_argument(
            Arguments.remove, Arguments.rm,
            help=HelpStrings.remove,
            action="store_true"
        )
        parser.add_argument(
            Arguments.core_size,
            help=HelpStrings.core_size,
            default=settings.core_size
        )
        parser.add_argument(
            Arguments.n_jobs,
            help=HelpStrings.n_jobs,
            default=settings.n_jobs
        )
        parser.add_argument(
            Arguments.cache_name,
            help=HelpStrings.cache_name,
            default=None
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
            return user_choice.lower() in self.settings.confirm_choice
        return True
