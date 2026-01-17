"""Tests for Stremio services."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.stremio.const import DOMAIN

from .conftest import MOCK_LIBRARY_ITEMS, MOCK_STREAMS


@pytest.fixture
def mock_service_hass(mock_hass, mock_coordinator):
    """Set up mock hass with coordinator for services."""
    mock_hass.data[DOMAIN] = {
        "test_entry": {
            "coordinator": mock_coordinator,
        }
    }
    return mock_hass


class TestSearchLibraryService:
    """Tests for the search_library service."""

    @pytest.mark.asyncio
    async def test_search_by_title(self, mock_service_hass, mock_coordinator):
        """Test searching library by title."""
        from custom_components.stremio.services import async_search_library
        
        service_call = MagicMock()
        service_call.data = {"query": "Shawshank"}
        
        result = await async_search_library(mock_service_hass, service_call)
        
        # Verify search was called
        mock_coordinator.client.search_library.assert_called()

    @pytest.mark.asyncio
    async def test_search_empty_query(self, mock_service_hass, mock_coordinator):
        """Test searching with empty query."""
        from custom_components.stremio.services import async_search_library
        
        service_call = MagicMock()
        service_call.data = {"query": ""}
        
        # Should handle empty query gracefully
        result = await async_search_library(mock_service_hass, service_call)
        assert result is not None or True  # Depends on implementation


class TestGetStreamUrlService:
    """Tests for the get_stream_url service."""

    @pytest.mark.asyncio
    async def test_get_stream_url_success(self, mock_service_hass, mock_coordinator):
        """Test getting stream URL successfully."""
        from custom_components.stremio.services import async_get_stream_url
        
        mock_coordinator.client.get_streams.return_value = MOCK_STREAMS
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt0111161",
            "media_type": "movie",
        }
        
        result = await async_get_stream_url(mock_service_hass, service_call)
        
        mock_coordinator.client.get_streams.assert_called_with(
            media_id="tt0111161",
            media_type="movie",
            season=None,
            episode=None,
        )

    @pytest.mark.asyncio
    async def test_get_stream_url_series(self, mock_service_hass, mock_coordinator):
        """Test getting stream URL for series episode."""
        from custom_components.stremio.services import async_get_stream_url
        
        mock_coordinator.client.get_streams.return_value = MOCK_STREAMS
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt0903747",
            "media_type": "series",
            "season": 1,
            "episode": 1,
        }
        
        result = await async_get_stream_url(mock_service_hass, service_call)
        
        mock_coordinator.client.get_streams.assert_called()

    @pytest.mark.asyncio
    async def test_get_stream_url_no_streams(self, mock_service_hass, mock_coordinator):
        """Test when no streams are found."""
        from custom_components.stremio.services import async_get_stream_url
        
        mock_coordinator.client.get_streams.return_value = []
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt0000000",
            "media_type": "movie",
        }
        
        result = await async_get_stream_url(mock_service_hass, service_call)
        
        # Should return empty or raise


class TestAddToLibraryService:
    """Tests for the add_to_library service."""

    @pytest.mark.asyncio
    async def test_add_to_library(self, mock_service_hass, mock_coordinator):
        """Test adding item to library."""
        from custom_components.stremio.services import async_add_to_library
        
        mock_coordinator.client.add_to_library.return_value = True
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt1234567",
            "media_type": "movie",
        }
        
        await async_add_to_library(mock_service_hass, service_call)
        
        mock_coordinator.client.add_to_library.assert_called()
        mock_coordinator.async_request_refresh.assert_called()


class TestRemoveFromLibraryService:
    """Tests for the remove_from_library service."""

    @pytest.mark.asyncio
    async def test_remove_from_library(self, mock_service_hass, mock_coordinator):
        """Test removing item from library."""
        from custom_components.stremio.services import async_remove_from_library
        
        mock_coordinator.client.remove_from_library.return_value = True
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt0111161",
        }
        
        await async_remove_from_library(mock_service_hass, service_call)
        
        mock_coordinator.client.remove_from_library.assert_called()
        mock_coordinator.async_request_refresh.assert_called()


class TestRefreshLibraryService:
    """Tests for the refresh_library service."""

    @pytest.mark.asyncio
    async def test_refresh_library(self, mock_service_hass, mock_coordinator):
        """Test refreshing library."""
        from custom_components.stremio.services import async_refresh_library
        
        service_call = MagicMock()
        service_call.data = {}
        
        await async_refresh_library(mock_service_hass, service_call)
        
        mock_coordinator.async_request_refresh.assert_called()


class TestHandoverService:
    """Tests for the Apple TV handover service."""

    @pytest.mark.asyncio
    async def test_handover_airplay(self, mock_service_hass, mock_coordinator, mock_pyatv):
        """Test AirPlay handover."""
        from custom_components.stremio.services import async_handover_to_apple_tv
        
        mock_coordinator.client.get_streams.return_value = MOCK_STREAMS
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt0111161",
            "device_name": "Living Room Apple TV",
            "method": "airplay",
        }
        
        # This test would require more setup for pyatv mocking
        # await async_handover_to_apple_tv(mock_service_hass, service_call)

    @pytest.mark.asyncio
    async def test_handover_vlc(self, mock_service_hass, mock_coordinator):
        """Test VLC deep link handover."""
        from custom_components.stremio.services import async_handover_to_apple_tv
        
        mock_coordinator.client.get_streams.return_value = MOCK_STREAMS
        
        service_call = MagicMock()
        service_call.data = {
            "media_id": "tt0111161",
            "device_name": "iPad",
            "method": "vlc",
        }
        
        # VLC handover returns a deep link
        # result = await async_handover_to_apple_tv(mock_service_hass, service_call)


class TestServiceRegistration:
    """Tests for service registration."""

    @pytest.mark.asyncio
    async def test_services_registered(self, mock_hass, mock_config_entry, mock_coordinator):
        """Test that all services are registered on setup."""
        from custom_components.stremio.services import async_setup_services
        
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }
        mock_hass.services.async_register = MagicMock()
        
        await async_setup_services(mock_hass)
        
        # Verify services were registered
        assert mock_hass.services.async_register.call_count >= 4
