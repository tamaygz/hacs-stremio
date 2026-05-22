"""Helpers for updating playback state via services."""

from __future__ import annotations

import logging

from .stremio_client import StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)


async def async_update_playback_state_after_handover(
    client: StremioClient,
    media_id: str | None,
    media_type: str | None,
    season: int | None,
    episode: int | None,
    progress: int | None,
    duration: int | None,
) -> None:
    """Update playback state after a handover operation."""
    if not media_id:
        return

    resolved_media_type = media_type or "movie"

    try:
        success = await client.async_set_currently_watching(
            media_id=media_id,
            media_type=resolved_media_type,
            season=season,
            episode=episode,
            progress=progress,
            duration=duration,
        )
        if not success:
            _LOGGER.warning(
                "Set currently watching failed after handover; falling back to mark watched"
            )
            await client.async_mark_watched(
                media_id=media_id,
                media_type=resolved_media_type,
                season=season,
                episode=episode,
                progress=progress,
                duration=duration,
            )
    except StremioConnectionError as err:
        _LOGGER.warning("Failed to update playback state after handover: %s", err)
