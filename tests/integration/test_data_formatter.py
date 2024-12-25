import pytest
import json
from pathlib import Path
import pretty_midi

from ai_beat_saber.data_formatter.format_data import DataFormatter

@pytest.fixture
def data_formatter(temp_extract_dir, tmp_path):
    """Create a DataFormatter instance for testing."""
    output_dir = tmp_path / "formatted_output"
    print(f"\nCreating test DataFormatter with:\n  temp_extract_dir: {temp_extract_dir}\n  output_dir: {output_dir}")
    return DataFormatter(temp_extract_dir, output_dir)

def create_test_midi(midi_path: Path, instrument_name: str = 'Choir Aahs', bpm: float = 120.0):
    """Create a test MIDI file with some notes."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=round(bpm, 2))
    program = pretty_midi.instrument_name_to_program(instrument_name)
    instrument = pretty_midi.Instrument(program=program)
    
    # Add a test note
    note = pretty_midi.Note(velocity=64, pitch=60, start=0.0, end=0.5)
    instrument.notes.append(note)
    pm.instruments.append(instrument)
    pm.write(str(midi_path))

def test_format_real_map(data_formatter, temp_extract_dir, test_data_zip):
    """Test formatting a real Beat Saber map."""
    print("\n=== Starting test_format_real_map ===")
    
    # First extract test data
    import zipfile
    test_folder = temp_extract_dir / "test_song_id_123"
    test_folder.mkdir(parents=True)
    print(f"Created test folder: {test_folder}")
    
    with zipfile.ZipFile(test_data_zip, 'r') as zip_ref:
        zip_ref.extractall(test_folder)
    print(f"Extracted test data to: {test_folder}")
    print(f"Contents: {list(test_folder.iterdir())}")
    
    # Read the actual BPM from info.dat
    with open(test_folder / "Info.dat") as f:
        info_data = json.load(f)
        actual_bpm = round(float(info_data['_beatsPerMinute']), 2)
    
    # Create a dummy MIDI file in the data/midi directory
    midi_dir = Path("data") / "midi"
    midi_dir.mkdir(parents=True, exist_ok=True)
    midi_file = midi_dir / "test_song_id_123.mid"
    create_test_midi(midi_file, bpm=actual_bpm)
    print(f"Created test MIDI file: {midi_file}")
    
    # Format the map
    result = data_formatter.format_map(test_folder)
    
    # Verify basic structure
    print("\nVerifying formatted data structure:")
    print(f"song_id: {result['song_id']}")
    print(f"info keys: {list(result['info'].keys())}")
    print(f"number of difficulties: {len(result['difficulties'])}")
    print(f"midi data preview: {result['midi_data'][:100]}...")
    
    assert result['song_id'] == 'test_song_id_123'
    assert result['info'] is not None
    assert isinstance(result['info'], dict)
    
    # Verify info.dat fields are preserved exactly
    assert '_songName' in result['info']
    assert '_songAuthorName' in result['info']
    assert '_difficultyBeatmapSets' in result['info']
    
    # Verify difficulties were formatted
    assert len(result['difficulties']) > 0
    for diff_name, diff_data in result['difficulties'].items():
        print(f"\nVerifying difficulty: {diff_name}")
        print(f"Keys in difficulty data: {list(diff_data.keys())}")
        
        # Verify difficulty data structure is preserved exactly
        assert any(key in diff_data for key in ['_notes', 'colorNotes', 'basicBeatmapEvents']), \
            f"Difficulty {diff_name} missing notes data"
        assert any(key in diff_data for key in ['_obstacles', 'obstacles']), \
            f"Difficulty {diff_name} missing obstacles data"
        assert any(key in diff_data for key in ['_events', 'basicBeatmapEvents']), \
            f"Difficulty {diff_name} missing events data"
    
    # Verify MIDI data was included and has expected content
    assert result['midi_data'] is not None
    import re
    tempo_match = re.search(r'Tempo: (\d+\.\d+) BPM', result['midi_data'])
    assert tempo_match is not None, "Could not find tempo in MIDI data"
    midi_tempo = float(tempo_match.group(1))
    assert round(midi_tempo, 2) == actual_bpm, f"Expected tempo {actual_bpm} BPM, got {midi_tempo} BPM"
    assert 'Instrument 0: Choir Aahs' in result['midi_data']
    assert 'Note: C4' in result['midi_data']  # Middle C
    print("\nTest completed successfully")

def test_format_all_with_multiple_maps(data_formatter, temp_extract_dir, test_data_zip):
    """Test formatting multiple maps."""
    print("\n=== Starting test_format_all_with_multiple_maps ===")
    
    # Create two test maps
    import zipfile
    bpms = []  # Store BPMs for verification
    for i in range(2):
        test_folder = temp_extract_dir / f"test_song_id_{i}"
        test_folder.mkdir(parents=True)
        print(f"Created test folder {i}: {test_folder}")
        
        with zipfile.ZipFile(test_data_zip, 'r') as zip_ref:
            zip_ref.extractall(test_folder)
        print(f"Extracted test data to folder {i}")
        print(f"Contents: {list(test_folder.iterdir())}")
        
        # Read the actual BPM from info.dat
        with open(test_folder / "Info.dat") as f:
            info_data = json.load(f)
            bpms.append(round(float(info_data['_beatsPerMinute']), 2))
    
    # Create MIDI files in data/midi
    midi_dir = Path("data") / "midi"
    midi_dir.mkdir(parents=True, exist_ok=True)
    for i in range(2):
        midi_file = midi_dir / f"test_song_id_{i}.mid"
        create_test_midi(midi_file, bpm=bpms[i])
        print(f"Created test MIDI file {i}: {midi_file}")
    
    # Format all maps
    results = data_formatter.format_all()
    print(f"\nFormatted {len(results)} maps")
    
    # Verify results
    assert len(results) == 2
    
    # Check output files were created
    output_files = list(data_formatter.output_dir.glob("*.json"))
    print(f"\nOutput files created: {[f.name for f in output_files]}")
    assert len(output_files) == 2
    
    # Verify each output file
    for i in range(2):
        output_file = data_formatter.output_dir / f"test_song_id_{i}.json"
        assert output_file.exists()
        print(f"\nVerifying output file {i}: {output_file}")
        
        with open(output_file) as f:
            data = json.load(f)
            print(f"Loaded JSON data for song_id: {data['song_id']}")
            print(f"Number of difficulties: {len(data['difficulties'])}")
            assert data['song_id'] == f"test_song_id_{i}"
            assert data['info'] is not None
            assert len(data['difficulties']) > 0
            assert data['midi_data'] is not None
            
            # Verify MIDI data has expected content
            import re
            tempo_match = re.search(r'Tempo: (\d+\.\d+) BPM', data['midi_data'])
            assert tempo_match is not None, "Could not find tempo in MIDI data"
            midi_tempo = float(tempo_match.group(1))
            assert round(midi_tempo, 2) == bpms[i], f"Expected tempo {bpms[i]} BPM, got {midi_tempo} BPM"
            assert 'Instrument 0: Choir Aahs' in data['midi_data']
            assert 'Note: C4' in data['midi_data']
    
    print("\nTest completed successfully")

def test_format_map_missing_files(data_formatter, temp_extract_dir):
    """Test error handling with missing files."""
    print("\n=== Starting test_format_map_missing_files ===")
    
    # Create empty test folder
    test_folder = temp_extract_dir / "empty_test"
    test_folder.mkdir(parents=True)
    print(f"Created empty test folder: {test_folder}")
    
    # Test missing info.dat
    print("\nTesting missing info.dat case")
    with pytest.raises(FileNotFoundError):
        data_formatter.format_map(test_folder)
    print("Successfully caught FileNotFoundError for missing info.dat")
    
    # Create info.dat but missing difficulty files
    info_data = {
        "_songName": "Test Song",
        "_songAuthorName": "Test Author",
        "_beatsPerMinute": 128.0,  # Add BPM to test data
        "_difficultyBeatmapSets": [{
            "_difficultyBeatmaps": [{
                "_difficulty": "Easy",
                "_beatmapFilename": "EasyStandard.dat"
            }]
        }]
    }
    info_path = test_folder / "info.dat"
    with open(info_path, 'w') as f:
        json.dump(info_data, f)
    print(f"\nCreated test info.dat at: {info_path}")
    print(f"info.dat contents: {info_data}")
    
    # Should still work but with empty difficulties and no MIDI
    result = data_formatter.format_map(test_folder)
    print("\nVerifying result with missing difficulty files:")
    print(f"song_id: {result['song_id']}")
    print(f"difficulties: {result['difficulties']}")
    print(f"midi_data: {result['midi_data']}")
    assert result['difficulties'] == {}
    assert result['midi_data'] is None
    
    print("\nTest completed successfully") 