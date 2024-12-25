"""
Preprocess YouTube songs for Beat Saber map generation.
"""

import asyncio
from pathlib import Path
import yt_dlp
from typing import Optional, Dict, Any
import soundfile as sf
import tempfile
import os

from ai_beat_saber.converter.convert_audio import AudioConverter

class YouTubePreprocessor:
    """Download and preprocess YouTube songs for Beat Saber map generation."""
    
    def __init__(self, output_dir: Path):
        """Initialize the preprocessor.
        
        Args:
            output_dir: Directory to save processed files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.audio_dir = self.output_dir / "audio"
        self.midi_dir = self.output_dir / "midi"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.midi_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize audio converter
        self.audio_converter = AudioConverter(self.audio_dir, self.midi_dir)
    
    async def download_song(self, youtube_url: str) -> Optional[Dict[str, Any]]:
        """Download a song from YouTube.
        
        Args:
            youtube_url: URL of the YouTube video
            
        Returns:
            Dict containing paths to downloaded files and metadata, or None if download fails
        """
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Try mp3 first as it's more reliable
                    'preferredquality': '192',
                }],
                'outtmpl': str(self.audio_dir / '%(id)s.%(ext)s'),
                'quiet': False,  # Enable output for debugging
                'no_warnings': False,  # Show warnings for debugging
                'keepvideo': False,
                'writethumbnail': False,
                'verbose': True  # Add verbose output for debugging
            }
            
            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    print(f"\nDownloading audio from: {youtube_url}")
                    info = ydl.extract_info(youtube_url, download=True)
                    if info is None:
                        print("No video information found")
                        return None
                    
                    # Try to find the downloaded file with any audio extension
                    video_id = info['id']
                    audio_extensions = ['.mp3', '.ogg', '.m4a', '.opus']
                    audio_path = None
                    
                    for ext in audio_extensions:
                        potential_path = self.audio_dir / f"{video_id}{ext}"
                        if potential_path.exists():
                            audio_path = potential_path
                            print(f"Found audio file: {audio_path}")
                            break
                    
                    if audio_path is None:
                        print(f"No audio file found in {self.audio_dir} for video ID: {video_id}")
                        print(f"Directory contents: {list(self.audio_dir.glob('*'))}")
                        return None
                    
                    result = {
                        'video_id': video_id,
                        'title': info.get('title', 'Unknown Title'),
                        'duration': info.get('duration', 0),
                        'audio_path': audio_path
                    }
                    print(f"Download successful: {result}")
                    return result
                    
                except yt_dlp.utils.DownloadError as e:
                    print(f"Download error: {str(e)}")
                    return None
                    
        except Exception as e:
            print(f"Error downloading YouTube video: {str(e)}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Audio directory: {self.audio_dir}")
            return None
    
    async def process_song(self, youtube_url: str) -> Optional[Dict[str, Any]]:
        """Download and process a YouTube song for Beat Saber map generation.
        
        Args:
            youtube_url: URL of the YouTube video
            
        Returns:
            Dict containing paths to processed files and metadata, or None if processing fails
        """
        # Download the song
        download_result = await self.download_song(youtube_url)
        if not download_result:
            return None
        
        try:
            print(f"\nConverting audio to MIDI: {download_result['audio_path']}")
            # Convert to MIDI
            midi_path = await self.audio_converter.convert_audio(download_result['audio_path'])
            
            # Add MIDI path to results
            download_result['midi_path'] = midi_path
            print(f"Conversion successful: {midi_path}")
            return download_result
            
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None 