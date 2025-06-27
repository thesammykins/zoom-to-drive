#!/bin/bash

# run_zoom_manager.sh - Script to set up environment and run the Zoom recording manager
# 
# This script:
# 1. Creates a Python virtual environment if needed
# 2. Installs requirements from requirements.txt
# 3. Installs the zoom_manager module
# 4. Verifies rclone installation and configuration
# 5. Runs the zoom manager with specified parameters

set -e  # Exit immediately if a command exits with a non-zero status

DEFAULT_NAME="Demo + Shoutouts + Q&A"
DEFAULT_EMAIL="xavier.shay@ferocia.com.au"
DEFAULT_DAYS=5
VENV_DIR="venv"

# Default rclone settings (override via --rclone-remote / --rclone-base-path)
DEFAULT_RCLONE_REMOTE=""
DEFAULT_RCLONE_BASE_PATH=""

# Initialize variables with defaults
rclone_remote="$DEFAULT_RCLONE_REMOTE"
rclone_base_path="$DEFAULT_RCLONE_BASE_PATH"
name="$DEFAULT_NAME"
email="$DEFAULT_EMAIL"
days="$DEFAULT_DAYS"
no_slack=false
setup_only=false

# Display help message
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -n, --name NAME         Specify the recording name (default: \"$DEFAULT_NAME\")"
    echo "  -e, --email EMAIL       Specify the email address (default: \"$DEFAULT_EMAIL\")"
    echo "  -d, --days DAYS         Specify the number of days to search (default: $DEFAULT_DAYS)"
    echo "  --no-slack              Disable Slack notifications"
    echo "  -s, --setup-only        Only set up the environment, don't run the zoom manager"
    echo "  --rclone-remote REMOTE  Override RCLONE_REMOTE_NAME"
    echo "  --rclone-base-path PATH Override RCLONE_BASE_PATH"
    echo "  -h, --help              Display this help message and exit"
    echo
    echo "Example:"
    echo "  $0 --name \"Meeting Recording\" --email \"user@example.com\" --days 7 --no-slack"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--name)
            name="$2"
            shift 2
            ;;
        -e|--email)
            email="$2"
            shift 2
            ;;
        -d|--days)
            days="$2"
            shift 2
            ;;
        --no-slack)
            no_slack=true
            shift
            ;;
        --rclone-remote)
            rclone_remote="$2"
            shift 2
            ;;
        --rclone-base-path)
            rclone_base_path="$2"
            shift 2
            ;;
        -s|--setup-only)
            setup_only=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to verify rclone installation and configuration
verify_rclone_setup() {
    echo "=== Verifying rclone setup ==="
    
    # Check if rclone is installed
    if ! command -v rclone &> /dev/null; then
        echo "Error: rclone is not installed. Please install rclone and try again."
        echo "Install rclone from: https://rclone.org/downloads/"
        exit 1
    fi
    
    echo "rclone is installed: $(rclone version | head -n 1)"
    
    # Load RCLONE_REMOTE_NAME from .env using python-dotenv to handle special characters
    if [ -f ".env" ]; then
        eval "$(python3 - <<-PYCODE
import os
from dotenv import load_dotenv
load_dotenv()
val = os.getenv('RCLONE_REMOTE_NAME')
if val:
    print(f'export RCLONE_REMOTE_NAME="{val}"')
PYCODE
)"
    fi
    
    # Check if RCLONE_REMOTE_NAME is set
    if [ -z "$RCLONE_REMOTE_NAME" ]; then
        echo "Warning: RCLONE_REMOTE_NAME not set in .env file"
        echo "Using default remote name: recordingdrive"
        RCLONE_REMOTE_NAME="recordingdrive"
    fi
    
    # Check if the rclone remote is configured
    if ! rclone listremotes | grep -q "^${RCLONE_REMOTE_NAME}:"; then
        echo "Error: rclone remote '${RCLONE_REMOTE_NAME}' is not configured."
        echo "Please configure your Google Drive remote with:"
        echo "  rclone config"
        echo "Or run the test script first:"
        echo "  python3 test_rclone.py"
        exit 1
    fi
    
    echo "rclone remote '${RCLONE_REMOTE_NAME}' is configured"
    echo "rclone setup verification complete!"
    echo
}

# Function to set up the Python environment
setup_environment() {
    echo "=== Setting up Python environment ==="
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment in $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    else
        echo "Virtual environment already exists in $VENV_DIR"
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        echo "Warning: requirements.txt not found. Skipping dependency installation."
    fi
    
    # Install zoom_manager module in development mode
    echo "Installing zoom_manager module..."
    pip install -e .
    
    echo "Environment setup complete!"
    echo
}

# Set up the environment
setup_environment

# Export any rclone overrides
if [ -n "$rclone_remote" ]; then
    export RCLONE_REMOTE_NAME="$rclone_remote"
fi
if [ -n "$rclone_base_path" ]; then
    export RCLONE_BASE_PATH="$rclone_base_path"
fi

# Verify rclone setup
verify_rclone_setup

# If setup_only flag is set, exit here
if [ "$setup_only" = true ]; then
    echo "Setup completed. Exiting without running zoom manager."
    exit 0
fi

# Display the parameters being used
echo "=== Running Zoom Manager ==="
echo "Starting Zoom manager with the following parameters:"
echo "  Name: $name"
echo "  Email: $email"
echo "  Days: $days"
if [ "$no_slack" = true ]; then
    echo "  Slack notifications: Disabled"
fi
echo "  Upload method: rclone (Google Drive)"
echo

# Make sure we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    source "$VENV_DIR/bin/activate"
fi

# Build the command with optional parameters
cmd="python3 zoom_manager/src/main.py --name \"$name\" --email \"$email\" --days \"$days\""

if [ "$no_slack" = true ]; then
    cmd="$cmd --no-slack"
fi

# Run the Python script with the specified parameters
eval "$cmd"

# Exit with the same status as the Python script
exit $?

