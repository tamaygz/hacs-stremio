# Architecture Overview

This document describes the architecture of the Stremio HACS Integration.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Home Assistant                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌─────────────────────────────────────────┐   │
│  │   Lovelace   │    │           Stremio Integration           │   │
│  │     UI       │    │                                         │   │
│  │              │    │  ┌─────────────────────────────────┐   │   │
│  │ ┌──────────┐ │    │  │      DataUpdateCoordinator      │   │   │
│  │ │  Player  │ │◄───┼──│  - Centralized data fetching    │   │   │
│  │ │   Card   │ │    │  │  - Update interval management   │   │   │
│  │ └──────────┘ │    │  │  - State caching               │   │   │
│  │              │    │  └───────────────┬─────────────────┘   │   │
│  │ ┌──────────┐ │    │                  │                      │   │
│  │ │ Library  │ │    │  ┌───────────────▼─────────────────┐   │   │
│  │ │   Card   │ │    │  │         StremioClient           │   │   │
│  │ └──────────┘ │    │  │  - API authentication           │   │   │
│  │              │    │  │  - Library management           │   │   │
│  │ ┌──────────┐ │    │  │  - Playback tracking            │   │   │
│  │ │  Media   │ │    │  └───────────────┬─────────────────┘   │   │
│  │ │ Details  │ │    │                  │                      │   │
│  │ └──────────┘ │    │                  ▼                      │   │
│  └──────────────┘    │         ┌────────────────┐              │   │
│                      │         │  Stremio API   │              │   │
│  ┌──────────────────┐│         │  (External)    │              │   │
│  │     Entities     ││         └────────────────┘              │   │
│  │                  ││                                         │   │
│  │ • Sensors        ││                                         │   │
│  │ • Binary Sensors ││                                         │   │
│  │ • Media Player   ││                                         │   │
│  └──────────────────┘│                                         │   │
│                      └─────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

```
custom_components/stremio/
│
├── __init__.py            ─────► Integration Setup & Lifecycle
│                                 - async_setup_entry()
│                                 - async_unload_entry()
│                                 - Platform forwarding
│
├── config_flow.py         ─────► Configuration UI
│                                 - User authentication flow
│                                 - Options flow
│                                 - Validation
│
├── coordinator.py         ─────► Data Coordination
│                                 - StremioDataUpdateCoordinator
│                                 - Centralized API polling
│                                 - Data transformation
│
├── stremio_client.py      ─────► API Client
│                                 - Authentication
│                                 - HTTP requests
│                                 - Response parsing
│
├── sensor.py              ─────► Sensor Entities
│                                 - Library count
│                                 - Continue watching count
│                                 - Current media
│                                 - Last watched
│
├── binary_sensor.py       ─────► Binary Sensor Entities
│                                 - Is playing
│                                 - Has new content
│
├── media_player.py        ─────► Media Player Entity
│                                 - Playback state
│                                 - Media metadata
│                                 - Transport controls
│
├── services.py            ─────► Service Handlers
│                                 - search_library
│                                 - get_stream_url
│                                 - add_to_library
│                                 - handover_to_apple_tv
│
├── media_source.py        ─────► Media Browser Integration
│                                 - Browse library
│                                 - Media resolution
│
├── const.py               ─────► Constants & Configuration
│                                 - Domain, platforms
│                                 - Default values
│                                 - Entity keys
│
└── www/                   ─────► Frontend Cards (Lovelace)
    ├── stremio-player-card.js
    ├── stremio-library-card.js
    └── stremio-media-details-card.js
```

---

## Data Flow

### 1. Initialization Flow

```
User adds integration
        │
        ▼
┌───────────────────┐
│   Config Flow     │
│   (config_flow.py)│
└─────────┬─────────┘
          │ Credentials
          ▼
┌───────────────────┐
│  StremioClient    │
│  - Authenticate   │
└─────────┬─────────┘
          │ Success
          ▼
┌───────────────────┐
│  Create Entry     │
│  - Store config   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  async_setup_entry│
│  (__init__.py)    │
└─────────┬─────────┘
          │
          ├─────────────────────────────┐
          ▼                             ▼
┌───────────────────┐    ┌─────────────────────────┐
│  Create           │    │  Forward Platform Setup │
│  Coordinator      │    │  - sensor               │
└─────────┬─────────┘    │  - binary_sensor        │
          │              │  - media_player         │
          │              └─────────────────────────┘
          ▼
┌───────────────────┐
│  Initial Refresh  │
│  - Fetch all data │
└───────────────────┘
```

### 2. Data Update Flow

