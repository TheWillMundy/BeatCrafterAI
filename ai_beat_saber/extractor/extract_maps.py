"""
Extract and parse Beat Saber map files from downloaded ZIPs.
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil

class MapExtractor:
    """Extract and parse Beat Saber map files."""
    
    def __init__(self, zip_dir: Path, output_dir: Path):
        """Initialize the extractor.
        
        Args:
            zip_dir: Directory containing downloaded map ZIPs
            output_dir: Directory to extract maps to
        """
        self.zip_dir = Path(zip_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_map(self, zip_path: Path) -> Dict[str, Any]:
        """Extract a single map ZIP file.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            Dict containing the extracted map data with structure:
            {
                'song_id': str,
                'info': dict,  # Contents of info.dat
                'difficulties': dict,  # Map of difficulty name to .dat contents
                'audio_file': str,  # Path to the audio file
                'has_errors': bool
            }
        """
        song_id = zip_path.stem
        extract_path = self.output_dir / song_id
        
        # Clean up any existing extracted files
        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True)
        
        result = {
            'song_id': song_id,
            'info': None,
            'difficulties': {},
            'audio_file': None,
            'has_errors': False
        }
        
        try:
            with zipfile.ZipFile(zip_path) as zf:
                # Extract all files
                zf.extractall(extract_path)
                
                # Read info.dat
                info_path = extract_path / 'info.dat'
                if info_path.exists():
                    with open(info_path, 'r', encoding='utf-8') as f:
                        result['info'] = json.load(f)
                else:
                    result['has_errors'] = True
                    return result
                
                # Find and record audio file
                audio_files = list(extract_path.glob('*.egg')) + list(extract_path.glob('*.ogg'))
                if audio_files:
                    result['audio_file'] = str(audio_files[0].relative_to(self.output_dir))
                
                # Read all difficulty files
                if '_difficultyBeatmapSets' in result['info']:
                    for beatmap_set in result['info']['_difficultyBeatmapSets']:
                        characteristic = beatmap_set['_beatmapCharacteristicName']
                        for diff_map in beatmap_set['_difficultyBeatmaps']:
                            diff_file = extract_path / diff_map['_beatmapFilename']
                            if diff_file.exists():
                                diff_name = f"{diff_map['_difficulty']}{characteristic}"
                                with open(diff_file, 'r', encoding='utf-8') as f:
                                    result['difficulties'][diff_name] = json.load(f)
                
                return result
                
        except Exception as e:
            result['has_errors'] = True
            print(f"Error extracting {song_id}: {str(e)}")
            return result
    
    def extract_all(self) -> List[Dict[str, Any]]:
        """Extract all maps in the ZIP directory.
        
        Returns:
            List of extracted map data dictionaries
        """
        results = []
        zip_files = list(self.zip_dir.glob('*.zip'))
        
        for zip_path in zip_files:
            result = self.extract_map(zip_path)
            if not result['has_errors']:
                results.append(result)
        
        return results
    
    def get_extracted_map_path(self, song_id: str) -> Optional[Path]:
        """Get the path to an extracted map directory.
        
        Args:
            song_id: ID of the song to locate
            
        Returns:
            Path to the extracted map directory if it exists, None otherwise
        """
        path = self.output_dir / song_id
        return path if path.exists() else None 