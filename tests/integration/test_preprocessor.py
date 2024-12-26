import pytest
import asyncio
from pathlib import Path
import mido
import yt_dlp

from beatcrafter_ai.preprocessor.preprocess_song import YouTubePreprocessor

# Optional package for progress bars
tqdm = pytest.importorskip("tqdm")

@pytest.fixture
def preprocessor(tmp_path):
    """Create a YouTubePreprocessor instance for testing."""
    output_dir = tmp_path / "preprocessed"
    return YouTubePreprocessor(output_dir)

@pytest.fixture
def test_youtube_url():
    """Return a test YouTube URL."""
    return "https://www.youtube.com/watch?v=QBgl4rVz3Ks"  

@pytest.mark.asyncio
async def test_download_song(preprocessor, test_youtube_url):
    """Test downloading a song from YouTube."""
    print(f"\nTesting download with URL: {test_youtube_url}")
    result = await preprocessor.download_song(test_youtube_url)
    
    # Detailed error output if download fails
    if result is None:
        pytest.fail("Download failed - check stdout for error messages")
    
    # Verify download succeeded
    assert 'video_id' in result, "Missing video_id in result"
    assert 'title' in result, "Missing title in result"
    assert 'duration' in result, "Missing duration in result"
    assert 'audio_path' in result, "Missing audio_path in result"
    
    # Verify file exists and has content
    audio_path = result['audio_path']
    assert audio_path.exists(), f"Audio file does not exist at {audio_path}"
    assert audio_path.stat().st_size > 0, f"Audio file is empty at {audio_path}"
    assert audio_path.suffix in ['.ogg', '.mp3', '.m4a'], f"Unexpected audio format: {audio_path.suffix}"
    
    print(f"\nDownload successful:")
    print(f"Title: {result['title']}")
    print(f"Duration: {result['duration']}s")
    print(f"Audio file: {audio_path}")

@pytest.mark.asyncio
async def test_process_song(preprocessor, test_youtube_url):
    """Test full song processing pipeline."""
    print(f"\nTesting full processing with URL: {test_youtube_url}")
    result = await preprocessor.process_song(test_youtube_url)
    
    # Detailed error output if processing fails
    if result is None:
        pytest.fail("Processing failed - check stdout for error messages")
    
    # Verify processing succeeded
    assert 'video_id' in result, "Missing video_id in result"
    assert 'audio_path' in result, "Missing audio_path in result"
    assert 'midi_path' in result, "Missing midi_path in result"
    
    # Verify audio file
    audio_path = result['audio_path']
    assert audio_path.exists(), f"Audio file does not exist at {audio_path}"
    assert audio_path.stat().st_size > 0, f"Audio file is empty at {audio_path}"
    
    # Verify MIDI file
    midi_path = result['midi_path']
    assert midi_path.exists(), f"MIDI file does not exist at {midi_path}"
    assert midi_path.stat().st_size > 0, f"MIDI file is empty at {midi_path}"
    
    print(f"\nProcessing successful:")
    print(f"Audio file: {audio_path}")
    print(f"MIDI file: {midi_path}")
    
    # Validate MIDI content
    midi_file = mido.MidiFile(midi_path)
    assert len(midi_file.tracks) > 0, "MIDI file has no tracks"
    
    # Check for note events
    note_events = []
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'note_on':
                note_events.append(msg)
                assert 0 <= msg.note <= 127, f"Invalid note value: {msg.note}"
                assert 0 <= msg.velocity <= 127, f"Invalid velocity value: {msg.velocity}"
    
    assert len(note_events) > 0, "No note events found in MIDI file"
    print(f"Found {len(note_events)} note events in MIDI file")

@pytest.mark.asyncio
async def test_invalid_url(preprocessor):
    """Test error handling with invalid URL."""
    result = await preprocessor.process_song("https://youtube.com/invalid")
    assert result is None, "Should return None for invalid URL"

@pytest.mark.asyncio
async def test_download_error_handling(preprocessor):
    """Test error handling during download."""
    # Test with non-existent video ID
    result = await preprocessor.download_song("https://youtube.com/watch?v=nonexistent")
    assert result is None, "Should return None for non-existent video" 