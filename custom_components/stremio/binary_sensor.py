"""Binary sensor platform for Stremio integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
from .entity_helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class StremioBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Stremio binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _get_series_with_new_episodes(data: dict[str, Any]) -> list[dict[str, str]]:
    """Get list of series that have unwatched episodes.

    A series is considered to have new episodes if:
    1. It's in the continue watching list (meaning it has been partially watched)
    2. It's of type "series"

    Args:
        data: Coordinator data

    Returns:
        List of series with unwatched episodes (title and imdb_id)
    """
    continue_watching = data.get("continue_watching", [])
    series_list = []
    seen_ids = set()

    for item in continue_watching:
        if item.get("type") == "series":
            imdb_id = item.get("imdb_id", "")
            if imdb_id and imdb_id not in seen_ids:
                seen_ids.add(imdb_id)
                series_list.append(
                    {
                        "title": item.get("title", "Unknown"),
                        "imdb_id": imdb_id,
                        "season": item.get("season"),
                        "episode": item.get("episode"),
                    }
                )

    return series_list


BINARY_SENSOR_TYPES: tuple[StremioBinarySensorEntityDescription, ...] = (
    StremioBinarySensorEntityDescription(
        key="is_watching",
        name="Is Watching",
        icon="mdi:play",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.get("current_watching") is not None,
        attributes_fn=lambda data: (
            {
                "title": data.get("current_watching", {}).get("title"),
                "type": data.get("current_watching", {}).get("type"),
                "progress_percent": data.get("current_watching", {}).get(
                    "progress_percent"
                ),
            }
            if data.get("current_watching")
            else {}
        ),
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
    StremioBinarySensorEntityDescription(
        key="has_new_episodes",
        name="Has New Episodes",
        icon="mdi:television-play",
        value_fn=lambda data: len(_get_series_with_new_episodes(data)) > 0,
        attributes_fn=lambda data: {
            "count": len(_get_series_with_new_episodes(data)),
            "series": _get_series_with_new_episodes(data),
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
        self._attr_device_info = get_device_info(entry)
        # Track previous value to avoid unnecessary updates
        self._previous_value: bool = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Only trigger a state update if the actual value has changed.
        This prevents unnecessary frontend refreshes.
        """
        current_value = self.is_on

        if current_value != self._previous_value:
            self._previous_value = current_value
            self.async_write_ha_state()

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
