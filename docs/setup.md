# Stremio Home Assistant Integration - Setup Guide

> **Development Environment?** If you're running Home Assistant Core in a development container and don't see the Add-ons menu or HACS, see [Development Environment Setup](dev-environment-hacs.md) for specific instructions.

## Prerequisites

- Home Assistant 2025.1 or later
- HACS (Home Assistant Community Store) installed
- Stremio account with valid credentials

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

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Stremio"**
4. Enter your Stremio credentials:
   - **Email**: Your Stremio account email
   - **Password**: Your Stremio account password
5. Click **"Submit"**

### Configuration Options

After initial setup, you can configure options:

1. Go to **Settings** → **Devices & Services**
2. Find **Stremio** integration
3. Click **"Configure"**

Available options:

| Option | Default | Description |
|--------|---------|-------------|
| Player Update Interval | 30s | How often to check playback state |
| Library Update Interval | 300s | How often to sync library |
| Enable Apple TV Handover | Off | Enable AirPlay/VLC handover feature |
| Handover Method | Auto | Choose AirPlay, VLC, or Auto |

## Entities Created

After setup, the following entities are created:

### Sensors
- `sensor.stremio_current_media` - Currently playing media
- `sensor.stremio_last_watched` - Last watched media
- `sensor.stremio_library_count` - Total library items
- `sensor.stremio_continue_watching_count` - Items in progress

### Binary Sensors
- `binary_sensor.stremio_is_playing` - On when media is playing
- `binary_sensor.stremio_has_new_content` - On when new content detected

### Media Player
- `media_player.stremio` - Stremio media player entity

## Verification

After setup, verify the integration is working:

1. Check that all entities are available in **Developer Tools** → **States**
2. Open the **Media Browser** panel and look for "Stremio"
3. Check for any errors in **Settings** → **System** → **Logs**

## Custom Lovelace Cards

The integration includes custom Lovelace cards that are automatically registered:

- `stremio-player-card` - Current playback display
- `stremio-library-card` - Library browser
- `stremio-media-details-card` - Detailed media information

See [UI Guide](ui.md) for card configuration.

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues and solutions.

## Next Steps

- Read the [Configuration Guide](configuration.md) for detailed options
- Check the [Services Guide](services.md) for automation capabilities
- View the [Events Guide](events.md) for automation triggers
