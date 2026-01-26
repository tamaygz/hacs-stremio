"""Stremio Media Source implementation for Home Assistant.

This module provides media browser integration for browsing and playing
Stremio library content through Home Assistant's Media Browser panel.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import BrowseError, MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant

from .const import CONF_SHOW_COPY_URL, DEFAULT_SHOW_COPY_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Media source identifier
MEDIA_SOURCE_ID = "stremio"

# Browse hierarchy identifiers
ROOT_IDENTIFIER = "root"
LIBRARY_IDENTIFIER = "library"
CONTINUE_WATCHING_IDENTIFIER = "continue_watching"
MOVIES_IDENTIFIER = "movies"
SERIES_IDENTIFIER = "series"
SEARCH_IDENTIFIER = "search"
STREAMS_IDENTIFIER = "streams"
CATALOGS_IDENTIFIER = "catalogs"
POPULAR_MOVIES_IDENTIFIER = "popular_movies"
POPULAR_SERIES_IDENTIFIER = "popular_series"
NEW_MOVIES_IDENTIFIER = "new_movies"
NEW_SERIES_IDENTIFIER = "new_series"
MOVIE_GENRES_IDENTIFIER = "movie_genres"
SERIES_GENRES_IDENTIFIER = "series_genres"
RECOMMENDED_IDENTIFIER = "recommended"
SIMILAR_IDENTIFIER = "similar"


async def async_get_media_source(hass: HomeAssistant) -> StremioMediaSource:
    """Set up Stremio media source."""
    return StremioMediaSource(hass)


class StremioMediaSource(MediaSource):
    """Provide Stremio library as media source for browsing."""

    name = "Stremio"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize Stremio media source."""
        super().__init__(MEDIA_SOURCE_ID)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a media item to a playable URL.

        Args:
            item: The MediaSourceItem containing the media identifier

        Returns:
            PlayMedia object with URL and mime type

        Raises:
            Unresolvable: If the media cannot be resolved
        """
        identifier = item.identifier
        _LOGGER.debug("Resolving media for identifier: %s", identifier)

        if not identifier:
            raise Unresolvable("No media identifier provided")

        # Handle copyurl: identifiers - these fire an event, not play media
        if identifier.startswith("copyurl:"):
            stream_url = identifier[8:]  # Remove "copyurl:" prefix
            _LOGGER.info("Stream URL copied: %s", stream_url)
            self.hass.bus.async_fire(
                "stremio_stream_url",
                {"url": stream_url, "action": "copy"},
            )
            # Return the URL as playable so it can be handled
            mime_type = self._get_mime_type(stream_url, {})
            return PlayMedia(url=stream_url, mime_type=mime_type)

        # Get coordinator from hass.data
        entries = self.hass.data.get(DOMAIN, {})
        if not entries:
            raise Unresolvable("Stremio integration not configured")

        # Get the first available coordinator
        coordinator = None
        for entry_id, entry_data in entries.items():
            if "coordinator" in entry_data:
                coordinator = entry_data["coordinator"]
                break

        if coordinator is None:
            raise Unresolvable("Stremio coordinator not available")

        # Extract stream index if present (format: type/id#stream_index or type/id/season/episode#stream_index)
        stream_index: int | None = None
        if "#" in identifier:
            identifier, stream_index_str = identifier.rsplit("#", 1)
            try:
                stream_index = int(stream_index_str)
            except ValueError:
                _LOGGER.warning("Invalid stream index: %s", stream_index_str)
                stream_index = 0

        # Parse identifier format: type/id or type/id/season/episode
        parts = identifier.split("/")
        if len(parts) < 2:
            raise Unresolvable(f"Invalid media identifier format: {identifier}")

        media_type = parts[0]
        media_id = parts[1]
        season = parts[2] if len(parts) > 2 else None
        episode = parts[3] if len(parts) > 3 else None

        try:
            # Get stream URL from Stremio API
            client = coordinator.client
            streams = await client.async_get_streams(
                media_id=media_id,
                media_type=media_type,
                season=int(season) if season else None,
                episode=int(episode) if episode else None,
            )

            if not streams:
                raise Unresolvable(f"No streams found for {identifier}")

            # Get the requested stream by index, or first one if not specified
            if stream_index is not None and 0 <= stream_index < len(streams):
                selected_stream = streams[stream_index]
            else:
                selected_stream = streams[0]

            stream_url = selected_stream.get("url") or selected_stream.get(
                "externalUrl"
            )

            if not stream_url:
                raise Unresolvable("No playable stream URL available")

            # Determine MIME type
            mime_type = self._get_mime_type(stream_url, selected_stream)

            return PlayMedia(url=stream_url, mime_type=mime_type)

        except Exception as err:
            _LOGGER.error("Error resolving media %s: %s", identifier, err)
            raise Unresolvable(f"Failed to resolve media: {err}") from err

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Browse Stremio media library.

        Args:
            item: The MediaSourceItem representing the current browse location

        Returns:
            BrowseMediaSource with browsable content
        """
        identifier = item.identifier or ROOT_IDENTIFIER
        _LOGGER.debug("Browsing media with identifier: %s", identifier)

        try:
            # Handle root level browsing
            if identifier == ROOT_IDENTIFIER or not identifier:
                return self._build_root_browse()

            # Handle copyurl: identifiers - fire event with URL for clipboard
            if identifier.startswith("copyurl:"):
                stream_url = identifier[8:]  # Remove "copyurl:" prefix
                _LOGGER.info("Stream URL requested for copy: %s", stream_url)
                # Fire an event with the URL so automations/frontend can handle it
                self.hass.bus.async_fire(
                    "stremio_stream_url",
                    {"url": stream_url, "action": "copy"},
                )
                # Return a simple browse result showing the URL was copied
                return BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=identifier,
                    media_class=MediaClass.URL,
                    media_content_type="",
                    title=f"URL: {stream_url}",
                    can_play=False,
                    can_expand=False,
                    children=[],
                )

            # Handle different browse sections
            if identifier == LIBRARY_IDENTIFIER:
                return await self._build_library_browse()
            if identifier == CONTINUE_WATCHING_IDENTIFIER:
                return await self._build_continue_watching_browse()
            if identifier == MOVIES_IDENTIFIER:
                return await self._build_movies_browse()
            if identifier == SERIES_IDENTIFIER:
                return await self._build_series_browse()
            if identifier == CATALOGS_IDENTIFIER:
                return self._build_catalogs_browse()
            if identifier == POPULAR_MOVIES_IDENTIFIER:
                return await self._build_popular_movies_browse()
            if identifier == POPULAR_SERIES_IDENTIFIER:
                return await self._build_popular_series_browse()
            if identifier == NEW_MOVIES_IDENTIFIER:
                return await self._build_new_movies_browse()
            if identifier == NEW_SERIES_IDENTIFIER:
                return await self._build_new_series_browse()
            if identifier == MOVIE_GENRES_IDENTIFIER:
                return self._build_movie_genres_browse()
            if identifier == SERIES_GENRES_IDENTIFIER:
                return self._build_series_genres_browse()
            if identifier == RECOMMENDED_IDENTIFIER:
                return await self._build_recommended_browse()

            # Handle similar content browsing (similar/type/imdb_id)
            if identifier.startswith(f"{SIMILAR_IDENTIFIER}/"):
                return await self._build_similar_browse(identifier)

            # Handle genre browsing with format: movie_genres/Genre or series_genres/Genre
            if identifier.startswith(f"{MOVIE_GENRES_IDENTIFIER}/"):
                return await self._build_genre_content_browse(identifier, "movie")
            if identifier.startswith(f"{SERIES_GENRES_IDENTIFIER}/"):
                return await self._build_genre_content_browse(identifier, "series")

            # Handle individual series items (series/imdb_id or series/imdb_id/season)
            if identifier.startswith(f"{SERIES_IDENTIFIER}/"):
                return await self._build_series_detail_browse(identifier)

            # Handle individual movie items (movie/imdb_id)
            if identifier.startswith("movie/"):
                return await self._build_movie_detail_browse(identifier)

            # Handle streams browsing (streams/type/imdb_id or streams/series/imdb_id/season/episode)
            if identifier.startswith(f"{STREAMS_IDENTIFIER}/"):
                return await self._build_streams_browse(identifier)

            # Unknown identifier - return error state instead of raising
            _LOGGER.warning("Unknown media identifier: %s", identifier)
            return self._build_error_browse(
                identifier, "Unknown", f"Unknown path: {identifier}"
            )

        except BrowseError:
            # Re-raise BrowseError as-is (these are intentional)
            raise
        except Exception as err:
            # Catch unexpected errors and return error state instead of crashing
            _LOGGER.exception("Error browsing media identifier %s: %s", identifier, err)
            return self._build_error_browse(
                identifier, "Error", f"Failed to load: {err}"
            )

    def _build_root_browse(self) -> BrowseMediaSource:
        """Build root level browse menu."""
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=ROOT_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title="Stremio",
            can_play=False,
            can_expand=True,
            thumbnail="https://www.stremio.com/website/stremio-logo-small.png",
            children=[
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=CONTINUE_WATCHING_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title="Continue Watching",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=RECOMMENDED_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title="⭐ Recommended For You",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=CATALOGS_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title="Browse Catalogs",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=LIBRARY_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title="My Library",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=MOVIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MOVIE,
                    title="My Movies",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=SERIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title="My TV Series",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
            ],
        )

    async def _build_library_browse(self) -> BrowseMediaSource:
        """Build library browse view."""
        coordinator = self._get_coordinator()
        if not coordinator or not coordinator.data:
            return self._build_empty_browse(LIBRARY_IDENTIFIER, "Library")

        library_items = coordinator.data.get("library", [])

        children = []
        for item in library_items[:100]:  # Limit to 100 items
            child = self._build_media_item(item)
            if child:
                children.append(child)

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=LIBRARY_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title="Library",
            can_play=False,
            can_expand=True,
            children=children,
        )

    async def _build_continue_watching_browse(self) -> BrowseMediaSource:
        """Build continue watching browse view."""
        coordinator = self._get_coordinator()
        if not coordinator or not coordinator.data:
            return self._build_empty_browse(
                CONTINUE_WATCHING_IDENTIFIER, "Continue Watching"
            )

        continue_items = coordinator.data.get("continue_watching", [])

        children = []
        for item in continue_items[:50]:  # Limit to 50 items
            child = self._build_media_item(item, show_progress=True)
            if child:
                children.append(child)

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=CONTINUE_WATCHING_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title="Continue Watching",
            can_play=False,
            can_expand=True,
            children=children,
        )

    async def _build_movies_browse(self) -> BrowseMediaSource:
        """Build movies browse view."""
        coordinator = self._get_coordinator()
        if not coordinator or not coordinator.data:
            return self._build_empty_browse(MOVIES_IDENTIFIER, "Movies")

        library_items = coordinator.data.get("library", [])
        movie_items = [item for item in library_items if item.get("type") == "movie"]

        children = []
        for item in movie_items[:100]:  # Limit to 100 items
            child = self._build_media_item(item)
            if child:
                children.append(child)

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=MOVIES_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MOVIE,
            title="Movies",
            can_play=False,
            can_expand=True,
            children=children,
        )

    async def _build_series_browse(self) -> BrowseMediaSource:
        """Build TV series browse view."""
        coordinator = self._get_coordinator()
        if not coordinator or not coordinator.data:
            return self._build_empty_browse(SERIES_IDENTIFIER, "TV Series")

        library_items = coordinator.data.get("library", [])
        series_items = [item for item in library_items if item.get("type") == "series"]

        children = []
        for item in series_items[:100]:  # Limit to 100 items
            child = self._build_series_item(item)
            if child:
                children.append(child)

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=SERIES_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.TVSHOW,
            title="TV Series",
            can_play=False,
            can_expand=True,
            children=children,
        )

    async def _build_movie_detail_browse(self, identifier: str) -> BrowseMediaSource:
        """Build movie detail view showing streams as children.

        Args:
            identifier: Format is movie/imdb_id

        Returns:
            BrowseMediaSource for the movie with streams as children
        """
        parts = identifier.split("/")
        media_id = parts[1] if len(parts) > 1 else None

        if not media_id:
            _LOGGER.warning("Invalid movie identifier: %s", identifier)
            return self._build_error_browse(
                identifier, "Invalid Movie", "Movie ID not found in path"
            )

        coordinator = self._get_coordinator()
        if not coordinator:
            _LOGGER.warning("Coordinator not available for movie detail browse")
            return self._build_error_browse(
                identifier, "Unavailable", "Stremio integration not ready"
            )

        # Find movie in library
        library_items = coordinator.data.get("library", []) if coordinator.data else []
        movie_item = next(
            (
                item
                for item in library_items
                if (item.get("imdb_id") == media_id or item.get("id") == media_id)
                and item.get("type") == "movie"
            ),
            None,
        )

        title = "Unknown Movie"
        poster = None
        year = None

        if movie_item:
            title = movie_item.get("title") or movie_item.get("name") or "Unknown Movie"
            poster = movie_item.get("poster") or movie_item.get("thumbnail")
            year = movie_item.get("year")
        else:
            title = f"Movie ({media_id})"

        if year:
            title = f"{title} ({year})"

        # Create children: streams and similar
        streams_identifier = f"{STREAMS_IDENTIFIER}/movie/{media_id}"
        similar_identifier = f"{SIMILAR_IDENTIFIER}/movie/{media_id}"
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=streams_identifier,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.VIDEO,
                title="▶️ Get Streams",
                can_play=False,
                can_expand=True,
                thumbnail=poster,
            ),
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=similar_identifier,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.VIDEO,
                title="🎬 Show Similar",
                can_play=False,
                can_expand=True,
                thumbnail=poster,
            ),
        ]

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.MOVIE,
            media_content_type=MediaType.MOVIE,
            title=title,
            can_play=False,
            can_expand=True,
            thumbnail=poster,
            children=children,
        )

    async def _build_series_detail_browse(self, identifier: str) -> BrowseMediaSource:
        """Build series detail view with seasons and episodes.

        Args:
            identifier: Format is series/imdb_id, series/imdb_id/season,
                       or series/imdb_id/season/episode
        """
        parts = identifier.split("/")
        media_id = parts[1] if len(parts) > 1 else None
        season = int(parts[2]) if len(parts) > 2 else None
        episode = int(parts[3]) if len(parts) > 3 else None

        if not media_id:
            _LOGGER.warning("Invalid series identifier: %s", identifier)
            return self._build_error_browse(
                identifier, "Invalid Series", "Series ID not found in path"
            )

        coordinator = self._get_coordinator()
        if not coordinator:
            _LOGGER.warning("Coordinator not available for series detail browse")
            return self._build_error_browse(
                identifier, "Unavailable", "Stremio integration not ready"
            )

        # Try to find series in library for basic info
        library_items = coordinator.data.get("library", []) if coordinator.data else []
        series_item = next(
            (
                item
                for item in library_items
                if item.get("imdb_id") == media_id or item.get("id") == media_id
            ),
            None,
        )

        # Get title and poster from library item if available
        title = None
        poster = None
        if series_item:
            title = series_item.get("title") or series_item.get("name")
            poster = series_item.get("poster")

        # Fetch detailed metadata from Cinemeta to get accurate season/episode info
        # This works for both library items and catalog items
        client = coordinator.client
        metadata = None
        try:
            metadata = await client.async_get_series_metadata(media_id)
        except Exception as err:
            _LOGGER.warning(
                "Failed to fetch series metadata for %s: %s", media_id, err
            )

        if not metadata:
            # If we can't get metadata, show an error state instead of crashing
            _LOGGER.warning("Could not fetch series metadata for %s", media_id)
            return self._build_error_browse(
                identifier,
                title or f"Series ({media_id})",
                "Failed to load series metadata. Please try again.",
            )

        # Use metadata for title and poster if not from library
        if not title:
            title = metadata.get("name") or metadata.get("title") or "Unknown Series"
        if not poster:
            poster = metadata.get("poster")

        seasons = metadata.get("seasons", [])

        # If no season specified, show season list
        if season is None:
            children = []
            if seasons:
                for season_data in seasons:
                    season_num = season_data.get("number", 1)
                    episode_count = len(season_data.get("episodes", []))
                    season_id = f"{SERIES_IDENTIFIER}/{media_id}/{season_num}"
                    season_title = season_data.get("title", f"Season {season_num}")
                    if episode_count > 0:
                        season_title = f"{season_title} ({episode_count} episodes)"
                    children.append(
                        BrowseMediaSource(
                            domain=DOMAIN,
                            identifier=season_id,
                            media_class=MediaClass.SEASON,
                            media_content_type=MediaType.SEASON,
                            title=season_title,
                            can_play=False,
                            can_expand=True,
                            thumbnail=poster,
                        )
                    )
            else:
                # No season data available, show message
                _LOGGER.warning("No season data available for series %s", media_id)
                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"{SERIES_IDENTIFIER}/{media_id}/1",
                        media_class=MediaClass.SEASON,
                        media_content_type=MediaType.SEASON,
                        title="Season 1 (metadata unavailable)",
                        can_play=False,
                        can_expand=True,
                        thumbnail=poster,
                    )
                )

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=identifier,
                media_class=MediaClass.TV_SHOW,
                media_content_type=MediaType.TVSHOW,
                title=title,
                can_play=False,
                can_expand=True,
                thumbnail=poster,
                children=children,
            )

        # Find the season data by number
        current_season: dict[str, Any] = next(
            (s for s in seasons if s.get("number") == season),
            {},
        )

        # If episode specified, show episode detail with streams
        if episode is not None:
            episode_list: list[dict[str, Any]] = current_season.get("episodes", [])
            ep_data: dict[str, Any] = next(
                (e for e in episode_list if e.get("number") == episode),
                {},
            )
            ep_title = ep_data.get("title") or f"Episode {episode}"
            ep_thumbnail = ep_data.get("thumbnail") or poster

            # Create children: streams and similar (similar is based on the series)
            streams_identifier = (
                f"{STREAMS_IDENTIFIER}/series/{media_id}/{season}/{episode}"
            )
            similar_identifier = f"{SIMILAR_IDENTIFIER}/series/{media_id}"
            children = [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=streams_identifier,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.VIDEO,
                    title="▶️ Get Streams",
                    can_play=False,
                    can_expand=True,
                    thumbnail=ep_thumbnail,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=similar_identifier,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title="📺 Show Similar Series",
                    can_play=False,
                    can_expand=True,
                    thumbnail=poster,
                ),
            ]

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=identifier,
                media_class=MediaClass.EPISODE,
                media_content_type=MediaType.EPISODE,
                title=f"{title} - S{season:02d}E{episode:02d}: {ep_title}",
                can_play=False,
                can_expand=True,
                thumbnail=ep_thumbnail,
                children=children,
            )

        # Show episodes for specific season
        episodes = []
        ep_list: list[dict[str, Any]] = current_season.get("episodes", [])

        for ep_data in ep_list:
            ep_num = ep_data.get("number", 0)
            ep_title = ep_data.get("title") or f"Episode {ep_num}"
            ep_identifier = f"{SERIES_IDENTIFIER}/{media_id}/{season}/{ep_num}"
            ep_thumbnail = ep_data.get("thumbnail") or poster

            episodes.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=ep_identifier,
                    media_class=MediaClass.EPISODE,
                    media_content_type=MediaType.EPISODE,
                    title=f"E{ep_num}: {ep_title}",
                    can_play=False,
                    can_expand=True,
                    thumbnail=ep_thumbnail,
                )
            )

        # If no episodes in data, show a message
        if not episodes:
            _LOGGER.warning(
                "No episode data available for series %s season %s", media_id, season
            )
            episodes.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{SERIES_IDENTIFIER}/{media_id}/{season}/1",
                    media_class=MediaClass.EPISODE,
                    media_content_type=MediaType.EPISODE,
                    title="Episode 1 (metadata unavailable)",
                    can_play=False,
                    can_expand=True,
                    thumbnail=poster,
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.SEASON,
            media_content_type=MediaType.SEASON,
            title=f"{title} - Season {season}",
            can_play=False,
            can_expand=True,
            thumbnail=poster,
            children=episodes,
        )

    def _build_media_item(
        self, item: dict[str, Any], show_progress: bool = False
    ) -> BrowseMediaSource | None:
        """Build a BrowseMediaSource for a library item.

        Args:
            item: Library item dictionary
            show_progress: Whether to show progress in title

        Returns:
            BrowseMediaSource or None if item is invalid
        """
        title = item.get("title") or item.get("name")
        if not title:
            return None

        media_type = item.get("type", "movie")
        media_id = item.get("imdb_id") or item.get("id")

        if not media_id:
            return None

        # Format identifier
        identifier = f"{media_type}/{media_id}"

        # Get poster/thumbnail
        poster = item.get("poster") or item.get("thumbnail")

        # Add progress to title if requested
        if show_progress:
            progress = item.get("progress_percent", 0)
            if progress > 0:
                title = f"{title} ({progress:.0f}%)"

        # Determine media class - all items are expandable to show streams
        if media_type == "series":
            media_class = MediaClass.TV_SHOW
            content_type = MediaType.TVSHOW
        else:
            media_class = MediaClass.MOVIE
            content_type = MediaType.MOVIE

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=media_class,
            media_content_type=content_type,
            title=title,
            can_play=False,  # Need to drill down to streams
            can_expand=True,
            thumbnail=poster,
        )

    def _build_series_item(self, item: dict[str, Any]) -> BrowseMediaSource | None:
        """Build a BrowseMediaSource for a TV series.

        Args:
            item: Series item dictionary

        Returns:
            BrowseMediaSource or None if item is invalid
        """
        title = item.get("title") or item.get("name")
        if not title:
            return None

        media_id = item.get("imdb_id") or item.get("id")
        if not media_id:
            return None

        # Series identifier for drilling down
        identifier = f"{SERIES_IDENTIFIER}/{media_id}"
        poster = item.get("poster") or item.get("thumbnail")

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.TV_SHOW,
            media_content_type=MediaType.TVSHOW,
            title=title,
            can_play=False,
            can_expand=True,
            thumbnail=poster,
        )

    def _get_stream_metadata(self, stream: dict[str, Any]) -> dict[str, str | None]:
        """Get parsed metadata from stream, using pre-parsed data if available.

        Args:
            stream: Stream dictionary from addon

        Returns:
            Dictionary with extracted metadata fields
        """
        # Use pre-parsed metadata from stremio_client if available
        if "parsed_metadata" in stream:
            return stream["parsed_metadata"]

        # Fallback: parse on-demand using the shared utility
        from .stremio_client import StremioClient

        return StremioClient.parse_stream_metadata(stream)

    def _format_stream_label(
        self, stream: dict[str, Any], index: int
    ) -> str:
        """Format stream information into a single-line label for Media Browser.

        Home Assistant's Media Browser doesn't support multiline titles,
        so we format with visual separators for clarity.

        Args:
            stream: Stream dictionary from addon
            index: Stream index for fallback naming

        Returns:
            Formatted single-line label string
        """
        # Get the stream name/title
        stream_name = (
            stream.get("name") or stream.get("title") or f"Stream {index + 1}"
        )

        # Get metadata (pre-parsed or parse on-demand)
        meta = self._get_stream_metadata(stream)

        # Build compact metadata chips for single-line display
        meta_parts = []
        if meta["addon"]:
            meta_parts.append(meta["addon"])
        if stream.get("size") or meta["size"]:
            size = stream.get("size") or meta["size"]
            meta_parts.append(size)
        if meta["seeders"]:
            meta_parts.append(f"👤{meta['seeders']}")
        if meta["codec"]:
            meta_parts.append(meta["codec"])
        if meta["hdr"]:
            meta_parts.append(meta["hdr"])
        if meta["audio"]:
            meta_parts.append(meta["audio"])

        # Format: "Stream Name  ⟨ addon · size · seeders · codec ⟩"
        if meta_parts:
            metadata_str = " · ".join(meta_parts)
            return f"{stream_name}  ⟨ {metadata_str} ⟩"
        return stream_name

    async def _build_streams_browse(self, identifier: str) -> BrowseMediaSource:
        """Build streams browse view for a movie or episode.

        Args:
            identifier: Format is streams/movie/imdb_id or
                       streams/series/imdb_id/season/episode

        Returns:
            BrowseMediaSource with available streams as children
        """
        parts = identifier.split("/")
        # streams/movie/imdb_id or streams/series/imdb_id/season/episode
        media_type = parts[1] if len(parts) > 1 else None
        media_id = parts[2] if len(parts) > 2 else None
        season = int(parts[3]) if len(parts) > 3 else None
        episode = int(parts[4]) if len(parts) > 4 else None

        if not media_type or not media_id:
            _LOGGER.warning("Invalid streams identifier: %s", identifier)
            return self._build_error_browse(
                identifier, "Invalid Request", "Missing media type or ID"
            )

        coordinator = self._get_coordinator()
        if not coordinator:
            _LOGGER.warning("Coordinator not available for streams browse")
            return self._build_error_browse(
                identifier, "Unavailable", "Stremio integration not ready"
            )

        # Build title based on content type
        title = "Available Streams"
        poster = None

        # Try to find item in library for metadata
        library_items = coordinator.data.get("library", []) if coordinator.data else []
        library_item = next(
            (
                item
                for item in library_items
                if item.get("imdb_id") == media_id or item.get("id") == media_id
            ),
            None,
        )

        if library_item:
            item_title = library_item.get("title") or library_item.get("name")
            poster = library_item.get("poster")
            if media_type == "series" and season and episode:
                title = f"Streams for {item_title} S{season:02d}E{episode:02d}"
            else:
                title = f"Streams for {item_title}"

        # Fetch available streams from the API
        streams = []
        try:
            client = coordinator.client
            streams = await client.async_get_streams(
                media_id=media_id,
                media_type=media_type,
                season=season,
                episode=episode,
            )
        except Exception as err:
            _LOGGER.error("Failed to fetch streams: %s", err)
            # Don't return error here, just show empty streams list

        # Build stream children
        children = []
        for idx, stream in enumerate(streams):
            # Get formatted stream label with metadata
            label = self._format_stream_label(stream, idx)

            # Get the stream URL for display
            stream_url = stream.get("url") or stream.get("externalUrl") or ""

            # Create stream identifier for playback
            # Format: type/media_id or type/media_id/season/episode with stream index
            if media_type == "series" and season and episode:
                stream_identifier = f"{media_type}/{media_id}/{season}/{episode}#{idx}"
            else:
                stream_identifier = f"{media_type}/{media_id}#{idx}"

            # Add the main playable stream entry
            # Use TRACK media class to render as list item instead of thumbnail grid
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=stream_identifier,
                    media_class=MediaClass.TRACK,
                    media_content_type=MediaType.VIDEO,
                    title=f"▶️ {label}",
                    can_play=True,
                    can_expand=False,
                    thumbnail=None,  # No thumbnail for list view
                )
            )

            # Add a URL copy entry if URL is available and option is enabled
            if stream_url and self._should_show_copy_url():
                # Truncate URL for display if too long
                display_url = stream_url
                if len(display_url) > 80:
                    display_url = display_url[:77] + "..."

                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"copyurl:{stream_url}",
                        media_class=MediaClass.URL,
                        media_content_type="",
                        title=f"   📋 Copy URL: {display_url}",
                        can_play=False,
                        can_expand=False,
                        thumbnail=None,
                    )
                )

        # If no streams found, show a message
        if not children:
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="",
                    media_class=MediaClass.VIDEO,
                    media_content_type=MediaType.VIDEO,
                    title="No streams available - use addon protocol",
                    can_play=False,
                    can_expand=False,
                    thumbnail=None,
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.VIDEO,
            title=title,
            can_play=False,
            can_expand=True,
            thumbnail=poster,
            children=children,
            children_media_class=MediaClass.TRACK,  # Hint to render children as list
        )

    def _build_catalogs_browse(self) -> BrowseMediaSource:
        """Build catalogs browse menu showing available catalog categories."""
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=CATALOGS_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title="Browse Catalogs",
            can_play=False,
            can_expand=True,
            children=[
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=POPULAR_MOVIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MOVIE,
                    title="🔥 Popular Movies",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=POPULAR_SERIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title="🔥 Popular TV Shows",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=NEW_MOVIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MOVIE,
                    title="🆕 New Movies",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=NEW_SERIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title="🆕 New TV Shows",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=MOVIE_GENRES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MOVIE,
                    title="🎭 Movie Genres",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=SERIES_GENRES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title="🎭 TV Show Genres",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
            ],
        )

    async def _build_popular_movies_browse(self) -> BrowseMediaSource:
        """Build popular movies catalog view."""
        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(POPULAR_MOVIES_IDENTIFIER, "Popular Movies")

        try:
            client = coordinator.client
            catalog_items = await client.async_get_popular_movies(limit=50)

            children = []
            for item in catalog_items:
                child = self._build_catalog_item(item)
                if child:
                    children.append(child)

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=POPULAR_MOVIES_IDENTIFIER,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.MOVIE,
                title="Popular Movies",
                can_play=False,
                can_expand=True,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching popular movies: %s", err)
            return self._build_empty_browse(POPULAR_MOVIES_IDENTIFIER, "Popular Movies")

    async def _build_popular_series_browse(self) -> BrowseMediaSource:
        """Build popular TV series catalog view."""
        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(
                POPULAR_SERIES_IDENTIFIER, "Popular TV Shows"
            )

        try:
            client = coordinator.client
            catalog_items = await client.async_get_popular_series(limit=50)

            children = []
            for item in catalog_items:
                child = self._build_catalog_item(item)
                if child:
                    children.append(child)

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=POPULAR_SERIES_IDENTIFIER,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.TVSHOW,
                title="Popular TV Shows",
                can_play=False,
                can_expand=True,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching popular series: %s", err)
            return self._build_empty_browse(
                POPULAR_SERIES_IDENTIFIER, "Popular TV Shows"
            )

    async def _build_new_movies_browse(self) -> BrowseMediaSource:
        """Build new movies catalog view (same as popular for now)."""
        # Note: Cinemeta doesn't have a specific "new releases" catalog
        # Using popular catalog which tends to include recent releases
        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(NEW_MOVIES_IDENTIFIER, "New Movies")

        try:
            client = coordinator.client
            # Get popular movies which tend to include recent releases
            catalog_items = await client.async_get_popular_movies(limit=50)

            children = []
            for item in catalog_items:
                child = self._build_catalog_item(item)
                if child:
                    children.append(child)

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=NEW_MOVIES_IDENTIFIER,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.MOVIE,
                title="New Movies",
                can_play=False,
                can_expand=True,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching new movies: %s", err)
            return self._build_empty_browse(NEW_MOVIES_IDENTIFIER, "New Movies")

    async def _build_new_series_browse(self) -> BrowseMediaSource:
        """Build new TV series catalog view (same as popular for now)."""
        # Note: Cinemeta doesn't have a specific "new releases" catalog
        # Using popular catalog which tends to include recent series
        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(NEW_SERIES_IDENTIFIER, "New TV Shows")

        try:
            client = coordinator.client
            # Get popular series which tend to include recent releases
            catalog_items = await client.async_get_popular_series(limit=50)

            children = []
            for item in catalog_items:
                child = self._build_catalog_item(item)
                if child:
                    children.append(child)

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=NEW_SERIES_IDENTIFIER,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.TVSHOW,
                title="New TV Shows",
                can_play=False,
                can_expand=True,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching new series: %s", err)
            return self._build_empty_browse(NEW_SERIES_IDENTIFIER, "New TV Shows")

    def _build_movie_genres_browse(self) -> BrowseMediaSource:
        """Build movie genres list view."""
        from .const import CINEMETA_GENRES

        children = []
        for genre in CINEMETA_GENRES:
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{MOVIE_GENRES_IDENTIFIER}/{genre}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MOVIE,
                    title=genre,
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=MOVIE_GENRES_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MOVIE,
            title="Movie Genres",
            can_play=False,
            can_expand=True,
            children=children,
        )

    def _build_series_genres_browse(self) -> BrowseMediaSource:
        """Build TV show genres list view."""
        from .const import CINEMETA_GENRES

        children = []
        for genre in CINEMETA_GENRES:
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{SERIES_GENRES_IDENTIFIER}/{genre}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title=genre,
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=SERIES_GENRES_IDENTIFIER,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.TVSHOW,
            title="TV Show Genres",
            can_play=False,
            can_expand=True,
            children=children,
        )

    async def _build_recommended_browse(self) -> BrowseMediaSource:
        """Build recommended content browse view based on user's library.

        Returns:
            BrowseMediaSource with personalized recommendations
        """
        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(
                RECOMMENDED_IDENTIFIER, "Recommended For You"
            )

        try:
            client = coordinator.client
            # Get recommendations (mix of movies and series based on library)
            recommendations = await client.async_get_recommendations(limit=30)

            children = []
            for item in recommendations:
                child = self._build_catalog_item(item)
                if child:
                    # Add recommendation reason to title if available
                    reason = item.get("recommendation_reason")
                    if reason and child.title:
                        child = BrowseMediaSource(
                            domain=child.domain,
                            identifier=child.identifier,
                            media_class=child.media_class,
                            media_content_type=child.media_content_type,
                            title=f"{child.title}",
                            can_play=child.can_play,
                            can_expand=child.can_expand,
                            thumbnail=child.thumbnail,
                        )
                    children.append(child)

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=RECOMMENDED_IDENTIFIER,
                media_class=MediaClass.DIRECTORY,
                media_content_type="",
                title="⭐ Recommended For You",
                can_play=False,
                can_expand=True,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching recommendations: %s", err)
            return self._build_empty_browse(
                RECOMMENDED_IDENTIFIER, "Recommended For You"
            )

    async def _build_similar_browse(self, identifier: str) -> BrowseMediaSource:
        """Build similar content browse view for a specific media item.

        Args:
            identifier: Format is similar/movie/imdb_id or similar/series/imdb_id

        Returns:
            BrowseMediaSource with similar content items
        """
        parts = identifier.split("/")
        media_type = parts[1] if len(parts) > 1 else None
        media_id = parts[2] if len(parts) > 2 else None

        if not media_type or not media_id:
            _LOGGER.warning("Invalid similar content identifier: %s", identifier)
            return self._build_error_browse(
                identifier, "Invalid Request", "Missing media type or ID"
            )

        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(identifier, "Similar Content")

        # Try to get source item info for better title
        title = "Similar Content"
        poster = None
        library_items = coordinator.data.get("library", []) if coordinator.data else []
        source_item = next(
            (
                item
                for item in library_items
                if item.get("imdb_id") == media_id or item.get("id") == media_id
            ),
            None,
        )

        if source_item:
            source_title = source_item.get("title") or source_item.get("name")
            poster = source_item.get("poster")
            if source_title:
                title = f"Similar to {source_title}"

        try:
            client = coordinator.client
            similar_items = await client.async_get_similar_content(
                media_id=media_id, limit=20
            )

            children = []
            for item in similar_items:
                child = self._build_catalog_item(item)
                if child:
                    children.append(child)

            # If no similar items found, show a message
            if not children:
                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier="",
                        media_class=MediaClass.VIDEO,
                        media_content_type="",
                        title="No similar content found",
                        can_play=False,
                        can_expand=False,
                        thumbnail=None,
                    )
                )

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=identifier,
                media_class=MediaClass.DIRECTORY,
                media_content_type=(
                    MediaType.MOVIE if media_type == "movie" else MediaType.TVSHOW
                ),
                title=title,
                can_play=False,
                can_expand=True,
                thumbnail=poster,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching similar content for %s: %s", media_id, err)
            return self._build_error_browse(
                identifier, title, f"Failed to load similar content"
            )

    async def _build_genre_content_browse(
        self, identifier: str, media_type: str
    ) -> BrowseMediaSource:
        """Build genre content view showing movies/series for a specific genre.

        Args:
            identifier: Format is movie_genres/Genre or series_genres/Genre
            media_type: "movie" or "series"

        Returns:
            BrowseMediaSource with genre-filtered catalog items
        """
        # Extract genre from identifier
        parts = identifier.split("/")
        genre = parts[1] if len(parts) > 1 else None

        if not genre:
            _LOGGER.warning("Invalid genre identifier: %s", identifier)
            return self._build_error_browse(
                identifier, "Invalid Genre", "Genre not specified"
            )

        coordinator = self._get_coordinator()
        if not coordinator:
            return self._build_empty_browse(
                identifier, f"{genre} {media_type.title()}s"
            )

        try:
            client = coordinator.client
            # Fetch catalog with genre filter
            if media_type == "movie":
                catalog_items = await client.async_get_popular_movies(
                    genre=genre, limit=50
                )
            else:
                catalog_items = await client.async_get_popular_series(
                    genre=genre, limit=50
                )

            children = []
            for item in catalog_items:
                child = self._build_catalog_item(item)
                if child:
                    children.append(child)

            title = f"{genre} {media_type.title()}s"
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=identifier,
                media_class=MediaClass.DIRECTORY,
                media_content_type=(
                    MediaType.MOVIE if media_type == "movie" else MediaType.TVSHOW
                ),
                title=title,
                can_play=False,
                can_expand=True,
                children=children,
            )
        except Exception as err:
            _LOGGER.error("Error fetching %s genre content: %s", genre, err)
            return self._build_error_browse(
                identifier,
                f"{genre} {media_type.title()}s",
                "Failed to load genre content",
            )

    def _build_catalog_item(self, item: dict[str, Any]) -> BrowseMediaSource | None:
        """Build a BrowseMediaSource for a catalog item.

        Args:
            item: Catalog item dictionary from Cinemeta

        Returns:
            BrowseMediaSource or None if item is invalid
        """
        title = item.get("title")
        if not title:
            return None

        media_type = item.get("type", "movie")
        media_id = item.get("imdb_id") or item.get("id")

        if not media_id:
            return None

        # Format identifier - catalog items use same format as library items
        identifier = f"{media_type}/{media_id}"

        # Get poster/thumbnail
        poster = item.get("poster")

        # Add year to title if available
        year = item.get("year")
        if year:
            title = f"{title} ({year})"

        # Determine media class
        if media_type == "series":
            media_class = MediaClass.TV_SHOW
            content_type = MediaType.TVSHOW
        else:
            media_class = MediaClass.MOVIE
            content_type = MediaType.MOVIE

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=media_class,
            media_content_type=content_type,
            title=title,
            can_play=False,  # Need to drill down to streams
            can_expand=True,
            thumbnail=poster,
        )

    def _build_empty_browse(self, identifier: str, title: str) -> BrowseMediaSource:
        """Build an empty browse result.

        Args:
            identifier: The browse identifier
            title: The title for the browse result

        Returns:
            BrowseMediaSource with no children
        """
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=title,
            can_play=False,
            can_expand=False,
            children=[],
        )

    def _build_error_browse(
        self, identifier: str, title: str, error_message: str
    ) -> BrowseMediaSource:
        """Build an error browse result that doesn't close the browser.

        Args:
            identifier: The browse identifier
            title: The title for the browse result
            error_message: Error message to display

        Returns:
            BrowseMediaSource with error message as child
        """
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=title,
            can_play=False,
            can_expand=False,
            children=[
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="",
                    media_class=MediaClass.VIDEO,
                    media_content_type="",
                    title=f"⚠️ {error_message}",
                    can_play=False,
                    can_expand=False,
                    thumbnail=None,
                )
            ],
        )

    def _get_coordinator(self):
        """Get the Stremio coordinator from hass.data."""
        entries = self.hass.data.get(DOMAIN, {})
        for entry_id, entry_data in entries.items():
            if isinstance(entry_data, dict) and "coordinator" in entry_data:
                return entry_data["coordinator"]
        return None

    def _get_config_entry(self):
        """Get the first Stremio config entry."""
        entries = self.hass.data.get(DOMAIN, {})
        for entry_id, entry_data in entries.items():
            if isinstance(entry_data, dict):
                # Return the config entry from hass.config_entries
                return self.hass.config_entries.async_get_entry(entry_id)
        return None

    def _should_show_copy_url(self) -> bool:
        """Check if Copy URL option should be shown in media browser."""
        entry = self._get_config_entry()
        if entry:
            return entry.options.get(CONF_SHOW_COPY_URL, DEFAULT_SHOW_COPY_URL)
        return DEFAULT_SHOW_COPY_URL

    def _get_mime_type(self, url: str, stream_data: dict[str, Any]) -> str:
        """Determine MIME type for a stream URL.

        Args:
            url: Stream URL
            stream_data: Stream metadata dictionary

        Returns:
            MIME type string
        """
        # Check stream metadata first
        mime = stream_data.get("mime_type") or stream_data.get("mimeType")
        if mime:
            return mime

        # Infer from URL
        url_lower = url.lower()
        if ".m3u8" in url_lower or "hls" in url_lower:
            return "application/x-mpegURL"
        if ".mp4" in url_lower:
            return "video/mp4"
        if ".mkv" in url_lower:
            return "video/x-matroska"
        if ".webm" in url_lower:
            return "video/webm"
        if ".avi" in url_lower:
            return "video/x-msvideo"

        # Default to generic video
        return "video/mp4"
