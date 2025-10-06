"""
Unit tests for RcloneClient.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess

from zoom_manager.src.rclone_client import RcloneClient


@pytest.mark.unit
class TestRcloneClient:
    """Test suite for RcloneClient."""

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_init_success(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test successful RcloneClient initialization."""
        mock_which.return_value = '/usr/bin/rclone'
        mock_result = Mock()
        mock_result.stdout = mock_rclone_listremotes
        mock_run.return_value = mock_result

        client = RcloneClient()

        assert client.remote_name == 'test_remote'
        assert client.base_path == 'Test/Path'
        assert client.rclone_executable == '/usr/bin/rclone'
        mock_which.assert_called_once_with('rclone')

    @patch('zoom_manager.src.rclone_client.shutil.which')
    def test_init_rclone_not_installed(self, mock_which):
        """Test initialization when rclone is not installed."""
        mock_which.return_value = None

        with pytest.raises(RuntimeError, match="rclone is not installed"):
            RcloneClient()

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_init_remote_not_configured(self, mock_run, mock_which):
        """Test initialization when remote is not configured."""
        mock_which.return_value = '/usr/bin/rclone'
        mock_result = Mock()
        mock_result.stdout = "other_remote:\n"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="remote 'test_remote' is not configured"):
            RcloneClient()

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_init_with_custom_parameters(self, mock_run, mock_which):
        """Test initialization with custom remote name and base path."""
        mock_which.return_value = '/usr/bin/rclone'
        mock_result = Mock()
        mock_result.stdout = "custom_remote:\n"
        mock_run.return_value = mock_result

        client = RcloneClient(remote_name='custom_remote', base_path='Custom/Path')

        assert client.remote_name == 'custom_remote'
        assert client.base_path == 'Custom/Path'

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_create_remote_directory(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test remote directory creation."""
        mock_which.return_value = '/usr/bin/rclone'

        # Setup for init
        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        # Setup for mkdir
        mkdir_result = Mock()
        mkdir_result.returncode = 0

        mock_run.side_effect = [init_result, mkdir_result]

        client = RcloneClient()
        result = client._create_remote_directory('test_remote:Test/Path/2024-01-15')

        assert result is True
        assert mock_run.call_count == 2

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_upload_directory_success(self, mock_run, mock_which, mock_rclone_listremotes, temp_download_dir):
        """Test successful directory upload."""
        mock_which.return_value = '/usr/bin/rclone'

        # Setup for init (listremotes)
        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        # Setup for mkdir
        mkdir_result = Mock()
        mkdir_result.returncode = 0

        # Setup for copy
        copy_result = Mock()
        copy_result.returncode = 0

        mock_run.side_effect = [init_result, mkdir_result, copy_result]

        client = RcloneClient()
        remote_path = client.upload_directory(temp_download_dir, '2024-01-15')

        assert remote_path == 'Test/Path/2024-01-15'
        # Should call: listremotes (init), mkdir, copy
        assert mock_run.call_count == 3

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_upload_directory_failure(self, mock_run, mock_which, mock_rclone_listremotes, temp_download_dir):
        """Test directory upload failure."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        mkdir_result = Mock()
        mkdir_result.returncode = 0

        # Simulate copy failure
        mock_run.side_effect = [
            init_result,
            mkdir_result,
            subprocess.CalledProcessError(1, 'rclone copy')
        ]

        client = RcloneClient()

        with pytest.raises(subprocess.CalledProcessError):
            client.upload_directory(temp_download_dir, '2024-01-15')

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_check_file_exists_true(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test file existence check when file exists."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        lsf_result = Mock()
        lsf_result.returncode = 0
        lsf_result.stdout = 'test_file.mp4\n'

        mock_run.side_effect = [init_result, lsf_result]

        client = RcloneClient()
        exists = client.check_file_exists('test_file.mp4', '2024-01-15')

        assert exists is True

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_check_file_exists_false(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test file existence check when file doesn't exist."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        lsf_result = Mock()
        lsf_result.returncode = 1
        lsf_result.stdout = ''

        mock_run.side_effect = [init_result, lsf_result]

        client = RcloneClient()
        exists = client.check_file_exists('nonexistent.mp4', '2024-01-15')

        assert exists is False

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_get_file_id_success(self, mock_run, mock_which, mock_rclone_listremotes, mock_rclone_lsjson_response):
        """Test successful file ID retrieval."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        lsjson_result = Mock()
        lsjson_result.stdout = json.dumps(mock_rclone_lsjson_response)

        mock_run.side_effect = [init_result, lsjson_result]

        client = RcloneClient()
        file_id = client.get_file_id('2024-01-15', 'test_file.mp4')

        assert file_id == 'drive_file_id_12345'

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_get_file_id_not_found(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test file ID retrieval when file not found."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        lsjson_result = Mock()
        lsjson_result.stdout = '[]'

        mock_run.side_effect = [init_result, lsjson_result]

        client = RcloneClient()

        with pytest.raises(ValueError, match="No metadata found"):
            client.get_file_id('2024-01-15', 'nonexistent.mp4')

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_test_connection_success(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test successful connection test."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        lsd_result = Mock()
        lsd_result.returncode = 0
        lsd_result.stdout = 'folder1\nfolder2\n'

        mock_run.side_effect = [init_result, lsd_result]

        client = RcloneClient()
        connected = client.test_connection()

        assert connected is True

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_test_connection_failure(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test connection test failure."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        mock_run.side_effect = [
            init_result,
            subprocess.CalledProcessError(1, 'rclone lsd')
        ]

        client = RcloneClient()
        connected = client.test_connection()

        assert connected is False

    @patch('zoom_manager.src.rclone_client.shutil.which')
    @patch('zoom_manager.src.rclone_client.subprocess.run')
    def test_get_remote_info(self, mock_run, mock_which, mock_rclone_listremotes):
        """Test getting remote configuration info."""
        mock_which.return_value = '/usr/bin/rclone'

        init_result = Mock()
        init_result.stdout = mock_rclone_listremotes

        config_result = Mock()
        config_result.stdout = "[test_remote]\ntype = drive\nscope = drive\n"

        mock_run.side_effect = [init_result, config_result]

        client = RcloneClient()
        config = client.get_remote_info()

        assert 'type' in config
        assert config['type'] == 'drive'
