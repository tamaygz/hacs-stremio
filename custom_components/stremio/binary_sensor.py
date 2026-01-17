"""Binary sensor platform for Stremio integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class StremioBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Stremio binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool] = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] = None


BINARY_SENSOR_TYPES: tuple[StremioBinarySensorEntityDescription, ...] = (
    StremioBinarySensorEntityDescription(
        key="is_watching",
        name="Is Watching",
        icon="mdi:play",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.get("current_watching") is not None,
        attributes_fn=lambda data: {
            "title": data.get("current_watching", {}).get("title"),
            "type": data.get("current_watching", {}).get("type"),
            "progress_percent": data.get("current_watching", {}).get("progress_percent"),
        }
        if data.get("current_watching")
        else {},
    ),
    StremioBinarySensorEntityDescription(
        key="has_continue_watching",
        name="Has Continue Watching",
        icon="mdi:play-pause",
        value_fn=lambda data: len(data.get("continue_watching", [])) > 0,
        attributes_fn=lambda data: {
            "count": len(data.get("continue_watching", [])),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stremio binary sensor platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: StremioDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Create binary sensor entities
    entities = [
        StremioBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class StremioBinarySensor(
    CoordinatorEntity[StremioDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of a Stremio binary sensor."""

    entity_description: StremioBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: StremioDataUpdateCoordinator,
        entry: ConfigEntry,
        description: StremioBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
            description: Binary sensor entity description
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Stremio {entry.data.get('email', 'Account')}",
            "manufacturer": "Stremio",
            "model": "Stremio Integration",
            "entry_type": "service",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data and self.entity_description.attributes_fn:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return {}
