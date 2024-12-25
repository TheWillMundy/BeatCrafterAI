"""
Format Beat Saber map data for LLM training and inference.
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import pretty_midi

class DataFormatter:
    """Format map data for LLM consumption."""
    
    def __init__(self, songs_dir: Path, output_dir: Path):
        """Initialize the formatter.
        
        Args:
            songs_dir: Directory containing extracted songs and MIDI
            output_dir: Directory to save formatted data
        """
        self.songs_dir = songs_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nInitialized DataFormatter with:\n  songs_dir: {songs_dir}\n  output_dir: {output_dir}")
    
    def _midi_to_text(self, midi_path: Path) -> str:
        """Convert MIDI file to text representation.
        
        Args:
            midi_path: Path to the MIDI file
            
        Returns:
            Text representation of the MIDI file
        """
        midi_data = pretty_midi.PrettyMIDI(str(midi_path))
        text_representation = []
        
        # Add tempo information
        tempo_changes = midi_data.get_tempo_changes()
        if len(tempo_changes[0]) > 0:  # If there are tempo changes
            text_representation.append(f"Tempo: {tempo_changes[1][0]} BPM")
        
        # Process each instrument
        for i, instrument in enumerate(midi_data.instruments):
            text_representation.append(f"\nInstrument {i}: {pretty_midi.program_to_instrument_name(instrument.program)}")
            
            # Sort notes by start time
            notes = sorted(instrument.notes, key=lambda x: x.start)
            
            # Convert each note to text
            for note in notes:
                note_name = pretty_midi.note_number_to_name(note.pitch)
                text_representation.append(
                    f"Note: {note_name}, Start: {note.start:.3f}s, End: {note.end:.3f}s, "
                    f"Duration: {(note.end - note.start):.3f}s, Velocity: {note.velocity}"
                )
        
        return "\n".join(text_representation)
    
    def format_map(self, map_dir: Path) -> Dict[str, Any]:
        """Format a single map's data.
        
        Args:
            map_dir: Directory containing map files
            
        Returns:
            Formatted map data for LLM
        """
        print(f"\nFormatting map in directory: {map_dir}")
        
        # Read info.dat
        info_path = map_dir / 'info.dat'
        if not info_path.exists():
            print(f"ERROR: info.dat not found in {map_dir}")
            raise FileNotFoundError(f"info.dat not found in {map_dir}")
            
        with open(info_path) as f:
            info_data = json.load(f)
        print(f"Loaded info.dat with fields: {list(info_data.keys())}")
            
        # Get all difficulty files
        difficulties = {}
        if '_difficultyBeatmapSets' in info_data:
            for beatmap_set in info_data['_difficultyBeatmapSets']:
                for diff_map in beatmap_set['_difficultyBeatmaps']:
                    diff_file = map_dir / diff_map['_beatmapFilename']
                    if diff_file.exists():
                        with open(diff_file) as f:
                            difficulties[diff_map['_beatmapFilename']] = json.load(f)
                            print(f"Loaded difficulty file: {diff_map['_beatmapFilename']}")
                    else:
                        print(f"Warning: Difficulty file not found: {diff_map['_beatmapFilename']}")
        
        print(f"Found {len(difficulties)} difficulty files")
        
        # Get MIDI file if it exists (should be named same as directory with .mid extension)
        # Look in data/midi folder relative to the workspace root
        midi_path = Path("data") / "midi" / f"{map_dir.name}.mid"
        midi_text = None
        if midi_path.exists():
            midi_text = self._midi_to_text(midi_path)
            print(f"Converted MIDI file to text representation: {midi_path}")
        else:
            print(f"Warning: No MIDI file found at: {midi_path}")
            # Try alternate location as fallback
            alt_midi_path = map_dir.parent / "midi_output" / f"{map_dir.name}.mid"
            if alt_midi_path.exists():
                midi_text = self._midi_to_text(alt_midi_path)
                print(f"Converted MIDI file from alternate location: {alt_midi_path}")
        
        # Check for cover image
        cover_path = map_dir / "cover.jpg"
        if cover_path.exists():
            print(f"Found cover image at: {cover_path}")
        else:
            print("No cover image found")
        
        # Format according to PRD specification
        formatted_data = {
            "song_id": map_dir.name,
            "info": info_data,  # Keep original info.dat structure intact
            "difficulties": difficulties,  # Keep original .dat files intact
            "midi_data": midi_text,  # Store MIDI as text representation
            "cover_image_path": str(cover_path) if cover_path.exists() else None
        }
        
        print(f"Successfully formatted map data for: {map_dir.name}")
        return formatted_data
    
    def format_all(self) -> List[Dict[str, Any]]:
        """Format all maps in the songs directory.
        
        Returns:
            List of formatted map data
        """
        print(f"\nStarting bulk format of all maps in: {self.songs_dir}")
        formatted_maps = []
        for map_dir in self.songs_dir.iterdir():
            if map_dir.is_dir() and (map_dir / 'info.dat').exists():
                try:
                    print(f"\nProcessing directory: {map_dir}")
                    formatted_map = self.format_map(map_dir)
                    formatted_maps.append(formatted_map)
                    
                    # Save individual JSON file
                    output_file = self.output_dir / f"{map_dir.name}.json"
                    with open(output_file, 'w') as f:
                        json.dump(formatted_map, f, indent=2)
                    print(f"Saved formatted data to: {output_file}")
                except Exception as e:
                    print(f"Error formatting map {map_dir.name}: {str(e)}")
                    continue
        
        print(f"\nCompleted formatting {len(formatted_maps)} maps")
        return formatted_maps 