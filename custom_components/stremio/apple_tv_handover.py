"""Apple TV Handover module for Stremio integration.

This module provides functionality to send Stremio streams to Apple TV devices
using either AirPlay (via pyatv) or VLC deep links as a fallback.
"""
from __future__ import annotations

import asyncio
import logging
import re
from enum import Enum
from typing import Any
from urllib.parse import quote, urlencode

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

# Try to import pyatv, but handle if not installed
try:
    import pyatv
    from pyatv.const import Protocol
    PYATV_AVAILABLE = True
except ImportError:
    PYATV_AVAILABLE = False
    _LOGGER.warning("pyatv not installed, AirPlay handover will not be available")


class HandoverMethod(Enum):
    """Handover method enumeration."""

    AUTO = "auto"
    AIRPLAY = "airplay"
    VLC = "vlc"


class StreamFormat(Enum):
    """Stream format enumeration."""

    HLS = "hls"  # HTTP Live Streaming (.m3u8)
    MP4 = "mp4"  # MPEG-4 video
    MKV = "mkv"  # Matroska video
    WEBM = "webm"  # WebM video
    UNKNOWN = "unknown"


class HandoverError(HomeAssistantError):
    """Error during handover operation."""


class DeviceNotFoundError(HandoverError):
    """Apple TV device not found."""


class ConnectionError(HandoverError):
    """Connection to Apple TV failed."""


class UnsupportedFormatError(HandoverError):
    """Stream format not supported for handover method."""


