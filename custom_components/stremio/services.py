"""Services for Stremio integration."""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .apple_tv_handover import HandoverError, HandoverManager
from .const import (
    CONF_ADDON_STREAM_ORDER,
    CONF_APPLE_TV_CREDENTIALS,
    CONF_APPLE_TV_IDENTIFIER,
    CONF_HANDOVER_METHOD,
    CONF_STREAM_QUALITY_PREFERENCE,
    DEFAULT_HANDOVER_METHOD,
    DEFAULT_STREAM_QUALITY_PREFERENCE,
    DOMAIN,
    EVENT_NEW_CONTENT,
    EVENT_PLAYBACK_STARTED,
    SERVICE_ADD_TO_LIBRARY,
    SERVICE_BROWSE_CATALOG,
    SERVICE_GET_ADDONS,
    SERVICE_GET_RECOMMENDATIONS,
    SERVICE_GET_SERIES_METADATA,
    SERVICE_GET_SIMILAR_CONTENT,
    SERVICE_GET_STREAMS,
    SERVICE_GET_UPCOMING_EPISODES,
    SERVICE_HANDOVER_TO_APPLE_TV,
    SERVICE_REFRESH_LIBRARY,
    SERVICE_REMOVE_FROM_LIBRARY,
    SERVICE_SEARCH_LIBRARY,
)
from .coordinator import StremioDataUpdateCoordinator
from .stremio_client import StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)

# Service field constants
ATTR_QUERY = "query"
ATTR_SEARCH_TYPE = "search_type"
ATTR_LIMIT = "limit"
ATTR_MEDIA_ID = "media_id"
ATTR_MEDIA_TYPE = "media_type"
ATTR_SEASON = "season"
ATTR_EPISODE = "episode"
ATTR_DEVICE_ID = "device_id"
ATTR_STREAM_URL = "stream_url"
ATTR_METHOD = "method"
ATTR_GENRE = "genre"
ATTR_SKIP = "skip"
ATTR_CATALOG_TYPE = "catalog_type"
ATTR_DAYS_AHEAD = "days_ahead"

# Service schemas
SEARCH_LIBRARY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_QUERY): cv.string,
        vol.Optional(ATTR_SEARCH_TYPE, default="all"): vol.In(
            ["all", "title", "genre", "cast"]
        ),
        vol.Optional(ATTR_LIMIT, default=10): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)  # type: ignore[arg-type]
        ),
    }
)

GET_STREAMS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDIA_ID): cv.string,
        vol.Required(ATTR_MEDIA_TYPE): vol.In(["movie", "series"]),
        vol.Optional(ATTR_SEASON): vol.Coerce(int),  # type: ignore[arg-type]
        vol.Optional(ATTR_EPISODE): vol.Coerce(int),  # type: ignore[arg-type]
    }
)

GET_SERIES_METADATA_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDIA_ID): cv.string,
    }
)

ADD_TO_LIBRARY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDIA_ID): cv.string,
        vol.Required(ATTR_MEDIA_TYPE): vol.In(["movie", "series"]),
    }
)

REMOVE_FROM_LIBRARY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDIA_ID): cv.string,
    }
)

HANDOVER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.entity_id,
        vol.Optional(ATTR_MEDIA_ID): cv.string,
        vol.Optional(ATTR_STREAM_URL): cv.string,
        vol.Optional(ATTR_METHOD): vol.In(["auto", "airplay", "vlc", "direct"]),
    }
)

BROWSE_CATALOG_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_MEDIA_TYPE, default="movie"): vol.In(["movie", "series"]),
        vol.Optional(ATTR_CATALOG_TYPE, default="popular"): vol.In(
            ["popular", "new", "genre"]
        ),
        vol.Optional(ATTR_GENRE): cv.string,
        vol.Optional(ATTR_SKIP, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0)  # type: ignore[arg-type]
        ),
        vol.Optional(ATTR_LIMIT, default=50): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=100)  # type: ignore[arg-type]
        ),
    }
)

GET_UPCOMING_EPISODES_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DAYS_AHEAD, default=7): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=30)  # type: ignore[arg-type]
        ),
    }
)

