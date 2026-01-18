# Example Automations for Stremio Integration

This folder contains ready-to-use automation examples for the Stremio HACS integration.

## Quick Start

Copy any of these YAML files to your Home Assistant configuration and customize as needed.

## Available Examples

### 1. Notification Automations

- **new_content_notification.yaml**: Get notified when new content is available in your library
- **new_episode_alert.yaml**: Get notified when TV shows you're watching have new episodes
- **playback_notification.yaml**: Notify family members when media starts playing

### 2. Device Control & Resume

- **auto_resume_apple_tv.yaml**: Offer to resume your last watched content when Apple TV turns on
  - Actionable notifications with "Resume" and "Not Now" buttons
  - Optional auto-resume without confirmation
  - Multi-room support for homes with multiple Apple TVs

### 3. Lighting Automations

- **movie_lights.yaml**: Dim lights when playback starts, restore when stopped
- **ambient_lights.yaml**: Set ambient lighting based on media type

### 4. Smart Home Automations

- **tv_power.yaml**: Auto power on TV when Stremio playback detected
- **do_not_disturb.yaml**: Enable DND mode during playback

### 5. Library Management

- **library_backup.yaml**: Weekly backup of library to file
- **watchlist_reminder.yaml**: Daily reminder of unwatched items

## Events Used

These automations use Stremio integration events. See [Events Documentation](../docs/events.md) for full details.

| Event | Description |
|-------|-------------|
| `stremio_playback_started` | Fired when playback begins |
| `stremio_playback_stopped` | Fired when playback ends |
| `stremio_new_content` | Fired when library changes |
| `stremio_new_episodes_detected` | Fired when series have new episodes |
| `stremio_resume_available` | Fired when resumable content exists |

## Usage

1. Copy the desired YAML file
2. Paste into your `automations.yaml` or via UI
3. Customize entity IDs and settings
4. Reload automations

## Prerequisites

Some automations require specific configurations:

- **Mobile notifications**: Home Assistant Companion App installed
- **Apple TV automations**: Apple TV integration configured, Stremio Apple TV handover enabled
- **TTS announcements**: Text-to-speech service configured

## Support

Report issues on GitHub: https://github.com/tamaygz/hacs-stremio/issues
