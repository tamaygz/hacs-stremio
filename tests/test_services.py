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
    SERVICE_GET_UPCOMING_EPISODES,
    SERVICE_GET_RECOMMENDATIONS,
    SERVICE_GET_SIMILAR_CONTENT,
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
    mock_client.async_get_upcoming_episodes = AsyncMock(return_value=[
        {
            "series_id": "tt0903747",
            "series_title": "Breaking Bad",
            "season": 5,
            "episode": 10,
            "episode_title": "Buried",
            "air_date": "2024-01-15T00:00:00Z",
            "air_date_formatted": "2024-01-15",
            "days_until": 3,
        }
    ])
    mock_client.async_get_recommendations = AsyncMock(return_value=[
        {
            "id": "tt1234567",
            "title": "Recommended Movie",
            "type": "movie",
            "recommendation_reason": "Based on your interest in Drama",
        }
    ])
    mock_client.async_get_similar_content = AsyncMock(return_value=[
        {
            "id": "tt7654321",
            "title": "Similar Show",
            "type": "series",
            "similarity_reason": "Similar Drama content",
        }
    ])

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

    @pytest.mark.asyncio
    async def test_get_streams_with_addon_order(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test get_streams service passes addon order to client."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create config entry with addon order preference
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"email": "test@example.com", "password": "test"},
            options={
                "addon_stream_order": "Torrentio\\nCinemetaStreams",
                "stream_quality_preference": "any",
            },
            entry_id="test_entry_with_prefs",
        )
        entry.add_to_hass(hass)

        mock_client = AsyncMock()
        mock_client.async_get_streams = AsyncMock(return_value=MOCK_STREAMS)

        hass.data[DOMAIN] = {
            entry.entry_id: {
                "coordinator": mock_coordinator,
                "client": mock_client,
            }
        }

        await async_setup_services(hass)

        calls = hass.services.async_register.call_args_list
        streams_call = next(c for c in calls if c[0][1] == SERVICE_GET_STREAMS)
        handler = streams_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt0111161",
            "media_type": "movie",
        }

        await handler(service_call)

        # Verify client was called with preferences
        mock_client.async_get_streams.assert_called_once()
        call_kwargs = mock_client.async_get_streams.call_args
        assert "addon_order" in call_kwargs.kwargs or len(call_kwargs.args) > 4

    @pytest.mark.asyncio
    async def test_get_streams_with_quality_preference(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test get_streams service passes quality preference to client."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create config entry with quality preference
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"email": "test@example.com", "password": "test"},
            options={
                "addon_stream_order": "",
                "stream_quality_preference": "1080p",
            },
            entry_id="test_entry_quality",
        )
        entry.add_to_hass(hass)

        mock_client = AsyncMock()
        mock_client.async_get_streams = AsyncMock(return_value=MOCK_STREAMS)

        hass.data[DOMAIN] = {
            entry.entry_id: {
                "coordinator": mock_coordinator,
                "client": mock_client,
            }
        }

        await async_setup_services(hass)

        calls = hass.services.async_register.call_args_list
        streams_call = next(c for c in calls if c[0][1] == SERVICE_GET_STREAMS)
        handler = streams_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "media_id": "tt0111161",
            "media_type": "movie",
        }

        await handler(service_call)

        # Verify client was called with quality preference
        mock_client.async_get_streams.assert_called_once()
        call_kwargs = mock_client.async_get_streams.call_args
        assert "quality_preference" in call_kwargs.kwargs or len(call_kwargs.args) > 5


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
        assert hass.services.has_service(DOMAIN, SERVICE_GET_UPCOMING_EPISODES)
        assert hass.services.has_service(DOMAIN, SERVICE_GET_RECOMMENDATIONS)
        assert hass.services.has_service(DOMAIN, SERVICE_GET_SIMILAR_CONTENT)

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


