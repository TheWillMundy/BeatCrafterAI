# AI Beat Saber Map Generator

## Overview
This project provides a fully automated pipeline for acquiring and processing Beat Saber maps, then using a Large Language Model (LLM) to generate new maps. The workflow includes:

* Bulk downloading maps from BeatSaver
* Extracting and converting audio into MIDI
* Preparing data in an LLM-friendly format
* Optionally generating new maps with an LLM

## Features
1. Download and handle hundreds of Beat Saber maps from the official community repository (beatsaver.com)
2. Extract map files (info.dat, .dat difficulties, .egg/.ogg audio) into a consistent directory structure
3. Convert audio into MIDI, enabling an AI-driven approach to map generation
4. Accept YouTube links for new songs, automatically handling the extraction, conversion, and packaging
5. Prompt an AI model to create brand-new .dat difficulty files

## Installation
1. Clone the Repository
    ```bash
    git clone <repo-url>
    cd beatcrafter-ai
    ```

2. Install System Dependencies
    - macOS:   `brew install ffmpeg`
    - Ubuntu:  `sudo apt-get install ffmpeg`
    - Windows: Download FFmpeg from https://ffmpeg.org/download.html

3. Set Up Python Environment and Install Additional Dependencies
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4. Configure Environment Variables
    - Copy the `.env.example` file to a new file named `.env`
    - Open the `.env` file and replace placeholder values with your actual API keys and other necessary configurations
    - For example, set your OpenAI API key:
        ```
        OPENAI_API_KEY=your_actual_openai_api_key
        ```

## Usage

### Running the Full Pipeline
Run the pipeline with default settings:
```bash
python example.py
```

Or customize the pipeline run:
```bash
python example.py --pages 2 --force --difficulty Expert
```

By default, it will download 1 page of maps, extract them, convert audio to MIDI, format everything, and prune to a specific difficulty.

### Advanced Usage

#### Using the Pipeline Programmatically
Import and call the pipeline directly:
```python
from beatcrafter_ai.run_pipeline import run_pipeline

# Configure pipeline arguments
args = {
    "pages": 2,
    "force": True,
    "difficulty": "Expert"
}
await run_pipeline(args)
```

#### Using Individual Components
You can also use any of the pipeline components directly:

```python
from beatcrafter_ai.downloader import BeatSaverDownloader
from beatcrafter_ai.converter import AudioConverter
from beatcrafter_ai.extractor import MapExtractor

# Download maps
downloader = BeatSaverDownloader(max_pages=1)
await downloader.download_all()

# Extract maps
extractor = MapExtractor(zip_dir="downloads", output_dir="extracted")
extracted_maps = extractor.extract_all()

# Convert audio to MIDI
converter = AudioConverter(songs_dir="extracted", output_dir="midi")
converter.convert_all()
```

### Cleanup
The pipeline generates numerous intermediate files. Use the cleanup script to manage these outputs:

```bash
# Clean all pipeline outputs while keeping directory structure
python -m beatcrafter_ai.cleanup

# Clean specific directories (downloads, extracted, midi, etc.)
python -m beatcrafter_ai.cleanup --targets downloads midi

# Remove entire pipeline directory structure
python -m beatcrafter_ai.cleanup --remove-structure
```

## Project Layout
```
beatcrafter-ai/
├── example.py                 # Example script showing how to use the package
├── beatcrafter_ai/           # Main Python package with submodules
│   ├── downloader/           # Downloading & scraping logic
│   ├── extractor/            # ZIP extraction & .dat file management
│   ├── converter/            # Audio → MIDI conversion code
│   ├── data_formatter/       # Consolidation of .dat + MIDI → dataset for LLM
│   ├── llm_prompting/        # Code to prompt an LLM for new map generation
│   └── post_processor/       # Pruning or refining final map data
├── tests/                    # Unit & integration tests
├── PRD.md                    # Product Requirements Document
└── README.md                 # This documentation
```

## Contributing

We love your input! Here's how you can contribute:

🔀 **Fork the Repository**  
Create your own fork of the project

🌿 **Create a Branch**  
Make your changes in a new git branch:
```bash
git checkout -b feature/amazing-feature
```

🔧 **Make Changes**  
- Write your code
- Add or update tests
- Update documentation

✅ **Verify**  
Make sure your code passes all tests:
```bash
pytest
```

📬 **Submit**  
Push your changes and create a pull request

## License
Distributed under the MIT License. See [LICENSE](LICENSE) file for more information.