import asyncio
import pytest
from pathlib import Path

from ai_beat_saber.downloader.scrape_and_download import BeatSaverDownloader

@pytest.mark.asyncio
async def test_fetch_ranked_maps():
    """Test that we can fetch ranked maps from the API."""
    downloader = BeatSaverDownloader(max_pages=1)
    data = await downloader.fetch_ranked_maps(page=0)
    
    # Verify response structure
    assert "docs" in data
    assert isinstance(data["docs"], list)
    assert len(data["docs"]) > 0
    
    # Verify first song has required fields
    first_song = data["docs"][0]
    assert "id" in first_song
    assert "versions" in first_song
    assert len(first_song["versions"]) > 0
    assert "downloadURL" in first_song["versions"][0]

@pytest.mark.asyncio
async def test_fetch_multiple_pages():
    """Test that we can fetch different pages from the API."""
    downloader = BeatSaverDownloader(max_pages=2)
    
    # Fetch two different pages
    data_page_0 = await downloader.fetch_ranked_maps(page=0)
    data_page_1 = await downloader.fetch_ranked_maps(page=1)
    
    # Verify both pages have data
    assert len(data_page_0["docs"]) > 0
    assert len(data_page_1["docs"]) > 0
    
    # Verify pages are different
    first_id_page_0 = data_page_0["docs"][0]["id"]
    first_id_page_1 = data_page_1["docs"][0]["id"]
    assert first_id_page_0 != first_id_page_1

@pytest.mark.asyncio
async def test_download_single_map(temp_download_dir):
    """Test downloading a single map."""
    downloader = BeatSaverDownloader(max_pages=1)
    downloader.download_path = temp_download_dir
    
    # First fetch a real song from the API
    data = await downloader.fetch_ranked_maps(page=0)
    first_song = data["docs"][0]
    song_id = first_song["id"]
    download_url = first_song["versions"][0]["downloadURL"]
    
    # Create a simple progress bar for testing
    progress = pytest.importorskip("tqdm").tqdm(total=1)
    
    # Download the song
    await downloader.download_map(song_id, download_url, progress)
    
    # Verify the file exists and has content
    zip_path = temp_download_dir / f"{song_id}.zip"
    assert zip_path.exists()
    assert zip_path.stat().st_size > 0

@pytest.mark.asyncio
async def test_download_multiple_pages(temp_download_dir):
    """Test downloading multiple pages of maps."""
    downloader = BeatSaverDownloader(max_pages=2)
    downloader.download_path = temp_download_dir
    
    await downloader.download_all()
    
    # Verify we downloaded some files
    downloaded_files = list(temp_download_dir.glob("*.zip"))
    assert len(downloaded_files) > 0
    
    # Verify each file has content
    for zip_file in downloaded_files:
        assert zip_file.stat().st_size > 0

@pytest.mark.asyncio
async def test_skip_existing_downloads(temp_download_dir):
    """Test that we skip already downloaded files."""
    downloader = BeatSaverDownloader(max_pages=1)
    downloader.download_path = temp_download_dir
    
    # First download
    await downloader.download_all()
    first_count = len(list(temp_download_dir.glob("*.zip")))
    assert first_count > 0
    
    # Second download of same page
    await downloader.download_all()
    second_count = len(list(temp_download_dir.glob("*.zip")))
    
    # Verify we didn't download duplicates
    assert first_count == second_count 