#!/usr/bin/env python3
"""
Google Drive Uploader for TikTok Slideshow Analysis
Uploads the downloaded images and metadata to Google Drive.
"""

import os
import pickle
from pathlib import Path
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveUploader:
    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize Google Drive uploader.

        Args:
            credentials_file: Path to Google OAuth credentials JSON file
        """
        self.credentials_file = credentials_file
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None

        # Token file stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found.\n"
                        f"Please download it from Google Cloud Console:\n"
                        f"1. Go to https://console.cloud.google.com/\n"
                        f"2. Create a project (if you haven't already)\n"
                        f"3. Enable Google Drive API\n"
                        f"4. Create OAuth 2.0 credentials\n"
                        f"5. Download the JSON file and save as 'credentials.json'"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        print("✓ Authenticated with Google Drive")

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive.

        Args:
            folder_name: Name of the folder to create
            parent_id: ID of parent folder (None for root)

        Returns:
            ID of the created folder
        """
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = self.service.files().create(
            body=file_metadata,
            fields='id, webViewLink'
        ).execute()

        print(f"✓ Created folder: {folder_name}")
        print(f"  Link: {folder.get('webViewLink')}")

        return folder.get('id')

    def upload_file(self, filepath: Path, parent_id: Optional[str] = None) -> str:
        """
        Upload a file to Google Drive.

        Args:
            filepath: Local path to file
            parent_id: ID of parent folder (None for root)

        Returns:
            ID of the uploaded file
        """
        file_metadata = {'name': filepath.name}

        if parent_id:
            file_metadata['parents'] = [parent_id]

        # Determine MIME type based on file extension
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.txt': 'text/plain',
        }

        mime_type = mime_types.get(filepath.suffix.lower(), 'application/octet-stream')

        media = MediaFileUpload(str(filepath), mimetype=mime_type, resumable=True)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    def upload_directory(self, local_dir: Path, parent_id: Optional[str] = None) -> str:
        """
        Recursively upload a directory and its contents to Google Drive.

        Args:
            local_dir: Local directory path
            parent_id: ID of parent folder in Drive

        Returns:
            ID of the created folder
        """
        # Create folder in Drive
        folder_id = self.create_folder(local_dir.name, parent_id)

        # Upload all files and subdirectories
        items = sorted(local_dir.iterdir())
        total_items = len(items)

        for idx, item in enumerate(items, 1):
            print(f"  [{idx}/{total_items}] {item.name}...", end=" ")

            if item.is_file():
                self.upload_file(item, folder_id)
                print("✓")
            elif item.is_dir():
                print()
                self.upload_directory(item, folder_id)

        return folder_id

    def upload_analysis_results(self, output_dir: str = 'output',
                               drive_folder_name: Optional[str] = None):
        """
        Upload complete analysis results to Google Drive.

        Args:
            output_dir: Local output directory containing analysis results
            drive_folder_name: Name for the Drive folder (default: TikTok_Analysis_<timestamp>)
        """
        from datetime import datetime

        output_path = Path(output_dir)

        if not output_path.exists():
            raise FileNotFoundError(f"Output directory '{output_dir}' not found")

        # Create main folder name
        if not drive_folder_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            drive_folder_name = f"TikTok_Analysis_{timestamp}"

        print("\n" + "=" * 60)
        print(f"Uploading to Google Drive: {drive_folder_name}")
        print("=" * 60)

        # Create main folder
        main_folder_id = self.create_folder(drive_folder_name)

        # Upload images directory
        images_dir = output_path / 'images'
        if images_dir.exists():
            print("\nUploading images...")
            self.upload_directory(images_dir, main_folder_id)

        # Upload metadata directory
        metadata_dir = output_path / 'metadata'
        if metadata_dir.exists():
            print("\nUploading metadata...")
            self.upload_directory(metadata_dir, main_folder_id)

        print("\n" + "=" * 60)
        print("✓ Upload complete!")
        print("=" * 60)

        return main_folder_id


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Upload TikTok slideshow analysis results to Google Drive'
    )
    parser.add_argument(
        '-d', '--directory',
        default='output',
        help='Local output directory to upload (default: output)'
    )
    parser.add_argument(
        '-n', '--name',
        help='Name for Google Drive folder (default: TikTok_Analysis_<timestamp>)'
    )
    parser.add_argument(
        '-c', '--credentials',
        default='credentials.json',
        help='Path to Google OAuth credentials file (default: credentials.json)'
    )

    args = parser.parse_args()

    try:
        uploader = GoogleDriveUploader(args.credentials)
        uploader.upload_analysis_results(args.directory, args.name)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
