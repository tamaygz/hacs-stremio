"""Pytest fixtures and configuration for Stremio integration tests.

NOTE: Tests must be run on Linux/macOS or in a devcontainer/WSL2.
The pytest-homeassistant-custom-component package uses pytest-socket to block
network calls, which conflicts with Windows' ProactorEventLoop for asyncio.
See docs/testing.md for details.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.stremio.const import DOMAIN

# Import fixtures from pytest-homeassistant-custom-component
# These provide properly mocked HomeAssistant instances that work with pytest-socket
pytest_plugins = "pytest_homeassistant_custom_component"

# ============================================================================
# Mock Data
# ============================================================================

MOCK_CONFIG_ENTRY = {
    CONF_EMAIL: "test@example.com",
    CONF_PASSWORD: "testpassword123",
}

MOCK_USER_DATA = {
    "id": "user123",
    "email": "test@example.com",
    "name": "Test User",
    "fbId": None,
    "avatar": "https://example.com/avatar.png",
    "premium": True,
    "dateCreated": "2020-01-01T00:00:00.000Z",
}

MOCK_LIBRARY_ITEMS = [
    {
        "id": "tt0111161",
        "imdb_id": "tt0111161",
        "type": "movie",
        "title": "The Shawshank Redemption",
        "year": 1994,
        "poster": "https://example.com/shawshank.jpg",
        "progress_percent": 45.5,
        "runtime": 8520,  # 142 minutes in seconds
        "genres": ["Drama"],
        "rating": "9.3",
    },
    {
        "id": "tt0468569",
        "imdb_id": "tt0468569",
        "type": "movie",
        "title": "The Dark Knight",
        "year": 2008,
        "poster": "https://example.com/darkknight.jpg",
        "progress_percent": 100,
        "runtime": 9120,  # 152 minutes
        "genres": ["Action", "Crime", "Drama"],
        "rating": "9.0",
    },
    {
        "id": "tt0903747",
        "imdb_id": "tt0903747",
        "type": "series",
        "title": "Breaking Bad",
        "year": 2008,
        "poster": "https://example.com/breakingbad.jpg",
        "progress_percent": 75.0,
        "genres": ["Crime", "Drama", "Thriller"],
        "rating": "9.5",
        "seasons": [
            {
                "number": 1,
                "episodes": [{"title": "Pilot"}, {"title": "Cat's in the Bag..."}],
            },
            {
                "number": 2,
                "episodes": [{"title": "Seven Thirty-Seven"}, {"title": "Grilled"}],
            },
        ],
    },
]

MOCK_CONTINUE_WATCHING = [
    {
        "id": "tt0111161",
        "imdb_id": "tt0111161",
        "type": "movie",
        "title": "The Shawshank Redemption",
        "poster": "https://example.com/shawshank.jpg",
        "progress_percent": 45.5,
        "position": 3834,  # seconds
        "duration": 8520,
    },
]

MOCK_STREAMS = [
    {
        "name": "Torrent",
        "title": "1080p BluRay",
        "url": "http://example.com/stream1.mp4",
        "quality": "1080p",
        "size": "2.5 GB",
        "seeds": 150,
    },
    {
        "name": "HTTP",
        "title": "720p WEB-DL",
        "externalUrl": "http://example.com/stream2.mp4",
        "quality": "720p",
        "size": "1.2 GB",
    },
]

MOCK_CURRENT_MEDIA = {
    "title": "The Shawshank Redemption",
    "type": "movie",
    "state": "playing",
    "position": 3834,
    "duration": 8520,
    "media_id": "tt0111161",
    "poster": "https://example.com/shawshank.jpg",
}


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_stremio_client():
    """Create a mock Stremio API client."""
    client = AsyncMock()

    # Configure mock methods
    client.login = AsyncMock(return_value=MOCK_USER_DATA)
    client.get_library = AsyncMock(return_value=MOCK_LIBRARY_ITEMS)
    client.get_continue_watching = AsyncMock(return_value=MOCK_CONTINUE_WATCHING)
    client.get_streams = AsyncMock(return_value=MOCK_STREAMS)
    client.search_library = AsyncMock(return_value=[MOCK_LIBRARY_ITEMS[0]])
    client.add_to_library = AsyncMock(return_value=True)
    client.remove_from_library = AsyncMock(return_value=True)
    client.get_user_info = AsyncMock(return_value=MOCK_USER_DATA)
    client.is_authenticated = True

    return client


@pytest.fixture
def mock_coordinator(mock_stremio_client):
    """Create a mock DataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.client = mock_stremio_client
    coordinator.data = {
        "library": MOCK_LIBRARY_ITEMS,
        "continue_watching": MOCK_CONTINUE_WATCHING,
        "current_media": MOCK_CURRENT_MEDIA,
        "is_playing": True,
        "user": MOCK_USER_DATA,
    }
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()

    return coordinator


@pytest.fixture
def mock_config_entry(hass: HomeAssistant):
    """Create a mock config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_ENTRY,
        options={
            "player_update_interval": 30,
            "library_update_interval": 300,
            "enable_apple_tv_handover": False,
            "handover_method": "auto",
        },
        unique_id="test@example.com",
        title="Stremio - test@example.com",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_hass(hass: HomeAssistant):
    """Create a mock HomeAssistant instance using pytest-homeassistant-custom-component.

    This fixture wraps the 'hass' fixture from pytest-homeassistant-custom-component
    and adds additional mock data structures needed by the Stremio integration tests.
    """
    hass.data = hass.data if hass.data else {}
    return hass


@pytest.fixture
def mock_stremio_api():
    """Patch the stremio_api module."""
    with patch("custom_components.stremio.stremio_client.StremioAPI") as mock:
        yield mock


@pytest.fixture
def mock_pyatv():
    """Patch the pyatv module for Apple TV tests."""
    with patch("custom_components.stremio.apple_tv_handover.pyatv") as mock:
        mock_device = MagicMock()
        mock_device.name = "Living Room Apple TV"
        mock_device.identifier = "apple_tv_123"
        mock.scan = AsyncMock(return_value=[mock_device])
        mock.connect = AsyncMock()

        yield mock


# ============================================================================
# Helpers
# ============================================================================


def create_mock_entity(entity_id: str, state: str, attributes: dict | None = None):
    """Create a mock entity state."""
    from homeassistant.core import State

    if attributes is None:
        attributes = {}

    return State(
        entity_id=entity_id,
        state=state,
        attributes=attributes or {},
    )


async def setup_integration(hass: HomeAssistant, config_entry):
    """Set up the Stremio integration for testing."""
    # Entry should already be added via mock_config_entry fixture
    if config_entry.entry_id not in [
        e.entry_id for e in hass.config_entries.async_entries(DOMAIN)
    ]:
        config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stremio.StremioClient",
        return_value=AsyncMock(),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return hass.data[DOMAIN][config_entry.entry_id]
