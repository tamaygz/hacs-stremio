"""Helpers for updating playback state via services."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SERVICE_SET_CURRENTLY_WATCHING

_LOGGER = logging.getLogger(__name__)


async def async_update_playback_state_after_handover(
    hass: HomeAssistant,
    media_id: str | None,
    media_type: str | None,
    season: int | None,
    episode: int | None,
    progress: int | None,
    duration: int | None,
) -> None:
    """Update playback state after a handover operation."""
    payload = {
        "media_id": media_id,
        "media_type": media_type or "movie",
        "season": season,
        "episode": episode,
        "progress": progress,
        "duration": duration,
        "fallback_to_watched": True,
    }
    filtered_payload = {
        key: value for key, value in payload.items() if value is not None
    }

    if not filtered_payload.get("media_id"):
        return

    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CURRENTLY_WATCHING,
            filtered_payload,
            blocking=True,
        )
    except HomeAssistantError as err:
        _LOGGER.warning("Failed to update playback state after handover: %s", err)
