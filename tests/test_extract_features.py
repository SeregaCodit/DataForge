import pytest
from tools.stats.extractor import FeatureExtractor


@pytest.fixture
def base_data():
    """Standard  VOC structure for tests"""
    return {
        "size": {"width": 100, "height": 100, "depth": 3},
        "object": []
    }


def test_extract_center_object(base_data):
    """20x20 object straight in center"""
    base_data["object"] = {
        "name": "car",
        "bndbox": {"xmin": 40, "ymin": 40, "xmax": 60, "ymax": 60}
    }
    results = FeatureExtractor.extract_features("test.xml", base_data)

    assert len(results) == 1
    res = results[0]
    assert res["object_in_center"] == 1
    assert res["object_in_right_side"] == 0
    assert res["object_in_left_top"] == 0
    assert res["object_relative_area"] == 0.04  # 400 / 10000


def test_extract_top_left_quadrant(base_data):
    # Об'єкт у верхньому лівому куті (не торкається центру)
    """Object is in the top left corner (doesn't touching center)"""
    base_data["object"] = {
        "name": "car",
        "bndbox": {"xmin": 5, "ymin": 5, "xmax": 20, "ymax": 20}
    }
    results = FeatureExtractor.extract_features("test.xml", base_data)
    res = results[0]
    assert res["object_in_left_top"] == 1
    assert res["object_in_center"] == 0
    assert res["truncated_left"] == 0


def test_truncation_detection(base_data):
    """Truncation detection mode. Object is truncated in left side"""
    base_data["object"] = {
        "name": "car",
        "bndbox": {"xmin": "2", "ymin": "20", "xmax": "30", "ymax": "50"}
    }
    results = FeatureExtractor.extract_features("test.xml", base_data, margin_threshold=5)
    res = results[0]
    assert res["truncated_left"] == 1
    assert res["truncated_right"] == 0


def test_zero_image_size(base_data):
    base_data["size"] = {"width": 0, "height": 0}
    results = FeatureExtractor.extract_features("test.xml", base_data)
    assert results == []


def test_multiple_objects_flag(base_data):
    base_data["object"] = [
        {"name": "car", "bndbox": {"xmin": 0, "ymin": 0, "xmax": 10, "ymax": 10}},
        {"name": "dog", "bndbox": {"xmin": 20, "ymin": 20, "xmax": 30, "ymax": 30}}
    ]
    results = FeatureExtractor.extract_features("test.xml", base_data)
    assert len(results) == 2
    assert results[0]["has_neighbors"] == 1
    assert results[1]["class_name"] == "dog"