# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.
``

Repository: zoom_to_drive (Python)
Purpose: Fetch Zoom cloud recordings for a given user and meeting name, download to zoom_manager/downloads/YYYY-MM-DD, upload to Google Drive via rclone, optionally send a Slack notification, then clean up.

Common commands (macOS + zsh)

Environment setup
- Check Python:
  - python3 --version
- Create and activate venv:
  - python3 -m venv .venv
  - source .venv/bin/activate
- Install dependencies:
  - python3 -m pip install --upgrade pip
  - python3 -m pip install -r zoom_manager/requirements.txt
- Environment variables: copy the template and fill placeholders (never commit secrets):
  - cp zoom_manager/env_example .env
  - $EDITOR .env

Run the CLI
- Show help:
  - python3 zoom_manager/src/main.py --help
- Typical run (required flags shown):
  - python3 zoom_manager/src/main.py \
      --name "Weekly Sync" \
      --email user@example.com \
      --days 14 \
      [--no-slack] [--slack-webhook https://hooks.slack.com/services/…]
- Debug mode (more verbose logging and mock download behavior in Zoom client):
  - DEBUG=1 python3 zoom_manager/src/main.py --name "Weekly Sync" --email user@example.com

rclone prerequisites and checks
- Ensure rclone is installed and the target remote is configured:
  - rclone version
  - rclone listremotes
- This app reads these env vars (see rclone_client.py and settings.py):
  - RCLONE_REMOTE_NAME (e.g., drive)
  - RCLONE_BASE_PATH  (e.g., Zoom/Recordings)
- Sanity checks before running uploads:
  - echo "$RCLONE_REMOTE_NAME" && echo "$RCLONE_BASE_PATH"
  - rclone lsd "$RCLONE_REMOTE_NAME:"
  - rclone lsjson "$RCLONE_REMOTE_NAME:$RCLONE_BASE_PATH" --recursive --fast-list | head -n 20

Logs and artifacts
- Logs: zoom_manager/logs/zoom_manager_YYYYMMDD.log
  - tail -F zoom_manager/logs/zoom_manager_*.log
- Downloads: zoom_manager/downloads/YYYY-MM-DD/
  - Main flow: Zoom fetch → local download → rclone upload → Slack notify → cleanup local files

High-level architecture
- Orchestrator (zoom_manager/src/main.py)
  - Parses CLI args: --name (meeting/topic substring), --email (Zoom user), --days (date range), Slack flags
  - Pipeline: resolve Zoom user → list recordings (date filtered) → filter by name → download files (skip if <5 minutes) → rclone upload directory → optional Slack notification (per .mp4) → cleanup local downloads
  - Logging setup uses settings.LOG_FILE and formatters; respects DEBUG for verbosity

- Zoom client (zoom_manager/src/zoom_client.py)
  - OAuth: obtains access_token via Zoom “account_credentials” grant using ZOOM_CLIENT_ID/SECRET and ZOOM_ACCOUNT_ID
  - get_user_by_email(email) → user JSON; get_recordings(user_id, from/to) → recordings JSON
  - process_recording(recording, meeting_name): determines Melbourne-local timestamps, groups files by type, maps file types to extensions, builds filenames, downloads with progress (tqdm). In DEBUG, download_recording returns False (no network fetch)
  - get_actual_duration(recording): computes duration from start_time and recording_end timestamps

- rclone client (zoom_manager/src/rclone_client.py)
  - Ensures rclone binary exists and the remote RCLONE_REMOTE_NAME is configured (listremotes)
  - upload_directory(local_path, date_folder): creates remote dir and copies whole directory to "RCLONE_REMOTE_NAME:RCLONE_BASE_PATH/date_folder"
  - get_file_id(date_folder, file_name): uses rclone lsjson to extract the Drive file ID (best-effort across ID key variants)
  - check_file_exists, test_connection helpers available

- Slack client (zoom_manager/src/slack_client.py)
  - send_notification(recording_name, file_name, file_id): posts to SLACK_WEBHOOK_URL (or explicit --slack-webhook) with a Drive link
  - If no webhook configured, logs and skips

- Settings (zoom_manager/config/settings.py)
  - Loads .env (python-dotenv) and sets paths: logs/, downloads/, credentials/
  - Env: ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID, SLACK_WEBHOOK_URL, RCLONE_REMOTE_NAME, RCLONE_BASE_PATH, DEBUG
  - Google Drive API settings remain for legacy compatibility but uploads now use rclone
  - Logging: daily file in logs/, console and file formatters; LOG_LEVEL depends on DEBUG

Environment variables (placeholders; see zoom_manager/env_example)
- ZOOM_CLIENT_ID=...
- ZOOM_CLIENT_SECRET=...
- ZOOM_ACCOUNT_ID=...
- RCLONE_REMOTE_NAME=drive
- RCLONE_BASE_PATH=Zoom/Recordings
- SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
- DEBUG=0

Build, lint, tests
- No explicit build, lint, or test configuration found in this repo. If you add pytest or linters later, update this section with exact commands (e.g., pytest -q, running a single test, etc.).

Notes on repo docs
- No CLAUDE.md, AGENT.md/AGENTS.md, Cursor rules, or Copilot instructions found here.
- If a README.md is added or updated, incorporate its important, repo-specific operational details here.

