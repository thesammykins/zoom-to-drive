"""
Pytest configuration and shared fixtures for Zoom to Drive tests.
"""
import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Set test environment variables before importing settings
os.environ['ZOOM_CLIENT_ID'] = 'test_client_id'
os.environ['ZOOM_CLIENT_SECRET'] = 'test_client_secret'
os.environ['ZOOM_ACCOUNT_ID'] = 'test_account_id'
os.environ['RCLONE_REMOTE_NAME'] = 'test_remote'
os.environ['RCLONE_BASE_PATH'] = 'Test/Path'
os.environ['SLACK_WEBHOOK_URL'] = 'https://hooks.slack.com/test/webhook'
os.environ['DEBUG'] = '1'


@pytest.fixture
def mock_zoom_user():
    """Mock Zoom user data."""
    return {
        'id': 'user123',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'type': 2
    }


@pytest.fixture
def mock_zoom_recording():
    """Mock Zoom recording data."""
    return {
        'uuid': 'recording123',
        'id': 123456,
        'topic': 'Weekly Sync Meeting',
        'start_time': '2024-01-15T10:00:00Z',
        'duration': 45,
        'recording_count': 2,
        'recording_files': [
            {
                'id': 'file1',
                'recording_type': 'shared_screen_with_speaker_view',
                'download_url': 'https://zoom.us/rec/download/file1',
                'file_size': 104857600,  # 100MB
                'recording_start': '2024-01-15T10:00:00Z',
                'recording_end': '2024-01-15T10:45:00Z'
            },
            {
                'id': 'file2',
                'recording_type': 'audio_only',
                'download_url': 'https://zoom.us/rec/download/file2',
                'file_size': 10485760,  # 10MB
                'recording_start': '2024-01-15T10:00:00Z',
                'recording_end': '2024-01-15T10:45:00Z'
            }
        ]
    }


@pytest.fixture
def mock_zoom_recordings_response(mock_zoom_recording):
    """Mock Zoom API recordings list response."""
    return {
        'meetings': [mock_zoom_recording],
        'page_count': 1,
        'page_size': 30,
        'total_records': 1
    }


@pytest.fixture
def mock_oauth_token_response():
    """Mock Zoom OAuth token response."""
    return {
        'access_token': 'test_access_token_123',
        'token_type': 'bearer',
        'expires_in': 3600,
        'scope': 'recording:read:admin user:read:admin'
    }


@pytest.fixture
def mock_rclone_listremotes():
    """Mock rclone listremotes output."""
    return "test_remote:\ndrive:\nbackup:\n"


@pytest.fixture
def mock_rclone_lsjson_response():
    """Mock rclone lsjson response with file metadata."""
    return [
        {
            'Path': 'test_file.mp4',
            'Name': 'test_file.mp4',
            'Size': 104857600,
            'MimeType': 'video/mp4',
            'ModTime': '2024-01-15T10:00:00Z',
            'IsDir': False,
            'ID': 'drive_file_id_12345'
        }
    ]


@pytest.fixture
def mock_slack_response():
    """Mock successful Slack webhook response."""
    response = Mock()
    response.status_code = 200
    response.text = 'ok'
    return response


@pytest.fixture
def temp_download_dir(tmp_path):
    """Create temporary download directory."""
    download_dir = tmp_path / "downloads" / "2024-01-15"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


@pytest.fixture
def sample_downloaded_file(temp_download_dir):
    """Create a sample downloaded file."""
    file_path = temp_download_dir / "test_recording.mp4"
    file_path.write_bytes(b"fake video content")
    return {
        'name': 'test_recording.mp4',
        'path': file_path,
        'date_folder': '2024-01-15',
        'recording_time': datetime(2024, 1, 15, 10, 0, 0),
        'file_size': len(b"fake video content")
    }


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration between tests."""
    import logging
    # Clear all handlers from the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    yield
    # Clean up after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
