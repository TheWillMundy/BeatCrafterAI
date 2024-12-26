import pytest
import json
from pathlib import Path
import mido

from beatcrafter_ai.llm_prompting.generate_maps import MapGenerator
from beatcrafter_ai.preprocessor.preprocess_song import YouTubePreprocessor

# Optional package for progress bars
tqdm = pytest.importorskip("tqdm")

def note_number_to_name(note_number):
    """Convert MIDI note number to note name."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    note = notes[note_number % 12]
    return f"{note}{octave}"

@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory."""
    output = tmp_path / "output"
    output.mkdir(parents=True)
    return output

@pytest.fixture
def formatted_dir(tmp_path):
    """Create a temporary directory for formatted training data."""
    formatted = tmp_path / "formatted"
    formatted.mkdir(parents=True)
    return formatted

@pytest.fixture
async def preprocessed_song(tmp_path):
    """Preprocess a test song from YouTube and return its data."""
    # Set up preprocessor
    preprocess_dir = tmp_path / "preprocessed"
    preprocessor = YouTubePreprocessor(preprocess_dir)
    
    # Use a known good test song (should be relatively short)
    test_url = "https://www.youtube.com/watch?v=QBgl4rVz3Ks"
    
    # Process the song
    result = await preprocessor.process_song(test_url)
    if result is None:
        pytest.skip("Failed to preprocess test song - skipping test")
    
    # Read and validate the MIDI file
    midi_file = mido.MidiFile(result['midi_path'])
    
    # Convert MIDI to text representation
    midi_text = []
    
    # Add tempo information
    tempo_track = midi_file.tracks[0]
    tempo_event = next((msg for msg in tempo_track if msg.type == 'set_tempo'), None)
    tempo = 120.0  # Default tempo
    if tempo_event:
        tempo = mido.tempo2bpm(tempo_event.tempo)
    midi_text.append(f"Tempo: {tempo:.1f} BPM")
    
    # Process each track
    for i, track in enumerate(midi_file.tracks):
        # Get instrument name if available
        name_event = next((msg for msg in track if msg.type == 'track_name'), None)
        track_name = name_event.name if name_event else f"Track {i}"
        midi_text.append(f"\nInstrument {i}: {track_name}")
        
        # Keep track of absolute time in ticks
        current_ticks = 0
        
        # Store note_on events to match with note_offs
        active_notes = {}  # key: note number, value: (start_ticks, velocity)
        
        # Process messages
        for msg in track:
            current_ticks += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                # Note started
                active_notes[msg.note] = (current_ticks, msg.velocity)
            elif (msg.type == 'note_off' or 
                  (msg.type == 'note_on' and msg.velocity == 0)) and \
                  msg.note in active_notes:
                # Note ended
                start_ticks, velocity = active_notes.pop(msg.note)
                
                # Convert ticks to beats
                start_beat = start_ticks / midi_file.ticks_per_beat
                end_beat = current_ticks / midi_file.ticks_per_beat
                
                # Convert beats to seconds
                start_time = (start_beat * 60.0) / tempo
                end_time = (end_beat * 60.0) / tempo
                duration = end_time - start_time
                
                note_name = note_number_to_name(msg.note)
                midi_text.append(
                    f"Note: {note_name}, "
                    f"Start: {start_time:.3f}s, "
                    f"End: {end_time:.3f}s, "
                    f"Duration: {duration:.3f}s, "
                    f"Beat: {start_beat:.3f}, "
                    f"Velocity: {velocity}"
                )
    
    return {
        'video_id': result['video_id'],
        'title': result.get('title', 'Unknown Title'),
        'midi_text': '\n'.join(midi_text)
    }

@pytest.fixture
def map_generator(formatted_dir, output_dir):
    """Create a MapGenerator instance with real training data."""
    # Look for training data in the project root
    training_data_dir = Path("training_data")
    if not training_data_dir.exists():
        pytest.skip("Training data not found. Please run example.py first (see README.md for usage instructions).")
    
    # Copy training data to the test directory
    import shutil
    for json_file in training_data_dir.glob("*.json"):
        shutil.copy2(json_file, formatted_dir)
    
    return MapGenerator(formatted_dir, output_dir)

