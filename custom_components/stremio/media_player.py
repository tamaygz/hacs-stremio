"""Media player platform for Stremio integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
from .entity_helpers import get_device_info
from .media_source import StremioMediaSource

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stremio media player platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: StremioDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Create media player entity
    async_add_entities([StremioMediaPlayer(coordinator, entry)])


class StremioMediaPlayer(
    CoordinatorEntity[StremioDataUpdateCoordinator], MediaPlayerEntity
):
    """Representation of a Stremio media player."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.BROWSE_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA
    )

    def __init__(
        self,
        coordinator: StremioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the media player.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_name = "Stremio"
        self._attr_has_entity_name = True
        self._attr_device_info = get_device_info(entry)
        # Track previous state to avoid unnecessary updates
        self._previous_state: MediaPlayerState | None = None
        self._previous_media_title: str | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Only trigger a state update if the actual state has changed.
        This prevents the media browser from resetting during navigation
        when the coordinator polls but nothing has changed.
        """
        current_state = self.state
        current_title = self.media_title

        # Only update if state or media actually changed
        if (
            current_state != self._previous_state
            or current_title != self._previous_media_title
        ):
            self._previous_state = current_state
            self._previous_media_title = current_title
            self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Skipping state update - no change (state=%s, title=%s)",
                current_state,
                current_title,
            )

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the media player."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_content_type(self) -> str | None:
        """Return the content type of current playing media."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            media_type = self.coordinator.data["current_watching"].get("type")
            if media_type == "series":
                return MediaType.TVSHOW
            elif media_type == "movie":
                return MediaType.MOVIE
        return None

    @property
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            return self.coordinator.data["current_watching"].get("title")
        return None

    @property
    def media_image_url(self) -> str | None:
        """Return the image URL of current playing media."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            return self.coordinator.data["current_watching"].get("poster")
        return None

    @property
    def media_position(self) -> int | None:
        """Return the position of current playing media in seconds."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            return self.coordinator.data["current_watching"].get("time_offset")
        return None

    @property
    def media_duration(self) -> int | None:
        """Return the duration of current playing media in seconds."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            return self.coordinator.data["current_watching"].get("duration")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            current = self.coordinator.data["current_watching"]
            return {
                "type": current.get("type"),
                "season": current.get("season"),
                "episode": current.get("episode"),
                "year": current.get("year"),
                "imdb_id": current.get("imdb_id"),
                "progress_percent": current.get("progress_percent"),
            }
        return {}

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper.

        This method enables the media browser UI in Home Assistant.
        It delegates to the StremioMediaSource implementation.

        Args:
            media_content_type: Content type to browse
            media_content_id: Content ID to browse (can be None for root,
                            a simple identifier like "library", or a full
                            media-source:// URI)

        Returns:
            BrowseMedia object with browsable content
        """
        _LOGGER.debug(
            "Browse media requested - type=%s, id=%s",
            media_content_type,
            media_content_id,
        )

        # Import MediaSourceItem
        from homeassistant.components.media_source import MediaSourceItem

        # Determine the identifier from media_content_id
        # It could be:
        # 1. None (root browsing)
        # 2. A simple identifier like "library" or "continue_watching"
        # 3. A full media-source URI like "media-source://stremio/library"
        if media_content_id and media_content_id.startswith("media-source://"):
            # Parse the URI to extract the identifier
            item = MediaSourceItem.from_uri(self.hass, media_content_id, self.entity_id)
        else:
            # Create MediaSourceItem directly with the identifier
            item = MediaSourceItem(
                hass=self.hass,
                domain=DOMAIN,
                identifier=media_content_id or "",
                target_media_player=self.entity_id,
            )

        # Get the media source and browse
        media_source = StremioMediaSource(self.hass)
        return await media_source.async_browse_media(item)

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media from a URL or file.

        Note: Stremio's API does not support remote playback control.
        This method logs the request but cannot initiate playback.
        Use the handover service to send content to external players.
        """
        _LOGGER.info(
            "Play media requested - type=%s, id=%s. Use handover service for playback.",
            media_type,
            media_id,
        )
