"""Tests for Apple TV handover helpers."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest

from custom_components.stremio.apple_tv_handover import (
    VLC_APP_ID,
    VLC_LAUNCH_CHECK,
    VLC_LAUNCH_RETRIES,
    HandoverError,
    HandoverManager,
    HandoverMethod,
    redact_url,
    safe_error,
)

VLC_PREFIX = "vlc-x-callback://x-callback-url/stream?url="
HANDOVER_LOGGER = "custom_components.stremio.apple_tv_handover"


def _manager() -> HandoverManager:
    return HandoverManager(MagicMock())


class TestGenerateVlcDeepLink:
    """Tests for the VLC x-callback link."""

    def test_uses_x_callback_scheme(self):
        link = _manager().generate_vlc_deep_link("https://example.com/a.mkv")
        assert link.startswith(VLC_PREFIX)

    @pytest.mark.parametrize("char", ["/", "?", "&", "=", ":"])
    def test_encodes_reserved_characters(self, char):
        url = f"https://example.com/a{char}b"
        encoded = _manager().generate_vlc_deep_link(url)[len(VLC_PREFIX) :]
        assert char not in encoded

    def test_round_trips_through_query_string(self):
        url = "https://host/path/file.mkv?token=a&b=c:d/e+f%20g"
        link = _manager().generate_vlc_deep_link(url)
        assert parse_qs(urlsplit(link).query)["url"] == [url]

    def test_debug_log_has_length_not_url(self, caplog):
        caplog.set_level(logging.DEBUG, logger=HANDOVER_LOGGER)
        url = "https://debrid.example/SECRETPATH/movie.mkv?token=SECRETQUERY"
        link = _manager().generate_vlc_deep_link(url)

        assert "SECRETPATH" not in caplog.text
        assert "SECRETQUERY" not in caplog.text
        assert str(len(link)) in caplog.text


class TestRedactUrl:
    """Tests for log redaction of stream URLs."""

    def test_keeps_host_and_length_only(self):
        url = "https://debrid.example.com/abc/TOKEN?k=SECRET"
        out = redact_url(url)
        assert "debrid.example.com" in out
        assert "TOKEN" not in out
        assert "SECRET" not in out
        assert f"len={len(url)}" in out

    @pytest.mark.parametrize("value", ["", None])
    def test_empty(self, value):
        assert redact_url(value) == "<empty>"


class TestHandoverViaVlcLogging:
    """Stream URLs must not reach the logs during a VLC handover."""

    async def test_handover_logs_no_path_or_query(self, caplog):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock()
        hass.services.async_call = AsyncMock()
        caplog.set_level(logging.DEBUG, logger=HANDOVER_LOGGER)

        url = "https://debrid.example/SECRETPATH/movie.mkv?token=SECRETQUERY"
        await HandoverManager(hass).handover_via_vlc(
            "media_player.bedroom_apple_tv", url
        )

        assert "SECRETPATH" not in caplog.text
        assert "SECRETQUERY" not in caplog.text
        media_content_id = hass.services.async_call.call_args.args[2][
            "media_content_id"
        ]
        assert media_content_id.startswith(VLC_PREFIX)


class TestRecommendedMethod:
    """Tests for auto method selection."""

    @pytest.mark.parametrize("pyatv_available", [True, False])
    @pytest.mark.parametrize("url", ["https://x/a.mkv", "https://x/a.webm"])
    def test_mkv_and_webm_use_vlc(self, url, pyatv_available):
        with patch(
            "custom_components.stremio.apple_tv_handover.PYATV_AVAILABLE",
            pyatv_available,
        ):
            assert _manager().get_recommended_method(url) == HandoverMethod.VLC

    def test_hls_still_uses_airplay_when_pyatv_available(self):
        with patch("custom_components.stremio.apple_tv_handover.PYATV_AVAILABLE", True):
            assert (
                _manager().get_recommended_method("https://x/a.m3u8")
                == HandoverMethod.AIRPLAY
            )


class TestSafeError:
    """Error text must never carry a URL (deep links embed debrid tokens)."""

    def test_strips_deep_link_and_stream_url(self):
        err = RuntimeError(
            "Could not resolve ['vlc-x-callback://x-callback-url/stream?url="
            "https%3A%2F%2Fdebrid.example%2FTOKEN%2Fa.mkv'] or https://x.example/TOKEN"
        )
        text = safe_error(err)
        assert "://" not in text
        assert "TOKEN" not in text
        assert text.startswith("RuntimeError: ")
        assert "<redacted-url>" in text

    def test_plain_message_kept(self):
        assert safe_error(HandoverError("launch_app is not supported")) == (
            "launch_app is not supported"
        )


def _vlc_hass(states):
    """Hass mock whose entity state walks through `states` on each read.

    Each entry is a state string or a (state, app_id) tuple.
    """
    hass = MagicMock()
    seq = iter(states)
    last = {"value": states[-1]}

    def _get(_entity_id):
        try:
            last["value"] = next(seq)
        except StopIteration:
            pass
        value = last["value"]
        state, app_id = value if isinstance(value, tuple) else (value, None)
        return MagicMock(state=state, attributes={"app_id": app_id})

    hass.states.get.side_effect = _get
    hass.services.async_call = AsyncMock()
    return hass


class TestHandoverViaVlcErrors:
    """VLC handover failures name the target but never the link."""

    async def test_error_has_entity_but_no_url(self):
        hass = _vlc_hass(["idle"])
        hass.services.async_call.side_effect = RuntimeError(
            "Could not resolve ['vlc-x-callback://x-callback-url/stream?url=SECRET']"
        )
        with pytest.raises(HandoverError) as err:
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv", "https://debrid.example/SECRET/a.mkv"
            )
        assert "media_player.media_apple_tv" in str(err.value)
        assert "://" not in str(err.value)
        assert "SECRET" not in str(err.value)


class TestHandoverViaVlcWake:
    """A sleeping Apple TV is woken, and VLC waits for it to settle."""

    async def test_awake_apple_tv_is_not_turned_on(self):
        hass = _vlc_hass(["idle"])
        with patch("asyncio.sleep", AsyncMock()) as sleep:
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv", "https://files.example/a.mp4"
            )
        services = [c.args[1] for c in hass.services.async_call.call_args_list]
        assert services == ["play_media"]
        sleep.assert_not_called()

    async def test_sleeping_apple_tv_is_woken_before_vlc(self):
        # off on the initial check, off once while waking, awake, then VLC opens
        hass = _vlc_hass(["off", "off", "idle", ("playing", VLC_APP_ID)])
        with patch("asyncio.sleep", AsyncMock()) as sleep:
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv",
                "https://files.example/a.mp4",
                wake_delay=3,
            )
        services = [c.args[1] for c in hass.services.async_call.call_args_list]
        assert services == ["turn_on", "play_media"]
        # one poll second while still off, the settle delay, one VLC check
        assert [c.args[0] for c in sleep.call_args_list] == [1, 3, 1]

    async def test_launch_resent_when_vlc_does_not_open(self):
        # awake, but tvOS drops the first launch; VLC opens after the resend
        hass = _vlc_hass(
            ["off", "idle"] + ["idle"] * VLC_LAUNCH_CHECK + [("playing", VLC_APP_ID)]
        )
        with patch("asyncio.sleep", AsyncMock()):
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv", "https://files.example/a.mp4"
            )
        services = [c.args[1] for c in hass.services.async_call.call_args_list]
        assert services == ["turn_on", "play_media", "play_media"]

    async def test_launch_retries_are_limited(self):
        hass = _vlc_hass(["off", "idle"])
        with patch("asyncio.sleep", AsyncMock()):
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv", "https://files.example/a.mp4"
            )
        services = [c.args[1] for c in hass.services.async_call.call_args_list]
        assert services == ["turn_on"] + ["play_media"] * (1 + VLC_LAUNCH_RETRIES)

    async def test_wake_timeout_still_tries_vlc(self, caplog):
        hass = _vlc_hass(["standby"])
        caplog.set_level(logging.WARNING, logger=HANDOVER_LOGGER)
        with patch("asyncio.sleep", AsyncMock()), patch(
            "custom_components.stremio.apple_tv_handover.WAKE_TIMEOUT", 0
        ):
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv",
                "https://files.example/a.mp4",
                wake_delay=0,
            )
        services = [c.args[1] for c in hass.services.async_call.call_args_list]
        assert services[:2] == ["turn_on", "play_media"]
        assert "still reports asleep" in caplog.text

    async def test_turn_on_failure_has_no_url(self):
        hass = _vlc_hass(["off"])
        hass.services.async_call.side_effect = RuntimeError("boom https://x.example/T")
        with pytest.raises(HandoverError) as err:
            await HandoverManager(hass).handover_via_vlc(
                "media_player.media_apple_tv", "https://files.example/a.mp4"
            )
        assert "Could not turn on" in str(err.value)
        assert "://" not in str(err.value)
