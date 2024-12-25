"""
Convert Beat Saber audio files to MIDI format.
"""

from pathlib import Path
import librosa
import numpy as np

class AudioConverter:
    """Convert audio files to MIDI format."""
    
    def __init__(self, songs_dir: Path, output_dir: Path):
        """Initialize the converter.
        
        Args:
            songs_dir: Directory containing extracted songs
            output_dir: Directory to save MIDI files
        """
        self.songs_dir = songs_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_audio(self, audio_path: Path) -> Path:
        """Convert a single audio file to MIDI.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Path to the generated MIDI file
        """
        # TODO: Implement audio to MIDI conversion
        raise NotImplementedError
    
    def convert_all(self):
        """Convert all audio files in the songs directory."""
        # TODO: Implement bulk conversion
        raise NotImplementedError 