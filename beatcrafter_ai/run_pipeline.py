"""
Main pipeline script for downloading, processing, and generating Beat Saber maps.
"""

import asyncio
from pathlib import Path
import argparse
import json
from typing import Dict, Any, List
from tqdm import tqdm

from beatcrafter_ai.downloader.scrape_and_download import BeatSaverDownloader
from beatcrafter_ai.extractor.extract_maps import MapExtractor
from beatcrafter_ai.converter.convert_audio import AudioConverter
from beatcrafter_ai.data_formatter.format_data import DataFormatter
from beatcrafter_ai.llm_prompting.generate_maps import MapGenerator
from beatcrafter_ai.post_processor.prune_maps import MapPruner

def load_checkpoint(file_path: Path) -> Dict[str, Any]:
    """Load checkpoint data from a JSON file."""
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_checkpoint(file_path: Path, data: Dict[str, Any]):
    """Save checkpoint data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

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
        "logs": base_dir / "output/logs",
        "combined": base_dir / "combined",  # Add combined dir to dirs dict
        "pruned": base_dir / "pruned"  # Add pruned dir for pruned maps
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint (or start fresh if force is True)
    checkpoint_file = base_dir / "pipeline_checkpoint.json"
    checkpoint = {} if args.force else load_checkpoint(checkpoint_file)
    
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
    
    # === Download Step ===
    if not checkpoint.get("downloads_complete") or args.force:
        print("\n=== Downloading Maps ===")
        # Always clean the downloads directory if force is True
        if args.force and dirs["downloads"].exists():
            import shutil
            shutil.rmtree(dirs["downloads"])
            dirs["downloads"].mkdir()
        
        await downloader.download_all()
        checkpoint["downloads_complete"] = True
        save_checkpoint(checkpoint_file, checkpoint)
    else:
        print("\n=== Skipping Downloads (already completed) ===")
    
    # === Extract Step ===
    if not checkpoint.get("extraction_complete") or args.force:
        print("\n=== Extracting Maps ===")
        # Always clean the extraction directory if force is True
        if args.force and dirs["extracted"].exists():
            import shutil
            shutil.rmtree(dirs["extracted"])
            dirs["extracted"].mkdir()
        
        extracted_maps = extractor.extract_all()
        # Save extraction results
        extraction_log = dirs["logs"] / "extraction_results.json"
        with open(extraction_log, 'w', encoding='utf-8') as f:
            json.dump({
                'total_extracted': len(extracted_maps),
                'maps': extracted_maps
            }, f, indent=2)
        checkpoint["extraction_complete"] = True
        save_checkpoint(checkpoint_file, checkpoint)
    else:
        print("\n=== Skipping Extraction (already completed) ===")
        # Load existing extraction results
        extraction_log = dirs["logs"] / "extraction_results.json"
        with open(extraction_log, 'r') as f:
            extracted_maps = json.load(f)["maps"]
    
    # === Convert Step ===
    if not checkpoint.get("conversion_complete") or args.force:
        print("\n=== Converting Audio to MIDI ===")
        # Always clean the MIDI directory if force is True
        if args.force and dirs["midi"].exists():
            import shutil
            shutil.rmtree(dirs["midi"])
            dirs["midi"].mkdir()
        
        # Search for audio files in extracted song directories
        audio_files = []
        for ext in ('*.ogg', '*.egg', '*.mp3', '*.m4a', '*.wav'):  # Added more formats
            audio_files.extend(dirs["extracted"].rglob(ext))
        
        print(f"Found {len(audio_files)} audio files to convert:")
        for audio_file in audio_files:
            print(f"  - {audio_file.relative_to(dirs['extracted'])}")
        
        if not audio_files:
            print("Warning: No audio files found in extracted directories!")
            print(f"Searched in: {dirs['extracted']}")
            print("Contents of extracted directory:")
            for item in dirs["extracted"].rglob("*"):
                print(f"  - {item.relative_to(dirs['extracted'])}")
        
        conversion_results = await converter.convert_all()
        successful_conversions = []
        failed_conversions = []
        for result in conversion_results:
            if isinstance(result, Exception):
                failed_conversions.append(str(result))
            elif isinstance(result, Path):
                successful_conversions.append(str(result))
        
        print(f"\nConversion Results:")
        print(f"  Successful: {len(successful_conversions)}")
        print(f"  Failed: {len(failed_conversions)}")
        if failed_conversions:
            print("\nFailed conversions:")
            for error in failed_conversions:
                print(f"  - {error}")
        
        # Log conversion results
        conversion_log = dirs["logs"] / "conversion_results.json"
        with open(conversion_log, 'w', encoding='utf-8') as f:
            json.dump({
                'total_attempted': len(successful_conversions) + len(failed_conversions),
                'successful': len(successful_conversions),
                'failed': len(failed_conversions),
                'successful_files': successful_conversions,
                'errors': failed_conversions
            }, f, indent=2)
        
        checkpoint["conversion_complete"] = True
        save_checkpoint(checkpoint_file, checkpoint)
    else:
        print("\n=== Skipping Conversion (already completed) ===")
        # Load existing conversion results
        conversion_log = dirs["logs"] / "conversion_results.json"
        with open(conversion_log, 'r') as f:
            conversion_data = json.load(f)
            successful_conversions = conversion_data["successful_files"]
            failed_conversions = conversion_data.get("errors", [])
    
    # === Prepare Combined Directory ===
    print("\n=== Preparing Combined Directory ===")
    # Always clean the combined directory
    import shutil
    if dirs["combined"].exists():
        shutil.rmtree(dirs["combined"])
    dirs["combined"].mkdir()
    
    # Copy extracted maps to combined directory
    for item in dirs["extracted"].glob("*"):
        if item.is_dir():
            dest = dirs["combined"] / item.name
            shutil.copytree(item, dest)
            # Create midi_output directory
            midi_output = dest / "midi_output"
            midi_output.mkdir(exist_ok=True)
            # Copy corresponding MIDI file if it exists
            midi_file = dirs["midi"] / f"{item.name}.mid"
            if midi_file.exists():
                shutil.copy2(midi_file, midi_output / f"{item.name}.mid")
    
    # === Format Step ===
    if not checkpoint.get("formatting_complete") or args.force:
        print("\n=== Formatting Training Data ===")
        # Always clean the formatted directory if force is True
        if args.force and dirs["formatted"].exists():
            shutil.rmtree(dirs["formatted"])
            dirs["formatted"].mkdir()
        
        formatter = DataFormatter(
            songs_dir=dirs["combined"],
            output_dir=dirs["formatted"]
        )
        
        try:
            formatted_data = formatter.format_all()
            print(f"\nFormatting complete: {len(formatted_data)} songs processed")
            print(f"\nTraining data saved to: {dirs['formatted'].absolute()}")
            checkpoint["formatting_complete"] = True
            save_checkpoint(checkpoint_file, checkpoint)
        except Exception as e:
            print(f"Error during formatting: {str(e)}")
            raise
    else:
        print("\n=== Skipping Formatting (already completed) ===")
    
    # === Prune Step ===
    if not checkpoint.get("pruning_complete") or args.force:
        print("\n=== Pruning Maps ===")
        # Always clean the pruned directory if force is True
        if args.force and dirs["pruned"].exists():
            shutil.rmtree(dirs["pruned"])
            dirs["pruned"].mkdir()
        
        pruner = MapPruner(dirs["formatted"], dirs["pruned"])
        pruner.process_all(args.difficulty)
        print(f"\nPruning complete. Pruned maps saved to: {dirs['pruned'].absolute()}")
        checkpoint["pruning_complete"] = True
        save_checkpoint(checkpoint_file, checkpoint)
    else:
        print("\n=== Skipping Pruning (already completed) ===")
    
    if args.generate:
        print("\n=== Generating New Maps ===")
        generator = MapGenerator(
            formatted_data_dir=dirs["pruned"],  # Use pruned data for generation
            output_dir=base_dir / "output"
        )
        # TODO: Implement map generation
        print("Map generation not yet implemented")

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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rerun of steps even if files exist"
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="Hard",
        choices=["Easy", "Normal", "Hard", "Expert", "ExpertPlus"],
        help="Target difficulty level to keep (default: Hard)"
    )
    
    args = parser.parse_args()
    asyncio.run(run_pipeline(args))

if __name__ == "__main__":
    main() 