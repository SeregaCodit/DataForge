import argparse
from typing import Union

from const_utils.arguments import Arguments
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from tools.mixins.file_remover import FileRemoverMixin
from tools.video_slicer import VideoSlicer


class SliceOperation(FileOperation, FileRemoverMixin):
    """
    An operation to extract images (frames) from video files.

    This class processes video files in source directory that match a specific
    pattern and saves their frames into the target directory. It can also
    automatically delete the source video file after the slicing process is finished.

    Attributes:
        step_sec (float): The time interval in seconds between extracted frames.
        suffix (str): The file extension for the output images (e.g., '.jpg').
        remove (bool): If True, the source video is deleted after processing.
        slicer (VideoSlicer): The tool used to perform the actual video slicing.
    """
    def __init__(self, **kwargs):
        """
        Initializes the slice operation with the required parameters.

        Args:
            **kwargs (dict): Arguments including 'step_sec', 'type', and 'remove'
                flags, usually passed from the command line or settings.
        """
        super().__init__(**kwargs)
        self.step_sec: float = kwargs.get("step_sec", self.settings.step_sec)
        self.suffix: str = kwargs.get('type', self.settings.suffix)
        self.remove: bool = kwargs.get('remove', self.settings.remove)
        self.slicer: VideoSlicer = VideoSlicer()


    @staticmethod
    def add_arguments(settings, parser: argparse.ArgumentParser) -> None:
        """
        Defines CLI arguments for the video slicing task.

        Args:
            settings (AppSettings): Global configuration for default values.
            parser (argparse.ArgumentParser): The parser to which arguments are added.
        """
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
        """
        Processes the collected video files one by one.

        This method uses the 'VideoSlicer' tool to extract frames. It logs
        how many images were created for each video. If the 'remove' flag
        is enabled, it deletes the source video using 'FileRemoverMixin'.
        """
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
                    self.remove_all(file_path)


    @property
    def step_sec(self) -> float:
        """float: Returns the time interval between frames."""
        return self._step_sec


    @step_sec.setter
    def step_sec(self, value: Union[float, int, str]) -> None:
        """
        Sets the time interval and ensures it is a float value.

        Args:
            value (Union[int, float, str]): The interval value to be converted.
        """
        if not isinstance(value, float):
            value = float(value)

        self._step_sec = value
