"""Track VLC playback on an Apple TV and save progress to Stremio.

VLC on tvOS can't report back to Stremio, but the Apple TV integration exposes
VLC's now-playing info. Home Assistant only refreshes media_position when
playback changes (play, pause, seek), so the live position is
media_position + time since media_position_updated_at while playing.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .apple_tv_handover import VLC_APP_ID, safe_error

_LOGGER = logging.getLogger(__name__)

# Seconds to wait for VLC to start playing the handed-over stream
START_TIMEOUT = 90
# Save progress this often while playing
SAVE_INTERVAL = timedelta(seconds=60)
# Skip a save when the position moved less than this (seconds)
MIN_SAVE_DELTA = 15
# Treat as finished at this share of the duration
FINISHED_RATIO = 0.92
# VLC always starts at 0:00. Keep the saved position this long (seconds) so the
# viewer can skip ahead; staying before it longer counts as starting over.
RESUME_GRACE = 300

DATA_TRACKERS = "stremio_playback_trackers"


@dataclass
class TrackedMedia:
    """What is playing, in Stremio terms."""

    media_id: str
    media_type: str = "movie"
    season: int | None = None
    episode: int | None = None
    # Position Stremio already had for this title/episode (seconds)
    saved_position: float = 0.0


def _is_vlc(state: State | None) -> bool:
    return bool(
        state
        and state.attributes.get("app_id") == VLC_APP_ID
        and state.state in ("playing", "paused")
    )


def live_position(state: State, now: datetime | None = None) -> float | None:
    """Current playback position in seconds, or None if unknown."""
    position = state.attributes.get("media_position")
    if position is None:
        return None
    position = float(position)
    if state.state == "playing":
        updated = state.attributes.get("media_position_updated_at")
        if isinstance(updated, str):
            updated = dt_util.parse_datetime(updated)
        if isinstance(updated, datetime):
            position += max(0.0, ((now or dt_util.utcnow()) - updated).total_seconds())
    duration = state.attributes.get("media_duration")
    if duration:
        position = min(position, float(duration))
    return max(0.0, position)


class PlaybackTracker:
    """Follow one VLC session on one Apple TV and mirror it to Stremio."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: Any,
        entity_id: str,
        media: TrackedMedia,
        on_saved: Callable[[], None] | None = None,
    ) -> None:
        self.hass = hass
        self.client = client
        self.entity_id = entity_id
        self.media = media
        self._on_saved = on_saved
        self._title_before: str | None = None
        self._title: str | None = None
        self._started = False
        self._last_position: float | None = None
        self._duration: float | None = None
        self._saved_position: float | None = None
        self._started_at: datetime | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._stopped = False

    @callback
    def start(self, title_before: str | None = None) -> None:
        """Begin watching the Apple TV entity.

        Args:
            title_before: VLC's media_title before the handover, so the previous
                file isn't mistaken for the new one
        """
        self._title_before = title_before
        self._unsubs.append(
            async_track_state_change_event(
                self.hass, [self.entity_id], self._handle_state_event
            )
        )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._handle_interval, SAVE_INTERVAL)
        )
        self._unsubs.append(
            async_call_later(self.hass, START_TIMEOUT, self._handle_start_timeout)
        )
        _LOGGER.debug("Tracking VLC playback on %s", self.entity_id)

    @callback
    def stop(self) -> None:
        """Stop tracking without saving."""
        self._stopped = True
        while self._unsubs:
            self._unsubs.pop()()

    @callback
    def _handle_start_timeout(self, _now: datetime) -> None:
        if not self._started and not self._stopped:
            _LOGGER.info(
                "VLC didn't start on %s within %ss; not tracking",
                self.entity_id,
                START_TIMEOUT,
            )
            self._finish(save=False)

    @callback
    def _handle_state_event(self, event: Event) -> None:
        self._update(event.data.get("new_state"))

    @callback
    def _handle_interval(self, _now: datetime) -> None:
        self._update(self.hass.states.get(self.entity_id), periodic=True)

    @callback
    def _update(self, state: State | None, periodic: bool = False) -> None:
        if self._stopped:
            return

        if not self._started:
            if not _is_vlc(state) or not state.attributes.get("media_duration"):
                return
            title = state.attributes.get("media_title")
            if self._title_before is not None and title == self._title_before:
                # Still the previous VLC file
                return
            self._started = True
            self._started_at = dt_util.utcnow()
            self._title = title
            _LOGGER.info("VLC playback started on %s", self.entity_id)

        if not _is_vlc(state) or (
            self._title is not None
            and state.attributes.get("media_title") not in (None, self._title)
        ):
            # VLC stopped, closed, or moved to another file: save where it was
            self._finish(save=True)
            return

        position = live_position(state)
        if position is not None and (position > 0 or self._last_position is None):
            self._last_position = position
        duration = state.attributes.get("media_duration")
        if duration:
            self._duration = float(duration)

        if self._is_finished():
            self._finish(save=True)
            return

        if state.state == "paused" or periodic:
            self._save_if_moved()

    def _is_finished(self) -> bool:
        return bool(
            self._duration
            and self._last_position is not None
            and self._last_position >= self._duration * FINISHED_RATIO
        )

    def _keeping_resume_point(self) -> bool:
        """True while the viewer may still be skipping ahead to the saved position."""
        floor = self.media.saved_position
        if not floor or self._last_position is None or self._last_position >= floor:
            return False
        if self._started_at is None:
            return True
        return (dt_util.utcnow() - self._started_at).total_seconds() < RESUME_GRACE

    @callback
    def _save_if_moved(self) -> None:
        if self._last_position is None or self._keeping_resume_point():
            return
        if (
            self._saved_position is not None
            and abs(self._last_position - self._saved_position) < MIN_SAVE_DELTA
        ):
            return
        self._save(finished=False)

    @callback
    def _finish(self, save: bool) -> None:
        finished = self._is_finished()
        self.stop()
        if (
            save
            and self._started
            and self._last_position is not None
            and (finished or not self._keeping_resume_point())
        ):
            self._save(finished=finished)
        trackers = self.hass.data.get(DATA_TRACKERS, {})
        if trackers.get(self.entity_id) is self:
            trackers.pop(self.entity_id)

    @callback
    def _save(self, finished: bool) -> None:
        position = self._last_position or 0.0
        self._saved_position = position
        self.hass.async_create_background_task(
            self._async_save(position, finished),
            f"stremio_save_progress_{self.entity_id}",
        )

    async def _async_save(self, position: float, finished: bool) -> None:
        try:
            await self.client.async_update_playback(
                media_id=self.media.media_id,
                media_type=self.media.media_type,
                season=self.media.season,
                episode=self.media.episode,
                time_offset=int(position * 1000),
                duration=int(self._duration * 1000) if self._duration else None,
                finished=finished,
            )
            _LOGGER.debug(
                "Saved Stremio progress for %s: %ss%s",
                self.media.media_id,
                int(position),
                " (finished)" if finished else "",
            )
            if self._on_saved:
                self._on_saved()
        except Exception as err:  # noqa: BLE001 - never break playback over a save
            _LOGGER.warning(
                "Couldn't save Stremio progress for %s: %s",
                self.media.media_id,
                safe_error(err),
            )


@callback
def vlc_title(state: State | None) -> str | None:
    """VLC's current media_title on an Apple TV, if VLC is playing."""
    return state.attributes.get("media_title") if _is_vlc(state) else None


@callback
def async_start_tracking(
    hass: HomeAssistant,
    client: Any,
    entity_id: str,
    media: TrackedMedia,
    title_before: str | None = None,
    on_saved: Callable[[], None] | None = None,
) -> PlaybackTracker:
    """Track a new VLC session on entity_id, saving and replacing any earlier one."""
    trackers: dict[str, PlaybackTracker] = hass.data.setdefault(DATA_TRACKERS, {})
    if (old := trackers.pop(entity_id, None)) is not None:
        old._finish(save=True)
    tracker = PlaybackTracker(hass, client, entity_id, media, on_saved)
    trackers[entity_id] = tracker
    tracker.start(title_before)
    return tracker
