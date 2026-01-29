import pytest

from const_utils.copmarer import Constants
from const_utils.default_values import AppSettings
from file_operations.move import MoveOperation
@pytest.fixture
def settings():
    settings = AppSettings.load_config(Constants.config_file)
    return settings

def test_pattern_setter(settings):
    operation = MoveOperation(settings=settings, src="./", dst="./")
    operation.pattern = ".jpg"
    assert operation.pattern == (".jpg", )
    assert isinstance(operation.pattern, tuple)

def test_sleep_setter(settings):
    operation = MoveOperation(settings=settings, src="./", dst="./")
    operation.sleep = "30"
    assert operation.sleep == 30

def test_get_files(tmp_path, settings):
    src = tmp_path / "source"
    src.mkdir()

    (src / "video1.mp4").write_text("fake_data")
    (src / "video2.MP4").write_text("fake_data")
    (src / "video3.avi").write_text("fake_data")
    (src / "image.jpg").write_text("fake_data")

    dst = tmp_path / "dst"
    dst.mkdir()
    operation = MoveOperation(settings=settings, src=str(src), dst=str(dst), pattern=(".mp4", ".MP4", ".avi"))
    files_for_task = operation.get_files(source_directory=operation.source_directory, pattern=operation.pattern)

    assert len(files_for_task) == 3
    names = [file.name for file in files_for_task]
    assert "video1.mp4" in names
    assert "video2.MP4" in names
    assert "video3.avi" in names
    assert "image.jpg" not in names

def test_move_files(tmp_path, settings):
    src = tmp_path / "source"
    src.mkdir()
    (src / "video1.mp4").write_text("fake_data")
    (src / "video2.avi").write_text("fake_data")
    (src / "image1.jpeg").write_text("fake_data")

    dst = tmp_path / "dst"
    dst.mkdir()
    operation = MoveOperation(settings=settings, src=str(src), dst=str(dst), pattern=(".mp4", ".avi"), repeat=False)
    operation.files_for_task = operation.get_files(source_directory=operation.source_directory, pattern=operation.pattern)

    operation.do_task()

    assert not (src / "video1.mp4").exists()
    assert not (src / "video2.avi").exists()
    assert (src / "image1.jpeg").exists()

    assert (dst / "video1.mp4").exists()
    assert (dst / "video2.avi").exists()
    assert not (dst / "image1.jpg").exists()
