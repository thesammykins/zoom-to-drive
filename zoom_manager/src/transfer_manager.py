"""
Transfer Manager module for Zoom to Drive Recording Manager
Handles high-speed downloads and uploads with progress tracking
"""

import asyncio
import aiohttp
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

from zoom_client import ZoomClient
from google_drive_client import GoogleDriveClient
from slack_client import SlackClient

class TransferManager:
    def __init__(self, config: Dict):
        self.config = config
        self.setup_logging()
        self.setup_clients()
        
    def setup_logging(self):
        """Configure logging based on debug mode"""
        level = logging.DEBUG if self.config['debug_mode'] else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_clients(self):
        """Initialize API clients"""
        # Load and decrypt environment variables
        self.load_env()
        
        # Initialize clients
        self.zoom = ZoomClient()
        self.gdrive = GoogleDriveClient()
        self.slack = SlackClient()

    def load_env(self):
        """Load and decrypt environment variables"""
        try:
            # Get encryption key
            key_path = Path.home() / '.zoom_drive' / 'key.key'
            with open(key_path, 'rb') as f:
                key = f.read()
            
            # Decrypt env file
            env_path = Path(self.config['env_file'])
            encrypted_path = env_path.with_suffix('.env.encrypted')
            
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)
            
            # Load environment variables
            load_dotenv(stream=decrypted_data.decode().splitlines())
            
        except Exception as e:
            self.logger.error(f"Failed to load environment: {str(e)}")
            raise

    async def download_file(self, url: str, filepath: Path, session: aiohttp.ClientSession) -> bool:
        """Download a file with progress tracking"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to download {url}: {response.status}")
                    return False
                
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192  # 8KB chunks
                downloaded = 0
                
                async with aiofiles.open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(block_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        progress = int((downloaded / total_size) * 100)
                        self.progress_callback(progress)
                
                return True
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {str(e)}")
            return False

    async def upload_file(self, filepath: Path, session: aiohttp.ClientSession) -> Optional[str]:
        """Upload a file to Google Drive with progress tracking"""
        try:
            file_id = await self.gdrive.upload_file_async(filepath, self.progress_callback)
            return file_id
        except Exception as e:
            self.logger.error(f"Error uploading {filepath}: {str(e)}")
            return None

    def progress_callback(self, progress: int):
        """Callback for progress updates"""
        if hasattr(self, 'progress_signal'):
            self.progress_signal.emit(progress)

    async def process_recording(self, recording: Dict, session: aiohttp.ClientSession) -> bool:
        """Process a single recording (download and upload)"""
        try:
            # Create download directory
            download_dir = Path('downloads') / recording['topic']
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Download files
            files_to_upload = []
            for file in recording.get('recording_files', []):
                filepath = download_dir / file['recording_type']
                if await self.download_file(file['download_url'], filepath, session):
                    files_to_upload.append(filepath)
            
            # Upload files
            for filepath in files_to_upload:
                file_id = await self.upload_file(filepath, session)
                if file_id and filepath.suffix == '.mp4':
                    await self.slack.send_notification_async(
                        recording_name=recording['topic'],
                        file_name=filepath.name,
                        file_id=file_id
                    )
            
            # Cleanup if enabled
            if self.config['cleanup']:
                for filepath in files_to_upload:
                    filepath.unlink()
                download_dir.rmdir()
            
            return True
        except Exception as e:
            self.logger.error(f"Error processing recording {recording['topic']}: {str(e)}")
            return False

    async def run(self):
        """Main execution flow"""
        try:
            # Get user ID
            user_info = await self.zoom.get_user_by_email_async(self.config['user_email'])
            user_id = user_info['id']
            
            # Set date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config['days'])
            
            # Get recordings
            recordings = await self.zoom.get_recordings_async(user_id, start_date, end_date)
            
            # Filter recordings
            target_recordings = [
                rec for rec in recordings.get('meetings', [])
                if self.config['meeting_name'].lower() in rec.get('topic', '').lower()
            ]
            
            if not target_recordings:
                self.logger.info(f"No recordings found matching '{self.config['meeting_name']}'")
                return
            
            # Process recordings
            async with aiohttp.ClientSession() as session:
                for recording in target_recordings:
                    if recording.get('duration', 0) < 5:
                        self.logger.info(f"Skipping short recording: {recording['topic']}")
                        continue
                    
                    await self.process_recording(recording, session)
            
            return True
        except Exception as e:
            self.logger.error(f"Transfer failed: {str(e)}")
            raise 