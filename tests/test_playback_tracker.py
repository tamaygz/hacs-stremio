"""Tests for saving VLC playback progress to Stremio."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.stremio.playback_tracker import (
    DATA_TRACKERS,
    VLC_APP_ID,
    TrackedMedia,
    async_start_tracking,
    live_position,
)
from custom_components.stremio.stremio_client import (
    StremioClient,
    watch_progress_percent,
)

ATV = "media_player.media_apple_tv"


def _vlc(state="playing", position=0, title="Show S01E04", duration=2889, at=None):
    return {
        "app_id": VLC_APP_ID,
        "app_name": "VLC",
        "media_title": title,
        "media_duration": duration,
        "media_position": position,
        "media_position_updated_at": (at or dt_util.utcnow()).isoformat(),
    }


class TestLivePosition:
    def test_playing_adds_elapsed_time(self):
        at = dt_util.utcnow() - timedelta(seconds=30)
        state = State(ATV, "playing", _vlc(position=100, at=at))
        assert 129 <= live_position(state) <= 131

    def test_paused_uses_reported_position(self):
        at = dt_util.utcnow() - timedelta(seconds=30)
        assert live_position(State(ATV, "paused", _vlc(position=201, at=at))) == 201

    def test_clamped_to_duration(self):
        at = dt_util.utcnow() - timedelta(hours=2)
        state = State(ATV, "playing", _vlc(position=100, at=at, duration=500))
        assert live_position(state) == 500


class TestWatchProgressPercent:
    def test_uses_time_offset_and_caps(self):
        assert watch_progress_percent(
            {"progress": 1760, "time_offset": 300, "duration": 1000}
        ) == 30
        assert watch_progress_percent({"progress": 1760, "duration": 1000}) == 100
        assert watch_progress_percent({"progress": 5, "duration": 0}) == 0


def _client():
    client = MagicMock()
    client.async_update_playback = AsyncMock(return_value=True)
    return client


async def _start(hass, client, media=None, title_before=None):
    tracker = async_start_tracking(
        hass, client, ATV, media or TrackedMedia("tt1", "movie"), title_before
    )
    await hass.async_block_till_done()
    return tracker


class TestTracker:
    async def test_pause_saves_position(self, hass: HomeAssistant):
        client = _client()
        hass.states.async_set(ATV, "idle", {})
        await _start(hass, client)

        hass.states.async_set(ATV, "playing", _vlc(position=0))
        hass.states.async_set(ATV, "paused", _vlc(state="paused", position=201))
        await hass.async_block_till_done()

        kwargs = client.async_update_playback.call_args.kwargs
        assert kwargs["media_id"] == "tt1"
        assert kwargs["time_offset"] == 201000
        assert kwargs["duration"] == 2889000
        assert kwargs["finished"] is False

    async def test_interval_saves_live_position(self, hass: HomeAssistant):
        client = _client()
        await _start(hass, client)
        at = dt_util.utcnow() - timedelta(seconds=120)
        hass.states.async_set(ATV, "playing", _vlc(position=0, at=at))
        await hass.async_block_till_done()
        client.async_update_playback.assert_not_called()

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
        await hass.async_block_till_done()
        offset = client.async_update_playback.call_args.kwargs["time_offset"]
        # 120 s since the position was reported (the timer fires; the clock is real)
        assert 120000 <= offset <= 122000

    async def test_stop_saves_last_position_and_ends(self, hass: HomeAssistant):
        client = _client()
        await _start(hass, client)
        hass.states.async_set(ATV, "paused", _vlc(state="paused", position=600))
        await hass.async_block_till_done()
        hass.states.async_set(ATV, "idle", {"app_id": VLC_APP_ID})
        await hass.async_block_till_done()

        assert client.async_update_playback.call_args.kwargs["time_offset"] == 600000
        assert ATV not in hass.data[DATA_TRACKERS]

    async def test_near_end_marks_finished(self, hass: HomeAssistant):
        client = _client()
        await _start(hass, client)
        hass.states.async_set(ATV, "paused", _vlc(state="paused", position=2800))
        await hass.async_block_till_done()
        assert client.async_update_playback.call_args.kwargs["finished"] is True

    async def test_previous_vlc_file_is_ignored(self, hass: HomeAssistant):
        client = _client()
        await _start(hass, client, title_before="Old file")
        hass.states.async_set(
            ATV, "paused", _vlc(state="paused", position=900, title="Old file")
        )
        await hass.async_block_till_done()
        client.async_update_playback.assert_not_called()

        hass.states.async_set(ATV, "paused", _vlc(state="paused", position=50, title="New"))
        await hass.async_block_till_done()
        assert client.async_update_playback.call_args.kwargs["time_offset"] == 50000

    async def test_resume_point_kept_while_skipping_ahead(self, hass: HomeAssistant):
        client = _client()
        await _start(hass, client, TrackedMedia("tt1", "movie", saved_position=2520))
        hass.states.async_set(ATV, "paused", _vlc(state="paused", position=40))
        await hass.async_block_till_done()
        client.async_update_playback.assert_not_called()

        hass.states.async_set(ATV, "paused", _vlc(state="paused", position=2600))
        await hass.async_block_till_done()
        assert client.async_update_playback.call_args.kwargs["time_offset"] == 2600000

    async def test_other_app_ends_without_save_before_start(self, hass: HomeAssistant):
        client = _client()
        await _start(hass, client)
        hass.states.async_set(ATV, "playing", {"app_id": "com.netflix.Netflix"})
        await hass.async_block_till_done()
        client.async_update_playback.assert_not_called()

    async def test_new_handover_replaces_tracker(self, hass: HomeAssistant):
        client = _client()
        first = await _start(hass, client)
        second = await _start(hass, client, TrackedMedia("tt2", "movie"))
        assert hass.data[DATA_TRACKERS][ATV] is second
        assert first is not second


class TestUpdatePlayback:
    @staticmethod
    def _client_with(item):
        client = StremioClient("test@example.com", "password")
        client._auth_key = "key"
        if item is None or item.get("removed"):
            client.async_find_existing_item = AsyncMock(return_value=None)
            client._async_new_library_item = AsyncMock(
                return_value=item and {**item, "temp": True}
            )
        else:
            client.async_find_existing_item = AsyncMock(return_value=item)
        response = MagicMock(status=200)
        response.json = AsyncMock(return_value={"result": {"success": True}})
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        client._get_session = AsyncMock(return_value=session)
        return client, session

    @staticmethod
    def _sent(session):
        return session.post.call_args.kwargs["json"]["changes"][0]

    async def test_title_not_in_library_is_temp(self):
        client, session = self._client_with(
            {"_id": "tt1", "type": "movie", "removed": True, "state": {}}
        )
        assert await client.async_update_playback("tt1", "movie")
        item = self._sent(session)
        assert item["removed"] is True and item["temp"] is True
        assert item["state"]["timeOffset"] == 1000  # enough to show in the list
        assert item["state"]["lastWatched"]

    async def test_library_title_keeps_saved_position(self):
        client, session = self._client_with(
            {
                "_id": "tt1",
                "type": "movie",
                "removed": False,
                "state": {"timeOffset": 2520000, "video_id": "tt1", "timeWatched": 10},
            }
        )
        await client.async_update_playback("tt1", "movie")
        item = self._sent(session)
        assert "temp" not in item
        assert item["state"]["timeOffset"] == 2520000

    async def test_new_episode_resets_and_records_position(self):
        client, session = self._client_with(
            {
                "_id": "tt9",
                "type": "series",
                "removed": False,
                "state": {"timeOffset": 900000, "video_id": "tt9:1:3"},
            }
        )
        await client.async_update_playback("tt9", "series", 1, 4, time_offset=201000)
        state = self._sent(session)["state"]
        assert state["video_id"] == "tt9:1:4"
        assert state["timeOffset"] == 201000
        assert state["timeWatched"] == 201000

    async def test_finished_marks_watched(self):
        client, session = self._client_with(
            {"_id": "tt1", "type": "movie", "removed": False, "state": {"timesWatched": 1}}
        )
        await client.async_update_playback("tt1", "movie", finished=True)
        state = self._sent(session)["state"]
        assert state["timeOffset"] == 0
        assert state["flaggedWatched"] == 1
        assert state["timesWatched"] == 2
        assert state["watched"]


class TestContinueWatchingIncludesTemp:
    def test_temp_items_listed_removed_items_not(self):
        client = StremioClient("test@example.com", "password")
        items = client._process_continue_watching(
            [
                {"_id": "tt1", "name": "A", "type": "movie", "removed": True, "temp": True, "state": {}},
                {"_id": "tt2", "name": "B", "type": "movie", "removed": True, "state": {}},
            ]
        )
        assert [i["imdb_id"] for i in items] == ["tt1"]


class TestNewLibraryItem:
    """Series not in the library get an entry built from Cinemeta."""

    async def test_series_without_default_video_id(self):
        client = StremioClient("test@example.com", "password")
        response = MagicMock(status=200)
        # Cinemeta series metadata has no behaviorHints.defaultVideoId
        response.json = AsyncMock(
            return_value={"meta": {"type": "series", "name": "VisionQuest", "poster": "p"}}
        )
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.get = MagicMock(return_value=ctx)
        client._get_session = AsyncMock(return_value=session)

        item = await client._async_new_library_item("tt9", "series")
        assert item["_id"] == "tt9"
        assert item["name"] == "VisionQuest"
        assert item["removed"] is True and item["temp"] is True

    async def test_unknown_title_returns_none(self):
        client = StremioClient("test@example.com", "password")
        response = MagicMock(status=404)
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.get = MagicMock(return_value=ctx)
        client._get_session = AsyncMock(return_value=session)
        assert await client._async_new_library_item("tt0", "series") is None

    async def test_new_series_episode_recorded(self):
        client = StremioClient("test@example.com", "password")
        client._auth_key = "key"
        client.async_find_existing_item = AsyncMock(return_value=None)
        client._async_new_library_item = AsyncMock(
            return_value={"_id": "tt9", "type": "series", "name": "V", "removed": True, "temp": True, "state": {}}
        )
        response = MagicMock(status=200)
        response.json = AsyncMock(return_value={"result": {"success": True}})
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.post = MagicMock(return_value=ctx)
        client._get_session = AsyncMock(return_value=session)

        assert await client.async_update_playback("tt9", "series", 1, 4)
        sent = session.post.call_args.kwargs["json"]["changes"][0]
        assert sent["state"]["video_id"] == "tt9:1:4"
        assert sent["state"]["timeOffset"] == 1000
