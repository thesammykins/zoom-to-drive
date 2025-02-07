"""
Google Drive client for managing file uploads and folder structure.
Handles authentication, folder creation, and file uploads with progress tracking.
"""

import logging
import json
from datetime import datetime
from pathlib import Path

import pytz
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm

from zoom_manager.config import settings
from zoom_manager.config.settings import (
    GOOGLE_SERVICE_ACCOUNT_KEY,
    GOOGLE_TARGET_FOLDER_ID,
    GOOGLE_SHARED_DRIVE_ID
)

class GoogleDriveClient:
    """
    Client for interacting with Google Drive API.
    Handles folder management and file uploads with proper metadata.
    Uses service account authentication and supports shared drives.
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self):
        """
        Initialize the client with authentication and logging setup.
        Raises:
            Exception: If authentication fails
        """
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.credentials = None
        self.folder_cache = {}
        self._authenticate()

    def _authenticate(self):
        """Set up Google Drive API authentication using either OAuth or Service Account."""
        try:
            if settings.GOOGLE_AUTH_TYPE == 'oauth':
                self._authenticate_oauth()
            else:
                self._authenticate_service_account()
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def _authenticate_oauth(self):
        """Authenticate using OAuth 2.0 credentials"""
        try:
            creds = None
            token_path = settings.CREDENTIALS_DIR / 'token.json'

            # Load existing token if available
            if token_path.exists():
                creds = OAuthCredentials.from_authorized_user_file(str(token_path), self.SCOPES)

            # If no valid credentials, run OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    client_config = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_KEY)
                    flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save token
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('drive', 'v3', credentials=creds)
            self.credentials = creds

        except Exception as e:
            self.logger.error(f"OAuth authentication failed: {str(e)}")
            raise

    def _authenticate_service_account(self):
        """Authenticate using Service Account credentials"""
        try:
            service_account_info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_KEY)
            creds = ServiceAccountCredentials.from_service_account_info(
                service_account_info, 
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=creds)
            self.credentials = creds
        except Exception as e:
            self.logger.error(f"Service account authentication failed: {str(e)}")
            raise

    def get_or_create_folder(self, folder_name, parent_id=None):
        """
        Retrieve existing folder or create new one in Google Drive.
        Uses caching to minimize API calls for repeated folder lookups.
        
        Args:
            folder_name (str): Name of the folder to find or create
            parent_id (str, optional): ID of parent folder. Uses target folder if None
            
        Returns:
            str: ID of the found or created folder
            
        Raises:
            Exception: If folder operations fail
        """
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
        """
        Upload file to Google Drive with metadata and progress tracking.
        Creates necessary folder structure and preserves recording timestamps.
        
        Args:
            file_dict (dict): File information containing:
                - name: File name
                - path: Local file path
                - date_folder: Target folder name
                - recording_time: Original recording timestamp
                - file_size: Size in bytes
                
        Returns:
            str: ID of the uploaded file
            
        Raises:
            Exception: If upload fails
        """
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
        """
        Check if file already exists in specified Google Drive folder.
        
        Args:
            file_name (str): Name of file to check
            folder_id (str): ID of folder to search in
            
        Returns:
            str: File ID if exists, None otherwise
            
        Note:
            Only checks non-trashed files in specified folder
        """
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
