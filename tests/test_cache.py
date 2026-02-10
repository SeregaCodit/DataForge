import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from tools.cache import CacheIO

@pytest.fixture
def cache_io(settings):
    return CacheIO(settings)


def test_generate_cache_filename_auto(cache_io, tmp_path):
    """Checks if automatic filename generation is stable and contains kwargs."""
    folder = tmp_path / "my images"
    folder.mkdir()

    name = cache_io.generate_cache_filename(folder, None, method="dhash", size=16)

    assert name.startswith("cache_")
    assert "my_images" in name
    assert "_method_dhash" in name
    assert "_size_16" in name
    assert name.endswith(".parquet")


def test_generate_cache_filename_manual(cache_io, tmp_path):
    """Checks if manual name correctly appends version suffix."""
    folder = tmp_path / "data"
    manual = "custom_export"

    name = cache_io.generate_cache_filename(folder, manual, size=32)

    assert name == "custom_export__size_32.parquet"


def test_save_and_load_dict(cache_io, tmp_path):
    """Tests saving a dictionary of hashes and loading it back as a DataFrame."""
    cache_file = tmp_path / "test_hashes.parquet"
    test_data = {
        Path("/tmp/img1.jpg"): np.array([True, False, True], dtype=bool),
        Path("/tmp/img2.jpg"): np.array([False, False, True], dtype=bool)
    }

    # Save
    cache_io.save(test_data, cache_file)
    assert cache_file.exists()

    # Load
    df = cache_io.load(cache_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "path" in df.columns
    assert "hash" in df.columns


def test_save_and_load_dataframe(cache_io, tmp_path):
    """Tests saving and loading a native pandas DataFrame."""
    cache_file = tmp_path / "stats.parquet"
    df_original = pd.DataFrame({
        "class_name": ["car", "dog"],
        "area": [0.5, 0.1]
    })

    cache_io.save(df_original, cache_file)
    df_loaded = cache_io.load(cache_file)

    assert not df_loaded.empty
    assert df_loaded.iloc[0]["class_name"] == "car"
    assert df_loaded.iloc[1]["area"] == 0.1


def test_load_non_existent_file(cache_io, tmp_path):
    """Ensures that loading a missing file returns an empty DataFrame."""
    fake_path = tmp_path / "ghost.parquet"
    df = cache_io.load(fake_path)
    assert df.empty


def test_save_invalid_type(cache_io, tmp_path):
    """Checks if passing invalid data types raises a TypeError."""
    with pytest.raises(TypeError):
        cache_io.save(["not", "a", "dict"], tmp_path / "fail.parquet")