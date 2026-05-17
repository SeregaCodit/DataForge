from typing import Dict, Tuple, Type

from const_utils.default_values import AppSettings
from services.augmenter.base_augmenter import BaseAugmenter
from services.augmenter.image_augmenter.umap_dhash import UmapDhashAugmenter
from tests.test_file_operation import settings


class AugmenterFactory:
    """
    Factory class to create augmenter instances based on the datatype and method specified in the settings.
    Args:
        _strategies (Dict[Tuple[str, str], Type[BaseAugmenter]]) : A mapping of (datatype, method) to the corresponding
         augmenter class.
    """
    _strategies: Dict[Tuple[str, str], Type[BaseAugmenter]] = {
        ("image", "umap_hash"): UmapDhashAugmenter
    }

    @staticmethod
    def get_augmenter(settings: AppSettings, method: str) -> BaseAugmenter:
        """
        Retrieves an augmenter instance based on the datatype and method specified in the settings.
        Args:
            settings (AppSettings): Global configuration containing the datatype.
            method (str): The augmentation method to be used.
        Returns:
            BaseAugmenter: An instance of the augmenter corresponding to the specified datatype and method.
        Raises:
            ValueError: If no augmenter is found for the given datatype and method.
        """
        datatype = settings.datatype
        key = (datatype, method)
        augmenter_class = AugmenterFactory._strategies.get(key)

        if not augmenter_class:
            raise ValueError(f"No augmenter found for datatype '{datatype}' and method '{method}'")

        return augmenter_class(settings=settings)