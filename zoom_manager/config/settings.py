import os
from datetime import datetime
import pytz
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
DOWNLOAD_DIR = BASE_DIR / "downloads"
CREDENTIALS_DIR = BASE_DIR / "credentials"

# Create necessary directories
LOGS_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)

# Timezone configuration
TIMEZONE = pytz.timezone('Australia/Melbourne')

# Zoom API Configuration
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_API_BASE_URL = "https://api.zoom.us/v2"

# Remove DAYS_TO_SEARCH from environment variables
# DAYS_TO_SEARCH = int(os.getenv("DAYS_TO_SEARCH", "7"))

# Google Drive Configuration
GOOGLE_CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
GOOGLE_TOKEN_FILE = CREDENTIALS_DIR / "token.pickle"
GOOGLE_SHARED_DRIVE_ID = os.getenv("GOOGLE_SHARED_DRIVE_ID") or None  # Allow CLI override
GOOGLE_TARGET_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID") or None  # Allow CLI override

# Slack Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Debug mode
DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 't')

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / f"zoom_manager_{datetime.now().strftime('%Y%m%d')}.log"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO