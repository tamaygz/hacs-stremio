"""Tests for Stremio binary sensor entities."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.stremio.const import DOMAIN
from custom_components.stremio.binary_sensor import (
    StremioBinarySensor,
    BINARY_SENSOR_TYPES,
    async_setup_entry,
)

from .conftest import MOCK_LIBRARY_ITEMS, MOCK_CONTINUE_WATCHING


class TestIsWatchingBinarySensor:
    """Tests for the is_watching binary sensor."""

    @pytest.fixture
    def is_watching_sensor(self, mock_coordinator, mock_config_entry):
        """Create is_watching sensor for testing."""
        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "is_watching")
        sensor = StremioBinarySensor(mock_coordinator, mock_config_entry, description)
        return sensor

    @pytest.mark.asyncio
    async def test_is_on_when_watching(self, mock_hass, mock_coordinator, is_watching_sensor):
        """Test sensor is on when media is being watched."""
        mock_coordinator.data = {
            "current_watching": {"title": "Test Movie", "type": "movie", "progress_percent": 50}
        }
        is_watching_sensor.hass = mock_hass
        
        assert is_watching_sensor.is_on is True

    @pytest.mark.asyncio
    async def test_is_off_when_not_watching(self, mock_hass, mock_coordinator, is_watching_sensor):
        """Test sensor is off when no media is being watched."""
        mock_coordinator.data = {"current_watching": None}
        is_watching_sensor.hass = mock_hass
        
        assert is_watching_sensor.is_on is False

    @pytest.mark.asyncio
    async def test_device_class(self, is_watching_sensor):
        """Test sensor device class."""
        assert is_watching_sensor.device_class == BinarySensorDeviceClass.RUNNING

    @pytest.mark.asyncio
    async def test_unique_id(self, mock_config_entry, is_watching_sensor):
        """Test sensor unique ID."""
        assert is_watching_sensor.unique_id is not None
        assert mock_config_entry.entry_id in is_watching_sensor.unique_id
        assert "is_watching" in is_watching_sensor.unique_id

    @pytest.mark.asyncio
    async def test_extra_state_attributes(self, mock_hass, mock_coordinator, is_watching_sensor):
        """Test extra state attributes."""
        mock_coordinator.data = {
            "current_watching": {"title": "Test Movie", "type": "movie", "progress_percent": 75}
        }
        is_watching_sensor.hass = mock_hass
        
        attrs = is_watching_sensor.extra_state_attributes
        
        assert attrs is not None
        assert attrs.get("title") == "Test Movie"
        assert attrs.get("type") == "movie"
        assert attrs.get("progress_percent") == 75


class TestHasContinueWatchingBinarySensor:
    """Tests for the has_continue_watching binary sensor."""

    @pytest.fixture
    def continue_watching_sensor(self, mock_coordinator, mock_config_entry):
        """Create has_continue_watching sensor for testing."""
        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "has_continue_watching")
        sensor = StremioBinarySensor(mock_coordinator, mock_config_entry, description)
        return sensor

    @pytest.mark.asyncio
    async def test_is_on_when_has_continue_watching(self, mock_hass, mock_coordinator, continue_watching_sensor):
        """Test sensor is on when there are items to continue watching."""
        mock_coordinator.data = {
            "continue_watching": MOCK_CONTINUE_WATCHING,
        }
        continue_watching_sensor.hass = mock_hass
        
        assert continue_watching_sensor.is_on is True

    @pytest.mark.asyncio
    async def test_is_off_when_no_continue_watching(self, mock_hass, mock_coordinator, continue_watching_sensor):
        """Test sensor is off when no items to continue watching."""
        mock_coordinator.data = {
            "continue_watching": [],
        }
        continue_watching_sensor.hass = mock_hass
        
        assert continue_watching_sensor.is_on is False

    @pytest.mark.asyncio
    async def test_extra_state_attributes(self, mock_hass, mock_coordinator, continue_watching_sensor):
        """Test extra state attributes contain count."""
        mock_coordinator.data = {
            "continue_watching": MOCK_CONTINUE_WATCHING,
        }
        continue_watching_sensor.hass = mock_hass
        
        attrs = continue_watching_sensor.extra_state_attributes
        
        assert attrs is not None
        assert "count" in attrs
        assert attrs["count"] == len(MOCK_CONTINUE_WATCHING)


class TestBinarySensorSetup:
    """Tests for binary sensor platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_hass, mock_config_entry, mock_coordinator):
        """Test binary sensor platform setup."""
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }
        
        async_add_entities = MagicMock()
        
        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)
        
        # Should add binary sensors for each description
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == len(BINARY_SENSOR_TYPES)


class TestBinarySensorDeviceInfo:
    """Tests for binary sensor device info."""

    @pytest.mark.asyncio
    async def test_device_info(self, mock_hass, mock_coordinator, mock_config_entry):
        """Test device info is set correctly."""
        description = BINARY_SENSOR_TYPES[0]
        sensor = StremioBinarySensor(mock_coordinator, mock_config_entry, description)
        sensor.hass = mock_hass
        
        device_info = sensor.device_info
        
        assert device_info is not None
        assert "identifiers" in device_info
        assert (DOMAIN, mock_config_entry.entry_id) in device_info["identifiers"]
