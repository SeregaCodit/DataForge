import argparse

from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings as hs
from const_utils.commands import Commands
from const_utils.arguments import Arguments as arg
# from const_utils.default_values import DefaultValues as defaults
from file_operations.deduplicate import DedupOperation
from file_operations.delete import DeleteOperation
from file_operations.move import MoveOperation
from file_operations.slice import SliceOperation
from logger.log_level_mapping import LevelMapping


class FileManager:
    """Class corresponding to CLI and launch command"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="FileManager")
        self.subparsers = self.parser.add_subparsers(dest="command")
        self.commands = {
            Commands.move: MoveOperation,
            Commands.slice: SliceOperation,
            Commands.delete: DeleteOperation,
            Commands.dedup: DedupOperation
        }
        self.settings = AppSettings.load_config(Constants.config_file)
        self._setup_commands()

    @staticmethod
    def _add_common_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        """Add common arguments for all commands"""
        parser.add_argument(arg.src, help=hs.src)
        # parser.add_argument(arg.dst, help=hs.dst)
        parser.add_argument(arg.pattern, arg.p, help=hs.pattern, nargs="+", default=[settings.pattern])
        parser.add_argument(arg.repeat, arg.r, help=hs.repeat, action='store_true')
        parser.add_argument(arg.sleep, arg.s, help=hs.sleep, default=settings.sleep)
        parser.add_argument(arg.log_path, help=hs.log_path, default=settings.log_path)
        parser.add_argument(arg.log_level, help=hs.log_level, default=settings.log_level)

    def _setup_commands(self) -> None:
        """setup all commands"""
        for command, operation_class in self.commands.items():
            subparser = self.subparsers.add_parser(command)
            self._add_common_arguments(self.settings, subparser)
            operation_class.add_arguments(self.settings, subparser)
            subparser.set_defaults(cls=operation_class)

    def execute(self):
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

    app = FileManager()
    app.execute()