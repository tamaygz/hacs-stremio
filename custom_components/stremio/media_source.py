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

from .const import DOMAIN

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

            # Get the best stream (first one or highest quality)
            best_stream = streams[0]
            stream_url = best_stream.get("url") or best_stream.get("externalUrl")

            if not stream_url:
                raise Unresolvable("No playable stream URL available")

            # Determine MIME type
            mime_type = self._get_mime_type(stream_url, best_stream)

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

        # Handle root level browsing
        if identifier == ROOT_IDENTIFIER or not identifier:
            return self._build_root_browse()

        # Handle different browse sections
        if identifier == LIBRARY_IDENTIFIER:
            return await self._build_library_browse()
        if identifier == CONTINUE_WATCHING_IDENTIFIER:
            return await self._build_continue_watching_browse()
        if identifier == MOVIES_IDENTIFIER:
            return await self._build_movies_browse()
        if identifier == SERIES_IDENTIFIER:
            return await self._build_series_browse()

        # Handle individual series items (series/imdb_id or series/imdb_id/season)
        if identifier.startswith(f"{SERIES_IDENTIFIER}/"):
            return await self._build_series_detail_browse(identifier)

        # Handle individual movie items (movie/imdb_id)
        if identifier.startswith("movie/"):
            return await self._build_movie_detail_browse(identifier)

        raise BrowseError(f"Unknown media identifier: {identifier}")

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
                    identifier=LIBRARY_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title="Library",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=MOVIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MOVIE,
                    title="Movies",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=SERIES_IDENTIFIER,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.TVSHOW,
                    title="TV Series",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
            ],
        )

    async def _build_library_browse(self) -> BrowseMediaSource:
        """Build library browse view."""
        coordinator = self._get_coordinator()
        if not coordinator:
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
        if not coordinator:
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
        if not coordinator:
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
        if not coordinator:
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
        """Build movie detail view showing the movie as playable.

        Args:
            identifier: Format is movie/imdb_id

        Returns:
            BrowseMediaSource for the movie
        """
        parts = identifier.split("/")
        media_id = parts[1] if len(parts) > 1 else None

        if not media_id:
            raise BrowseError("Invalid movie identifier")

        coordinator = self._get_coordinator()
        if not coordinator:
            raise BrowseError("Stremio coordinator not available")

        # Find movie in library
        library_items = coordinator.data.get("library", [])
        movie_item = next(
            (
                item
                for item in library_items
                if (item.get("imdb_id") == media_id or item.get("id") == media_id)
                and item.get("type") == "movie"
            ),
            None,
        )

        if not movie_item:
            # Return a placeholder for movies not in library (e.g., from search)
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=identifier,
                media_class=MediaClass.MOVIE,
                media_content_type=MediaType.MOVIE,
                title=f"Movie ({media_id})",
                can_play=True,
                can_expand=False,
                thumbnail=None,
            )

        title = movie_item.get("title") or movie_item.get("name") or "Unknown Movie"
        poster = movie_item.get("poster") or movie_item.get("thumbnail")
        year = movie_item.get("year")
        description = movie_item.get("description") or movie_item.get("overview")

        if year:
            title = f"{title} ({year})"

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.MOVIE,
            media_content_type=MediaType.MOVIE,
            title=title,
            can_play=True,
            can_expand=False,
            thumbnail=poster,
        )

    async def _build_series_detail_browse(self, identifier: str) -> BrowseMediaSource:
        """Build series detail view with seasons and episodes.

        Args:
            identifier: Format is series/imdb_id or series/imdb_id/season
        """
        parts = identifier.split("/")
        media_id = parts[1] if len(parts) > 1 else None
        season = int(parts[2]) if len(parts) > 2 else None

        if not media_id:
            raise BrowseError("Invalid series identifier")

        coordinator = self._get_coordinator()
        if not coordinator:
            raise BrowseError("Stremio coordinator not available")

        # Find series in library
        library_items = coordinator.data.get("library", [])
        series_item = next(
            (
                item
                for item in library_items
                if item.get("imdb_id") == media_id or item.get("id") == media_id
            ),
            None,
        )

        if not series_item:
            raise BrowseError(f"Series not found: {media_id}")

        title = series_item.get("title") or series_item.get("name") or "Unknown Series"
        poster = series_item.get("poster")
        seasons = series_item.get("seasons", [])

        # If no season specified, show season list
        if season is None:
            children = []
            for season_num in range(1, len(seasons) + 1 if seasons else 10):
                season_id = f"{SERIES_IDENTIFIER}/{media_id}/{season_num}"
                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=season_id,
                        media_class=MediaClass.SEASON,
                        media_content_type=MediaType.SEASON,
                        title=f"Season {season_num}",
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

        # Show episodes for specific season
        episodes = []
        season_data = seasons[season - 1] if seasons and season <= len(seasons) else {}
        episode_list = season_data.get("episodes", [])

        for ep_num, episode in enumerate(episode_list, 1):
            ep_title = episode.get("title") or f"Episode {ep_num}"
            ep_identifier = f"series/{media_id}/{season}/{ep_num}"
            ep_thumbnail = episode.get("thumbnail") or poster

            episodes.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=ep_identifier,
                    media_class=MediaClass.EPISODE,
                    media_content_type=MediaType.EPISODE,
                    title=ep_title,
                    can_play=True,
                    can_expand=False,
                    thumbnail=ep_thumbnail,
                )
            )

        # If no episodes in data, create placeholders
        if not episodes:
            for ep_num in range(1, 13):  # Default 12 episodes
                ep_identifier = f"series/{media_id}/{season}/{ep_num}"
                episodes.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=ep_identifier,
                        media_class=MediaClass.EPISODE,
                        media_content_type=MediaType.EPISODE,
                        title=f"Episode {ep_num}",
                        can_play=True,
                        can_expand=False,
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

        # Determine media class
        if media_type == "series":
            media_class = MediaClass.TV_SHOW
            content_type = MediaType.TVSHOW
            can_play = False  # Need to drill down to episode
            can_expand = True
        else:
            media_class = MediaClass.MOVIE
            content_type = MediaType.MOVIE
            can_play = True
            can_expand = False

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=media_class,
            media_content_type=content_type,
            title=title,
            can_play=can_play,
            can_expand=can_expand,
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

    def _get_coordinator(self):
        """Get the Stremio coordinator from hass.data."""
        entries = self.hass.data.get(DOMAIN, {})
        for entry_id, entry_data in entries.items():
            if isinstance(entry_data, dict) and "coordinator" in entry_data:
                return entry_data["coordinator"]
        return None

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
