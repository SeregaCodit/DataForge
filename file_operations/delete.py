import argparse
import shutil

from const_utils.arguments import Arguments
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation


class DeleteOperation(FileOperation):
    """Delete files that match the pattern"""
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """this class doesn't have unique arguments"""
        pass

    def do_task(self):
        """Delete files that match the pattern"""
        for file_path in self.files_for_task:
            if file_path.is_file():
                file_path.unlink(missing_ok=True)
                self.logger.info(f"deleted {file_path}")
