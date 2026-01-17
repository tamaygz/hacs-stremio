#!/usr/bin/env bash
# Install HACS (Home Assistant Community Store)
# This script downloads and installs the latest HACS release

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CHECK="✅"
CROSS="❌"
ARROW="➡️"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"
HACS_DIR="$CONFIG_DIR/custom_components/hacs"

print_status() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_step() {
    echo -e "${BLUE}${ARROW} $1${NC}"
}

# Check if HACS is already installed
if [ -d "$HACS_DIR" ] && [ -f "$HACS_DIR/manifest.json" ]; then
    HACS_VERSION=$(python3 -c "import json; print(json.load(open('$HACS_DIR/manifest.json')).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
    print_status "HACS is already installed (version: $HACS_VERSION)"
    
    # Check for --force flag
    if [ "$1" != "--force" ]; then
        echo -e "  Use ${YELLOW}--force${NC} to reinstall"
        exit 0
    fi
    
    print_step "Reinstalling HACS..."
    rm -rf "$HACS_DIR"
fi

# Create custom_components directory if it doesn't exist
mkdir -p "$CONFIG_DIR/custom_components"

# Temporary directory for download
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

print_step "Fetching latest HACS release information..."

# Get latest release info from GitHub API
RELEASE_INFO=$(curl -s "https://api.github.com/repos/hacs/integration/releases/latest")

if [ -z "$RELEASE_INFO" ] || echo "$RELEASE_INFO" | grep -q "API rate limit"; then
    print_error "Failed to fetch HACS release info (API rate limit or network error)"
    print_step "Trying alternative method..."
    
    # Fallback: Use the official HACS install script method
    DOWNLOAD_URL="https://github.com/hacs/integration/releases/latest/download/hacs.zip"
else
    # Extract download URL for hacs.zip using Python for cross-platform compatibility
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | python3 -c "import sys, json; data = json.load(sys.stdin); assets = data.get('assets', []); urls = [a['browser_download_url'] for a in assets if 'hacs.zip' in a['browser_download_url']]; print(urls[0] if urls else '')" 2>/dev/null)
    HACS_VERSION=$(echo "$RELEASE_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tag_name', ''))" 2>/dev/null)
    
    if [ -z "$DOWNLOAD_URL" ]; then
        print_step "Could not parse release info, using direct download URL..."
        DOWNLOAD_URL="https://github.com/hacs/integration/releases/latest/download/hacs.zip"
    else
        echo -e "  Latest version: ${GREEN}$HACS_VERSION${NC}"
    fi
fi

print_step "Downloading HACS..."
HACS_ZIP="$TEMP_DIR/hacs.zip"

if ! curl -sL "$DOWNLOAD_URL" -o "$HACS_ZIP"; then
    print_error "Failed to download HACS"
    exit 1
fi

# Verify the download
if [ ! -f "$HACS_ZIP" ] || [ ! -s "$HACS_ZIP" ]; then
    print_error "Downloaded file is empty or missing"
    exit 1
fi

print_step "Extracting HACS..."

# Create HACS directory and extract
mkdir -p "$HACS_DIR"

if ! unzip -q "$HACS_ZIP" -d "$HACS_DIR"; then
    print_error "Failed to extract HACS"
    rm -rf "$HACS_DIR"
    exit 1
fi

# Verify installation
if [ -f "$HACS_DIR/manifest.json" ]; then
    INSTALLED_VERSION=$(python3 -c "import json; print(json.load(open('$HACS_DIR/manifest.json')).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
    print_status "HACS installed successfully (version: $INSTALLED_VERSION)"
else
    print_error "HACS installation verification failed - manifest.json not found"
    exit 1
fi

echo ""
echo -e "HACS has been installed to: ${BLUE}$HACS_DIR${NC}"
echo -e "After starting Home Assistant, complete HACS setup at: ${BLUE}Settings → Integrations → + Add Integration → HACS${NC}"
