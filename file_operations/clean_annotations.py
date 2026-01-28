import argparse

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from file_operations.file_remover import FileRemoverMixin



class CleanAnnotationsOperation(FileOperation, FileRemoverMixin):

    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.a_suffix,
            help=HelpStrings.a_suffix,
            default=settings.a_suffix,
        )
        parser.add_argument(
            Arguments.a_source,
            help=HelpStrings.a_source,
            default=settings.a_source,
        )


    def do_task(self) -> None:
        self.logger.info(f"Checking for orphan annotations in {self.settings.a_source}")
        annotation_paths = self.get_files(
            source_directory=self.settings.a_source,
            pattern=self.settings.a_suffix
        )

        image_stems = set(image.stem for image in self.files_for_task)

        orphans_removed = 0
        for a_path in annotation_paths:
            if a_path.stem not in image_stems:
                if self._remove_file(a_path):
                    orphans_removed += 1
                    self.logger.info(f"Removed {a_path.stem}")

        self.logger.info(f"Removed {orphans_removed} orphan annotations")
