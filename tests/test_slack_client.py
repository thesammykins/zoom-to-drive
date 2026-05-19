"""
Unit tests for SlackClient.
"""
import pytest
import requests
from unittest.mock import Mock, patch

from zoom_manager.src.slack_client import SlackClient


@pytest.mark.unit
class TestSlackClient:
    """Test suite for SlackClient."""

    def test_init_with_webhook(self):
        """Test SlackClient initialization with webhook URL."""
        webhook = 'https://hooks.slack.com/custom/webhook'
        client = SlackClient(webhook_url=webhook)

        assert client.webhook_url == webhook
        assert client.logger is not None

    def test_init_without_webhook(self):
        """Test SlackClient initialization without webhook URL (uses settings)."""
        client = SlackClient()

        # Should use the test webhook from conftest
        assert client.webhook_url == 'https://hooks.slack.com/test/webhook'

    @patch('zoom_manager.src.slack_client.requests.post')
    def test_send_notification_success(self, mock_post, mock_slack_response):
        """Test successful notification sending."""
        mock_post.return_value = mock_slack_response

        client = SlackClient()
        client.send_notification(
            recording_name='Weekly Sync',
            file_name='recording.mp4',
            file_id='file_123'
        )

        # Verify the request was made
        mock_post.assert_called_once()
        assert mock_post.call_args.kwargs['timeout'] == (10, 30)

        # Verify the payload
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://hooks.slack.com/test/webhook'

        payload = call_args[1]['json']
        assert 'text' in payload
        assert 'Weekly Sync' in payload['text']
        assert 'blocks' in payload

        # Check blocks content
        blocks = payload['blocks']
        assert len(blocks) == 2
        assert blocks[0]['type'] == 'section'
        assert 'recording.mp4' in blocks[0]['text']['text']
        assert 'file_123' in blocks[0]['text']['text']

    @patch('zoom_manager.src.slack_client.requests.post')
    def test_send_notification_with_drive_link(self, mock_post, mock_slack_response):
        """Test notification includes proper Google Drive link."""
        mock_post.return_value = mock_slack_response

        client = SlackClient()
        file_id = 'abc123xyz'
        client.send_notification(
            recording_name='Test Meeting',
            file_name='test.mp4',
            file_id=file_id
        )

        payload = mock_post.call_args[1]['json']
        text_content = payload['blocks'][0]['text']['text']

        # Verify Drive link is correctly formatted
        assert f'https://drive.google.com/file/d/{file_id}/view' in text_content

    @patch('zoom_manager.src.slack_client.requests.post')
    def test_send_notification_request_failure_redacts_url(self, mock_post, caplog):
        """Test notification sending with request failure."""
        webhook_url = 'https://hooks.slack.com/services/secret/path'
        mock_post.side_effect = requests.ConnectionError(
            f"Failed to connect to {webhook_url}"
        )

        client = SlackClient(webhook_url=webhook_url)

        # Should not raise exception, just log error
        client.send_notification(
            recording_name='Test',
            file_name='test.mp4',
            file_id='123'
        )

        mock_post.assert_called_once()
        assert webhook_url not in caplog.text
        assert 'ConnectionError' in caplog.text

    def test_send_notification_no_webhook(self):
        """Test notification sending when no webhook configured."""
        client = SlackClient(webhook_url="")

        # Should not raise exception, just skip
        client.send_notification(
            recording_name='Test',
            file_name='test.mp4',
            file_id='123'
        )

    @patch('zoom_manager.src.slack_client.requests.post')
    def test_send_notification_http_error(self, mock_post, caplog):
        """Test notification sending with HTTP error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'invalid_payload'
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "400 Client Error for url: https://hooks.slack.com/services/secret",
            response=mock_response,
        )
        mock_post.return_value = mock_response

        client = SlackClient()

        # Should handle error gracefully
        client.send_notification(
            recording_name='Test',
            file_name='test.mp4',
            file_id='123'
        )

        mock_post.assert_called_once()
        assert 'HTTP 400 - invalid_payload' in caplog.text
        assert 'hooks.slack.com' not in caplog.text

    @patch('zoom_manager.src.slack_client.requests.post')
    def test_notification_message_structure(self, mock_post, mock_slack_response):
        """Test the structure of the notification message."""
        mock_post.return_value = mock_slack_response

        client = SlackClient()
        recording = 'Important Meeting'
        filename = 'recording_2024.mp4'
        file_id = 'xyz789'

        client.send_notification(
            recording_name=recording,
            file_name=filename,
            file_id=file_id
        )

        payload = mock_post.call_args[1]['json']

        # Verify top-level structure
        assert 'text' in payload
        assert 'blocks' in payload
        assert isinstance(payload['blocks'], list)

        # Verify section block
        section_block = payload['blocks'][0]
        assert section_block['type'] == 'section'
        assert section_block['text']['type'] == 'mrkdwn'
        assert recording in section_block['text']['text']
        assert filename in section_block['text']['text']

        # Verify context block
        context_block = payload['blocks'][1]
        assert context_block['type'] == 'context'
        assert 'elements' in context_block
        assert context_block['elements'][0]['type'] == 'mrkdwn'

    def test_notification_formats_fallback_drive_path(self):
        """Test fallback rclone paths are not formatted as Google Drive file IDs."""
        client = SlackClient(webhook_url="")

        reference = client._format_drive_reference('Test/Path/2024-01-15/test.mp4')

        assert reference == 'Drive location: `Test/Path/2024-01-15/test.mp4`'
