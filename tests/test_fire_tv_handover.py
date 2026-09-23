"""Tests for the Fire TV handover module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.stremio.fire_tv_handover import (
    FireTVHandoverError,
    FireTVHandoverManager,
    build_adb_command,
    build_deep_link,
)


class TestBuildDeepLink:
    """Deep-link URI construction."""

    def test_movie(self):
        assert (
            build_deep_link("movie", "tt0111161")
            == "stremio:///detail/movie/tt0111161/tt0111161"
        )

    def test_series_show_page(self):
        assert (
            build_deep_link("series", "tt12637874")
            == "stremio:///detail/series/tt12637874/tt12637874"
        )

    def test_series_specific_episode(self):
        assert (
            build_deep_link("series", "tt0944947", season=1, episode=3)
            == "stremio:///detail/series/tt0944947/tt0944947:1:3"
        )

    def test_series_partial_season_only_falls_back_to_show(self):
        # Season without episode is ambiguous → open the show page, not an episode.
        assert (
            build_deep_link("series", "tt0944947", season=1)
            == "stremio:///detail/series/tt0944947/tt0944947"
        )

    def test_always_triple_slash(self):
        # Triple slash is load-bearing: a double slash makes "detail" the URI
        # host and drops the path, landing on the app home instead of the title.
        assert build_deep_link("movie", "tt1").startswith("stremio:///")

    def test_invalid_media_type_raises(self):
        with pytest.raises(FireTVHandoverError):
            build_deep_link("channel", "tt1")

    def test_empty_media_id_raises(self):
        with pytest.raises(FireTVHandoverError):
            build_deep_link("movie", "")


def test_build_adb_command():
    uri = "stremio:///detail/movie/tt1/tt1"
    assert build_adb_command(uri) == (
        f'am start -a android.intent.action.VIEW -d "{uri}"'
    )


@pytest.fixture
def mock_hass():
    """A minimal hass whose androidtv service is available."""
    hass = MagicMock()
    hass.services.has_service = MagicMock(return_value=True)
    hass.services.async_call = AsyncMock()
    return hass


class TestFireTVHandoverManager:
    """The manager delegates to androidtv.adb_command."""

    async def test_handover_calls_androidtv_adb_command(self, mock_hass):
        manager = FireTVHandoverManager(mock_hass)

        result = await manager.async_handover(
            device_entity_id="media_player.fire_tv",
            media_type="series",
            media_id="tt12637874",
            season=1,
            episode=2,
        )

        mock_hass.services.async_call.assert_awaited_once()
        args, kwargs = mock_hass.services.async_call.call_args
        assert args[0] == "androidtv"
        assert args[1] == "adb_command"
        assert args[2]["entity_id"] == "media_player.fire_tv"
        assert (
            'stremio:///detail/series/tt12637874/tt12637874:1:2' in args[2]["command"]
        )
        assert kwargs.get("blocking") is True
        assert (
            result["uri"] == "stremio:///detail/series/tt12637874/tt12637874:1:2"
        )
        assert result["device_id"] == "media_player.fire_tv"

    async def test_handover_without_androidtv_raises(self, mock_hass):
        mock_hass.services.has_service = MagicMock(return_value=False)
        manager = FireTVHandoverManager(mock_hass)

        with pytest.raises(FireTVHandoverError):
            await manager.async_handover(
                "media_player.fire_tv", "movie", "tt1"
            )
        mock_hass.services.async_call.assert_not_awaited()

    async def test_handover_wraps_adb_failure(self, mock_hass):
        mock_hass.services.async_call = AsyncMock(
            side_effect=RuntimeError("adb boom")
        )
        manager = FireTVHandoverManager(mock_hass)

        with pytest.raises(FireTVHandoverError):
            await manager.async_handover(
                "media_player.fire_tv", "movie", "tt1"
            )
