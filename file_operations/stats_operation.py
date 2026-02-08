import argparse

from const_utils.default_values import AppSettings
from file_operations.file_operation import FileOperation


class StatsOperation(FileOperation):
    """
    This class show dataset information such as number of files object
    distribution, areas distribution etc. It can be used to get
    insights about the dataset before training a model.
    It can also be used to identify potential issues with the dataset,
    such as class or base features imbalance.
    """

    def __init__(self, settings: AppSettings, **kwargs):
        """Initializes the StatsOperation with settings and specific arguments."""
        super().__init__(settings, **kwargs)

    @staticmethod
    def add_arguments(settings: AppSettings, parser: argparse.ArgumentParser) -> None:
        pass

    def do_task(self):
        """
        This method should implement the logic to calculate and display the statistics of the dataset.
         It can include:
            - Counting the number of files in each class.
            - Calculating the distribution of object areas, positions etc.
            - Identifying any class imbalance issues.
            - Providing insights about the dataset that can help in model training and evaluation.
        """
        pass