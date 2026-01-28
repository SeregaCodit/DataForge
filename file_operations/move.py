import argparse
import shutil

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation

class MoveOperation(FileOperation):
    """Move files that match a patterns from source directory to target directory """
    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(Arguments.dst, help=HelpStrings.dst)
        pass

    def do_task(self):
        for file_path in self.files_for_task:
            if file_path.is_file() and file_path.parent.resolve() != self.target_directory.resolve():
                target_file_path = self.target_directory / file_path.name
                self.logger.info(f"{file_path} -> {self.target_directory}")

                try:
                    shutil.move(file_path, target_file_path)
                except Exception as e:
                    self.logger.error(e)