class HandoverManager:
    """Manages handover of streams to Apple TV devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the HandoverManager.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._discovered_devices: dict[str, Any] = {}
        self._discovery_lock = asyncio.Lock()

    @staticmethod
    def detect_stream_format(url: str) -> StreamFormat:
        """Detect the format of a stream URL.

        Args:
            url: The stream URL to analyze

        Returns:
            StreamFormat enum indicating the detected format
        """
        url_lower = url.lower()

        # Check for HLS
        if ".m3u8" in url_lower or "hls" in url_lower:
            return StreamFormat.HLS

        # Check for MP4
        if ".mp4" in url_lower:
            return StreamFormat.MP4

        # Check for MKV
        if ".mkv" in url_lower:
            return StreamFormat.MKV

        # Check for WebM
        if ".webm" in url_lower:
            return StreamFormat.WEBM

        # Check common streaming patterns
        if re.search(r"manifest|playlist|index", url_lower):
            return StreamFormat.HLS

        return StreamFormat.UNKNOWN

    def get_recommended_method(self, stream_url: str) -> HandoverMethod:
        """Get the recommended handover method for a stream.

        Args:
            stream_url: The stream URL

        Returns:
            Recommended HandoverMethod
        """
        stream_format = self.detect_stream_format(stream_url)

        # HLS works well with AirPlay
        if stream_format == StreamFormat.HLS and PYATV_AVAILABLE:
            return HandoverMethod.AIRPLAY

        # For MKV and other formats, VLC is more reliable
        if stream_format in (StreamFormat.MKV, StreamFormat.WEBM):
            return HandoverMethod.VLC

        # MP4 can work with either, prefer AirPlay if available
        if stream_format == StreamFormat.MP4 and PYATV_AVAILABLE:
            return HandoverMethod.AIRPLAY

        # Default to VLC for unknown formats
        return HandoverMethod.VLC

    async def discover_apple_tv_devices(
        self, timeout: float = 5.0
    ) -> dict[str, Any]:
        """Discover Apple TV devices on the network.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            Dictionary mapping device names to device info

        Raises:
            HandoverError: If pyatv is not available
        """
        if not PYATV_AVAILABLE:
            raise HandoverError("pyatv library not installed")

        async with self._discovery_lock:
            _LOGGER.debug("Discovering Apple TV devices (timeout: %ss)", timeout)

            try:
                devices = await pyatv.scan(
                    self.hass.loop,
                    timeout=timeout,
                )

                self._discovered_devices = {}
                for device in devices:
                    device_info = {
                        "name": device.name,
                        "address": str(device.address),
                        "identifier": device.identifier,
                        "device_info": device.device_info,
                        "services": [str(s.protocol) for s in device.services],
                    }
                    self._discovered_devices[device.name] = device_info
                    _LOGGER.debug("Found Apple TV: %s at %s", device.name, device.address)

                _LOGGER.info("Discovered %d Apple TV device(s)", len(self._discovered_devices))
                return self._discovered_devices

            except Exception as err:
                _LOGGER.error("Error discovering Apple TV devices: %s", err)
                raise HandoverError(f"Discovery failed: {err}") from err

    async def get_device_by_name(self, device_name: str) -> Any:
        """Get an Apple TV device configuration by name.

        Args:
            device_name: Name of the Apple TV device

        Returns:
            pyatv device configuration

        Raises:
            DeviceNotFoundError: If device not found
        """
        if not PYATV_AVAILABLE:
            raise HandoverError("pyatv library not installed")

        # Try discovery if we don't have the device cached
        if device_name not in self._discovered_devices:
            await self.discover_apple_tv_devices()

        if device_name not in self._discovered_devices:
            raise DeviceNotFoundError(f"Apple TV '{device_name}' not found")

        # Re-scan to get fresh device config for connection
        devices = await pyatv.scan(
            self.hass.loop,
            identifier=self._discovered_devices[device_name]["identifier"],
            timeout=5.0,
        )

        if not devices:
            raise DeviceNotFoundError(f"Apple TV '{device_name}' no longer available")

        return devices[0]

    async def handover_via_airplay(
        self,
        device_name: str,
        stream_url: str,
        title: str | None = None,
    ) -> bool:
        """Send stream to Apple TV via AirPlay.

        Args:
            device_name: Name of the target Apple TV
            stream_url: URL of the stream to play
            title: Optional title for the stream

        Returns:
            True if handover was successful

        Raises:
            HandoverError: If handover fails
            DeviceNotFoundError: If device not found
        """
        if not PYATV_AVAILABLE:
            raise HandoverError("pyatv library not installed for AirPlay")

        _LOGGER.info(
            "Starting AirPlay handover to '%s': %s",
            device_name,
            stream_url[:100],
        )

        try:
            # Get device configuration
            device_config = await self.get_device_by_name(device_name)

            # Connect to device
            atv = await pyatv.connect(device_config, self.hass.loop)

            try:
                # Check if AirPlay is available
                if not atv.features.in_state(
                    pyatv.interface.FeatureState.Available,
                    pyatv.interface.FeatureName.PlayUrl,
                ):
                    raise HandoverError("AirPlay streaming not available on this device")

                # Stream the URL
                await atv.stream.play_url(stream_url)
                _LOGGER.info("Successfully started AirPlay stream to '%s'", device_name)
                return True

            finally:
                # Always close the connection
                atv.close()

        except DeviceNotFoundError:
            raise
        except HandoverError:
            raise
        except Exception as err:
            _LOGGER.error("AirPlay handover failed: %s", err)
            raise ConnectionError(f"AirPlay handover failed: {err}") from err

    def generate_vlc_deep_link(
        self,
        stream_url: str,
        title: str | None = None,
        subtitle_url: str | None = None,
    ) -> str:
        """Generate a VLC deep link URL.

        Args:
            stream_url: URL of the stream to play
            title: Optional title for display
            subtitle_url: Optional subtitle file URL

        Returns:
            VLC deep link URL
        """
        # VLC URL scheme: vlc-x-callback://x-callback-url/stream?url=...
        base_url = "vlc-x-callback://x-callback-url/stream"

        params = {
            "url": stream_url,
        }

        if title:
            params["title"] = title

        if subtitle_url:
            params["sub"] = subtitle_url

        # Build the URL with proper encoding
        deep_link = f"{base_url}?{urlencode(params, quote_via=quote)}"

        _LOGGER.debug("Generated VLC deep link: %s", deep_link[:100])
        return deep_link

    async def handover_via_vlc(
        self,
        device_entity_id: str,
        stream_url: str,
        title: str | None = None,
        subtitle_url: str | None = None,
    ) -> bool:
        """Send stream to device via VLC deep link.

        This uses Home Assistant's media_player service to send the VLC deep link
        to the target device (typically an Apple TV with VLC installed).

        Args:
            device_entity_id: Entity ID of the target media player
            stream_url: URL of the stream to play
            title: Optional title for display
            subtitle_url: Optional subtitle file URL

        Returns:
            True if the deep link was sent

        Raises:
            HandoverError: If handover fails
        """
        _LOGGER.info(
            "Starting VLC handover to '%s': %s",
            device_entity_id,
            stream_url[:100],
        )

        try:
            vlc_url = self.generate_vlc_deep_link(stream_url, title, subtitle_url)

            # Use media_player service to send the deep link
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": device_entity_id,
                    "media_content_type": "url",
                    "media_content_id": vlc_url,
                },
                blocking=True,
            )

            _LOGGER.info("Successfully sent VLC deep link to '%s'", device_entity_id)
            return True

        except Exception as err:
            _LOGGER.error("VLC handover failed: %s", err)
            raise HandoverError(f"VLC handover failed: {err}") from err

    async def handover(
        self,
        device_identifier: str,
        stream_url: str,
        method: HandoverMethod | str = HandoverMethod.AUTO,
        title: str | None = None,
        subtitle_url: str | None = None,
    ) -> dict[str, Any]:
        """Perform handover to Apple TV using the specified method.

        Args:
            device_identifier: Device name (for AirPlay) or entity_id (for VLC)
            stream_url: URL of the stream to play
            method: Handover method to use
            title: Optional title for display
            subtitle_url: Optional subtitle URL

        Returns:
            Dictionary with handover result info

        Raises:
            HandoverError: If handover fails
        """
        # Convert string to enum if needed
        if isinstance(method, str):
            method = HandoverMethod(method.lower())

        # Auto-detect method if needed
        if method == HandoverMethod.AUTO:
            method = self.get_recommended_method(stream_url)
            _LOGGER.debug("Auto-detected handover method: %s", method.value)

        stream_format = self.detect_stream_format(stream_url)
        result = {
            "method": method.value,
            "stream_format": stream_format.value,
            "device": device_identifier,
            "success": False,
        }

        try:
            if method == HandoverMethod.AIRPLAY:
                if not PYATV_AVAILABLE:
                    _LOGGER.warning("AirPlay unavailable, falling back to VLC")
                    method = HandoverMethod.VLC
                else:
                    await self.handover_via_airplay(device_identifier, stream_url, title)
                    result["success"] = True
                    result["method"] = "airplay"
                    return result

            if method == HandoverMethod.VLC:
                await self.handover_via_vlc(
                    device_identifier, stream_url, title, subtitle_url
                )
                result["success"] = True
                result["method"] = "vlc"
                return result

        except Exception as err:
            result["error"] = str(err)
            raise

        return result
