"""Stremio API Client wrapper."""

from __future__ import annotations

import logging
from typing import Any

from stremio_api import StremioAPIClient as StremioAPI

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class StremioClient:
    """Stremio API client wrapper with error handling and retries."""

    def __init__(self, email: str, password: str) -> None:
        """Initialize the Stremio client.

        Args:
            email: Stremio account email
            password: Stremio account password
        """
        self._email = email
        self._password = password
        self._auth_key: str | None = None
        self._client: StremioAPI | None = None

    async def async_authenticate(self) -> str:
        """Authenticate with Stremio and get auth key.

        Returns:
            Authentication key

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        try:
            async with StremioAPI(auth_key=None) as client:
                auth_key = await client.login(self._email, self._password)
                if not auth_key:
                    raise StremioAuthError("No auth key received")
                self._auth_key = auth_key

                # Initialize persistent client
                self._client = StremioAPI(auth_key=self._auth_key)
                await self._client.__aenter__()

                return auth_key
        except StremioAuthError:
            raise
        except Exception as err:
            _LOGGER.error("Authentication failed: %s", err)
            if "401" in str(err) or "authentication" in str(err).lower():
                raise StremioAuthError(f"Authentication failed: {err}") from err
            raise StremioConnectionError(f"Connection failed: {err}") from err

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

    async def async_get_streams(
        self,
        media_id: str,
        media_type: str = "movie",
        season: int | None = None,
        episode: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get available streams for content.

        Args:
            media_id: Content identifier (e.g., IMDb ID)
            media_type: Type of media (movie or series)
            season: Season number for series
            episode: Episode number for series

        Returns:
            List of stream dictionaries

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            # Build video ID for series
            if media_type == "series" and season is not None and episode is not None:
                video_id = f"{media_id}:{season}:{episode}"
            else:
                video_id = media_id

            # Attempt to get streams (API method may vary)
            streams = await self._client.get_streams(media_type, video_id)
            return self._process_streams(streams)
        except AttributeError:
            _LOGGER.warning("Stream fetching may not be available in stremio-api")
            return []
        except Exception as err:
            _LOGGER.error("Failed to get streams: %s", err)
            raise StremioConnectionError(f"Failed to get streams: {err}") from err

    async def async_add_to_library(
        self, media_id: str, media_type: str = "movie"
    ) -> bool:
        """Add item to library.

        Args:
            media_id: Content identifier (e.g., IMDb ID)
            media_type: Type of media (movie or series)

        Returns:
            True if successful

        Raises:
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            await self._client.add_to_library(media_type, media_id)
            return True
        except AttributeError:
            _LOGGER.warning("add_to_library may not be available in stremio-api")
            return False
        except Exception as err:
            _LOGGER.error("Failed to add to library: %s", err)
            raise StremioConnectionError(f"Failed to add to library: {err}") from err

    async def async_remove_from_library(self, media_id: str) -> bool:
        """Remove item from library.

        Args:
            media_id: Content identifier (e.g., IMDb ID)

        Returns:
            True if successful

        Raises:
            StremioConnectionError: Connection failed
        """
        if not self._client:
            raise StremioConnectionError("Client not initialized")

        try:
            await self._client.remove_from_library(media_id)
            return True
        except AttributeError:
            _LOGGER.warning("remove_from_library may not be available in stremio-api")
            return False
        except Exception as err:
            _LOGGER.error("Failed to remove from library: %s", err)
            raise StremioConnectionError(
                f"Failed to remove from library: {err}"
            ) from err

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
                    "imdb_id": getattr(item, "imdb_id", None)
                    or getattr(item, "id", None),
                    "title": getattr(item, "name", None)
                    or getattr(item, "title", "Unknown"),
                    "type": getattr(item, "type", "unknown"),
                    "poster": getattr(item, "poster", None),
                    "year": getattr(item, "year", None),
                    "genres": getattr(item, "genres", []),
                    "cast": getattr(item, "cast", []),
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
                    "imdb_id": getattr(item, "imdb_id", None)
                    or getattr(item, "id", None),
                    "title": getattr(item, "name", None)
                    or getattr(item, "title", "Unknown"),
                    "type": getattr(item, "type", "unknown"),
                    "poster": getattr(item, "poster", None),
                    "progress": getattr(item, "progress", 0),
                    "duration": getattr(item, "duration", 0),
                    "season": getattr(item, "season", None),
                    "episode": getattr(item, "episode", None),
                    "year": getattr(item, "year", None),
                    "watched_at": getattr(item, "watched_at", None),
                }
                items.append(processed_item)
        except (AttributeError, TypeError) as err:
            _LOGGER.warning("Error processing continue watching items: %s", err)

        return items

    def _process_streams(self, streams: Any) -> list[dict[str, Any]]:
        """Process streams into consistent format.

        Args:
            streams: Raw stream data from API

        Returns:
            Processed stream items
        """
        if not streams:
            return []

        items = []
        try:
            for stream in streams:
                processed = {
                    "url": getattr(stream, "url", None),
                    "name": getattr(stream, "name", None),
                    "title": getattr(stream, "title", None),
                    "quality": getattr(stream, "quality", None),
                    "source": getattr(stream, "source", None),
                }
                if processed["url"]:
                    items.append(processed)
        except (AttributeError, TypeError) as err:
            _LOGGER.warning("Error processing streams: %s", err)

        return items


class StremioAuthError(HomeAssistantError):
    """Error to indicate authentication failure."""


class StremioConnectionError(HomeAssistantError):
    """Error to indicate connection failure."""
