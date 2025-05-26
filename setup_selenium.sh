#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Update package lists and install necessary packages
sudo apt-get update
sudo apt-get install -y wget unzip jq

# Install Google Chrome
echo "Installing Google Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Get installed Chrome version
CHROME_VERSION_FULL=$(google-chrome --version | cut -d ' ' -f3) # e.g., 120.0.6099.71
CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION_FULL" | cut -d '.' -f1) # e.g., 120
echo "Installed Chrome version: $CHROME_VERSION_FULL (Major: $CHROME_MAJOR_VERSION)"

# Determine ChromeDriver version using Chrome for Testing (CfT) JSON endpoints
echo "Determining appropriate ChromeDriver version using CfT JSON..."
CHROMEDRIVER_URL=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | \
    jq -r --arg MAJOR_VERSION "$CHROME_MAJOR_VERSION" \
    '.versions[] | select(.version | startswith($MAJOR_VERSION + ".")) | .downloads.chromedriver // [] | .[] | select(.platform=="linux64") | .url' | \
    sort -V | tail -n 1)

if [ -z "$CHROMEDRIVER_URL" ]; then
    echo "Could not find ChromeDriver URL for Chrome major version $CHROME_MAJOR_VERSION using primary CfT endpoint."
    echo "Attempting deprecated LATEST_RELEASE for $CHROME_MAJOR_VERSION..."
    CHROMEDRIVER_VERSION_TO_DOWNLOAD=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}")
    if [ -n "$CHROMEDRIVER_VERSION_TO_DOWNLOAD" ] && [[ "$CHROMEDRIVER_VERSION_TO_DOWNLOAD" != *"Error"* ]]; then # Basic check for error in response
        echo "Found ChromeDriver version $CHROMEDRIVER_VERSION_TO_DOWNLOAD using deprecated LATEST_RELEASE endpoint."
        CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION_TO_DOWNLOAD}/chromedriver_linux64.zip"
    else
        echo "Failed to find ChromeDriver using all methods. Please check Chrome and ChromeDriver availability manually."
        exit 1
    fi
fi

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"
wget -qN "$CHROMEDRIVER_URL" -P ~/
ARCHIVE_NAME=$(basename "$CHROMEDRIVER_URL") # Should be chromedriver-linux64.zip or similar
DOWNLOADED_ZIP_PATH=~/"$ARCHIVE_NAME"

echo "Unzipping $DOWNLOADED_ZIP_PATH..."
unzip -o "$DOWNLOADED_ZIP_PATH" -d ~/

# ChromeDriver zips (e.g., chromedriver-linux64.zip) create a directory like 'chromedriver-linux64'
UNZIPPED_DIR_NAME=$(echo "$ARCHIVE_NAME" | sed 's/\.zip$//') # e.g., chromedriver-linux64

if [ -f ~/"$UNZIPPED_DIR_NAME"/chromedriver ]; then
    echo "Found chromedriver in ~/$UNZIPPED_DIR_NAME"
    sudo mv ~/"$UNZIPPED_DIR_NAME"/chromedriver /usr/local/bin/chromedriver
    rm -r ~/"$UNZIPPED_DIR_NAME"
elif [ -f ~/chromedriver ]; then # Fallback if chromedriver is directly in the zip (less common for current CfT zips)
    echo "Found chromedriver directly in ~/"
    sudo mv ~/chromedriver /usr/local/bin/chromedriver
else
    echo "ChromeDriver executable not found in expected locations (~/$UNZIPPED_DIR_NAME/ or ~/) after unzipping."
    echo "Contents of ~/: "
    ls -la ~/
    if [ -d ~/"$UNZIPPED_DIR_NAME" ]; then
        echo "Contents of ~/$UNZIPPED_DIR_NAME/:"
        ls -la ~/"$UNZIPPED_DIR_NAME"/
    fi
    exit 1
fi

echo "Removing $DOWNLOADED_ZIP_PATH..."
rm "$DOWNLOADED_ZIP_PATH"
sudo chmod +x /usr/local/bin/chromedriver

# List versions
echo "--- Installed versions ---"
google-chrome --version
chromedriver --version
echo "--------------------------"

# Install Python packages
echo "Installing Python packages from requirements.txt..."
pip install -r requirements.txt

echo "Setup complete."
echo "To use Selenium with Chrome in Python, ensure ChromeDriver is in your PATH."
echo "If you encounter issues, you might need to manually specify the ChromeDriver path when instantiating the WebDriver."
