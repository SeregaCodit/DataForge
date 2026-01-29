import argparse
from pathlib import Path
from typing import Union

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from file_operations.file_remover import FileRemoverMixin



class CleanAnnotationsOperation(FileOperation, FileRemoverMixin):
    def __init__(self, **kwargs):
        """
        Cleans orphan annotations from same or different paths with images.
        Unique args:
        a_source: Path - a path to annotations directory. If None - will be set as source_directory value
        a_suffix: Tuple[str, ...] - Pattern for annotations file suffix
        """
        super().__init__(**kwargs)
        self.a_source = self.settings.a_source


    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
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
        self.logger.info(f"Checking for orphan annotations in {self.settings.a_source}")
        annotation_paths = self.get_files(
            source_directory=self.a_source,
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

    @property
    def a_source(self) -> Path:
        return self._a_source

    @a_source.setter
    def a_source(self, value: Union[Path, str, None]) -> None:
        """setter for a_source, it might be set to Path type, or rise Type error """
        if isinstance(value, Path):
            self._a_source = value
        elif isinstance(value, str):
            self._a_source = Path(value)
        elif value is None:
            self._a_source = self.source_directory
        else:
            self.logger.error(f"Invalid value for a_source: {value}")
            raise TypeError(f"Invalid value for a_source, can be Union[Path, str, None], got {type(value)}")
