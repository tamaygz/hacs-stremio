"""Tests for Stremio media player entity."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from homeassistant.components.media_player import MediaPlayerState, MediaType

from custom_components.stremio.const import DOMAIN

from .conftest import MOCK_CURRENT_MEDIA, MOCK_LIBRARY_ITEMS


@pytest.fixture
def mock_media_coordinator(mock_coordinator):
    """Create coordinator with media player data."""
    mock_coordinator.data = {
        "current_media": MOCK_CURRENT_MEDIA,
        "is_playing": True,
        "library": MOCK_LIBRARY_ITEMS,
    }
    return mock_coordinator


class TestStremioMediaPlayer:
    """Tests for the Stremio media player entity."""

    @pytest.mark.asyncio
    async def test_state_playing(self, mock_hass, mock_media_coordinator):
        """Test media player state when playing."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.state == MediaPlayerState.PLAYING

    @pytest.mark.asyncio
    async def test_state_paused(self, mock_hass, mock_coordinator):
        """Test media player state when paused."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        mock_coordinator.data = {
            "current_media": {**MOCK_CURRENT_MEDIA, "state": "paused"},
            "is_playing": False,
        }
        
        player = StremioMediaPlayer(mock_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.state == MediaPlayerState.PAUSED

    @pytest.mark.asyncio
    async def test_state_idle(self, mock_hass, mock_coordinator):
        """Test media player state when idle."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        mock_coordinator.data = {
            "current_media": None,
            "is_playing": False,
        }
        
        player = StremioMediaPlayer(mock_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.state == MediaPlayerState.IDLE

    @pytest.mark.asyncio
    async def test_media_title(self, mock_hass, mock_media_coordinator):
        """Test media title property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.media_title == "The Shawshank Redemption"

    @pytest.mark.asyncio
    async def test_media_position(self, mock_hass, mock_media_coordinator):
        """Test media position property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.media_position == 3834

    @pytest.mark.asyncio
    async def test_media_duration(self, mock_hass, mock_media_coordinator):
        """Test media duration property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.media_duration == 8520

    @pytest.mark.asyncio
    async def test_media_content_type(self, mock_hass, mock_media_coordinator):
        """Test media content type property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.media_content_type == MediaType.MOVIE

    @pytest.mark.asyncio
    async def test_media_image_url(self, mock_hass, mock_media_coordinator):
        """Test media image URL property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.media_image_url == "https://example.com/shawshank.jpg"

    @pytest.mark.asyncio
    async def test_device_info(self, mock_hass, mock_media_coordinator):
        """Test device info property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        device_info = player.device_info
        
        assert device_info is not None
        assert "identifiers" in device_info
        assert (DOMAIN, "test_entry") in device_info["identifiers"]

    @pytest.mark.asyncio
    async def test_unique_id(self, mock_hass, mock_media_coordinator):
        """Test unique ID property."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        assert player.unique_id == "test_entry_media_player"

    @pytest.mark.asyncio
    async def test_supported_features(self, mock_hass, mock_media_coordinator):
        """Test supported features."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        # Should have limited features (read-only)
        assert player.supported_features is not None

    @pytest.mark.asyncio
    async def test_extra_state_attributes(self, mock_hass, mock_media_coordinator):
        """Test extra state attributes."""
        from custom_components.stremio.media_player import StremioMediaPlayer
        
        player = StremioMediaPlayer(mock_media_coordinator, "test_entry")
        player.hass = mock_hass
        
        attrs = player.extra_state_attributes
        
        assert "media_id" in attrs
        assert attrs["media_id"] == "tt0111161"
