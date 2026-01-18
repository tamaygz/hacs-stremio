# Stremio HACS Integration - Project Specifications

## Overview

A Home Assistant Custom Component (HACS) integration that connects to the Stremio API to track user library, viewing activity, and media consumption. This integration provides sensors, events, and a media player entity to monitor and interact with Stremio content.

**Project Status:** Specification Phase  
**Last Updated:** January 17, 2026  
**Target HA Version:** 2025.1+  
**Python Version:** 3.12+

---

## Table of Contents

1. [Research Summary](#research-summary)
2. [Technical Architecture](#technical-architecture)
3. [Features & Entities](#features--entities)
4. [Configuration](#configuration)
5. [API Integration](#api-integration)
6. [Implementation Plan](#implementation-plan)
7. [Known Limitations](#known-limitations)
8. [Future Enhancements](#future-enhancements)

---

## Research Summary

### Stremio API Library

**Recommended Library:** [`stremio-api`](https://pypi.org/project/stremio-api/) (v0.1.0)

- **Author:** @AboveColin
- **License:** MIT
- **Features:**
  - ✨ Async functionality using `httpx`
  - 👤 User authentication and profile management
  - 📚 Library and Addon collection access
  - 📺 "Continue Watching" synchronization
  - 🎬 Metadata fetching (via Cinemeta)

**Installation:**
```bash
pip install stremio-api
```

**Basic Usage:**
```python
from stremio_api import StremioAPIClient

async with StremioAPIClient(auth_key=None) as client:
    auth_key = await client.login("email@example.com", "password")
    user = await client.get_user()
    watching = await client.get_continue_watching(limit=5)
```

### Stremio API Capabilities

**API Endpoint:** `https://api.strem.io`

**Authentication Methods:**
- Email/Password login
- Apple Sign-In authentication
- Persistent auth key (stored after login)

**Available Data:**
- User profile (email, name, user ID)
- Library items (movies, series, added content)
- Continue Watching list with progress
- Watch time statistics
- Addon collection
- Item metadata (via Cinemeta)

### Existing Reference Implementation

[@AboveColin's stremio-ha](https://github.com/AboveColin/stremio-ha) provides a working example with:
- Config flow authentication
- Media player entity
- Multiple sensor types
- Media source browser
- Stream fetching service

---

## Technical Architecture

### Component Structure

```
custom_components/stremio/
├── __init__.py              # Component initialization & setup
├── manifest.json            # Integration metadata
├── config_flow.py           # Config & options flow handlers
├── const.py                 # Constants and defaults
├── coordinator.py           # DataUpdateCoordinator for API polling
├── api.py                   # Stremio API wrapper/client
├── sensor.py                # Sensor entities
├── binary_sensor.py         # Binary sensor entities
├── media_player.py          # Media player entity
├── services.yaml            # Service definitions
└── translations/
    └── en.json              # English translations
```

### Data Flow Architecture

```
┌─────────────────┐
│  Home Assistant │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Config  │
    │  Flow   │
    └────┬────┘
         │ (auth credentials)
         │
    ┌────▼────────────┐
    │  Coordinator    │◄──── Polling (60s interval)
    │ (API Manager)   │
    └────┬────────────┘
         │
    ┌────▼──────────┐
    │  stremio-api  │
    │    Client     │
    └────┬──────────┘
         │
    ┌────▼────────────┐
    │ Stremio API     │
    │ api.strem.io    │
    └─────────────────┘
```

### Coordinator Pattern

**DataUpdateCoordinator** polls the Stremio API at regular intervals (default: 60 seconds) and provides coordinated updates to all entities:

```python
class StremioDataUpdateCoordinator(DataUpdateCoordinator):
    """Manage fetching Stremio data."""
    
    async def _async_update_data(self):
        """Fetch data from Stremio API."""
        return {
            "user": await self.client.get_user(),
            "library": await self.client.get_library(),
            "continue_watching": await self.client.get_continue_watching(),
            "addons": await self.client.get_addons(),
        }
```

---

## Features & Entities

### 1. Config Flow Setup

**Initial Configuration:**
- User enters Stremio email and password
- Integration authenticates and retrieves auth key
- Auth key is stored securely in config entry
- Device registration via API (if supported)

**Options Flow:**
- Update polling interval (30s - 300s)
- Toggle specific sensors on/off
- Configure notification preferences
- Re-authenticate if needed

### 2. Sensors

#### 2.1 User Profile Sensor
```yaml
sensor.stremio_user
  state: "user_display_name"
  attributes:
    email: "user@example.com"
    user_id: "abc123xyz"
    premium: false
    avatar: "https://..."
```

#### 2.2 Library Statistics Sensor
```yaml
sensor.stremio_library
  state: 150  # Total items
  attributes:
    movies: 85
    series: 65
    recently_added: 5
    last_added: "Movie Title"
    last_added_date: "2026-01-15T10:30:00Z"
```

#### 2.3 Current Watching Sensor
```yaml
sensor.stremio_current_watching
  state: "Movie/Series Title"
  attributes:
    type: "series"  # or "movie"
    season: 2
    episode: 5
    episode_title: "Episode Name"
    progress_percent: 45
    duration: 2400  # seconds
    time_offset: 1080  # seconds watched
    poster: "https://..."
    imdb_id: "tt1234567"
    year: 2024
    started_at: "2026-01-17T20:00:00Z"
```

#### 2.4 Last Watched Sensor
```yaml
sensor.stremio_last_watched
  state: "Previous Title"
  attributes:
    type: "movie"
    finished_at: "2026-01-17T19:45:00Z"
    completed: true
    # Similar attributes to current_watching
```

#### 2.5 Watch Time Sensor
```yaml
sensor.stremio_watch_time
  state: 127.5  # Total hours
  attributes:
    total_seconds: 459000
    last_7_days: 8.5
    last_30_days: 35.2
    movies_watched: 45
    episodes_watched: 120
```

#### 2.6 Addons Sensor
```yaml
sensor.stremio_addons
  state: 12  # Number of installed addons
  attributes:
    addons:
      - name: "Torrentio"
        transport_url: "https://..."
        flags:
          official: false
          protected: false
      - name: "Cinemeta"
        transport_url: "https://..."
        flags:
          official: true
          protected: true
```

#### 2.7 Metadata Sensors (for current item)
```yaml
sensor.stremio_current_cast:
  state: "Actor 1, Actor 2, Actor 3"

sensor.stremio_current_director:
  state: "Director Name"

sensor.stremio_current_genres:
  state: "Action, Drama, Thriller"

sensor.stremio_current_rating:
  state: 8.5  # IMDb rating

sensor.stremio_current_description:
  state: "Plot synopsis..."
```

### 3. Binary Sensors

#### 3.1 Currently Playing
```yaml
binary_sensor.stremio_playing
  state: on/off
  device_class: running
  attributes:
    last_changed: "2026-01-17T20:15:00Z"
```

#### 3.2 Library Updated
```yaml
binary_sensor.stremio_library_updated
  state: on/off  # On when library changes detected
  device_class: update
  attributes:
    last_update: "2026-01-17T18:00:00Z"
```

### 4. Media Player Entity

```yaml
media_player.stremio
  state: "playing" / "paused" / "idle"
  attributes:
    media_content_type: "movie" / "tvshow"
    media_title: "Current Title"
    media_series_title: "Series Name"  # if tvshow
    media_season: 2
    media_episode: 5
    media_duration: 2400
    media_position: 1080
    media_position_updated_at: "2026-01-17T20:15:00Z"
    media_content_id: "tt1234567"
    media_album_name: "Season 2"  # for episodes
    entity_picture: "https://poster.url"
    source: "Stremio"
    supported_features: 0  # Read-only, no controls
```

**Note:** The media player is **read-only** as Stremio API doesn't support remote playback control.

### 5. Events

#### 5.1 Playback Start Event
```yaml
event_type: stremio_playback_started
data:
  title: "Movie Title"
  type: "movie"
  imdb_id: "tt1234567"
  started_at: "2026-01-17T20:00:00Z"
```

#### 5.2 Playback Update Event
```yaml
event_type: stremio_playback_progress
data:
  title: "Movie Title"
  progress_percent: 50
  time_offset: 1200
  duration: 2400
```

#### 5.3 Library Update Event
```yaml
event_type: stremio_library_updated
data:
  action: "added" / "removed"
  title: "New Movie"
  type: "movie"
  added_at: "2026-01-17T18:00:00Z"
```

### 6. Services

#### 6.1 Get Stream Links
```yaml
service: stremio.get_streams
data:
  content_id: "tt1234567"
  type: "movie"
```

**Response:** Fires `stremio_streams_received` event with available streams.

#### 6.2 Play on Apple TV
```yaml
service: stremio.play_on_apple_tv
data:
  entity_id: "media_player.living_room_apple_tv"
  content_id: "tt1234567"
  stream_url: "https://stream.url/video.mp4"  # Optional, auto-fetched if not provided
```

Fetches stream URLs from Stremio and plays on the specified Apple TV using AirPlay or VLC.

**Modes:**
- **Direct AirPlay** (default): Uses `pyatv` to stream URL directly via AirPlay
- **VLC Handover**: Launches VLC app on Apple TV with stream URL using `vlc-x-callback://` scheme

#### 6.3 Refresh Data
```yaml
service: stremio.refresh
```

Forces an immediate data refresh from the API.

#### 6.4 Add to Library
```yaml
service: stremio.add_to_library
data:
  content_id: "tt1234567"
  type: "movie"
  name: "Movie Title"
```

#### 6.5 Remove from Library
```yaml
service: stremio.remove_from_library
data:
  content_id: "tt1234567"
```

---

---

## UI Components & Cards

### Overview

Provide rich, interactive UI components for browsing Stremio library, viewing current media, and managing streams. All components emphasize stream URL access and copying for flexibility and external player support.

### Component Architecture

```
┌─────────────────────────────────────────┐
│     Stremio Media Player Card           │
│  (mini-media-player style)              │
│  - Current media display                │
│  - Playback controls (read-only)        │
│  - Quick actions: Get Streams, Play on  │
│    Apple TV, Copy URL                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     Stremio Library Browser             │
│  (Media Source Integration)             │
│  - Browse movies/series                 │
│  - Filter by type, genre                │
│  - Search functionality                 │
│  - Item detail views with actions       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     Stream Selector Dialog              │
│  (browser_mod popup)                    │
│  - List available streams               │
│  - Quality/source indicators            │
│  - Copy URL buttons                     │
│  - Play on device actions               │
└─────────────────────────────────────────┘
```

### 1. Stremio Media Player Card

**Type:** Custom Lovelace Card (inspired by mini-media-player)

**Purpose:** Display current/last watched media with rich controls and actions

**Features:**
- Display current watching media with artwork
- Show playback progress (from Continue Watching)
- Media metadata (title, episode, rating, cast)
- Quick action buttons
- Responsive design (mobile & desktop)

**Card Configuration:**

```yaml
type: custom:stremio-media-card
entity: media_player.stremio
artwork: cover  # cover, full-cover, material, none
info: scroll  # scroll, short
hide:
  power: true
  volume: true
  controls: true  # Hide play/pause (read-only anyway)
shortcuts:
  - name: Get Streams
    type: service
    id: stremio.get_streams
    icon: mdi:play-network
    data:
      content_id: "{{ state_attr('media_player.stremio', 'media_content_id') }}"
  - name: Copy URL
    type: script
    id: script.stremio_show_stream_urls
    icon: mdi:content-copy
  - name: Play on Apple TV
    type: service
    id: stremio.play_on_apple_tv
    icon: mdi:apple
    data:
      entity_id: media_player.living_room_apple_tv
      content_id: "{{ state_attr('media_player.stremio', 'media_content_id') }}"
```

**Visual Design:**

```
┌────────────────────────────────────────┐
│  [Artwork Background]                  │
│                                        │
│  🎬 Movie Title (2024)                 │
│  ⭐ 8.5/10  •  Action, Sci-Fi          │
│  ─────────────────── 45%               │
│                                        │
│  [Get Streams] [Copy URL] [▶ Apple TV]│
│                                        │
│  Director: John Doe                    │
│  Cast: Actor 1, Actor 2, Actor 3       │
└────────────────────────────────────────┘
```

**Implementation:**
- Extend mini-media-player or create custom card
- Use LitElement/TypeScript
- Support HA theme variables
- Responsive grid layout
- Service call actions on shortcuts

### 2. Stremio Library Browser

**Type:** Media Source Integration + Optional Custom Card

**Purpose:** Browse and manage Stremio library with advanced filtering

#### 2.1 Media Source Integration (Built-in HA)

**Implementation:**
```python
# In Stremio integration
from homeassistant.components.media_source import MediaSource

class StremioMediaSource(MediaSource):
    """Stremio media source implementation."""
    
    name = "Stremio"
    
    async def async_browse_media(self, item):
        """Browse Stremio library."""
        # Return library structure:
        # - Continue Watching
        # - Movies
        # - Series
        # - Recently Added
```

**Hierarchy:**
```
Stremio
├── Continue Watching (5 items)
│   ├── Movie Title (45% watched)
│   └── Series S02E03 (12:30 / 42:00)
├── Movies (85 items)
│   ├── Action (25)
│   ├── Comedy (18)
│   └── Drama (42)
└── Series (65 items)
    ├── Currently Watching (8)
    └── All Series (65)
```

**Features:**
- Browse via standard HA media browser
- Click item to see details
- "Play on" action for media_player entities
- Context menu for actions

#### 2.2 Custom Library Card (Optional)

**Type:** Custom Lovelace Card

**Purpose:** Enhanced library browsing with grid view and filters

```yaml
type: custom:stremio-library-card
entity: sensor.stremio_library
view: grid  # grid, list, compact
filter:
  type: all  # all, movies, series
  sort: recent  # recent, title, rating, year
search: true
actions:
  show_streams: true  # Show "Get Streams" button
  play_on_devices: true  # Show device selection
  add_to_continue: true  # Add to continue watching
```

**Visual Design (Grid View):**

```
┌──────────────────────────────────────────────┐
│  Stremio Library                             │
│  [Movies▾] [Sort: Recent▾] [🔍____________]  │
│                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
│  │[img] │  │[img] │  │[img] │  │[img] │    │
│  │Title │  │Title │  │Title │  │Title │    │
│  │2024  │  │2024  │  │2023  │  │2024  │    │
│  │⭐8.5 │  │⭐7.2 │  │⭐9.0 │  │⭐6.8 │    │
│  │[📡]  │  │[📡]  │  │[📡]  │  │[📡]  │    │
│  └──────┘  └──────┘  └──────┘  └──────┘    │
│                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
│  │ ...  │  │ ...  │  │ ...  │  │ ...  │    │
└──────────────────────────────────────────────┘

[📡] = Get Streams button on hover/tap
```

**Implementation:**
- Custom card with TypeScript/LitElement
- Virtual scrolling for large libraries
- Lazy image loading
- Filter/search in frontend
- Tap item → Show detail popup
- Tap [📡] → Show streams dialog

### 3. Stream Selector Dialog

**Type:** browser_mod popup / HA dialog

**Purpose:** Display available streams for content and enable URL copying

**Trigger Methods:**
1. Click "Get Streams" button on media player card
2. Click stream icon [📡] on library card
3. Service call: `stremio.show_stream_selector`

**Service Definition:**
```yaml
service: stremio.show_stream_selector
data:
  content_id: "tt1234567"
  browser_id: "this"  # Show on current browser only
```

**Dialog Content:**

```
┌────────────────────────────────────────────┐
│  Available Streams for "Movie Title"       │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │ 🎬 Source: Torrentio                │   │
│  │ 📊 Quality: 1080p WEBRip            │   │
│  │ 💾 Size: 2.4 GB                     │   │
│  │                                     │   │
│  │ [📋 Copy URL] [▶ Play on Apple TV] │   │
│  └────────────────────────────────────┘   │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │ 🎬 Source: Torrentio                │   │
│  │ 📊 Quality: 720p WEBRip             │   │
│  │ 💾 Size: 1.2 GB                     │   │
│  │                                     │   │
│  │ [📋 Copy URL] [▶ Play on Apple TV] │   │
│  └────────────────────────────────────┘   │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │ 🎬 Source: Streaming Service        │   │
│  │ 📊 Quality: 1080p Stream            │   │
│  │                                     │   │
│  │ [📋 Copy URL] [▶ Play on Apple TV] │   │
│  └────────────────────────────────────┘   │
│                                            │
│                            [Close]         │
└────────────────────────────────────────────┘
```

**Implementation:**

```python
# In Stremio integration
async def show_stream_selector(hass, content_id, browser_id="this"):
    """Show stream selector dialog."""
    # 1. Fetch streams from Stremio
    streams = await coordinator.client.get_streams(content_id)
    
    # 2. Build dialog content
    card_config = {
        "type": "custom:stremio-stream-dialog",
        "streams": streams,
        "content_id": content_id,
    }
    
    # 3. Show via browser_mod
    await hass.services.async_call(
        "browser_mod",
        "popup",
        {
            "browser_id": browser_id,
            "title": f"Streams for {title}",
            "card": card_config,
        },
    )
```

**Copy URL Functionality:**

**Option 1: Native Clipboard API (Preferred)**
```javascript
// In custom card JavaScript
async copyToClipboard(url) {
  try {
    await navigator.clipboard.writeText(url);
    // Show success toast
    this._showToast("URL copied to clipboard!");
  } catch (err) {
    // Fallback: show text field for manual copy
    this._showUrlDialog(url);
  }
}
```

**Option 2: Notification with Copyable Text (Android)**
```yaml
# Automation triggered by stream selection
automation:
  - trigger:
      platform: event
      event_type: stremio_stream_selected
    action:
      - service: notify.mobile_app
        data:
          title: "Stream URL"
          message: "{{ trigger.event.data.stream_url }}"
          data:
            actions:
              - action: "COPY_URL"
                title: "Copy URL"
```

**Option 3: Display in Input Text Helper**
```yaml
# Create helper
input_text:
  stremio_stream_url:
    name: Stremio Stream URL
    max: 500

# Card to display
type: entities
entities:
  - entity: input_text.stremio_stream_url
    name: Stream URL
    icon: mdi:link
```

### 4. Quick Action Buttons

**Purpose:** Add "Get Streams" and "Copy URL" buttons everywhere media is displayed

**Locations:**
1. Media player card shortcuts
2. Library card item actions
3. Continue Watching list items
4. Media browser context menu
5. Sensor cards (current watching, last watched)

**Button Card Example:**

```yaml
type: custom:button-card
name: Get Streams
icon: mdi:play-network
tap_action:
  action: call-service
  service: stremio.show_stream_selector
  service_data:
    content_id: "{{ state_attr('sensor.stremio_current_watching', 'imdb_id') }}"
styles:
  card:
    - height: 50px
  icon:
    - color: var(--primary-color)
```

### 5. Continue Watching Quick Resume Card

**Type:** Custom Card with List View

**Purpose:** Quick access to continue watching items with resume actions

```yaml
type: custom:stremio-continue-watching-card
entity: sensor.stremio_current_watching
limit: 5
show_progress: true
actions:
  - resume_on_apple_tv
  - get_streams
  - remove_from_list
```

**Visual Design:**

```
┌──────────────────────────────────────────────┐
│  Continue Watching                           │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ [Poster] Movie Title (2024)            │ │
│  │          ████████────────── 45%        │ │
│  │          [▶ Resume] [📡] [❌]          │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ [Poster] Series S02E03                 │ │
│  │          ███─────────────── 15%        │ │
│  │          [▶ Resume] [📡] [❌]          │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  View All (12) →                             │
└──────────────────────────────────────────────┘
```

### 6. Lovelace Dashboard Examples

#### 6.1 Media Room Dashboard

```yaml
title: Media Room
views:
  - title: Stremio
    path: stremio
    cards:
      # Main player card
      - type: custom:stremio-media-card
        entity: media_player.stremio
        artwork: full-cover
        shortcuts:
          - name: Get Streams
            type: service
            id: stremio.show_stream_selector
          - name: Apple TV
            type: service
            id: stremio.play_on_apple_tv
            data:
              entity_id: media_player.living_room_apple_tv

      # Continue Watching
      - type: custom:stremio-continue-watching-card
        entity: sensor.stremio_current_watching
        limit: 5

      # Quick Stats
      - type: glance
        entities:
          - entity: sensor.stremio_library
            name: Library
          - entity: sensor.stremio_watch_time
            name: Watch Time
          - entity: sensor.stremio_addons
            name: Addons

      # Library Browser
      - type: custom:stremio-library-card
        entity: sensor.stremio_library
        view: grid
```

#### 6.2 Mobile Quick Actions

```yaml
# For mobile app, use compact view
type: vertical-stack
cards:
  - type: custom:stremio-media-card
    entity: media_player.stremio
    artwork: cover
    info: short
    hide:
      controls: true
      volume: true

  - type: horizontal-stack
    cards:
      - type: custom:button-card
        name: Get Streams
        icon: mdi:play-network
        tap_action:
          action: call-service
          service: stremio.show_stream_selector
      - type: custom:button-card
        name: Copy URL
        icon: mdi:content-copy
        tap_action:
          action: call-service
          service: script.stremio_copy_stream_url
      - type: custom:button-card
        name: Play on TV
        icon: mdi:apple
        tap_action:
          action: call-service
          service: stremio.play_on_apple_tv
```

### 7. Automation & Script Examples

#### 7.1 Auto-show Streams on Playback Start

```yaml
automation:
  - alias: "Stremio: Show streams when new media starts"
    trigger:
      - platform: state
        entity_id: sensor.stremio_current_watching
    condition:
      - condition: template
        value_template: >
          {{ trigger.to_state.state != trigger.from_state.state }}
    action:
      - service: stremio.show_stream_selector
        data:
          content_id: >
            {{ state_attr('sensor.stremio_current_watching', 'imdb_id') }}
          browser_id: "this"
```

#### 7.2 Script: Copy Stream URL to Input Text

```yaml
script:
  stremio_copy_stream_url:
    alias: "Copy Stremio Stream URL"
    sequence:
      - service: stremio.get_streams
        data:
          content_id: >
            {{ state_attr('sensor.stremio_current_watching', 'imdb_id') }}
        response_variable: streams
      - service: input_text.set_value
        target:
          entity_id: input_text.stremio_stream_url
        data:
          value: "{{ streams.streams[0].url }}"
      - service: browser_mod.notification
        data:
          message: "Stream URL copied to input_text.stremio_stream_url"
          duration: 5000
```

### 8. Development Requirements

#### Frontend (Custom Cards)

**Technology Stack:**
- TypeScript
- LitElement (HA standard)
- Rollup for bundling
- HACS compatible structure

**File Structure:**
```
www/stremio-cards/
├── stremio-media-card.js
├── stremio-library-card.js
├── stremio-stream-dialog.js
└── stremio-continue-watching-card.js
```

**Card Registration:**
```javascript
customElements.define('stremio-media-card', StremioMediaCard);
customElements.define('stremio-library-card', StremioLibraryCard);
customElements.define('stremio-stream-dialog', StremioStreamDialog);
customElements.define('stremio-continue-watching-card', StremioContinueWatchingCard);
```

#### Backend (Integration)

**Media Source Implementation:**
```python
# media_source.py
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)

async def async_get_media_source(hass):
    """Set up Stremio media source."""
    return StremioMediaSource(hass)

class StremioMediaSource(MediaSource):
    """Stremio media source."""
    
    name: str = "Stremio"
    
    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a playable URL."""
        # Return stream URL
        
    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Browse Stremio library."""
        # Return browseable media structure
```

**Service: Show Stream Selector:**
```python
async def show_stream_selector(call):
    """Service to show stream selector dialog."""
    content_id = call.data.get("content_id")
    browser_id = call.data.get("browser_id", "this")
    
    # Fetch streams
    streams = await coordinator.async_get_streams(content_id)
    
    # Fire event for dialog display
    hass.bus.async_fire(
        "stremio_show_streams",
        {
            "content_id": content_id,
            "streams": streams,
            "browser_id": browser_id,
        },
    )
```

### 9. HACS Resources Configuration

**resources.yaml / dashboard resources:**

```yaml
resources:
  - url: /hacsfiles/stremio/stremio-media-card.js
    type: module
  - url: /hacsfiles/stremio/stremio-library-card.js
    type: module
  - url: /hacsfiles/stremio/stremio-stream-dialog.js
    type: module
  - url: /hacsfiles/stremio/stremio-continue-watching-card.js
    type: module
```

### 10. Implementation Checklist

**Phase 1: Basic Media Player Card**
- [ ] Create base media player card extending mini-media-player pattern
- [ ] Display current media with artwork
- [ ] Add shortcut buttons for actions
- [ ] Implement service call actions
- [ ] Test with media player entity

**Phase 2: Stream Selector Dialog**
- [ ] Create stream dialog component
- [ ] Implement `stremio.show_stream_selector` service
- [ ] Add stream URL display with copy button
- [ ] Integrate clipboard API (with fallbacks)
- [ ] Test popup display via browser_mod

**Phase 3: Media Source Integration**
- [ ] Implement `MediaSource` for Stremio
- [ ] Create library browsing structure
- [ ] Add continue watching section
- [ ] Test with HA media browser
- [ ] Add context menu actions

**Phase 4: Library Card**
- [ ] Create custom library card with grid/list views
- [ ] Implement filtering and search
- [ ] Add stream icons on items
- [ ] Lazy loading for large libraries
- [ ] Mobile responsive design

**Phase 5: Continue Watching Card**
- [ ] Create continue watching list card
- [ ] Show progress bars
- [ ] Add resume/remove actions
- [ ] Integrate with sensors

**Phase 6: Documentation & Examples**
- [ ] Card configuration examples
- [ ] Dashboard templates
- [ ] Automation examples
- [ ] Troubleshooting guide

---

## Configuration

### Config Flow

**Step 1: User Authentication**
- Input fields:
  - Email (required, string)
  - Password (required, password field)
  
**Step 2: Validation**
- Attempt login via `stremio-api`
- Retrieve and store auth key
- Fetch user profile for validation

**Step 3: Completion**
- Create config entry with encrypted auth key
- Set up coordinator and entities
- Show success message

### Options Flow

**Configurable Options:**

```yaml
options:
  scan_interval: 60  # seconds (30-300)
  enable_metadata_sensors: true
  enable_events: true
  continue_watching_limit: 10  # items to fetch
  library_sync: true
```

**Options UI:**
- Number selector for scan interval
- Toggle switches for features
- Save and apply changes without restarting

---

## API Integration

### Authentication Flow

```python
async def authenticate(email: str, password: str) -> str:
    """Authenticate with Stremio and return auth key."""
    async with StremioAPIClient(auth_key=None) as client:
        auth_key = await client.login(email, password)
        return auth_key
```

### Data Update Cycle

**Update Frequency:** 60 seconds (configurable)

**Data Fetched Per Cycle:**
1. User profile (cached, updated hourly)
2. Continue watching list (every update)
3. Library items (every update, paginated if needed)
4. Addon collection (cached, updated hourly)
5. Metadata for current item (on change)

### Error Handling

**Authentication Errors:**
- Invalid credentials → Prompt re-authentication
- Expired auth key → Auto re-login if credentials stored
- API unavailable → Retry with exponential backoff

**Data Errors:**
- Network timeout → Use cached data, retry next cycle
- Rate limiting → Increase scan interval temporarily
- Malformed data → Log warning, skip update

### Rate Limiting

- Default: 60-second intervals (1 request/minute per endpoint)
- Respect API rate limits (if documented)
- Implement exponential backoff on 429 errors

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Set up project structure
- [ ] Implement manifest.json and strings.json
- [ ] Create `const.py` with constants
- [ ] Set up basic `__init__.py` with platform loading

### Phase 2: Authentication (Week 1)
- [ ] Implement config flow with email/password
- [ ] Add authentication validation
- [ ] Secure auth key storage
- [ ] Add error handling for auth failures

### Phase 3: API Client (Week 2)
- [ ] Install and wrap `stremio-api` library
- [ ] Create `coordinator.py` with DataUpdateCoordinator
- [ ] Implement data fetching methods
- [ ] Add error handling and retries

### Phase 4: Core Entities (Week 2-3)
- [ ] Implement user sensor
- [ ] Implement library sensor
- [ ] Implement current/last watching sensors
- [ ] Implement watch time sensor
- [ ] Implement addon sensor

### Phase 5: Advanced Entities (Week 3)
- [ ] Implement metadata sensors
- [ ] Implement binary sensors
- [ ] Implement media player entity (read-only)
- [ ] Add entity state management

### Phase 6: Events & Services (Week 4)
- [ ] Implement event firing for playback changes
- [ ] Implement library update events
- [ ] Add `get_streams` service
- [ ] Add `refresh` service
- [ ] Add library management services
- [ ] Implement Apple TV handover service (Phase 6a)
  - [ ] Basic AirPlay streaming via `pyatv`
  - [ ] VLC deep linking support
  - [ ] Automatic method selection
  - [ ] Stream URL fetching and caching

### Phase 7: Options Flow (Week 4)
- [ ] Implement options flow handler
- [ ] Add configuration options UI
- [ ] Add options validation
- [ ] Test options updates

### Phase 8: Testing & Polish (Week 5)
- [ ] Unit tests for all components
- [ ] Integration tests
- [ ] Documentation structure setup
  - [ ] Create /docs/ directory structure
  - [ ] Write README.md
  - [ ] Write installation guide
  - [ ] Write configuration reference
  - [ ] Create feature documentation
  - [ ] Write development guides
- [ ] HACS validation
- [ ] Logo and branding

### Phase 9: Release (Week 5)
- [ ] Complete CHANGELOG.md
- [ ] HACS submission
- [ ] Community announcement
- [ ] Initial user feedback
- [ ] Bug fixes

---

## Known Limitations

### 1. No Real-Time Player Control

**Issue:** Stremio API does not provide webhooks or real-time player state.

**Impact:**
- Cannot detect play/pause/stop events in real-time
- Cannot control playback remotely
- Updates only via polling (60-second intervals)

**Workaround:**
- Poll "Continue Watching" API for progress changes
- Infer playback events from progress deltas
- Lower polling interval for more responsive updates (trade-off: more API calls)

**Future:** There's an open feature request ([#768](https://github.com/Stremio/stremio-core/issues/768)) for webhooks, but no ETA.

### 2. Limited Player State Information

**Issue:** API only exposes watch progress, not current playback state.

**Impact:**
- Cannot determine if user is actively watching NOW
- Only know "last watched" and "currently watching" (from Continue Watching)
- No pause/buffering/error states available

**Workaround:**
- Infer "playing" state by monitoring progress updates
- Mark as "idle" if no progress change in X minutes
- Use binary sensor to indicate likely playback

### 3. Device-Specific Limitations

**Issue:** Stremio API is user-centric, not device-specific.

**Impact:**
- Cannot distinguish which device is playing
- Multi-device households see aggregated data
- Cannot target specific devices for commands

### 4. Metadata Completeness

**Issue:** Metadata depends on addons and content sources.

**Impact:**
- Some content may lack complete metadata
- IMDb IDs may be missing for some items
- Poster images may not always be available

### 5. Library Sync Delays

**Issue:** Library changes may not reflect immediately in API.

**Impact:**
- Adding/removing items may take time to appear
- Sync conflicts between devices possible

---

## Apple TV Handover Feature

### Overview

Enable seamless playback of Stremio content on Apple TV devices directly from Home Assistant. This feature allows users to "hand over" their current Stremio stream or any library content to an Apple TV for big-screen viewing.

### Implementation Approaches

#### Approach 1: Direct AirPlay Streaming (Recommended)

**Technology:** Home Assistant's Apple TV integration + `pyatv` library

**How it works:**
1. Fetch stream URL from Stremio API for requested content
2. Use `pyatv.stream.play_url()` to send URL directly to Apple TV via AirPlay
3. Apple TV fetches and plays the stream natively

**Advantages:**
- No additional apps required on Apple TV
- Native AirPlay protocol support
- Works with most video formats supported by Apple TV
- Reliable playback control
- Integrates with existing HA Apple TV integration

**Limitations:**
- Limited format support (MP4, M4V, MOV primarily)
- May not work with DRM-protected streams
- Requires network-accessible stream URLs
- HTTPS streams must have valid certificates

**Implementation:**
```python
# In Stremio integration
async def play_on_apple_tv(
    hass: HomeAssistant,
    apple_tv_entity_id: str,
    stream_url: str,
    metadata: dict
):
    """Play stream on Apple TV via AirPlay."""
    await hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": apple_tv_entity_id,
            "media_content_type": "url",
            "media_content_id": stream_url,
        },
    )
```

#### Approach 2: VLC App Deep Linking

**Technology:** VLC for Apple TV + URL scheme `vlc-x-callback://`

**How it works:**
1. Fetch stream URL from Stremio API
2. Launch VLC app on Apple TV using deep link
3. Pass stream URL to VLC using `vlc-x-callback://x-callback-url/stream?url=<STREAM_URL>`
4. VLC handles playback with broader format support

**Advantages:**
- Support for MKV, AVI, and other formats not supported by Apple TV natively
- Subtitle support
- Advanced playback controls
- Works with various streaming protocols (HTTP, RTSP, etc.)

**Limitations:**
- Requires VLC app installed on Apple TV
- URL scheme support on tvOS is limited (may not work on all tvOS versions)
- Less native integration than AirPlay
pyatv>=0.14.0  # For Apple TV AirPlay streaming
```

### Home Assistant Requirements

- Core: 2025.1+
- Config Flow support
- DataUpdateCoordinator
- Entity platform support
- Apple TV integration (optional, for handover feature)

### Optional Dependencies

- VLC for Apple TV 3.3.9+ (for enhanced format support)p linking
await hass.services.async_call(
    "media_player",
    "play_media",
    {
        "entity_id": apple_tv_entity_id,
        "media_content_type": "url",
        "media_content_id": vlc_url,
    },
)
```

**VLC URL Scheme Format:**
```
vlc-x-callback://x-callback-url/stream?url=<ENCODED_STREAM_URL>&x-success=<SUCCESS_CALLBACK>&x-error=<ERROR_CALLBACK>
```

#### Approach 3: Hybrid Mode (Recommended for Production)

Automatically select best method based on:
1. Stream format/protocol
2. Available apps on Apple TV
3. User preference

**Decision Logic:**
```python
if stream_format in ["mp4", "m4v", "mov"] and not requires_subtitles:
    # Use native AirPlay
    use_airplay_streaming()
elif vlc_installed_on_apple_tv:
    # Use VLC for broader compatibility
    use_vlc_deep_link()
else:
    # Fallback to AirPlay with format warning
    use_airplay_streaming(warn_user=True)
```

### Service Definition

**Service:** `stremio.play_on_apple_tv`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| entity_id | string | Yes | Apple TV media player entity ID |
| content_id | string | Conditional* | Stremio content ID (e.g., IMDb ID) |
| stream_url | string | Conditional* | Direct stream URL (if already known) |
| method | string | No | Playback method: "auto", "airplay", "vlc" (default: "auto") |
| subtitle_url | string | No | URL to subtitle file (SRT, VTT) |
| start_position | integer | No | Start playback at position (seconds) |

\* Either `content_id` or `stream_url` must be provided

**Examples:**

```yaml
# Play current watching item
service: stremio.play_on_apple_tv
data:
  entity_id: media_player.living_room_apple_tv
  content_id: "{{ state_attr('sensor.stremio_current_watching', 'imdb_id') }}"
  start_position: "{{ state_attr('sensor.stremio_current_watching', 'time_offset') }}"
```

```yaml
# Play specific movie via VLC
service: stremio.play_on_apple_tv
data:
  entity_id: media_player.bedroom_apple_tv
  content_id: "tt1234567"
  method: "vlc"
```

```yaml
# Play with direct stream URL
service: stremio.play_on_apple_tv
data:
  entity_id: media_player.living_room_apple_tv
  stream_url: "https://stream.provider.com/video.mp4"
  method: "airplay"
```

### Configuration Options

**Options Flow Settings:**

```yaml
apple_tv_integration:
  enabled: true
  default_method: "auto"  # auto, airplay, vlc
  preferred_quality: "1080p"  # 4k, 1080p, 720p, auto
  auto_resume: true  # Resume from Continue Watching position
  subtitle_language: "en"  # Default subtitle language
  fallback_to_airplay: true  # If VLC fails, try AirPlay
```

### User Experience Flow

**Scenario 1: Resume Current Watching on Apple TV**

1. User clicks "Play on Apple TV" button in Lovelace
2. Integration fetches current watching item from Stremio
3. Retrieves available stream URLs via `stremio.get_streams`
4. Selects best quality stream based on preferences
5. Detects best playback method (AirPlay vs VLC)
6. Sends stream to Apple TV at last watched position
7. Fires `stremio_handover_started` event
8. Apple TV begins playback

**Scenario 2: Play Library Item**

1. User browses Stremio library in HA Media Browser
2. Selects a movie/episode
3. Chooses Apple TV as playback device
4. Integration fetches stream URLs
5. Launches on Apple TV with selected method
6. Updates Continue Watching in Stremio

### Technical Requirements

**Home Assistant Integration Dependencies:**
```yaml
dependencies:
  - apple_tv  # HA built-in Apple TV integration
```

**Python Library Requirements:**
```txt
pyatv>=0.14.0  # For AirPlay streaming control
```

**Apple TV Requirements:**
- tvOS 14.0+ (for deep linking support)
- VLC for Apple TV 3.3.9+ (if using VLC method)
- Network connectivity between HA and Apple TV
- AirPlay enabled on Apple TV

### Implementation Checklist

**Phase 1: Core Functionality**
- [ ] Add `pyatv` as dependency
- [ ] Implement stream URL fetching from Stremio
- [ ] Create basic AirPlay streaming service
- [ ] Add error handling for unsupported formats
- [ ] Test with common stream formats

**Phase 2: VLC Integration**
- [ ] Implement VLC URL scheme builder
- [ ] Add VLC app detection (optional)
- [ ] Create VLC deep link launcher
- [ ] Handle VLC-specific error cases
- [ ] Test with MKV, AVI formats

**Phase 3: Smart Selection**
- [ ] Implement automatic method selection
- [ ] Add format detection logic
- [ ] Create user preference system
- [ ] Add configuration options in options flow
- [ ] Implement fallback mechanisms

**Phase 4: Enhanced Features**
- [ ] Add subtitle support
- [ ] Implement resume from position
- [ ] Add quality selection
- [ ] Create Lovelace cards for quick handover
- [ ] Add automation blueprints

### Error Handling

**Common Errors:**

1. **Apple TV Not Found**
   - Error: "Apple TV entity not found or unavailable"
   - Resolution: Verify Apple TV integration is set up and device is on

2. **Stream URL Unavailable**
   - Error: "No stream URLs available for this content"
   - Resolution: Check Stremio addons configuration, ensure content is streamable

3. **Unsupported Format**
   - Error: "Stream format not supported by AirPlay"
   - Resolution: Automatically switch to VLC method or warn user

4. **VLC Not Installed**
   - Error: "VLC app not available on Apple TV"
   - Resolution: Fallback to AirPlay or prompt user to install VLC

5. **Network Timeout**
   - Error: "Failed to connect to stream source"
   - Resolution: Retry with exponential backoff, check network connectivity

### Security Considerations

1. **Stream URL Validation**
   - Validate URLs before passing to Apple TV
   - Ensure HTTPS for secure streams
   - Sanitize URLs to prevent injection

2. **Token Handling**
   - Don't expose Stremio auth tokens in stream URLs
   - Use time-limited stream URLs when possible
   - Validate stream URL expiration

3. **Network Security**
   - Ensure Apple TV is on trusted network
   - Validate SSL certificates for HTTPS streams
   - Don't log sensitive stream URLs

### Performance Considerations

1. **Stream URL Caching**
   - Cache stream URLs for 5 minutes
   - Refresh on expiration
   - Clear cache on quality change

2. **Apple TV Discovery**
   - Use existing HA Apple TV integration for discovery
   - Cache Apple TV device info
   - Re-scan on service call if needed

3. **Parallel Processing**
   - Fetch stream URLs asynchronously
   - Don't block UI during handover
   - Show progress indicator

## Future Enhancements

### Short-Term (Next 3-6 months)

1. **Media Source Browser**
   - Browse Stremio library from HA Media Browser
   - Launch streams directly from HA

2. **Enhanced Statistics**
   - Viewing trends over time
   - Most watched genres/actors
   - Daily/weekly/monthly statistics

3. **Notification Integration**
   - Notify when new content added to library
   - Alert on Continue Watching updates
   - Addon update notifications

4. **Device Setup Improvements**
   - QR code for easy device pairing
   - Support for Apple Sign-In
   - OAuth flow option

5. **Apple TV Handover (Priority Feature)**
   - Stream Stremio content to Apple TV
   - Support for AirPlay direct streaming
   - VLC app integration for broader format support
   - Auto-discovery of Apple TVs on network
   - Resume playback from Continue Watching

### Medium-Term (6-12 months)

1. **Trakt Integration**
   - Sync with Trakt.tv
   - Combined watch history
   - Scrobbling support

2. **Automation Templates**
   - Pre-built automations for common scenarios
   - "Lights off when watching" blueprints
   - Viewing time tracking automations

3. **Advanced Media Player**
   - Support external players (if API allows)
   - Cast integration
   - Kodi/Plex bridge

4. **Multi-User Support**
   - Multiple Stremio accounts per HA instance
   - Per-user sensors and entities
   - Family viewing tracking

### Long-Term (12+ months)

1. **Real-Time Events (if API adds webhooks)**
   - Instant play/pause/stop detection
   - Real-time progress tracking
   - Live state synchronization

2. **Remote Playback Control (if API adds)**
   - Play/pause/stop commands
   - Seek functionality
   - Volume control

3. **Smart Recommendations**
   - AI-powered content suggestions
   - Based on viewing patterns
   - Family-safe filtering

4. **Advanced Analytics Dashboard**
   - Lovelace cards for statistics
   - Viewing history visualization
   - Trend analysis

---

## Dependencies

### Python Packages

```txt
stremio-api>=0.1.0
homeassistant>=2025.1.0
```

### Home Assistant Requirements

- Core: 2025.1+
- Config Flow support
- DataUpdateCoordinator
- Entity platform support

---

## Documentation Structure

### Root Level Documentation

**README.md** - Main project documentation
- Project overview and features
- Quick installation via HACS
- Basic configuration steps
- Links to detailed docs
- Support and community links

**project.specs.md** (this file) - Complete technical specifications
- Architecture and design decisions
- Implementation details
- API integration specs
- Feature specifications

**agentinstructions.md** - AI agent development instructions
- Context for AI assistants
- Development workflow
- Code generation guidelines
- Testing procedures

### /docs/ Directory Structure

```
docs/
├── installation.md          # Detailed installation guide
├── configuration.md         # Complete configuration reference
├── features/
│   ├── media-player.md      # Media player entity details
│   ├── sensors.md           # All sensor entities
│   ├── services.md          # Service definitions and examples
│   ├── events.md            # Event types and payloads
│   ├── apple-tv.md          # Apple TV handover feature
│   └── ui-components.md     # Custom cards and UI
├── guides/
│   ├── quick-start.md       # 5-minute setup guide
│   ├── automations.md       # Automation examples
│   ├── dashboards.md        # Dashboard configurations
│   └── troubleshooting.md   # Common issues and solutions
├── development/
│   ├── setup.md             # Development environment
│   ├── architecture.md      # Code architecture
│   ├── testing.md           # Testing strategy and tools
│   ├── contributing.md      # Contribution guidelines
│   └── release.md           # Release process
├── api/
│   ├── stremio-api.md       # Stremio API reference
│   ├── rate-limits.md       # API rate limiting details
│   └── authentication.md    # Auth flow details
└── CHANGELOG.md             # Version history
```

### Documentation Content Map

#### docs/installation.md
- HACS installation (recommended)
- Manual installation
- Prerequisites and dependencies
- First-time setup wizard
- Verification steps

#### docs/configuration.md
- Config flow options
- Options flow settings
- YAML configuration (if supported)
- Advanced configuration
- Multiple instances

#### docs/features/media-player.md
- Entity attributes
- Supported features
- State meanings
- Update frequency
- Example use cases

#### docs/features/sensors.md
- All sensor types
- Attribute descriptions
- Update intervals
- Template examples
- Integration with other systems

#### docs/features/services.md
- Service definitions
- Parameter descriptions
- YAML examples
- Response handling
- Error codes

#### docs/features/events.md
- Event types
- Event data structures
- Listening to events
- Automation triggers
- Example automations

#### docs/features/apple-tv.md
- Setup requirements
- Configuration options
- Usage examples
- Troubleshooting
- Format compatibility

#### docs/features/ui-components.md
- Custom card installation
- Card configurations
- Dashboard examples
- Theming
- Mobile optimization

#### docs/guides/quick-start.md
- 5-minute setup
- First automation
- Dashboard setup
- Common patterns

#### docs/guides/automations.md
- Playback automations
- Library notifications
- Device handover
- Conditional triggers
- Blueprint templates

#### docs/guides/dashboards.md
- Basic dashboard
- Media room setup
- Mobile layout
- Tablet view
- Complete examples

#### docs/guides/troubleshooting.md
- Common errors
- Debug logging
- Network issues
- API problems
- Support resources

#### docs/development/setup.md
- Development environment
- Required tools
- Running locally
- Hot reload setup
- VS Code configuration

#### docs/development/architecture.md
- Component structure
- Data flow
- Coordinator pattern
- Entity lifecycle
- Service registration

#### docs/development/testing.md
- Unit testing
- Integration testing
- Manual testing
- Test coverage
- CI/CD pipeline

#### docs/development/contributing.md
- Code standards
- Commit conventions
- Pull request process
- Review guidelines
- Community guidelines

#### docs/development/release.md
- Version numbering
- Release checklist
- HACS validation
- Announcement template
- Rollback procedures

#### docs/api/stremio-api.md
- API endpoints
- Request/response formats
- Authentication details
- Error codes
- Example requests

#### docs/api/rate-limits.md
- Rate limit details
- Backoff strategies
- Best practices
- Monitoring

#### docs/api/authentication.md
- Auth flow
- Token management
- Re-authentication
- Security considerations

#### docs/CHANGELOG.md
- Version history
- Breaking changes
- New features
- Bug fixes
- Migration guides

---

## Testing Strategy

### Unit Tests
- Config flow authentication
- Options flow updates
- Coordinator data updates
- Entity state calculations
- Error handling

**Details:** See [docs/development/testing.md](docs/development/testing.md)

### Integration Tests
- Full setup flow
- Entity registration
- Service calls
- Event firing

**Details:** See [docs/development/testing.md](docs/development/testing.md)

### Manual Testing
- Real Stremio account integration
- Multi-device scenarios
- Network failure handling
- Rate limiting behavior

**Details:** See [docs/development/testing.md](docs/development/testing.md)

---

## Security Considerations

1. **Credential Storage**
   - Use HA's encrypted storage for auth keys
   - Never log passwords or auth keys
   - Secure transmission (HTTPS only)

2. **API Rate Limiting**
   - Respect API limits
   - Implement backoff strategies
   - Warn users of excessive polling

3. **Data Privacy**
   - Minimize data storage
   - Clear data on uninstall
   - No external telemetry

---

## Performance Considerations

1. **Memory Usage**
   - Cache frequently accessed data
   - Limit stored library items
   - Paginate large libraries

2. **CPU Usage**
   - Efficient JSON parsing
   - Async operations throughout
   - Minimal blocking calls

3. **Network Usage**
   - Compress API responses if possible
   - Batch requests where feasible
   - Configurable polling intervals

---

## License

MIT License (matching stremio-api library)

---

## References

- [Stremio API Client (JS)](https://github.com/Stremio/stremio-api-client)
- [stremio-api Python Library](https://pypi.org/project/stremio-api/)
- [Documentation Files

### Root Files
- `README.md` - Main project overview and quick start
- `project.specs.md` - This file, complete technical specifications
- `agentinstructions.md` - AI agent development instructions

### Documentation Directory (/docs/)
All detailed documentation lives in the `/docs/` directory. See [Documentation Structure](#documentation-structure) section above for complete file listing.

**Key Documentation:**
- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Features Overview](docs/features/)
- [User Guides](docs/guides/)
- [Development Guides](docs/development/)
- [API Reference](docs/api/)
- [Changelog](docs/CHANGELOG.md)

---

## Contact & Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Community:** Home Assistant Community Forum
- **Documentation:** [Full Documentation](docs/)

---

**Document Version:** 1.1  
**Created:** January 17, 2026  
**Last Updssues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Community:** Home Assistant Community Forum

---

**Document Version:** 1.0  
**Created:** January 17, 2026  
**Author:** AI Toolkit with Research  
**Status:** Ready for Development