"""Sensor platform for Stremio integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
from .entity_helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class StremioSensorEntityDescription(SensorEntityDescription):
    """Describes Stremio sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _format_last_watched_title(data: dict[str, Any]) -> str:
    """Format the last watched title, including S##E## for TV shows.

    Args:
        data: Coordinator data dictionary

    Returns:
        Formatted title string (e.g., "Blacklist S01E02 The Freelancer")
    """
    last_watched = data.get("last_watched")
    if not last_watched:
        return "Nothing"

    title = last_watched.get("title", "Unknown")
    media_type = last_watched.get("type")
    season = last_watched.get("season")
    episode = last_watched.get("episode")
    episode_title = last_watched.get("episode_title")

    # For TV shows, format as "Title S##E## Episode Title"
    if media_type == "series" and season is not None and episode is not None:
        formatted = f"{title} S{season:02d}E{episode:02d}"
        if episode_title:
            formatted = f"{formatted} {episode_title}"
        return formatted

    return title


def _format_current_watching_title(data: dict[str, Any]) -> str:
    """Format the current watching title, including S##E## for TV shows.

    Args:
        data: Coordinator data dictionary

    Returns:
        Formatted title string (e.g., "Blacklist S01E02 The Freelancer")
    """
    current = data.get("current_watching")
    if not current:
        return "Nothing"

    title = current.get("title", "Unknown")
    media_type = current.get("type")
    season = current.get("season")
    episode = current.get("episode")
    episode_title = current.get("episode_title")

    # For TV shows, format as "Title S##E## Episode Title"
    if media_type == "series" and season is not None and episode is not None:
        formatted = f"{title} S{season:02d}E{episode:02d}"
        if episode_title:
            formatted = f"{formatted} {episode_title}"
        return formatted

    return title


SENSOR_TYPES: tuple[StremioSensorEntityDescription, ...] = (
    StremioSensorEntityDescription(
        key="library_count",
        name="Library Count",
        icon="mdi:library",
        native_unit_of_measurement="items",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("library_count", 0),
        attributes_fn=lambda data: {
            "items": [
                {
                    "title": item.get("title"),
                    "type": item.get("type"),
                    "poster": item.get("poster"),
                    "imdb_id": item.get("imdb_id"),
                    "id": item.get("id"),
                    "year": item.get("year"),
                    "progress_percent": (
                        round(
                            (item.get("progress", 0) / item.get("duration", 1)) * 100, 1
                        )
                        if item.get("duration", 0) > 0
                        else 0
                    ),
                }
                for item in data.get("library", [])
            ]
        },
    ),
    StremioSensorEntityDescription(
        key="current_watching",
        name="Current Watching",
        icon="mdi:play-circle",
        value_fn=_format_current_watching_title,
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
                "episode_title": data.get("current_watching", {}).get("episode_title"),
                "year": data.get("current_watching", {}).get("year"),
                "imdb_id": data.get("current_watching", {}).get("imdb_id"),
                "poster": data.get("current_watching", {}).get("poster"),
            }
            if data.get("current_watching")
            else {}
        ),
    ),
    StremioSensorEntityDescription(
        key="current_stream_url",
        name="Current Stream URL",
        icon="mdi:link-variant",
        value_fn=lambda data: (
            data.get("current_watching", {}).get("stream_url")
            if data.get("current_watching")
            else None
        ),
        attributes_fn=lambda data: (
            {
                "title": data.get("current_watching", {}).get("title"),
                "type": data.get("current_watching", {}).get("type"),
                "imdb_id": data.get("current_watching", {}).get("imdb_id"),
            }
            if data.get("current_watching")
            else {}
        ),
    ),
    StremioSensorEntityDescription(
        key="last_watched",
        name="Last Watched",
        icon="mdi:history",
        value_fn=_format_last_watched_title,
        attributes_fn=lambda data: (
            {
                "type": data.get("last_watched", {}).get("type"),
                "progress_percent": data.get("last_watched", {}).get(
                    "progress_percent"
                ),
                "watched_at": data.get("last_watched", {}).get("watched_at"),
                "season": data.get("last_watched", {}).get("season"),
                "episode": data.get("last_watched", {}).get("episode"),
                "episode_title": data.get("last_watched", {}).get("episode_title"),
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
                    "poster": item.get("poster"),
                    "imdb_id": item.get("imdb_id"),
                    "id": item.get("id"),
                    "year": item.get("year"),
                    "progress_percent": (
                        round(
                            (item.get("progress", 0) / item.get("duration", 1)) * 100, 1
                        )
                        if item.get("duration", 0) > 0
                        else 0
                    ),
                }
                for item in data.get("continue_watching", [])
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
        # Track previous value to avoid unnecessary updates
        self._previous_value: StateType = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Only trigger a state update if the actual value has changed.
        This prevents unnecessary frontend refreshes.
        """
        current_value = self.native_value

        # Log sensor data for debugging
        if self.entity_description.key in ["library_count", "continue_watching_count"]:
            _LOGGER.info(
                "Sensor %s: value=%s, previous=%s, coordinator_data_keys=%s",
                self.entity_description.key,
                current_value,
                self._previous_value,
                list(self.coordinator.data.keys()) if self.coordinator.data else "None",
            )
            if self.entity_description.key == "library_count" and self.coordinator.data:
                _LOGGER.info(
                    "Sensor library_count: library items in coordinator data: %d",
                    len(self.coordinator.data.get("library", [])),
                )
            if (
                self.entity_description.key == "continue_watching_count"
                and self.coordinator.data
            ):
                _LOGGER.info(
                    "Sensor continue_watching_count: items in coordinator data: %d",
                    len(self.coordinator.data.get("continue_watching", [])),
                )

        if current_value != self._previous_value:
            self._previous_value = current_value
            self.async_write_ha_state()

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
            attrs = self.entity_description.attributes_fn(self.coordinator.data)
            # Log attributes for debugging
            if self.entity_description.key in [
                "library_count",
                "continue_watching_count",
            ]:
                _LOGGER.info(
                    "Sensor %s: attributes items count: %d",
                    self.entity_description.key,
                    len(attrs.get("items", [])) if isinstance(attrs, dict) else 0,
                )
            return attrs
        return {}
