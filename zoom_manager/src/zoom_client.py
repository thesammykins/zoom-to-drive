import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import pytz
import requests
from tqdm import tqdm

from zoom_manager.config.settings import (
    ZOOM_API_BASE_URL,
    ZOOM_CLIENT_ID,
    ZOOM_CLIENT_SECRET,
    ZOOM_ACCOUNT_ID,
    DOWNLOAD_DIR,
    DEBUG  # Add this line
)

class ZoomClient:
    MIN_VIDEO_SIZE_MB = 20  # Minimum size in MB for video files

    # Add or update the file type to extension mapping
    FILE_TYPE_EXTENSION_MAP = {
        'shared_screen_with_speaker_view(cc)': '.mp4',
        'audio_only': '.m4a',
        'video_only(m4s)': '.m4s',
        'closed_caption': '.vtt',
        'chat_file': 'txt'
        # Add other mappings as needed
    }

    def __init__(self):
        """Initialize the ZoomClient with logging and token placeholders."""
        self.logger = logging.getLogger(__name__)
        self.access_token = None
        self.token_expires_at = None
        
    def _get_access_token(self):
        """Get OAuth 2.0 access token from Zoom"""
        if self.access_token and datetime.now() < self.token_expires_at:
            return self.access_token

        url = "https://zoom.us/oauth/token"
        auth = (ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
        data = {
            "grant_type": "account_credentials",
            "account_id": ZOOM_ACCOUNT_ID
        }

        try:
            response = requests.post(url, auth=auth, data=data)
            response.raise_for_status()
            token_info = response.json()
            
            self.access_token = token_info["access_token"]
            self.token_expires_at = datetime.now() + timedelta(seconds=token_info["expires_in"] - 300)
            
            return self.access_token
        except requests.RequestException as e:
            self.logger.error(f"Failed to get access token: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response content: {e.response.text}")
            raise

    def _get_headers(self):
        """Get authenticated headers for API requests"""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }

    def _convert_to_melbourne_time(self, utc_time_str):
        """Convert UTC time to Melbourne time."""
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        melbourne_time = utc_time.astimezone(melbourne_tz)
        return melbourne_time

    def get_user_by_email(self, email: str):
        """Look up a Zoom user by their email address."""
        try:
            self.logger.info(f"Looking up user with email: {email}")
            encoded_email = quote(email)
            url = f"{ZOOM_API_BASE_URL}/users/{encoded_email}"
            
            response = requests.get(
                url, 
                headers=self._get_headers()
            )
            
            if response.status_code == 404:
                raise ValueError(f"User with email {email} not found")
                
            response.raise_for_status()
            user_info = response.json()
            
            self.logger.info(f"Successfully found user: {user_info.get('first_name')} {user_info.get('last_name')}")
            return user_info
            
        except requests.RequestException as e:
            error_message = str(e)
            if hasattr(e.response, 'text'):
                try:
                    error_detail = json.loads(e.response.text)
                    error_message = f"{error_message} - Details: {json.dumps(error_detail, indent=2)}"
                except json.JSONDecodeError:
                    error_message = f"{error_message} - Response: {e.response.text}"
            
            self.logger.error(f"Failed to look up user: {error_message}")
            raise

    def get_recordings(self, user_id: str, start_date=None, end_date=None):
        """Get recordings for a specific user."""
        url = f"{ZOOM_API_BASE_URL}/users/{user_id}/recordings"
        params = {}
        
        if start_date:
            params["from"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["to"] = end_date.strftime("%Y-%m-%d")

        try:
            self.logger.info(f"Fetching recordings for user ID: {user_id}")
            self.logger.debug(f"Date range: {start_date} to {end_date}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            recordings = response.json()
            
            total_recordings = len(recordings.get('meetings', []))
            self.logger.info(f"Found {total_recordings} recordings")
            return recordings
            
        except requests.RequestException as e:
            error_message = str(e)
            if hasattr(e.response, 'text'):
                try:
                    error_detail = json.loads(e.response.text)
                    error_message = f"{error_message} - Details: {json.dumps(error_detail, indent=2)}"
                except json.JSONDecodeError:
                    error_message = f"{error_message} - Response: {e.response.text}"
            
            self.logger.error(f"Failed to get recordings: {error_message}")
            raise

    def download_recording(self, download_url, output_path):
        """Download a recording file with progress bar."""
        if DEBUG:
            self.logger.info(f"[DEBUG] Would download from {download_url} to {output_path}")
            return False  # Indicate that download was skipped

        try:
            response = requests.get(
                download_url,
                headers=self._get_headers(),
                stream=True
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1 Mebibyte

            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=f"Downloading {output_path.name}") as progress_bar:
                with open(output_path, 'wb') as file:
                    for data in response.iter_content(block_size):
                        progress_bar.update(len(data))
                        file.write(data)

            if total_size != 0 and progress_bar.n != total_size:
                raise RuntimeError("Download incomplete")
                
            return True
            
        except requests.RequestException as e:
            error_message = str(e)
            if hasattr(e.response, 'text'):
                try:
                    error_details = e.response.json()
                    error_message += f" - {error_details}"
                except json.JSONDecodeError:
                    pass
            self.logger.error(f"Failed to download recording: {error_message}")
            if output_path.exists():
                output_path.unlink()
            raise
        except Exception as e:
            self.logger.error(f"Error during download: {str(e)}")
            if output_path.exists():
                output_path.unlink()
            raise

    def process_recording(self, recording_info, meeting_name):
        """Process a recording including video, transcript, and chat."""
        melbourne_time = self._convert_to_melbourne_time(recording_info['start_time'])
        base_folder_name = melbourne_time.strftime("%d %B %Y - ") + meeting_name
        date_folder = melbourne_time.strftime("%Y-%m-%d")  # Ensure correct date format

        folder_path = DOWNLOAD_DIR / date_folder
        folder_path.mkdir(parents=True, exist_ok=True)
        downloaded_files = []
        recording_files = recording_info.get('recording_files', [])

        # Group recordings by type
        recordings_by_type = {}
        for file_info in recording_files:
            file_type = file_info.get('recording_type', '').lower()
            if file_type not in recordings_by_type:
                recordings_by_type[file_type] = []
            recordings_by_type[file_type].append(file_info)

        for file_type in recordings_by_type:
            extension = self._get_file_extension(file_type)
            if not extension:
                self.logger.warning(f"Unknown file type: {file_type}")
                continue

            for index, file_info in enumerate(recordings_by_type[file_type]):
                download_url = file_info.get('download_url')
                part_suffix = f"_{index + 1}" if len(recordings_by_type[file_type]) > 1 else ""
                file_name = f"{base_folder_name}{part_suffix}{extension}"
                output_path = folder_path / file_name

                if self.download_recording(download_url, output_path):
                    downloaded_files.append({
                        'name': file_name,
                        'path': output_path,
                        'date_folder': date_folder,  # Assign the correct date_folder
                        'recording_time': recording_info['start_time'],
                        'file_size': output_path.stat().st_size
                    })

        if DEBUG and downloaded_files:
            self.logger.debug("Available items to download:")
            for file in downloaded_files:
                self.logger.debug(f"- {file['name']} at {file['path']}")

        return downloaded_files

<<<<<<< HEAD
    def _get_file_extension(self, file_type):
        """Get the file extension based on the recording type."""
        return self.FILE_TYPE_EXTENSION_MAP.get(file_type)
=======
    @staticmethod
    def _get_file_extension(file_type):
        """Get file extension based on recording type."""
        extensions = {
            'shared_screen_with_speaker_view': '.mp4',
            'shared_screen_with_gallery_view': '.mp4',
            'shared_screen': '.mp4',
            'speaker_view': '.mp4',
            'gallery_view': '.mp4',
            'audio_transcript': '.vtt',
            'chat_file': '.txt',
            'audio_only': '.m4a'
        }
        return extensions.get(file_type)
>>>>>>> 15131b2 (Prepare repository for public release)
