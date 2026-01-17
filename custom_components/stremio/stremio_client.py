"""Stremio API Client wrapper.

This module provides a Python client for interacting with the Stremio API.
It handles authentication, library management, and data synchronization.

API Documentation:
- Stremio uses a REST-like API at https://api.strem.io
- Authentication returns an authKey used for subsequent requests
- Library data is stored via the datastore API (datastoreMeta, datastoreGet, datastorePut)
- Addon collections are managed via addonCollectionGet/addonCollectionSet

See: https://github.com/Stremio/stremio-api-client
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientTimeout
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

# Stremio API endpoints - based on official stremio-api-client
STREMIO_API_BASE = "https://api.strem.io"
STREMIO_AUTH_URL = f"{STREMIO_API_BASE}/api/login"
STREMIO_LOGOUT_URL = f"{STREMIO_API_BASE}/api/logout"
STREMIO_DATASTORE_META_URL = f"{STREMIO_API_BASE}/api/datastoreMeta"
STREMIO_DATASTORE_GET_URL = f"{STREMIO_API_BASE}/api/datastoreGet"
STREMIO_DATASTORE_PUT_URL = f"{STREMIO_API_BASE}/api/datastorePut"
STREMIO_ADDON_COLLECTION_URL = f"{STREMIO_API_BASE}/api/addonCollectionGet"

# Datastore collection types
COLLECTION_LIBRARY_ITEM = "libraryItem"
COLLECTION_USER = "user"


class StremioClient:
    """Stremio API client wrapper with error handling and retries.

    This client communicates with the Stremio API to:
    - Authenticate users and manage sessions
    - Fetch and update library items
    - Manage continue watching state
    - Retrieve stream information from addons
    """

    def __init__(self, email: str, password: str) -> None:
        """Initialize the Stremio client.

        Args:
            email: Stremio account email
            password: Stremio account password
        """
        self._email = email
        self._password = password
        self._auth_key: str | None = None
        self._user_id: str | None = None
        self._session: aiohttp.ClientSession | None = None
        self._last_auth_time: float = 0
        _LOGGER.debug("StremioClient initialized for user: %s", email)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
            _LOGGER.debug("Created new aiohttp session")
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication."""
        return self._auth_key is not None

    async def async_authenticate(self) -> str:
        """Authenticate with Stremio and get auth key.

        Uses the /api/login endpoint with email and password.
        Returns an authKey that must be used for all subsequent API calls.

        Returns:
            Authentication key

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        _LOGGER.info("Authenticating with Stremio API for user: %s", self._email)

        try:
            session = await self._get_session()

            # Login to Stremio - matching stremio-api-client login params
            payload = {
                "email": self._email,
                "password": self._password,
                "facebook": False,
            }

            _LOGGER.debug("Sending authentication request to %s", STREMIO_AUTH_URL)

            async with session.post(STREMIO_AUTH_URL, json=payload) as response:
                _LOGGER.debug("Auth response status: %d", response.status)

                if response.status == 401:
                    _LOGGER.warning("Authentication failed: Invalid credentials")
                    raise StremioAuthError("Invalid email or password")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Authentication failed with status %d: %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Authentication failed with status {response.status}: {text}"
                    )

                data = await response.json()

                # Handle different response formats
                auth_key = data.get("authKey") or data.get("result", {}).get("authKey")
                user_data = data.get("user") or data.get("result", {})

                if not auth_key:
                    _LOGGER.error("No auth key in response: %s", data.keys())
                    raise StremioAuthError("No auth key received in response")

                self._auth_key = auth_key
                self._user_id = user_data.get("_id")
                self._last_auth_time = time.time()

                _LOGGER.info(
                    "Successfully authenticated with Stremio (user_id: %s)",
                    self._user_id,
                )
                return auth_key

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during authentication")
            raise StremioConnectionError(f"Authentication error: {err}") from err

    async def async_close(self) -> None:
        """Close the API client and cleanup resources."""
        _LOGGER.debug("Closing StremioClient session")
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        self._auth_key = None
        _LOGGER.debug("StremioClient session closed")

    async def async_get_user(self) -> dict[str, Any]:
        """Get user profile information.

        Uses the datastoreMeta endpoint with type=user to get user profile data.

        Returns:
            User profile dictionary

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot get user: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        _LOGGER.debug("Fetching user profile from Stremio API")

        try:
            session = await self._get_session()
            url = f"{STREMIO_DATASTORE_META_URL}?authKey={self._auth_key}&type={COLLECTION_USER}"

            async with session.get(url) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while fetching user")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error("Failed to get user (status %d): %s", response.status, text[:200])
                    raise StremioConnectionError(
                        f"Failed to get user with status {response.status}: {text}"
                    )

                data = await response.json()
                user_data = data.get("result", {})

                _LOGGER.debug("Successfully fetched user profile")
                return {
                    "email": self._email,
                    "user_id": user_data.get("_id") or self._user_id,
                    "auth_key": self._auth_key,
                }

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting user: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to get user profile")
            raise StremioConnectionError(f"Failed to get user: {err}") from err

    async def async_get_library(self) -> list[dict[str, Any]]:
        """Fetch user's library items.

        Uses the datastoreMeta endpoint with type=libraryItem to get all library items.
        This returns items with metadata including watch state, timestamps, etc.

        Returns:
            List of library item dictionaries

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot get library: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        _LOGGER.debug("Fetching library from Stremio API")

        try:
            session = await self._get_session()
            url = f"{STREMIO_DATASTORE_META_URL}?authKey={self._auth_key}&type={COLLECTION_LIBRARY_ITEM}"

            async with session.get(url) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while fetching library")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error("Failed to get library (status %d): %s", response.status, text[:200])
                    raise StremioConnectionError(
                        f"Failed to get library with status {response.status}: {text}"
                    )

                data = await response.json()
                library_items = data.get("result", [])

                _LOGGER.info("Fetched %d library items from Stremio", len(library_items))
                return self._process_library_items(library_items)

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting library: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to get library")
            raise StremioConnectionError(f"Failed to get library: {err}") from err

    async def async_get_continue_watching(
        self, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get continue watching list.

        Fetches library items and filters to those with active watch progress.
        Items are sorted by most recently watched.

        Args:
            limit: Maximum items to return

        Returns:
            List of continue watching items

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot get continue watching: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        _LOGGER.debug("Fetching continue watching list (limit: %d)", limit)

        try:
            session = await self._get_session()
            # Get library items with state data
            url = f"{STREMIO_DATASTORE_META_URL}?authKey={self._auth_key}&type={COLLECTION_LIBRARY_ITEM}"

            async with session.get(url) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while fetching continue watching")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to get continue watching (status %d): %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Failed to get continue watching with status {response.status}: {text}"
                    )

                data = await response.json()
                library_items = data.get("result", [])

                # Filter items with watch progress (timeWatched > 0)
                watching = [
                    item
                    for item in library_items
                    if item.get("state", {}).get("timeWatched", 0) > 0
                ]

                # Sort by most recently watched and limit
                watching.sort(
                    key=lambda x: x.get("state", {}).get("lastWatched", 0), reverse=True
                )
                watching = watching[:limit]

                _LOGGER.debug(
                    "Found %d items in continue watching list",
                    len(watching),
                )
                return self._process_continue_watching(watching)

        except StremioAuthError:
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting continue watching: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to get continue watching")
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

        Note: Stream fetching requires querying user's installed addons.
        Each addon provides streams via the Stremio addon protocol:
        - Addon manifest at /manifest.json
        - Streams at /stream/{type}/{videoID}.json

        This is a complex operation that requires addon integration.

        Args:
            media_id: Content identifier (e.g., IMDb ID like "tt1234567")
            media_type: Type of media ("movie" or "series")
            season: Season number for series
            episode: Episode number for series

        Returns:
            List of stream dictionaries

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot get streams: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        try:
            # Build video ID for series (format: imdb_id:season:episode)
            if media_type == "series" and season is not None and episode is not None:
                video_id = f"{media_id}:{season}:{episode}"
            else:
                video_id = media_id

            _LOGGER.info(
                "Stream fetching requested for %s (type: %s, video_id: %s)",
                media_id,
                media_type,
                video_id,
            )

            # TODO: Implement addon-based stream fetching
            # This would require:
            # 1. Get user's addon collection via addonCollectionGet
            # 2. For each addon that provides "stream" resource:
            #    - Query /stream/{type}/{video_id}.json
            # 3. Aggregate and return all streams
            #
            # For now, return empty list with info logging
            _LOGGER.warning(
                "Stream fetching via addons not yet implemented. "
                "Use the handover service with a direct stream URL instead."
            )
            return []

        except Exception as err:
            _LOGGER.exception("Failed to get streams for %s", media_id)
            raise StremioConnectionError(f"Failed to get streams: {err}") from err

    async def async_add_to_library(
        self, media_id: str, media_type: str = "movie"
    ) -> bool:
        """Add item to library.

        Uses the datastorePut endpoint to add an item to the user's library.
        The item is created with default state (not watched).

        Args:
            media_id: Content identifier (e.g., IMDb ID like "tt1234567")
            media_type: Type of media ("movie" or "series")

        Returns:
            True if successful

        Raises:
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot add to library: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        _LOGGER.info("Adding to library: %s (type: %s)", media_id, media_type)

        try:
            session = await self._get_session()

            # Build library item ID (format: type:imdb_id)
            item_id = f"{media_type}:{media_id}"
            current_time = int(time.time() * 1000)  # milliseconds

            # Create library item structure based on Stremio's format
            library_item = {
                "_id": item_id,
                "type": media_type,
                "name": "",  # Name will be populated by Stremio
                "poster": "",
                "removed": False,
                "temp": False,
                "state": {
                    "lastWatched": None,
                    "timeWatched": 0,
                    "timeOffset": 0,
                    "duration": 0,
                    "video_id": None,
                    "watched": False,
                    "noNotif": False,
                },
                "mtime": current_time,
            }

            payload = {
                "authKey": self._auth_key,
                "collection": COLLECTION_LIBRARY_ITEM,
                "changes": [library_item],
            }

            _LOGGER.debug("Sending datastorePut request to add library item")

            async with session.post(STREMIO_DATASTORE_PUT_URL, json=payload) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while adding to library")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to add to library (status %d): %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Failed to add to library with status {response.status}: {text}"
                    )

                data = await response.json()
                success = data.get("success", False) or data.get("result", {}).get("success", False)

                if success:
                    _LOGGER.info("Successfully added %s to library", media_id)
                else:
                    _LOGGER.warning("Add to library returned non-success: %s", data)

                return success

        except (StremioAuthError, StremioConnectionError):
            raise
        except ClientError as err:
            _LOGGER.error("Connection error adding to library: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to add to library")
            raise StremioConnectionError(f"Failed to add to library: {err}") from err

    async def async_remove_from_library(self, media_id: str) -> bool:
        """Remove item from library.

        Uses the datastorePut endpoint to mark an item as removed.
        The item is not actually deleted, but flagged with removed=True.

        Args:
            media_id: Content identifier (e.g., IMDb ID like "tt1234567")

        Returns:
            True if successful

        Raises:
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot remove from library: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        _LOGGER.info("Removing from library: %s", media_id)

        try:
            session = await self._get_session()
            current_time = int(time.time() * 1000)  # milliseconds

            # Try both movie and series formats since we may not know the type
            # In practice, the ID should include the type prefix
            if ":" in media_id:
                item_id = media_id
            else:
                # Default to movie format, but this may need adjustment
                item_id = f"movie:{media_id}"
                _LOGGER.debug("No type prefix in media_id, assuming movie: %s", item_id)

            # Mark item as removed
            library_item = {
                "_id": item_id,
                "removed": True,
                "mtime": current_time,
            }

            payload = {
                "authKey": self._auth_key,
                "collection": COLLECTION_LIBRARY_ITEM,
                "changes": [library_item],
            }

            _LOGGER.debug("Sending datastorePut request to remove library item")

            async with session.post(STREMIO_DATASTORE_PUT_URL, json=payload) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while removing from library")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to remove from library (status %d): %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Failed to remove from library with status {response.status}: {text}"
                    )

                data = await response.json()
                success = data.get("success", False) or data.get("result", {}).get("success", False)

                if success:
                    _LOGGER.info("Successfully removed %s from library", media_id)
                else:
                    _LOGGER.warning("Remove from library returned non-success: %s", data)

                return success

        except (StremioAuthError, StremioConnectionError):
            raise
        except ClientError as err:
            _LOGGER.error("Connection error removing from library: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to remove from library")
            raise StremioConnectionError(
                f"Failed to remove from library: {err}"
            ) from err

    def _process_library_items(
        self, library: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process library items into consistent format.

        Args:
            library: Raw library data from API

        Returns:
            Processed library items
        """
        if not library:
            _LOGGER.debug("No library items to process")
            return []

        items = []
        errors = 0

        for item in library:
            try:
                # Skip removed items
                if item.get("removed", False):
                    continue

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
                errors += 1
                _LOGGER.debug("Error processing library item %s: %s", item.get("_id", "unknown"), err)

        if errors > 0:
            _LOGGER.warning("Encountered %d errors processing library items", errors)

        _LOGGER.debug("Processed %d library items (filtered from %d)", len(items), len(library))
        return items

    def _process_continue_watching(
        self, watching: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process continue watching items into consistent format.

        Args:
            watching: Raw continue watching data from API

        Returns:
            Processed continue watching items
        """
        if not watching:
            _LOGGER.debug("No continue watching items to process")
            return []

        items = []
        errors = 0

        for item in watching:
            try:
                # Skip removed items
                if item.get("removed", False):
                    continue

                # Extract item data
                _id = item.get("_id", "")
                name = item.get("name", "Unknown")
                item_type = item.get("type", "unknown")
                state = item.get("state", {})

                # Parse ID
                imdb_id = _id.split(":", 1)[1] if ":" in _id else _id

                # Extract video info from state (for series: imdb:season:episode)
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
                errors += 1
                _LOGGER.debug(
                    "Error processing continue watching item %s: %s",
                    item.get("_id", "unknown"),
                    err,
                )

        if errors > 0:
            _LOGGER.warning("Encountered %d errors processing continue watching items", errors)

        _LOGGER.debug("Processed %d continue watching items", len(items))
        return items

    def _process_streams(self, streams: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process streams into consistent format.

        Args:
            streams: Raw stream data from addon response

        Returns:
            Processed stream items
        """
        if not streams:
            _LOGGER.debug("No streams to process")
            return []

        items = []
        errors = 0

        for stream in streams:
            try:
                url = stream.get("url")
                if url:
                    processed = {
                        "url": url,
                        "name": stream.get("name"),
                        "title": stream.get("title"),
                        "quality": stream.get("quality"),
                        "source": stream.get("source"),
                        "behaviorHints": stream.get("behaviorHints", {}),
                    }
                    items.append(processed)
            except (AttributeError, TypeError, KeyError) as err:
                errors += 1
                _LOGGER.debug("Error processing stream: %s", err)

        if errors > 0:
            _LOGGER.warning("Encountered %d errors processing streams", errors)

        _LOGGER.debug("Processed %d streams from %d raw entries", len(items), len(streams))
        return items

    async def async_get_addon_collection(self) -> list[dict[str, Any]]:
        """Get user's installed addon collection.

        Uses the addonCollectionGet endpoint to retrieve the user's addon manifests.

        Returns:
            List of addon manifest dictionaries

        Raises:
            StremioConnectionError: Connection failed
        """
        if not self._auth_key:
            _LOGGER.error("Cannot get addon collection: client not authenticated")
            raise StremioConnectionError("Client not authenticated")

        _LOGGER.debug("Fetching addon collection from Stremio API")

        try:
            session = await self._get_session()

            payload = {
                "authKey": self._auth_key,
                "update": True,
            }

            async with session.post(STREMIO_ADDON_COLLECTION_URL, json=payload) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while fetching addons")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to get addon collection (status %d): %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Failed to get addon collection with status {response.status}: {text}"
                    )

                data = await response.json()
                addons = data.get("addons", []) or data.get("result", {}).get("addons", [])

                _LOGGER.info("Fetched %d addons from user's collection", len(addons))
                return addons

        except (StremioAuthError, StremioConnectionError):
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting addon collection: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to get addon collection")
            raise StremioConnectionError(f"Failed to get addon collection: {err}") from err


class StremioAuthError(HomeAssistantError):
    """Error to indicate authentication failure."""


class StremioConnectionError(HomeAssistantError):
    """Error to indicate connection failure."""
