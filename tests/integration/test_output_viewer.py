import json
from pathlib import Path
import pytest
from ai_beat_saber.llm_prompting.generate_maps import MapGenerator

@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "output"

@pytest.fixture
def formatted_dir(tmp_path):
    return tmp_path / "formatted"

@pytest.fixture
def example_midi_text():
    """Create a simple example MIDI text."""
    return (
        "Tempo: 120.0 BPM\n"
        "Instrument 0: Piano\n"
        "Note: C4, Start: 0.000s, End: 0.500s, Duration: 0.500s, Velocity: 64\n"
        "Note: E4, Start: 0.500s, End: 1.000s, Duration: 0.500s, Velocity: 64\n"
        "Note: G4, Start: 1.000s, End: 1.500s, Duration: 0.500s, Velocity: 64\n"
        "Note: C5, Start: 1.500s, End: 2.000s, Duration: 0.500s, Velocity: 64"
    )

def test_save_map_output(output_dir, formatted_dir, example_midi_text):
    """Generate a map and save it to a local file for viewing."""
    # Initialize the generator
    map_generator = MapGenerator(formatted_dir, output_dir)
    
    # Generate a map
    result = map_generator.generate_map(example_midi_text, "easy")
    
    # Save the output to a file in the current directory
    output_file = Path("map_output.json")
    with open(output_file, 'w') as f:
        json.dump({
            'midi_text': example_midi_text,
            'map_data': result,
            'debug_log_file': str(list(output_dir.glob("logs/debug_*.log"))[0]),
            'response_log_file': str(list(output_dir.glob("logs/*.json"))[0])
        }, f, indent=2)
    
    print(f"\nOutput saved to: {output_file.absolute()}") 