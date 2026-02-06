import argparse
from pathlib import Path
from typing import Union

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.mixins.file_remover import FileRemoverMixin


class CleanAnnotationsOperation(FileOperation, FileRemoverMixin):
    """
    An operation to remove 'orphan' annotation files.

    This class identifies annotation files (like .xml or .txt) that do not have
    a corresponding image file in the source directory. It helps to maintain
    dataset integrity by cleaning up labels that are no longer needed.

    Attributes:
        a_source (Path): The directory path where annotation files are stored.
    """
    def __init__(self, **kwargs):
        """
        Initializes the cleanup operation for annotations.

        Args:
            **kwargs (dict): Arguments from the command line or settings,
                specifically looking for 'a_source' and 'a_suffix'.
        """
        super().__init__(**kwargs)
        self.a_source = self.settings.a_source


    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        """
        Adds specific CLI arguments for annotation cleaning.

        Args:
            settings (AppSettings): Global configuration for default values.
            parser (argparse.ArgumentParser): The parser to which 'a_suffix'
                and 'a_source' arguments are added.
        """
        parser.add_argument(
            Arguments.a_suffix,
            nargs="+",
            help=HelpStrings.a_suffix,
            default=settings.a_suffix,
        )
        parser.add_argument(
            Arguments.a_source,
            help=HelpStrings.a_source,
            default=settings.a_source,
        )


    def do_task(self) -> None:
        """
        Executes the synchronization and removal process.

        It collects all image names (stems) from the source directory and
        compares them with annotation files. If an annotation stem is not
        found in the image stems, the file is deleted using FileRemoverMixin.
        """
        self.logger.info(f"Checking for orphan annotations in {self.settings.a_source}")
        annotation_paths = self.get_files(
            source_directory=self.a_source,
            pattern=self.settings.a_suffix
        )

        image_stems = set(image.stem for image in self.files_for_task)
        orphans_removed = 0

        for a_path in annotation_paths:
            if a_path.stem not in image_stems:
                if self.remove_file(a_path):
                    orphans_removed += 1
                    self.logger.info(f"Removed {a_path.stem}")

        self.logger.info(f"Removed {orphans_removed} orphan annotations")


    @property
    def a_source(self) -> Path:
        """Path: Returns the directory path for annotations."""
        return self._a_source


    @a_source.setter
    def a_source(self, value: Union[Path, str, None]) -> None:
        """
        Sets the annotation source path with type validation.

        If the provided value is None, it defaults to the main source_directory.
        It converts string inputs into Path objects.

        Args:
            value (Union[Path, str, None]): The path to the annotations folder.

        Raises:
            TypeError: If the value is not a Path, string, or None.
        """
        if isinstance(value, Path):
            self._a_source = value
        elif isinstance(value, str):
            self._a_source = Path(value)
        elif value is None:
            self._a_source = self.source_directory
        else:
            msg = f"Invalid value for a_source, can be Union[Path, str, None], got {type(value)}"
            self.logger.error(msg)
            raise TypeError(msg)
