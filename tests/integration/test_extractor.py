import pytest
from pathlib import Path
import zipfile
import json
import shutil
import asyncio

from beatcrafter_ai.extractor.extract_maps import MapExtractor
from beatcrafter_ai.downloader.scrape_and_download import BeatSaverDownloader

# Optional package for progress bars
tqdm = pytest.importorskip("tqdm")

@pytest.fixture
def extractor(temp_zip_dir, temp_extract_dir):
    """Create an extractor instance with test data."""
    return MapExtractor(temp_zip_dir, temp_extract_dir)

def test_extract_real_map(extractor):
    """Test extracting a real Beat Saber map."""
    zip_path = next(extractor.zip_dir.glob('*.zip'))
    result = extractor.extract_map(zip_path)
    
    # Verify no errors occurred
    assert not result['has_errors']
    
    # Verify basic structure
    assert result['song_id'] == 'test_data'
    assert result['info'] is not None
    assert isinstance(result['info'], dict)
    
    # Verify required info.dat fields
    assert '_songName' in result['info']
    assert '_songAuthorName' in result['info']
    assert '_difficultyBeatmapSets' in result['info']
    
    # Verify difficulties were extracted
    assert len(result['difficulties']) > 0, "Should have at least one difficulty"
    for diff_name, diff_data in result['difficulties'].items():
        # Check for either old format (_notes) or new format (colorNotes/basicBeatmapEvents)
        assert any(key in diff_data for key in ['_notes', 'colorNotes', 'basicBeatmapEvents']), \
            f"Difficulty {diff_name} missing notes data"
        assert any(key in diff_data for key in ['_obstacles', 'obstacles']), \
            f"Difficulty {diff_name} missing obstacles data"
        assert any(key in diff_data for key in ['_events', 'basicBeatmapEvents']), \
            f"Difficulty {diff_name} missing events data"
    
    # Verify audio file was found
    assert result['audio_file'] is not None, "Audio file should be present"
    assert result['audio_file'].endswith('.egg') or result['audio_file'].endswith('.ogg'), \
        "Audio file should be .egg or .ogg format"
    
    # Verify file structure
    map_dir = extractor.get_extracted_map_path(result['song_id'])
    assert map_dir is not None, "Extracted map directory should exist"
    assert (map_dir / 'info.dat').exists(), "info.dat should exist"
    
    # Verify at least one difficulty file exists
    diff_files = list(map_dir.glob('*.dat'))
    assert len(diff_files) > 1, "Should have info.dat and at least one difficulty file"

@pytest.mark.asyncio
async def test_download_and_extract_integration(temp_download_dir, temp_extract_dir):
    """Integration test: Download maps and extract them."""
    # Download a few maps
    downloader = BeatSaverDownloader(max_pages=1)
    downloader.download_path = temp_download_dir
    download_results = await downloader.download_all()
    
    # Verify we have some successful downloads
    assert any(download_results), "Should have at least one successful download"
    downloaded_files = list(temp_download_dir.glob('*.zip'))
    assert len(downloaded_files) > 0, "No files were downloaded"
    
    # Extract the downloaded maps
    extractor = MapExtractor(temp_download_dir, temp_extract_dir)
    results = extractor.extract_all()
    
    # Verify extraction results
    assert len(results) > 0, "No maps were extracted"
    for result in results:
        assert not result['has_errors'], f"Extraction failed for {result['song_id']}"
        assert result['info'] is not None, "Missing info.dat data"
        assert len(result['difficulties']) > 0, "No difficulties found"
        assert result['audio_file'] is not None, "Missing audio file"
        
        # Verify file structure for each map
        map_dir = extractor.get_extracted_map_path(result['song_id'])
        assert map_dir is not None, f"Missing directory for {result['song_id']}"
        assert (map_dir / 'info.dat').exists(), "Missing info.dat file"
        
        # Verify difficulty files
        diff_files = list(map_dir.glob('*.dat'))
        assert len(diff_files) > 1, "Should have info.dat and at least one difficulty file"
        
        # Verify audio file
        audio_path = map_dir / Path(result['audio_file']).name
        assert audio_path.exists(), "Audio file not found"

def test_extract_all_with_real_data(extractor):
    """Test bulk extraction with real test data."""
    results = extractor.extract_all()
    
    # Verify we got results
    assert len(results) > 0, "No maps were extracted"
    assert all(not r['has_errors'] for r in results), "Some extractions failed"
    
    # Verify each extracted map
    for result in results:
        # Check basic structure
        assert 'song_id' in result, "Missing song_id"
        assert 'info' in result, "Missing info data"
        assert 'difficulties' in result, "Missing difficulties"
        assert 'audio_file' in result, "Missing audio file"
        
        # Verify files were extracted
        map_dir = extractor.get_extracted_map_path(result['song_id'])
        assert map_dir is not None, f"Missing directory for {result['song_id']}"
        assert (map_dir / 'info.dat').exists(), "Missing info.dat file"
        
        # Verify difficulty files match info.dat
        if '_difficultyBeatmapSets' in result['info']:
            for beatmap_set in result['info']['_difficultyBeatmapSets']:
                for diff_map in beatmap_set['_difficultyBeatmaps']:
                    diff_file = map_dir / diff_map['_beatmapFilename']
                    assert diff_file.exists(), f"Missing difficulty file: {diff_map['_beatmapFilename']}"

def test_extraction_error_handling(extractor):
    """Test error handling with corrupted/invalid files."""
    # Create a corrupted ZIP
    corrupt_zip = extractor.zip_dir / "corrupt.zip"
    with open(corrupt_zip, 'wb') as f:
        f.write(b'PK\x03\x04' + b'corrupted data')
    
    result = extractor.extract_map(corrupt_zip)
    assert result['has_errors'], "Should fail on corrupted ZIP"
    
    # Test with missing required files
    empty_zip = extractor.zip_dir / "empty.zip"
    with zipfile.ZipFile(empty_zip, 'w') as zf:
        zf.writestr('dummy.txt', 'dummy content')
    
    result = extractor.extract_map(empty_zip)
    assert result['has_errors'], "Should fail on missing required files"
    
    # Verify these failed extractions don't affect valid ones
    results = extractor.extract_all()
    assert len(results) > 0, "Should still extract valid test data"
    assert all(not r['has_errors'] for r in results), "Valid extractions should succeed" 