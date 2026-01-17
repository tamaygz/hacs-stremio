"""Tests for Stremio sensor entities."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from homeassistant.const import STATE_UNKNOWN

from custom_components.stremio.const import DOMAIN

from .conftest import MOCK_LIBRARY_ITEMS, MOCK_CONTINUE_WATCHING, MOCK_CURRENT_MEDIA


@pytest.fixture
def mock_sensor_coordinator(mock_coordinator):
    """Create coordinator with sensor-specific data."""
    mock_coordinator.data = {
        "library": MOCK_LIBRARY_ITEMS,
        "continue_watching": MOCK_CONTINUE_WATCHING,
        "current_media": MOCK_CURRENT_MEDIA,
        "is_playing": True,
        "library_count": len(MOCK_LIBRARY_ITEMS),
        "continue_watching_count": len(MOCK_CONTINUE_WATCHING),
    }
    return mock_coordinator


class TestCurrentMediaSensor:
    """Tests for the current media sensor."""

    @pytest.mark.asyncio
    async def test_sensor_state_playing(self, mock_hass, mock_sensor_coordinator):
        """Test sensor state when media is playing."""
        from custom_components.stremio.sensor import StremioCurrentMediaSensor
        
        sensor = StremioCurrentMediaSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.native_value == "The Shawshank Redemption"
        assert sensor.available is True

    @pytest.mark.asyncio
    async def test_sensor_state_idle(self, mock_hass, mock_coordinator):
        """Test sensor state when idle."""
        from custom_components.stremio.sensor import StremioCurrentMediaSensor
        
        mock_coordinator.data = {"current_media": None, "is_playing": False}
        
        sensor = StremioCurrentMediaSensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        # Should show idle/none state
        assert sensor.native_value in [None, STATE_UNKNOWN, "None", "Idle"]

    @pytest.mark.asyncio
    async def test_sensor_attributes(self, mock_hass, mock_sensor_coordinator):
        """Test sensor extra state attributes."""
        from custom_components.stremio.sensor import StremioCurrentMediaSensor
        
        sensor = StremioCurrentMediaSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        attrs = sensor.extra_state_attributes
        
        assert "media_type" in attrs or "type" in attrs
        assert "position" in attrs or "media_position" in attrs


class TestLibraryCountSensor:
    """Tests for the library count sensor."""

    @pytest.mark.asyncio
    async def test_sensor_value(self, mock_hass, mock_sensor_coordinator):
        """Test library count value."""
        from custom_components.stremio.sensor import StremioLibraryCountSensor
        
        sensor = StremioLibraryCountSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.native_value == len(MOCK_LIBRARY_ITEMS)

    @pytest.mark.asyncio
    async def test_sensor_attributes_contain_items(self, mock_hass, mock_sensor_coordinator):
        """Test that library items are in attributes."""
        from custom_components.stremio.sensor import StremioLibraryCountSensor
        
        sensor = StremioLibraryCountSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        attrs = sensor.extra_state_attributes
        
        # Should contain library items or summary
        assert "items" in attrs or "movies_count" in attrs or "series_count" in attrs


class TestContinueWatchingSensor:
    """Tests for the continue watching sensor."""

    @pytest.mark.asyncio
    async def test_sensor_value(self, mock_hass, mock_sensor_coordinator):
        """Test continue watching count."""
        from custom_components.stremio.sensor import StremioContinueWatchingSensor
        
        sensor = StremioContinueWatchingSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.native_value == len(MOCK_CONTINUE_WATCHING)

    @pytest.mark.asyncio
    async def test_sensor_attributes(self, mock_hass, mock_sensor_coordinator):
        """Test continue watching attributes."""
        from custom_components.stremio.sensor import StremioContinueWatchingSensor
        
        sensor = StremioContinueWatchingSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        attrs = sensor.extra_state_attributes
        
        # Should contain items list
        assert "items" in attrs


class TestSensorDeviceInfo:
    """Tests for sensor device info."""

    @pytest.mark.asyncio
    async def test_device_info(self, mock_hass, mock_sensor_coordinator):
        """Test that sensors have proper device info."""
        from custom_components.stremio.sensor import StremioCurrentMediaSensor
        
        sensor = StremioCurrentMediaSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        device_info = sensor.device_info
        
        assert device_info is not None
        assert "identifiers" in device_info

    @pytest.mark.asyncio
    async def test_unique_id(self, mock_hass, mock_sensor_coordinator):
        """Test sensor unique ID."""
        from custom_components.stremio.sensor import StremioCurrentMediaSensor
        
        sensor = StremioCurrentMediaSensor(mock_sensor_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.unique_id is not None
        assert "test_entry" in sensor.unique_id


class TestSensorIcons:
    """Tests for sensor icons."""

    @pytest.mark.asyncio
    async def test_current_media_icon(self, mock_hass, mock_sensor_coordinator):
        """Test current media sensor icon."""
        from custom_components.stremio.sensor import StremioCurrentMediaSensor
        
        sensor = StremioCurrentMediaSensor(mock_sensor_coordinator, "test_entry")
        
        assert sensor.icon is not None
        assert sensor.icon.startswith("mdi:")

    @pytest.mark.asyncio
    async def test_library_icon(self, mock_hass, mock_sensor_coordinator):
        """Test library sensor icon."""
        from custom_components.stremio.sensor import StremioLibraryCountSensor
        
        sensor = StremioLibraryCountSensor(mock_sensor_coordinator, "test_entry")
        
        assert sensor.icon is not None
