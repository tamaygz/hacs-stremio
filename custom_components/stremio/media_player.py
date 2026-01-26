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
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .apple_tv_handover import HandoverError, HandoverManager
from .const import (
    CONF_APPLE_TV_CREDENTIALS,
    CONF_APPLE_TV_ENTITY_ID,
    CONF_APPLE_TV_IDENTIFIER,
    CONF_ENABLE_APPLE_TV_HANDOVER,
    CONF_HANDOVER_METHOD,
    DEFAULT_ENABLE_APPLE_TV_HANDOVER,
    DEFAULT_HANDOVER_METHOD,
    DOMAIN,
)
from .coordinator import StremioDataUpdateCoordinator
from .entity_helpers import get_device_info
from .media_source import StremioMediaSource
from .stremio_client import StremioClient, StremioConnectionError

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
    client: StremioClient = hass.data[DOMAIN][entry.entry_id]["client"]

    # Create media player entity
    async_add_entities([StremioMediaPlayer(coordinator, client, entry)])


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
        client: StremioClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the media player.

        Args:
            coordinator: Data update coordinator
            client: Stremio API client
            entry: Config entry
        """
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_translation_key = "stremio"
        self._attr_has_entity_name = True
        self._attr_device_info = get_device_info(entry)
        # Track previous state to avoid unnecessary updates
        self._previous_state: MediaPlayerState | None = None
        self._previous_media_title: str | None = None
        self._previous_media_id: str | None = None
        # Flag to allow state updates (set by handover operations)
        self._pending_state_update: bool = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        This method is very conservative about triggering state updates to prevent
        the media browser from resetting during navigation. State updates only occur:
        1. When _pending_state_update flag is set (after handover operations)
        2. When the entity is first initialized (previous values are None)

        Regular polling updates are suppressed to keep the media browser stable.
        """
        current_state = self.state
        current_title = self.media_title
        current_media_id = self._get_current_media_id()

        # Check if this is the first update (initialization)
        is_first_update = (
            self._previous_state is None
            and self._previous_media_title is None
            and self._previous_media_id is None
        )

        # Check if anything actually changed
        state_changed = current_state != self._previous_state
        title_changed = current_title != self._previous_media_title
        media_id_changed = current_media_id != self._previous_media_id
        something_changed = state_changed or title_changed or media_id_changed

        # Only update state if:
        # 1. This is the first update (initialization), OR
        # 2. A pending update was requested (from handover), OR
        # 3. The state went from PLAYING to IDLE or vice versa (major state change)
        should_update = (
            is_first_update
            or self._pending_state_update
            or (something_changed and state_changed)
        )

        if should_update and something_changed:
            _LOGGER.debug(
                "Media player state update: state=%s (changed=%s), title=%s (changed=%s), "
                "media_id=%s (changed=%s), pending=%s, first=%s",
                current_state,
                state_changed,
                current_title,
                title_changed,
                current_media_id,
                media_id_changed,
                self._pending_state_update,
                is_first_update,
            )
            self._previous_state = current_state
            self._previous_media_title = current_title
            self._previous_media_id = current_media_id
            self._pending_state_update = False  # Clear the flag
            self.async_write_ha_state()
        else:
            # Still update the tracked values to stay in sync, but don't trigger UI update
            if something_changed:
                _LOGGER.debug(
                    "Suppressing state update to avoid media browser reset "
                    "(state=%s, title=%s, media_id=%s)",
                    current_state,
                    current_title,
                    current_media_id,
                )
                self._previous_state = current_state
                self._previous_media_title = current_title
                self._previous_media_id = current_media_id

    def request_state_update(self) -> None:
        """Request a state update on the next coordinator update.

        Call this after a handover operation to ensure the UI reflects
        the new state.
        """
        self._pending_state_update = True
        # Trigger an immediate update
        self._handle_coordinator_update()

    def _get_current_media_id(self) -> str | None:
        """Get the current media IMDB ID from coordinator data."""
        if self.coordinator.data and self.coordinator.data.get("current_watching"):
            return self.coordinator.data["current_watching"].get("imdb_id")
        return None

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
            attrs = {
                "type": current.get("type"),
                "season": current.get("season"),
                "episode": current.get("episode"),
                "episode_title": current.get("episode_title"),
                "year": current.get("year"),
                "imdb_id": current.get("imdb_id"),
                "progress_percent": current.get("progress_percent"),
                "poster": current.get("poster"),
                # Extended metadata (may be populated from metadata fetch)
                "description": current.get("description"),
                "genres": current.get("genres", []),
                "cast": current.get("cast", []),
                "director": current.get("director"),
                "backdrop_url": current.get("backdrop"),
                "runtime": current.get("duration"),
                "rating": current.get("rating"),
                "series_title": current.get("series_title"),
            }
            # Remove None values to keep attributes clean
            return {k: v for k, v in attrs.items() if v is not None}
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
        """Play media from the media browser.

        When a media item is selected from the browser, this method extracts the
        media information and triggers a handover to Apple TV if configured.

        The media_id format from StremioMediaSource (via async_resolve_media):
        - media-source://stremio/{type}/{imdb_id}#{stream_index}
        - media-source://stremio/{type}/{imdb_id}/{season}/{episode}#{stream_index}

        Direct URL format (from external calls):
        - http(s)://... (direct stream URL)

        Args:
            media_type: The type of media content
            media_id: The media content identifier or URL
            **kwargs: Additional arguments (e.g., extra for metadata)
        """
        _LOGGER.debug(
            "Play media requested - type=%s, id=%s, kwargs=%s",
            media_type,
            media_id,
            kwargs,
        )

        # Check if Apple TV handover is enabled
        options = self._entry.options
        enable_handover = options.get(
            CONF_ENABLE_APPLE_TV_HANDOVER, DEFAULT_ENABLE_APPLE_TV_HANDOVER
        )
        apple_tv_entity_id = options.get(CONF_APPLE_TV_ENTITY_ID)

        if not enable_handover or not apple_tv_entity_id:
            _LOGGER.info(
                "Apple TV handover not configured. Enable it in integration options "
                "to play media on Apple TV. media_id=%s",
                media_id,
            )
            return

        # Parse the media_id to extract stream information and media metadata
        stream_url = None
        title = None
        media_info: dict[str, Any] = {}

        # Case 1: Direct HTTP(S) URL
        if media_id.startswith(("http://", "https://")):
            stream_url = media_id
            _LOGGER.debug("Direct stream URL provided: %s", stream_url[:100])
            # For direct URLs, we have minimal info
            media_info = {"stream_url": stream_url}

        # Case 2: media-source:// URI format from media browser
        elif media_id.startswith("media-source://stremio/"):
            # Format: media-source://stremio/{type}/{imdb_id}[/{season}/{episode}][#{stream_index}]
            identifier = media_id.replace("media-source://stremio/", "")
            stream_url, title, media_info = await self._resolve_and_build_media_info(
                identifier
            )

        # Case 3: Direct identifier format (type/imdb_id or type/imdb_id/s/e)
        elif "/" in media_id:
            stream_url, title, media_info = await self._resolve_and_build_media_info(
                media_id
            )

        else:
            _LOGGER.warning(
                "Unknown media_id format: %s. Expected media-source:// URI or HTTP URL.",
                media_id,
            )
            raise HomeAssistantError(
                f"Unknown media format: {media_id}. "
                "Please select a stream from the media browser."
            )

        # Check if we have a valid stream URL
        if not stream_url:
            _LOGGER.warning(
                "Could not determine stream URL for media_id=%s. "
                "Ensure streams are available for this media.",
                media_id,
            )
            raise HomeAssistantError(
                f"No stream URL found for media: {media_id}. "
                "Please try selecting a specific stream from the media browser."
            )

        # Get handover configuration
        handover_method = options.get(CONF_HANDOVER_METHOD, DEFAULT_HANDOVER_METHOD)
        credentials = options.get(CONF_APPLE_TV_CREDENTIALS)
        device_identifier = options.get(CONF_APPLE_TV_IDENTIFIER)

        # Use title from media_info if not set from stream resolution
        display_title = title or media_info.get("title")

        _LOGGER.info(
            "Starting Apple TV handover: device=%s, method=%s, title=%s, media_id=%s",
            apple_tv_entity_id,
            handover_method,
            display_title,
            media_info.get("imdb_id"),
        )

        # Create handover manager and perform handover
        handover_manager = HandoverManager(
            self.hass,
            credentials=credentials,
            device_identifier=device_identifier,
        )

        try:
            result = await handover_manager.handover(
                device_identifier=apple_tv_entity_id,
                stream_url=stream_url,
                method=handover_method,
                title=display_title,
            )

            _LOGGER.info(
                "Apple TV handover completed: method=%s, success=%s",
                result.get("method"),
                result.get("success"),
            )

            # Update the current media on the Stremio device coordinator
            self.coordinator.set_current_media(media_info, stream_url)

            # Request a state update so the UI reflects the new media
            self.request_state_update()

            # Schedule a refresh after a short delay to allow Stremio's backend to sync
            self.coordinator.schedule_refresh_after_playback()

        except HandoverError as err:
            _LOGGER.error("Apple TV handover failed: %s", err)
            raise HomeAssistantError(f"Apple TV handover failed: {err}") from err

    async def _resolve_media_source_identifier(
        self, identifier: str
    ) -> tuple[str | None, str | None]:
        """Resolve a media source identifier to a stream URL.

        Args:
            identifier: Format: {type}/{imdb_id}[/{season}/{episode}][#{stream_index}]

        Returns:
            Tuple of (stream_url, title) or (None, None) if not found
        """
        stream_url, title, _ = await self._resolve_and_build_media_info(identifier)
        return stream_url, title

    async def _resolve_and_build_media_info(
        self, identifier: str
    ) -> tuple[str | None, str | None, dict[str, Any]]:
        """Resolve a media source identifier to a stream URL and build media info.

        This method parses the identifier, extracts media metadata, resolves the
        stream URL, and enriches the media info with data from the library.

        Args:
            identifier: Format: {type}/{imdb_id}[/{season}/{episode}][#{stream_index}]

        Returns:
            Tuple of (stream_url, title, media_info) or (None, None, {}) if not found
        """
        media_info: dict[str, Any] = {}

        # Extract stream index if present
        stream_index: int = 0
        if "#" in identifier:
            identifier, stream_index_str = identifier.rsplit("#", 1)
            try:
                stream_index = int(stream_index_str)
            except ValueError:
                _LOGGER.warning("Invalid stream index: %s, using 0", stream_index_str)
                stream_index = 0

        # Parse identifier: type/media_id or type/media_id/season/episode
        parts = identifier.split("/")
        if len(parts) < 2:
            _LOGGER.warning("Invalid identifier format: %s", identifier)
            return None, None, {}

        media_type = parts[0]
        imdb_id = parts[1]
        season = int(parts[2]) if len(parts) > 2 else None
        episode = int(parts[3]) if len(parts) > 3 else None

        # Build initial media_info from parsed identifier
        media_info = {
            "type": media_type,
            "imdb_id": imdb_id,
            "media_id": imdb_id,
        }

        if season is not None:
            media_info["season"] = season
        if episode is not None:
            media_info["episode"] = episode

        _LOGGER.debug(
            "Resolving media: type=%s, id=%s, S%sE%s, stream_index=%d",
            media_type,
            imdb_id,
            season,
            episode,
            stream_index,
        )

        # Enrich media_info with library data before fetching streams
        if self.coordinator.data:
            # Check library for matching item
            library = self.coordinator.data.get("library", [])
            for item in library:
                if item.get("imdb_id") == imdb_id:
                    media_info["title"] = item.get("title")
                    media_info["poster"] = item.get("poster")
                    media_info["year"] = item.get("year")
                    media_info["genres"] = item.get("genres", [])
                    _LOGGER.debug(
                        "Enriched media_info with library data: title=%s",
                        media_info.get("title"),
                    )
                    break

            # Check continue watching for matching item with progress
            continue_watching = self.coordinator.data.get("continue_watching", [])
            for item in continue_watching:
                if item.get("imdb_id") == imdb_id:
                    # For series, also match season/episode
                    if media_type == "series":
                        if (
                            item.get("season") == season
                            and item.get("episode") == episode
                        ):
                            media_info["title"] = media_info.get("title") or item.get(
                                "title"
                            )
                            media_info["poster"] = media_info.get("poster") or item.get(
                                "poster"
                            )
                            media_info["year"] = media_info.get("year") or item.get(
                                "year"
                            )
                            media_info["episode_title"] = item.get("episode_title")
                            media_info["progress"] = item.get("progress", 0)
                            media_info["duration"] = item.get("duration", 0)
                            media_info["time_offset"] = item.get("progress", 0)
                            media_info["progress_percent"] = item.get(
                                "progress_percent", 0
                            )
                            _LOGGER.debug(
                                "Enriched series with continue watching data: "
                                "episode_title=%s, progress=%s",
                                media_info.get("episode_title"),
                                media_info.get("progress_percent"),
                            )
                            break
                    else:
                        media_info["title"] = media_info.get("title") or item.get(
                            "title"
                        )
                        media_info["poster"] = media_info.get("poster") or item.get(
                            "poster"
                        )
                        media_info["year"] = media_info.get("year") or item.get("year")
                        media_info["progress"] = item.get("progress", 0)
                        media_info["duration"] = item.get("duration", 0)
                        media_info["time_offset"] = item.get("progress", 0)
                        media_info["progress_percent"] = item.get("progress_percent", 0)
                        _LOGGER.debug(
                            "Enriched movie with continue watching data: progress=%s",
                            media_info.get("progress_percent"),
                        )
                        break

        # Get streams from API
        try:
            streams = await self._client.async_get_streams(
                media_id=imdb_id,
                media_type=media_type,
                season=season,
                episode=episode,
            )

            if not streams:
                _LOGGER.warning("No streams found for %s", identifier)
                return None, None, media_info

            # Get the requested stream by index
            if 0 <= stream_index < len(streams):
                selected_stream = streams[stream_index]
            else:
                _LOGGER.warning(
                    "Stream index %d out of range (available: %d), using first stream",
                    stream_index,
                    len(streams),
                )
                selected_stream = streams[0]

            stream_url = selected_stream.get("url") or selected_stream.get(
                "externalUrl"
            )
            stream_title = selected_stream.get("title") or selected_stream.get("name")

            # Add stream-specific info to media_info
            media_info["stream_name"] = selected_stream.get("name")
            media_info["stream_title"] = stream_title
            media_info["stream_quality"] = selected_stream.get("quality")
            media_info["stream_addon"] = selected_stream.get("addon")

            _LOGGER.debug(
                "Resolved stream: url=%s, title=%s, media_info=%s",
                stream_url[:100] if stream_url else None,
                stream_title,
                {k: v for k, v in media_info.items() if k != "poster"},
            )

            return stream_url, stream_title, media_info

        except StremioConnectionError as err:
            _LOGGER.error("Failed to get streams for %s: %s", identifier, err)
            return None, None, media_info

    async def _build_media_info_from_identifier(
        self, media_id: str, title: str | None, stream_url: str | None
    ) -> dict[str, Any]:
        """Build media info dictionary from a media identifier.

        This extracts media details from the media_id (which could be a
        media-source:// URI or direct identifier) and combines it with
        any available metadata to create a complete media info dict.

        Note: This method is deprecated in favor of _resolve_and_build_media_info
        which builds media info during resolution.

        Args:
            media_id: The media content identifier
            title: Optional title from stream resolution
            stream_url: The stream URL

        Returns:
            Dictionary with media details for coordinator
        """
        # For direct URLs, return minimal info
        if media_id.startswith(("http://", "https://")):
            return {
                "title": title,
                "stream_url": stream_url,
            }

        # Parse the identifier and get enriched media info
        identifier = media_id
        if media_id.startswith("media-source://stremio/"):
            identifier = media_id.replace("media-source://stremio/", "")

        _, _, media_info = await self._resolve_and_build_media_info(identifier)

        # Override title if provided
        if title:
            media_info["title"] = title
        media_info["stream_url"] = stream_url

        return media_info