```
┌─────────────────────────────────────────┐
│        DataUpdateCoordinator            │
│                                         │
│  Update Interval Timer (e.g., 30 sec)   │
│              │                          │
│              ▼                          │
│  ┌─────────────────────────────────┐   │
│  │     _async_update_data()        │   │
│  │                                 │   │
│  │  1. client.get_library()        │   │
│  │  2. client.get_continue_watching│   │
│  │  3. client.get_current_playback │   │
│  │  4. Transform & cache data      │   │
│  └─────────────┬───────────────────┘   │
│                │                        │
│                ▼                        │
│  ┌─────────────────────────────────┐   │
│  │    Notify Listeners             │   │
│  │    (All entities subscribed)    │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────────┐
│ Sensor │  │ Binary │  │   Media    │
│        │  │ Sensor │  │   Player   │
└────────┘  └────────┘  └────────────┘
    │            │            │
    └────────────┴────────────┘
                 │
                 ▼
         ┌─────────────┐
         │  State      │
         │  Machine    │
         │  Update     │
         └─────────────┘
                 │
                 ▼
         ┌─────────────┐
         │  Lovelace   │
         │  UI Update  │
         └─────────────┘
```

### 3. Event Flow

```
Stremio API reports playback change
              │
              ▼
     ┌────────────────┐
     │  Coordinator   │
     │  detects       │
     │  state change  │
     └───────┬────────┘
             │
             ├──────────────────┐
             ▼                  ▼
    ┌────────────────┐  ┌──────────────────┐
    │ Update Entity  │  │ Fire HA Event    │
    │ State          │  │                  │
    └────────────────┘  │ stremio_playback │
                        │ _started/stopped │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │   Automations    │
                        │   listening for  │
                        │   event trigger  │
                        └──────────────────┘
```

---

## Key Files & Responsibilities

### `__init__.py`
- Entry point for the integration
- Sets up coordinator and forwards to platforms
- Handles unload/reload
- Registers services

### `coordinator.py`
- **`StremioDataUpdateCoordinator`**: Inherits from `DataUpdateCoordinator`
- Single source of truth for all Stremio data
- Manages update intervals and error handling
- Transforms raw API data into entity-friendly format

### `stremio_client.py`
- **`StremioClient`**: Async API client
- Handles authentication (login/token refresh)
- Provides methods: `get_library()`, `get_streams()`, `search()`, etc.
- Error handling and retry logic

### `sensor.py`
- Multiple sensor entities sharing coordinator data
- **Sensors**: library_count, continue_watching_count, current_media, last_watched, watch_time
- Each sensor extracts specific data from coordinator

### `binary_sensor.py`
- Boolean state sensors
- **Binary Sensors**: is_watching, has_continue_watching, has_new_episodes
- Simple on/off based on coordinator data
- `has_new_episodes` - On when any series in continue watching has unwatched episodes

### `media_player.py`
- **`StremioMediaPlayer`**: Full media player entity
- State: playing, paused, idle
- Attributes: media_title, media_artist, media_image_url, media_duration, media_position
- Transport controls (if supported)

### `services.py`
- Custom service definitions
- **Services**:
  - `stremio.search_library`: Search user's library
  - `stremio.get_stream_url`: Get streaming URLs
  - `stremio.add_to_library`: Add item to library
  - `stremio.handover_to_apple_tv`: Send to Apple TV

---

## Frontend Architecture

### Card Components

```
www/
├── stremio-player-card.js
│   └── Shows current playback with poster, progress, controls
│
├── stremio-library-card.js
│   └── Grid/list view of library items
│       └── Click to show details or play
│
└── stremio-media-details-card.js
    └── Detailed view of selected media
        └── Synopsis, cast, ratings, actions
```

### Card Registration

Cards auto-register via `customElements.define()`:
```javascript
customElements.define('stremio-player-card', StremioPlayerCard);
```

Home Assistant discovers them via `customCards` array:
```javascript
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'stremio-player-card',
  name: 'Stremio Player Card',
  description: 'Shows current Stremio playback',
});
```

---

## External Dependencies

| Dependency | Purpose |
|------------|---------|
| `stremio-api` | Python library for Stremio API communication |
| `aiohttp` | Async HTTP client (via Home Assistant) |
| `homeassistant` | Core HA framework |

---

## Configuration Storage

```yaml
# .storage/core.config_entries
{
  "data": {
    "entries": [
      {
        "domain": "stremio",
        "data": {
          "email": "user@example.com",
          "auth_token": "...",  # Encrypted
        },
        "options": {
          "scan_interval": 30,
          "enable_handover": true,
        }
      }
    ]
  }
}
```

---

## Error Handling

```
API Error
    │
    ▼
┌─────────────────────┐
│ StremioClient       │
│ catches exception   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Coordinator         │
│ UpdateFailed raised │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Exponential backoff │
│ Retry logic         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Entity state:       │
│ "unavailable"       │
└─────────────────────┘
```

---

## Security Considerations

1. **Credentials**: Stored encrypted in HA's `.storage/`
2. **API Tokens**: Refreshed automatically, never logged
3. **HTTPS**: All API communication over TLS
4. **No secrets in code**: Use `secrets.yaml` for testing