@pytest.mark.asyncio
async def test_generate_map_single_difficulty(map_generator, preprocessed_song):
    """Test generating a map for a single difficulty using real preprocessed data."""
    # Generate a map at Hard difficulty
    result = map_generator.generate_map(preprocessed_song['midi_text'], "Hard")
    
    # Save the output to a file for inspection
    output_file = Path("single_difficulty_output.json")
    with open(output_file, 'w') as f:
        json.dump({
            'midi_text': preprocessed_song['midi_text'],
            'map_data': result,
            'debug_log_file': str(list(map_generator.logs_dir.glob("debug_*.log"))[0]),
            'response_log_file': str(list(map_generator.logs_dir.glob("*.json"))[0])
        }, f, indent=2)
    
    print(f"\nSingle difficulty output saved to: {output_file.absolute()}")
    
    # Verify basic structure
    assert isinstance(result, dict)
    assert all(k in result for k in ['_notes', '_obstacles', '_events'])
    
    # Verify notes are properly structured and follow musical timing
    assert len(result['_notes']) >= 20, "Map should have at least 20 notes for Hard difficulty"
    
    previous_time = -1
    for note in result['_notes']:
        # Verify note structure
        assert '_time' in note
        assert '_lineIndex' in note
        assert '_lineLayer' in note
        assert '_type' in note
        assert '_cutDirection' in note
        
        # Verify timing is sequential
        assert note['_time'] > previous_time, "Notes should be in chronological order"
        previous_time = note['_time']
        
        # Verify values are in valid ranges
        assert 0 <= note['_lineIndex'] <= 3, "Note line index out of range"
        assert 0 <= note['_lineLayer'] <= 2, "Note layer out of range"
        assert note['_type'] in [0, 1, 3], "Invalid note type"
        assert 0 <= note['_cutDirection'] <= 8, "Invalid cut direction"
    
    # Verify logs were created
    log_files = list(map_generator.logs_dir.glob("*.json"))
    assert len(log_files) == 1
    
    # Verify log content
    with open(log_files[0]) as f:
        log_data = json.load(f)
        assert log_data["prompt"].startswith("You are an expert Beat Saber map creator")
        assert preprocessed_song['midi_text'] in log_data["prompt"]
        assert isinstance(log_data["response"], dict)

@pytest.mark.asyncio
async def test_generate_full_set(map_generator, preprocessed_song):
    """Test generating a full set of difficulties using real preprocessed data."""
    # Generate all difficulties
    results = map_generator.generate_full_set(
        preprocessed_song['midi_text'],
        preprocessed_song['title']
    )
    
    # Save the output to a file for inspection
    output_file = Path("full_set_output.json")
    with open(output_file, 'w') as f:
        json.dump({
            'midi_text': preprocessed_song['midi_text'],
            'map_data': results,
            'debug_log_file': str(list(map_generator.logs_dir.glob("debug_*.log"))[0]),
            'response_log_file': str(list(map_generator.logs_dir.glob("*.json"))[0])
        }, f, indent=2)
    
    print(f"\nFull set output saved to: {output_file.absolute()}")
    
    # Verify we got all difficulties
    assert len(results) == 3
    difficulties = {r["name"] for r in results}
    assert difficulties == {"easy", "normal", "expert"}
    
    # Verify files were created
    map_dir = map_generator.maps_dir / preprocessed_song['title']
    assert map_dir.exists()
    
    # Verify info.dat
    info_path = map_dir / "info.dat"
    assert info_path.exists()
    with open(info_path) as f:
        info_data = json.load(f)
        assert info_data["_songName"] == preprocessed_song['title']
        assert len(info_data["_difficultyBeatmapSets"]) == 1
        assert len(info_data["_difficultyBeatmapSets"][0]["_difficultyBeatmaps"]) == 3
    
    # Verify each difficulty file
    for diff in ["Easy", "Normal", "Expert"]:
        diff_path = map_dir / f"{diff}Standard.dat"
        assert diff_path.exists()
        
        with open(diff_path) as f:
            diff_data = json.load(f)
            
            # Verify basic structure
            assert all(k in diff_data for k in ['_notes', '_obstacles', '_events'])
            
            # Verify notes are properly structured
            for note in diff_data['_notes']:
                assert '_time' in note
                assert '_lineIndex' in note
                assert '_lineLayer' in note
                assert '_type' in note
                assert '_cutDirection' in note
                
                # Verify values are in valid ranges
                assert 0 <= note['_lineIndex'] <= 3, "Note line index out of range"
                assert 0 <= note['_lineLayer'] <= 2, "Note layer out of range"
                assert note['_type'] in [0, 1, 3], "Invalid note type"
                assert 0 <= note['_cutDirection'] <= 8, "Invalid cut direction"
            
            # Verify difficulty progression
            if diff == "Easy":
                assert len(diff_data['_notes']) <= 100, "Too many notes for Easy difficulty"
            elif diff == "Normal":
                assert len(diff_data['_notes']) <= 200, "Too many notes for Normal difficulty"

@pytest.mark.asyncio
async def test_invalid_difficulty(map_generator, preprocessed_song):
    """Test error handling with invalid difficulty."""
    with pytest.raises(ValueError):
        map_generator.generate_map(preprocessed_song['midi_text'], "invalid") 