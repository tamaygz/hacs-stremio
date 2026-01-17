"""Sensor platform for Stremio integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
from .entity_helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=False)
class StremioSensorEntityDescription(SensorEntityDescription):
    """Describes Stremio sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_TYPES: tuple[StremioSensorEntityDescription, ...] = (
    StremioSensorEntityDescription(
        key="library_count",
        name="Library Count",
        icon="mdi:library",
        native_unit_of_measurement="items",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("library_count", 0),
    ),
    StremioSensorEntityDescription(
        key="current_watching",
        name="Current Watching",
        icon="mdi:play-circle",
        value_fn=lambda data: (
            data.get("current_watching", {}).get("title", "Nothing")
            if data.get("current_watching")
            else "Nothing"
        ),
        attributes_fn=lambda data: (
            {
                "type": data.get("current_watching", {}).get("type"),
                "progress_percent": data.get("current_watching", {}).get(
                    "progress_percent"
                ),
                "time_offset": data.get("current_watching", {}).get("time_offset"),
                "duration": data.get("current_watching", {}).get("duration"),
                "season": data.get("current_watching", {}).get("season"),
                "episode": data.get("current_watching", {}).get("episode"),
                "year": data.get("current_watching", {}).get("year"),
                "imdb_id": data.get("current_watching", {}).get("imdb_id"),
                "poster": data.get("current_watching", {}).get("poster"),
            }
            if data.get("current_watching")
            else {}
        ),
    ),
    StremioSensorEntityDescription(
        key="last_watched",
        name="Last Watched",
        icon="mdi:history",
        value_fn=lambda data: (
            data.get("last_watched", {}).get("title", "Nothing")
            if data.get("last_watched")
            else "Nothing"
        ),
        attributes_fn=lambda data: (
            {
                "type": data.get("last_watched", {}).get("type"),
                "progress_percent": data.get("last_watched", {}).get(
                    "progress_percent"
                ),
                "watched_at": data.get("last_watched", {}).get("watched_at"),
                "season": data.get("last_watched", {}).get("season"),
                "episode": data.get("last_watched", {}).get("episode"),
                "year": data.get("last_watched", {}).get("year"),
                "imdb_id": data.get("last_watched", {}).get("imdb_id"),
                "poster": data.get("last_watched", {}).get("poster"),
            }
            if data.get("last_watched")
            else {}
        ),
    ),
    StremioSensorEntityDescription(
        key="continue_watching_count",
        name="Continue Watching Count",
        icon="mdi:play-pause",
        native_unit_of_measurement="items",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("continue_watching", [])),
        attributes_fn=lambda data: {
            "items": [
                {
                    "title": item.get("title"),
                    "type": item.get("type"),
                    "progress_percent": (
                        round(
                            (item.get("progress", 0) / item.get("duration", 1)) * 100, 1
                        )
                        if item.get("duration", 0) > 0
                        else 0
                    ),
                }
                for item in data.get("continue_watching", [])[:5]
            ]
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stremio sensor platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: StremioDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Create sensor entities
    entities = [
        StremioSensor(coordinator, entry, description) for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class StremioSensor(CoordinatorEntity[StremioDataUpdateCoordinator], SensorEntity):
    """Representation of a Stremio sensor."""

    entity_description: StremioSensorEntityDescription

    def __init__(
        self,
        coordinator: StremioDataUpdateCoordinator,
        entry: ConfigEntry,
        description: StremioSensorEntityDescription,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
            description: Sensor entity description
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data and self.entity_description.attributes_fn:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return {}
