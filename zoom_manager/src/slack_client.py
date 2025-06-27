import logging
import requests
from zoom_manager.config.settings import SLACK_WEBHOOK_URL

class SlackClient:
    """
    Client for sending notifications to Slack about uploaded recordings.
    Uses Slack's incoming webhook functionality for message delivery.
    """
    
    def __init__(self):
        """Initialize SlackClient with logging configuration."""
        self.logger = logging.getLogger(__name__)
        
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
        if not SLACK_WEBHOOK_URL:
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
                                "text": "_Brought to you with the power of Copilot, Warp and Cursor_"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(SLACK_WEBHOOK_URL, json=message)
            response.raise_for_status()
            self.logger.info(f"Slack notification sent for {file_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
