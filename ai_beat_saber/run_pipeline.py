"""
Main pipeline script for downloading, processing, and generating Beat Saber maps.
"""

import asyncio
from pathlib import Path
import argparse
import json

from ai_beat_saber.downloader.scrape_and_download import BeatSaverDownloader
from ai_beat_saber.extractor.extract_maps import MapExtractor
from ai_beat_saber.converter.convert_audio import AudioConverter
from ai_beat_saber.data_formatter.format_data import DataFormatter
from ai_beat_saber.llm_prompting.generate_maps import MapGenerator

async def run_pipeline(args):
    """Run the full pipeline."""
    # Setup directories
    base_dir = Path(args.output_dir)
    dirs = {
        "downloads": base_dir / "songs",
        "extracted": base_dir / "extracted",
        "midi": base_dir / "midi",
        "formatted": base_dir / "formatted",
        "generated": base_dir / "output/new_maps",
        "logs": base_dir / "output/logs"
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    downloader = BeatSaverDownloader(max_pages=args.pages)
    downloader.download_path = dirs["downloads"]
    
    extractor = MapExtractor(
        zip_dir=dirs["downloads"],
        output_dir=dirs["extracted"]
    )
    
    converter = AudioConverter(
        songs_dir=dirs["extracted"],
        output_dir=dirs["midi"]
    )
    
    formatter = DataFormatter(
        songs_dir=dirs["extracted"],
        output_dir=dirs["formatted"]
    )
    
    generator = MapGenerator(
        formatted_data_dir=dirs["formatted"],
        output_dir=dirs["generated"]
    )
    
    # Run pipeline
    print("Downloading maps...")
    await downloader.download_all()
    
    print("Extracting maps...")
    extracted_maps = extractor.extract_all()
    print(f"Successfully extracted {len(extracted_maps)} maps")
    
    # Save extraction results for debugging/analysis
    extraction_log = dirs["logs"] / "extraction_results.json"
    with open(extraction_log, 'w', encoding='utf-8') as f:
        json.dump({
            'total_extracted': len(extracted_maps),
            'maps': extracted_maps
        }, f, indent=2)
    
    print("Converting audio to MIDI...")
    converter.convert_all()
    
    print("Formatting data...")
    formatted_data = formatter.format_all()
    
    if args.generate:
        print("Generating new maps...")
        # TODO: Implement map generation pipeline
        pass

def main():
    parser = argparse.ArgumentParser(description="Run the Beat Saber map pipeline")
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to download (default: 1)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Base output directory (default: current directory)"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate new maps after processing"
    )
    
    args = parser.parse_args()
    asyncio.run(run_pipeline(args))

if __name__ == "__main__":
    main() 