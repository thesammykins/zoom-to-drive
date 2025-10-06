"""
Integration tests for main.py.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
from io import StringIO

from zoom_manager.src.main import (
    setup_logging,
    cleanup_downloads,
    parse_args,
    main
)


@pytest.mark.unit
class TestLoggingSetup:
    """Test suite for logging configuration."""

    def test_setup_logging(self):
        """Test logging setup creates proper handlers."""
        logger = setup_logging()

        assert logger is not None
        # Should have file and console handlers
        assert len(logger.handlers) >= 2

    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        import logging

        # Add a dummy handler
        root_logger = logging.getLogger()
        dummy_handler = logging.NullHandler()
        root_logger.addHandler(dummy_handler)
        initial_count = len(root_logger.handlers)

        logger = setup_logging()

        # Should have cleared old handlers and added new ones
        assert logger is root_logger


@pytest.mark.unit
class TestCleanup:
    """Test suite for cleanup functionality."""

    def test_cleanup_downloads_success(self, temp_download_dir):
        """Test successful cleanup of downloaded files."""
        # Create test files
        test_file1 = temp_download_dir / 'test1.mp4'
        test_file2 = temp_download_dir / 'test2.m4a'
        test_file1.write_text('test content 1')
        test_file2.write_text('test content 2')

        # Create subdirectory with file
        subdir = temp_download_dir / 'subdir'
        subdir.mkdir()
        test_file3 = subdir / 'test3.txt'
        test_file3.write_text('test content 3')

        # Run cleanup
        cleanup_downloads(temp_download_dir)

        # Verify cleanup
        assert not test_file1.exists()
        assert not test_file2.exists()
        assert not test_file3.exists()
        assert not subdir.exists()
        assert not temp_download_dir.exists()

    def test_cleanup_downloads_nonexistent_folder(self):
        """Test cleanup with nonexistent folder doesn't raise error."""
        nonexistent = Path('/nonexistent/path/to/folder')

        # Should not raise exception
        cleanup_downloads(nonexistent)

    def test_cleanup_downloads_handles_errors(self, temp_download_dir, monkeypatch):
        """Test cleanup handles permission errors gracefully."""
        test_file = temp_download_dir / 'test.mp4'
        test_file.write_text('test')

        # Mock unlink to raise exception
        original_unlink = Path.unlink

        def failing_unlink(self, *args, **kwargs):
            raise PermissionError("Access denied")

        monkeypatch.setattr(Path, 'unlink', failing_unlink)

        # Should not raise exception, just log error
        cleanup_downloads(temp_download_dir)


@pytest.mark.unit
class TestArgumentParsing:
    """Test suite for command line argument parsing."""

    def test_parse_args_required_fields(self):
        """Test parsing with required arguments."""
        test_args = ['--name', 'Test Meeting', '--email', 'test@example.com']

        with patch('sys.argv', ['main.py'] + test_args):
            args = parse_args()

        assert args.name == 'Test Meeting'
        assert args.email == 'test@example.com'
        assert args.days == 7  # default value

    def test_parse_args_with_custom_days(self):
        """Test parsing with custom days parameter."""
        test_args = ['--name', 'Meeting', '--email', 'test@example.com', '--days', '14']

        with patch('sys.argv', ['main.py'] + test_args):
            args = parse_args()

        assert args.days == 14

    def test_parse_args_no_slack_flag(self):
        """Test parsing with --no-slack flag."""
        test_args = ['--name', 'Meeting', '--email', 'test@example.com', '--no-slack']

        with patch('sys.argv', ['main.py'] + test_args):
            args = parse_args()

        assert args.no_slack is True

    def test_parse_args_custom_slack_webhook(self):
        """Test parsing with custom Slack webhook."""
        webhook = 'https://custom.webhook.url'
        test_args = ['--name', 'Meeting', '--email', 'test@example.com', '--slack-webhook', webhook]

        with patch('sys.argv', ['main.py'] + test_args):
            args = parse_args()

        assert args.slack_webhook == webhook

    def test_parse_args_rclone_overrides(self):
        """Test parsing with rclone parameter overrides."""
        test_args = [
            '--name', 'Meeting',
            '--email', 'test@example.com',
            '--rclone-remote', 'mydrive',
            '--rclone-base-path', 'Custom/Path'
        ]

        with patch('sys.argv', ['main.py'] + test_args):
            args = parse_args()

        assert args.rclone_remote == 'mydrive'
        assert args.rclone_base_path == 'Custom/Path'

    def test_parse_args_missing_required(self):
        """Test parsing fails when required arguments missing."""
        test_args = ['--name', 'Meeting']  # Missing email

        with patch('sys.argv', ['main.py'] + test_args):
            with pytest.raises(SystemExit):
                parse_args()


