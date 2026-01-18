"""Tests for Stremio services."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.stremio.const import (
    DOMAIN,
    SERVICE_SEARCH_LIBRARY,
    SERVICE_GET_STREAMS,
    SERVICE_ADD_TO_LIBRARY,
    SERVICE_REMOVE_FROM_LIBRARY,
    SERVICE_REFRESH_LIBRARY,
    SERVICE_HANDOVER_TO_APPLE_TV,
)
from custom_components.stremio.services import (
    async_setup_services,
    async_unload_services,
)

from .conftest import MOCK_LIBRARY_ITEMS, MOCK_STREAMS


@pytest.fixture
def mock_service_hass(hass: HomeAssistant, mock_coordinator):
    """Set up mock hass with coordinator for services."""
    mock_client = AsyncMock()
    mock_client.async_get_streams = AsyncMock(return_value=MOCK_STREAMS)
    mock_client.async_add_to_library = AsyncMock(return_value=True)
    mock_client.async_remove_from_library = AsyncMock(return_value=True)

    hass.data[DOMAIN] = {
        "test_entry": {
            "coordinator": mock_coordinator,
            "client": mock_client,
        }
    }

    return hass


class TestSearchLibraryService:
    """Tests for the search_library service."""

    @pytest.mark.asyncio
    async def test_search_by_title(self, mock_service_hass, mock_coordinator):
        """Test searching library by title."""
        mock_coordinator.data = {"library": MOCK_LIBRARY_ITEMS}

        await async_setup_services(mock_service_hass)

        # Find the registered search_library handler
        calls = mock_service_hass.services.async_register.call_args_list
        search_call = next(c for c in calls if c[0][1] == SERVICE_SEARCH_LIBRARY)
        handler = search_call[0][2]

        # Create mock service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"query": "Shawshank", "search_type": "title", "limit": 10}

        result = await handler(service_call)

        assert "results" in result
        assert "count" in result

    @pytest.mark.asyncio
    async def test_search_empty_query(self, mock_service_hass, mock_coordinator):
        """Test searching with empty query."""
        mock_coordinator.data = {"library": MOCK_LIBRARY_ITEMS}

        await async_setup_services(mock_service_hass)

        # Find the registered search_library handler
        calls = mock_service_hass.services.async_register.call_args_list
        search_call = next(c for c in calls if c[0][1] == SERVICE_SEARCH_LIBRARY)
        handler = search_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"query": "", "search_type": "all", "limit": 10}

        result = await handler(service_call)

        # Should return empty results
        assert result["count"] == 0


class TestGetStreamsService:
    """Tests for the get_streams service."""

    @pytest.mark.asyncio
    async def test_get_stream_url_success(self, mock_service_hass, mock_coordinator):
        """Test getting stream URL successfully."""
        await async_setup_services(mock_service_hass)

        # Find the registered get_streams handler
        calls = mock_service_hass.services.async_register.call_args_list
        streams_call = next(c for c in calls if c[0][1] == SERVICE_GET_STREAMS)
        handler = streams_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt0111161",
            "media_type": "movie",
        }

        result = await handler(service_call)

        assert "streams" in result
        assert "count" in result

    @pytest.mark.asyncio
    async def test_get_stream_url_series(self, mock_service_hass, mock_coordinator):
        """Test getting stream URL for series episode."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        streams_call = next(c for c in calls if c[0][1] == SERVICE_GET_STREAMS)
        handler = streams_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt0903747",
            "media_type": "series",
            "season": 1,
            "episode": 1,
        }

        result = await handler(service_call)

        assert "streams" in result

    @pytest.mark.asyncio
    async def test_get_stream_url_series_missing_episode(
        self, mock_service_hass, mock_coordinator
    ):
        """Test validation error when series missing season/episode."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        streams_call = next(c for c in calls if c[0][1] == SERVICE_GET_STREAMS)
        handler = streams_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt0903747",
            "media_type": "series",
            # Missing season and episode
        }

        with pytest.raises(ServiceValidationError):
            await handler(service_call)


class TestAddToLibraryService:
    """Tests for the add_to_library service."""

    @pytest.mark.asyncio
    async def test_add_to_library(self, mock_service_hass, mock_coordinator):
        """Test adding item to library."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        add_call = next(c for c in calls if c[0][1] == SERVICE_ADD_TO_LIBRARY)
        handler = add_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt1234567",
            "media_type": "movie",
        }

        await handler(service_call)

        # Verify client method was called
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_add_to_library.assert_called_once()

        # Verify refresh was requested
        mock_coordinator.async_request_refresh.assert_called()

        # Verify event was fired
        mock_service_hass.bus.async_fire.assert_called()


