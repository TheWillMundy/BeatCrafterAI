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
        self.download_path.mkdir(exist_ok=True)
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        
    async def fetch_ranked_maps(self, page: int = 0) -> Dict[str, Any]:
        """Fetch a page of ranked maps from BeatSaver API."""
        url = f"{BASE_API_URL}/{page}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=PARAMS)
            response.raise_for_status()
            return response.json()

    async def download_map(self, song_id: str, download_url: str, progress_bar: tqdm) -> None:
        """Download a single map ZIP file."""
        zip_path = self.download_path / f"{song_id}.zip"
        
        if zip_path.exists():
            progress_bar.write(f"Skipping {song_id}, already downloaded")
            progress_bar.update(1)
            return
            
        async with self.semaphore:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(download_url)
                    response.raise_for_status()
                    
                    zip_path.write_bytes(response.content)
                    progress_bar.update(1)
            except Exception as e:
                progress_bar.write(f"Error downloading {song_id}: {str(e)}")

    async def process_page(self, page: int, total_progress: tqdm) -> List[asyncio.Task]:
        """Process a single page of ranked maps and return download tasks."""
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
            
            total_progress.update(1)
            return tasks
                        
        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")
            return []

    async def download_all(self):
        """Download all ranked maps up to max_pages."""
        total_progress = tqdm(total=self.max_pages, desc="Processing pages")
        
        all_tasks = []
        for page in range(self.max_pages):
            tasks = await self.process_page(page, total_progress)
            all_tasks.extend(tasks)
        
        if all_tasks:
            await asyncio.gather(*all_tasks)

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
