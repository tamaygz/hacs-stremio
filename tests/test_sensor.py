"""Tests for Stremio sensor entities."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from homeassistant.const import STATE_UNKNOWN

from custom_components.stremio.const import DOMAIN
from custom_components.stremio.sensor import (
    StremioSensor,
    SENSOR_TYPES,
    async_setup_entry,
)

from .conftest import MOCK_LIBRARY_ITEMS, MOCK_CONTINUE_WATCHING, MOCK_CURRENT_MEDIA


@pytest.fixture
def mock_sensor_coordinator(mock_coordinator):
    """Create coordinator with sensor-specific data."""
    mock_coordinator.data = {
        "library": MOCK_LIBRARY_ITEMS,
        "library_count": len(MOCK_LIBRARY_ITEMS),
        "continue_watching": MOCK_CONTINUE_WATCHING,
        "current_watching": {
            "title": "The Shawshank Redemption",
            "type": "movie",
            "progress_percent": 45.5,
            "time_offset": 3834,
            "duration": 8520,
            "year": 1994,
            "imdb_id": "tt0111161",
            "poster": "https://example.com/shawshank.jpg",
        },
        "last_watched": {
            "title": "The Dark Knight",
            "type": "movie",
            "progress_percent": 100,
            "watched_at": "2024-01-01T12:00:00Z",
            "year": 2008,
            "imdb_id": "tt0468569",
        },
        "is_playing": True,
    }
    return mock_coordinator


class TestCurrentWatchingSensor:
    """Tests for the current watching sensor."""

    @pytest.fixture
    def current_watching_sensor(self, mock_sensor_coordinator, mock_config_entry):
        """Create current watching sensor for testing."""
        description = next(d for d in SENSOR_TYPES if d.key == "current_watching")
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)
        return sensor

    @pytest.mark.asyncio
    async def test_sensor_state_playing(self, mock_hass, current_watching_sensor):
        """Test sensor state when media is playing."""
        current_watching_sensor.hass = mock_hass

        assert current_watching_sensor.native_value == "The Shawshank Redemption"
        assert current_watching_sensor.available is True

    @pytest.mark.asyncio
    async def test_sensor_state_idle(
        self, mock_hass, mock_coordinator, mock_config_entry
    ):
        """Test sensor state when idle."""
        mock_coordinator.data = {"current_watching": None}
        description = next(d for d in SENSOR_TYPES if d.key == "current_watching")
        sensor = StremioSensor(mock_coordinator, mock_config_entry, description)
        sensor.hass = mock_hass

        # Should show "Nothing" when no current watching
        assert sensor.native_value == "Nothing"

    @pytest.mark.asyncio
    async def test_sensor_attributes(self, mock_hass, current_watching_sensor):
        """Test sensor extra state attributes."""
        current_watching_sensor.hass = mock_hass

        attrs = current_watching_sensor.extra_state_attributes

        assert "type" in attrs
        assert attrs["type"] == "movie"
        assert "progress_percent" in attrs
        assert attrs["progress_percent"] == 45.5


class TestLibraryCountSensor:
    """Tests for the library count sensor."""

    @pytest.fixture
    def library_count_sensor(self, mock_sensor_coordinator, mock_config_entry):
        """Create library count sensor for testing."""
        description = next(d for d in SENSOR_TYPES if d.key == "library_count")
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)
        return sensor

    @pytest.mark.asyncio
    async def test_sensor_value(self, mock_hass, library_count_sensor):
        """Test library count value."""
        library_count_sensor.hass = mock_hass

        assert library_count_sensor.native_value == len(MOCK_LIBRARY_ITEMS)

    @pytest.mark.asyncio
    async def test_sensor_icon(self, library_count_sensor):
        """Test library sensor icon."""
        assert library_count_sensor.icon == "mdi:library"

    @pytest.mark.asyncio
    async def test_sensor_unit_of_measurement(self, library_count_sensor):
        """Test library sensor unit of measurement."""
        assert library_count_sensor.native_unit_of_measurement == "items"


class TestContinueWatchingCountSensor:
    """Tests for the continue watching count sensor."""

    @pytest.fixture
    def continue_watching_sensor(self, mock_sensor_coordinator, mock_config_entry):
        """Create continue watching count sensor for testing."""
        description = next(
            d for d in SENSOR_TYPES if d.key == "continue_watching_count"
        )
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)
        return sensor

    @pytest.mark.asyncio
    async def test_sensor_value(self, mock_hass, continue_watching_sensor):
        """Test continue watching count."""
        continue_watching_sensor.hass = mock_hass

        assert continue_watching_sensor.native_value == len(MOCK_CONTINUE_WATCHING)

    @pytest.mark.asyncio
    async def test_sensor_attributes(self, mock_hass, continue_watching_sensor):
        """Test continue watching attributes."""
        continue_watching_sensor.hass = mock_hass

        attrs = continue_watching_sensor.extra_state_attributes

        # Should contain items list
        assert "items" in attrs


class TestLastWatchedSensor:
    """Tests for the last watched sensor."""

    @pytest.fixture
    def last_watched_sensor(self, mock_sensor_coordinator, mock_config_entry):
        """Create last watched sensor for testing."""
        description = next(d for d in SENSOR_TYPES if d.key == "last_watched")
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)
        return sensor

    @pytest.mark.asyncio
    async def test_sensor_value(self, mock_hass, last_watched_sensor):
        """Test last watched sensor value."""
        last_watched_sensor.hass = mock_hass

        assert last_watched_sensor.native_value == "The Dark Knight"

    @pytest.mark.asyncio
    async def test_sensor_attributes(self, mock_hass, last_watched_sensor):
        """Test last watched attributes."""
        last_watched_sensor.hass = mock_hass

        attrs = last_watched_sensor.extra_state_attributes

        assert "type" in attrs
        assert "watched_at" in attrs


class TestSensorDeviceInfo:
    """Tests for sensor device info."""

    @pytest.mark.asyncio
    async def test_device_info(
        self, mock_hass, mock_sensor_coordinator, mock_config_entry
    ):
        """Test that sensors have proper device info."""
        description = SENSOR_TYPES[0]
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)
        sensor.hass = mock_hass

        device_info = sensor.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert (DOMAIN, mock_config_entry.entry_id) in device_info["identifiers"]

    @pytest.mark.asyncio
    async def test_unique_id(
        self, mock_hass, mock_sensor_coordinator, mock_config_entry
    ):
        """Test sensor unique ID."""
        description = SENSOR_TYPES[0]
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)
        sensor.hass = mock_hass

        assert sensor.unique_id is not None
        assert mock_config_entry.entry_id in sensor.unique_id


class TestSensorIcons:
    """Tests for sensor icons."""

    @pytest.mark.asyncio
    async def test_current_watching_icon(
        self, mock_sensor_coordinator, mock_config_entry
    ):
        """Test current watching sensor icon."""
        description = next(d for d in SENSOR_TYPES if d.key == "current_watching")
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)

        assert sensor.icon is not None
        assert sensor.icon.startswith("mdi:")
        assert sensor.icon == "mdi:play-circle"

    @pytest.mark.asyncio
    async def test_library_icon(self, mock_sensor_coordinator, mock_config_entry):
        """Test library sensor icon."""
        description = next(d for d in SENSOR_TYPES if d.key == "library_count")
        sensor = StremioSensor(mock_sensor_coordinator, mock_config_entry, description)

        assert sensor.icon is not None
        assert sensor.icon == "mdi:library"


class TestSensorSetup:
    """Tests for sensor platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(
        self, mock_hass, mock_config_entry, mock_coordinator
    ):
        """Test sensor platform setup."""
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator,
            }
        }

        async_add_entities = MagicMock()

        await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

        # Should add sensors for each description
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == len(SENSOR_TYPES)
