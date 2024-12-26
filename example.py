#!/usr/bin/env python3

"""
Example script that demonstrates how to call the AI Beat Saber pipeline
from the ai_beat_saber package. This script follows a typical usage flow:
1. Specify how many pages of ranked Beat Saber maps you want to download.
2. Specify where the pipeline outputs should be stored.
3. Request to generate new maps or not.
4. Force the pipeline to rerun steps as needed.
5. Specify the difficulty level to filter/prune.

Usage:
    python run_full_pipeline.py --pages 2 --output-dir ./my_pipeline_output --force

Refer to the package code in ai_beat_saber/run_pipeline.py for the full pipeline details.
"""

import argparse
import asyncio
from ai_beat_saber.run_pipeline import run_pipeline

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
