import argparse
from pathlib import Path

from const_utils.arguments import Arguments
from const_utils.default_values import DefaultValues
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.video_slicer import VideoSlicer


class SliceOperation(FileOperation):
    """Slice the files that match a pattern from source directory to target directory"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step_sec: float = kwargs.get("step_sec", DefaultValues.step_sec)
        self.suffix: str = kwargs.get('type', DefaultValues.type)
        self.remove: bool = kwargs.get('remove', DefaultValues.remove)
        self.slicer: VideoSlicer = VideoSlicer()

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(Arguments.dst, help=HelpStrings.dst)
        parser.add_argument(
            Arguments.remove, Arguments.rm,
            help=HelpStrings.remove,
            action='store_true'
        )
        parser.add_argument(
            Arguments.type, Arguments.t,
            help=HelpStrings.type,
            default=DefaultValues.type
        )
        parser.add_argument(
            Arguments.step_sec, Arguments.step,
            help=HelpStrings.step_sec,
            default=DefaultValues.step_sec
        )

    def do_task(self):
        for file_path in self.files_for_task:
            if file_path.is_file():
                ret, sliced_count = self.slicer.slice(
                    source_file=file_path,
                    target_dir=self.target_directory,
                    suffix=self.suffix,
                    step=self.step_sec
                )

                if ret:
                    self.logger.info(f"{file_path} sliced to {sliced_count} images")
                else:
                    self.logger.warning(f"Unable to read {file_path}. Not sliced.")
                    continue

                if self.remove:
                    self.remove_source(file_path)


    def remove_source(self,source_file: Path) -> None:
        """delete source file that just was sliced"""
        source_file.unlink(missing_ok=True)
        self.logger.info(f"{source_file} deleted")

    @property
    def step_sec(self) -> float:
        return self._step_sec

    @step_sec.setter
    def step_sec(self, value) -> None:
        if not isinstance(value, (int, float)):
            value = float(value)

        self._step_sec = value
