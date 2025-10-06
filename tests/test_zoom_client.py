"""
Unit tests for ZoomClient.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pytz

from zoom_manager.src.zoom_client import ZoomClient


@pytest.mark.unit
class TestZoomClient:
    """Test suite for ZoomClient."""

    def test_init(self):
        """Test ZoomClient initialization."""
        client = ZoomClient()
        assert client.access_token is None
        assert client.token_expires_at is None
        assert client.logger is not None

    @patch('zoom_manager.src.zoom_client.requests.post')
    def test_get_access_token_success(self, mock_post, mock_oauth_token_response):
        """Test successful OAuth token retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_oauth_token_response
        mock_post.return_value = mock_response

        client = ZoomClient()
        token = client._get_access_token()

        assert token == 'test_access_token_123'
        assert client.access_token == 'test_access_token_123'
        assert client.token_expires_at is not None
        mock_post.assert_called_once()

    @patch('zoom_manager.src.zoom_client.requests.post')
    def test_get_access_token_cached(self, mock_post, mock_oauth_token_response):
        """Test that cached token is used when still valid."""
        mock_response = Mock()
        mock_response.json.return_value = mock_oauth_token_response
        mock_post.return_value = mock_response

        client = ZoomClient()
        # Get token first time
        token1 = client._get_access_token()
        # Get token second time (should use cache)
        token2 = client._get_access_token()

        assert token1 == token2
        # Should only call the API once
        assert mock_post.call_count == 1

    @patch('zoom_manager.src.zoom_client.requests.post')
    def test_get_access_token_failure(self, mock_post):
        """Test OAuth token retrieval failure."""
        mock_post.side_effect = Exception("API Error")

        client = ZoomClient()
        with pytest.raises(Exception):
            client._get_access_token()

    def test_get_headers(self):
        """Test header construction with access token."""
        client = ZoomClient()
        client.access_token = 'test_token'
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        headers = client._get_headers()

        assert headers['Authorization'] == 'Bearer test_token'
        assert headers['Content-Type'] == 'application/json'

    def test_convert_to_melbourne_time(self):
        """Test UTC to Melbourne timezone conversion."""
        client = ZoomClient()

        # Test with Z suffix
        utc_time = '2024-01-15T00:00:00Z'
        mel_time = client._convert_to_melbourne_time(utc_time)

        assert mel_time.tzinfo.zone == 'Australia/Melbourne'
        # January is summer in Melbourne (UTC+11)
        assert mel_time.hour == 11

    @patch('zoom_manager.src.zoom_client.requests.get')
    def test_get_user_by_email_success(self, mock_get, mock_zoom_user):
        """Test successful user lookup by email."""
        mock_response = Mock()
        mock_response.json.return_value = mock_zoom_user
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = ZoomClient()
        client.access_token = 'test_token'
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        user_info = client.get_user_by_email('test@example.com')

        assert user_info == mock_zoom_user
        assert user_info['email'] == 'test@example.com'

    @patch('zoom_manager.src.zoom_client.requests.get')
    def test_get_user_by_email_not_found(self, mock_get):
        """Test user lookup when user not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = ZoomClient()
        client.access_token = 'test_token'
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        with pytest.raises(ValueError, match="not found"):
            client.get_user_by_email('nonexistent@example.com')

    @patch('zoom_manager.src.zoom_client.requests.get')
    def test_get_recordings_success(self, mock_get, mock_zoom_recordings_response):
        """Test successful recordings retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_zoom_recordings_response
        mock_get.return_value = mock_response

        client = ZoomClient()
        client.access_token = 'test_token'
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        recordings = client.get_recordings('user123', start_date, end_date)

        assert 'meetings' in recordings
        assert len(recordings['meetings']) == 1
        assert recordings['meetings'][0]['topic'] == 'Weekly Sync Meeting'

    def test_get_actual_duration(self, mock_zoom_recording):
        """Test actual duration calculation from timestamps."""
        client = ZoomClient()

        duration = client.get_actual_duration(mock_zoom_recording)

        # 45 minutes duration
        assert duration == 45.0

    def test_get_actual_duration_fallback(self):
        """Test duration fallback when timestamps missing."""
        client = ZoomClient()
        recording = {'duration': 30}

        duration = client.get_actual_duration(recording)

        assert duration == 30

    @patch('zoom_manager.src.zoom_client.requests.get')
    @patch('zoom_manager.src.zoom_client.Path')
    def test_process_recording_debug_mode(self, mock_path, mock_get, mock_zoom_recording):
        """Test process_recording in debug mode (no actual download)."""
        import zoom_manager.config.settings as settings
        original_debug = settings.DEBUG
        settings.DEBUG = True

        try:
            client = ZoomClient()
            client.access_token = 'test_token'
            client.token_expires_at = datetime.now() + timedelta(hours=1)

            # Mock directory creation
            mock_dir = MagicMock()
            mock_path.return_value = mock_dir
            mock_dir.exists.return_value = True

            downloaded_files = client.process_recording(mock_zoom_recording, 'Weekly Sync')

            # In debug mode, should return empty list (no downloads)
            assert downloaded_files == []
            # Should not make any download requests
            mock_get.assert_not_called()
        finally:
            settings.DEBUG = original_debug

    def test_file_type_extension_mapping(self):
        """Test file type to extension mapping."""
        client = ZoomClient()

        assert client.FILE_TYPE_EXTENSION_MAP['shared_screen_with_speaker_view'] == '.mp4'
        assert client.FILE_TYPE_EXTENSION_MAP['audio_only'] == '.m4a'
        assert client.FILE_TYPE_EXTENSION_MAP['chat_file'] == '.txt'
        assert client.FILE_TYPE_EXTENSION_MAP['closed_caption'] == '.vtt'

    @patch('zoom_manager.src.zoom_client.DEBUG', False)
    @patch('zoom_manager.src.zoom_client.requests.get')
    @patch('zoom_manager.src.zoom_client.tqdm')
    def test_download_recording_file(self, mock_tqdm, mock_get, temp_download_dir):
        """Test individual file download with progress."""
        # Mock successful download
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b'chunk1', b'chunk2'])
        mock_response.headers = {'content-length': '12'}
        mock_get.return_value = mock_response

        # Mock tqdm progress bar
        mock_progress = MagicMock()
        mock_progress.n = 12  # Total size downloaded
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=False)
        mock_tqdm.return_value = mock_progress

        client = ZoomClient()
        client.access_token = 'test_token'
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        file_path = temp_download_dir / 'test.mp4'
        download_url = 'https://zoom.us/rec/download/test'

        result = client.download_recording(download_url, file_path)

        assert result is True
        mock_get.assert_called_once()
