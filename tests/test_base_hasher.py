import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch
from tools.comparer.img_comparer.hasher.dhash import DHash


@pytest.fixture
def mock_cache_io():
    return MagicMock()


@pytest.fixture
def hasher(settings, mock_cache_io):
    """Create hasher with mock CacheIO."""
    return DHash(settings=settings, cache_io=mock_cache_io)


def test_df_to_hash_map_conversion(hasher):
    """Test convertion from Pandas back to Dict[Path, np.array]."""
    test_df = pd.DataFrame([
        {'path': '/tmp/1.jpg', 'hash': [True, False]},
        {'path': '/tmp/2.jpg', 'hash': [False, True]}
    ])

    result = hasher._df_to_hash_map(test_df)

    assert len(result) == 2
    assert isinstance(list(result.keys())[0], Path)
    assert isinstance(list(result.values())[0], np.ndarray)
    assert result[Path('/tmp/1.jpg')][0] == True


def test_validate_hash_map_sync(hasher):
    """Synchronization test: removing old files and detecting new ones."""
    # Дані в кеші (один файл видалено з диска)
    existing_hash_map = {
        Path("old.jpg"): np.array([True]),
        Path("stay.jpg"): np.array([True])
    }

    current_paths = (Path("stay.jpg"), Path("new.jpg"))

    with patch.object(hasher, 'update_hashes', return_value=[np.array([False])]):
        is_valid, final_map = hasher.validate_hash_map(current_paths, existing_hash_map)

        assert is_valid is False
        assert Path("old.jpg") not in final_map
        assert Path("stay.jpg") in final_map
        assert Path("new.jpg") in final_map


def test_get_hashmap_cache_hit(hasher, mock_cache_io):
    """Test that when cache is valid, no new hash calculations are performed."""
    path = Path("test.jpg")
    test_df = pd.DataFrame([{'path': str(path), 'hash': [True]}])

    mock_cache_io.load.return_value = test_df

    with patch.object(hasher, 'update_hashes') as mock_update:
        result = hasher.get_hashmap((path,))

        assert path in result
        mock_update.assert_not_called()  # Важливо: ми не рахували заново


def test_find_duplicates_vectorization(hasher):
    """Test that find_duplicates correctly identifies duplicates based on the threshold."""
    # Два однакові хеші, один різний
    h1 = np.array([True, True, False], dtype=bool)
    h2 = np.array([True, True, False], dtype=bool)  # дублікат h1
    h3 = np.array([False, False, False], dtype=bool)  # унікальний

    hash_map = {
        Path("1.jpg"): h1,
        Path("2.jpg"): h2,
        Path("3.jpg"): h3
    }

    hasher._threshold = 0
    duplicates = hasher.find_duplicates(hash_map)

    assert len(duplicates) == 1
    assert Path("2.jpg") in duplicates


def test_n_jobs_clamping(hasher):
    """Test that n_jobs is clamped to a valid range based on CPU cores."""
    import multiprocessing
    cores = multiprocessing.cpu_count()

    hasher.n_jobs = 999
    assert hasher.n_jobs == cores - 1 if cores > 1 else 1

    hasher.n_jobs = 0
    assert hasher.n_jobs == 1


def test_threshold_recalculation_on_core_size_change(hasher):
    """Test that changing core_size correctly updates the threshold in bits."""
    hasher.threshold = 10  # 10%
    hasher.core_size = 8  # 64 bits -> threshold 6
    assert hasher.threshold == 6

    hasher.core_size = 16  # 256 bits -> threshold 25
    assert hasher.threshold == 25