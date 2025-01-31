import logging
import json
from datetime import datetime
from pathlib import Path

import pytz
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm

from zoom_manager.config.settings import (
    GOOGLE_SERVICE_ACCOUNT_KEY,
    GOOGLE_TARGET_FOLDER_ID,
    GOOGLE_SHARED_DRIVE_ID
)

class GoogleDriveClient:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self):
        """Initialize the GoogleDriveClient and authenticate."""
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.credentials = None
        self.folder_cache = {}
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive using a service account key"""
        try:
            service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_KEY)
            creds = Credentials.from_service_account_info(service_account_info, scopes=self.SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            self.credentials = creds
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def get_or_create_folder(self, folder_name, parent_id=None):
        """Get existing folder or create new one in Google Drive."""
        cache_key = f"{parent_id or 'root'}:{folder_name}"
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key]

        try:
            # Search for existing folder
            query = [
                "mimeType = 'application/vnd.google-apps.folder'",
                f"name = '{folder_name}'",
                "trashed = false"
            ]
            if parent_id:
                query.append(f"'{parent_id}' in parents")
            
            results = self.service.files().list(
                q=" and ".join(query),
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                driveId=GOOGLE_SHARED_DRIVE_ID,
                corpora='drive'
            ).execute()

            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                self.folder_cache[cache_key] = folder_id
                return folder_id

            # Create new folder if it doesn't exist
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id] if parent_id else [GOOGLE_TARGET_FOLDER_ID],
                'driveId': GOOGLE_SHARED_DRIVE_ID
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()

            folder_id = folder.get('id')
            self.folder_cache[cache_key] = folder_id
            return folder_id

        except Exception as e:
            self.logger.error(f"Failed to get or create folder {folder_name}: {str(e)}")
            raise

    def upload_file(self, file_dict):
        """Upload a file to Google Drive with proper folder structure."""
        try:
            self.logger.debug(f"Uploading file_dict: {file_dict}")  # Added logging

            # Create date folder under the target folder
            date_folder_id = self.get_or_create_folder(file_dict['date_folder'], GOOGLE_TARGET_FOLDER_ID)

            # Convert recording time to RFC 3339 format for Google Drive
            recording_time = datetime.strptime(file_dict['recording_time'], "%Y-%m-%dT%H:%M:%SZ")
            recording_time = recording_time.replace(tzinfo=pytz.UTC)
            modified_time = recording_time.isoformat()

            file_metadata = {
                'name': file_dict['name'],
                'parents': [date_folder_id],
                'driveId': GOOGLE_SHARED_DRIVE_ID,
                'modifiedTime': modified_time
            }

            media = MediaFileUpload(
                str(file_dict['path']),
                resumable=True,
                chunksize=1024*1024
            )

            file_size = file_dict['file_size']
            
            self.logger.info(f"Uploading {file_dict['name']} to folder {file_dict['date_folder']}")
            
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {file_dict['name']}") as pbar:
                request = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, modifiedTime',
                    supportsAllDrives=True
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        pbar.update(status.resumable_progress - pbar.n)

            # Update the file's modified time in case it wasn't set during creation
            try:
                self.service.files().update(
                    fileId=response.get('id'),
                    body={'modifiedTime': modified_time},
                    supportsAllDrives=True
                ).execute()
            except Exception as e:
                self.logger.warning(f"Could not update modified time: {str(e)}")

            self.logger.info(f"Successfully uploaded {file_dict['name']} (ID: {response.get('id')})")
            return response.get('id')

        except Exception as e:
            self.logger.error(f"Failed to upload file: {str(e)}")
            raise

    def check_file_exists(self, file_name, folder_id):
        """Check if a file already exists in the specified folder."""
        try:
            query = [
                f"name = '{file_name}'",
                f"'{folder_id}' in parents",
                "trashed = false"
            ]
            
            results = self.service.files().list(
                q=" and ".join(query),
                spaces='drive',
                fields='files(id, name, modifiedTime)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                driveId=GOOGLE_SHARED_DRIVE_ID,
                corpora='drive'
            ).execute()

            files = results.get('files', [])
            return files[0]['id'] if files else None

        except Exception as e:
            self.logger.error(f"Failed to check file existence: {str(e)}")
            return None
