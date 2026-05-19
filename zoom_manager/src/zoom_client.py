import logging
import json
import re
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
)
from zoom_manager.config import settings


REQUEST_TIMEOUT = (10, 60)
DOWNLOAD_TIMEOUT = (10, 300)
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

class ZoomClient:
    """
    A client for interacting with the Zoom API to manage recordings.
    Handles authentication, user lookup, and recording downloads.
    """

    FILE_TYPE_EXTENSION_MAP = {
        'shared_screen_with_speaker_view(cc)': '.mp4',
        'shared_screen_with_speaker_view': '.mp4',
        'audio_only': '.m4a',
        'video_only(m4s)': '.m4s',
        'closed_caption': '.vtt',
        'chat_file': '.txt'
        # Add other mappings as needed
    }

    def __init__(self):
        """Initialize the ZoomClient with logging and token management."""
        self.logger = logging.getLogger(__name__)
        self.access_token = None
        self.token_expires_at = None
        
    def _get_access_token(self):
        """
        Retrieve or refresh OAuth 2.0 access token for Zoom API authentication.
        Returns cached token if valid, otherwise requests new token.
        """
        if self.access_token and datetime.now() < self.token_expires_at:
            return self.access_token

        url = "https://zoom.us/oauth/token"
        auth = (ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
        data = {
            "grant_type": "account_credentials",
            "account_id": ZOOM_ACCOUNT_ID
        }

        try:
            response = requests.post(url, auth=auth, data=data, timeout=REQUEST_TIMEOUT)
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
        """
        Construct HTTP headers with current access token for API requests.
        Returns dict with Authorization and Content-Type headers.
        """
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }

    def _convert_to_melbourne_time(self, utc_time_str):
        """
        Convert an ISO8601 UTC timestamp to Melbourne timezone.

        Handles strings ending with 'Z' or with timezone offsets, with or without fractional seconds.
        """
        # Normalize 'Z' suffix to '+00:00' for fromisoformat
        iso_ts = utc_time_str
        if utc_time_str.endswith('Z'):
            iso_ts = utc_time_str[:-1] + '+00:00'
        # Parse ISO8601 timestamp
        dt = datetime.fromisoformat(iso_ts)
        # Ensure UTC tzinfo if none
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        # Convert to Melbourne timezone
        mel_tz = pytz.timezone('Australia/Melbourne')
        return dt.astimezone(mel_tz)

    def get_user_by_email(self, email: str):
        """
        Retrieve Zoom user details using their email address.
        Args:
            email (str): User's email address
        Returns:
            dict: User information from Zoom API
        Raises:
            ValueError: If user not found
            RequestException: If API request fails
        """
        try:
            self.logger.info(f"Looking up user with email: {email}")
            encoded_email = quote(email, safe="")
            url = f"{ZOOM_API_BASE_URL}/users/{encoded_email}"
            
            response = requests.get(
                url, 
                headers=self._get_headers(),
                timeout=REQUEST_TIMEOUT,
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
        """
        Fetch recording list for specified user within optional date range.
        Args:
            user_id (str): Zoom user ID
            start_date (datetime, optional): Start date for recording search
            end_date (datetime, optional): End date for recording search
        Returns:
            dict: JSON response containing recording information
        """
        url = f"{ZOOM_API_BASE_URL}/users/{user_id}/recordings"
        params = {"page_size": 300}
        
        if start_date:
            params["from"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["to"] = end_date.strftime("%Y-%m-%d")

        try:
            self.logger.info(f"Fetching recordings for user ID: {user_id}")
            self.logger.debug(f"Date range: {start_date} to {end_date}")
            
            all_meetings = []
            recordings = {}
            next_page_token = None

            while True:
                if next_page_token:
                    params["next_page_token"] = next_page_token
                else:
                    params.pop("next_page_token", None)

                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                recordings = response.json()
                all_meetings.extend(recordings.get('meetings', []))

                next_page_token = recordings.get("next_page_token")
                if not next_page_token:
                    break

            recordings["meetings"] = all_meetings
            recordings["total_records"] = max(recordings.get("total_records", 0), len(all_meetings))

            total_recordings = len(all_meetings)
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
        """
        Download recording file with progress tracking.
        Args:
            download_url (str): URL to download the recording
            output_path (Path): Destination path for downloaded file
        Returns:
            bool: True if download successful, False if skipped in DEBUG mode
        Raises:
            RuntimeError: If download is incomplete
            RequestException: If download request fails
        """
        if settings.DEBUG:
            self.logger.info(f"[DEBUG] Would download from {download_url} to {output_path}")
            return False  # Indicate that download was skipped

        try:
            response = requests.get(
                download_url,
                headers=self._get_headers(),
                stream=True,
                timeout=DOWNLOAD_TIMEOUT,
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1 Mebibyte

            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=f"Downloading {output_path.name}") as progress_bar:
                with open(output_path, 'wb') as file:
                    for data in response.iter_content(block_size):
                        if not data:
                            continue
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
        """
        Process and download all files associated with a recording.
        Handles multiple recording types (video, transcript, chat) and manages file organization.
        
        Args:
            recording_info (dict): Recording metadata from Zoom API
            meeting_name (str): Name of the meeting for file naming
        Returns:
            list: Information about downloaded files including paths and metadata
        """
        melbourne_time = self._convert_to_melbourne_time(recording_info['start_time'])
        safe_meeting_name = self._sanitize_filename_part(meeting_name, "recording")
        base_folder_name = melbourne_time.strftime("%d %B %Y - ") + safe_meeting_name
        date_folder = melbourne_time.strftime("%Y-%m-%d")  # Ensure correct date format

        folder_path = DOWNLOAD_DIR / date_folder
        folder_path.mkdir(parents=True, exist_ok=True)
        downloaded_files = []
        recording_files = recording_info.get('recording_files', [])
        
        # Debug: Log the recording files structure
        if settings.DEBUG:
            self.logger.debug(f"Recording files structure: {json.dumps(recording_files, indent=2)}")

        # Group recordings by type
        recordings_by_type = {}
        for file_info in recording_files:
            file_type = file_info.get('recording_type', '').lower()
            if file_type not in recordings_by_type:
                recordings_by_type[file_type] = []
            recordings_by_type[file_type].append(file_info)

        # Check for recordings still being processed
        processing_files = [f for f in recording_files if f.get('status') == 'processing']
        if processing_files:
            self.logger.warning(f"Found {len(processing_files)} files still being processed by Zoom. These will be skipped.")
            self.logger.info("Tip: Wait a few minutes for processing to complete, then try again.")
        
        for file_type in recordings_by_type:
            extension = self._get_file_extension(file_type)
            if not extension:
                if file_type == '':  # Empty file type usually means processing
                    processing_count = len([f for f in recordings_by_type[file_type] if f.get('status') == 'processing'])
                    if processing_count > 0:
                        self.logger.warning(f"Skipping {processing_count} files that are still being processed")
                    else:
                        self.logger.warning(f"Unknown file type: {file_type}")
                else:
                    self.logger.warning(f"Unknown file type: {file_type}")
                continue

            for index, file_info in enumerate(recordings_by_type[file_type]):
                download_url = file_info.get('download_url')
                if not download_url:
                    self.logger.warning(f"Skipping {file_type or 'unknown'} file without a download URL")
                    continue

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

        if settings.DEBUG and downloaded_files:
            self.logger.debug("Available items to download:")
            for file in downloaded_files:
                self.logger.debug(f"- {file['name']} at {file['path']}")


        return downloaded_files

    def get_actual_duration(self, recording_info: dict) -> float:
        """
        Calculate actual meeting duration in minutes from start_time and recording end timestamps.
        Fallback to metadata 'duration' if no recording end info available.
        """
        # Parse meeting start time
        try:
            start = self._convert_to_melbourne_time(recording_info.get('start_time', ''))
        except Exception:
            return recording_info.get('duration', 0)

        # Gather all recording end timestamps
        ends = []
        for f in recording_info.get('recording_files', []):
            end_ts = f.get('recording_end')
            if end_ts:
                try:
                    ends.append(self._convert_to_melbourne_time(end_ts))
                except Exception:
                    continue
        if not ends:
            return recording_info.get('duration', 0)

        # Compute duration between meeting start and last recording end
        duration_minutes = (max(ends) - start).total_seconds() / 60
        return round(duration_minutes, 1)

    def _get_file_extension(self, file_type):
        """
        Get appropriate file extension for recording type.
        Args:
            file_type (str): Recording type from Zoom API
        Returns:
            str: File extension including dot prefix, or None if type unknown
        """
        return self.FILE_TYPE_EXTENSION_MAP.get(file_type)

    def _sanitize_filename_part(self, value, fallback):
        """
        Return a safe single path component for downloaded recording file names.
        """
        sanitized = INVALID_FILENAME_CHARS.sub("_", value or "")
        sanitized = re.sub(r"\s+", " ", sanitized).strip(" ._")
        return sanitized[:180] or fallback
