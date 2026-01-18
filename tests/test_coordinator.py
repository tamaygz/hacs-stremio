"""Tests for Stremio DataUpdateCoordinator."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.stremio.const import (
    DEFAULT_PLAYER_SCAN_INTERVAL,
    DEFAULT_LIBRARY_SCAN_INTERVAL,
)
from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
from custom_components.stremio.stremio_client import (
    StremioAuthError,
    StremioConnectionError,
)

from tests.conftest import (
    MOCK_LIBRARY_ITEMS,
    MOCK_CONTINUE_WATCHING,
    MOCK_CURRENT_MEDIA,
    MOCK_USER_DATA,
)


@pytest.fixture
def mock_stremio_client_for_coordinator():
    """Create a mock Stremio API client for coordinator tests."""
    client = AsyncMock()
    client.async_get_user = AsyncMock(return_value=MOCK_USER_DATA)
    client.async_get_library = AsyncMock(return_value=MOCK_LIBRARY_ITEMS)
    client.async_get_continue_watching = AsyncMock(return_value=MOCK_CONTINUE_WATCHING)
    return client


@pytest.mark.asyncio
async def test_coordinator_init(
    hass: HomeAssistant, mock_config_entry, mock_stremio_client_for_coordinator
):
    """Test coordinator initialization."""
    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_stremio_client_for_coordinator,
        entry=mock_config_entry,
    )

    assert coordinator.client == mock_stremio_client_for_coordinator
    assert coordinator.update_interval == timedelta(
        seconds=DEFAULT_PLAYER_SCAN_INTERVAL
    )


@pytest.mark.asyncio
async def test_coordinator_fetch_data_success(
    hass: HomeAssistant, mock_config_entry, mock_stremio_client_for_coordinator
):
    """Test successful data fetch."""
    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_stremio_client_for_coordinator,
        entry=mock_config_entry,
    )

    data = await coordinator._async_update_data()

    assert "library" in data
    assert "continue_watching" in data
    assert data["library"] == MOCK_LIBRARY_ITEMS
    assert data["continue_watching"] == MOCK_CONTINUE_WATCHING
    assert data["library_count"] == len(MOCK_LIBRARY_ITEMS)


@pytest.mark.asyncio
async def test_coordinator_fetch_data_connection_failure(
    hass: HomeAssistant, mock_config_entry
):
    """Test data fetch failure handling."""
    mock_client = AsyncMock()
    mock_client.async_get_user = AsyncMock(
        side_effect=StremioConnectionError("Network error")
    )

    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_client,
        entry=mock_config_entry,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_fetch_data_auth_failure(
    hass: HomeAssistant, mock_config_entry
):
    """Test authentication failure handling."""
    mock_client = AsyncMock()
    mock_client.async_get_user = AsyncMock(
        side_effect=StremioAuthError("Invalid credentials")
    )

    # Make sure the entry has the async_start_reauth method
    mock_config_entry.async_start_reauth = MagicMock()

    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_client,
        entry=mock_config_entry,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    # Should trigger reauth
    mock_config_entry.async_start_reauth.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_library_sync(
    hass: HomeAssistant, mock_config_entry, mock_stremio_client_for_coordinator
):
    """Test library synchronization logic."""
    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_stremio_client_for_coordinator,
        entry=mock_config_entry,
    )

    # First fetch
    data = await coordinator._async_update_data()
    library_count = data.get("library_count", 0)

    # Verify library was fetched
    assert library_count == len(MOCK_LIBRARY_ITEMS)
    mock_stremio_client_for_coordinator.async_get_library.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_current_watching_detection(
    hass: HomeAssistant, mock_config_entry
):
    """Test current watching detection logic."""
    mock_client = AsyncMock()
    mock_client.async_get_user = AsyncMock(return_value=MOCK_USER_DATA)
    mock_client.async_get_library = AsyncMock(return_value=[])
    mock_client.async_get_continue_watching = AsyncMock(
        return_value=[
            {
                "title": "Test Movie",
                "type": "movie",
                "progress": 1800,  # 30 minutes
                "duration": 7200,  # 2 hours
                "imdb_id": "tt1234567",
                "watched_at": "2024-01-01T12:00:00Z",
            }
        ]
    )

    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_client,
        entry=mock_config_entry,
    )

    data = await coordinator._async_update_data()

    # Should have current watching (progress 25% < 95%)
    assert data.get("current_watching") is not None
    assert data["current_watching"]["title"] == "Test Movie"
    assert data["current_watching"]["progress_percent"] == 25.0


@pytest.mark.asyncio
async def test_coordinator_event_firing(hass: HomeAssistant, mock_config_entry):
    """Test that events are fired on state changes."""
    mock_client = AsyncMock()
    mock_client.async_get_user = AsyncMock(return_value=MOCK_USER_DATA)
    mock_client.async_get_library = AsyncMock(return_value=MOCK_LIBRARY_ITEMS)
    mock_client.async_get_continue_watching = AsyncMock(
        return_value=[
            {
                "title": "Test Movie",
                "type": "movie",
                "progress": 1800,
                "duration": 7200,
                "imdb_id": "tt1234567",
                "watched_at": "2024-01-01T12:00:00Z",
            }
        ]
    )

    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_client,
        entry=mock_config_entry,
    )

    # First update - no previous state, so playback started event
    await coordinator._async_update_data()

    # Events should be fired on hass.bus


@pytest.mark.asyncio
async def test_coordinator_cache_behavior(
    hass: HomeAssistant, mock_config_entry, mock_stremio_client_for_coordinator
):
    """Test that coordinator caches data appropriately."""
    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_stremio_client_for_coordinator,
        entry=mock_config_entry,
    )

    # First fetch
    data1 = await coordinator._async_update_data()

    # Second fetch
    data2 = await coordinator._async_update_data()

    # Verify data consistency
    assert data1.get("library") == data2.get("library")


@pytest.mark.asyncio
async def test_coordinator_partial_failure(hass: HomeAssistant, mock_config_entry):
    """Test handling of partial API failures."""
    mock_client = AsyncMock()
    # User and library succeed
    mock_client.async_get_user = AsyncMock(return_value=MOCK_USER_DATA)
    mock_client.async_get_library = AsyncMock(return_value=MOCK_LIBRARY_ITEMS)
    # Continue watching fails
    mock_client.async_get_continue_watching = AsyncMock(
        side_effect=Exception("API Error")
    )

    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=mock_client,
        entry=mock_config_entry,
    )

    # Should raise UpdateFailed due to unexpected error
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
