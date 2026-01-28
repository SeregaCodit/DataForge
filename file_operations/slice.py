import argparse

from const_utils.arguments import Arguments
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from file_operations.file_remover import FileRemoverMixin
from tools.video_slicer import VideoSlicer


class SliceOperation(FileOperation, FileRemoverMixin):
    """Slice the files that match a pattern from source directory to target directory"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step_sec: float = kwargs.get("step_sec", self.settings.step_sec)
        self.suffix: str = kwargs.get('type', self.settings.suffix)
        self.remove: bool = kwargs.get('remove', self.settings.remove)
        self.slicer: VideoSlicer = VideoSlicer()

    @staticmethod
    def add_arguments(settings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(Arguments.dst, help=HelpStrings.dst)
        parser.add_argument(
            Arguments.remove, Arguments.rm,
            help=HelpStrings.remove,
            action='store_true'
        )
        parser.add_argument(
            Arguments.type, Arguments.t,
            help=HelpStrings.type,
            default=settings.suffix
        )
        parser.add_argument(
            Arguments.step_sec, Arguments.step,
            help=HelpStrings.step_sec,
            default=settings.step_sec
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
                    self._remove_all(file_path)

    @property
    def step_sec(self) -> float:
        return self._step_sec

    @step_sec.setter
    def step_sec(self, value) -> None:
        if not isinstance(value, (int, float)):
            value = float(value)

        self._step_sec = value
