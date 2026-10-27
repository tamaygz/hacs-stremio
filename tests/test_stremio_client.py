"""Tests for Stremio API client streaming features."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.stremio.stremio_client import StremioClient


class TestAddonSorting:
    """Tests for addon sorting by user preference."""

    def test_sort_addons_by_preference_basic(self):
        """Test basic addon sorting by preference list."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {"name": "CinemetaStreams", "id": "cinemeta"},
            {"name": "Torrentio", "id": "torrentio"},
            {"name": "OpenSubtitles", "id": "opensubtitles"},
        ]

        addon_order = ["Torrentio", "OpenSubtitles", "CinemetaStreams"]

        result = client._sort_addons_by_preference(addons, addon_order)

        assert result[0]["name"] == "Torrentio"
        assert result[1]["name"] == "OpenSubtitles"
        assert result[2]["name"] == "CinemetaStreams"

    def test_sort_addons_by_preference_partial(self):
        """Test sorting when only some addons are in preference list."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {"name": "Addon1", "id": "addon1"},
            {"name": "Addon2", "id": "addon2"},
            {"name": "Addon3", "id": "addon3"},
        ]

        # Only specify order for Addon2
        addon_order = ["Addon2"]

        result = client._sort_addons_by_preference(addons, addon_order)

        # Addon2 should be first, others follow
        assert result[0]["name"] == "Addon2"

    def test_sort_addons_by_preference_empty_order(self):
        """Test sorting with empty preference list."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {"name": "Addon1", "id": "addon1"},
            {"name": "Addon2", "id": "addon2"},
        ]

        result = client._sort_addons_by_preference(addons, [])

        # Should return addons unchanged
        assert len(result) == 2

    def test_sort_addons_by_preference_string_parsing(self):
        """Test sorting when addon_order is a multiline string."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {"name": "CinemetaStreams", "id": "cinemeta"},
            {"name": "Torrentio", "id": "torrentio"},
        ]

        # Multiline string as it comes from config
        addon_order = "Torrentio\nCinemetaStreams"

        result = client._sort_addons_by_preference(addons, addon_order)

        assert result[0]["name"] == "Torrentio"
        assert result[1]["name"] == "CinemetaStreams"

    def test_sort_addons_case_insensitive(self):
        """Test that sorting is case insensitive."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {"name": "TORRENTIO", "id": "torrentio"},
            {"name": "CinemetaStreams", "id": "cinemeta"},
        ]

        addon_order = ["torrentio", "cinemetastreams"]

        result = client._sort_addons_by_preference(addons, addon_order)

        assert result[0]["name"] == "TORRENTIO"
        assert result[1]["name"] == "CinemetaStreams"

    def test_sort_addons_by_id(self):
        """Test sorting by addon ID when name doesn't match."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {"name": "Some Addon Name", "id": "torrentio"},
            {"name": "Another Addon", "id": "cinemeta"},
        ]

        # Use addon IDs in preference
        addon_order = ["cinemeta", "torrentio"]

        result = client._sort_addons_by_preference(addons, addon_order)

        assert result[0]["id"] == "cinemeta"
        assert result[1]["id"] == "torrentio"


class TestQualityFiltering:
    """Tests for stream quality filtering."""

    def test_filter_streams_4k(self):
        """Test filtering for 4K streams."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "Source1", "title": "1080p BluRay"},
            {"name": "Source2", "title": "4K HDR"},
            {"name": "Source3", "title": "2160p UHD"},
            {"name": "Source4", "title": "720p WEB"},
        ]

        result = client._filter_streams_by_quality(streams, "4k")

        # 4K and 2160p should be first
        assert len(result) == 4
        assert result[0]["title"] == "4K HDR"
        assert result[1]["title"] == "2160p UHD"

    def test_filter_streams_1080p(self):
        """Test filtering for 1080p streams."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "Source1", "title": "720p WEB"},
            {"name": "Source2", "title": "1080p BluRay"},
            {"name": "Source3", "title": "Full HD Movie"},
            {"name": "Source4", "title": "480p HDTV"},
        ]

        result = client._filter_streams_by_quality(streams, "1080p")

        # 1080p and FHD should be first
        assert result[0]["title"] == "1080p BluRay"
        assert result[1]["title"] == "Full HD Movie"

    def test_filter_streams_720p(self):
        """Test filtering for 720p streams."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "Source1", "title": "1080p BluRay"},
            {"name": "Source2", "title": "720p WEB-DL"},
            {"name": "Source3", "quality": "HD"},
        ]

        result = client._filter_streams_by_quality(streams, "720p")

        # 720p and HD should be first
        assert result[0]["title"] == "720p WEB-DL"

    def test_filter_streams_any(self):
        """Test that 'any' quality returns all streams unchanged."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "Source1", "title": "1080p"},
            {"name": "Source2", "title": "720p"},
        ]

        result = client._filter_streams_by_quality(streams, "any")

        assert result == streams

    def test_filter_streams_preserves_all(self):
        """Test that filtering preserves all streams (just reorders)."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "A", "title": "720p"},
            {"name": "B", "title": "1080p"},
            {"name": "C", "title": "480p"},
        ]

        result = client._filter_streams_by_quality(streams, "1080p")

        # All streams should still be present
        assert len(result) == 3
        # 1080p should be first
        assert result[0]["title"] == "1080p"

    def test_filter_streams_quality_in_name(self):
        """Test quality detection in stream name field."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "1080p BluRay x264", "title": "Movie"},
            {"name": "720p WEB-DL", "title": "Movie"},
        ]

        result = client._filter_streams_by_quality(streams, "1080p")

        assert result[0]["name"] == "1080p BluRay x264"

    def test_filter_streams_quality_field(self):
        """Test quality detection in quality field."""
        client = StremioClient("test@example.com", "password")

        streams = [
            {"name": "Source", "title": "Movie", "quality": "1080p"},
            {"name": "Source", "title": "Movie", "quality": "720p"},
        ]

        result = client._filter_streams_by_quality(streams, "1080p")

        assert result[0]["quality"] == "1080p"


class TestStreamAddonFiltering:
    """Tests for stream addon filtering."""

    def test_filter_stream_addons_provides_stream(self):
        """Test filtering addons that provide stream resource."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {
                "manifest": {
                    "name": "TestAddon",
                    "id": "test",
                    "resources": ["stream"],
                    "types": ["movie"],
                },
                "transportUrl": "https://test.com/manifest.json",
            },
            {
                "manifest": {
                    "name": "MetaOnly",
                    "id": "meta",
                    "resources": ["meta"],
                    "types": ["movie"],
                },
                "transportUrl": "https://meta.com/manifest.json",
            },
        ]

        result = client._filter_stream_addons(addons, "movie", "tt1234567")

        assert len(result) == 1
        assert result[0]["name"] == "TestAddon"

    def test_filter_stream_addons_type_match(self):
        """Test filtering addons by content type."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {
                "manifest": {
                    "name": "MovieAddon",
                    "id": "movies",
                    "resources": ["stream"],
                    "types": ["movie"],
                },
                "transportUrl": "https://movies.com/manifest.json",
            },
            {
                "manifest": {
                    "name": "SeriesAddon",
                    "id": "series",
                    "resources": ["stream"],
                    "types": ["series"],
                },
                "transportUrl": "https://series.com/manifest.json",
            },
        ]

        result = client._filter_stream_addons(addons, "series", "tt1234567")

        assert len(result) == 1
        assert result[0]["name"] == "SeriesAddon"

    def test_filter_stream_addons_id_prefix(self):
        """Test filtering addons by ID prefix."""
        client = StremioClient("test@example.com", "password")

        addons = [
            {
                "manifest": {
                    "name": "IMDBAddon",
                    "id": "imdb",
                    "resources": ["stream"],
                    "types": ["movie"],
                    "idPrefixes": ["tt"],
                },
                "transportUrl": "https://imdb.com/manifest.json",
            },
            {
                "manifest": {
                    "name": "KitsuAddon",
                    "id": "kitsu",
                    "resources": ["stream"],
                    "types": ["movie"],
                    "idPrefixes": ["kitsu:"],
                },
                "transportUrl": "https://kitsu.com/manifest.json",
            },
        ]

        result = client._filter_stream_addons(addons, "movie", "tt1234567")

        assert len(result) == 1
        assert result[0]["name"] == "IMDBAddon"


class TestGetStreamsIntegration:
    """Integration tests for get_streams with preferences."""

    @pytest.mark.asyncio
    async def test_get_streams_with_addon_order(self):
        """Test get_streams respects addon order preference."""
        client = StremioClient("test@example.com", "password")
        client._auth_key = "test_key"

        mock_addons = [
            {
                "manifest": {
                    "name": "Addon1",
                    "id": "addon1",
                    "resources": ["stream"],
                    "types": ["movie"],
                },
                "transportUrl": "https://addon1.com/manifest.json",
            },
            {
                "manifest": {
                    "name": "Addon2",
                    "id": "addon2",
                    "resources": ["stream"],
                    "types": ["movie"],
                },
                "transportUrl": "https://addon2.com/manifest.json",
            },
        ]

        mock_streams = [
            {"name": "Stream1", "url": "http://test.com/1.mp4", "addon": "Addon1"},
        ]

        with patch.object(
            client, "async_get_addon_collection", return_value=mock_addons
        ), patch.object(
            client, "_fetch_streams_from_addons", return_value=mock_streams
        ):
            result = await client.async_get_streams(
                media_id="tt1234567",
                media_type="movie",
                addon_order=["Addon2", "Addon1"],
                quality_preference="any",
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_streams_with_quality_preference(self):
        """Test get_streams applies quality preference."""
        client = StremioClient("test@example.com", "password")
        client._auth_key = "test_key"

        mock_addons = [
            {
                "manifest": {
                    "name": "TestAddon",
                    "id": "test",
                    "resources": ["stream"],
                    "types": ["movie"],
                },
                "transportUrl": "https://test.com/manifest.json",
            },
        ]

        mock_streams = [
            {"name": "720p", "title": "720p WEB", "url": "http://test.com/720.mp4"},
            {
                "name": "1080p",
                "title": "1080p BluRay",
                "url": "http://test.com/1080.mp4",
            },
        ]

        with patch.object(
            client, "async_get_addon_collection", return_value=mock_addons
        ), patch.object(
            client, "_fetch_streams_from_addons", return_value=mock_streams
        ):
            result = await client.async_get_streams(
                media_id="tt1234567",
                media_type="movie",
                quality_preference="1080p",
            )

            # 1080p should be first
            assert result[0]["title"] == "1080p BluRay"
            # 720p should still be included
            assert len(result) == 2


class TestContinueWatchingResumeFields:
    """Continue-watching items carry the playback position for resume hints."""

    def test_time_offset_and_video_id_exposed(self):
        client = StremioClient("test@example.com", "password")
        items = client._process_continue_watching(
            [
                {
                    "_id": "tt0111161",
                    "name": "Movie",
                    "type": "movie",
                    "state": {"timeWatched": 900000, "timeOffset": 2520000, "duration": 8520000},
                },
                {
                    "_id": "tt0903747",
                    "name": "Show",
                    "type": "series",
                    "state": {
                        "timeWatched": 100,
                        "timeOffset": 600000,
                        "duration": 3000000,
                        "video_id": "tt0903747:2:5",
                    },
                },
            ]
        )
        movie, show = items
        assert movie["time_offset"] == 2520000
        assert movie["progress"] == 900000  # unchanged: total time watched
        assert show["time_offset"] == 600000
        assert show["video_id"] == "tt0903747:2:5"
        assert (show["season"], show["episode"]) == (2, 5)

    def test_missing_time_offset_defaults_to_zero(self):
        client = StremioClient("test@example.com", "password")
        (item,) = client._process_continue_watching(
            [{"_id": "tt1", "name": "M", "type": "movie", "state": {}}]
        )
        assert item["time_offset"] == 0


class TestContinueWatchingFilter:
    """Continue Watching uses Stremio's rule: in progress and in library or temp."""

    async def test_filter(self):
        from unittest.mock import AsyncMock, MagicMock

        client = StremioClient("test@example.com", "password")
        client._auth_key = "key"
        library = [
            {"_id": "tt1", "name": "In progress", "type": "movie", "state": {"timeOffset": 5000, "timeWatched": 5000, "lastWatched": "2026-10-27T01:00:00.000Z"}},
            {"_id": "tt2", "name": "Finished", "type": "movie", "state": {"timeOffset": 0, "timeWatched": 9000}},
            {"_id": "tt3", "name": "Temp in progress", "type": "movie", "removed": True, "temp": True, "state": {"timeOffset": 1000, "lastWatched": "2026-10-27T02:00:00.000Z"}},
            {"_id": "tt4", "name": "Removed", "type": "movie", "removed": True, "state": {"timeOffset": 1000}},
        ]
        response = MagicMock(status=200)
        response.json = AsyncMock(return_value={"result": library})
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        client._get_session = AsyncMock(return_value=session)

        items = await client.async_get_continue_watching()
        assert [i["imdb_id"] for i in items] == ["tt3", "tt1"]
