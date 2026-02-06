import pytest
import logging
from pathlib import Path
from typing import Union, List, Tuple
from tools.mixins.file_remover import FileRemoverMixin

class MockLogger:
    def __init__(self):
        self.warnings = []
        self.infos = []

    def warning(self, msg: str):
        self.warnings.append(msg)

    def info(self, msg: str):
        self.infos.append(msg)

class DummyRemover(FileRemoverMixin):
    def __init__(self):
        self.logger = MockLogger()

@pytest.fixture
def remover():
    """Fixture to provide a DummyRemover instance."""
    return DummyRemover()

def test_remove_file_success(remover, tmp_path):
    """Test successful file removal."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    assert test_file.exists()
    result = remover.remove_file(test_file)

    assert result is True
    assert not test_file.exists()
    assert f"{test_file} removed" in remover.logger.infos

def test_remove_file_not_exists(remover, tmp_path):
    """Test removing a file that does not exist."""
    test_file = tmp_path / "non_existent.txt"

    result = remover.remove_file(test_file)

    # According to the code, it returns True because unlink(missing_ok=True) is used
    # and it logs a warning if it's not a file.
    assert result is True
    assert f"{test_file} is not a file" in remover.logger.warnings

def test_remove_all_list(remover, tmp_path):
    """Test removing multiple files using a list."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("1")
    file2.write_text("2")

    remover.remove_all([file1, file2])

    assert not file1.exists()
    assert not file2.exists()

def test_remove_all_tuple(remover, tmp_path):
    """Test removing multiple files using a tuple."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("1")
    file2.write_text("2")

    remover.remove_all((file1, file2))

    assert not file1.exists()
    assert not file2.exists()

def test_remove_all_single_path(remover, tmp_path):
    """Test removing a single file using a Path object."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("1")

    remover.remove_all(file1)

    assert not file1.exists()

def test_remove_all_invalid_type(remover):
    """Test that _remove_all raises TypeError for invalid input."""
    with pytest.raises(TypeError, match="filepaths should be a list or a tuple or a Path"):
        remover.remove_all("not a path")
