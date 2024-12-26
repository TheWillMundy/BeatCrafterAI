# AI Beat Saber Map Generator

## Overview
This project provides a fully automated pipeline for acquiring and processing Beat Saber maps, then using a Large Language Model (LLM) to generate new maps. The workflow includes:

• Bulk downloading maps from BeatSaver  
• Extracting and converting audio into MIDI  
• Preparing data in an LLM-friendly format  
• Optionally generating new maps with an LLM

## Features
1. Download and handle hundreds of Beat Saber maps from the official community repository (beatsaver.com).  
2. Extract map files (info.dat, .dat difficulties, .egg/.ogg audio) into a consistent directory structure.  
3. Convert audio into MIDI, enabling an AI-driven approach to map generation.  
4. Accept YouTube links for new songs, automatically handling the extraction, conversion, and packaging.  
5. Prompt an AI model to create brand-new .dat difficulty files.

## Installation
1. Clone the Repository  
   ┌───────────────────────  
   git clone <repo-url>  
   cd beatcrafter-ai  
   └───────────────────────  

2. Install System Dependencies  
   - macOS:   brew install ffmpeg  
   - Ubuntu:  sudo apt-get install ffmpeg  
   - Windows: Download FFmpeg from https://ffmpeg.org/download.html  

3. Set Up Python Environment and Install Additional Dependencies  
   ┌─────────────────────────────  
   python -m venv venv  
   source venv/bin/activate  
   pip install -r requirements.txt  
   └─────────────────────────────  

4. Configure Environment Variables  
   - Copy the `.env.example` file to a new file named `.env`.  
   - Open the `.env` file and replace placeholder values with your actual API keys and other necessary configurations.  
   - For example, set your OpenAI API key:  
     ```
     OPENAI_API_KEY=your_actual_openai_api_key
     ```

## Usage
After installation:

• Run the pipeline:  
  ┌──────────────────────────────────────  
  python example.py --pages 2 --force  
  └──────────────────────────────────────  
  
  By default, it will download 1 page of maps, extract them, convert audio to MIDI, format everything, and prune to a specific difficulty.  

• For advanced usage or custom scripts, import and call the pipeline directly:  
  ┌─────────────────────────────────────────────────────────
  from beatcrafter_ai.run_pipeline import run_pipeline
  
  # Then pass your own argparse-like arguments
  └─────────────────────────────────────────────────────────

• Clean up pipeline outputs:
  The pipeline generates numerous intermediate files across multiple stages (downloads, MIDI conversions, etc.).
  Use the cleanup script to manage these outputs while preserving your working directory:
  
  ┌──────────────────────────────────────  
  # Clean all pipeline outputs while keeping directory structure
  python -m beatcrafter_ai.cleanup
  
  # Clean specific directories (downloads, extracted, midi, etc.)
  python -m beatcrafter_ai.cleanup --targets downloads midi
  
  # Remove entire pipeline directory structure
  python -m beatcrafter_ai.cleanup --remove-structure
  └──────────────────────────────────────

## Project Layout
| Folder/File                   | Description                                                   |
|-------------------------------|---------------------------------------------------------------|
| example.py                    | Example script showing how to use the package                |
| beatcrafter_ai/              | Main Python package with submodules                         |
| ├─ downloader/                | Downloading & scraping logic                                 |
| ├─ extractor/                 | ZIP extraction & .dat file management                        |
| ├─ converter/                 | Audio → MIDI conversion code                                 |
| ├─ data_formatter/            | Consolidation of .dat + MIDI → dataset for LLM              |
| ├─ llm_prompting/             | Code to prompt an LLM for new map generation                |
| ├─ post_processor/            | Pruning or refining final map data                           |
| tests/                        | Unit & integration tests                                     |
| PRD.md                        | Product Requirements Document (concise spec & approach)      |
| README.md                     | This documentation                                           |

## Contributing
Contributions are welcome!  
1. Fork the repository  
2. Create a feature branch  
3. Develop and test thoroughly  
4. Submit a pull request  

## License
Distributed under the MIT License. See [LICENSE](LICENSE) file for more information.