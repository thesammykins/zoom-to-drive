# Zoom to Drive

A Python automation tool that fetches Zoom cloud recordings, downloads them locally, uploads to Google Drive via rclone, and optionally sends Slack notifications.

## Features

- 🎥 **Smart Recording Retrieval**: Fetch recordings by meeting name and date range
- ⚡ **Automated Workflow**: Download → Upload → Notify → Cleanup
- 🔍 **Duration Filtering**: Automatically skips recordings shorter than 5 minutes
- 📁 **Organized Storage**: Date-based folder structure (YYYY-MM-DD)
- 🚀 **rclone Integration**: Fast, reliable uploads to Google Drive
- 💬 **Slack Notifications**: Optional notifications with Drive links
- 🐛 **Debug Mode**: Test runs without actual downloads
- 🛡️ **Secure**: Environment variable based configuration

## Quick Start

### Prerequisites

- Python 3.7+
- [rclone](https://rclone.org/) installed and configured with Google Drive
- Zoom OAuth 2.0 application credentials
- Optional: Slack webhook for notifications

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zoom_to_drive
   ```

2. **Set up environment**
   ```bash
   # Make the wrapper script executable
   chmod +x ./run_zoom_manager.sh
   
   # Create your environment file
   cp zoom_manager/env_example .env
   ```

3. **Configure credentials**
   
   Edit `.env` with your actual credentials:
   ```env
   # Zoom OAuth 2.0 Credentials
   ZOOM_CLIENT_ID=your_zoom_client_id
   ZOOM_CLIENT_SECRET=your_zoom_client_secret
   ZOOM_ACCOUNT_ID=your_zoom_account_id
   
   # rclone Configuration
   RCLONE_REMOTE_NAME=drive
   RCLONE_BASE_PATH=Zoom/Recordings
   
   # Optional Slack Integration
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   
   # Debug Mode
   DEBUG=0
   ```

4. **Configure rclone**
   ```bash
   # Install rclone (macOS)
   brew install rclone
   
   # Configure Google Drive remote
   rclone config
   
   # Test the connection
   python3 test_rclone.py
   ```

### Usage

**Using the wrapper script (recommended):**

```bash
# Basic usage
./run_zoom_manager.sh --name "Weekly Sync" --email user@example.com --days 7

# With custom settings
./run_zoom_manager.sh \
  --name "Team Meeting" \
  --email user@example.com \
  --days 14 \
  --rclone-remote mydrive \
  --rclone-base-path "Custom/Path"

# Debug mode (no actual downloads)
DEBUG=1 ./run_zoom_manager.sh --name "Test Meeting" --email user@example.com --days 1

# Disable Slack notifications
./run_zoom_manager.sh --name "Meeting" --email user@example.com --no-slack
```

**Direct Python usage:**

```bash
python3 zoom_manager/src/main.py \
  --name "Weekly Sync" \
  --email user@example.com \
  --days 7
```

## How It Works

1. **🔍 Discovery**: Searches for recordings by user email and meeting name
2. **📥 Download**: Downloads matching recordings to `zoom_manager/downloads/YYYY-MM-DD/`
3. **📤 Upload**: Uses rclone to upload entire folders to Google Drive
4. **💬 Notify**: Sends Slack notifications with Drive links (optional)
5. **🧹 Cleanup**: Removes local files after successful upload

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ZOOM_CLIENT_ID` | Zoom OAuth 2.0 Client ID | ✅ |
| `ZOOM_CLIENT_SECRET` | Zoom OAuth 2.0 Client Secret | ✅ |
| `ZOOM_ACCOUNT_ID` | Zoom Account ID | ✅ |
| `RCLONE_REMOTE_NAME` | rclone remote name (e.g., "drive") | ✅ |
| `RCLONE_BASE_PATH` | Base path in Drive (e.g., "Zoom/Recordings") | ✅ |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for notifications | ❌ |
| `DEBUG` | Enable debug mode (0 or 1) | ❌ |

### Command Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `--name` | Meeting name/topic substring to search for | ✅ |
| `--email` | Email of the Zoom user | ✅ |
| `--days` | Number of days to search back (default: 7) | ❌ |
| `--no-slack` | Disable Slack notifications | ❌ |
| `--slack-webhook` | Override Slack webhook URL | ❌ |
| `--rclone-remote` | Override rclone remote name | ❌ |
| `--rclone-base-path` | Override rclone base path | ❌ |

## Setup Guides

### Zoom OAuth 2.0 Setup

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Create a new "Server-to-Server OAuth" app
3. Get your Client ID, Client Secret, and Account ID
4. Add required scopes: `recording:read:admin`, `user:read:admin`

### rclone Google Drive Setup

1. Run `rclone config`
2. Choose "Google Drive" as the storage type
3. Follow the authentication flow
4. Test with `rclone lsd your-remote-name:`

### Slack Webhook Setup (Optional)

1. Go to your Slack workspace's app settings
2. Create a new "Incoming Webhooks" integration
3. Choose your target channel
4. Copy the webhook URL

## Architecture

```
zoom_manager/
├── src/
│   ├── main.py           # CLI orchestrator and main workflow
│   ├── zoom_client.py    # Zoom API integration and OAuth
│   ├── rclone_client.py  # rclone integration and file operations
│   └── slack_client.py   # Slack notifications
├── config/
│   └── settings.py       # Configuration and environment variables
└── logs/                 # Application logs (auto-created)
```

### Key Components

- **Main Orchestrator**: Handles CLI parsing and coordinates the workflow
- **Zoom Client**: Manages OAuth authentication and recording retrieval
- **rclone Client**: Handles Google Drive uploads with progress tracking
- **Slack Client**: Sends notifications with Drive file links
- **Settings**: Centralized configuration management

## Troubleshooting

### Common Issues

**Permission denied on script:**
```bash
chmod +x ./run_zoom_manager.sh
```

**Python not found:**
```bash
# macOS
brew install python3

# Or check your PATH
which python3
```

**rclone not configured:**
```bash
# Check if rclone is installed
rclone version

# List configured remotes
rclone listremotes

# Configure a new remote
rclone config
```

**Environment variables not loading:**
- Ensure `.env` file exists in the project root
- Check file permissions: `ls -la .env`
- Verify no syntax errors in `.env`

### Debug Mode

Enable debug mode for verbose logging and mock operations:

```bash
DEBUG=1 ./run_zoom_manager.sh --name "Test" --email user@example.com --days 1
```

In debug mode:
- Downloads are skipped (mock operation)
- Verbose logging is enabled
- All operations are logged to `zoom_manager/logs/`

### Logs

Application logs are stored in `zoom_manager/logs/zoom_manager_YYYYMMDD.log`:

```bash
# Follow logs in real-time
tail -F zoom_manager/logs/zoom_manager_*.log

# View recent errors
grep ERROR zoom_manager/logs/zoom_manager_*.log
```

## Development

### Project Structure

```
zoom_to_drive/
├── run_zoom_manager.sh   # Convenience wrapper script
├── setup.py              # Package configuration
├── test_rclone.py        # rclone integration tests
├── WARP.md              # Development guide for AI assistants
└── zoom_manager/
    ├── requirements.txt  # Python dependencies
    ├── env_example      # Environment template
    └── ...
```

### Running Tests

```bash
# Test rclone integration
python3 test_rclone.py

# Test with debug mode
DEBUG=1 python3 zoom_manager/src/main.py --name "Test" --email test@example.com --days 1
```

## Security

- ✅ All credentials stored in environment variables
- ✅ Sensitive files excluded from git via `.gitignore`
- ✅ OAuth 2.0 token management with automatic refresh
- ✅ Local file cleanup after successful uploads
- ⚠️ **Never commit** `.env`, `credentials/`, or `run_zoom_manager.sh`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly with debug mode
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 Check [WARP.md](WARP.md) for detailed development guidance
- 🐛 Create an issue for bugs or feature requests
- 💡 Review logs in `zoom_manager/logs/` for troubleshooting

---

**⚠️ Important**: This tool requires proper API credentials and permissions. Always test in debug mode before running on production recordings.
