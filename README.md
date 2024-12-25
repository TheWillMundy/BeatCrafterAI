## AI Beat Saber Map Generator

### Project Description
**Project**: AI Beat Saber Map Generator  
**Description**: This project automates downloading ranked Beat Saber maps from BeatSaver, processes them, and uses an LLM to generate new maps. The goal is to create high-quality, playable Beat Saber maps using AI.

### Project Structure
```
project-root/
  ├─ README.md                 # Project documentation
  ├─ requirements.txt          # Python dependencies
  ├─ ai_beat_saber/           # Main package directory
  │   ├─ downloader/          # BeatSaver API interaction & map downloading
  │   ├─ extractor/           # Map extraction utilities
  │   ├─ converter/           # Audio processing & MIDI conversion
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

2. **Set Up Python Environment**  
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

### Development

#### Running Tests
```bash
pytest tests/
```

The test suite includes:
- Integration tests for the BeatSaver API interaction
- Download functionality verification
- File handling and extraction tests

#### Contributing
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

### Project Status
- ✅ Implemented: BeatSaver API integration and map downloading
- 🚧 In Progress: Map extraction and processing
- 📅 Planned: Audio to MIDI conversion, LLM integration

### License
[License Type] - See LICENSE file for details

### Acknowledgments
- BeatSaver API for providing access to the Beat Saber map database
- Beat Saber community for map data and inspiration