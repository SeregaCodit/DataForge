from typing import Union

import cv2
import numpy as np


def compute_dhash(image_data: np.ndarray, core_size: int) -> Union[np.ndarray, None]:
    """
    Calculates a dual-axis structural dHash for an image or object crop.

    This method generates a robust bit-signature by analyzing brightness
    gradients in two directions. It captures both vertical and horizontal
    structural edges, making it highly effective for identifying unique
    object silhouettes in a dataset.

    The process includes:
    1. Loading the image in grayscale mode.
    2. Resizing to (core_size + 1, core_size + 1) to support dual-axis
       difference calculation.
    3. Computing horizontal differences (detects vertical structures).
    4. Computing vertical differences (detects horizontal structures).
    5. Concatenating both into a single high-dimensional feature vector.

    Args:
        image_data (np.ndarray): A 2D NumPy array representing the grayscale image data.
        core_size (int): The base resolution for hashing. For a core_size
            of 8, the resulting vector length is 144 bits (2 * 8 * 9).

    Returns:
        Union[np.ndarray, None]: A 1D boolean NumPy array representing the
            dual-gradient hash. Returns None if the image cannot be read.
    """
    # Resize to N+1 to allow calculation of N differences in both axes
    resized_image = cv2.resize(image_data, (core_size + 1, core_size + 1), interpolation=cv2.INTER_AREA)

    gradient_difference_horizontal = resized_image[:, 1:] > resized_image[:, :-1]
    gradient_difference_vertical = resized_image[1:, :] > resized_image[:-1, :]
    full_hash = np.hstack((gradient_difference_horizontal.flatten(), gradient_difference_vertical.flatten()), dtype="int8")
    return full_hash