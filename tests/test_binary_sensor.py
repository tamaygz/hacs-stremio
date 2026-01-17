"""Tests for Stremio binary sensor entities."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.stremio.const import DOMAIN

from .conftest import MOCK_LIBRARY_ITEMS


class TestIsPlayingBinarySensor:
    """Tests for the is_playing binary sensor."""

    @pytest.mark.asyncio
    async def test_is_on_when_playing(self, mock_hass, mock_coordinator):
        """Test sensor is on when media is playing."""
        from custom_components.stremio.binary_sensor import StremioIsPlayingBinarySensor
        
        mock_coordinator.data = {"is_playing": True}
        
        sensor = StremioIsPlayingBinarySensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.is_on is True

    @pytest.mark.asyncio
    async def test_is_off_when_not_playing(self, mock_hass, mock_coordinator):
        """Test sensor is off when media is not playing."""
        from custom_components.stremio.binary_sensor import StremioIsPlayingBinarySensor
        
        mock_coordinator.data = {"is_playing": False}
        
        sensor = StremioIsPlayingBinarySensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.is_on is False

    @pytest.mark.asyncio
    async def test_device_class(self, mock_hass, mock_coordinator):
        """Test sensor device class."""
        from custom_components.stremio.binary_sensor import StremioIsPlayingBinarySensor
        
        sensor = StremioIsPlayingBinarySensor(mock_coordinator, "test_entry")
        
        # Should have appropriate device class
        assert sensor.device_class is not None

    @pytest.mark.asyncio
    async def test_unique_id(self, mock_hass, mock_coordinator):
        """Test sensor unique ID."""
        from custom_components.stremio.binary_sensor import StremioIsPlayingBinarySensor
        
        sensor = StremioIsPlayingBinarySensor(mock_coordinator, "test_entry")
        
        assert sensor.unique_id is not None
        assert "test_entry" in sensor.unique_id


class TestHasNewContentBinarySensor:
    """Tests for the has_new_content binary sensor."""

    @pytest.mark.asyncio
    async def test_is_on_when_new_content(self, mock_hass, mock_coordinator):
        """Test sensor is on when new content detected."""
        from custom_components.stremio.binary_sensor import StremioHasNewContentBinarySensor
        
        mock_coordinator.data = {
            "has_new_content": True,
            "library": MOCK_LIBRARY_ITEMS,
        }
        
        sensor = StremioHasNewContentBinarySensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.is_on is True

    @pytest.mark.asyncio
    async def test_is_off_when_no_new_content(self, mock_hass, mock_coordinator):
        """Test sensor is off when no new content."""
        from custom_components.stremio.binary_sensor import StremioHasNewContentBinarySensor
        
        mock_coordinator.data = {
            "has_new_content": False,
            "library": MOCK_LIBRARY_ITEMS,
        }
        
        sensor = StremioHasNewContentBinarySensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        assert sensor.is_on is False

    @pytest.mark.asyncio
    async def test_device_class(self, mock_hass, mock_coordinator):
        """Test sensor device class is update."""
        from custom_components.stremio.binary_sensor import StremioHasNewContentBinarySensor
        
        sensor = StremioHasNewContentBinarySensor(mock_coordinator, "test_entry")
        
        # Should indicate update availability
        assert sensor.device_class == BinarySensorDeviceClass.UPDATE

    @pytest.mark.asyncio
    async def test_extra_state_attributes(self, mock_hass, mock_coordinator):
        """Test extra state attributes."""
        from custom_components.stremio.binary_sensor import StremioHasNewContentBinarySensor
        
        mock_coordinator.data = {
            "has_new_content": True,
            "new_items": [{"title": "New Movie", "type": "movie"}],
        }
        
        sensor = StremioHasNewContentBinarySensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        attrs = sensor.extra_state_attributes
        
        # Should contain new items info
        assert attrs is not None


class TestBinarySensorSetup:
    """Tests for binary sensor platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_hass, mock_config_entry, mock_coordinator):
        """Test binary sensor platform setup."""
        from custom_components.stremio.binary_sensor import async_setup_entry
        
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }
        
        async_add_entities = MagicMock()
        
        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)
        
        # Should add at least 2 binary sensors
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) >= 2


class TestBinarySensorDeviceInfo:
    """Tests for binary sensor device info."""

    @pytest.mark.asyncio
    async def test_device_info(self, mock_hass, mock_coordinator):
        """Test device info is set correctly."""
        from custom_components.stremio.binary_sensor import StremioIsPlayingBinarySensor
        
        mock_coordinator.data = {"is_playing": False}
        
        sensor = StremioIsPlayingBinarySensor(mock_coordinator, "test_entry")
        sensor.hass = mock_hass
        
        device_info = sensor.device_info
        
        assert device_info is not None
        assert "identifiers" in device_info
        assert (DOMAIN, "test_entry") in device_info["identifiers"]