GET_RECOMMENDATIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_MEDIA_TYPE): vol.In(["movie", "series"]),
        vol.Optional(ATTR_LIMIT, default=20): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)  # type: ignore[arg-type]
        ),
    }
)

GET_SIMILAR_CONTENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDIA_ID): cv.string,
        vol.Optional(ATTR_LIMIT, default=10): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=30)  # type: ignore[arg-type]
        ),
    }
)

# Get addons has no required parameters
GET_ADDONS_SCHEMA = vol.Schema({})


def _get_entry_data(
    hass: HomeAssistant,
) -> tuple[StremioDataUpdateCoordinator, StremioClient, str]:
    """Get coordinator, client, and entry_id from first config entry.

    Args:
        hass: Home Assistant instance

    Returns:
        Tuple of coordinator, client, and entry_id

    Raises:
        ServiceValidationError: If no Stremio integration configured
    """
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        raise ServiceValidationError(
            "No Stremio integration configured",
            translation_domain=DOMAIN,
            translation_key="no_integration",
        )

    # Get the first entry's data
    entry_id = next(iter(hass.data[DOMAIN]))
    entry_data = hass.data[DOMAIN][entry_id]
    return entry_data["coordinator"], entry_data["client"], entry_id


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Stremio services.

    Args:
        hass: Home Assistant instance
    """

    async def handle_search_library(call: ServiceCall) -> ServiceResponse:  # type: ignore[return-value]
        """Handle search_library service call."""
        coordinator, _, _ = _get_entry_data(hass)

        query = call.data[ATTR_QUERY]
        search_type = call.data.get(ATTR_SEARCH_TYPE, "all")
        limit = call.data.get(ATTR_LIMIT, 10)

        _LOGGER.debug(
            "Searching library: query=%s, type=%s, limit=%s", query, search_type, limit
        )

        try:
            # Return empty results for empty query
            if not query or not query.strip():
                return {"results": [], "count": 0}

            # Get library from coordinator
            if coordinator.data is None:
                _LOGGER.warning("Coordinator data is None, refreshing...")
                await coordinator.async_request_refresh()

            library = (coordinator.data or {}).get("library", [])
            _LOGGER.debug("Library has %d items", len(library))

            # Filter based on search type
            results = []
            query_lower = query.lower()

            for item in library:
                match = False
                if search_type in ("all", "title"):
                    if query_lower in item.get("title", "").lower():
                        match = True
                if search_type in ("all", "genre"):
                    genres = item.get("genres", [])
                    if any(query_lower in g.lower() for g in genres):
                        match = True
                if search_type in ("all", "cast"):
                    cast = item.get("cast", [])
                    if any(query_lower in c.lower() for c in cast):
                        match = True

                if match:
                    results.append(
                        {
                            "id": item.get("imdb_id") or item.get("id"),
                            "title": item.get("title"),
                            "type": item.get("type"),
                            "year": item.get("year"),
                            "poster": item.get("poster"),
                            "genres": item.get("genres", []),
                        }
                    )

                if len(results) >= limit:
                    break

            return {"results": results, "count": len(results)}

        except Exception as err:
            _LOGGER.exception("Error searching library: %s", err)
            raise HomeAssistantError(f"Failed to search library: {err}") from err

    async def handle_get_streams(call: ServiceCall) -> ServiceResponse:  # type: ignore[return-value]
        """Handle get_streams service call."""
        _, client, entry_id = _get_entry_data(hass)

        media_id = call.data[ATTR_MEDIA_ID]
        media_type = call.data[ATTR_MEDIA_TYPE]
        season = call.data.get(ATTR_SEASON)
        episode = call.data.get(ATTR_EPISODE)

        # Validate series requires season/episode
        if media_type == "series" and (season is None or episode is None):
            raise ServiceValidationError(
                "Season and episode are required for series",
                translation_domain=DOMAIN,
                translation_key="missing_season_episode",
            )

        _LOGGER.debug(
            "Getting streams: media_id=%s, type=%s, S%sE%s",
            media_id,
            media_type,
            season,
            episode,
        )

        # Get user preferences from config entry options
        entry = hass.config_entries.async_get_entry(entry_id)
        addon_order = None
        quality_preference = DEFAULT_STREAM_QUALITY_PREFERENCE
        if entry:
            addon_order_raw = entry.options.get(CONF_ADDON_STREAM_ORDER)
            if addon_order_raw:
                # Handle both list (from new selector) and string (legacy) formats
                if isinstance(addon_order_raw, list):
                    addon_order = addon_order_raw
                else:
                    # Parse multiline text to list (legacy format)
                    addon_order = [
                        line.strip()
                        for line in addon_order_raw.split("\n")
                        if line.strip()
                    ]
            quality_preference = entry.options.get(
                CONF_STREAM_QUALITY_PREFERENCE, DEFAULT_STREAM_QUALITY_PREFERENCE
            )

        try:
            streams = await client.async_get_streams(
                media_id=media_id,
                media_type=media_type,
                season=season,
                episode=episode,
                addon_order=addon_order,
                quality_preference=quality_preference,
            )

            return {
                "streams": streams,
                "count": len(streams),
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to get streams: {err}") from err

    async def handle_get_series_metadata(call: ServiceCall) -> ServiceResponse:  # type: ignore[return-value]
        """Handle get_series_metadata service call.

        Fetch series metadata including seasons and episodes from Cinemeta.
        Returns structured data for the episode picker UI.
        """
        _, client, _ = _get_entry_data(hass)

        media_id = call.data[ATTR_MEDIA_ID]

        _LOGGER.debug("Getting series metadata: media_id=%s", media_id)

        try:
            metadata = await client.async_get_series_metadata(media_id)

            if not metadata:
                return {
                    "success": False,
                    "error": "No metadata found for series",
                    "media_id": media_id,
                }

            return {
                "success": True,
                "metadata": metadata,
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to get series metadata: {err}") from err
        except Exception as err:
            _LOGGER.exception("Error fetching series metadata: %s", err)
            raise HomeAssistantError(f"Failed to get series metadata: {err}") from err

    async def handle_add_to_library(call: ServiceCall) -> None:
        """Handle add_to_library service call."""
        coordinator, client, _ = _get_entry_data(hass)

        media_id = call.data[ATTR_MEDIA_ID]
        media_type = call.data[ATTR_MEDIA_TYPE]

        _LOGGER.info("Adding to library: %s (%s)", media_id, media_type)

        try:
            await client.async_add_to_library(media_id, media_type)

            # Refresh coordinator data
            await coordinator.async_request_refresh()

            # Fire event
            hass.bus.async_fire(
                EVENT_NEW_CONTENT,
                {
                    "action": "added",
                    "media_id": media_id,
                    "media_type": media_type,
                },
            )

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to add to library: {err}") from err

    async def handle_remove_from_library(call: ServiceCall) -> None:
        """Handle remove_from_library service call."""
        coordinator, client, _ = _get_entry_data(hass)

        media_id = call.data[ATTR_MEDIA_ID]

        _LOGGER.info("Removing from library: %s", media_id)

        try:
            await client.async_remove_from_library(media_id)

            # Refresh coordinator data
            await coordinator.async_request_refresh()

            # Fire event
            hass.bus.async_fire(
                EVENT_NEW_CONTENT,
                {
                    "action": "removed",
                    "media_id": media_id,
                },
            )

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to remove from library: {err}") from err

    async def handle_refresh_library(call: ServiceCall) -> None:
        """Handle refresh_library service call."""
        coordinator, _, _ = _get_entry_data(hass)

        _LOGGER.info("Refreshing library data")

        await coordinator.async_request_refresh()

    async def handle_handover_to_apple_tv(call: ServiceCall) -> None:
        """Handle handover_to_apple_tv service call."""
        coordinator, client, entry_id = _get_entry_data(hass)

        device_id = call.data[ATTR_DEVICE_ID]
        media_id = call.data.get(ATTR_MEDIA_ID)
        stream_url = call.data.get(ATTR_STREAM_URL)

        # Get configured default method from entry options
        entry = hass.config_entries.async_get_entry(entry_id)
        configured_method = DEFAULT_HANDOVER_METHOD
        if entry:
            configured_method = entry.options.get(
                CONF_HANDOVER_METHOD, DEFAULT_HANDOVER_METHOD
            )

        # Use service call method if provided, otherwise use configured default
        method = call.data.get(ATTR_METHOD) or configured_method

        _LOGGER.info(
            "Handover to Apple TV: device=%s, media=%s, method=%s",
            device_id,
            media_id,
            method,
        )

        # Track media info for updating coordinator after handover
        media_info: dict = {}

        # Get stream URL if not provided
        if not stream_url:
            if not media_id:
                # Try to get from current watching
                if coordinator.data is None:
                    raise ServiceValidationError(
                        "Coordinator data not available",
                        translation_domain=DOMAIN,
                        translation_key="no_data_available",
                    )
                current = coordinator.data.get("current_watching")
                if not current:
                    raise ServiceValidationError(
                        "No media_id provided and nothing currently watching",
                        translation_domain=DOMAIN,
                        translation_key="no_media_for_handover",
                    )
                media_id = current.get("imdb_id")
                media_type = current.get("type", "movie")
                season = current.get("season")
                episode = current.get("episode")
                # Copy existing media info
                media_info = {
                    "title": current.get("title"),
                    "type": media_type,
                    "imdb_id": media_id,
                    "poster": current.get("poster"),
                    "year": current.get("year"),
                    "season": season,
                    "episode": episode,
                    "episode_title": current.get("episode_title"),
                    "progress": current.get("progress", 0),
                    "duration": current.get("duration", 0),
                    "progress_percent": current.get("progress_percent", 0),
                    "time_offset": current.get("time_offset", 0),
                }
            else:
                media_type = "movie"  # Default assumption
                season = None
                episode = None
                media_info = {
                    "imdb_id": media_id,
                    "type": media_type,
                }

            try:
                streams = await client.async_get_streams(
                    media_id=media_id,
                    media_type=media_type,
                    season=season,
                    episode=episode,
                )
                if streams:
                    stream_url = streams[0].get("url")
            except StremioConnectionError as err:
                raise HomeAssistantError(f"Failed to get stream URL: {err}") from err
        else:
            # Stream URL was provided directly, build minimal media info
            media_info = {
                "imdb_id": media_id,
                "type": "movie",  # Default assumption
            }

        if not stream_url:
            raise ServiceValidationError(
                "Could not determine stream URL",
                translation_domain=DOMAIN,
                translation_key="no_stream_url",
            )

        # Get current watching title for display
        title = media_info.get("title")
        if not title and coordinator.data:
            current = coordinator.data.get("current_watching")
            if current:
                title = current.get("title")
                # Update media_info with title if we found it
                if title:
                    media_info["title"] = title

        # Get stored Apple TV credentials from config entry options
        entry = hass.config_entries.async_get_entry(entry_id)
        credentials = None
        device_identifier = None
        if entry:
            credentials = entry.options.get(CONF_APPLE_TV_CREDENTIALS)
            device_identifier = entry.options.get(CONF_APPLE_TV_IDENTIFIER)

        # Use HandoverManager for proper handover with credentials
        handover_manager = HandoverManager(
            hass,
            credentials=credentials,
            device_identifier=device_identifier,
        )

        try:
            result = await handover_manager.handover(
                device_identifier=device_id,
                stream_url=stream_url,
                method=method,
                title=title,
            )

            _LOGGER.info("Handover result: %s", result)

            # Update the current media on the Stremio device coordinator
            coordinator.set_current_media(media_info, stream_url)

        except HandoverError as err:
            raise HomeAssistantError(f"Handover failed: {err}") from err

        # Fire event
        hass.bus.async_fire(
            EVENT_PLAYBACK_STARTED,
            {
                "device_id": device_id,
                "media_id": media_id,
                "stream_url": stream_url,
                "method": method,
            },
        )

        # Schedule a refresh after a short delay to allow Stremio's backend to sync
        # The Stremio API is event-driven but not real-time, so we poll after playback starts
        async def _delayed_refresh():
            """Refresh coordinator data after playback has started."""
            try:
                await asyncio.sleep(10)  # Wait 10 seconds for Stremio backend to sync
                _LOGGER.debug(
                    "Triggering refresh after handover to update continue watching list"
                )
                await coordinator.async_request_refresh()
            except asyncio.CancelledError:
                # Task was cancelled during shutdown, this is expected
                _LOGGER.debug("Delayed refresh cancelled during shutdown")
            except Exception as err:
                _LOGGER.warning("Error during delayed refresh after handover: %s", err)

        hass.async_create_task(_delayed_refresh(), eager_start=True)

    async def handle_browse_catalog(call: ServiceCall) -> ServiceResponse:
        """Handle browse_catalog service call.

        Browse the Stremio catalog for popular or new movies/series, optionally filtered by genre.
        Returns a list of catalog items with metadata.
        """
        _, client, _ = _get_entry_data(hass)

        media_type = call.data.get(ATTR_MEDIA_TYPE, "movie")
        catalog_type = call.data.get(ATTR_CATALOG_TYPE, "popular")
        genre = call.data.get(ATTR_GENRE)
        skip = call.data.get(ATTR_SKIP, 0)
        limit = call.data.get(ATTR_LIMIT, 50)

        _LOGGER.debug(
            "Browsing catalog: type=%s, catalog=%s, genre=%s, skip=%d, limit=%d",
            media_type,
            catalog_type,
            genre,
            skip,
            limit,
        )

        try:
            # Fetch catalog based on media type and catalog type
            # Note: Currently only "popular" is fully implemented
            # "new" and "genre" catalog types can be added when API supports them
            if media_type == "movie":
                catalog_items = await client.async_get_popular_movies(
                    genre=genre, skip=skip, limit=limit
                )
            else:  # series
                catalog_items = await client.async_get_popular_series(
                    genre=genre, skip=skip, limit=limit
                )

            return {
                "items": catalog_items,
                "count": len(catalog_items),
                "media_type": media_type,
                "catalog_type": catalog_type,
                "genre": genre,
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to browse catalog: {err}") from err

    async def handle_get_upcoming_episodes(call: ServiceCall) -> ServiceResponse:
        """Handle get_upcoming_episodes service call.

        Get air dates for upcoming episodes of series in the user's library.
        Returns a list of upcoming episodes sorted by air date.
        """
        _, client, _ = _get_entry_data(hass)

        days_ahead = call.data.get(ATTR_DAYS_AHEAD, 7)

        _LOGGER.debug("Getting upcoming episodes for next %d days", days_ahead)

        try:
            upcoming = await client.async_get_upcoming_episodes(days_ahead=days_ahead)

            return {
                "episodes": upcoming,
                "count": len(upcoming),
                "days_ahead": days_ahead,
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to get upcoming episodes: {err}") from err

    async def handle_get_recommendations(call: ServiceCall) -> ServiceResponse:
        """Handle get_recommendations service call.

        Get content recommendations based on the user's library.
        Analyzes library genres and preferences to suggest new content.
        """
        _, client, _ = _get_entry_data(hass)

        media_type = call.data.get(ATTR_MEDIA_TYPE)
        limit = call.data.get(ATTR_LIMIT, 20)

        _LOGGER.debug("Getting recommendations: type=%s, limit=%d", media_type, limit)

        try:
            recommendations = await client.async_get_recommendations(
                media_type=media_type,
                limit=limit,
            )

            return {
                "recommendations": recommendations,
                "count": len(recommendations),
                "media_type": media_type,
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to get recommendations: {err}") from err

    async def handle_get_similar_content(call: ServiceCall) -> ServiceResponse:
        """Handle get_similar_content service call.

        Get similar movies or shows based on a specific media item.
        Uses genre and metadata matching to find related content.
        """
        _, client, _ = _get_entry_data(hass)

        media_id = call.data[ATTR_MEDIA_ID]
        limit = call.data.get(ATTR_LIMIT, 10)

        _LOGGER.debug("Getting similar content for %s, limit=%d", media_id, limit)

        try:
            similar = await client.async_get_similar_content(
                media_id=media_id,
                limit=limit,
            )

            return {
                "similar": similar,
                "count": len(similar),
                "source_media_id": media_id,
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to get similar content: {err}") from err

    async def handle_get_addons(call: ServiceCall) -> ServiceResponse:
        """Handle get_addons service call.

        Retrieves the user's configured Stremio addons with their details
        including manifest information, transport URLs, and capabilities.
        """
        _, client, _ = _get_entry_data(hass)

        _LOGGER.debug("Getting configured addons")

        try:
            addons = await client.async_get_addon_collection()

            # Process addons to extract useful information
            processed_addons = []
            for addon in addons:
                manifest = addon.get("manifest", {})
                transport_url = addon.get("transportUrl", "")

                # Extract resources (capabilities)
                resources = manifest.get("resources", [])
                capabilities = []
                for resource in resources:
                    if isinstance(resource, str):
                        capabilities.append(resource)
                    elif isinstance(resource, dict):
                        capabilities.append(resource.get("name", ""))

                # Extract types supported
                types = manifest.get("types", [])

                # Extract catalogs
                catalogs = manifest.get("catalogs", [])
                catalog_info = []
                for catalog in catalogs:
                    if isinstance(catalog, dict):
                        catalog_info.append(
                            {
                                "type": catalog.get("type"),
                                "id": catalog.get("id"),
                                "name": catalog.get("name"),
                            }
                        )

                processed_addon = {
                    "id": manifest.get("id", ""),
                    "name": manifest.get("name", "Unknown"),
                    "version": manifest.get("version", ""),
                    "description": manifest.get("description", ""),
                    "logo": manifest.get("logo", ""),
                    "background": manifest.get("background", ""),
                    "transport_url": transport_url,
                    "types": types,
                    "resources": capabilities,
                    "catalogs": catalog_info,
                    "id_prefixes": manifest.get("idPrefixes", []),
                    "behavior_hints": manifest.get("behaviorHints", {}),
                }
                processed_addons.append(processed_addon)

            _LOGGER.info("Retrieved %d configured addons", len(processed_addons))

            return {
                "addons": processed_addons,
                "count": len(processed_addons),
            }

        except StremioConnectionError as err:
            raise HomeAssistantError(f"Failed to get addons: {err}") from err

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH_LIBRARY,
        handle_search_library,
        schema=SEARCH_LIBRARY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_STREAMS,
        handle_get_streams,
        schema=GET_STREAMS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SERIES_METADATA,
        handle_get_series_metadata,
        schema=GET_SERIES_METADATA_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TO_LIBRARY,
        handle_add_to_library,
        schema=ADD_TO_LIBRARY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_FROM_LIBRARY,
        handle_remove_from_library,
        schema=REMOVE_FROM_LIBRARY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_LIBRARY,
        handle_refresh_library,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_HANDOVER_TO_APPLE_TV,
        handle_handover_to_apple_tv,
        schema=HANDOVER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_BROWSE_CATALOG,
        handle_browse_catalog,
        schema=BROWSE_CATALOG_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_UPCOMING_EPISODES,
        handle_get_upcoming_episodes,
        schema=GET_UPCOMING_EPISODES_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_RECOMMENDATIONS,
        handle_get_recommendations,
        schema=GET_RECOMMENDATIONS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SIMILAR_CONTENT,
        handle_get_similar_content,
        schema=GET_SIMILAR_CONTENT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_ADDONS,
        handle_get_addons,
        schema=GET_ADDONS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Stremio services.

    Args:
        hass: Home Assistant instance
    """
    hass.services.async_remove(DOMAIN, SERVICE_SEARCH_LIBRARY)
    hass.services.async_remove(DOMAIN, SERVICE_GET_STREAMS)
    hass.services.async_remove(DOMAIN, SERVICE_GET_SERIES_METADATA)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_TO_LIBRARY)
    hass.services.async_remove(DOMAIN, SERVICE_REMOVE_FROM_LIBRARY)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_LIBRARY)
    hass.services.async_remove(DOMAIN, SERVICE_HANDOVER_TO_APPLE_TV)
    hass.services.async_remove(DOMAIN, SERVICE_BROWSE_CATALOG)
    hass.services.async_remove(DOMAIN, SERVICE_GET_UPCOMING_EPISODES)
    hass.services.async_remove(DOMAIN, SERVICE_GET_RECOMMENDATIONS)
    hass.services.async_remove(DOMAIN, SERVICE_GET_SIMILAR_CONTENT)
    hass.services.async_remove(DOMAIN, SERVICE_GET_ADDONS)
