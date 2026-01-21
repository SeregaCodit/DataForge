import argparse
from const_utils.parser_help import HelpStrings as hs
from const_utils.commands import Commands
from const_utils.arguments import Arguments as arg
from const_utils.default_values import DefaultValues as defaults
from file_operations.delete import DeleteOperation
from file_operations.move import MoveOperation
from file_operations.slice import SliceOperation


class FileManager:
    """Class corresponding to CLI and launch command"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="FileManager")
        self.subparsers = self.parser.add_subparsers(dest="command")
        self.commands = {
            Commands.move: MoveOperation,
            Commands.slice: SliceOperation,
            Commands.delete: DeleteOperation
        }

        self._setup_commands()

    @staticmethod
    def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
        """Add common arguments for all commands"""
        parser.add_argument(arg.src, help=hs.src)
        # parser.add_argument(arg.dst, help=hs.dst)
        parser.add_argument(arg.pattern, arg.p, help=hs.pattern, nargs="+", default=[defaults.pattern])
        parser.add_argument(arg.repeat, arg.r, help=hs.repeat, action='store_true')
        parser.add_argument(arg.sleep, arg.s, help=hs.sleep, default=defaults.sleep)

    def _setup_commands(self) -> None:
        """setup all commands"""
        for command, operation_class in self.commands.items():
            subparser = self.subparsers.add_parser(command)
            self._add_common_arguments(subparser)
            operation_class.add_arguments(subparser)
            subparser.set_defaults(cls=operation_class)

    def execute(self):
        args = self.parser.parse_args()

        if hasattr(args, "cls"):
            operation = args.cls(**vars(args))
            operation.run()
        else:
            self.parser.print_help()

if __name__ == "__main__":
    import sys

    # Емулюємо введення в терміналі:
    # #-----SLICE-----
    # sys.argv = [
    #     "fileManager.py",
    #     "slice",
    #     "./media/",
    #     "./media/imgs/",
    #     "-p", ".mp4", ".MP4",
    #     "-t", ".jpg",
    #     "-r",
    #     "-s", "60",
    #     "-step", "5",
    # ]

    #-----SLICE WITH DELETING-----
    # sys.argv = [
    #     "fileManager.py",
    #     "slice",
    #     "./media/imgs/",
    #     "./media/imgs/",
    #     "-p", ".mp4", ".MP4",
    #     "-t", ".jpg",
    #     # "-r",
    #     "-rm",
    #     "-s", "60",
    #     "-step", "1",
    # ]

    # #-----MOVE-----
    # sys.argv = [
    #     "fileManager.py",
    #     "move",
    #     "./media/imgs/",
    #     "./media/imgs_new/",
    #     "-p", ".jpg",
    #     "-r",
    #     "-s", "30"
    # ]
    #-----DELETE-----
    # sys.argv = [
    #     "fileManager.py",
    #     "delete",
    #     "./media/imgs/",
    #     "-p", ".jpg",
    # ]
    app = FileManager()
    app.execute()