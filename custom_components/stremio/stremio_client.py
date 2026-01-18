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

    def __init__(
        self, email: str, password: str, session: aiohttp.ClientSession | None = None
    ) -> None:
        """Initialize the Stremio client.

        Args:
            email: Stremio account email
            password: Stremio account password
            session: Optional aiohttp session (uses Home Assistant's shared session)
        """
        self._email = email
        self._password = password
        self._auth_key: str | None = None
        self._user_id: str | None = None
        self._session: aiohttp.ClientSession | None = session
        self._owns_session: bool = session is None  # Track if we created the session
        self._last_auth_time: float = 0
        _LOGGER.debug(
            "StremioClient initialized for user: %s (external_session=%s)",
            email,
            session is not None,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
            self._owns_session = True  # We created it, so we own it
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
        """Close the API client and cleanup resources.

        Only closes the session if we own it (i.e., we created it ourselves).
        If using Home Assistant's shared session, we don't close it.
        """
        _LOGGER.debug("Closing StremioClient (owns_session=%s)", self._owns_session)
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
            _LOGGER.debug("Closed owned aiohttp session")
        self._session = None
        self._auth_key = None
        _LOGGER.debug("StremioClient closed")

    async def async_get_user(self) -> dict[str, Any]:
        """Get user profile information.

        Uses the getUser endpoint to retrieve the user profile.
        Based on Stremio Core API: APIRequest::GetUser { auth_key }

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
            # Use getUser endpoint - based on Stremio Core API
            payload = {
                "authKey": self._auth_key,
            }
            _LOGGER.debug("Sending getUser request")

            async with session.post(
                f"{STREMIO_API_BASE}/api/getUser", json=payload
            ) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while fetching user")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to get user (status %d): %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Failed to get user with status {response.status}: {text}"
                    )

                data = await response.json()
                user_data = data.get("result", {})

                _LOGGER.debug(
                    "Successfully fetched user profile: %s",
                    (
                        list(user_data.keys())
                        if isinstance(user_data, dict)
                        else type(user_data)
                    ),
                )
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

        Uses the datastoreGet endpoint with all=true to get all library items.
        Based on Stremio Core API: https://github.com/Stremio/stremio-core

        DatastoreCommand::Get { ids: [], all: true } fetches all items.

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
            # Use datastoreGet with all=true to fetch full library items
            # Based on Stremio Core: DatastoreRequest { auth_key, collection, command: Get { ids: [], all: true } }
            payload = {
                "authKey": self._auth_key,
                "collection": COLLECTION_LIBRARY_ITEM,
                "all": True,
                "ids": [],
            }
            _LOGGER.debug("Sending datastoreGet request for library items")

            async with session.post(
                STREMIO_DATASTORE_GET_URL, json=payload
            ) as response:
                if response.status == 401:
                    _LOGGER.warning("Authentication expired while fetching library")
                    raise StremioAuthError("Authentication expired or invalid")
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error(
                        "Failed to get library (status %d): %s",
                        response.status,
                        text[:200],
                    )
                    raise StremioConnectionError(
                        f"Failed to get library with status {response.status}: {text}"
                    )

                data = await response.json()
                _LOGGER.debug("Library API response keys: %s", list(data.keys()))

                # datastoreGet returns {"result": [item1, item2, ...]} - flat array of items
                library_items = data.get("result", [])

                # Validate response structure
                if not isinstance(library_items, list):
                    _LOGGER.warning(
                        "Unexpected library response type: %s", type(library_items)
                    )
                    library_items = []

                _LOGGER.info(
                    "Fetched %d library items from Stremio", len(library_items)
                )
                if library_items and isinstance(library_items[0], dict):
                    _LOGGER.debug(
                        "First library item keys: %s", list(library_items[0].keys())
                    )
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
        self, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get continue watching list.

        Fetches library items and filters to those with active watch progress.
        Items are sorted by most recently watched.

        Args:
            limit: Maximum items to return (default 100 to match Stremio Web)

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
            # Use datastoreGet with all=true to fetch full library items
            payload = {
                "authKey": self._auth_key,
                "collection": COLLECTION_LIBRARY_ITEM,
                "all": True,
                "ids": [],
            }
            _LOGGER.debug("Sending datastoreGet request for continue watching")

            async with session.post(
                STREMIO_DATASTORE_GET_URL, json=payload
            ) as response:
                if response.status == 401:
                    _LOGGER.warning(
                        "Authentication expired while fetching continue watching"
                    )
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

                if not isinstance(library_items, list):
                    library_items = []

                # Filter items with watch progress (timeWatched > 0)
                watching = [
                    item
                    for item in library_items
                    if isinstance(item, dict)
                    and item.get("state", {}).get("timeWatched", 0) > 0
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
        addon_order: list[str] | None = None,
        quality_preference: str = "any",
    ) -> list[dict[str, Any]]:
        """Get available streams for content from user's installed addons.

        Stream fetching queries user's installed addons via the Stremio addon protocol:
        - Get addon collection via addonCollectionGet
        - Filter addons providing "stream" resource for the content type
        - Query each addon at /stream/{type}/{videoID}.json
        - Aggregate and return all streams

        Args:
            media_id: Content identifier (e.g., IMDb ID like "tt1234567")
            media_type: Type of media ("movie" or "series")
            season: Season number for series
            episode: Episode number for series
            addon_order: Optional list of addon names/IDs in preferred order
            quality_preference: Preferred quality ("any", "4k", "1080p", "720p", "480p")

        Returns:
            List of stream dictionaries with keys like:
            - name: Stream source name
            - title: Stream description
            - url: Direct URL (if available)
            - infoHash: Torrent info hash (if torrent)
            - quality: Stream quality

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
                "Fetching streams for %s (type: %s, video_id: %s)",
                media_id,
                media_type,
                video_id,
            )

            # Get user's addon collection
            addons = await self.async_get_addon_collection()

            # Filter addons that provide stream resource for this content type
            stream_addons = self._filter_stream_addons(addons, media_type, media_id)
            _LOGGER.debug(
                "Found %d addons providing streams for %s",
                len(stream_addons),
                media_type,
            )

            # Sort addons by user preference if addon_order is provided
            if addon_order:
                stream_addons = self._sort_addons_by_preference(
                    stream_addons, addon_order
                )
                _LOGGER.debug(
                    "Sorted addons by user preference: %s",
                    [a.get("name") for a in stream_addons],
                )

            if not stream_addons:
                _LOGGER.info("No stream addons found for %s %s", media_type, media_id)
                return []

            # Query each addon for streams (in parallel)
            all_streams = await self._fetch_streams_from_addons(
                stream_addons, media_type, video_id
            )

            # Filter streams by quality preference
            if quality_preference and quality_preference != "any":
                all_streams = self._filter_streams_by_quality(
                    all_streams, quality_preference
                )
                _LOGGER.debug(
                    "Filtered to %d streams matching quality preference: %s",
                    len(all_streams),
                    quality_preference,
                )

            _LOGGER.info(
                "Found %d total streams for %s from %d addons",
                len(all_streams),
                video_id,
                len(stream_addons),
            )

            return all_streams

        except (StremioAuthError, StremioConnectionError):
            raise
        except Exception as err:
            _LOGGER.exception("Failed to get streams for %s", media_id)
            raise StremioConnectionError(f"Failed to get streams: {err}") from err

    def _filter_stream_addons(
        self,
        addons: list[dict[str, Any]],
        media_type: str,
        media_id: str,
    ) -> list[dict[str, Any]]:
        """Filter addons that provide streams for the given content type.

        Args:
            addons: List of addon manifests from user's collection
            media_type: Content type (movie, series)
            media_id: Content ID (for prefix matching)

        Returns:
            List of addons that can provide streams
        """
        stream_addons = []

        for addon in addons:
            manifest = addon.get("manifest", {})
            transport_url = addon.get("transportUrl", "")

            if not transport_url:
                continue

            # Check if addon provides stream resource
            resources = manifest.get("resources", [])
            provides_stream = False
            types_match = False
            prefix_match = (
                True  # Default to true if no prefix defined or media_id is empty
            )

            for resource in resources:
                if isinstance(resource, str):
                    if resource == "stream":
                        provides_stream = True
                        # Use manifest-level types
                        types = manifest.get("types", [])
                        types_match = media_type in types or not types
                        # Check id prefix - skip check if media_id is empty
                        prefixes = manifest.get("idPrefixes", [])
                        if prefixes and media_id:
                            prefix_match = any(media_id.startswith(p) for p in prefixes)
                        else:
                            prefix_match = True
                elif isinstance(resource, dict):
                    if resource.get("name") == "stream":
                        provides_stream = True
                        # Use resource-specific types or fallback to manifest
                        types = resource.get("types", manifest.get("types", []))
                        types_match = media_type in types or not types
                        # Check id prefix - skip check if media_id is empty
                        prefixes = resource.get(
                            "idPrefixes", manifest.get("idPrefixes", [])
                        )
                        if prefixes and media_id:
                            prefix_match = any(media_id.startswith(p) for p in prefixes)
                        else:
                            prefix_match = True

            if provides_stream and types_match and prefix_match:
                stream_addons.append(
                    {
                        "name": manifest.get("name", "Unknown Addon"),
                        "id": manifest.get("id", ""),
                        "transport_url": transport_url,
                    }
                )
                _LOGGER.debug(
                    "Addon '%s' can provide streams for %s",
                    manifest.get("name"),
                    media_type,
                )

        return stream_addons

    def _sort_addons_by_preference(
        self,
        addons: list[dict[str, Any]],
        addon_order: list[str] | str,
    ) -> list[dict[str, Any]]:
        """Sort addons according to user preference.

        Args:
            addons: List of addon dictionaries with 'name' and 'id' keys
            addon_order: User's preferred order (list of addon names/IDs or multiline string)

        Returns:
            Sorted list of addons with preferred ones first
        """
        if not addon_order:
            return addons

        # Parse addon_order if it's a string (multiline text from config)
        order_list: list[str]
        if isinstance(addon_order, str):
            order_list = [
                line.strip() for line in addon_order.split("\n") if line.strip()
            ]
        else:
            order_list = addon_order

        if not order_list:
            return addons

        _LOGGER.debug("Addon preference order: %s", order_list)
        _LOGGER.debug("Available addons: %s", [a.get("name") for a in addons])

        # Create a mapping of addon name/id to index in preference list
        # Lower index = higher priority
        # Store both exact lowercase match and normalized (alphanumeric only) for fuzzy match
        preference_map: dict[str, int] = {}
        preference_map_normalized: dict[str, int] = {}
        for idx, pref in enumerate(order_list):
            pref_lower = pref.lower()
            preference_map[pref_lower] = idx
            # Create normalized version (remove special chars for fuzzy matching)
            pref_normalized = "".join(c.lower() for c in pref if c.isalnum())
            if pref_normalized:
                preference_map_normalized[pref_normalized] = idx

        def get_sort_key(addon: dict[str, Any]) -> tuple[int, str]:
            """Get sort key for addon (priority, name)."""
            name = addon.get("name", "")
            addon_id = addon.get("id", "")
            name_lower = name.lower()
            addon_id_lower = addon_id.lower()

            # First try exact match (case-insensitive)
            if name_lower in preference_map:
                _LOGGER.debug(
                    "Addon '%s' matched by exact name at position %d",
                    name,
                    preference_map[name_lower],
                )
                return (preference_map[name_lower], name_lower)
            if addon_id_lower in preference_map:
                _LOGGER.debug(
                    "Addon '%s' matched by exact ID at position %d",
                    name,
                    preference_map[addon_id_lower],
                )
                return (preference_map[addon_id_lower], name_lower)

            # Try normalized match (ignore special characters)
            name_normalized = "".join(c.lower() for c in name if c.isalnum())
            addon_id_normalized = "".join(c.lower() for c in addon_id if c.isalnum())
            if name_normalized in preference_map_normalized:
                _LOGGER.debug(
                    "Addon '%s' matched by normalized name at position %d",
                    name,
                    preference_map_normalized[name_normalized],
                )
                return (preference_map_normalized[name_normalized], name_lower)
            if addon_id_normalized in preference_map_normalized:
                _LOGGER.debug(
                    "Addon '%s' matched by normalized ID at position %d",
                    name,
                    preference_map_normalized[addon_id_normalized],
                )
                return (preference_map_normalized[addon_id_normalized], name_lower)

            # Try partial/contains match for preferences
            for pref_lower, idx in preference_map.items():
                if pref_lower in name_lower or name_lower in pref_lower:
                    _LOGGER.debug(
                        "Addon '%s' matched by partial name '%s' at position %d",
                        name,
                        pref_lower,
                        idx,
                    )
                    return (idx, name_lower)
                if pref_lower in addon_id_lower or addon_id_lower in pref_lower:
                    _LOGGER.debug(
                        "Addon '%s' matched by partial ID '%s' at position %d",
                        name,
                        pref_lower,
                        idx,
                    )
                    return (idx, name_lower)

            # Not in preference list - put at the end
            _LOGGER.debug("Addon '%s' not matched, placing at end", name)
            return (len(order_list), name_lower)

        return sorted(addons, key=get_sort_key)

    def _filter_streams_by_quality(
        self,
        streams: list[dict[str, Any]],
        quality_preference: str,
    ) -> list[dict[str, Any]]:
        """Filter and sort streams by quality preference.

        Args:
            streams: List of stream dictionaries
            quality_preference: Desired quality ("4k", "1080p", "720p", "480p")

        Returns:
            Filtered list with matching quality streams first, then others
        """
        if quality_preference == "any":
            return streams

        # Quality patterns to look for (in stream name/title)
        quality_patterns: dict[str, list[str]] = {
            "4k": ["4k", "2160p", "uhd"],
            "1080p": ["1080p", "1080", "fhd", "full hd"],
            "720p": ["720p", "720", "hd"],
            "480p": ["480p", "480", "sd"],
        }

        patterns = quality_patterns.get(quality_preference.lower(), [])
        if not patterns:
            return streams

        def stream_matches_quality(stream: dict[str, Any]) -> bool:
            """Check if stream matches the quality preference."""
            # Check in name, title, and quality fields
            searchable = " ".join(
                [
                    str(stream.get("name", "")),
                    str(stream.get("title", "")),
                    str(stream.get("quality", "")),
                ]
            ).lower()

            return any(pattern in searchable for pattern in patterns)

        # Sort streams: matching quality first, then others
        matching = [s for s in streams if stream_matches_quality(s)]
        non_matching = [s for s in streams if not stream_matches_quality(s)]

        _LOGGER.debug(
            "Quality filter '%s': %d matching, %d other streams",
            quality_preference,
            len(matching),
            len(non_matching),
        )

        return matching + non_matching

    async def _fetch_streams_from_addons(
        self,
        addons: list[dict[str, Any]],
        media_type: str,
        video_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch streams from multiple addons.

        Args:
            addons: List of filtered addons with transport URLs
            media_type: Content type
            video_id: Video ID (imdb_id or imdb_id:season:episode)

        Returns:
            Aggregated list of streams from all addons
        """
        import asyncio

        all_streams: list[dict[str, Any]] = []
        session = await self._get_session()

        async def fetch_from_addon(addon: dict[str, Any]) -> list[dict[str, Any]]:
            """Fetch streams from a single addon."""
            transport_url = addon["transport_url"]
            addon_name = addon["name"]

            # Build stream URL: {base_url}/stream/{type}/{video_id}.json
            # Remove manifest.json from URL if present
            base_url = transport_url.replace("/manifest.json", "")
            stream_url = f"{base_url}/stream/{media_type}/{video_id}.json"

            try:
                _LOGGER.debug("Fetching streams from %s: %s", addon_name, stream_url)

                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        _LOGGER.debug(
                            "Addon %s returned status %d for streams",
                            addon_name,
                            response.status,
                        )
                        return []

                    data = await response.json()
                    streams = data.get("streams", [])

                    # Add addon name to each stream for identification
                    for stream in streams:
                        if "addon" not in stream:
                            stream["addon"] = addon_name

                    _LOGGER.debug(
                        "Addon %s returned %d streams", addon_name, len(streams)
                    )
                    return streams

            except asyncio.TimeoutError:
                _LOGGER.debug("Timeout fetching streams from %s", addon_name)
                return []
            except Exception as err:
                _LOGGER.debug("Error fetching streams from %s: %s", addon_name, err)
                return []

        # Fetch from all addons in parallel
        tasks = [fetch_from_addon(addon) for addon in addons]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_streams.extend(result)

        return all_streams

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

            async with session.post(
                STREMIO_DATASTORE_PUT_URL, json=payload
            ) as response:
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
                success = data.get("success", False) or data.get("result", {}).get(
                    "success", False
                )

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

            async with session.post(
                STREMIO_DATASTORE_PUT_URL, json=payload
            ) as response:
                if response.status == 401:
                    _LOGGER.warning(
                        "Authentication expired while removing from library"
                    )
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
                success = data.get("success", False) or data.get("result", {}).get(
                    "success", False
                )

                if success:
                    _LOGGER.info("Successfully removed %s from library", media_id)
                else:
                    _LOGGER.warning(
                        "Remove from library returned non-success: %s", data
                    )

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
                item_id = (
                    item.get("_id", "unknown")
                    if isinstance(item, dict)
                    else "invalid_item"
                )
                _LOGGER.debug("Error processing library item %s: %s", item_id, err)

        if errors > 0:
            _LOGGER.warning("Encountered %d errors processing library items", errors)

        _LOGGER.debug(
            "Processed %d library items (filtered from %d)", len(items), len(library)
        )
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
                    "episode_title": None,  # Will be populated if metadata is fetched
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
            _LOGGER.warning(
                "Encountered %d errors processing continue watching items", errors
            )

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

        _LOGGER.debug(
            "Processed %d streams from %d raw entries", len(items), len(streams)
        )
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

            async with session.post(
                STREMIO_ADDON_COLLECTION_URL, json=payload
            ) as response:
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
                addons = data.get("addons", []) or data.get("result", {}).get(
                    "addons", []
                )

                _LOGGER.info("Fetched %d addons from user's collection", len(addons))
                return addons

        except (StremioAuthError, StremioConnectionError):
            raise
        except ClientError as err:
            _LOGGER.error("Connection error getting addon collection: %s", err)
            raise StremioConnectionError(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Failed to get addon collection")
            raise StremioConnectionError(
                f"Failed to get addon collection: {err}"
            ) from err

    async def async_get_series_metadata(self, media_id: str) -> dict[str, Any] | None:
        """Fetch series metadata including seasons and episodes from Cinemeta.

        Args:
            media_id: IMDb ID of the series (e.g., "tt1234567")

        Returns:
            Dictionary with series metadata including videos (episodes), or None if not found
        """
        _LOGGER.debug("Fetching series metadata for %s", media_id)

        # Cinemeta is the standard metadata addon for Stremio
        cinemeta_url = f"https://v3-cinemeta.strem.io/meta/series/{media_id}.json"

        try:
            session = await self._get_session()

            async with session.get(
                cinemeta_url,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Cinemeta returned status %d for series %s",
                        response.status,
                        media_id,
                    )
                    return None

                data = await response.json()
                meta = data.get("meta", {})

                if not meta:
                    _LOGGER.debug("No metadata found for series %s", media_id)
                    return None

                # Process videos (episodes) into seasons structure
                videos = meta.get("videos", [])
                seasons_dict: dict[int, dict[str, Any]] = {}

                for video in videos:
                    season_num = video.get("season")
                    episode_num = video.get("episode") or video.get("number")

                    if season_num is None:
                        continue

                    if season_num not in seasons_dict:
                        seasons_dict[season_num] = {
                            "number": season_num,
                            "title": f"Season {season_num}",
                            "episodes": [],
                        }

                    seasons_dict[season_num]["episodes"].append(
                        {
                            "number": episode_num,
                            "title": video.get("title")
                            or video.get("name")
                            or f"Episode {episode_num}",
                            "overview": video.get("overview"),
                            "thumbnail": video.get("thumbnail"),
                            "released": video.get("released"),
                            "id": video.get("id"),
                        }
                    )

                # Sort seasons and episodes
                seasons = []
                for season_num in sorted(seasons_dict.keys()):
                    season_data = seasons_dict[season_num]
                    # Sort episodes by number
                    season_data["episodes"] = sorted(
                        season_data["episodes"],
                        key=lambda e: e.get("number", 0) or 0,
                    )
                    seasons.append(season_data)

                result = {
                    "id": meta.get("id"),
                    "imdb_id": meta.get("imdb_id") or media_id,
                    "title": meta.get("name"),
                    "poster": meta.get("poster"),
                    "background": meta.get("background"),
                    "description": meta.get("description"),
                    "year": meta.get("year"),
                    "genres": meta.get("genres", []),
                    "seasons": seasons,
                    "season_count": len(seasons),
                }

                _LOGGER.debug(
                    "Fetched metadata for %s: %d seasons",
                    media_id,
                    len(seasons),
                )
                return result

        except Exception as err:
            _LOGGER.debug("Error fetching series metadata for %s: %s", media_id, err)
            return None

    async def async_get_catalog(
        self,
        media_type: str = "movie",
        catalog_id: str = "top",
        genre: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch catalog items from Cinemeta (popular, trending, etc.).

        Uses Cinemeta's catalog endpoint to browse popular movies and series.
        Endpoint format: /catalog/{type}/{catalog_id}/{extra}.json

        Example URLs:
        - https://v3-cinemeta.strem.io/catalog/movie/top/popular.json
        - https://v3-cinemeta.strem.io/catalog/series/top/popular.json?genre=Drama
        - https://v3-cinemeta.strem.io/catalog/movie/top/popular.json?skip=20

        Args:
            media_type: Content type ("movie" or "series")
            catalog_id: Catalog identifier ("top" for popular/trending)
            genre: Optional genre filter (Action, Drama, etc.)
            skip: Number of items to skip for pagination
            limit: Maximum items to return (default 50)

        Returns:
            List of catalog item dictionaries with keys:
            - id: IMDb ID
            - type: "movie" or "series"
            - name: Title
            - poster: Poster image URL
            - posterShape: "poster" or "square"
            - year: Release year (optional)
            - description: Plot summary (optional)

        Raises:
            StremioConnectionError: Connection or request failed
        """
        _LOGGER.debug(
            "Fetching catalog: type=%s, catalog=%s, genre=%s, skip=%d",
            media_type,
            catalog_id,
            genre,
            skip,
        )

        # Build catalog URL
        # Cinemeta API uses path-based format for extra parameters:
        # /catalog/{type}/{id}.json - basic catalog
        # /catalog/{type}/{id}/genre={genre}.json - genre filtered
        # /catalog/{type}/{id}/skip={skip}.json - pagination
        # /catalog/{type}/{id}/genre={genre}&skip={skip}.json - combined
        from .const import CINEMETA_BASE_URL

        # Build extra path components for genre and skip
        extra_parts = []
        if genre:
            extra_parts.append(f"genre={genre}")
        if skip > 0:
            extra_parts.append(f"skip={skip}")

        if extra_parts:
            extra_path = "&".join(extra_parts)
            catalog_url = f"{CINEMETA_BASE_URL}/catalog/{media_type}/{catalog_id}/{extra_path}.json"
        else:
            catalog_url = f"{CINEMETA_BASE_URL}/catalog/{media_type}/{catalog_id}.json"

        try:
            session = await self._get_session()

            async with session.get(
                catalog_url,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status != 200:
                    _LOGGER.warning(
                        "Cinemeta catalog returned status %d for %s/%s",
                        response.status,
                        media_type,
                        catalog_id,
                    )
                    return []

                data = await response.json()
                metas = data.get("metas", [])

                if not metas:
                    _LOGGER.debug(
                        "No catalog items found for %s/%s", media_type, catalog_id
                    )
                    return []

                # Limit results
                metas = metas[:limit]

                # Process catalog items into consistent format
                processed_items = []
                for meta in metas:
                    try:
                        item = {
                            "id": meta.get("id"),
                            "imdb_id": meta.get("id"),
                            "type": meta.get("type", media_type),
                            "title": meta.get("name"),
                            "poster": meta.get("poster"),
                            "posterShape": meta.get("posterShape", "poster"),
                            "year": meta.get("releaseInfo"),
                            "description": meta.get("description"),
                            "genres": meta.get("genres", []),
                            "cast": meta.get("cast", []),
                            "director": meta.get("director"),
                            "rating": meta.get("imdbRating"),
                        }
                        processed_items.append(item)
                    except (AttributeError, TypeError, KeyError) as err:
                        _LOGGER.debug(
                            "Error processing catalog item %s: %s",
                            meta.get("id", "unknown"),
                            err,
                        )
                        continue

                _LOGGER.info(
                    "Fetched %d catalog items for %s/%s",
                    len(processed_items),
                    media_type,
                    catalog_id,
                )
                return processed_items

        except Exception as err:
            _LOGGER.error(
                "Error fetching catalog %s/%s: %s", media_type, catalog_id, err
            )
            raise StremioConnectionError(f"Failed to fetch catalog: {err}") from err

    async def async_get_popular_movies(
        self, genre: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get popular movies from Cinemeta.

        Args:
            genre: Optional genre filter
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            List of popular movie dictionaries
        """
        return await self.async_get_catalog(
            media_type="movie",
            catalog_id="top",
            genre=genre,
            skip=skip,
            limit=limit,
        )

    async def async_get_popular_series(
        self, genre: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get popular TV series from Cinemeta.

        Args:
            genre: Optional genre filter
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            List of popular series dictionaries
        """
        return await self.async_get_catalog(
            media_type="series",
            catalog_id="top",
            genre=genre,
            skip=skip,
            limit=limit,
        )

    async def async_get_upcoming_episodes(
        self, days_ahead: int = 7
    ) -> list[dict[str, Any]]:
        """Get upcoming episode air dates for series in the user's library.

        Fetches metadata for all series in the library and checks for upcoming
        episodes based on air dates.

        Args:
            days_ahead: Number of days to look ahead (default 7)

        Returns:
            List of upcoming episodes with series info and air dates

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        import datetime

        _LOGGER.debug("Fetching upcoming episodes for next %d days", days_ahead)

        try:
            # Get user's library
            library = await self.async_get_library()

            # Filter to series only
            series_items = [item for item in library if item.get("type") == "series"]
            _LOGGER.debug("Found %d series in library", len(series_items))

            upcoming = []
            today = datetime.datetime.now(datetime.timezone.utc)
            cutoff_date = today + datetime.timedelta(days=days_ahead)

            # Fetch metadata for each series (limit concurrent requests)
            for series in series_items[:20]:  # Limit to avoid rate limiting
                try:
                    imdb_id = (
                        series.get("imdb_id") or series.get("id", "").split(":")[-1]
                    )
                    if not imdb_id:
                        continue

                    metadata = await self.async_get_series_metadata(imdb_id)
                    if not metadata:
                        continue

                    # Check each season/episode for upcoming air dates
                    for season in metadata.get("seasons", []):
                        for episode in season.get("episodes", []):
                            released_str = episode.get("released")
                            if not released_str:
                                continue

                            try:
                                # Parse ISO format air date
                                air_date = datetime.datetime.fromisoformat(
                                    released_str.replace("Z", "+00:00")
                                )

                                # Check if it's upcoming (after today, before cutoff)
                                if today <= air_date <= cutoff_date:
                                    upcoming.append(
                                        {
                                            "series_id": imdb_id,
                                            "series_title": series.get("title")
                                            or metadata.get("title"),
                                            "poster": series.get("poster")
                                            or metadata.get("poster"),
                                            "season": season.get("number"),
                                            "episode": episode.get("number"),
                                            "episode_title": episode.get("title"),
                                            "air_date": released_str,
                                            "air_date_formatted": air_date.strftime(
                                                "%Y-%m-%d"
                                            ),
                                            "days_until": (air_date - today).days,
                                        }
                                    )
                            except (ValueError, TypeError):
                                continue

                except Exception as err:
                    _LOGGER.debug(
                        "Error fetching metadata for series %s: %s",
                        series.get("title"),
                        err,
                    )
                    continue

            # Sort by air date
            upcoming.sort(key=lambda x: x.get("air_date", ""))

            _LOGGER.info(
                "Found %d upcoming episodes in next %d days", len(upcoming), days_ahead
            )
            return upcoming

        except StremioAuthError:
            raise
        except StremioConnectionError:
            raise
        except Exception as err:
            _LOGGER.exception("Failed to get upcoming episodes: %s", err)
            raise StremioConnectionError(
                f"Failed to get upcoming episodes: {err}"
            ) from err

    async def async_get_recommendations(
        self,
        media_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get content recommendations based on user's library.

        Analyzes the user's library to identify preferred genres and fetches
        recommendations from catalogs matching those preferences.

        Args:
            media_type: Optional filter for "movie" or "series" (None for both)
            limit: Maximum recommendations to return (default 20)

        Returns:
            List of recommended content items

        Raises:
            StremioAuthError: Authentication failed
            StremioConnectionError: Connection failed
        """
        _LOGGER.debug("Fetching recommendations: type=%s, limit=%d", media_type, limit)

        try:
            # Get user's library to analyze preferences
            library = await self.async_get_library()

            if not library:
                _LOGGER.debug("Library is empty, returning popular content")
                # Return popular content if library is empty
                if media_type == "movie":
                    return await self.async_get_popular_movies(limit=limit)
                elif media_type == "series":
                    return await self.async_get_popular_series(limit=limit)
                else:
                    movies = await self.async_get_popular_movies(limit=limit // 2)
                    series = await self.async_get_popular_series(limit=limit // 2)
                    return movies + series

            # Filter library by type if specified
            filtered_library = library
            if media_type:
                filtered_library = [
                    item for item in library if item.get("type") == media_type
                ]

            # Analyze genres from library
            genre_counts: dict[str, int] = {}
            library_ids = set()
            for item in filtered_library:
                library_ids.add(item.get("imdb_id") or item.get("id"))
                for genre in item.get("genres", []):
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1

            # Get top genres (sorted by count)
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            _LOGGER.debug("Top genres from library: %s", top_genres)

            recommendations = []
            seen_ids = set()

            # Fetch recommendations based on top genres
            for genre, _ in top_genres:
                try:
                    if media_type == "movie" or media_type is None:
                        movies = await self.async_get_catalog(
                            media_type="movie",
                            catalog_id="top",
                            genre=genre,
                            limit=limit,
                        )
                        for movie in movies:
                            item_id = movie.get("imdb_id") or movie.get("id")
                            if (
                                item_id
                                and item_id not in library_ids
                                and item_id not in seen_ids
                            ):
                                movie["recommendation_reason"] = (
                                    f"Based on your interest in {genre}"
                                )
                                recommendations.append(movie)
                                seen_ids.add(item_id)

                    if media_type == "series" or media_type is None:
                        series = await self.async_get_catalog(
                            media_type="series",
                            catalog_id="top",
                            genre=genre,
                            limit=limit,
                        )
                        for show in series:
                            item_id = show.get("imdb_id") or show.get("id")
                            if (
                                item_id
                                and item_id not in library_ids
                                and item_id not in seen_ids
                            ):
                                show["recommendation_reason"] = (
                                    f"Based on your interest in {genre}"
                                )
                                recommendations.append(show)
                                seen_ids.add(item_id)

                except Exception as err:
                    _LOGGER.debug(
                        "Error fetching recommendations for genre %s: %s", genre, err
                    )
                    continue

                if len(recommendations) >= limit:
                    break

            # If not enough recommendations, add some popular content
            if len(recommendations) < limit:
                try:
                    popular = await self.async_get_catalog(
                        media_type=media_type or "movie",
                        catalog_id="top",
                        limit=limit - len(recommendations),
                    )
                    for item in popular:
                        item_id = item.get("imdb_id") or item.get("id")
                        if (
                            item_id
                            and item_id not in library_ids
                            and item_id not in seen_ids
                        ):
                            item["recommendation_reason"] = "Popular right now"
                            recommendations.append(item)
                            seen_ids.add(item_id)
                            if len(recommendations) >= limit:
                                break
                except Exception as err:
                    _LOGGER.debug("Error fetching popular content: %s", err)

            _LOGGER.info("Generated %d recommendations", len(recommendations[:limit]))
            return recommendations[:limit]

        except StremioAuthError:
            raise
        except StremioConnectionError:
            raise
        except Exception as err:
            _LOGGER.exception("Failed to get recommendations: %s", err)
            raise StremioConnectionError(
                f"Failed to get recommendations: {err}"
            ) from err

    async def async_get_similar_content(
        self,
        media_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get similar movies/shows based on a specific media item.

        Uses Cinemeta's meta endpoint to fetch related content based on
        genres, cast, and other metadata similarities.

        Args:
            media_id: IMDb ID of the media item (e.g., "tt1234567")
            limit: Maximum similar items to return (default 10)

        Returns:
            List of similar content items

        Raises:
            StremioConnectionError: Connection failed
        """
        _LOGGER.debug("Fetching similar content for %s, limit=%d", media_id, limit)

        try:
            # First, get the source item's metadata
            # Try series first, then movie
            from .const import CINEMETA_BASE_URL

            session = await self._get_session()
            source_meta = None
            source_type = None

            for content_type in ["series", "movie"]:
                meta_url = f"{CINEMETA_BASE_URL}/meta/{content_type}/{media_id}.json"
                try:
                    async with session.get(
                        meta_url,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            source_meta = data.get("meta", {})
                            if source_meta:
                                source_type = content_type
                                break
                except Exception:
                    continue

            if not source_meta:
                _LOGGER.debug("Could not find metadata for %s", media_id)
                return []

            # Extract genres and other metadata for finding similar content
            source_genres = source_meta.get("genres", [])
            source_director = source_meta.get("director")
            source_cast = source_meta.get("cast", [])[:3]  # Top 3 cast members

            _LOGGER.debug(
                "Source: %s, genres=%s, director=%s",
                source_meta.get("name"),
                source_genres,
                source_director,
            )

            similar = []
            seen_ids = {media_id}  # Don't include the source item

            # Search by primary genre
            if source_genres:
                primary_genre = source_genres[0]
                try:
                    genre_results = await self.async_get_catalog(
                        media_type=source_type,
                        catalog_id="top",
                        genre=primary_genre,
                        limit=limit * 2,  # Fetch more to filter
                    )

                    for item in genre_results:
                        item_id = item.get("imdb_id") or item.get("id")
                        if item_id and item_id not in seen_ids:
                            # Score similarity based on shared genres
                            item_genres = item.get("genres", [])
                            shared_genres = set(source_genres) & set(item_genres)
                            item["similarity_score"] = len(shared_genres)
                            item["similarity_reason"] = (
                                f"Similar {primary_genre} content"
                            )
                            similar.append(item)
                            seen_ids.add(item_id)

                except Exception as err:
                    _LOGGER.debug("Error fetching genre-based similar: %s", err)

            # If we have a secondary genre and need more results
            if len(source_genres) > 1 and len(similar) < limit:
                secondary_genre = source_genres[1]
                try:
                    genre_results = await self.async_get_catalog(
                        media_type=source_type,
                        catalog_id="top",
                        genre=secondary_genre,
                        limit=limit,
                    )

                    for item in genre_results:
                        item_id = item.get("imdb_id") or item.get("id")
                        if item_id and item_id not in seen_ids:
                            item_genres = item.get("genres", [])
                            shared_genres = set(source_genres) & set(item_genres)
                            item["similarity_score"] = len(shared_genres)
                            item["similarity_reason"] = (
                                f"You might also like this {secondary_genre}"
                            )
                            similar.append(item)
                            seen_ids.add(item_id)
                            if len(similar) >= limit * 2:
                                break

                except Exception as err:
                    _LOGGER.debug("Error fetching secondary genre similar: %s", err)

            # Sort by similarity score and limit
            similar.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            result = similar[:limit]

            _LOGGER.info("Found %d similar items for %s", len(result), media_id)
            return result

        except Exception as err:
            _LOGGER.exception("Failed to get similar content for %s: %s", media_id, err)
            raise StremioConnectionError(
                f"Failed to get similar content: {err}"
            ) from err


class StremioAuthError(HomeAssistantError):
    """Error to indicate authentication failure."""


class StremioConnectionError(HomeAssistantError):
    """Error to indicate connection failure."""
