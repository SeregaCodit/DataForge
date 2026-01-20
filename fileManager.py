import argparse
from const_utils.parser_help import HelpStrings as hs
from const_utils.commands import Commands as cmd
from const_utils.arguments import Arguments as arg
from const_utils.default_values import DefaultValues as defaults
from file_operations.move import MoveOperation
from file_operations.slice import SliceOperation


class FileManager:
    """Клас, що відповідає за CLI та запуск команд"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="FileManager")
        self.subparsers = self.parser.add_subparsers(dest="command")
        self._setup_commands()

    def _setup_commands(self):
        move_parser = self.subparsers.add_parser(cmd.move, help=hs.move)
        move_parser.add_argument(arg.src, help=hs.src)
        move_parser.add_argument(arg.dst, help=hs.dst)
        move_parser.add_argument(arg.pattern, arg.p, help=hs.pattern, nargs="+", default=[defaults.pattern])
        move_parser.add_argument(arg.repeat, arg.r, help=hs.repeat, action='store_true')
        move_parser.add_argument(arg.sleep, arg.s, help=hs.sleep, default=defaults.sleep)
        move_parser.set_defaults(cls=MoveOperation)

        slice_parser = self.subparsers.add_parser(cmd.slice)
        slice_parser.add_argument(arg.src, help=hs.src)
        slice_parser.add_argument(arg.dst, help=hs.dst)
        slice_parser.add_argument(arg.pattern, arg.p, help=hs.pattern, nargs="+", default=[defaults.pattern])
        slice_parser.add_argument(arg.type, arg.t, help=hs.type, default=defaults.type)
        slice_parser.add_argument(arg.step_sec, arg.step, help=hs.step_sec, default=1)
        slice_parser.add_argument(arg.repeat, arg.r, help=hs.repeat, action='store_true')
        slice_parser.add_argument(arg.sleep, arg.s, help=hs.sleep, default=defaults.sleep)
        slice_parser.set_defaults(cls=SliceOperation)

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


    # sys.argv = [
    #     "fileManager.py",
    #     "move",
    #     "./media/imgs/",
    #     "./media/imgs_new/",
    #     "-p", ".jpg",
    #     "-r",
    #     "-s", "30"
    # ]
    app = FileManager()
    app.execute()