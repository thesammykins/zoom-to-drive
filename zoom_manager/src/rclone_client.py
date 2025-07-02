"""
Rclone client for managing file uploads to Google Shared Drive.
Replaces Google Drive API with rclone for more efficient file transfers.
Uses the 'recordingdrive' remote configured for Google Shared Drive.
"""
import logging
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime
import pytz

from zoom_manager.config import settings
from zoom_manager.config.settings import RCLONE_REMOTE_NAME, RCLONE_BASE_PATH


class RcloneClient:
    """
    Client for interacting with rclone to upload files to Google Drive.
    Handles directory structure creation and file uploads using rclone.
    Uses the 'recordingdrive' remote configured for Google Shared Drive.
    """
    
    def __init__(self, remote_name=None, base_path=None):
        """
        Initialize the rclone client.
        
        Args:
            remote_name (str): Name of the rclone remote (defaults to settings.RCLONE_REMOTE_NAME)
            base_path (str): Base path for recordings (defaults to settings.RCLONE_BASE_PATH)
        """
        self.logger = logging.getLogger(__name__)
        self.remote_name = remote_name or RCLONE_REMOTE_NAME
        self.base_path = base_path or RCLONE_BASE_PATH
        self.rclone_executable = None
        self._check_rclone_availability()
    
    def _check_rclone_availability(self):
        """
        Check if rclone is available and properly configured.
        
        Raises:
            RuntimeError: If rclone is not available or remote is not configured
        """
        try:
            # Check if rclone is installed
            self.rclone_executable = shutil.which("rclone")
            if not self.rclone_executable:
                raise RuntimeError("rclone is not installed or not in PATH")
            
            # Check if the remote is configured
            result = subprocess.run(
                [self.rclone_executable, "listremotes"],
                capture_output=True,
                text=True,
                check=True
            )
            
            configured_remotes = [line.strip().rstrip(':') for line in result.stdout.strip().split('\n') if line.strip()]
            
            if self.remote_name not in configured_remotes:
                raise RuntimeError(f"rclone remote '{self.remote_name}' is not configured. "
                                   f"Available remotes: {', '.join(configured_remotes)}")
            
            self.logger.info(f"rclone is available and remote '{self.remote_name}' is configured")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to check rclone configuration: {e}")
            raise RuntimeError(f"rclone configuration check failed: {e}")
        except Exception as e:
            self.logger.error(f"Error checking rclone availability: {e}")
            raise
    
    def _create_remote_directory(self, remote_path):
        """
        Create directory structure on the remote if it doesn't exist.
        
        Args:
            remote_path (str): Full remote path including remote name
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            # Use rclone mkdir to create the directory
            result = subprocess.run(
                [self.rclone_executable, "mkdir", remote_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.debug(f"Created/verified remote directory: {remote_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            # rclone mkdir doesn't fail if directory already exists
            self.logger.warning(f"Directory creation command returned non-zero exit code: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create remote directory {remote_path}: {e}")
            return False
    
    def upload_file(self, file_dict):
        """
        Upload file to Google Drive using rclone.
        Creates the necessary directory structure and uploads the file.
        
        Args:
            file_dict (dict): File information containing:
                - name: File name
                - path: Local file path
                - date_folder: Target folder name (e.g., "2024-06-20")
                - recording_time: Original recording timestamp
                - file_size: Size in bytes
                
        Returns:
            str: Success message or file path
            
        Raises:
            Exception: If upload fails
        """
        try:
            self.logger.debug(f"Uploading file_dict: {file_dict}")
            
            # Build the remote path following the structure:
            # recordingdrive:"FOLDER/SUBFOLDER/YYYY-MM-DD/"
            date_folder = file_dict['date_folder']
            
            # Construct the full remote directory path
            remote_dir = f"{self.remote_name}:{self.base_path}/{date_folder}"
            
            # Create the directory structure if it doesn't exist
            self.logger.info(f"Creating remote directory: {remote_dir}")
            self._create_remote_directory(remote_dir)
            
            # Prepare the source file path
            source_file = str(file_dict['path'])
            
            # Construct the destination path (not directly used in copy cmd)
            destination = f"{self.remote_name}:{self.base_path}/{date_folder}/{file_dict['name']}"
            
            self.logger.info(f"Uploading {file_dict['name']} to {self.base_path}/{date_folder}/")
            
            # Use rclone copy command with progress output
            rclone_cmd = [
                self.rclone_executable,
                "copy",
                source_file,
                remote_dir,
                "--progress",
                "--stats-one-line",
                "--stats=1s",
            ]
            
            # Add debug output if in debug mode
            if settings.DEBUG:
                rclone_cmd.extend(["--verbose", "--log-level", "DEBUG"])
            
            # Execute the rclone copy command
            subprocess.run(
                rclone_cmd,
                check=True
            )

            self.logger.info(f"Successfully uploaded {file_dict['name']}")

            return f"{self.base_path}/{date_folder}/{file_dict['name']}"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"rclone copy failed: {e}"
            if e.stderr:
                error_msg += f" - stderr: {e.stderr}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            self.logger.error(f"Failed to upload file: {str(e)}")
            raise

    def upload_directory(self, local_path, date_folder):
        """
        Upload all files from a local folder to the remote date_folder in one rclone copy.

        Args:
            local_path (str or Path): Local directory containing files to upload
            date_folder (str): Date folder name on remote (e.g., "2024-06-20")

        Returns:
            str: Relative remote path where files were uploaded (base_path/date_folder)
        """
        remote_dir = f"{self.remote_name}:{self.base_path}/{date_folder}"
        self.logger.info(f"Creating/validating remote directory: {remote_dir}")
        self._create_remote_directory(remote_dir)

        cmd = [
            self.rclone_executable,
            "copy",
            str(local_path),
            remote_dir,
            "--progress",
            "--stats-one-line",
            "--stats=1s",
            "--checksum"  # verify file integrity and skip unchanged
        ]
        if settings.DEBUG:
            cmd.extend(["--verbose", "--log-level", "DEBUG"])

        self.logger.info(f"Uploading directory {local_path} to {remote_dir}")
        subprocess.run(cmd, check=True)
        return f"{self.base_path}/{date_folder}"

    def check_file_exists(self, file_name, date_folder):
        """
        Check if file already exists in the specified remote directory.
        
        Args:
            file_name (str): Name of file to check
            date_folder (str): Date folder name (e.g., "2024-06-20")
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            remote_path = f"{self.remote_name}:{self.base_path}/{date_folder}/{file_name}"
            
            # Use rclone lsf to check if the specific file exists
            result = subprocess.run(
                [self.rclone_executable, "lsf", remote_path],
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # If the command succeeds and returns output, the file exists
            exists = result.returncode == 0 and result.stdout.strip()
            
            if exists:
                self.logger.info(f"File {file_name} already exists in {date_folder}")
            else:
                self.logger.debug(f"File {file_name} does not exist in {date_folder}")
            
            return bool(exists)
            
        except Exception as e:
            self.logger.error(f"Failed to check file existence: {str(e)}")
            return False
    
    def get_file_id(self, date_folder: str, file_name: str) -> str:
        """
        Retrieve the Google Drive file ID for the specified file in the remote directory.
        Uses rclone lsjson to fetch metadata and extract the file ID.
        """
        remote_path = f"{self.remote_name}:{self.base_path}/{date_folder}/{file_name}"
        try:
            result = subprocess.run(
                [self.rclone_executable, "lsjson", remote_path],
                capture_output=True,
                text=True,
                check=True
            )
            entries = json.loads(result.stdout)
            if not entries:
                raise ValueError(f"No metadata found for file '{file_name}' in '{date_folder}'")
            meta = entries[0]
            
            file_id = meta.get("ID") or meta.get("Id") or meta.get("id")
            if not file_id:
                
                for key, val in meta.items():
                    if 'id' in key.lower():
                        file_id = val
                        break
            if not file_id:
                raise ValueError(f"File ID not found in metadata keys: {list(meta.keys())}")
            return file_id
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to retrieve metadata via rclone: {e.stderr or e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse rclone metadata JSON: {e}")
    
    def get_remote_info(self):
        """
        Get information about the configured rclone remote.
        
        Returns:
            dict: Remote configuration information
        """
        try:
            # Get remote configuration
            result = subprocess.run(
                [self.rclone_executable, "config", "show", self.remote_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            config_info = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line and not line.startswith('['):
                    key, value = line.split('=', 1)
                    config_info[key.strip()] = value.strip()
            
            return config_info
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get remote info: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error getting remote info: {str(e)}")
            return {}
    
    def test_connection(self):
        """
        Test the connection to the rclone remote.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to list the root of the remote
            result = subprocess.run(
                [self.rclone_executable, "lsd", f"{self.remote_name}:"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 30 second timeout
            )
            
            self.logger.info(f"Successfully connected to remote '{self.remote_name}'")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to connect to remote '{self.remote_name}': {e}")
            if e.stderr:
                self.logger.error(f"rclone error: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f"Connection test to remote '{self.remote_name}' timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error testing connection: {str(e)}")
            return False
