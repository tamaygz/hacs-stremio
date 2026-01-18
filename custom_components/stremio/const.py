"""Constants for the Stremio integration."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Final

# Read version from manifest.json
MANIFEST_PATH = Path(__file__).parent / "manifest.json"
with open(MANIFEST_PATH, encoding="utf-8") as f:
    INTEGRATION_VERSION: Final[str] = json.load(f).get("version", "0.0.0")

DOMAIN: Final = "stremio"

# Frontend constants
URL_BASE: Final[str] = "/stremio"

# JavaScript modules to register with Lovelace
JSMODULES: Final[list[dict[str, str]]] = [
    {
        "name": "Stremio Cards Bundle",
        "filename": "stremio-card-bundle.js",
        "version": INTEGRATION_VERSION,
    },
]

# Update intervals
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=30)
LIBRARY_SCAN_INTERVAL: Final = timedelta(minutes=5)
CATALOG_SCAN_INTERVAL: Final = timedelta(hours=6)  # Catalogs change less frequently

# Configuration
CONF_AUTH_KEY: Final = "auth_key"
CONF_PLAYER_SCAN_INTERVAL: Final = "player_scan_interval"
CONF_LIBRARY_SCAN_INTERVAL: Final = "library_scan_interval"
CONF_ENABLE_APPLE_TV_HANDOVER: Final = "enable_apple_tv_handover"
CONF_HANDOVER_METHOD: Final = "handover_method"
CONF_APPLE_TV_DEVICE: Final = "apple_tv_device"
CONF_APPLE_TV_ENTITY_ID: Final = "apple_tv_entity_id"
CONF_APPLE_TV_CREDENTIALS: Final = "apple_tv_credentials"
CONF_APPLE_TV_IDENTIFIER: Final = "apple_tv_identifier"
CONF_POLLING_GATE_ENTITIES: Final = "polling_gate_entities"

# Options defaults
DEFAULT_PLAYER_SCAN_INTERVAL: Final = 30  # seconds
DEFAULT_LIBRARY_SCAN_INTERVAL: Final = 300  # seconds (5 minutes)
DEFAULT_ENABLE_APPLE_TV_HANDOVER: Final = False
DEFAULT_HANDOVER_METHOD: Final = "auto"
DEFAULT_APPLE_TV_DEVICE: Final = ""
DEFAULT_APPLE_TV_ENTITY_ID: Final = ""
DEFAULT_POLLING_GATE_ENTITIES: Final[list[str]] = []

# Polling gate intervals (seconds)
POLLING_GATE_ACTIVE_INTERVAL: Final = None  # Use configured interval
POLLING_GATE_IDLE_INTERVAL: Final = 86400  # 24 hours when all gate entities are off

# Handover methods
# Note: VLC deep links do NOT work on tvOS - kept for reference but will fail
HANDOVER_METHOD_AUTO: Final = "auto"
HANDOVER_METHOD_AIRPLAY: Final = "airplay"
HANDOVER_METHOD_VLC: Final = "vlc"  # Does NOT work on tvOS!
HANDOVER_METHOD_DIRECT: Final = "direct"
HANDOVER_METHODS: Final = [
    HANDOVER_METHOD_AUTO,
    HANDOVER_METHOD_AIRPLAY,
    HANDOVER_METHOD_DIRECT,
    # VLC is intentionally last and will show a warning - it doesn't work on tvOS
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
SERVICE_GET_SERIES_METADATA: Final = "get_series_metadata"
SERVICE_SEARCH_LIBRARY: Final = "search_library"
SERVICE_ADD_TO_LIBRARY: Final = "add_to_library"
SERVICE_REMOVE_FROM_LIBRARY: Final = "remove_from_library"
SERVICE_REFRESH_LIBRARY: Final = "refresh_library"
SERVICE_HANDOVER_TO_APPLE_TV: Final = "handover_to_apple_tv"
SERVICE_BROWSE_CATALOG: Final = "browse_catalog"

# API Constants
API_BASE_URL: Final = "https://api.strem.io"
API_TIMEOUT: Final = 10

# Defaults
DEFAULT_NAME: Final = "Stremio"

# Catalog constants
CINEMETA_BASE_URL: Final = "https://v3-cinemeta.strem.io"
CATALOG_TYPE_MOVIE: Final = "movie"
CATALOG_TYPE_SERIES: Final = "series"
CATALOG_ID_TOP: Final = "top"
CATALOG_ID_POPULAR: Final = "popular"

# Catalog definitions for browsing
CATALOG_DEFINITIONS: Final = {
    "popular_movies": {
        "name": "Popular Movies",
        "type": CATALOG_TYPE_MOVIE,
        "catalog_id": CATALOG_ID_TOP,
        "extra": "popular.json",
    },
    "popular_series": {
        "name": "Popular TV Shows",
        "type": CATALOG_TYPE_SERIES,
        "catalog_id": CATALOG_ID_TOP,
        "extra": "popular.json",
    },
    "new_movies": {
        "name": "New Movies",
        "type": CATALOG_TYPE_MOVIE,
        "catalog_id": CATALOG_ID_TOP,
        "extra": "popular.json?genre=",  # Recent movies from popular
    },
    "new_series": {
        "name": "New TV Shows",
        "type": CATALOG_TYPE_SERIES,
        "catalog_id": CATALOG_ID_TOP,
        "extra": "popular.json?genre=",  # Recent series from popular
    },
}

# Supported genres for Cinemeta filtering
CINEMETA_GENRES: Final = [
    "Action",
    "Adventure",
    "Animation",
    "Biography",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Sport",
    "Thriller",
    "War",
    "Western",
]
