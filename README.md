# 🎥 Zoom to Drive Recording Manager

> *Automate your Zoom recording to Google Drive workflow with ease!*

> ⚡ **AI-Assisted Development**: This application was developed with the assistance of Large Language Models (LLMs) to enhance code quality and documentation. While this has helped create robust and efficient code, please review and test thoroughly for your specific use case.

This application streamlines the process of managing Zoom recordings by automating downloads, organization, and Google Drive uploads. Built with the assistance of AI/LLMs to ensure efficient and reliable performance! 🚀

## ✨ Features

- 📥 Downloads Zoom recordings based on meeting name and user email
- 🎯 Supports video, audio, transcript, and chat file downloads
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

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up credentials:
    - Copy `.env_example` to `.env`
    - Fill in your credentials:
      - Zoom OAuth 2.0 credentials (from Zoom Marketplace)
      - Google Drive API credentials
      - Slack webhook URL (optional)
    - Store your Google Cloud service account key as a GitHub Secret

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
GOOGLE_SERVICE_ACCOUNT_KEY=your_service_account_key
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

---

## 🛠️ GitHub Actions

To automate running the application, you can set up a GitHub Action workflow. Follow these steps:

1. Create a new file in your repository at `.github/workflows/run-zoom-to-drive.yml`.

2. Add the following content to the file:

```yaml
name: Run Zoom to Drive

on:
  schedule:
    - cron: '10 0 * * 5' # Runs every Friday at 11:10am Melbourne time
  workflow_dispatch:

jobs:
  run-zoom-to-drive:
    runs-on: ubuntu-latest

    env:
      ZOOM_CLIENT_ID: ${{ secrets.ZOOM_CLIENT_ID }}
      ZOOM_CLIENT_SECRET: ${{ secrets.ZOOM_CLIENT_SECRET }}
      ZOOM_ACCOUNT_ID: ${{ secrets.ZOOM_ACCOUNT_ID }}
      GOOGLE_SHARED_DRIVE_ID: ${{ secrets.GOOGLE_SHARED_DRIVE_ID }}
      GOOGLE_DRIVE_FOLDER_ID: ${{ secrets.GOOGLE_DRIVE_FOLDER_ID }}
      GOOGLE_SERVICE_ACCOUNT_KEY: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_KEY }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
      DEBUG: 'false'

    steps:
    - name: Checkout repository
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r zoom_manager/requirements.txt

    - name: Run Zoom to Drive
      run: |
        python zoom_manager/src/main.py --name "${{ secrets.MEETING_NAME }}" --email "${{ secrets.USER_EMAIL }}" --days ${{ secrets.DAYS }}
```

3. Add your secrets to the GitHub repository:
   - Go to the repository settings.
   - Click on "Secrets and variables" > "Actions".
   - Add the following secrets:
     - `ZOOM_CLIENT_ID`
     - `ZOOM_CLIENT_SECRET`
     - `ZOOM_ACCOUNT_ID`
     - `GOOGLE_SHARED_DRIVE_ID`
     - `GOOGLE_DRIVE_FOLDER_ID`
     - `GOOGLE_SERVICE_ACCOUNT_KEY`
     - `SLACK_WEBHOOK_URL` (optional)

4. The GitHub Action will now run the script on a schedule (e.g., daily at midnight) or manually via the "Run workflow" button in the Actions tab.

## 🌐 Obtaining the GOOGLE_SERVICE_ACCOUNT_KEY

To obtain the `GOOGLE_SERVICE_ACCOUNT_KEY`, follow these steps:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing project.
3. Enable the Google Drive API for your project.
4. Create a service account:
   - Go to the "IAM & Admin" > "Service Accounts" page.
   - Click "Create Service Account".
   - Fill in the required details and click "Create".
5. Assign the necessary roles to the service account:
   - Click on the service account you created.
   - Go to the "Permissions" tab.
   - Click "Add Member" and add the roles required for accessing Google Drive (e.g., "Drive API Admin").
6. Create a key for the service account:
   - Go to the "Keys" tab.
   - Click "Add Key" > "Create New Key".
   - Select "JSON" and click "Create".
   - A JSON file containing the service account key will be downloaded to your computer.
7. Open the JSON file and copy its contents.
8. Store the contents of the JSON file as a GitHub Secret named `GOOGLE_SERVICE_ACCOUNT_KEY`.

