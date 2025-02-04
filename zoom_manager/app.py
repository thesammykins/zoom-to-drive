from flask import Flask, render_template, request, redirect, url_for, flash
from config import settings
import threading
import logging

app = Flask(__name__)
app.secret_key = 'replace-this-secret-key'  # Use a secure random key in production

# Function that wraps the entire workflow:
def process_zoom_to_drive():
    # ...existing code or function call that:
    # 1. Authenticates to Zoom and Google Drive,
    # 2. Fetches meeting recordings (optionally by date range),
    # 3. Downloads recordings locally,
    # 4. Uploads them to Google Drive,
    # 5. Optionally sends a Slack notification.
    logging.info("Starting process to download Zoom recordings and upload to Google Drive.")
    # Placeholder for the actual processing logic:
    # download_and_upload_recordings()
    logging.info("Process completed.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_process():
    # Run the long task in a background thread so the UI remains responsive.
    thread = threading.Thread(target=process_zoom_to_drive)
    thread.start()
    flash("Process started. Check logs for progress.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    if settings.DEBUG:
        app.run(debug=True)
    else:
        app.run()
