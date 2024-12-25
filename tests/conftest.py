import pytest
import shutil
from pathlib import Path

@pytest.fixture
def temp_download_dir(tmp_path):
    """Create a temporary download directory for tests."""
    download_dir = tmp_path / "test_songs"
    download_dir.mkdir()
    yield download_dir
    # Cleanup after test
    shutil.rmtree(download_dir) 