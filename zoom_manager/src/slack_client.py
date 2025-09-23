import logging
import requests
from zoom_manager.config.settings import SLACK_WEBHOOK_URL

class SlackClient:
    """
    Client for sending notifications to Slack about uploaded recordings.
    Uses Slack's incoming webhook functionality for message delivery.
    """

    def __init__(self, webhook_url=None):
        """Initialize SlackClient with logging configuration.

        Args:
            webhook_url (str, optional): Custom Slack webhook URL. If not provided,
                                       will use SLACK_WEBHOOK_URL from settings.
        """
        self.logger = logging.getLogger(__name__)
        self.webhook_url = webhook_url or SLACK_WEBHOOK_URL

    def send_notification(self, recording_name: str, file_name: str, file_id: str):
        """
        Send a formatted notification to Slack about an uploaded recording.

        Args:
            recording_name (str): Name of the recording/meeting
            file_name (str): Name of the uploaded file
            file_id (str): Google Drive file ID for direct link

        Returns:
            None

        Note:
            Silently fails if no webhook URL is configured
        """
        if not self.webhook_url:
            self.logger.warning("No Slack webhook URL configured, skipping notification")
            return

        try:
            message = {
                "text": f"New recording uploaded: {recording_name}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*New recording uploaded*\n• Recording: {recording_name}\n• File: {file_name}\n• <https://drive.google.com/file/d/{file_id}/view|View in Google Drive>"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "_Brought to you with the power of Copilot, Zed, Warp and Cursor_"
                            }
                        ]
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=message)
            response.raise_for_status()
            self.logger.info(f"Slack notification sent for {file_name} to {self.webhook_url[:50]}...")

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
