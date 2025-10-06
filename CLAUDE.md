# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python automation tool that fetches Zoom cloud recordings, downloads them locally, uploads to Google Drive via rclone, and sends optional Slack notifications. The workflow is: Discovery → Download → Upload → Notify → Cleanup.

## Common Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r zoom_manager/requirements.txt

# Configure environment variables
cp zoom_manager/env_example .env
# Edit .env with actual credentials (never commit this file)

# Test rclone integration
python3 test_rclone.py
```

### Running the Application

**Recommended: Use the wrapper script**
```bash
# Make executable (first time only)
chmod +x ./run_zoom_manager.sh

# Basic usage
./run_zoom_manager.sh --name "Weekly Sync" --email user@example.com --days 7

# With rclone overrides (preferred over env vars)
./run_zoom_manager.sh --name "Meeting" --email user@example.com --days 14 \
  --rclone-remote mydrive --rclone-base-path "Custom/Path"

# Debug mode (verbose logging, mock downloads)
DEBUG=1 ./run_zoom_manager.sh --name "Test" --email user@example.com --days 1

# Disable Slack notifications
./run_zoom_manager.sh --name "Meeting" --email user@example.com --no-slack
```

**Alternative: Direct Python execution**
```bash
python3 zoom_manager/src/main.py \
  --name "Weekly Sync" \
  --email user@example.com \
  --days 7 \
  [--no-slack] \
  [--rclone-remote drive] \
  [--rclone-base-path "Zoom/Recordings"]
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=zoom_manager --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest tests/test_zoom_client.py

# Run specific test
pytest tests/test_zoom_client.py::TestZoomClient::test_get_access_token_success

# Run tests with verbose output
pytest -v

# Run tests and show print statements
pytest -s
```

### Debugging and Logs
```bash
# Follow logs in real-time
tail -F zoom_manager/logs/zoom_manager_*.log

# View recent errors
grep ERROR zoom_manager/logs/zoom_manager_*.log

# Check rclone setup
rclone version
rclone listremotes
rclone lsd <remote-name>:
```

## Architecture

### High-Level Flow
1. **CLI Parsing** (main.py): Parses arguments, sets up logging
2. **User Lookup** (ZoomClient): Resolves email to Zoom user ID
3. **Recording Fetch** (ZoomClient): Gets recordings within date range, filters by meeting name
4. **Duration Check**: Skips recordings shorter than 5 minutes
5. **Download** (ZoomClient): Downloads files to `zoom_manager/downloads/YYYY-MM-DD/`
6. **Upload** (RcloneClient): Batch uploads entire directory to Google Drive via rclone
7. **Notify** (SlackClient): Sends Slack notifications with Drive links (for .mp4 files only)
8. **Cleanup**: Removes local files after successful upload

### Key Components

**Main Orchestrator** (`zoom_manager/src/main.py`)
- Entry point and CLI interface
- Coordinates workflow: user lookup → recordings fetch → download → upload → notify → cleanup
- Handles logging setup (file + console, respects DEBUG mode)
- Configuration precedence: CLI flags > shell env vars > .env file

**Zoom Client** (`zoom_manager/src/zoom_client.py`)
- OAuth 2.0 authentication using account_credentials grant
- `get_user_by_email(email)` - Resolves email to user info
- `get_recordings(user_id, start_date, end_date)` - Fetches recordings in date range
- `process_recording(recording, meeting_name)` - Downloads files with progress tracking (tqdm)
- `get_actual_duration(recording)` - Computes duration from start/end timestamps
- **DEBUG mode**: `download_recording()` returns False (no actual download)
- Timezone: All timestamps converted to Australia/Melbourne
- File mapping: Maps Zoom file types to extensions (.mp4, .m4a, .vtt, .txt, etc.)

**Rclone Client** (`zoom_manager/src/rclone_client.py`)
- Validates rclone binary and remote configuration on init
- **Constructor accepts overrides**: `RcloneClient(remote_name=None, base_path=None)` - CLI args take precedence over env vars
- `upload_directory(local_path, date_folder)` - Batch uploads entire folder to remote
- `get_file_id(date_folder, file_name)` - Extracts Google Drive file ID from rclone metadata
- `test_connection()` - Validates remote connectivity
- Remote path structure: `{RCLONE_REMOTE_NAME}:{RCLONE_BASE_PATH}/{date_folder}/`

**Slack Client** (`zoom_manager/src/slack_client.py`)
- Constructor: `SlackClient(webhook_url=None)` - accepts custom webhook URL
- `send_notification(recording_name, file_name, file_id)` - Posts to webhook with Drive link
- Gracefully skips if no webhook configured

**Settings** (`zoom_manager/config/settings.py`)
- Loads `.env` via python-dotenv
- Key paths: `logs/`, `downloads/`, `credentials/`
- Environment variables:
  - Zoom: `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `ZOOM_ACCOUNT_ID`
  - Rclone: `RCLONE_REMOTE_NAME`, `RCLONE_BASE_PATH`
  - Slack: `SLACK_WEBHOOK_URL` (optional)
  - Debug: `DEBUG` (0/1 or true/false)
