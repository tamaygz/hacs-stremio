"""Button platform for Stremio integration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .apple_tv_handover import HandoverError, HandoverManager
from .const import (
    CONF_APPLE_TV_DEVICE,
    CONF_APPLE_TV_ENTITY_ID,
    CONF_ENABLE_APPLE_TV_HANDOVER,
    CONF_HANDOVER_METHOD,
    DEFAULT_HANDOVER_METHOD,
    DOMAIN,
)
from .coordinator import StremioDataUpdateCoordinator
from .entity_helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class StremioButtonEntityDescription(ButtonEntityDescription):
    """Describes Stremio button entity."""

    press_fn: (
        Callable[[StremioDataUpdateCoordinator], Coroutine[Any, Any, None]] | None
    ) = None


async def _force_refresh(coordinator: StremioDataUpdateCoordinator) -> None:
    """Force a full data refresh from the Stremio API.

    Args:
        coordinator: The data update coordinator.
    """
    _LOGGER.info("Force refresh requested")
    await coordinator.async_request_refresh()


async def _refresh_library(coordinator: StremioDataUpdateCoordinator) -> None:
    """Refresh the library data from the Stremio API.

    Args:
        coordinator: The data update coordinator.
    """
    _LOGGER.info("Library refresh requested")
    await coordinator.async_request_refresh()


BUTTON_TYPES: tuple[StremioButtonEntityDescription, ...] = (
    StremioButtonEntityDescription(
        key="force_refresh",
        name="Force Refresh",
        icon="mdi:refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        press_fn=_force_refresh,
    ),
    StremioButtonEntityDescription(
        key="refresh_library",
        name="Refresh Library",
        icon="mdi:library-shelves",
        entity_category=EntityCategory.DIAGNOSTIC,
        press_fn=_refresh_library,
    ),
)

# Apple TV handover button description (added conditionally)
APPLE_TV_HANDOVER_BUTTON = StremioButtonEntityDescription(
    key="handover_apple_tv",
    name="Handover to Apple TV",
    icon="mdi:apple",
    press_fn=None,  # Handled specially in StremioAppleTVHandoverButton
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stremio button platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: StremioDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Create standard button entities
    entities: list[ButtonEntity] = [
        StremioButton(coordinator, entry, description) for description in BUTTON_TYPES
    ]

    # Add Apple TV handover button if enabled in options
    if entry.options.get(CONF_ENABLE_APPLE_TV_HANDOVER, False):
        entities.append(
            StremioAppleTVHandoverButton(coordinator, entry, APPLE_TV_HANDOVER_BUTTON)
        )

    async_add_entities(entities)


class StremioButton(CoordinatorEntity[StremioDataUpdateCoordinator], ButtonEntity):
    """Representation of a Stremio button."""

    entity_description: StremioButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StremioDataUpdateCoordinator,
        entry: ConfigEntry,
        description: StremioButtonEntityDescription,
    ) -> None:
        """Initialize the button.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
            description: Entity description
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = get_device_info(entry)

    async def async_press(self) -> None:
        """Handle the button press.

        Calls the press function defined in the entity description.
        """
        if self.entity_description.press_fn is not None:
            await self.entity_description.press_fn(self.coordinator)


class StremioAppleTVHandoverButton(
    CoordinatorEntity[StremioDataUpdateCoordinator], ButtonEntity
):
    """Button to handover current watching content to Apple TV."""

    entity_description: StremioButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StremioDataUpdateCoordinator,
        entry: ConfigEntry,
        description: StremioButtonEntityDescription,
    ) -> None:
        """Initialize the Apple TV handover button.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
            description: Entity description
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = get_device_info(entry)

    @property
    def available(self) -> bool:
        """Return if the button is available.

        The button is only available when something is currently being watched.
        """
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("current_watching") is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        current = self.coordinator.data.get("current_watching")
        if current:
            return {
                "current_title": current.get("title"),
                "current_type": current.get("type"),
                "current_imdb_id": current.get("imdb_id"),
            }
        return {}

    async def async_press(self) -> None:
        """Handle the button press - handover current content to Apple TV.

        Discovers Apple TV devices and sends the current watching stream.
        """
        if not self.coordinator.data:
            _LOGGER.warning("No coordinator data available for handover")
            return

        current = self.coordinator.data.get("current_watching")
        if not current:
            _LOGGER.warning("Nothing currently watching to handover")
            return

        media_id = current.get("imdb_id")
        media_type = current.get("type", "movie")
        season = current.get("season")
        episode = current.get("episode")
        title = current.get("title")

        _LOGGER.info("Handover to Apple TV requested for: %s (%s)", title, media_id)

        # Get stream URL
        client = self.coordinator.client
        try:
            streams = await client.async_get_streams(
                media_id=media_id,
                media_type=media_type,
                season=season,
                episode=episode,
            )
        except Exception as err:
            _LOGGER.error("Failed to get streams for handover: %s", err)
            return

        if not streams:
            _LOGGER.warning("No streams available for handover")
            return

        stream_url = streams[0].get("url") or streams[0].get("externalUrl")
        if not stream_url:
            _LOGGER.warning("No playable stream URL found for handover")
            return

        # Use HandoverManager to discover and handover
        handover_manager = HandoverManager(self.hass)

        # Get configuration
        configured_device = self._entry.options.get(CONF_APPLE_TV_DEVICE, "")
        configured_entity = self._entry.options.get(CONF_APPLE_TV_ENTITY_ID, "")
        handover_method = self._entry.options.get(
            CONF_HANDOVER_METHOD, DEFAULT_HANDOVER_METHOD
        )

        try:
            # Determine device identifier based on method and configuration
            device_id: str | None = None

            if handover_method == "vlc" and configured_entity:
                # For VLC method, prefer the configured entity_id
                device_id = configured_entity
                _LOGGER.info(
                    "Using configured entity_id for VLC handover: %s", device_id
                )
            elif configured_device:
                # Use configured device name
                device_id = configured_device
                _LOGGER.info("Using configured Apple TV device: %s", device_id)
            else:
                # No configuration - discover and find an actual Apple TV
                devices = await handover_manager.discover_apple_tv_devices(timeout=5)
                if not devices:
                    _LOGGER.warning("No Apple TV devices discovered")
                    return

                # Try to find an actual Apple TV (not HomePod, MacBook, etc.)
                apple_tv_keywords = ["apple tv", "tv", "appletv"]
                for name in devices.keys():
                    name_lower = name.lower()
                    if any(kw in name_lower for kw in apple_tv_keywords):
                        device_id = name
                        _LOGGER.info(
                            "Auto-selected Apple TV device: %s (matched TV keyword)",
                            device_id,
                        )
                        break

                # If no TV found, use the first device but warn
                if not device_id:
                    device_id = list(devices.keys())[0]
                    _LOGGER.warning(
                        "No Apple TV found in discovered devices, using first device: %s. "
                        "Consider configuring the target device in integration options.",
                        device_id,
                    )

            _LOGGER.info("Handing over to Apple TV: %s", device_id)

            result = await handover_manager.handover(
                device_identifier=device_id,
                stream_url=stream_url,
                method=handover_method,
                title=title,
            )
            _LOGGER.info("Handover result: %s", result)

        except HandoverError as err:
            _LOGGER.error("Handover failed: %s", err)
        except Exception as err:
            _LOGGER.exception("Unexpected error during handover: %s", err)
