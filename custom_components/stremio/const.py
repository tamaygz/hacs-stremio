"""Constants for the Stremio integration."""

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "stremio"

# Update intervals
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=30)
LIBRARY_SCAN_INTERVAL: Final = timedelta(minutes=5)

# Platforms
PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
]

# Configuration
CONF_AUTH_KEY: Final = "auth_key"
CONF_PLAYER_SCAN_INTERVAL: Final = "player_scan_interval"
CONF_LIBRARY_SCAN_INTERVAL: Final = "library_scan_interval"
CONF_ENABLE_APPLE_TV_HANDOVER: Final = "enable_apple_tv_handover"
CONF_HANDOVER_METHOD: Final = "handover_method"

# Options defaults
DEFAULT_PLAYER_SCAN_INTERVAL: Final = 30  # seconds
DEFAULT_LIBRARY_SCAN_INTERVAL: Final = 300  # seconds (5 minutes)
DEFAULT_ENABLE_APPLE_TV_HANDOVER: Final = False
DEFAULT_HANDOVER_METHOD: Final = "auto"

# Handover methods
HANDOVER_METHOD_AUTO: Final = "auto"
HANDOVER_METHOD_AIRPLAY: Final = "airplay"
HANDOVER_METHOD_VLC: Final = "vlc"
HANDOVER_METHODS: Final = [
    HANDOVER_METHOD_AUTO,
    HANDOVER_METHOD_AIRPLAY,
    HANDOVER_METHOD_VLC,
]

# Sensor Types
SENSOR_TYPES: Final = {
    "current_media": {
        "name": "Current Watching",
        "icon": "mdi:play-circle",
        "device_class": None,
    },
    "last_watched": {
        "name": "Last Watched",
        "icon": "mdi:history",
        "device_class": None,
    },
    "current_position": {
        "name": "Current Position",
        "icon": "mdi:progress-clock",
        "device_class": "duration",
        "unit": "s",
    },
    "current_duration": {
        "name": "Current Duration",
        "icon": "mdi:timer",
        "device_class": "duration",
        "unit": "s",
    },
    "library_count": {
        "name": "Library Count",
        "icon": "mdi:library",
        "device_class": None,
    },
    "continue_watching": {
        "name": "Continue Watching",
        "icon": "mdi:play-pause",
        "device_class": None,
    },
    "total_watch_time": {
        "name": "Total Watch Time",
        "icon": "mdi:clock",
        "device_class": "duration",
        "unit": "h",
    },
    "favorite_genre": {
        "name": "Favorite Genre",
        "icon": "mdi:star",
        "device_class": None,
    },
    "watch_streak": {
        "name": "Watch Streak",
        "icon": "mdi:fire",
        "device_class": None,
        "unit": "days",
    },
}

# Binary Sensor Types
BINARY_SENSOR_TYPES: Final = {
    "is_playing": {
        "name": "Playing",
        "icon": "mdi:play",
        "device_class": "running",
    },
    "new_content": {
        "name": "New Content Available",
        "icon": "mdi:new-box",
        "device_class": "update",
    },
}

# Event Types
EVENT_PLAYBACK_STARTED: Final = "stremio_playback_started"
EVENT_PLAYBACK_STOPPED: Final = "stremio_playback_stopped"
EVENT_NEW_CONTENT: Final = "stremio_new_content"
EVENT_STREAM_URL: Final = "stremio_stream_url"

# Service Names
SERVICE_GET_STREAMS: Final = "get_streams"
SERVICE_SEARCH_LIBRARY: Final = "search_library"
SERVICE_ADD_TO_LIBRARY: Final = "add_to_library"
SERVICE_REMOVE_FROM_LIBRARY: Final = "remove_from_library"
SERVICE_REFRESH_LIBRARY: Final = "refresh_library"
SERVICE_HANDOVER_TO_APPLE_TV: Final = "handover_to_apple_tv"

# API Constants
API_BASE_URL: Final = "https://api.strem.io"
API_TIMEOUT: Final = 10

# Defaults
DEFAULT_NAME: Final = "Stremio"