- Logging: Daily log file, DEBUG controls verbosity
- Timezone: Australia/Melbourne

### File Structure
```
zoom_manager/
├── src/
│   ├── main.py           # CLI orchestrator, main workflow
│   ├── zoom_client.py    # Zoom API integration (OAuth, recordings)
│   ├── rclone_client.py  # rclone file operations
│   └── slack_client.py   # Slack notifications
├── config/
│   └── settings.py       # Configuration and env vars
├── logs/                 # Application logs (auto-created)
├── downloads/            # Temporary download storage (auto-created)
└── requirements.txt      # Python dependencies

tests/
├── conftest.py           # Shared fixtures and test configuration
├── test_zoom_client.py   # Unit tests for ZoomClient
├── test_rclone_client.py # Unit tests for RcloneClient
├── test_slack_client.py  # Unit tests for SlackClient
└── test_main.py          # Integration tests for main workflow

pytest.ini               # Pytest configuration
requirements-test.txt    # Test dependencies
```

## Important Implementation Details

### Configuration Priority
CLI arguments override environment variables, which override .env values:
1. CLI flags (`--rclone-remote`, `--rclone-base-path`, `--slack-webhook`)
2. Shell environment variables
3. `.env` file values

### Duration Filtering
- Recordings shorter than 5 minutes are automatically skipped
- Duration calculated from API metadata AND actual start/end timestamps (uses maximum value)
- Logged at debug level for transparency

### Rclone Parameter Handling
- **Important**: Use CLI args (`--rclone-remote`, `--rclone-base-path`) instead of env vars when possible
- RcloneClient accepts parameters in constructor to bypass env timing issues
- The wrapper script forwards these CLI args directly to the Python script

### Debug Mode
When `DEBUG=1`:
- Verbose logging enabled (shows debug-level messages)
- ZoomClient skips actual downloads (mock mode)
- RcloneClient includes `--verbose --log-level DEBUG` flags
- All operations logged to both console and file

### Slack Notifications
- Only sent for `.mp4` files
- Can be disabled with `--no-slack` flag
- Requires Drive file ID extraction via `rclone lsjson`
- Gracefully handles missing webhook configuration

## Prerequisites

1. **Python 3.7+** installed and in PATH
2. **rclone** installed and configured:
   - Install: `brew install rclone` (macOS) or `curl https://rclone.org/install.sh | sudo bash`
   - Configure: `rclone config` (create Google Drive remote)
   - Verify: `rclone listremotes`
3. **Zoom OAuth 2.0 credentials**:
   - Server-to-Server OAuth app from Zoom Marketplace
   - Required scopes: `recording:read:admin`, `user:read:admin`
4. **Slack webhook** (optional for notifications)

## Security Notes

- All credentials in environment variables (never commit `.env`)
- `.gitignore` excludes: `.env`, `credentials/`, `run_zoom_manager.sh`, `downloads/`, `logs/`
- OAuth tokens cached with automatic refresh (5-minute buffer before expiry)
- Local files deleted after successful upload

## Troubleshooting

### Common Issues

**Permission denied on wrapper script:**
```bash
chmod +x ./run_zoom_manager.sh
```

**rclone not configured:**
```bash
rclone listremotes  # Check configured remotes
rclone config       # Configure new remote
```

**Environment variables not loading:**
- Ensure `.env` exists in project root
- Check file permissions: `ls -la .env`
- Verify no syntax errors in `.env`

**Rclone parameters not respected:**
- Use CLI flags instead of env vars: `--rclone-remote`, `--rclone-base-path`
- These are passed directly to RcloneClient constructor
