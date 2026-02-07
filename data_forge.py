import argparse

from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings as hs
from const_utils.commands import Commands
from const_utils.arguments import Arguments as arg
from file_operations.convert_annotations import ConvertAnnotationsOperation
from file_operations.deduplicate import DedupOperation
from file_operations.delete import DeleteOperation
from file_operations.move import MoveOperation
from file_operations.slice import SliceOperation
from file_operations.clean_annotations import CleanAnnotationsOperation


class DataForge:
    """
    The main entry point for the DataForge toolkit.

    This class orchestrates the Command Line Interface (CLI). It registers
    all available file operations, loads the global configuration, and
    manages the execution of specific tasks based on user input.

    Attributes:
        parser (argparse.ArgumentParser): The main CLI parser.
        subparsers (argparse._SubParsersAction): A collection of command-specific parsers.
        commands (Dict[str, Type[FileOperation]]): A mapping of command names
            to their respective operation classes.
        settings (AppSettings): The global configuration object loaded from
            JSON and environment variables.
    """
    def __init__(self):
        """
        Initializes the DataForge application.

        It sets up the argument parser, registers the list of supported
        commands, and loads the initial settings from the configuration file.
        """
        self.parser = argparse.ArgumentParser(description="FileManager")
        self.subparsers = self.parser.add_subparsers(dest="command")
        self.commands = {
            Commands.move: MoveOperation,
            Commands.slice: SliceOperation,
            Commands.delete: DeleteOperation,
            Commands.dedup: DedupOperation,
            Commands.clean_annotations: CleanAnnotationsOperation,
            Commands.convert_annotations: ConvertAnnotationsOperation
        }
        self.settings = AppSettings.load_config(Constants.config_file)
        self._setup_commands()


    @staticmethod
    def _add_common_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        """
        Adds shared arguments to a command subparser.

        These arguments are available for all operations, such as source
        directory, file patterns, and execution loop settings.

        Args:
            settings (AppSettings): Configuration object used to set default values.
            parser (argparse.ArgumentParser): The subparser for a specific command.
        """
        parser.add_argument(arg.src, help=hs.src)
        parser.add_argument(arg.pattern, arg.p, help=hs.pattern, nargs="+", default=[settings.pattern])
        parser.add_argument(arg.repeat, arg.r, help=hs.repeat, action='store_true')
        parser.add_argument(arg.sleep, arg.s, help=hs.sleep, default=settings.sleep)
        parser.add_argument(arg.log_path, help=hs.log_path, default=settings.log_path)
        parser.add_argument(arg.log_level, help=hs.log_level, default=settings.log_level)


    def _setup_commands(self) -> None:
        """
        Registers and configures all operation commands.

        It iterates through the 'commands' dictionary to create subparsers
        and adds both common and operation-specific arguments for each command.
        """
        for command, operation_class in self.commands.items():
            subparser = self.subparsers.add_parser(command)
            self._add_common_arguments(self.settings, subparser)
            operation_class.add_arguments(self.settings, subparser)
            subparser.set_defaults(cls=operation_class)


    def execute(self):
        """
        Parses CLI arguments and executes the selected operation.

        This method merges the input from the command line with the
        existing settings. It ensures that CLI arguments have the highest
        priority. Then, it creates an instance of the chosen operation
        and calls its 'run' method.
        """
        args = self.parser.parse_args()
        cli_data = {key: value for key, value in vars(args).items() if value is not None and key != "command"}

        if hasattr(args, "cls"):
            for key, value in cli_data.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            operation = args.cls(settings=self.settings, **vars(args))
            operation.run()
        else:
            self.parser.print_help()

if __name__ == "__main__":
    app = DataForge()
    app.execute()