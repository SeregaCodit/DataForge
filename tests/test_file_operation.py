import pytest

from file_operations.move import MoveOperation

def test_pattern_setter():
    operation = MoveOperation(src="./", dst="./")
    operation.pattern = ".jpg"
    assert operation.pattern == (".jpg", )
    assert isinstance(operation.pattern, tuple)

def test_sleep_setter():
    operation = MoveOperation(src="./", dst="./")
    operation.sleep = "30"
    assert operation.sleep == 30

def test_get_files(tmp_path):
    src = tmp_path / "source"
    src.mkdir()

    (src / "video1.mp4").write_text("fake_data")
    (src / "video2.MP4").write_text("fake_data")
    (src / "video3.avi").write_text("fake_data")
    (src / "image.jpg").write_text("fake_data")

    dst = tmp_path / "dst"
    dst.mkdir()
    operation = MoveOperation(src=str(src), dst=str(dst), pattern=(".mp4", ".MP4", ".avi"))
    operation.get_files()

    assert len(operation.files_for_task) == 3
    names = [file.name for file in operation.files_for_task]
    assert "video1.mp4" in names
    assert "video2.MP4" in names
    assert "video3.avi" in names
    assert "image.jpg" not in names

def test_move_files(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "video1.mp4").write_text("fake_data")
    (src / "video2.avi").write_text("fake_data")
    (src / "image1.jpeg").write_text("fake_data")

    dst = tmp_path / "dst"
    dst.mkdir()
    operation = MoveOperation(src=str(src), dst=str(dst), pattern=(".mp4", ".avi"), repeat=False)
    operation.get_files()

    operation.do_task()

    assert not (src / "video1.mp4").exists()
    assert not (src / "video2.avi").exists()
    assert (src / "image1.jpeg").exists()

    assert (dst / "video1.mp4").exists()
    assert (dst / "video2.avi").exists()
    assert not (dst / "image1.jpg").exists()
