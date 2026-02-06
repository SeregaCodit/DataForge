import argparse
from const_utils.arguments import Arguments
from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.mixins.file_remover import FileRemoverMixin
from tools.comparer.img_comparer.img_comparer import ImageComparer


class DedupOperation(FileOperation, FileRemoverMixin):
    """
    An operation to find and remove visual duplicates in a dataset.

    This class compares images in the source folder using hashing algorithms
    (like dHash). It identifies similar images based on a similarity threshold
    and can either delete them automatically or ask the user for confirmation.

    Attributes:
        filetype (str): The type of files to process (e.g., 'image').
        method (str): The hashing method used for comparison (e.g., 'dhash').
        remove (bool): If True, duplicates are deleted automatically without asking.
        comparer (ImageComparer): The engine that performs the actual image comparison.
    """
    def __init__(self, **kwargs):
        """
        Initializes the deduplication operation.

        Args:
            **kwargs (dict): Parameters from the command line or settings, including
                'filetype', 'method', 'threshold', and 'core_size'.
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
        """
        Defines CLI arguments for the deduplication task.

        Args:
            settings (AppSettings): Global configuration for default values.
            parser (argparse.ArgumentParser): The parser to which arguments are added.
        """
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
        Executes the deduplication process.

        This method uses the 'ImageComparer' to find duplicates among the
        collected files. If duplicates are found, it checks for user
        confirmation (or uses the 'remove' flag) and deletes the files
        using 'FileRemoverMixin'.
        """
        duplicates = self.comparer.compare(self.files_for_task)
        duplicates_count = len(duplicates)
        self.logger.info(f"Found {duplicates_count} duplicates in {len(self.files_for_task)} files")

        if duplicates_count > 0 and self.confirm_removing():
                self.remove_all(duplicates)

    def confirm_removing(self) -> bool:
        """
        Checks if the operation has permission to delete the found duplicates.

        If the 'remove' flag is not set, the method asks the user to type
        'delete' in the console to proceed.

        Returns:
            bool: True if deletion is confirmed, False otherwise.
        """
        if not self.remove:
            user_choice = input("for deleting founded duplicate files type 'delete': ")
            return user_choice.lower() in self.settings.confirm_choice
        return True
