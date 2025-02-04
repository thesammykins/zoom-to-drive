"""
Main entry point for the Zoom recording manager.
Handles command line interface, orchestrates the downloading of Zoom recordings,
uploading to Google Drive, and sending Slack notifications.
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Global configuration IDs for Google Drive
GOOGLE_TARGET_FOLDER_ID = None 
GOOGLE_SHARED_DRIVE_ID = None

# Update imports to absolute paths
from zoom_manager.config.settings import (
    LOG_FILE,
    LOG_LEVEL,
    DEBUG,
    FILE_FORMATTER,
    CONSOLE_FORMATTER,
    DOWNLOAD_DIR,
    GOOGLE_TARGET_FOLDER_ID as ENV_TARGET_FOLDER_ID,
    GOOGLE_SHARED_DRIVE_ID as ENV_SHARED_DRIVE_ID
)
from zoom_manager.src.zoom_client import ZoomClient
from zoom_manager.src.google_drive_client import GoogleDriveClient
from zoom_manager.src.slack_client import SlackClient

def setup_logging():
    """
    Configure application-wide logging with both file and console outputs.
    File logging always uses debug level, while console logging format depends on DEBUG setting.
    
    Returns:
        logging.Logger: Configured root logger
    """
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler - always use debug format
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(FILE_FORMATTER)
    logger.addHandler(file_handler)

    # Console handler - use simple format unless in debug mode
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CONSOLE_FORMATTER)
    logger.addHandler(console_handler)

    return logger

def cleanup_downloads(folder_path: Path):
    """
    Remove downloaded files and empty directories after successful upload.
    
    Args:
        folder_path (Path): Path to the folder containing downloaded files
        
    Note:
        Errors during cleanup are logged but don't interrupt the main process
    """
    try:
        if (folder_path.exists()):
            for file_path in folder_path.glob('**/*'):
                if file_path.is_file():
                    file_path.unlink()
            
            # Remove empty directories
            for dir_path in reversed(list(folder_path.glob('**/*'))):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
            
            if folder_path.exists() and not any(folder_path.iterdir()):
                folder_path.rmdir()
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during cleanup: {str(e)}")

def parse_args():
    """
    Parse and validate command line arguments.
    Combines environment variables with CLI arguments, with CLI taking precedence.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    global GOOGLE_TARGET_FOLDER_ID, GOOGLE_SHARED_DRIVE_ID
    
    # Initialize with environment values
    GOOGLE_TARGET_FOLDER_ID = ENV_TARGET_FOLDER_ID
    GOOGLE_SHARED_DRIVE_ID = ENV_SHARED_DRIVE_ID
    
    parser = argparse.ArgumentParser(description='Zoom Recording Manager')
    parser.add_argument('--drive-id', 
                       help='Google Drive folder ID',
                       default=GOOGLE_TARGET_FOLDER_ID)
    parser.add_argument('--shared-id',
                       help='Google Shared Drive ID', 
                       default=GOOGLE_SHARED_DRIVE_ID)
    parser.add_argument(
        '--name',
        required=True,
        help="Name of the target recording"
    )
    parser.add_argument(
        '--email',
        required=True,
        help="Email of the target Zoom user"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help="Number of days to search for recordings (default: 7)"
    )
    
    args = parser.parse_args()
    
    # Override with CLI args if provided
    if args.drive_id:
        GOOGLE_TARGET_FOLDER_ID = args.drive_id
    if args.shared_id:
        GOOGLE_SHARED_DRIVE_ID = args.shared_id
        
    return args

def main():
    """
    Main execution flow:
    1. Set up logging and parse arguments
    2. Initialize API clients (Zoom, Google Drive, Slack)
    3. Look up Zoom user and fetch recordings
    4. Download matching recordings
    5. Upload to Google Drive
    6. Send Slack notifications
    7. Clean up downloaded files
    """
    logger = setup_logging()

    # Parse command-line arguments
    args = parse_args()

    target_recording_name = args.name
    target_user_email = args.email
    days_to_search = args.days

    logger.info(f"Starting Zoom recording manager (searching last {days_to_search} days)")

    try:
        # Initialize clients
        zoom = ZoomClient()
        gdrive = GoogleDriveClient()
        slack = SlackClient()

        # Look up user by email
        try:
            user_info = zoom.get_user_by_email(target_user_email)
            user_id = user_info['id']
            logger.info(f"Found user: {user_info.get('first_name')} {user_info.get('last_name')} (ID: {user_id})")
        except ValueError as e:
            logger.error(f"User lookup failed: {str(e)}")
            return
        except Exception as e:
            logger.error(f"Error during user lookup: {str(e)}")
            return

        # Set date range based on days_to_search
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_to_search)

        # Get recordings for the specific user
        recordings = zoom.get_recordings(user_id, start_date, end_date)
        
        # Filter recordings by name
        target_recordings = [
            rec for rec in recordings.get('meetings', [])
            if target_recording_name.lower() in rec.get('topic', '').lower()
        ]

        if not target_recordings:
            logger.info(f"No recordings found matching '{target_recording_name}' in the last {days_to_search} days")
            return

        # Process each recording
        for recording in target_recordings:
            logger.info(f"Processing recording: {recording['topic']}")
            
            try:
                # Download files
                downloaded_files = zoom.process_recording(recording, target_recording_name)
                
                if not downloaded_files:
                    logger.warning(f"No files were downloaded for recording: {recording['topic']}")
                    continue

                # Upload files to Google Drive
                for file_dict in downloaded_files:
                    try:
                        file_id = gdrive.upload_file(file_dict)
                        logger.info(f"Successfully uploaded {file_dict['name']} (ID: {file_id})")
                        
                        # Send Slack notification only for .mp4 files
                        if file_dict['name'].endswith('.mp4'):
                            slack.send_notification(
                                recording_name=recording['topic'],
                                file_name=file_dict['name'],
                                file_id=file_id
                            )
                    except Exception as upload_error:
                        logger.error(f"Failed to upload {file_dict['name']}: {str(upload_error)}")
                        continue

                # Clean up downloaded files after successful upload
                if downloaded_files:
                    cleanup_downloads(downloaded_files[0]['path'].parent)
                    logger.info(f"Cleaned up downloaded files for {recording['topic']}")

            except Exception as proc_error:
                logger.error(f"Error processing recording {recording['topic']}: {str(proc_error)}")
                continue

        logger.info("Finished processing all recordings")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
