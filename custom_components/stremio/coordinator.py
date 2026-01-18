"""DataUpdateCoordinator for Stremio integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_OFF,
    STATE_STANDBY,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_PLAYER_SCAN_INTERVAL,
    CONF_POLLING_GATE_ENTITIES,
    DEFAULT_PLAYER_SCAN_INTERVAL,
    DEFAULT_POLLING_GATE_ENTITIES,
    DOMAIN,
    EVENT_NEW_CONTENT,
    EVENT_PLAYBACK_STARTED,
    EVENT_PLAYBACK_STOPPED,
    POLLING_GATE_IDLE_INTERVAL,
)
from .stremio_client import StremioAuthError, StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 10.0  # seconds


class StremioDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Stremio data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: StremioClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            client: Stremio API client
            entry: Config entry

        Note:
            Following Home Assistant best practices (2024.8+), complex initialization
            logic that requires hass or async operations is deferred to _async_setup().
        """
        self.client = client
        self.entry = entry
        self._previous_watching: dict[str, Any] | None = None
        self._previous_library_count: int = 0
        self._consecutive_failures: int = 0
        self._state_change_unsub: list[Any] = []
        self._is_polling_gated: bool = False
        self._current_stream_url: str | None = None  # Track current stream URL

        # Get scan interval from options or use default
        self._configured_scan_interval = entry.options.get(
            CONF_PLAYER_SCAN_INTERVAL, DEFAULT_PLAYER_SCAN_INTERVAL
        )

        # Get polling gate entities from options
        self._polling_gate_entities: list[str] = entry.options.get(
            CONF_POLLING_GATE_ENTITIES, DEFAULT_POLLING_GATE_ENTITIES
        )

        # Start with the configured interval; _async_setup will adjust if needed
        # based on gate entity states (requires hass to be available)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._configured_scan_interval),
            config_entry=entry,
        )

    async def _async_setup(self) -> None:
        """Set up the coordinator.

        This method is called during async_config_entry_first_refresh() and provides
        proper error handling. Use this for initialization that requires hass or
        async operations.
        """
        # Calculate initial interval based on gate entity states
        # (now self.hass is available)
        initial_interval = self._calculate_update_interval()
        if initial_interval != self.update_interval:
            self.update_interval = initial_interval
            _LOGGER.debug(
                "Adjusted initial update interval to %s based on gate entity states",
                initial_interval,
            )

        # Set up state change listeners for gate entities
        self._setup_gate_entity_listeners()

    def _setup_gate_entity_listeners(self) -> None:
        """Set up state change listeners for polling gate entities."""
        # Clean up any existing listeners
        for unsub in self._state_change_unsub:
            unsub()
        self._state_change_unsub.clear()

        if not self._polling_gate_entities:
            _LOGGER.debug("No polling gate entities configured")
            return

        _LOGGER.debug(
            "Setting up state change listeners for polling gate entities: %s",
            self._polling_gate_entities,
        )

        # Listen for state changes on all gate entities
        unsub = async_track_state_change_event(
            self.hass,
            self._polling_gate_entities,
            self._handle_gate_entity_state_change,
        )
        self._state_change_unsub.append(unsub)

    @callback
    def _handle_gate_entity_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Handle state change of a polling gate entity."""
        entity_id = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        old_state_str = old_state.state if old_state else "unknown"
        new_state_str = new_state.state if new_state else "unknown"

        _LOGGER.debug(
            "Polling gate entity %s changed from %s to %s",
            entity_id,
            old_state_str,
            new_state_str,
        )

        # Recalculate and update the polling interval
        self._update_polling_interval()

    def _is_entity_active(self, entity_id: str) -> bool:
        """Check if an entity is considered 'active' (on/playing).

        Args:
            entity_id: The entity ID to check

        Returns:
            True if the entity is active, False otherwise
        """
        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        # Inactive states
        inactive_states = {
            STATE_OFF,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
            STATE_STANDBY,
            "idle",
            "paused",
        }

        return state.state.lower() not in inactive_states

    def _any_gate_entity_active(self) -> bool:
        """Check if any polling gate entity is active.

        Returns:
            True if at least one gate entity is active, or if no gate entities
            are configured (always poll in that case)
        """
        if not self._polling_gate_entities:
            # No gate entities configured - always poll at normal interval
            return True

        for entity_id in self._polling_gate_entities:
            if self._is_entity_active(entity_id):
                _LOGGER.debug("Gate entity %s is active", entity_id)
                return True

        _LOGGER.debug("All gate entities are inactive")
        return False

    def _calculate_update_interval(self) -> timedelta:
        """Calculate the appropriate update interval based on gate entity states.

        Returns:
            The update interval to use
        """
        if self._any_gate_entity_active():
            self._is_polling_gated = False
            return timedelta(seconds=self._configured_scan_interval)
        else:
            self._is_polling_gated = True
            return timedelta(seconds=POLLING_GATE_IDLE_INTERVAL)

    @callback
    def _update_polling_interval(self) -> None:
        """Update the polling interval based on current gate entity states."""
        new_interval = self._calculate_update_interval()

        if new_interval != self.update_interval:
            was_gated = self._is_polling_gated
            old_interval = self.update_interval

            self.update_interval = new_interval

            if self._is_polling_gated:
                _LOGGER.info(
                    "All polling gate entities are inactive. "
                    "Reducing poll frequency from %s to %s (24h idle mode)",
                    old_interval,
                    new_interval,
                )
            else:
                _LOGGER.info(
                    "Polling gate entity became active. "
                    "Restoring poll frequency from %s to %s",
                    old_interval,
                    new_interval,
                )

                # If we were gated and now active, trigger an immediate refresh
                if was_gated:
                    _LOGGER.debug("Triggering immediate refresh after gate activation")
                    self.hass.async_create_task(self.async_request_refresh())

    def update_options(self, entry: ConfigEntry) -> None:
        """Update coordinator with new options.

        Args:
            entry: Updated config entry
        """
        self._configured_scan_interval = entry.options.get(
            CONF_PLAYER_SCAN_INTERVAL, DEFAULT_PLAYER_SCAN_INTERVAL
        )

        new_gate_entities = entry.options.get(
            CONF_POLLING_GATE_ENTITIES, DEFAULT_POLLING_GATE_ENTITIES
        )

        # Check if gate entities changed
        if new_gate_entities != self._polling_gate_entities:
            self._polling_gate_entities = new_gate_entities
            self._setup_gate_entity_listeners()

        # Recalculate interval with new settings
        self._update_polling_interval()

    def set_current_stream_url(self, stream_url: str | None) -> None:
        """Set the current stream URL being played.

        This is called when a handover is performed to track the stream URL.

        Args:
            stream_url: The stream URL being played, or None to clear
        """
        self._current_stream_url = stream_url
        _LOGGER.debug(
            "Current stream URL set to: %s", stream_url[:100] if stream_url else None
        )

        # Update the data if we have current_watching
        if self.data and self.data.get("current_watching"):
            self.data["current_watching"]["stream_url"] = stream_url
            self.async_set_updated_data(self.data)

    async def async_shutdown(self) -> None:
        """Clean up resources on shutdown."""
        # Unsubscribe from state change events
        for unsub in self._state_change_unsub:
            unsub()
        self._state_change_unsub.clear()

        await super().async_shutdown()

    async def _async_fetch_with_retry(self, fetch_func, description: str) -> Any:
        """Execute a fetch function with exponential backoff retry.

        Args:
            fetch_func: Async function to execute
            description: Description for logging

        Returns:
            Result from fetch_func

        Raises:
            StremioConnectionError: After all retries exhausted
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                return await fetch_func()
            except StremioConnectionError as err:
                last_error = err
                if attempt < MAX_RETRIES - 1:
                    delay = min(BASE_RETRY_DELAY * (2**attempt), MAX_RETRY_DELAY)
                    _LOGGER.debug(
                        "Retry %d/%d for %s after %.1fs: %s",
                        attempt + 1,
                        MAX_RETRIES,
                        description,
                        delay,
                        err,
                    )
                    await asyncio.sleep(delay)

        raise last_error  # type: ignore[misc]

    async def _enrich_with_episode_titles(self, data: dict[str, Any]) -> None:
        """Enrich current_watching and last_watched with episode titles for series.

        Fetches metadata from Cinemeta to get episode titles for TV shows.
        This is only done for the current and last watched items, not the full list.

        Args:
            data: The coordinator data dictionary to enrich
        """
        items_to_enrich = []

        # Collect series items that need episode title enrichment
        if data.get("current_watching"):
            current = data["current_watching"]
            if (
                current.get("type") == "series"
                and current.get("season") is not None
                and current.get("episode") is not None
                and not current.get("episode_title")
            ):
                items_to_enrich.append(("current_watching", current))

        if data.get("last_watched"):
            last = data["last_watched"]
            if (
                last.get("type") == "series"
                and last.get("season") is not None
                and last.get("episode") is not None
                and not last.get("episode_title")
            ):
                # Don't fetch again if it's the same as current_watching
                current = data.get("current_watching", {})
                if (
                    last.get("imdb_id") != current.get("imdb_id")
                    or last.get("season") != current.get("season")
                    or last.get("episode") != current.get("episode")
                ):
                    items_to_enrich.append(("last_watched", last))
                else:
                    # Copy episode title from current if same episode
                    if current.get("episode_title"):
                        last["episode_title"] = current["episode_title"]

        # Fetch metadata for unique series
        fetched_metadata: dict[str, dict[str, Any] | None] = {}

        for key, item in items_to_enrich:
            imdb_id = item.get("imdb_id")
            if not imdb_id:
                continue

            # Fetch metadata if not already fetched
            if imdb_id not in fetched_metadata:
                try:
                    metadata = await self.client.async_get_series_metadata(imdb_id)
                    fetched_metadata[imdb_id] = metadata
                except Exception as err:
                    _LOGGER.debug("Failed to fetch metadata for %s: %s", imdb_id, err)
                    fetched_metadata[imdb_id] = None

            metadata = fetched_metadata.get(imdb_id)
            if not metadata:
                continue

            # Find the episode title
            season_num = item.get("season")
            episode_num = item.get("episode")

            for season_data in metadata.get("seasons", []):
                if season_data.get("number") == season_num:
                    for ep_data in season_data.get("episodes", []):
                        if ep_data.get("number") == episode_num:
                            episode_title = ep_data.get("title")
                            if episode_title:
                                data[key]["episode_title"] = episode_title
                                _LOGGER.debug(
                                    "Enriched %s with episode title: %s",
                                    key,
                                    episode_title,
                                )
                            break
                    break

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Stremio API.

        Returns:
            Dictionary with user, library, and continue watching data

        Raises:
            UpdateFailed: When update fails
        """
        try:
            # Fetch user profile with retry
            user = await self._async_fetch_with_retry(
                self.client.async_get_user, "user profile"
            )

            # Fetch library items with retry
            library = await self._async_fetch_with_retry(
                self.client.async_get_library, "library"
            )

            # Fetch continue watching with retry
            continue_watching = await self._async_fetch_with_retry(
                lambda: self.client.async_get_continue_watching(limit=10),
                "continue watching",
            )

            # Prepare data structure
            data = {
                "user": user,
                "library": library,
                "library_count": len(library),
                "continue_watching": continue_watching,
                "current_watching": None,
                "last_watched": None,
            }

            # Determine current and last watched
            if continue_watching:
                # Sort by watched_at if available (numeric timestamp, 0 as default)
                sorted_watching = sorted(
                    continue_watching,
                    key=lambda x: x.get("watched_at") or 0,
                    reverse=True,
                )

                # Current watching is the most recently watched with progress < 100%
                for item in sorted_watching:
                    progress = item.get("progress", 0)
                    duration = item.get("duration", 1)
                    progress_percent = (
                        (progress / duration * 100) if duration > 0 else 0
                    )

                    if 0 < progress_percent < 95:  # Not finished
                        data["current_watching"] = {
                            **item,
                            "progress_percent": round(progress_percent, 1),
                            "time_offset": progress,
                            "stream_url": self._current_stream_url,
                        }
                        break

                # Last watched is the most recent item
                if sorted_watching:
                    last_item = sorted_watching[0]
                    data["last_watched"] = {
                        **last_item,
                        "progress_percent": (
                            round(
                                (
                                    last_item.get("progress", 0)
                                    / last_item.get("duration", 1)
                                )
                                * 100,
                                1,
                            )
                            if last_item.get("duration", 0) > 0
                            else 0
                        ),
                    }

            # Fetch episode titles for series items
            await self._enrich_with_episode_titles(data)

            _LOGGER.debug(
                "Fetched data: %d library items, %d continue watching",
                data["library_count"],
                len(continue_watching),
            )

            # Fire events based on state changes
            self._fire_events(data)

            # Reset failure counter on success
            if self._consecutive_failures > 0:
                _LOGGER.info(
                    "Connection restored after %d consecutive failures",
                    self._consecutive_failures,
                )
            self._consecutive_failures = 0

            return data

        except StremioAuthError as err:
            # Authentication error - trigger reauth
            self._consecutive_failures += 1
            _LOGGER.error("Authentication failed: %s", err)
            self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except StremioConnectionError as err:
            # Connection error - retry next cycle (after all retries exhausted)
            self._consecutive_failures += 1
            _LOGGER.warning(
                "Connection failed (attempt %d), will retry next cycle: %s",
                self._consecutive_failures,
                err,
            )
            raise UpdateFailed(f"Connection failed: {err}") from err

        except Exception as err:
            # Unexpected error
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _fire_events(self, data: dict[str, Any]) -> None:
        """Fire events based on state changes.

        Args:
            data: Current data from API
        """
        current_watching = data.get("current_watching")
        library_count = data.get("library_count", 0)

        # Check for playback started
        if current_watching and not self._previous_watching:
            _LOGGER.debug("Firing playback started event")
            self.hass.bus.async_fire(
                EVENT_PLAYBACK_STARTED,
                {
                    "media_id": current_watching.get("imdb_id"),
                    "title": current_watching.get("title"),
                    "type": current_watching.get("type"),
                    "season": current_watching.get("season"),
                    "episode": current_watching.get("episode"),
                    "progress_percent": current_watching.get("progress_percent"),
                },
            )
        # Check for playback stopped
        elif not current_watching and self._previous_watching:
            _LOGGER.debug("Firing playback stopped event")
            self.hass.bus.async_fire(
                EVENT_PLAYBACK_STOPPED,
                {
                    "media_id": self._previous_watching.get("imdb_id"),
                    "title": self._previous_watching.get("title"),
                    "type": self._previous_watching.get("type"),
                },
            )
        # Check for content change (different media)
        elif (
            current_watching
            and self._previous_watching
            and current_watching.get("imdb_id")
            != self._previous_watching.get("imdb_id")
        ):
            _LOGGER.debug("Firing playback stopped and started events (content change)")
            self.hass.bus.async_fire(
                EVENT_PLAYBACK_STOPPED,
                {
                    "media_id": self._previous_watching.get("imdb_id"),
                    "title": self._previous_watching.get("title"),
                    "type": self._previous_watching.get("type"),
                },
            )
            self.hass.bus.async_fire(
                EVENT_PLAYBACK_STARTED,
                {
                    "media_id": current_watching.get("imdb_id"),
                    "title": current_watching.get("title"),
                    "type": current_watching.get("type"),
                    "season": current_watching.get("season"),
                    "episode": current_watching.get("episode"),
                    "progress_percent": current_watching.get("progress_percent"),
                },
            )

        # Check for library changes
        if (
            self._previous_library_count > 0
            and library_count != self._previous_library_count
        ):
            change = library_count - self._previous_library_count
            _LOGGER.debug("Firing library changed event: %+d items", change)
            self.hass.bus.async_fire(
                EVENT_NEW_CONTENT,
                {
                    "action": "added" if change > 0 else "removed",
                    "count_change": abs(change),
                    "new_count": library_count,
                },
            )

        # Update previous state
        self._previous_watching = current_watching
        self._previous_library_count = library_count
