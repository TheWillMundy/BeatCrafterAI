## AI Beat Saber Map Generator

### Project Description
**Project**: AI Beat Saber Map Generator  
**Description**: This project automates downloading ranked Beat Saber maps from BeatSaver, processes them, and uses an LLM to generate new maps. The goal is to create high-quality, playable Beat Saber maps using AI. Users can generate maps from both BeatSaver data and their own songs via YouTube links.

### Project Structure
```
project-root/
  ├─ README.md                 # Project documentation
  ├─ requirements.txt          # Python dependencies
  ├─ ai_beat_saber/           # Main package directory
  │   ├─ downloader/          # BeatSaver API interaction & map downloading
  │   ├─ extractor/           # Map extraction utilities
  │   ├─ converter/           # Audio processing & MIDI conversion
  │   ├─ preprocessor/        # YouTube song preprocessing
  │   ├─ data_formatter/      # Data preparation for LLM
  │   └─ llm_prompting/       # LLM interaction & map generation
  ├─ tests/                   # Test suite
  │   ├─ integration/         # Integration tests
  │   └─ unit/               # Unit tests
  └─ data/                    # Data directories
      ├─ downloads/           # Downloaded map ZIPs
      ├─ extracted/           # Extracted map contents
      ├─ midi/               # Converted MIDI files
      └─ output/             # Generated maps
```

### Installation

1. **Clone the Repository**  
   ```bash
   git clone <repo-url>
   cd ai-beat-saber
   ```

2. **Install System Dependencies**
   ```bash
   # On macOS
   brew install ffmpeg

   # On Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ffmpeg

   # On Windows
   # Download FFmpeg from https://ffmpeg.org/download.html
   ```

3. **Set Up Python Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Core Components

#### Map Downloader
The downloader component (`ai_beat_saber.downloader`) provides:
- Automated fetching of ranked maps from BeatSaver API
- Pagination support for bulk downloads
- Automatic skipping of previously downloaded maps
- Progress tracking during downloads
- Configurable download limits and filtering

Example usage:
```python
from ai_beat_saber.downloader import BeatSaverDownloader

downloader = BeatSaverDownloader(max_pages=2)
await downloader.download_all()
```

#### YouTube Preprocessor
The preprocessor component (`ai_beat_saber.preprocessor`) enables:
- Downloading songs from YouTube URLs
- Converting audio to MP3 format
- Processing audio into MIDI for map generation
- Support for various audio formats and quality levels

Example usage:
```python
from ai_beat_saber.preprocessor import YouTubePreprocessor

preprocessor = YouTubePreprocessor(output_dir="data/processed")
result = await preprocessor.process_song("https://youtube.com/watch?v=...")
if result:
    print(f"MIDI file created at: {result['midi_path']}")
```

### Development

#### Running Tests
```bash
pytest tests/
```

The test suite includes:
- Integration tests for the BeatSaver API interaction
- Download functionality verification
- Audio processing and conversion tests
- YouTube integration tests
- File handling and extraction tests

#### Contributing
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

### Project Status
- ✅ Implemented: BeatSaver API integration and map downloading
- ✅ Implemented: Map extraction and processing
- ✅ Implemented: Audio to MIDI conversion
- ✅ Implemented: YouTube song preprocessing
- 🚧 In Progress: Data formatting for LLM
- 📅 Planned: LLM integration and map generation

### Dependencies
Key dependencies include:
- `yt-dlp`: YouTube video downloading
- `ffmpeg-python`: Audio format conversion
- `librosa`: Audio processing and analysis
- `pretty_midi`: MIDI file creation
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support

See `requirements.txt` for complete list and versions.

### License
[License Type] - See LICENSE file for details

### Acknowledgments
- BeatSaver API for providing access to the Beat Saber map database
- Beat Saber community for map data and inspiration
- YouTube-DL project for video downloading capabilities