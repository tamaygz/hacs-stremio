# Stremio Home Assistant Integration - Setup Guide

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the repository URL: `https://github.com/tamaygz/hacs-stremio`
6. Select category "Integration"
7. Click "Add"
8. Find "Stremio" in the integration list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the files
3. Copy the `custom_components/stremio` folder to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Stremio"
4. Enter your Stremio credentials:
   - Email
   - Password
5. Click "Submit"

## Verification

After setup, you should see:
- Stremio integration in your integrations list
- Multiple sensor entities created
- Media player entity created

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues and solutions.
