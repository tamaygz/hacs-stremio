# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Breaking**: Replaced `stremio-api` dependency with native aiohttp implementation
  - Resolves pydantic v2 dependency conflict with Home Assistant's pydantic v1
  - Improves compatibility and reduces external dependencies
  - All API calls now use aiohttp directly with proper error handling

## [1.0.0] - 2026-01-17

### Added

- **Initial Release** 🎉

#### Core Features

- Config flow for easy setup with Stremio credentials
- Options flow for customizing update intervals and features
- DataUpdateCoordinator for efficient API polling

#### Entities

- **Sensors**
  - Current media sensor (shows currently playing content)
  - Last watched sensor
  - Library count sensor
  - Continue watching count sensor
- **Binary Sensors**
  - Is playing binary sensor
  - Has new content binary sensor
- **Media Player**
  - Read-only media player entity with playback state

#### Services

- `stremio.search_library` - Search your library
- `stremio.get_stream_url` - Get playable stream URLs
- `stremio.add_to_library` - Add media to library
- `stremio.remove_from_library` - Remove media from library
- `stremio.refresh_library` - Force library refresh
- `stremio.handover_to_apple_tv` - Apple TV handover service

#### Events

- `stremio_playback_started` - Fired when playback begins
- `stremio_playback_stopped` - Fired when playback stops
- `stremio_new_content` - Fired when new library content detected

#### Apple TV Handover

- AirPlay handover for HLS streams
- VLC deep link fallback for other formats
- Configurable handover method (Auto/AirPlay/VLC)

#### Custom Lovelace Cards

- `stremio-player-card` - Current playback display
- `stremio-library-card` - Library browser with search
- `stremio-media-details-card` - Detailed media info
- `stremio-stream-dialog` - Stream selector dialog
- Auto-registration of cards (no manual resource setup)

#### Media Source Integration

- Browse Stremio library in HA Media Browser
- Navigate: Library → Movies/Series → Seasons → Episodes
- Direct playback from Media Browser

#### Documentation

- Comprehensive setup guide
- Configuration reference
- Services documentation
- UI/Cards guide
- Events documentation
- Example automations
- API reference
- Development guide

### Dependencies

- Home Assistant 2025.1+
- Python 3.11+
- stremio-api>=0.1.0
- pyatv>=0.14.0 (optional, for AirPlay)

---

## Future Releases

### Planned for v1.1.0

- Real-time playback control (requires Stremio API updates)
- Chromecast handover support
- Multi-account support
- Statistics dashboard card

### Planned for v1.2.0

- Jellyfin library sync
- Plex cross-platform library
- IFTTT-style recipes
- Additional language translations

---

[Unreleased]: https://github.com/tamaygz/hacs-stremio/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/tamaygz/hacs-stremio/releases/tag/v1.0.0
