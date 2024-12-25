"""
Convert Beat Saber audio files to MIDI format.
"""

from pathlib import Path
import librosa
import numpy as np
import pretty_midi
import asyncio
from typing import Union, List
import soundfile as sf
from tqdm import tqdm
import warnings
import json

class AudioConverter:
    """Convert audio files to MIDI format."""
    
    def __init__(self, songs_dir: Path, output_dir: Path, max_concurrent: int = 5):
        """Initialize the converter.
        
        Args:
            songs_dir: Directory containing extracted songs
            output_dir: Directory to save MIDI files
            max_concurrent: Maximum number of concurrent conversions (default: 5)
        """
        self.songs_dir = Path(songs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    def _generate_output_path(self, audio_path: Path) -> Path:
        """Generate a unique output path for the MIDI file based on the song folder structure.
        
        Args:
            audio_path: Path to the input audio file
            
        Returns:
            Path where the MIDI file should be saved
        """
        # Get the parent folder name (song ID/name)
        song_folder = audio_path.parent.name
        
        # Create a unique name using the song folder
        midi_name = f"{song_folder}.mid"
        
        # Return the full output path
        return self.output_dir / midi_name
    
    def _get_song_bpm(self, audio_path: Path) -> float:
        """Get the BPM from the song's info.dat file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            BPM from info.dat, or None if not found
        """
        info_path = audio_path.parent / 'info.dat'
        if info_path.exists():
            try:
                with open(info_path) as f:
                    info_data = json.load(f)
                    if '_beatsPerMinute' in info_data:
                        # Round to 2 decimal places for consistent display
                        return round(float(info_data['_beatsPerMinute']), 2)
            except Exception:
                pass
        return None
    
    async def convert_audio(self, audio_path: Union[str, Path]) -> Path:
        """Convert a single audio file to MIDI.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Path to the generated MIDI file
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            Exception: If the audio file is invalid or conversion fails
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Input file not found: {audio_path}")
        
        # Validate file before processing
        try:
            with open(audio_path, 'rb') as f:
                header = f.read(4)
                if header not in (b'OggS', b'RIFF'):  # Common headers for .ogg and .egg files
                    raise Exception("Invalid audio file format")
        except Exception as e:
            if "Invalid audio file format" in str(e):
                raise
            raise Exception("Invalid audio file: Failed to read file header")
        
        # Generate output path based on song folder structure
        output_path = self._generate_output_path(audio_path)
        
        # Use semaphore to limit concurrent conversions
        async with self._semaphore:
            # Run the CPU-intensive conversion in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._convert_audio_to_midi_sync, audio_path, output_path)
        
        return output_path
    
    def _convert_audio_to_midi_sync(self, input_path: Path, output_path: Path) -> None:
        """
        Synchronous implementation of audio to MIDI conversion.
        Uses librosa for audio processing and pretty_midi for MIDI creation.
        """
        try:
            # Load the audio file
            y, sr = librosa.load(str(input_path))
            
            # Extract pitch using librosa with more conservative parameters
            hop_length = 512  # Increase for better pitch stability
            fmin = librosa.note_to_hz('C2')  # Set minimum frequency
            fmax = librosa.note_to_hz('C7')  # Set maximum frequency
            
            # Use more reliable pitch detection with amplitude threshold
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pitches, magnitudes = librosa.piptrack(
                    y=y, 
                    sr=sr,
                    hop_length=hop_length,
                    fmin=fmin,
                    fmax=fmax,
                    threshold=0.1  # Add threshold to filter out very quiet sounds
                )
            
            # Create a PrettyMIDI object with the song's BPM if available
            bpm = self._get_song_bpm(input_path)
            pm = pretty_midi.PrettyMIDI(initial_tempo=bpm if bpm is not None else 120.0)
            
            # Create a voice program instead of piano
            voice_program = pretty_midi.instrument_name_to_program('Choir Aahs')  # Using choir voice
            voice = pretty_midi.Instrument(program=voice_program)
            
            # Convert pitch detections to MIDI notes with onset detection
            onset_frames = librosa.onset.onset_detect(
                y=y, 
                sr=sr,
                hop_length=hop_length,
                backtrack=True,
                pre_max=20,  # Look up to 20 frames back for onset
                post_max=20,  # Look up to 20 frames ahead for onset
                pre_avg=100,  # Compare with 100 frames of history
                post_avg=100,  # Compare with 100 frames of future
                delta=0.2,    # Minimum difference for onset
                wait=30       # Wait 30 frames after onset
            )
            
            # Process each onset
            for onset_frame in onset_frames:
                # Find the highest magnitude pitch at this frame
                pitch_index = magnitudes[:, onset_frame].argmax()
                magnitude = magnitudes[pitch_index, onset_frame]
                
                # Only process if magnitude is significant
                if magnitude > 0.1:  # Adjust threshold as needed
                    pitch_hz = pitches[pitch_index, onset_frame]
                    
                    if pitch_hz > 0:  # Ensure we have a valid frequency
                        # Convert Hz to MIDI note number
                        pitch_midi = librosa.hz_to_midi(pitch_hz)
                        
                        # Ensure pitch is within valid MIDI range (0-127)
                        if 0 <= pitch_midi <= 127:
                            # Convert frame numbers to time
                            start_time = librosa.frames_to_time(onset_frame, sr=sr, hop_length=hop_length)
                            # Make note duration proportional to onset spacing
                            if onset_frame + 1 < len(onset_frames):
                                next_onset = onset_frames[onset_frame + 1]
                                duration = librosa.frames_to_time(next_onset - onset_frame, sr=sr, hop_length=hop_length)
                                duration = min(duration, 1.0)  # Cap duration at 1 second
                            else:
                                duration = 0.25  # Default duration for last note
                            
                            # Create a Note object
                            note = pretty_midi.Note(
                                velocity=64,  # Use a more moderate velocity
                                pitch=int(round(pitch_midi)),
                                start=start_time,
                                end=start_time + duration
                            )
                            voice.notes.append(note)
            
            # Add the instrument to the PrettyMIDI object
            pm.instruments.append(voice)
            
            # Write out the MIDI file
            pm.write(str(output_path))
            
        except Exception as e:
            raise Exception(f"Failed to convert audio file: {str(e)}")
    
    async def convert_all(self) -> List[Union[Path, Exception]]:
        """Convert all audio files in the songs directory.
        
        Returns:
            List of paths to the generated MIDI files or exceptions for failed conversions
        """
        audio_files = []
        for ext in ('*.egg', '*.ogg'):
            audio_files.extend(self.songs_dir.rglob(ext))
        
        if not audio_files:
            return []
        
        # Create tasks for each file
        tasks = [self.convert_audio(audio_file) for audio_file in audio_files]
        
        # Create progress bar
        pbar = tqdm(total=len(tasks), desc="Converting audio files")
        
        # Process tasks and update progress
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                results.append(e)
            pbar.update(1)
        
        pbar.close()
        return results 