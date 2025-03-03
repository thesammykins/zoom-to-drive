"""
Tests for the TransferManager class
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import asyncio
from zoom_manager.src.transfer_manager import TransferManager

@pytest.fixture
def config():
    return {
        'meeting_name': 'Test Meeting',
        'user_email': 'test@example.com',
        'days': 7,
        'debug_mode': True,
        'cleanup': True,
        'env_file': 'test.env'
    }

@pytest.fixture
def transfer_manager(config):
    with patch('zoom_manager.src.transfer_manager.ZoomClient') as mock_zoom, \
         patch('zoom_manager.src.transfer_manager.GoogleDriveClient') as mock_gdrive, \
         patch('zoom_manager.src.transfer_manager.SlackClient') as mock_slack:
        manager = TransferManager(config)
        manager.zoom = mock_zoom.return_value
        manager.gdrive = mock_gdrive.return_value
        manager.slack = mock_slack.return_value
        return manager

@pytest.mark.asyncio
async def test_download_file(transfer_manager):
    """Test file download functionality"""
    url = 'https://example.com/test.mp4'
    filepath = Path('test.mp4')
    
    # Mock aiohttp.ClientSession
    mock_response = Mock()
    mock_response.status = 200
    mock_response.headers = {'content-length': '1000'}
    mock_response.content.iter_chunked.return_value = [b'chunk1', b'chunk2']
    
    mock_session = Mock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        success = await transfer_manager.download_file(url, filepath, mock_session)
        assert success is True

@pytest.mark.asyncio
async def test_process_recording(transfer_manager):
    """Test recording processing"""
    recording = {
        'topic': 'Test Meeting',
        'recording_files': [
            {
                'recording_type': 'mp4',
                'download_url': 'https://example.com/test.mp4'
            }
        ]
    }
    
    # Mock session
    mock_session = Mock()
    
    # Mock download and upload
    transfer_manager.download_file = Mock(return_value=True)
    transfer_manager.upload_file = Mock(return_value='file_id')
    
    success = await transfer_manager.process_recording(recording, mock_session)
    assert success is True

@pytest.mark.asyncio
async def test_run(transfer_manager):
    """Test main execution flow"""
    # Mock user info
    transfer_manager.zoom.get_user_by_email_async.return_value = {'id': 'user123'}
    
    # Mock recordings
    transfer_manager.zoom.get_recordings_async.return_value = {
        'meetings': [
            {
                'topic': 'Test Meeting',
                'duration': 10,
                'recording_files': [
                    {
                        'recording_type': 'mp4',
                        'download_url': 'https://example.com/test.mp4'
                    }
                ]
            }
        ]
    }
    
    # Mock session
    mock_session = Mock()
    
    # Mock download and upload
    transfer_manager.download_file = Mock(return_value=True)
    transfer_manager.upload_file = Mock(return_value='file_id')
    
    success = await transfer_manager.run()
    assert success is True 