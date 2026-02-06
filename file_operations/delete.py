import argparse

from const_utils.default_values import AppSettings
from file_operations.file_operation import FileOperation
from tools.mixins.file_remover import FileRemoverMixin


class DeleteOperation(FileOperation, FileRemoverMixin):
    """
    An operation to delete files from source directory that match specific patterns.

    This class identifies files in the source directory and removes them
    permanently. It uses the FileRemoverMixin to ensure that each deletion
    is handled safely and logged correctly.
    """
    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        """
        Defines command-line arguments for the delete operation.

        This specific operation does not require unique arguments beyond
        the standard source and pattern parameters.

        Args:
            settings (AppSettings): The global settings object for default values.
            parser (argparse.ArgumentParser): The CLI parser to which arguments are added.
        """
        pass


    def do_task(self):
        """
        Executes the deletion task for all collected files.

        This method calls the '_remove_all' helper from FileRemoverMixin
        to process the list of files found in the source directory.
        """
        self.remove_all(self.files_for_task)
