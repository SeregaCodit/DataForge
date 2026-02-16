import pytest
import cv2
import numpy as np
from pathlib import Path
from tools.stats.image_analyzer import ImageContentAnalyzer
from const_utils.stats_constansts import ImageStatsKeys


@pytest.fixture
def create_test_image(tmp_path):
    """Fixture to create temporary images for testing."""

    def _generate(filename: str, color: int = 128, blur: bool = False):
        img_path = tmp_path / filename
        # Create a 100x100 grayscale image
        img = np.full((100, 100), color, dtype=np.uint8)

        if blur:
            # Create a very blurry image by filling with a single value
            # or applying a heavy kernel
            img = cv2.GaussianBlur(img, (15, 15), 0)
        else:
            # Add some texture for contrast/blur score (a simple checkerboard)
            img[0:50, 0:50] = 200
            img[50:100, 50:100] = 50

        cv2.imwrite(str(img_path), img)
        return img_path

    return _generate


def test_analyze_metrics_success(create_test_image):
    """Test if metrics are calculated correctly for a valid image."""
    img_path = create_test_image("valid.jpg", color=128)

    metrics = ImageContentAnalyzer.analyze_metrics(img_path)

    assert isinstance(metrics, dict)
    assert ImageStatsKeys.im_brightness in metrics
    assert ImageStatsKeys.im_contrast in metrics
    assert ImageStatsKeys.im_blur_score in metrics

    # For our 128-base checkerboard:
    # Brightness should be roughly the average of 200 and 50
    assert 120 <= metrics[ImageStatsKeys.im_brightness] <= 130


def test_analyze_metrics_invalid_path():
    """Test if an empty dictionary is returned for a non-existent path."""
    fake_path = Path("this/path/does/not/exist.png")
    metrics = ImageContentAnalyzer.analyze_metrics(fake_path)
    assert metrics == {}


def test_blur_detection_logic(create_test_image):
    """Test if a blurred image has a lower score than a sharp one."""
    sharp_path = create_test_image("sharp.jpg", blur=False)
    blurry_path = create_test_image("blurry.jpg", blur=True)

    sharp_metrics = ImageContentAnalyzer.analyze_metrics(sharp_path)
    blurry_metrics = ImageContentAnalyzer.analyze_metrics(blurry_path)

    # Sharpness (Laplacian variance) must be significantly higher for the sharp image
    assert sharp_metrics[ImageStatsKeys.im_blur_score] > blurry_metrics[ImageStatsKeys.im_blur_score]


def test_metrics_types(create_test_image):
    """Verify that returned values are floats as required for Parquet/Pandas."""
    img_path = create_test_image("types.jpg")
    metrics = ImageContentAnalyzer.analyze_metrics(img_path)

    for key in metrics:
        assert isinstance(metrics[key], float)