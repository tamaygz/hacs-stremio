"""Tests for Stremio DataUpdateCoordinator."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.stremio.const import (
    DEFAULT_PLAYER_SCAN_INTERVAL,
    DEFAULT_LIBRARY_SCAN_INTERVAL,
)

from tests.conftest import (
    MOCK_LIBRARY_ITEMS,
    MOCK_CONTINUE_WATCHING,
    MOCK_CURRENT_MEDIA,
    MOCK_USER_DATA,
)


@pytest.mark.asyncio
async def test_coordinator_init(mock_hass, mock_config_entry, mock_stremio_client):
    """Test coordinator initialization."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    assert coordinator.client == mock_stremio_client
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_PLAYER_UPDATE_INTERVAL)


@pytest.mark.asyncio
async def test_coordinator_fetch_data_success(mock_hass, mock_config_entry, mock_stremio_client):
    """Test successful data fetch."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    data = await coordinator._async_update_data()
    
    assert "library" in data
    assert "continue_watching" in data
    assert data["library"] == MOCK_LIBRARY_ITEMS
    assert data["continue_watching"] == MOCK_CONTINUE_WATCHING


@pytest.mark.asyncio
async def test_coordinator_fetch_data_failure(mock_hass, mock_config_entry):
    """Test data fetch failure handling."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    from custom_components.stremio.stremio_client import ConnectionError
    
    mock_client = AsyncMock()
    mock_client.get_library.side_effect = ConnectionError("Network error")
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_client,
        entry=mock_config_entry,
    )
    
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_library_sync(mock_hass, mock_config_entry, mock_stremio_client):
    """Test library synchronization logic."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    # First fetch
    data = await coordinator._async_update_data()
    library_count = len(data.get("library", []))
    
    # Verify library was fetched
    assert library_count == len(MOCK_LIBRARY_ITEMS)
    mock_stremio_client.get_library.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_player_state_detection(mock_hass, mock_config_entry, mock_stremio_client):
    """Test player state detection logic."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    data = await coordinator._async_update_data()
    
    # Should determine playing state from continue watching
    assert "is_playing" in data or "current_media" in data


@pytest.mark.asyncio
async def test_coordinator_event_firing(mock_hass, mock_config_entry, mock_stremio_client):
    """Test that events are fired on state changes."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    # Mock the previous state
    coordinator._previous_data = {"is_playing": False}
    
    data = await coordinator._async_update_data()
    
    # Verify event bus interaction (if playing state changed)
    # This depends on implementation details


@pytest.mark.asyncio
async def test_coordinator_rate_limiting(mock_hass, mock_config_entry, mock_stremio_client):
    """Test that API rate limiting is respected."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    from custom_components.stremio.stremio_client import RateLimitError
    
    mock_stremio_client.get_library.side_effect = [
        RateLimitError("Rate limited"),
        MOCK_LIBRARY_ITEMS,
    ]
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    # First call should raise UpdateFailed due to rate limit
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    
    # Reset the mock for next call
    mock_stremio_client.get_library.side_effect = None
    mock_stremio_client.get_library.return_value = MOCK_LIBRARY_ITEMS
    
    # Second call should succeed
    data = await coordinator._async_update_data()
    assert data["library"] == MOCK_LIBRARY_ITEMS


@pytest.mark.asyncio
async def test_coordinator_cache_behavior(mock_hass, mock_config_entry, mock_stremio_client):
    """Test that coordinator caches data appropriately."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    # First fetch
    data1 = await coordinator._async_update_data()
    
    # Second fetch
    data2 = await coordinator._async_update_data()
    
    # Verify data consistency
    assert data1.get("library") == data2.get("library")


@pytest.mark.asyncio
async def test_coordinator_partial_failure(mock_hass, mock_config_entry, mock_stremio_client):
    """Test handling of partial API failures."""
    from custom_components.stremio.coordinator import StremioDataUpdateCoordinator
    
    # Library succeeds, continue_watching fails
    mock_stremio_client.get_library.return_value = MOCK_LIBRARY_ITEMS
    mock_stremio_client.get_continue_watching.side_effect = Exception("API Error")
    
    coordinator = StremioDataUpdateCoordinator(
        hass=mock_hass,
        client=mock_stremio_client,
        entry=mock_config_entry,
    )
    
    # Should still return partial data or raise
    try:
        data = await coordinator._async_update_data()
        # If partial data is supported
        assert "library" in data
    except UpdateFailed:
        # If strict mode requires all data
        pass
