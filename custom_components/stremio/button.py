"""Button platform for Stremio integration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .apple_tv_handover import HandoverError, HandoverManager
from .const import CONF_ENABLE_APPLE_TV_HANDOVER, DOMAIN
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
        press_fn=_force_refresh,
    ),
    StremioButtonEntityDescription(
        key="refresh_library",
        name="Refresh Library",
        icon="mdi:library-shelves",
        press_fn=_refresh_library,
    ),
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

    # Create button entities
    entities = [
        StremioButton(coordinator, entry, description) for description in BUTTON_TYPES
    ]

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
