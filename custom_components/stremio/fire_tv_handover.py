"""Fire TV Handover module for Stremio integration.

Unlike the Apple TV handover (which AirPlays a resolved stream URL via pyatv,
because tvOS has no usable Stremio deep link), Fire OS ships the Stremio Android
app, which registers the ``stremio://`` URI scheme. So the Fire TV handover is
fundamentally simpler and better: we don't resolve a stream at all — we open the
Stremio app directly to the title via a deep link, and because the Fire TV's
Stremio is signed into the same account, playback position syncs (continue
watching resumes where you left off).

Mechanism: build a ``stremio://`` deep link and fire it as an Android
``VIEW`` intent. Rather than opening a second ADB connection (which would
contend with the ``androidtv`` integration that already holds one to the Fire
TV), we delegate to that integration's ``androidtv.adb_command`` service. The
Fire TV device is therefore any entity managed by ``androidtv``.

Deep-link format (the triple slash is load-bearing — ``stremio://detail/...``
parses "detail" as the URI host and drops the path, landing on the app home)::

    movie:            stremio:///detail/movie/<imdb_id>/<imdb_id>
    series (show):    stremio:///detail/series/<imdb_id>/<imdb_id>
    series (episode): stremio:///detail/series/<imdb_id>/<imdb_id>:<season>:<episode>

The ``<imdb_id>:<season>:<episode>`` video id mirrors the identifier the
integration already builds for stream lookups (see ``stremio_client``).
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

ANDROIDTV_DOMAIN = "androidtv"
ANDROIDTV_ADB_COMMAND_SERVICE = "adb_command"

# Android implicit intent that opens a URI in whichever app registers its scheme.
_INTENT_ACTION_VIEW = "android.intent.action.VIEW"


class FireTVHandoverError(HomeAssistantError):
    """Error during a Fire TV handover operation."""


def build_deep_link(
    media_type: str,
    media_id: str,
    season: int | None = None,
    episode: int | None = None,
) -> str:
    """Build a Stremio ``stremio://`` deep link for a title.

    Args:
        media_type: "movie" or "series".
        media_id: IMDb id (e.g. "tt12637874") or other Stremio meta id.
        season: Season number (series only; requires ``episode``).
        episode: Episode number (series only; requires ``season``).

    Returns:
        A ``stremio:///detail/...`` URI. For a series with both season and
        episode, the deep link targets that episode; otherwise the show page.

    Raises:
        FireTVHandoverError: If ``media_type`` is not "movie"/"series", or
            ``media_id`` is empty.
    """
    if media_type not in ("movie", "series"):
        raise FireTVHandoverError(
            f"Unsupported media_type '{media_type}' (expected 'movie' or 'series')"
        )
    if not media_id:
        raise FireTVHandoverError("media_id is required to build a deep link")

    if media_type == "series" and season is not None and episode is not None:
        video_id = f"{media_id}:{season}:{episode}"
    else:
        video_id = media_id

    # Triple slash: empty authority so the whole route lands in the URI path.
    return f"stremio:///detail/{media_type}/{media_id}/{video_id}"


def build_adb_command(uri: str) -> str:
    """Build the ``am start`` shell command that fires the deep link."""
    return f'am start -a {_INTENT_ACTION_VIEW} -d "{uri}"'


class FireTVHandoverManager:
    """Opens Stremio deep links on a Fire TV via the ``androidtv`` integration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager.

        Args:
            hass: Home Assistant instance.
        """
        self.hass = hass

    async def async_handover(
        self,
        device_entity_id: str,
        media_type: str,
        media_id: str,
        season: int | None = None,
        episode: int | None = None,
    ) -> dict[str, str]:
        """Open a title in Stremio on the given Fire TV.

        Args:
            device_entity_id: An ``androidtv`` entity (media_player.* or
                remote.*) pointing at the Fire TV.
            media_type: "movie" or "series".
            media_id: IMDb id of the title.
            season: Season number (series episode target).
            episode: Episode number (series episode target).

        Returns:
            A dict with the ``uri``, ``command`` and ``device_id`` used.

        Raises:
            FireTVHandoverError: If the androidtv integration/service is not
                available, or the ADB command fails.
        """
        if not self.hass.services.has_service(
            ANDROIDTV_DOMAIN, ANDROIDTV_ADB_COMMAND_SERVICE
        ):
            raise FireTVHandoverError(
                "The 'androidtv' integration is not set up, so no Fire TV is "
                "reachable. Add your Fire TV via the Android TV / Fire TV "
                "integration first."
            )

        uri = build_deep_link(media_type, media_id, season, episode)
        command = build_adb_command(uri)

        _LOGGER.info(
            "Fire TV handover: device=%s uri=%s", device_entity_id, uri
        )

        try:
            await self.hass.services.async_call(
                ANDROIDTV_DOMAIN,
                ANDROIDTV_ADB_COMMAND_SERVICE,
                {"entity_id": device_entity_id, "command": command},
                blocking=True,
            )
        except Exception as err:
            # androidtv surfaces a missing entity, an offline device or an ADB
            # failure as a variety of exception types — wrap them uniformly.
            raise FireTVHandoverError(
                f"Failed to send deep link to {device_entity_id}: {err}"
            ) from err

        return {"uri": uri, "command": command, "device_id": device_entity_id}
