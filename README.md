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
- 🔒 Secure credential storage with encryption
- 🖥️ Native macOS application with modern UI
- 🚀 Optimized for high-speed transfers

## 🔧 Prerequisites

- macOS 10.13 or higher
- Zoom OAuth 2.0 credentials ([official documentation](https://marketplace.zoom.us/docs/guides/auth/oauth/))
- Google Drive API credentials ([official documentation](https://developers.google.com/drive/api/v3/quickstart/python))
- Slack webhook URL (optional)

## 🚀 Installation

### For End Users

1. Download the latest release from the [releases page](https://github.com/thesammykins/zoom-to-drive/releases)
2. Drag "Zoom to Drive.app" to your Applications folder
3. Create a `.env` file with your credentials (see Configuration section)
4. Launch the application from your Applications folder

### For Developers

1. Clone the repository:
```bash
git clone https://github.com/thesammykins/zoom-to-drive.git
cd zoom-to-drive
```

2. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Build the application:
```bash
pyinstaller zoom_manager.spec
```

The built application will be available in the `dist` folder.

## 🔧 Configuration

Create a `.env` file with your credentials:
```bash
ZOOM_CLIENT_ID=your_actual_client_id
ZOOM_CLIENT_SECRET=your_actual_client_secret
ZOOM_ACCOUNT_ID=your_actual_account_id
GOOGLE_SHARED_DRIVE_ID=your_drive_id
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_SERVICE_ACCOUNT_KEY=your_service_account_key
SLACK_WEBHOOK_URL=your_webhook_url  # Optional
DEBUG=false
```

When you first launch the application, you'll be prompted to select this `.env` file. The application will encrypt it for secure storage.

## 🎮 Usage

1. Launch "Zoom to Drive" from your Applications folder
2. Select your encrypted `.env` file
3. Enter the meeting name and user email
4. (Optional) Adjust the number of days to search
5. Enable debug mode if needed
6. Click "Start Transfer"

The application will show progress bars for both download and upload operations.

## 🔧 Common Errors and Troubleshooting

### Error: "Authentication failed"
- Ensure that your Zoom OAuth 2.0 and Google Drive API credentials are correct
- Verify that your `.env` file is properly formatted

### Error: "Failed to get access token"
- Check your Zoom OAuth 2.0 credentials
- Ensure that your Zoom account has the necessary permissions

### Error: "Failed to upload file"
- Verify that your Google Drive API credentials are correct
- Check your internet connection

For more detailed logs, enable debug mode in the application settings.

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