class TestGetUpcomingEpisodesService:
    """Tests for the get_upcoming_episodes service."""

    @pytest.mark.asyncio
    async def test_get_upcoming_episodes(self, mock_service_hass, mock_coordinator):
        """Test getting upcoming episodes."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        upcoming_call = next(c for c in calls if c[0][1] == SERVICE_GET_UPCOMING_EPISODES)
        handler = upcoming_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"days_ahead": 7}

        result = await handler(service_call)

        assert "episodes" in result
        assert "count" in result
        assert "days_ahead" in result

        # Verify client method was called
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_upcoming_episodes.assert_called_once_with(days_ahead=7)

    @pytest.mark.asyncio
    async def test_get_upcoming_episodes_default_days(self, mock_service_hass, mock_coordinator):
        """Test getting upcoming episodes with default days_ahead."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        upcoming_call = next(c for c in calls if c[0][1] == SERVICE_GET_UPCOMING_EPISODES)
        handler = upcoming_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {}

        result = await handler(service_call)

        assert "episodes" in result
        # Verify default value of 7 was used
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_upcoming_episodes.assert_called_once_with(days_ahead=7)


class TestGetRecommendationsService:
    """Tests for the get_recommendations service."""

    @pytest.mark.asyncio
    async def test_get_recommendations_all(self, mock_service_hass, mock_coordinator):
        """Test getting all recommendations."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        rec_call = next(c for c in calls if c[0][1] == SERVICE_GET_RECOMMENDATIONS)
        handler = rec_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"limit": 20}

        result = await handler(service_call)

        assert "recommendations" in result
        assert "count" in result

        # Verify client method was called
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_recommendations.assert_called_once_with(
            media_type=None,
            limit=20,
        )

    @pytest.mark.asyncio
    async def test_get_recommendations_movies_only(self, mock_service_hass, mock_coordinator):
        """Test getting movie recommendations only."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        rec_call = next(c for c in calls if c[0][1] == SERVICE_GET_RECOMMENDATIONS)
        handler = rec_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"media_type": "movie", "limit": 10}

        result = await handler(service_call)

        assert "recommendations" in result
        assert "media_type" in result

        # Verify client method was called with movie type
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_recommendations.assert_called_once_with(
            media_type="movie",
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_get_recommendations_series_only(self, mock_service_hass, mock_coordinator):
        """Test getting series recommendations only."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        rec_call = next(c for c in calls if c[0][1] == SERVICE_GET_RECOMMENDATIONS)
        handler = rec_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"media_type": "series", "limit": 15}

        result = await handler(service_call)

        assert "recommendations" in result

        # Verify client method was called with series type
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_recommendations.assert_called_once_with(
            media_type="series",
            limit=15,
        )


class TestGetSimilarContentService:
    """Tests for the get_similar_content service."""

    @pytest.mark.asyncio
    async def test_get_similar_content(self, mock_service_hass, mock_coordinator):
        """Test getting similar content."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        similar_call = next(c for c in calls if c[0][1] == SERVICE_GET_SIMILAR_CONTENT)
        handler = similar_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"media_id": "tt0903747", "limit": 10}

        result = await handler(service_call)

        assert "similar" in result
        assert "count" in result
        assert "source_media_id" in result

        # Verify client method was called
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_similar_content.assert_called_once_with(
            media_id="tt0903747",
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_get_similar_content_default_limit(self, mock_service_hass, mock_coordinator):
        """Test getting similar content with default limit."""
        await async_setup_services(mock_service_hass)

        calls = mock_service_hass.services.async_register.call_args_list
        similar_call = next(c for c in calls if c[0][1] == SERVICE_GET_SIMILAR_CONTENT)
        handler = similar_call[0][2]

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"media_id": "tt0468569"}

        result = await handler(service_call)

        assert "similar" in result

        # Verify default limit of 10 was used
        client = mock_service_hass.data[DOMAIN]["test_entry"]["client"]
        client.async_get_similar_content.assert_called_once_with(
            media_id="tt0468569",
            limit=10,
        )
