import logging
import requests
from zoom_manager.config.settings import SLACK_WEBHOOK_URL

class SlackClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def send_notification(self, recording_name: str, file_name: str, file_id: str):
        """Send notification about uploaded recording to Slack"""
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
                                "text": "_Brought to you with the power of Copilot_"
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