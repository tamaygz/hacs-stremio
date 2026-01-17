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
