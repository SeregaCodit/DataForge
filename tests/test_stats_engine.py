import pytest
import pandas as pd

from pathlib import Path
from unittest.mock import MagicMock, patch
from tools.stats.voc_stats import VOCStats
from const_utils.stats_constansts import ImageStatsKeys


@pytest.fixture
def voc_stats(settings):
    """A fixture for VOCStats initialization with mocked CacheIO."""
    settings.margin_threshold = 5
    settings.n_jobs = 2

    analyzer = VOCStats(source_format="voc", settings=settings)
    analyzer.cache_io = MagicMock()
    # Мокаємо шлях до зображень, щоб не сканувати реальну папку
    analyzer.img_path = Path("/tmp/fake_images")
    analyzer.extensions = (".jpg",)
    return analyzer


def test_voc_worker_integration():
    """Test the integration of VOCStats worker: does it correctly combine geometry and pixel data?"""
    mock_reader = MagicMock()
    mock_reader.read.return_value = {
        "annotation": {
            "size": {"width": 100, "height": 100, "depth": 3},
            "object": [{"name": "tank", "bndbox": {"xmin": 10, "ymin": 10, "xmax": 20, "ymax": 20}}]
        }
    }

    # imitation of Shared Memory for processes
    fake_img_path = "/tmp/fake_images/img1.jpg"
    VOCStats._init_worker({"img1": fake_img_path})

    with patch("tools.stats.image_analyzer.ImageContentAnalyzer.analyze_metrics") as mock_pixel:
        mock_pixel.return_value = {"img_brightness": 150.0}

        results = VOCStats._analyze_worker(Path("img1.xml"), mock_reader, margin_threshold=5)

        assert len(results) == 1
        assert results[0]["class_name"] == "tank"
        assert results[0]["img_brightness"] == 150.0
        assert "object_in_center" in results[0]


def test_incremental_logic_skips_unchanged_files(voc_stats, tmp_path):
    """Test the incremental logic: if mtime matches, no re-computation should occur."""
    # create a fake file and set its mtime
    test_file = tmp_path / "data.xml"
    test_file.touch()
    path_str = str(test_file.resolve())
    current_mtime = test_file.stat().st_mtime

    # cache emulation: the file is already in cache with the same mtime,
    # so it should be used without re-computation
    df_cached = pd.DataFrame([{
        ImageStatsKeys.path: path_str,
        ImageStatsKeys.mtime: current_mtime,
        "class_name": "tank"
    }])
    voc_stats.cache_io.load.return_value = df_cached

    # PoolExtractor should not be called since the file is unchanged
    with patch("tools.stats.base_stats.ProcessPoolExecutor") as mock_executor:
        df_result = voc_stats.get_features((test_file,))

        # calculations should be skipped, so the executor's map method should not be called
        mock_executor.assert_not_called()
        assert len(df_result) == 1
        assert df_result.iloc[0]["class_name"] == "tank"


def test_incremental_logic_updates_on_mtime_change(voc_stats, tmp_path):
    """Test the incremental logic: if mtime has changed, the file should be re-processed."""

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    ann_dir = tmp_path / "annotations"
    ann_dir.mkdir()

    voc_stats.img_path = img_dir
    voc_stats.extensions = ('.jpg',)

    test_file = ann_dir / "data.xml"
    test_file.touch()
    path_str = str(test_file.resolve())

    # create old cache data with an old mtime (simulate that the file was changed after caching)
    old_mtime = test_file.stat().st_mtime - 1000
    df_cached = pd.DataFrame([{
        ImageStatsKeys.path: path_str,
        ImageStatsKeys.mtime: old_mtime,
        "class_name": "old_data"
    }])
    voc_stats.cache_io.load.return_value = df_cached

    # use patch to intercept ProcessPoolExecutor and return new data as if the worker re-processed the file
    with patch("tools.stats.base_stats.ProcessPoolExecutor") as mock_executor:
        mock_pool = mock_executor.return_value.__enter__.return_value
        mock_pool.map.return_value = [[{
            ImageStatsKeys.path: path_str,
            "class_name": "new_data"
        }]]

        # Act
        df_result = voc_stats.get_features((test_file,))

        # Assert
        assert "new_data" in df_result["class_name"].values
        assert "old_data" not in df_result["class_name"].values
        assert df_result.iloc[0][ImageStatsKeys.mtime] > old_mtime


def test_feature_extractor_edge_case():
    """Math test: object truncated by image edge."""
    from tools.stats.extractor import FeatureExtractor
    data = {
        "size": {"width": 100, "height": 100, "depth": 3},
        "object": [{"name": "car", "bndbox": {"xmin": 0, "ymin": 10, "xmax": 20, "ymax": 50}}]
    }
    results = FeatureExtractor.extract_features(Path("test.xml"), data, margin_threshold=5)

    assert results[0]["truncated_left"] == 1
    assert results[0]["truncated_right"] == 0