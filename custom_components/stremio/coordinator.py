"""DataUpdateCoordinator for Stremio integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_PLAYER_SCAN_INTERVAL,
    DEFAULT_PLAYER_SCAN_INTERVAL,
    DOMAIN,
    EVENT_NEW_CONTENT,
    EVENT_PLAYBACK_STARTED,
    EVENT_PLAYBACK_STOPPED,
)
from .stremio_client import StremioAuthError, StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)


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
        """
        self.client = client
        self.entry = entry
        self._previous_watching: dict[str, Any] | None = None
        self._previous_library_count: int = 0

        # Get scan interval from options or use default
        scan_interval_seconds = entry.options.get(
            CONF_PLAYER_SCAN_INTERVAL, DEFAULT_PLAYER_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Stremio API.

        Returns:
            Dictionary with user, library, and continue watching data

        Raises:
            UpdateFailed: When update fails
        """
        try:
            # Fetch user profile
            user = await self.client.async_get_user()

            # Fetch library items
            library = await self.client.async_get_library()

            # Fetch continue watching
            continue_watching = await self.client.async_get_continue_watching(limit=10)

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

            _LOGGER.debug(
                "Fetched data: %d library items, %d continue watching",
                data["library_count"],
                len(continue_watching),
            )

            # Fire events based on state changes
            self._fire_events(data)

            return data

        except StremioAuthError as err:
            # Authentication error - trigger reauth
            _LOGGER.error("Authentication failed: %s", err)
            self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except StremioConnectionError as err:
            # Connection error - retry next cycle
            _LOGGER.warning("Connection failed, will retry: %s", err)
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
