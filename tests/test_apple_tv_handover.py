"""Tests for Apple TV handover helpers."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest

from custom_components.stremio.apple_tv_handover import (
    HandoverManager,
    HandoverMethod,
    redact_url,
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
