"""
Main entry point for the Zoom recording manager.
Handles command line interface, orchestrates the downloading of Zoom recordings,
uploading to Google Drive, and sending Slack notifications.
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Update imports to absolute paths
from zoom_manager.config.settings import (
    LOG_FILE,
    LOG_LEVEL,
    DEBUG,
    FILE_FORMATTER,
    CONSOLE_FORMATTER,
    DOWNLOAD_DIR,
)
from zoom_manager.src.zoom_client import ZoomClient
from zoom_manager.src.rclone_client import RcloneClient
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
    parser = argparse.ArgumentParser(description='Zoom Recording Manager')
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
    return args

def main():
    """
    Main execution flow:
    1. Set up logging and parse arguments
    2. Initialize API clients (Zoom, Google Drive, Slack)
    3. Look up Zoom user and fetch recordings
    4. Download matching recordings (if longer than 5 minutes)
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
        rclone = RcloneClient()
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
            
            # Check recording duration using API start_time and recording end timestamps
            meta_duration = recording.get('duration', 0)
            actual_duration = zoom.get_actual_duration(recording)
            duration = max(meta_duration, actual_duration)
            logger.debug(
                f"Recording '{recording['topic']}' durations – metadata: {meta_duration}min, actual: {actual_duration:.1f}min"
            )
            if duration < 5:
                logger.info(
                    f"Skipping recording '{recording['topic']}' – duration ({duration:.1f} minutes) is below threshold"
                )
                continue
            
            try:
                # Download files
                downloaded_files = zoom.process_recording(recording, target_recording_name)
                
                if not downloaded_files:
                    logger.warning(f"No files were downloaded for recording: {recording['topic']}")
                    continue

                # Batch upload entire directory via rclone
                local_dir = downloaded_files[0]['path'].parent
                date_folder = downloaded_files[0]['date_folder']
                remote_dir = rclone.upload_directory(local_dir, date_folder)
                logger.info(f"Successfully uploaded all files to {remote_dir}")

                # Send Slack notifications for .mp4 recordings
                for file_dict in downloaded_files:
                    if file_dict['name'].endswith('.mp4'):
                        try:
                            drive_file_id = rclone.get_file_id(
                                file_dict['date_folder'], file_dict['name']
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to retrieve Drive file ID for {file_dict['name']}: {e}"
                            )
                            drive_file_id = None

                        slack.send_notification(
                            recording_name=recording['topic'],
                            file_name=file_dict['name'],
                            file_id=drive_file_id or f"{remote_dir}/{file_dict['name']}"
                        )

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
