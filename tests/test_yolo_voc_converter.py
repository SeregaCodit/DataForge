import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import MagicMock
from tools.annotation_converter.converter.yolo_voc_converter import YoloVocConverter


@pytest.fixture
def converter(tmp_path):
    """Creates an instance of converter with temporary pathes"""
    return YoloVocConverter(
        source_format="yolo",
        dest_format="voc",
        extensions=(".jpg", ".jpeg", ".png"),
        labels_path=tmp_path / "labels",
        img_path=tmp_path / "images",
    )


@pytest.fixture
def mock_dependencies():
    """Creates fake reader and writer"""
    reader = MagicMock()
    writer = MagicMock()
    return reader, writer


def test_img_path_setter_logic(converter, tmp_path):
    """Test of automatic path definition logic """

    # if img_path is not defined (None), it must be set same the labels_path
    converter.img_path = None
    assert converter.img_path == converter.labels_path

    # definition via string
    converter.img_path = str(tmp_path / "custom")
    assert isinstance(converter.img_path, Path)
    assert converter.img_path.name == "custom"


def test_math_yolo_to_voc_conversion(converter, tmp_path, mock_dependencies):
    """Test of math yolo to voc conversion accuracy"""
    reader, writer = mock_dependencies

    # create test image 100 x 100
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    img_path = img_dir / "test.jpg"
    cv2.imwrite(str(img_path), np.zeros((100, 100, 3), dtype=np.uint8))

    # setting up shared memory of path's
    YoloVocConverter._init_worker({"test": str(img_path)})

    # Expected pixels: xmin=40, ymin=40, xmax=60, ymax=60
    reader.read.return_value = {"0 0.5 0.5 0.2 0.2": None}
    class_mapping = {"0": "car"}

    # Act
    success = converter._convert_worker(
        file_path=Path("test.txt"),
        destination_path=tmp_path / "out",
        reader=reader,
        writer=writer,
        class_mapping=class_mapping,
        suffix=".xml"
    )

    # Assert
    assert success is True

    args, *data = writer.write.call_args
    xml_dict = data[0]

    assert "xmin>40</xmin" in xml_dict["data"]
    assert "xmax>60</xmax" in xml_dict["data"]
    assert "ymin>40</ymin" in xml_dict["data"]
    assert "ymax>60</ymax" in xml_dict["data"]
    assert "name>car</name" in xml_dict["data"]


def test_worker_skips_missing_images(converter, tmp_path, mock_dependencies):
    """worker must return False if an image doesn't found in the map"""
    reader, writer = mock_dependencies
    YoloVocConverter._init_worker({})  # порожня мапа

    success = converter._convert_worker(
        file_path=Path("missing.txt"),
        destination_path=tmp_path / "out",
        reader=reader,
        writer=writer,
        class_mapping={},
        suffix=".xml"
    )
    assert success is False


@pytest.mark.parametrize("yolo_line, expected_truncated", [
    ("0 0.5 0.5 0.2 0.2", 0),  # in center and not truncated
    ("0 0.05 0.5 0.1 0.2", 1),  # touching left boarder (0.05 - 0.1/2 = 0) - Truncated
])
def test_truncated_flag_logic(converter, tmp_path, mock_dependencies, yolo_line, expected_truncated):
    """Test automatic definition of truncated objects"""
    reader, writer = mock_dependencies

    img_dir = tmp_path / "images"
    img_dir.mkdir(exist_ok=True)
    img_path = img_dir / "test.jpg"
    cv2.imwrite(str(img_path), np.zeros((100, 100, 3), dtype=np.uint8))

    YoloVocConverter._init_worker({"test": str(img_path)})
    reader.read.return_value = {yolo_line: None}

    converter._convert_worker(
        file_path=Path("test.txt"),
        destination_path=tmp_path / "out",
        reader=reader,
        writer=writer,
        class_mapping={"0": "obj"},
        suffix=".xml"
    )

    _, *args = writer.write.call_args
    assert f"<truncated>{expected_truncated}</truncated>" in args[0]["data"]