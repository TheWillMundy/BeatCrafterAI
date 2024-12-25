import pytest
import asyncio
from pathlib import Path
import mido  # We'll use this to validate the MIDI output
from ai_beat_saber.converter.convert_audio import AudioConverter

@pytest.fixture
def audio_converter(temp_extract_dir):
    """Create an AudioConverter instance for testing."""
    output_dir = temp_extract_dir / "midi_output"
    return AudioConverter(temp_extract_dir, output_dir)

@pytest.fixture
async def audio_file(temp_extract_dir, test_data_zip):
    """Extract and provide the audio file from test data."""
    import zipfile
    
    # Create a specific test folder to verify naming
    test_folder = temp_extract_dir / "test_song_id_123"
    test_folder.mkdir(parents=True, exist_ok=True)
    
    # Extract the test data to the specific folder
    with zipfile.ZipFile(test_data_zip, 'r') as zip_ref:
        zip_ref.extract('song.egg', test_folder)
    
    audio_path = test_folder / 'song.egg'
    assert audio_path.exists(), "Audio file should exist after extraction"
    return audio_path

@pytest.mark.asyncio
async def test_convert_audio_creates_midi(audio_converter, audio_file):
    """Test that the audio conversion creates a MIDI file."""
    # Convert the audio file
    output_path = await audio_converter.convert_audio(audio_file)
    
    # Check that the output file exists and is in the correct directory
    assert output_path.exists(), "MIDI file should be created"
    assert output_path.parent == audio_converter.output_dir, "MIDI file should be in output directory"
    assert output_path.suffix == '.mid', "Output file should have .mid extension"
    
    # Verify the MIDI filename matches the source folder name
    expected_name = f"{audio_file.parent.name}.mid"
    assert output_path.name == expected_name, f"MIDI filename should be {expected_name}"
    
    # Basic file size check
    assert output_path.stat().st_size > 0, "MIDI file should not be empty"

@pytest.mark.asyncio
async def test_convert_audio_content_valid(audio_converter, audio_file):
    """Test that the converted MIDI file has valid content."""
    # Convert the audio file
    output_path = await audio_converter.convert_audio(audio_file)
    
    # Load and validate the MIDI file
    midi_file = mido.MidiFile(output_path)
    
    # Basic MIDI structure checks
    assert len(midi_file.tracks) > 0, "MIDI should have at least one track"
    
    # Check for note events and valid note values
    note_events = []
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'note_on':
                note_events.append(msg)
                assert 0 <= msg.note <= 127, "Note values should be within MIDI range"
                assert 0 <= msg.velocity <= 127, "Velocity values should be within MIDI range"
    
    assert len(note_events) > 0, "MIDI should contain note events"

@pytest.mark.asyncio
async def test_convert_audio_invalid_input(audio_converter):
    """Test that conversion fails gracefully with invalid input."""
    with pytest.raises(FileNotFoundError):
        await audio_converter.convert_audio(Path('nonexistent.egg'))

@pytest.mark.asyncio
async def test_convert_audio_invalid_format(audio_converter, temp_extract_dir):
    """Test that conversion fails gracefully with invalid audio formats."""
    # Create test folder with specific ID
    test_folder = temp_extract_dir / "invalid_test_123"
    test_folder.mkdir(parents=True)
    
    # Test with invalid .egg file
    egg_path = test_folder / 'test.egg'
    
    # Create a small test file with invalid header
    egg_path.write_bytes(b'INVALID')
    
    with pytest.raises(Exception) as exc_info:
        await audio_converter.convert_audio(egg_path)
    assert "Invalid audio file" in str(exc_info.value)

@pytest.mark.asyncio
async def test_convert_all_empty_directory(audio_converter):
    """Test convert_all with an empty directory."""
    results = await audio_converter.convert_all()
    assert len(results) == 0, "Should return empty list for directory with no audio files"

@pytest.mark.asyncio
async def test_convert_all_with_files(audio_converter, audio_file):
    """Test convert_all with audio files present."""
    # Create a second test file in a different folder
    second_folder = audio_file.parent.parent / "test_song_id_456"
    second_folder.mkdir(parents=True)
    second_file = second_folder / "song.egg"
    second_file.write_bytes(audio_file.read_bytes())
    
    results = await audio_converter.convert_all()
    
    # Filter out any exceptions from results
    successful_conversions = [r for r in results if isinstance(r, Path)]
    
    assert len(successful_conversions) == 2, "Should convert all valid audio files"
    
    # Verify each MIDI file matches its source folder
    for path in successful_conversions:
        assert path.exists(), "All output files should exist"
        assert path.suffix == '.mid', "All output files should be MIDI"
        # Extract expected folder name from the MIDI filename
        midi_folder_name = path.stem
        # Verify a matching source folder exists
        source_folder = audio_converter.songs_dir / midi_folder_name
        assert source_folder.exists(), f"Source folder {midi_folder_name} should exist" 