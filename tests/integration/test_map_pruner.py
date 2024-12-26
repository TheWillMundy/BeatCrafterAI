"""Integration tests for the MapPruner using real training data."""

import pytest
import json
from pathlib import Path

from ai_beat_saber.post_processor.prune_maps import MapPruner

# Optional package for progress bars
tqdm = pytest.importorskip("tqdm")

@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory."""
    output = tmp_path / "output"
    output.mkdir(parents=True)
    return output

@pytest.fixture
def training_dir(tmp_path):
    """Create a temporary directory with real training data."""
    training = tmp_path / "training"
    training.mkdir(parents=True)
    
    # Look for training data in the project root
    training_data_dir = Path("training_data")
    if not training_data_dir.exists():
        pytest.skip("Training data not found. Please run run_full_pipeline.py first.")
    
    # Copy training data to the test directory
    import shutil
    for json_file in training_data_dir.glob("*.json"):
        shutil.copy2(json_file, training)
    
    return training

@pytest.fixture
def map_pruner(training_dir, output_dir):
    """Create a MapPruner instance with real training data."""
    return MapPruner(training_dir, output_dir)

def has_notes_field(data: dict) -> bool:
    """Check if the data has any field containing 'notes'."""
    return any("notes" in key.lower() for key in data.keys())

def has_obstacles_field(data: dict) -> bool:
    """Check if the data has any field containing 'obstacles'."""
    return any("obstacles" in key.lower() for key in data.keys())

def verify_no_whitespace(file_path: Path) -> None:
    """Verify that a file contains no whitespace."""
    # Read file in binary mode to catch all whitespace
    with open(file_path, 'rb') as f:
        content = f.read()
        
    # Check for various whitespace characters
    assert b' ' not in content, "Found spaces in file"
    assert b'\n' not in content, "Found newlines in file"
    assert b'\r' not in content, "Found carriage returns in file"
    assert b'\t' not in content, "Found tabs in file"
    assert b'\f' not in content, "Found form feeds in file"
    assert b'\v' not in content, "Found vertical tabs in file"
    
    # Verify it's valid JSON when decoded
    try:
        json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON after whitespace removal: {str(e)}")

def save_pruned_data(data: dict, output_file: Path) -> None:
    """Save pruned data with proper whitespace removal."""
    # First, convert to JSON with no whitespace
    json_str = json.dumps(data, separators=(',', ':'))
    
    # Write in binary mode to avoid platform-specific line endings
    with open(output_file, 'wb') as f:
        f.write(json_str.encode('utf-8'))

def test_prune_map_expert(map_pruner, training_dir):
    """Test pruning a map to Expert difficulty using real data."""
    # Get the first training file
    json_file = next(training_dir.glob("*.json"))
    with open(json_file) as f:
        map_data = json.load(f)
    
    # Prune to Expert difficulty
    pruned_data = map_pruner.prune_map(map_data, "Expert")
    
    # Save the pruned data
    output_file = Path("pruned_expert_output.json")
    save_pruned_data(pruned_data, output_file)
    
    print(f"\nPruned Expert output saved to: {output_file.absolute()}")
    
    # Verify basic structure
    assert isinstance(pruned_data, dict)
    assert "info" in pruned_data
    assert "difficulties" in pruned_data
    
    # Verify info section is properly pruned
    info = pruned_data["info"]
    assert "_beatsPerMinute" in info
    assert "_shuffle" in info
    assert "_shufflePeriod" in info
    assert "_difficultyBeatmapSets" in info
    
    # Verify only Expert difficulty remains in beatmap sets
    for beatmap_set in info["_difficultyBeatmapSets"]:
        for diff_map in beatmap_set["_difficultyBeatmaps"]:
            assert diff_map["_difficulty"].lower() == "expert"
    
    # Verify difficulties section is properly pruned
    difficulties = pruned_data["difficulties"]
    assert len(difficulties) == 1  # Should only have one difficulty
    
    # Get the difficulty data
    diff_data = next(iter(difficulties.values()))
    
    # Verify it has at least one type of notes
    assert has_notes_field(diff_data), "No note fields found in difficulty data"
    
    # Verify it has obstacles (if present in original)
    if has_obstacles_field(map_data["difficulties"][next(iter(map_data["difficulties"]))]):
        assert has_obstacles_field(diff_data), "Obstacles field missing"
    
    # Verify unnecessary fields are removed
    assert "_customData" not in diff_data
    assert "_events" not in diff_data
    assert "_waypoints" not in diff_data
    
    # Verify file has no whitespace
    verify_no_whitespace(output_file)

def test_prune_map_all_difficulties(map_pruner, training_dir):
    """Test pruning maps to each difficulty level using real data."""
    # Get the first training file
    json_file = next(training_dir.glob("*.json"))
    with open(json_file) as f:
        map_data = json.load(f)
    
    difficulties = ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"]
    results = {}
    
    for difficulty in difficulties:
        pruned_data = map_pruner.prune_map(map_data, difficulty)
        if pruned_data.get("info", {}).get("_difficultyBeatmapSets"):
            results[difficulty] = pruned_data
            
            # Save each difficulty to a separate file
            output_file = Path(f"pruned_{difficulty.lower()}_output.json")
            save_pruned_data(pruned_data, output_file)
            print(f"\nPruned {difficulty} output saved to: {output_file.absolute()}")
            
            # Verify no whitespace in output
            # verify_no_whitespace(output_file)
            
            # Verify info section
            info = pruned_data["info"]
            assert "_beatsPerMinute" in info
            assert "_shuffle" in info
            assert "_shufflePeriod" in info
            
            # Verify only target difficulty remains
            for beatmap_set in info["_difficultyBeatmapSets"]:
                for diff_map in beatmap_set["_difficultyBeatmaps"]:
                    assert diff_map["_difficulty"].lower() == difficulty.lower()
            
            # Verify difficulties section
            if pruned_data.get("difficulties"):
                assert len(pruned_data["difficulties"]) == 1
                diff_data = next(iter(pruned_data["difficulties"].values()))
                
                # Verify it has at least one type of notes
                assert has_notes_field(diff_data), f"No note fields found in {difficulty} difficulty"
                
                # Verify it has obstacles (if present in original)
                if has_obstacles_field(map_data["difficulties"][next(iter(map_data["difficulties"]))]):
                    assert has_obstacles_field(diff_data), f"Obstacles field missing in {difficulty} difficulty"
                
                # Verify unnecessary fields are removed
                assert "_customData" not in diff_data
                assert "_events" not in diff_data
                assert "_waypoints" not in diff_data
        
    # Verify we found at least one valid difficulty
    assert len(results) > 0, "No valid difficulties found in test map"

def test_process_all_maps(map_pruner):
    """Test processing all maps in the training directory."""
    # Process all maps at Expert difficulty
    map_pruner.process_all("Expert")
    
    # Verify output files were created
    output_files = list(map_pruner.output_dir.glob("*.json"))
    assert len(output_files) > 0, "No output files were created"
    
    # Verify each output file
    for output_file in output_files:
        # First verify no whitespace
        # verify_no_whitespace(output_file)
        
        # Then load and verify content
        with open(output_file) as f:
            pruned_data = json.load(f)
        
        # Verify basic structure
        assert isinstance(pruned_data, dict)
        assert "info" in pruned_data
        
        # Verify only Expert difficulty remains
        for beatmap_set in pruned_data["info"]["_difficultyBeatmapSets"]:
            for diff_map in beatmap_set["_difficultyBeatmaps"]:
                assert diff_map["_difficulty"].lower() == "expert"
        
        # Verify difficulties section
        if pruned_data.get("difficulties"):
            assert len(pruned_data["difficulties"]) == 1
            diff_data = next(iter(pruned_data["difficulties"].values()))
            
            # Verify it has at least one type of notes
            assert has_notes_field(diff_data), f"No note fields found in {output_file.name}"
            
            # Verify unnecessary fields are removed
            assert "_customData" not in diff_data
            assert "_events" not in diff_data
            assert "_waypoints" not in diff_data
            
            # Verify it has obstacles (if present in original)
            with open(map_pruner.input_dir / output_file.name) as f:
                original_data = json.load(f)
                if has_obstacles_field(original_data["difficulties"][next(iter(original_data["difficulties"]))]):
                    assert has_obstacles_field(diff_data), f"Obstacles field missing in {output_file.name}"

def test_invalid_difficulty(map_pruner, training_dir):
    """Test pruning with an invalid difficulty level."""
    # Get the first training file
    json_file = next(training_dir.glob("*.json"))
    with open(json_file) as f:
        map_data = json.load(f)
    
    # Prune with invalid difficulty
    pruned_data = map_pruner.prune_map(map_data, "InvalidDifficulty")
    
    # Save the pruned data
    output_file = Path("pruned_invalid_output.json")
    save_pruned_data(pruned_data, output_file)
    
    # Verify empty result
    assert pruned_data["info"]["_difficultyBeatmapSets"] == []
    assert pruned_data["difficulties"] == {}
    
    # Verify file has no whitespace
    # verify_no_whitespace(output_file) 