@pytest.mark.integration
class TestMainWorkflow:
    """Integration tests for main workflow."""

    @patch('zoom_manager.src.main.SlackClient')
    @patch('zoom_manager.src.main.RcloneClient')
    @patch('zoom_manager.src.main.ZoomClient')
    def test_main_success_flow(self, mock_zoom_class, mock_rclone_class, mock_slack_class,
                                mock_zoom_user, mock_zoom_recordings_response,
                                sample_downloaded_file, tmp_path):
        """Test successful main workflow execution."""
        # Mock ZoomClient
        mock_zoom = Mock()
        mock_zoom.get_user_by_email.return_value = mock_zoom_user
        mock_zoom.get_recordings.return_value = mock_zoom_recordings_response
        mock_zoom.get_actual_duration.return_value = 45
        mock_zoom.process_recording.return_value = [sample_downloaded_file]
        mock_zoom_class.return_value = mock_zoom

        # Mock RcloneClient
        mock_rclone = Mock()
        mock_rclone.upload_directory.return_value = 'Test/Path/2024-01-15'
        mock_rclone.get_file_id.return_value = 'file_id_123'
        mock_rclone_class.return_value = mock_rclone

        # Mock SlackClient
        mock_slack = Mock()
        mock_slack_class.return_value = mock_slack

        # Mock sys.argv
        test_args = [
            'main.py',
            '--name', 'Weekly',
            '--email', 'test@example.com',
            '--days', '7'
        ]

        with patch('sys.argv', test_args):
            main()

        # Verify workflow
        mock_zoom.get_user_by_email.assert_called_once_with('test@example.com')
        mock_zoom.get_recordings.assert_called_once()
        mock_zoom.process_recording.assert_called_once()
        mock_rclone.upload_directory.assert_called_once()
        mock_slack.send_notification.assert_called_once()

    @patch('zoom_manager.src.main.SlackClient')
    @patch('zoom_manager.src.main.RcloneClient')
    @patch('zoom_manager.src.main.ZoomClient')
    def test_main_with_no_slack_flag(self, mock_zoom_class, mock_rclone_class, mock_slack_class,
                                     mock_zoom_user, mock_zoom_recordings_response,
                                     sample_downloaded_file):
        """Test main workflow with Slack notifications disabled."""
        mock_zoom = Mock()
        mock_zoom.get_user_by_email.return_value = mock_zoom_user
        mock_zoom.get_recordings.return_value = mock_zoom_recordings_response
        mock_zoom.get_actual_duration.return_value = 45
        mock_zoom.process_recording.return_value = [sample_downloaded_file]
        mock_zoom_class.return_value = mock_zoom

        mock_rclone = Mock()
        mock_rclone.upload_directory.return_value = 'Test/Path/2024-01-15'
        mock_rclone_class.return_value = mock_rclone

        mock_slack = Mock()
        mock_slack_class.return_value = mock_slack

        test_args = [
            'main.py',
            '--name', 'Weekly',
            '--email', 'test@example.com',
            '--no-slack'
        ]

        with patch('sys.argv', test_args):
            main()

        # Slack notification should not be called
        mock_slack.send_notification.assert_not_called()

    @patch('zoom_manager.src.main.SlackClient')
    @patch('zoom_manager.src.main.RcloneClient')
    @patch('zoom_manager.src.main.ZoomClient')
    def test_main_user_not_found(self, mock_zoom_class, mock_rclone_class, mock_slack_class):
        """Test main workflow when user is not found."""
        mock_zoom = Mock()
        mock_zoom.get_user_by_email.side_effect = ValueError("No user found")
        mock_zoom_class.return_value = mock_zoom

        mock_rclone = Mock()
        mock_rclone_class.return_value = mock_rclone

        mock_slack = Mock()
        mock_slack_class.return_value = mock_slack

        test_args = [
            'main.py',
            '--name', 'Test',
            '--email', 'nonexistent@example.com'
        ]

        with patch('sys.argv', test_args):
            # Should handle error gracefully
            main()

        # Should have attempted user lookup
        mock_zoom.get_user_by_email.assert_called_once()
        # Should not proceed to get recordings
        mock_zoom.get_recordings.assert_not_called()

    @patch('zoom_manager.src.main.SlackClient')
    @patch('zoom_manager.src.main.RcloneClient')
    @patch('zoom_manager.src.main.ZoomClient')
    def test_main_no_recordings_found(self, mock_zoom_class, mock_rclone_class,
                                      mock_slack_class, mock_zoom_user):
        """Test main workflow when no matching recordings found."""
        mock_zoom = Mock()
        mock_zoom.get_user_by_email.return_value = mock_zoom_user
        # Return empty recordings
        mock_zoom.get_recordings.return_value = {'meetings': []}
        mock_zoom_class.return_value = mock_zoom

        mock_rclone = Mock()
        mock_rclone_class.return_value = mock_rclone

        mock_slack = Mock()
        mock_slack_class.return_value = mock_slack

        test_args = [
            'main.py',
            '--name', 'Nonexistent Meeting',
            '--email', 'test@example.com'
        ]

        with patch('sys.argv', test_args):
            main()

        # Should have searched for recordings
        mock_zoom.get_recordings.assert_called_once()
        # Should not process any recordings
        mock_zoom.process_recording.assert_not_called()

    @patch('zoom_manager.src.main.SlackClient')
    @patch('zoom_manager.src.main.RcloneClient')
    @patch('zoom_manager.src.main.ZoomClient')
    def test_main_skips_short_recordings(self, mock_zoom_class, mock_rclone_class,
                                         mock_slack_class, mock_zoom_user):
        """Test that recordings shorter than 5 minutes are skipped."""
        # Create short recording
        short_recording = {
            'uuid': 'recording456',
            'id': 456789,
            'topic': 'Weekly Sync Meeting',
            'start_time': '2024-01-15T10:00:00Z',
            'duration': 3,  # 3 minutes - below threshold
            'recording_count': 1,
            'recording_files': [{
                'id': 'file1',
                'recording_type': 'shared_screen_with_speaker_view',
                'download_url': 'https://zoom.us/rec/download/file1',
                'file_size': 10485760,
                'recording_start': '2024-01-15T10:00:00Z',
                'recording_end': '2024-01-15T10:03:00Z'
            }]
        }

        mock_zoom = Mock()
        mock_zoom.get_user_by_email.return_value = mock_zoom_user
        mock_zoom.get_recordings.return_value = {'meetings': [short_recording]}
        # Return short duration (3 minutes)
        mock_zoom.get_actual_duration.return_value = 3.0
        mock_zoom_class.return_value = mock_zoom

        mock_rclone = Mock()
        mock_rclone_class.return_value = mock_rclone

        mock_slack = Mock()
        mock_slack_class.return_value = mock_slack

        test_args = [
            'main.py',
            '--name', 'Weekly',
            '--email', 'test@example.com'
        ]

        with patch('sys.argv', test_args):
            main()

        # Should not process the recording
        mock_zoom.process_recording.assert_not_called()
        mock_rclone.upload_directory.assert_not_called()
