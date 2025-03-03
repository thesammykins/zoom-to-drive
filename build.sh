#!/bin/bash

# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create application icon
echo "Creating application icon..."
python zoom_manager/src/create_icon.py

# Build the application
echo "Building application..."
pyinstaller zoom_manager.spec

# Create zip file for release
echo "Creating release package..."
cd dist
zip -r "Zoom to Drive.app.zip" "Zoom to Drive.app"
cd ..

echo "Build complete! Application is available in dist/Zoom to Drive.app"
echo "Release package is available in dist/Zoom to Drive.app.zip" 