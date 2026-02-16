import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from tools.stats.voc_stats import VOCStats


@pytest.fixture
def mock_reader():
    """Create fake reader object."""
    reader = MagicMock()
    reader.read.return_value = {
        "annotation": {
            "size": {"width": 100, "height": 100, "depth": 3},
            "object": [{"name": "car", "bndbox": {"xmin": 10, "ymin": 10, "xmax": 20, "ymax": 20}}]
        }
    }
    return reader


def test_voc_analyze_worker_success(mock_reader):
    """test successful processing of valid file"""
    file_path = Path("test_image.xml")

    results = VOCStats._analyze_worker(file_path, mock_reader, margin_threshold=5)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["class_name"] == "car"
    assert results[0]["path"] == str(file_path)


def test_voc_analyze_worker_invalid_xml(mock_reader):
    """Test with invalid xml file."""
    mock_reader.read.return_value = {}

    results = VOCStats._analyze_worker(Path("bad.xml"), mock_reader)

    assert results == []



@patch("tools.stats.extractor.FeatureExtractor.extract_features")
def test_voc_analyze_worker_exception_handling(mock_extractor, mock_reader):
    """Test the worker does not fail handling unexpected error"""
    mock_extractor.side_effect = Exception("System Crash")

    results = VOCStats._analyze_worker(Path("test.xml"), mock_reader)

    assert results == []