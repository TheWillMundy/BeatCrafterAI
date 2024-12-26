#!/usr/bin/env python3

"""
Example script demonstrating how to use the pipeline functionality
from the beatcrafter_ai package. This script follows a typical usage flow:

1. Download maps from BeatSaver
2. Extract the downloaded maps
3. Convert audio to MIDI
4. Format data for LLM training
5. Generate new maps with LLM
6. Post-process and prune maps

Refer to the package code in beatcrafter_ai/run_pipeline.py for the full pipeline details.
"""

import argparse
import asyncio
from pathlib import Path
from beatcrafter_ai.run_pipeline import run_pipeline

async def main():
    parser = argparse.ArgumentParser(description="Example usage of the AI Beat Saber pipeline.")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to download (default 1)")
    parser.add_argument("--output-dir", type=str, default="pipeline_output", help="Base output directory")
    parser.add_argument("--generate", action="store_true", help="Generate new maps after processing")
    parser.add_argument("--force", action="store_true", help="Force rerun of steps even if files exist")
    parser.add_argument("--difficulty", type=str, default="Hard",
                        choices=["Easy", "Normal", "Hard", "Expert", "ExpertPlus"],
                        help="Target difficulty level to keep (default: Hard)")
    args = parser.parse_args()

    # Simply call into the pipeline logic provided by the package
    await run_pipeline(args)

if __name__ == "__main__":
    asyncio.run(main())
