import pytest
from pathlib import Path
from const_utils.default_values import AppSettings


@pytest.fixture(scope="session")
def settings(tmp_path_factory):
    temp_log_dir = tmp_path_factory.mktemp("test_logs")
    conf = AppSettings(
        log_path=temp_log_dir,
        n_jobs=2
    )
    return conf