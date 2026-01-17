"""Stremio API Client wrapper."""
from __future__ import annotations

import logging
from typing import Any

from stremio_api import StremioAPIClient as StremioAPI

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class StremioClient:
    """Stremio API client wrapper with error handling and retries."""

    def __init__(self, hass: HomeAssistant, auth_key: str) -> None:
        """Initialize the Stremio client.

        Args:
            hass: Home Assistant instance
            auth_key: Stremio authentication key
        """
        self.hass = hass
        self._auth_key = auth_key
        self._client: StremioAPI | None = None

    async def async_init(self) -> None:
        """Initialize the API client."""
        self._client = StremioAPI(auth_key=self._auth_key)
        await self._client.__aenter__()

    async def async_close(self) -> None:
        """Close the API client."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def async_get_user(self) -> dict[str, Any]:
        """Get user profile information.

        Returns:
            User profile dictionary

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            user = await self._client.get_user()
            return {
                "email": user.email if hasattr(user, "email") else "unknown",
                "user_id": user.id if hasattr(user, "id") else None,
            }
        except Exception as err:
            _LOGGER.error("Failed to get user profile: %s", err)
            if "401" in str(err) or "authentication" in str(err).lower():
                raise StremioAuthError("Authentication failed") from err
            raise StremioConnectionError(f"Failed to get user: {err}") from err

    async def async_get_library(self) -> list[dict[str, Any]]:
        """Fetch user's library items.

        Returns:
            List of library item dictionaries

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            library = await self._client.get_library()
            return self._process_library_items(library)
        except Exception as err:
            _LOGGER.error("Failed to get library: %s", err)
            if "401" in str(err) or "authentication" in str(err).lower():
                raise StremioAuthError("Authentication failed") from err
            raise StremioConnectionError(f"Failed to get library: {err}") from err

    async def async_get_continue_watching(
        self, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get continue watching list.

        Args:
            limit: Maximum items to return

        Returns:
            List of continue watching items

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            watching = await self._client.get_continue_watching(limit=limit)
            return self._process_continue_watching(watching)
        except Exception as err:
            _LOGGER.error("Failed to get continue watching: %s", err)
            if "401" in str(err) or "authentication" in str(err).lower():
                raise StremioAuthError("Authentication failed") from err
            raise StremioConnectionError(
                f"Failed to get continue watching: {err}"
            ) from err

    async def async_get_streams(self, content_id: str) -> list[dict[str, Any]]:
        """Get available streams for content.

        Args:
            content_id: Content identifier (e.g., IMDb ID)

        Returns:
            List of stream dictionaries

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            # Note: stremio-api may not have this method yet
            # This is a placeholder for future implementation
            _LOGGER.warning("Stream fetching not yet implemented in stremio-api")
            return []
        except Exception as err:
            _LOGGER.error("Failed to get streams: %s", err)
            raise StremioConnectionError(f"Failed to get streams: {err}") from err

    def _process_library_items(self, library: Any) -> list[dict[str, Any]]:
        """Process library items into consistent format.

        Args:
            library: Raw library data from API

        Returns:
            Processed library items
        """
        if not library:
            return []

        items = []
        try:
            for item in library:
                processed_item = {
                    "id": getattr(item, "id", None),
                    "name": getattr(item, "name", "Unknown"),
                    "type": getattr(item, "type", "unknown"),
                    "poster": getattr(item, "poster", None),
                    "added_at": getattr(item, "added_at", None),
                }
                items.append(processed_item)
        except (AttributeError, TypeError) as err:
            _LOGGER.warning("Error processing library items: %s", err)

        return items

    def _process_continue_watching(self, watching: Any) -> list[dict[str, Any]]:
        """Process continue watching items into consistent format.

        Args:
            watching: Raw continue watching data from API

        Returns:
            Processed continue watching items
        """
        if not watching:
            return []

        items = []
        try:
            for item in watching:
                processed_item = {
                    "id": getattr(item, "id", None),
                    "name": getattr(item, "name", "Unknown"),
                    "type": getattr(item, "type", "unknown"),
                    "poster": getattr(item, "poster", None),
                    "progress": getattr(item, "progress", 0),
                    "duration": getattr(item, "duration", 0),
                    "watched_at": getattr(item, "watched_at", None),
                }
                items.append(processed_item)
        except (AttributeError, TypeError) as err:
            _LOGGER.warning("Error processing continue watching items: %s", err)

        return items


class StremioAuthError(HomeAssistantError):
    """Error to indicate authentication failure."""


class StremioConnectionError(HomeAssistantError):
    """Error to indicate connection failure."""
