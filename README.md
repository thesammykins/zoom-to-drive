# 🎥 Zoom to Drive Recording Manager

> *Automate your Zoom recording to Google Drive workflow with ease!*

> ⚡ **AI-Assisted Development**: This application was developed with the assistance of Large Language Models (LLMs) to enhance code quality and documentation. While this has helped create robust and efficient code, please review and test thoroughly for your specific use case.

This application streamlines the process of managing Zoom recordings by automating downloads, organization, and Google Drive uploads. Built with the assistance of AI/LLMs to ensure efficient and reliable performance! 🚀

## ✨ Features

- 📥 Downloads Zoom recordings based on meeting name and user email
- 🎯 Supports video, audio, transcript, and chat file downloads
- ⏱️ Automatically filters out recordings shorter than 5 minutes
- 📁 Organizes files by date in Google Drive
- 💬 Sends notifications to Slack when videos are uploaded
- 📊 Includes progress bars for download and upload operations
- 🧹 Automatically cleans up local downloads after successful upload

## 🔧 Prerequisites

- Python 3.8 or higher
- pip (if not already installed, follow the instructions [here](https://pip.pypa.io/en/stable/installation/))
- Zoom OAuth 2.0 credentials ([official documentation](https://marketplace.zoom.us/docs/guides/auth/oauth/))
- Google Drive API credentials ([official documentation](https://developers.google.com/drive/api/v3/quickstart/python))
- Slack webhook URL (optional)

## 🚀 Installation

### Option 1: Automated Setup (Recommended)

Use the provided setup script for automatic environment configuration:

```bash
git clone https://github.com/thesammykins/zoom-to-drive.git
cd zoom-to-drive
./run_zoom_manager.sh --setup-only
```

### Option 2: Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/thesammykins/zoom-to-drive.git
cd zoom-to-drive
```

2. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the package:
```bash
pip install -e .
```

4. Install and configure rclone:
```bash
# Install rclone (macOS)
brew install rclone

# Configure rclone for Google Drive
rclone config
```

5. Set up credentials:
    - Copy `zoom_manager/env_example` to `.env`
    - Configure your credentials (see Configuration section below)

## 📁 Project Structure

## ⚙️ Configuration

1. Create required directories:
```bash
mkdir -p logs downloads credentials
```

2. Configure `.env` file:
   - Never commit this file (it should be in .gitignore)
   - Fill in your actual credentials:
```bash
ZOOM_CLIENT_ID=your_actual_client_id
ZOOM_CLIENT_SECRET=your_actual_client_secret
ZOOM_ACCOUNT_ID=your_actual_account_id
GOOGLE_SHARED_DRIVE_ID=your_drive_id
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
SLACK_WEBHOOK_URL=your_webhook_url  # Optional
DEBUG=false
```

## 🎮 Usage

Run the script from the root directory:
```bash
python zoom_manager.src.main.py --name "Meeting Name" --email "user@example.com" --days 7
```

Arguments:
- `--name`: Target recording name to search for (required)
- `--email`: Email of the Zoom user (required)
- `--days`: Number of days to search (default: 7)
- `--drive-id`: Google Drive folder ID (optional, overrides environment variable)
- `--shared-id`: Google Shared Drive ID (optional, overrides environment variable)

## 📝 Logging

Log levels are controlled by the DEBUG environment variable:
- With `DEBUG=true`:
  - Detailed API responses
  - Download progress
  - File operations
  - No downloads are made
- With `DEBUG=false`:
  - Important operations
  - Errors and warnings
  - Final status
  - Downloads are made

Logs are stored in:
- `./logs/zoom_manager.log` (main log file)
- `./logs/error.log` (error-only logs)

## ⚠️ Error Handling

The application includes comprehensive error handling for:
- API authentication
- Download failures
- Upload issues
- File system operations

## 🔧 Common Errors and Troubleshooting

### Error: "Authentication failed"
- Ensure that your Zoom OAuth 2.0 and Google Drive API credentials are correct.
- Verify that the `GOOGLE_SERVICE_ACCOUNT_KEY` is set correctly in the `.env` file.

### Error: "Failed to get access token"
- Check your Zoom OAuth 2.0 credentials in the `.env` file.
- Ensure that your Zoom account has the necessary permissions.

### Error: "Failed to upload file"
- Verify that your Google Drive API credentials are correct.
- Check the internet connection and retry the operation.

For more detailed logs, enable debug mode by setting `DEBUG=true` in the `.env` file.

## 💡 Support

For issues and questions, please open an issue in the [GitHub repository](https://github.com/thesammykins/zoom-to-gdrive/issues).

## 📜 License

Copyright (c) 2024, thesammykins
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

