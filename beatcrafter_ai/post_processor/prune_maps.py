"""
Post-process Beat Saber maps by pruning them to a specific difficulty level and removing unnecessary fields.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import re

class MapPruner:
    """Prune Beat Saber maps to specific difficulty and remove unnecessary fields."""
    
    def __init__(self, input_dir: Path, output_dir: Path):
        """Initialize the pruner.
        
        Args:
            input_dir: Directory containing formatted map data
            output_dir: Directory to save pruned maps
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _prune_info(self, info: Dict[str, Any], target_difficulty: str) -> Dict[str, Any]:
        """Prune the info section of the map data.
        
        Args:
            info: Original info data
            target_difficulty: Target difficulty level
            
        Returns:
            Pruned info data
        """
        # Keep only essential fields
        pruned_info = {
            "_beatsPerMinute": info.get("_beatsPerMinute", 0),
            "_shuffle": info.get("_shuffle", 0),
            "_shufflePeriod": info.get("_shufflePeriod", 0.0),
            "_difficultyBeatmapSets": []
        }
        
        # Filter difficulty beatmap sets
        for beatmap_set in info.get("_difficultyBeatmapSets", []):
            pruned_beatmaps = []
            for diff_map in beatmap_set.get("_difficultyBeatmaps", []):
                if diff_map.get("_difficulty", "").lower() == target_difficulty.lower():
                    pruned_beatmaps.append(diff_map)
            
            if pruned_beatmaps:
                pruned_set = {
                    "_beatmapCharacteristicName": beatmap_set.get("_beatmapCharacteristicName", ""),
                    "_difficultyBeatmaps": pruned_beatmaps
                }
                pruned_info["_difficultyBeatmapSets"].append(pruned_set)
        
        return pruned_info
    
    def _has_field_containing(self, data: Dict[str, Any], substring: str) -> bool:
        """Check if dictionary has any key containing the given substring."""
        return any(substring in key.lower() for key in data.keys())
    
    def _prune_difficulties(self, difficulties: Dict[str, Any], target_difficulty: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """Prune the difficulties section of the map data.
        
        Args:
            difficulties: Original difficulties data
            target_difficulty: Target difficulty level
            info: Pruned info data (needed to find correct filename)
            
        Returns:
            Pruned difficulties data
        """
        pruned_difficulties = {}
        
        # Find the target difficulty filename from info
        target_filename = None
        for beatmap_set in info.get("_difficultyBeatmapSets", []):
            for diff_map in beatmap_set.get("_difficultyBeatmaps", []):
                if diff_map.get("_difficulty", "").lower() == target_difficulty.lower():
                    target_filename = diff_map.get("_beatmapFilename")
                    break
            if target_filename:
                break
        
        if not target_filename or target_filename not in difficulties:
            return pruned_difficulties
        
        # Get the target difficulty data and remove unnecessary fields
        difficulty_data = difficulties[target_filename].copy()
        
        # Keep only note-related fields and obstacles
        pruned_difficulty = {}
        for key, value in difficulty_data.items():
            # Keep any fields with 'notes' in the name (e.g. _notes, colorNotes, bombNotes)
            if "notes" in key.lower():
                pruned_difficulty[key] = value
                continue
                
            # Keep obstacles if they exist
            if "obstacles" in key.lower():
                pruned_difficulty[key] = value
                continue
            
            # Keep version info if it exists
            if "version" in key.lower():
                pruned_difficulty[key] = value
                continue
        
        pruned_difficulties[target_filename] = pruned_difficulty
        return pruned_difficulties
    
    def prune_map(self, map_data: Dict[str, Any], target_difficulty: str) -> Dict[str, Any]:
        """Prune a single map to the target difficulty.
        
        Args:
            map_data: Original map data
            target_difficulty: Target difficulty level
            
        Returns:
            Pruned map data
        """
        pruned_data = {}
        
        # Prune info section
        if "info" in map_data:
            pruned_data["info"] = self._prune_info(map_data["info"], target_difficulty)
        
        # Prune difficulties section
        if "difficulties" in map_data:
            pruned_data["difficulties"] = self._prune_difficulties(
                map_data["difficulties"], 
                target_difficulty,
                pruned_data.get("info", {})
            )
        
        # Keep MIDI data if present
        if "midi_data" in map_data:
            pruned_data["midi_data"] = map_data["midi_data"]
        
        return pruned_data
    
    def process_all(self, target_difficulty: str) -> None:
        """Process all maps in the input directory.
        
        Args:
            target_difficulty: Target difficulty level to keep
        """
        for json_file in self.input_dir.glob("*.json"):
            try:
                # Read input map
                with open(json_file) as f:
                    map_data = json.load(f)
                
                # Prune the map
                pruned_data = self.prune_map(map_data, target_difficulty)
                
                # Skip files that don't have the requested difficulty
                if not pruned_data.get("info", {}).get("_difficultyBeatmapSets") or \
                   not pruned_data.get("difficulties"):
                    print(f"Skipping {json_file.name} - does not contain {target_difficulty} difficulty")
                    continue
                
                # Save pruned map without any whitespace
                output_file = self.output_dir / json_file.name
                
                # First convert to JSON string with minimal whitespace
                json_str = json.dumps(pruned_data, separators=(',', ':'), ensure_ascii=False)
                
                # Then remove ALL remaining whitespace characters
                json_str = ''.join(json_str.split())
                
                # Write in binary mode to avoid any platform-specific line endings
                with open(output_file, 'wb') as f:
                    f.write(json_str.encode('utf-8'))
                    
            except Exception as e:
                print(f"Error processing {json_file.name}: {str(e)}") 