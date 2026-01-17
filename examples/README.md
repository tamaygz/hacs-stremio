# Example Automations for Stremio Integration

This folder contains ready-to-use automation examples for the Stremio HACS integration.

## Quick Start

Copy any of these YAML files to your Home Assistant configuration and customize as needed.

## Available Examples

### 1. Notification Automations

- **new_content_notification.yaml**: Get notified when new content is available in your library
- **playback_notification.yaml**: Notify family members when media starts playing

### 2. Lighting Automations

- **movie_lights.yaml**: Dim lights when playback starts, restore when stopped
- **ambient_lights.yaml**: Set ambient lighting based on media type

### 3. Smart Home Automations

- **tv_power.yaml**: Auto power on TV when Stremio playback detected
- **do_not_disturb.yaml**: Enable DND mode during playback

### 4. Library Management

- **library_backup.yaml**: Weekly backup of library to file
- **watchlist_reminder.yaml**: Daily reminder of unwatched items

## Usage

1. Copy the desired YAML file
2. Paste into your `automations.yaml` or via UI
3. Customize entity IDs and settings
4. Reload automations

## Support

Report issues on GitHub: https://github.com/tamaygz/hacs-stremio/issues
