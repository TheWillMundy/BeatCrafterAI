import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import argparse

import httpx
from tqdm import tqdm

BASE_API_URL = "https://beatsaver.com/api/search/text"
PARAMS = {
    "sortOrder": "Rating",
    "leaderboard": "Ranked"
}
MAX_CONCURRENT_DOWNLOADS = 5

class BeatSaverDownloader:
    def __init__(self, max_pages: int = 1):
        self.download_path = Path("songs")
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    
    def setup_directories(self):
        """Ensure download directory exists."""
        self.download_path = Path(self.download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        
    async def fetch_ranked_maps(self, page: int = 0) -> Dict[str, Any]:
        """Fetch a page of ranked maps from BeatSaver API."""
        url = f"{BASE_API_URL}/{page}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=PARAMS)
            response.raise_for_status()
            return response.json()

    async def download_map(self, song_id: str, download_url: str, progress_bar: tqdm) -> bool:
        """Download a single map ZIP file.
        
        Returns:
            bool: True if download was successful, False otherwise
        """
        zip_path = self.download_path / f"{song_id}.zip"
        
        if zip_path.exists():
            progress_bar.write(f"Skipping {song_id}, already downloaded")
            progress_bar.update(1)
            return True
            
        async with self.semaphore:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(download_url)
                    response.raise_for_status()
                    
                    # Ensure parent directory exists
                    zip_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write the file
                    zip_path.write_bytes(response.content)
                    progress_bar.update(1)
                    return True
                    
            except Exception as e:
                progress_bar.write(f"Error downloading {song_id}: {str(e)}")
                # Clean up partial downloads
                if zip_path.exists():
                    zip_path.unlink()
                return False

    async def process_page(self, page: int, total_progress: tqdm) -> List[bool]:
        """Process a single page of ranked maps and return download results.
        
        Returns:
            List[bool]: List of download success flags
        """
        try:
            data = await self.fetch_ranked_maps(page)
            songs = data.get("docs", [])
            tasks = []
            
            download_progress = tqdm(
                total=len(songs),
                desc=f"Page {page + 1}/{self.max_pages}",
                leave=False
            )
            
            for song in songs:
                song_id = song["id"]
                versions = song.get("versions", [])
                
                if versions:
                    download_url = versions[0].get("downloadURL")
                    if download_url:
                        task = asyncio.create_task(
                            self.download_map(song_id, download_url, download_progress)
                        )
                        tasks.append(task)
            
            results = await asyncio.gather(*tasks) if tasks else []
            total_progress.update(1)
            return results
                        
        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")
            return []

    async def download_all(self) -> List[bool]:
        """Download all ranked maps up to max_pages.
        
        Returns:
            List[bool]: List of download success flags
        """
        self.setup_directories()
        
        total_progress = tqdm(total=self.max_pages, desc="Processing pages")
        
        all_results = []
        for page in range(self.max_pages):
            results = await self.process_page(page, total_progress)
            all_results.extend(results)
        
        return all_results

async def main():
    parser = argparse.ArgumentParser(description="Download ranked Beat Saber maps")
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to download (default: 1)"
    )
    args = parser.parse_args()
    
    downloader = BeatSaverDownloader(max_pages=args.pages)
    await downloader.download_all()

if __name__ == "__main__":
    asyncio.run(main())
