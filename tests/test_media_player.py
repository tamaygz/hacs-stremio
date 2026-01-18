"""Tests for Stremio media player entity."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.components.media_player import MediaPlayerState, MediaType
from homeassistant.core import HomeAssistant

from custom_components.stremio.const import DOMAIN
from custom_components.stremio.media_player import StremioMediaPlayer, async_setup_entry

from .conftest import MOCK_CURRENT_MEDIA, MOCK_LIBRARY_ITEMS


@pytest.fixture
def mock_media_coordinator(mock_coordinator):
    """Create coordinator with media player data."""
    mock_coordinator.data = {
        "current_watching": {
            "title": "The Shawshank Redemption",
            "type": "movie",
            "poster": "https://example.com/shawshank.jpg",
            "time_offset": 3834,  # seconds
            "duration": 8520,  # seconds
            "imdb_id": "tt0111161",
            "year": 1994,
            "progress_percent": 45.5,
        },
        "library": MOCK_LIBRARY_ITEMS,
    }
    return mock_coordinator


class TestStremioMediaPlayer:
    """Tests for the Stremio media player entity."""

    @pytest.mark.asyncio
    async def test_state_playing(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test media player state when playing."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        assert player.state == MediaPlayerState.PLAYING

    @pytest.mark.asyncio
    async def test_state_idle(self, hass: HomeAssistant, mock_coordinator, mock_config_entry):
        """Test media player state when idle."""
        mock_coordinator.data = {
            "current_watching": None,
        }

        player = StremioMediaPlayer(mock_coordinator, mock_config_entry)
        player.hass = hass

        assert player.state == MediaPlayerState.IDLE

    @pytest.mark.asyncio
    async def test_media_title(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test media title property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        assert player.media_title == "The Shawshank Redemption"

    @pytest.mark.asyncio
    async def test_media_position(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test media position property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        assert player.media_position == 3834

    @pytest.mark.asyncio
    async def test_media_duration(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test media duration property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        assert player.media_duration == 8520

    @pytest.mark.asyncio
    async def test_media_content_type(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test media content type property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        assert player.media_content_type == MediaType.MOVIE

    @pytest.mark.asyncio
    async def test_media_content_type_series(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test media content type for series."""
        mock_coordinator.data = {
            "current_watching": {
                "title": "Breaking Bad",
                "type": "series",
                "season": 1,
                "episode": 1,
            },
        }

        player = StremioMediaPlayer(mock_coordinator, mock_config_entry)
        player.hass = hass

        assert player.media_content_type == MediaType.TVSHOW

    @pytest.mark.asyncio
    async def test_media_image_url(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test media image URL property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        assert player.media_image_url == "https://example.com/shawshank.jpg"

    @pytest.mark.asyncio
    async def test_device_info(
        self, hass: HomeAssistant, mock_media_coordinator, mock_config_entry
    ):
        """Test device info property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = hass

        device_info = player.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert (DOMAIN, mock_config_entry.entry_id) in device_info["identifiers"]

    @pytest.mark.asyncio
    async def test_unique_id(
        self, mock_hass, mock_media_coordinator, mock_config_entry
    ):
        """Test unique ID property."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = mock_hass

        assert player.unique_id == f"{mock_config_entry.entry_id}_media_player"

    @pytest.mark.asyncio
    async def test_supported_features(
        self, mock_hass, mock_media_coordinator, mock_config_entry
    ):
        """Test supported features."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = mock_hass

        # Should have browse media and play media features
        assert player.supported_features is not None

    @pytest.mark.asyncio
    async def test_extra_state_attributes(
        self, mock_hass, mock_media_coordinator, mock_config_entry
    ):
        """Test extra state attributes."""
        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = mock_hass

        attrs = player.extra_state_attributes

        assert "imdb_id" in attrs
        assert attrs["imdb_id"] == "tt0111161"
        assert "type" in attrs
        assert attrs["type"] == "movie"

    @pytest.mark.asyncio
    async def test_extra_state_attributes_empty_when_idle(
        self, mock_hass, mock_coordinator, mock_config_entry
    ):
        """Test extra state attributes are empty when idle."""
        mock_coordinator.data = {"current_watching": None}

        player = StremioMediaPlayer(mock_coordinator, mock_config_entry)
        player.hass = mock_hass

        attrs = player.extra_state_attributes

        assert attrs == {}


class TestMediaPlayerSetup:
    """Tests for media player platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(
        self, mock_hass, mock_config_entry, mock_coordinator
    ):
        """Test media player platform setup."""
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }

        async_add_entities = MagicMock()

        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        # Should add one media player entity
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], StremioMediaPlayer)


class TestMediaPlayerBrowse:
    """Tests for media player browsing functionality."""

    @pytest.mark.asyncio
    async def test_async_browse_media_root(
        self, mock_hass, mock_media_coordinator, mock_config_entry
    ):
        """Test browsing media at root level."""
        # Set up hass.data with coordinator
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_media_coordinator,
            }
        }

        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = mock_hass

        # Browse root level
        result = await player.async_browse_media()

        # Should return BrowseMedia object with children
        assert result is not None
        assert result.title == "Stremio"
        assert result.can_expand is True
        assert result.can_play is False
        assert result.children is not None
        assert len(result.children) > 0

    @pytest.mark.asyncio
    async def test_async_browse_media_library(
        self, mock_hass, mock_media_coordinator, mock_config_entry
    ):
        """Test browsing library section."""
        # Set up hass.data with coordinator
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_media_coordinator,
            }
        }

        player = StremioMediaPlayer(mock_media_coordinator, mock_config_entry)
        player.hass = mock_hass

        # Browse library
        result = await player.async_browse_media(media_content_id="library")

        # Should return library items
        assert result is not None
        assert result.title == "Library"
        assert result.can_expand is True
