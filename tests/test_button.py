"""Tests for Stremio button platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, EntityCategory
from homeassistant.core import HomeAssistant

from custom_components.stremio.button import (
    APPLE_TV_HANDOVER_BUTTON,
    BUTTON_TYPES,
    StremioAppleTVHandoverButton,
    StremioButton,
    async_setup_entry,
)
from custom_components.stremio.const import CONF_ENABLE_APPLE_TV_HANDOVER, DOMAIN

from .conftest import MOCK_LIBRARY_ITEMS, MOCK_STREAMS


@pytest.fixture
def mock_button_coordinator(mock_coordinator):
    """Create coordinator with button-specific data."""
    mock_coordinator.data = {
        "library": MOCK_LIBRARY_ITEMS,
        "current_watching": {
            "title": "The Shawshank Redemption",
            "type": "movie",
            "imdb_id": "tt0111161",
            "season": None,
            "episode": None,
        },
    }
    mock_coordinator.async_request_refresh = AsyncMock()
    return mock_coordinator


class TestStremioButton:
    """Tests for the Stremio button entity."""

    @pytest.mark.asyncio
    async def test_button_press(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button press calls coordinator refresh."""
        button = StremioButton(
            mock_button_coordinator, mock_config_entry, BUTTON_TYPES[0]
        )
        button.hass = hass

        await button.async_press()

        # Should trigger coordinator refresh
        mock_button_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_button_unique_id(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button unique ID generation."""
        button = StremioButton(
            mock_button_coordinator, mock_config_entry, BUTTON_TYPES[0]
        )
        button.hass = hass

        expected_id = f"{mock_config_entry.entry_id}_{BUTTON_TYPES[0].key}"
        assert button.unique_id == expected_id

    @pytest.mark.asyncio
    async def test_button_device_info(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button has correct device info."""
        button = StremioButton(
            mock_button_coordinator, mock_config_entry, BUTTON_TYPES[0]
        )
        button.hass = hass

        assert button.device_info is not None
        assert "identifiers" in button.device_info

    @pytest.mark.asyncio
    async def test_button_entity_category(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button has diagnostic entity category."""
        button = StremioButton(
            mock_button_coordinator, mock_config_entry, BUTTON_TYPES[0]
        )
        button.hass = hass

        # All button types should be diagnostic
        assert button.entity_description.entity_category == EntityCategory.DIAGNOSTIC


class TestAppleTVHandoverButton:
    """Tests for the Apple TV handover button."""

    @pytest.mark.asyncio
    async def test_button_available_when_watching(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button is available when something is being watched."""
        button = StremioAppleTVHandoverButton(
            mock_button_coordinator, mock_config_entry, APPLE_TV_HANDOVER_BUTTON
        )
        button.hass = hass

        assert button.available is True

    @pytest.mark.asyncio
    async def test_button_unavailable_when_not_watching(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test button is unavailable when nothing is being watched."""
        mock_coordinator.data = {"current_watching": None}

        button = StremioAppleTVHandoverButton(
            mock_coordinator, mock_config_entry, APPLE_TV_HANDOVER_BUTTON
        )
        button.hass = hass

        assert button.available is False

    @pytest.mark.asyncio
    async def test_button_extra_state_attributes(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button shows current media in attributes."""
        button = StremioAppleTVHandoverButton(
            mock_button_coordinator, mock_config_entry, APPLE_TV_HANDOVER_BUTTON
        )
        button.hass = hass

        attrs = button.extra_state_attributes

        assert "current_title" in attrs
        assert attrs["current_title"] == "The Shawshank Redemption"
        assert attrs["current_type"] == "movie"
        assert attrs["current_imdb_id"] == "tt0111161"

    @pytest.mark.asyncio
    async def test_button_press_no_watching(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test button press when nothing is being watched."""
        mock_coordinator.data = {"current_watching": None}

        button = StremioAppleTVHandoverButton(
            mock_coordinator, mock_config_entry, APPLE_TV_HANDOVER_BUTTON
        )
        button.hass = hass

        # Should return early without error
        await button.async_press()

    @pytest.mark.asyncio
    async def test_button_press_with_stream(
        self, hass: HomeAssistant, mock_button_coordinator, mock_config_entry
    ):
        """Test button press gets stream and attempts handover."""
        from unittest.mock import patch

        mock_client = AsyncMock()
        mock_client.async_get_streams = AsyncMock(return_value=MOCK_STREAMS)

        mock_button_coordinator.client = mock_client

        button = StremioAppleTVHandoverButton(
            mock_button_coordinator, mock_config_entry, APPLE_TV_HANDOVER_BUTTON
        )
        button.hass = hass

        # Mock HandoverManager to avoid actual Apple TV discovery
        with patch(
            "custom_components.stremio.button.HandoverManager"
        ) as mock_handover_class:
            mock_handover = AsyncMock()
            mock_handover.handover = AsyncMock(return_value={"success": True})
            mock_handover.discover_apple_tv_devices = AsyncMock(
                return_value={"Living Room Apple TV": "device_123"}
            )
            mock_handover_class.return_value = mock_handover

            await button.async_press()

            # Should have called async_get_streams
            mock_client.async_get_streams.assert_called_once()


class TestButtonPlatformSetup:
    """Tests for button platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_without_apple_tv(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test button platform setup without Apple TV handover."""
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinator": mock_coordinator}
        }

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, async_add_entities)

        # Should add only standard buttons (not Apple TV button)
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == len(BUTTON_TYPES)
        assert all(isinstance(e, StremioButton) for e in entities)

    @pytest.mark.asyncio
    async def test_async_setup_entry_with_apple_tv(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test button platform setup with Apple TV handover enabled."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a new config entry with Apple TV enabled
        entry_with_apple_tv = MockConfigEntry(
            domain=DOMAIN,
            data=mock_config_entry.data,
            options={
                **mock_config_entry.options,
                CONF_ENABLE_APPLE_TV_HANDOVER: True,
            },
            unique_id=mock_config_entry.unique_id,
            title=mock_config_entry.title,
        )
        entry_with_apple_tv.add_to_hass(hass)

        hass.data[DOMAIN] = {
            entry_with_apple_tv.entry_id: {"coordinator": mock_coordinator}
        }

        async_add_entities = MagicMock()

        await async_setup_entry(hass, entry_with_apple_tv, async_add_entities)

        # Should add standard buttons + Apple TV button
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == len(BUTTON_TYPES) + 1

        # Check we have both types
        button_types = [type(e).__name__ for e in entities]
        assert "StremioButton" in button_types
        assert "StremioAppleTVHandoverButton" in button_types
