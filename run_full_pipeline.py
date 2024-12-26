#!/usr/bin/env python3

"""
Script to run the full Beat Saber pipeline and generate training data.
"""

import asyncio
from pathlib import Path
import logging

from ai_beat_saber.run_pipeline import run_pipeline
from ai_beat_saber.post_processor.prune_maps import MapPruner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Set up pipeline arguments
    class Args:
        def __init__(self):
            self.pages = 1  # Start with 1 page for testing
            self.output_dir = "pipeline_output"  # Store everything in a dedicated directory
            self.generate = False  # Don't generate new maps yet, just prepare training data
            self.force = True  # Force rerun of steps to ensure we get data
            self.difficulty = "Hard"  # Default difficulty level to keep
    
    # Create output directory structure
    output_dir = Path("pipeline_output")
    training_data_dir = Path("training_data")
    
    # Create directories
    output_dir.mkdir(exist_ok=True)
    training_data_dir.mkdir(exist_ok=True)
    
    print("=== Starting Beat Saber Pipeline ===")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Training data will be saved to: {training_data_dir.absolute()}")
    
    # Run the pipeline
    await run_pipeline(Args())
    
    # Get formatted data and prune it
    formatted_dir = output_dir / "formatted"
    if formatted_dir.exists():
        # Clear existing training data
        if training_data_dir.exists():
            import shutil
            shutil.rmtree(training_data_dir)
            training_data_dir.mkdir()
        
        # Post-process the maps and save directly to training_data
        print("\n=== Post-processing Maps ===")
        pruner = MapPruner(formatted_dir, training_data_dir)
        pruner.process_all(Args().difficulty)
        print(f"Pruned maps saved to: {training_data_dir.absolute()}")
    else:
        print("\nWarning: No formatted data found!")

if __name__ == "__main__":
    asyncio.run(main())
