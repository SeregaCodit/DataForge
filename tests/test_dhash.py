import io
import multiprocessing
import os
import tempfile
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import pytest
from unittest.mock import patch

from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
from tools.comparer.img_comparer.hasher.dhash import DHash


#-----FIXTURES-----

@pytest.fixture
def settings():
    settings = AppSettings.load_config(Constants.config_file)
    return settings

@pytest.fixture
def hasher(settings):
    """create instance of DHash"""
    hasher = DHash(settings)
    hasher.core_size = 16
    hasher.threshold = 10
    return hasher

@pytest.fixture
def create_test_image(tmp_path):
    """
        a fixture for creating real test image in temp folder. After testing the image will be deleted
        The image will be just a simple gradient that changing pixel bright from left to right
    """
    def _generate(filename: str, width: int = 100, height: int = 100):
        img_path = tmp_path / filename
        img = np.tile(np.linspace(0, 255, width, dtype=np.uint8), (height, 1))
        cv2.imwrite(str(img_path), img)
        return img_path
    return _generate


def create_temp_img_file(color=(255, 0, 0), quality=100, noise=False):
    """Створює тимчасовий файл зображення і повертає шлях до нього."""
    # Створюємо тимчасовий файл з розширенням .jpg
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    img = Image.new('RGB', (100, 100), color)

    if noise:
        for x in range(40, 60):
            for y in range(40, 60):
                img.putpixel((x, y), (0, 255, 0))

    img.save(temp_file.name, format="JPEG", quality=quality)
    temp_file.close()
    return temp_file.name

@pytest.mark.parametrize("input_value, expected_vals", [
    (0.1, 0),    # int(0.1) * (16*16) = 0
    (10, 25),    # int((10 / 100 ) * (16*16)) = 25
    (1, 2),       # int(1 / 100) * (16*16) = 2
])

#-----TEST-----

def test_threshold(hasher, input_value, expected_vals):
    """test threshold setter"""

    hasher.threshold = input_value
    assert isinstance(hasher.threshold, int)
    assert hasher.threshold == expected_vals


@pytest.mark.parametrize("input_value, expected_val", [
    (16, 16),
    ((10, 25), 10),
    (17.5, 17),
    ("8", 8)
])
def test_core_size(hasher, input_value, expected_val):

    hasher.core_size = input_value

    assert isinstance(hasher.core_size, int)
    assert hasher.core_size == expected_val


@pytest.mark.parametrize("input_value, expected_value", [
    (100, multiprocessing.cpu_count() - 1 if multiprocessing.cpu_count() > 1 else 1),
    (0, 1),
    (-5, 1),
    ("4", 4 if multiprocessing.cpu_count() > 4 else multiprocessing.cpu_count() - 1),
])
def test_n_jobs_clamping(hasher, input_value, expected_value):
    hasher.n_jobs = input_value

    assert isinstance(hasher.n_jobs, int)
    assert hasher.n_jobs == expected_value


@pytest.mark.parametrize("input_value, expected_val", [
    (16, 16 * 16),
    ((10, 25), 10 * 10),
    (17.5, 17 * 17),
    ("8", 8 * 8)
])
def test_compute_hash_returns_correct_shape(hasher, create_test_image, input_value, expected_val):
    # Arrange
    hasher.core_size = input_value
    image_path = create_test_image("valid.jpg")

    # Act
    result = hasher.compute_hash(image_path=image_path, core_size=hasher.core_size)

    # Assert
    assert result is not None
    assert isinstance(result, np.ndarray)
    # the shape must be core_size * core_size (16*16=256)
    assert result.shape == (expected_val,)
    assert result.dtype == bool

def test_compute_hash_with_invalid_file(hasher, tmp_path):
    # Arrange
    not_an_image = tmp_path / "text.txt"
    not_an_image.write_text("This is not a picture")

    # Act
    result = hasher.compute_hash(not_an_image, hasher.core_size)

    # Assert
    assert result is None

