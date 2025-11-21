#!/usr/bin/env python3
"""
TikTok Slideshow Analyzer
Downloads slideshow images from TikTok JSON data and organizes them for Google Drive upload.
"""

import json
import os
import csv
import requests
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time


class TikTokSlideshowAnalyzer:
    def __init__(self, json_file: str, output_dir: str = "output"):
        """
        Initialize the TikTok Slideshow Analyzer.

        Args:
            json_file: Path to the JSON file containing TikTok data
            output_dir: Directory where images and metadata will be saved
        """
        self.json_file = json_file
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.metadata_dir = self.output_dir / "metadata"

        # Create output directories
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def load_json_data(self) -> List[Dict[str, Any]]:
        """Load and parse the JSON file."""
        print(f"Loading JSON data from {self.json_file}...")
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} entries")
        return data

    def filter_slideshows(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for entries that are slideshows and don't have errors."""
        slideshows = [
            entry for entry in data
            if entry.get('isSlideshow') and 'error' not in entry
        ]
        print(f"Found {len(slideshows)} slideshow posts")
        return slideshows

    def download_image(self, url: str, filepath: Path, max_retries: int = 3) -> bool:
        """
        Download an image from a URL with retry logic.

        Args:
            url: Image URL to download
            filepath: Local filepath to save the image
            max_retries: Maximum number of download attempts

        Returns:
            True if download successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return True
            except Exception as e:
                print(f"  Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        return False

    def download_slideshow_images(self, slideshow: Dict[str, Any]) -> List[str]:
        """
        Download all images from a slideshow post.

        Args:
            slideshow: Slideshow entry from JSON data

        Returns:
            List of local filepaths where images were saved
        """
        post_id = slideshow.get('id', 'unknown')
        author = slideshow.get('authorMeta', {}).get('name', 'unknown')

        # Create a folder for this post
        post_folder = self.images_dir / f"{author}_{post_id}"
        post_folder.mkdir(exist_ok=True)

        downloaded_files = []
        slideshow_links = slideshow.get('slideshowImageLinks', [])

        print(f"\nDownloading {len(slideshow_links)} images for post {post_id} by @{author}")

        for idx, image_data in enumerate(slideshow_links, 1):
            download_url = image_data.get('downloadLink')
            if not download_url:
                print(f"  Skipping image {idx}: No download link")
                continue

            # Extract filename from URL or create one
            filename = f"slide_{idx:02d}.jpg"
            filepath = post_folder / filename

            print(f"  Downloading image {idx}/{len(slideshow_links)}...", end=" ")

            if self.download_image(download_url, filepath):
                print("✓")
                downloaded_files.append(str(filepath))
            else:
                print("✗ Failed")

        return downloaded_files

    def extract_metadata(self, slideshow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant metadata from a slideshow post.

        Args:
            slideshow: Slideshow entry from JSON data

        Returns:
            Dictionary containing extracted metadata
        """
        author_meta = slideshow.get('authorMeta', {})
        music_meta = slideshow.get('musicMeta', {})

        metadata = {
            'post_id': slideshow.get('id'),
            'author_username': author_meta.get('name'),
            'author_nickname': author_meta.get('nickName'),
            'author_verified': author_meta.get('verified'),
            'author_followers': author_meta.get('fans'),
            'post_url': slideshow.get('webVideoUrl'),
            'post_text': slideshow.get('text', '').strip(),
            'create_time': slideshow.get('createTimeISO'),
            'location': slideshow.get('locationCreated'),
            'hashtags': ', '.join([h.get('name', '') for h in slideshow.get('hashtags', [])]),
            'music_name': music_meta.get('musicName'),
            'music_author': music_meta.get('musicAuthor'),
            'likes': slideshow.get('diggCount'),
            'shares': slideshow.get('shareCount'),
            'plays': slideshow.get('playCount'),
            'comments': slideshow.get('commentCount'),
            'collects': slideshow.get('collectCount'),
            'num_slides': len(slideshow.get('slideshowImageLinks', [])),
            'is_ad': slideshow.get('isAd'),
            'is_sponsored': slideshow.get('isSponsored'),
        }

        return metadata

    def save_metadata_csv(self, metadata_list: List[Dict[str, Any]]):
        """
        Save metadata to a CSV file.

        Args:
            metadata_list: List of metadata dictionaries
        """
        if not metadata_list:
            print("No metadata to save")
            return

        csv_path = self.metadata_dir / "slideshows_metadata.csv"

        print(f"\nSaving metadata to {csv_path}...")

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=metadata_list[0].keys())
            writer.writeheader()
            writer.writerows(metadata_list)

        print(f"✓ Saved metadata for {len(metadata_list)} slideshows")

    def save_metadata_json(self, metadata_list: List[Dict[str, Any]]):
        """
        Save metadata to a JSON file.

        Args:
            metadata_list: List of metadata dictionaries
        """
        json_path = self.metadata_dir / "slideshows_metadata.json"

        print(f"Saving metadata to {json_path}...")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved metadata for {len(metadata_list)} slideshows")

    def generate_summary(self, metadata_list: List[Dict[str, Any]]):
        """
        Generate a summary report.

        Args:
            metadata_list: List of metadata dictionaries
        """
        summary_path = self.metadata_dir / "summary.txt"

        total_posts = len(metadata_list)
        total_slides = sum(m.get('num_slides', 0) for m in metadata_list)
        total_likes = sum(m.get('likes', 0) for m in metadata_list)
        total_shares = sum(m.get('shares', 0) for m in metadata_list)
        total_plays = sum(m.get('plays', 0) for m in metadata_list)

        # Get top authors
        authors = {}
        for m in metadata_list:
            username = m.get('author_username')
            if username:
                authors[username] = authors.get(username, 0) + 1

        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]

        summary = f"""TikTok Slideshow Analysis Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overview:
- Total slideshow posts: {total_posts}
- Total slides downloaded: {total_slides}
- Total likes: {total_likes:,}
- Total shares: {total_shares:,}
- Total plays: {total_plays:,}

Top Authors (by number of slideshows):
"""

        for idx, (author, count) in enumerate(top_authors, 1):
            summary += f"{idx}. @{author}: {count} posts\n"

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"\n{summary}")
        print(f"✓ Summary saved to {summary_path}")

    def run(self):
        """Execute the complete workflow."""
        print("=" * 60)
        print("TikTok Slideshow Analyzer")
        print("=" * 60)

        # Load data
        data = self.load_json_data()

        # Filter for slideshows
        slideshows = self.filter_slideshows(data)

        if not slideshows:
            print("No slideshows found in the data.")
            return

        # Process each slideshow
        metadata_list = []

        for idx, slideshow in enumerate(slideshows, 1):
            print(f"\n[{idx}/{len(slideshows)}] Processing slideshow...")

            # Download images
            self.download_slideshow_images(slideshow)

            # Extract metadata
            metadata = self.extract_metadata(slideshow)
            metadata_list.append(metadata)

            # Small delay to be respectful to servers
            time.sleep(0.5)

        # Save metadata
        self.save_metadata_csv(metadata_list)
        self.save_metadata_json(metadata_list)

        # Generate summary
        self.generate_summary(metadata_list)

        print("\n" + "=" * 60)
        print("✓ Analysis complete!")
        print(f"Output saved to: {self.output_dir.absolute()}")
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze TikTok slideshow posts and download images'
    )
    parser.add_argument(
        'json_file',
        help='Path to JSON file containing TikTok data'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='Output directory (default: output)'
    )

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.json_file):
        print(f"Error: File '{args.json_file}' not found")
        return 1

    # Run analyzer
    analyzer = TikTokSlideshowAnalyzer(args.json_file, args.output)
    analyzer.run()

    return 0


if __name__ == '__main__':
    exit(main())
