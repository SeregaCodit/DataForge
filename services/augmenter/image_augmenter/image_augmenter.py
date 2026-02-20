from abc import ABC, abstractmethod
from concurrent.futures.process import ProcessPoolExecutor
from functools import partial
from typing import Type, Iterable, List, Tuple

import cv2
import numpy as np
import pandas as pd

from services.augmenter.base_augmenter import BaseAugmenter
from services.to_dhash import compute_dhash
from tools.comparer.img_comparer.hasher.dhash import DHash


class ImageAugmenter(BaseAugmenter, ABC):

    def __init__(self, settings):
        super().__init__(settings)
        pass

    def get_unique_objects(self, df: pd.DataFrame):
        hahses = self._compute_hashes(df=df)
        df["obj_hash"] = hahses

        for class_name in df["class_name"].unique():
            mask = df["class_name"] == class_name
            class_hashes = np.stack(df.loc[mask, "obj_hash"].values)

            consensus = self._get_consensus_hash(class_hashes)

            df.loc[mask, "uniqueness_score"] = np.count_nonzero(
                class_hashes != consensus, axis=1
            )

        return df




    def _compute_hashes(self, df: pd.DataFrame) -> pd.Series:
        task_data = [
            (idx, row["im_path"], row["bbox"])
            for idx, row in df.iterrows()
        ]

        compute_function = partial(
            self._compute_hash_worker,
            core_size=self.settings.core_size
        )

        self.logger.info(f"Starting hash computation for {len(df) } items using {self.settings.n_jobs} workers")

        with ProcessPoolExecutor(max_workers=self.settings.n_jobs) as executor:
            hash_data = list(executor.map(compute_function, task_data))

        hash_map = {idx: h for idx, h in hash_data if h is not None}
        hash_series = pd.Series(hash_map)
        return hash_series

    @staticmethod
    def _get_consensus_hash( hashes_matrix: np.ndarray) -> np.ndarray:
        """
        Calculates the 'Consensus' (majority) hash for a group of hashes.

        Args:
            hashes_matrix (np.ndarray): 2D array of shape (N, total_bits).

        Returns:
            np.ndarray: A 1D boolean array representing the most common bits.
        """
        # Рахуємо кількість '1' у кожній колонці бітів
        # Якщо більше половини об'єктів мають 1, то біт консенсусу = True
        column_sums = np.sum(hashes_matrix, axis=0)
        consensus = column_sums > (len(hashes_matrix) / 2)
        return consensus


    @staticmethod
    def _compute_hash_worker(payload: Tuple[int, str, dict], core_size: int) -> Tuple[int, np.ndarray]:
        idx, im_path, bbox = payload

        ymin, ymax, xmin, xmax = int(bbox["ymin"]), int(bbox["ymax"]), int(bbox["xmin"]), int(bbox["xmax"])
        annotated_object = cv2.imread(im_path, cv2.IMREAD_GRAYSCALE)[ymin: ymax, xmin: xmax]

        dhash = compute_dhash(image_data=annotated_object, core_size=core_size)
        return idx, dhash
