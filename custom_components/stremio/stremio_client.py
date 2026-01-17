"""Stremio API Client wrapper."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientTimeout

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

# Stremio API endpoints
STREMIO_API_BASE = "https://api.strem.io"
STREMIO_AUTH_URL = f"{STREMIO_API_BASE}/api/login"
STREMIO_USER_URL = f"{STREMIO_API_BASE}/api/datastoreMeta"
STREMIO_ADDON_COLLECTION_URL = f"{STREMIO_API_BASE}/api/addonCollectionGet"



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
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def async_authenticate(self) -> str:
        """Authenticate with Stremio and get auth key.

        Returns:
            Authentication key

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        try:
            session = await self._get_session()
            
            # Login to Stremio
            payload = {
                "email": self._email,
                "password": self._password,
                "facebook": False,
            }
            
            async with session.post(STREMIO_AUTH_URL, json=payload) as response:
                if response.status == 401:
                    raise StremioAuthError("Invalid email or password")
                if response.status != 200:
                    text = await response.text()
                    raise StremioConnectionError(
                        f"Authentication failed with status {response.status}: {text}"
                    )
                
                data = await response.json()
                auth_key = data.get("authKey") or data.get("result", {}).get("authKey")
                
                if not auth_key:
                    raise StremioAuthError("No auth key received in response")
                
                self._auth_key = auth_key
                return auth_key

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise StremioConnectionError(f"Authentication error: {err}") from err

    async def async_close(self) -> None:
        """Close the API client."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def async_get_user(self) -> dict[str, Any]:
        """Get user profile information.

        Returns:
            User profile dictionary

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            raise StremioConnectionError("Client not authenticated")

        try:
            session = await self._get_session()
            url = f"{STREMIO_USER_URL}?authKey={self._auth_key}&type=user"
            
            async with session.get(url) as response:
                if response.status == 401:
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    raise StremioConnectionError(
                        f"Failed to get user with status {response.status}: {text}"
                    )
                
                data = await response.json()
                user_data = data.get("result", {})
                
                return {
                    "email": self._email,
                    "user_id": user_data.get("_id"),
                    "auth_key": self._auth_key,
                }

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting user: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.error("Failed to get user profile: %s", err)
            raise StremioConnectionError(f"Failed to get user: {err}") from err


    async def async_get_library(self) -> list[dict[str, Any]]:
        """Fetch user's library items.

        Returns:
            List of library item dictionaries

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            raise StremioConnectionError("Client not authenticated")

        try:
            session = await self._get_session()
            url = f"{STREMIO_USER_URL}?authKey={self._auth_key}&type=libraryItem"
            
            async with session.get(url) as response:
                if response.status == 401:
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    raise StremioConnectionError(
                        f"Failed to get library with status {response.status}: {text}"
                    )
                
                data = await response.json()
                library_items = data.get("result", [])
                
                return self._process_library_items(library_items)

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting library: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.error("Failed to get library: %s", err)
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
        if not self._auth_key:
            raise StremioConnectionError("Client not authenticated")

        try:
            session = await self._get_session()
            # Get continue watching from library items with state
            url = f"{STREMIO_USER_URL}?authKey={self._auth_key}&type=libraryItem"
            
            async with session.get(url) as response:
                if response.status == 401:
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    raise StremioConnectionError(
                        f"Failed to get continue watching with status {response.status}: {text}"
                    )
                
                data = await response.json()
                library_items = data.get("result", [])
                
                # Filter items with watch progress
                watching = [
                    item for item in library_items
                    if item.get("state", {}).get("timeWatched", 0) > 0
                ]
                
                # Sort by most recently watched and limit
                watching.sort(
                    key=lambda x: x.get("state", {}).get("lastWatched", 0),
                    reverse=True
                )
                watching = watching[:limit]
                
                return self._process_continue_watching(watching)

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting continue watching: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.error("Failed to get continue watching: %s", err)
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
        if not self._auth_key:
            raise StremioConnectionError("Client not authenticated")

        try:
            # Build video ID for series
            if media_type == "series" and season is not None and episode is not None:
                video_id = f"{media_id}:{season}:{episode}"
            else:
                video_id = media_id

            # Note: Stream fetching requires addons and is complex
            # This would need to query the user's installed addons
            # For now, return empty list
            _LOGGER.info("Stream fetching for %s not yet implemented", video_id)
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
        if not self._auth_key:
            raise StremioConnectionError("Client not authenticated")

        try:
            _LOGGER.info("Add to library for %s not yet fully implemented", media_id)
            # This would require posting to the datastore
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
        if not self._auth_key:
            raise StremioConnectionError("Client not authenticated")

        try:
            _LOGGER.info("Remove from library for %s not yet fully implemented", media_id)
            # This would require posting to the datastore
            return False

        except Exception as err:
            _LOGGER.error("Failed to remove from library: %s", err)
            raise StremioConnectionError(
                f"Failed to remove from library: {err}"
            ) from err


    def _process_library_items(self, library: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                # Extract item data
                _id = item.get("_id", "")
                name = item.get("name", "Unknown")
                item_type = item.get("type", "unknown")
                
                # Parse ID (format: type:id, e.g., "movie:tt1234567")
                imdb_id = _id.split(":", 1)[1] if ":" in _id else _id
                
                processed_item = {
                    "id": _id,
                    "imdb_id": imdb_id,
                    "title": name,
                    "type": item_type,
                    "poster": item.get("poster"),
                    "year": item.get("year"),
                    "genres": item.get("genres", []),
                    "cast": item.get("cast", []),
                    "added_at": item.get("mtime"),
                }
                items.append(processed_item)
        except (AttributeError, TypeError, KeyError) as err:
            _LOGGER.warning("Error processing library items: %s", err)

        return items

    def _process_continue_watching(self, watching: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                # Extract item data
                _id = item.get("_id", "")
                name = item.get("name", "Unknown")
                item_type = item.get("type", "unknown")
                state = item.get("state", {})
                
                # Parse ID
                imdb_id = _id.split(":", 1)[1] if ":" in _id else _id
                
                # Extract video info from state
                video_id = state.get("video_id", "")
                season = None
                episode = None
                if ":" in video_id:
                    parts = video_id.split(":")
                    if len(parts) >= 3:
                        season = int(parts[1]) if parts[1].isdigit() else None
                        episode = int(parts[2]) if parts[2].isdigit() else None
                
                processed_item = {
                    "id": _id,
                    "imdb_id": imdb_id,
                    "title": name,
                    "type": item_type,
                    "poster": item.get("poster"),
                    "progress": state.get("timeWatched", 0),
                    "duration": state.get("duration", 0),
                    "season": season,
                    "episode": episode,
                    "year": item.get("year"),
                    "watched_at": state.get("lastWatched"),
                }
                items.append(processed_item)
        except (AttributeError, TypeError, KeyError) as err:
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
