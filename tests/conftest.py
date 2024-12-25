import pytest
import shutil
from pathlib import Path

@pytest.fixture
def temp_download_dir(tmp_path):
    """Create a temporary download directory for tests."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir

@pytest.fixture
def temp_extract_dir(tmp_path):
    """Create a temporary extraction directory for tests."""
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir()
    return extract_dir

@pytest.fixture
def test_data_dir():
    """Get the directory containing test data files."""
    return Path(__file__).parent / "data"

@pytest.fixture
def test_data_zip():
    """Get the path to the test data ZIP file."""
    zip_path = Path(__file__).parent / "test_data.zip"
    assert zip_path.exists(), "test_data.zip must exist in the tests directory"
    return zip_path

@pytest.fixture
def temp_zip_dir(tmp_path, test_data_zip):
    """Create a temporary directory with test ZIP file."""
    zip_dir = tmp_path / "zips"
    zip_dir.mkdir()
    shutil.copy(test_data_zip, zip_dir / test_data_zip.name)
    return zip_dir

# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest-asyncio to use function scope by default."""
    config.option.asyncio_mode = "auto"
    # Set default fixture loop scope to function
    config.option.asyncio_fixture_loop_scope = "function" 