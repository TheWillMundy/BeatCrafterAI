"""
Helper script to clean up pipeline outputs and cached data.
"""

import shutil
from pathlib import Path
import logging
from typing import Optional, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_directory(directory: Path, keep_structure: bool = True):
    """Clean a directory while optionally preserving its structure.
    
    Args:
        directory: Directory to clean
        keep_structure: If True, keep the directory but remove contents
    """
    if not directory.exists():
        return
        
    if keep_structure:
        # Remove contents but keep directory
        for item in directory.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    else:
        # Remove entire directory
        shutil.rmtree(directory)

def clean_pipeline_outputs(base_dir: str = "pipeline_output", 
                         training_dir: str = "training_data",
                         targets: Optional[List[str]] = None):
    """Clean pipeline outputs while preserving directory structure.
    
    Args:
        base_dir: Base pipeline output directory
        training_dir: Training data directory
        targets: Specific targets to clean. If None, clean all.
                Options: ['downloads', 'extracted', 'midi', 'formatted', 
                         'generated', 'logs', 'combined', 'pruned', 'training', 'all']
    """
    base_path = Path(base_dir)
    training_path = Path(training_dir)
    
    # Define all cleanable directories
    directories = {
        'downloads': base_path / "songs",
        'extracted': base_path / "extracted",
        'midi': base_path / "midi",
        'formatted': base_path / "formatted",
        'generated': base_path / "output/new_maps",
        'logs': base_path / "output/logs",
        'combined': base_path / "combined",
        'pruned': base_path / "pruned",
        'training': training_path
    }
    
    # If no specific targets, clean everything
    if targets is None or 'all' in targets:
        targets = directories.keys()
    
    # Clean checkpoint file if it exists
    checkpoint_file = base_path / "pipeline_checkpoint.json"
    if checkpoint_file.exists():
        checkpoint_file.unlink()
        logger.info("Removed checkpoint file")
    
    # Clean each specified directory
    for target in targets:
        if target in directories:
            dir_path = directories[target]
            clean_directory(dir_path)
            logger.info(f"Cleaned {target} directory: {dir_path}")
        else:
            logger.warning(f"Unknown target directory: {target}")

def main():
    """Command line interface for cleanup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean pipeline outputs and cached data")
    parser.add_argument(
        "--base-dir",
        type=str,
        default="pipeline_output",
        help="Base pipeline output directory"
    )
    parser.add_argument(
        "--training-dir",
        type=str,
        default="training_data",
        help="Training data directory"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=['downloads', 'extracted', 'midi', 'formatted', 
                'generated', 'logs', 'combined', 'pruned', 'training', 'all'],
        help="Specific targets to clean"
    )
    parser.add_argument(
        "--remove-structure",
        action="store_true",
        help="Remove directory structure as well (default: keep structure)"
    )
    
    args = parser.parse_args()
    
    if args.remove_structure:
        # Remove entire directories
        if args.targets is None or 'all' in args.targets:
            if Path(args.base_dir).exists():
                shutil.rmtree(args.base_dir)
                logger.info(f"Removed entire pipeline directory: {args.base_dir}")
            if Path(args.training_dir).exists():
                shutil.rmtree(args.training_dir)
                logger.info(f"Removed entire training directory: {args.training_dir}")
        else:
            clean_pipeline_outputs(args.base_dir, args.training_dir, args.targets)
    else:
        # Keep structure but clean contents
        clean_pipeline_outputs(args.base_dir, args.training_dir, args.targets)

if __name__ == "__main__":
    main() 