class TestRemoveFromLibraryService:
    """Tests for the remove_from_library service."""

    @pytest.mark.asyncio
    async def test_remove_from_library(self, mock_service_hass, mock_coordinator):
        """Test removing item from library."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        remove_call = next(c for c in calls if c[0][1] == SERVICE_REMOVE_FROM_LIBRARY)
        handler = remove_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt0111161",
        }

        await handler(service_call)

        # Verify client method was called
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_remove_from_library.assert_called_once()

        # Verify refresh was requested
        mock_coordinator.async_request_refresh.assert_called()


class TestRefreshLibraryService:
    """Tests for the refresh_library service."""

    @pytest.mark.asyncio
    async def test_refresh_library(self, mock_service_hass, mock_coordinator):
        """Test refreshing library."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        refresh_call = next(c for c in calls if c[0][1] == SERVICE_REFRESH_LIBRARY)
        handler = refresh_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {}

        await handler(service_call)

        mock_coordinator.async_request_refresh.assert_called()


class TestHandoverService:
    """Tests for the Apple TV handover service."""

    @pytest.mark.asyncio
    async def test_handover_with_stream_url(self, mock_service_hass, mock_coordinator):
        """Test handover with provided stream URL."""
        mock_coordinator.data = {"current_watching": None}

        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        handover_call = next(
            c for c in calls if c[0][1] == SERVICE_HANDOVER_TO_APPLE_TV
        )
        handler = handover_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "device_id": "media_player.apple_tv",
            "stream_url": "http://example.com/stream.mp4",
            "method": "vlc",
        }

        with patch(
            "custom_components.stremio.services.HandoverManager"
        ) as mock_handover:
            mock_manager = MagicMock()
            mock_manager.handover = AsyncMock(return_value={"success": True})
            mock_handover.return_value = mock_manager

            await handler(service_call)

            mock_manager.handover.assert_called_once()


class TestServiceRegistration:
    """Tests for service registration."""

    @pytest.mark.asyncio
    async def test_services_registered(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test that all services are registered on setup."""
        mock_client = AsyncMock()
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
                "client": mock_client,
            }
        }

        await async_setup_services(hass)

        # Verify services were registered
        assert hass.services.has_service(DOMAIN, SERVICE_SEARCH_LIBRARY)
        assert hass.services.has_service(DOMAIN, SERVICE_GET_STREAMS)
        assert hass.services.has_service(DOMAIN, SERVICE_ADD_TO_LIBRARY)
        assert hass.services.has_service(DOMAIN, SERVICE_REMOVE_FROM_LIBRARY)
        assert hass.services.has_service(DOMAIN, SERVICE_REFRESH_LIBRARY)
        assert hass.services.has_service(DOMAIN, SERVICE_HANDOVER_TO_APPLE_TV)

    @pytest.mark.asyncio
    async def test_services_unregistered(self, hass: HomeAssistant):
        """Test that all services are unregistered on unload."""
        # First setup services
        hass.data[DOMAIN] = {
            "test_entry": {"coordinator": MagicMock(), "client": AsyncMock()}
        }
        await async_setup_services(hass)

        # Then unload
        await async_unload_services(hass)

        # Verify services were removed
        assert not hass.services.has_service(DOMAIN, SERVICE_SEARCH_LIBRARY)
        assert not hass.services.has_service(DOMAIN, SERVICE_GET_STREAMS)
