#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script's directory to ensure youtube_uploader.py and its resources are found
cd "$SCRIPT_DIR"

# Execute the Python script
echo "Starting YouTube Uploader..."
python3 youtube_uploader.py

# Keep the terminal window open until the user presses Enter
echo "" # Newline for clarity
read -p "Script finished. Press [Enter] key to close this window."