def test_compute_hash_consistency(hasher, create_test_image):
    # the same input must give the same result
    img_path = create_test_image("consistent.png")

    hash1 = hasher.compute_hash(img_path, hasher.core_size)
    hash2 = hasher.compute_hash(img_path, hasher.core_size)

    assert np.array_equal(hash1, hash2)


def test_threshold_conversion(hasher):
    """Перевірка, що відсоток правильно конвертувався в біти"""
    hasher.core_size = 8
    hasher.threshold = 10
    assert hasher.threshold == 6

def test_find_duplicates(hasher):
    """
    Тестуємо схожість у межах 10% (поріг 6 бітів).
    Відрізняються у 4 бітах — це має бути дублікат.
    """
    h1 = np.zeros(64, dtype=bool)
    h2 = np.zeros(64, dtype=bool)
    h2[:4] = True  # відстань 4 (менше за поріг 6)

    hashmap = {Path("img1.jpg"): h1, Path("img2.jpg"): h2}

    result = hasher.find_duplicates(hashmap)
    assert Path("img2.jpg") in result

def test_find_duplicates_outside_percentage(hasher):
    """
    Тестуємо різницю понад 10%.
    Відрізняються у 10 бітах — це НЕ дублікат.
    """
    hasher.core_size = 8
    hasher.threshold = 10
    h1 = np.zeros(64, dtype=bool)
    h2 = np.zeros(64, dtype=bool)
    h2[:10] = True  # відстань 10 (більше за поріг 6)

    hashmap = {Path("img1.jpg"): h1, Path("img2.jpg"): h2}

    result = hasher.find_duplicates(hashmap)
    assert result == []

def test_find_duplicates_logic_flow(hasher):
    """
    Перевірка логічного ланцюжка.
    A і B схожі (відст 2) -> B дублікат.
    A і C схожі (відст 3) -> C дублікат.
    """
    h_a = np.zeros(64, dtype=bool)
    h_b = np.zeros(64, dtype=bool); h_b[:2] = True
    h_c = np.zeros(64, dtype=bool); h_c[:3] = True

    hashmap = {
        Path("A.jpg"): h_a,
        Path("B.jpg"): h_b,
        Path("C.jpg"): h_c
    }

    result = hasher.find_duplicates(hashmap)

    assert len(result) == 2
    assert Path("B.jpg") in result
    assert Path("C.jpg") in result
    assert Path("A.jpg") not in result


def test_identical_with_different_compression(hasher):
    # 1. Створюємо оригінал та стиснену копію як реальні файли
    path_orig = Path(create_temp_img_file(color=(100, 150, 200), quality=100))
    path_comp = Path(create_temp_img_file(color=(100, 150, 200), quality=10))  # низька якість

    hasher.core_size = 8
    hasher.threshold = 5

    try:
        hash_map = {
            path_orig: hasher.compute_hash(path_orig, hasher.core_size),
            path_comp: hasher.compute_hash(path_comp, hasher.core_size),
        }
        assert hasher.find_duplicates(hash_map), "Мали бути дублікатами при малому core_size"
    finally:
        # Видаляємо тимчасові файли
        if os.path.exists(path_orig): os.remove(path_orig)
        if os.path.exists(path_comp): os.remove(path_comp)

@pytest.mark.parametrize(
    "input_value, expected_value",
    [
        (8, False), # images should not be duplicates because details become unimportant
        (32, True)  # images should be duplicates because details become more important
    ]
)
def test_different_images_with_similar_composition(hasher, input_value, expected_value):
    # Створюємо два різних зображення (різні кольори)
    path_img1 = Path(create_temp_img_file(color=(0, 0, 255), noise=True))  # Синє з шумом
    path_img2 = Path(create_temp_img_file(color=(0, 0, 255), noise=False))  # Просто синє

    hasher.core_size = input_value
    hasher.threshold = 5

    try:
        hash_map = {
            path_img1: hasher.compute_hash(path_img1, hasher.core_size),
            path_img2: hasher.compute_hash(path_img2, hasher.core_size),
        }

        result = hasher.find_duplicates(hash_map)
        assert bool(result) == expected_value
    finally:
        if os.path.exists(path_img1): os.remove(path_img1)
        if os.path.exists(path_img2): os.remove(path_img2)