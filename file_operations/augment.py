import argparse

from const_utils.arguments import Arguments
from const_utils.default_values import AppSettings
from const_utils.parser_help import HelpStrings
from file_operations.file_operation import FileOperation
from services.augmenter.augmenter_factory import AugmenterFactory
from services.augmenter.base_augmenter import BaseAugmenter


class AugmentOperation(FileOperation):
    def __init__(self, settings: AppSettings, **kwargs):
        super().__init__(settings, **kwargs)

        self.settings = settings

        self.augmenter: BaseAugmenter = AugmenterFactory.get_augmenter(settings, method=self.settings.augment_method)

    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            Arguments.datatype,
            help=HelpStrings.datatype,
            default=settings.datatype,
        )

        parser.add_argument(
            Arguments.core_size,
            help=HelpStrings.core_size,
            default=settings.core_size,
        )

        parser.add_argument(
            Arguments.n_jobs,
            help=HelpStrings.n_jobs,
            default=settings.n_jobs,
        )

        parser.add_argument(
            Arguments.augment_method,
            help=HelpStrings.augment_method,
            default=settings.augment_method,
        )

    def do_task(self):
        cache_file = self.files_for_task[0]
        df = self.augmenter.cache_io.load(cache_file)
        df = self.augmenter.select_candidates(df)
        candidates = df["is_candidate"]

        # data_gaps = self.augmenter.get_data_gaps(df=df, bins=50)
        self.logger.info(f"Augmenting {self.settings.core_size}")
        print()
