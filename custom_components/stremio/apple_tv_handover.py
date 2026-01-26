"""Apple TV Handover module for Stremio integration.

This module provides functionality to send Stremio streams to Apple TV devices.

IMPORTANT: tvOS has significant limitations for URL schemes and deep links:
- VLC deep links (vlc://, vlc-x-callback://) do NOT work on tvOS
- Only certain apps support deep links (YouTube, Netflix, Disney+, etc.)
- Generic HTTP/HTTPS URLs can only be played via:
  1. AirPlay using pyatv library (recommended)
  2. Direct playback for HLS/MP4 streams (limited support)

The recommended approach is AirPlay via pyatv, which uses the native player
and supports HLS (.m3u8) and MP4 streams.
"""

from __future__ import annotations

import asyncio
import logging
import re
from enum import Enum
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

# Try to import pyatv, but handle if not installed or incompatible
try:
    import pyatv

    PYATV_AVAILABLE = True
except (ImportError, Exception) as e:
    PYATV_AVAILABLE = False
    _LOGGER.warning("pyatv not installed or not compatible, AirPlay handover will not be available: %s", e)


class HandoverMethod(Enum):
    """Handover method enumeration."""

    AUTO = "auto"
    AIRPLAY = "airplay"
    VLC = "vlc"
    DIRECT = "direct"


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


class AppleTVConnectionError(HandoverError):
    """Connection to Apple TV failed."""


class UnsupportedFormatError(HandoverError):
    """Stream format not supported for handover method."""


class HandoverManager:
    """Manages handover of streams to Apple TV devices."""

    # Content types that Apple TV native player supports
    SUPPORTED_CONTENT_TYPES = {
        StreamFormat.HLS: "application/x-mpegURL",
        StreamFormat.MP4: "video/mp4",
    }

    def __init__(
        self,
        hass: HomeAssistant,
        credentials: str | None = None,
        device_identifier: str | None = None,
    ) -> None:
        """Initialize the HandoverManager.

        Args:
            hass: Home Assistant instance
            credentials: Optional stored AirPlay credentials from pairing
            device_identifier: Optional device identifier for faster reconnection
        """
        self.hass = hass
        self._discovered_devices: dict[str, Any] = {}
        self._discovery_lock = asyncio.Lock()
        self._credentials = credentials
        self._device_identifier = device_identifier

    @staticmethod
    def validate_stream_url(url: str) -> tuple[bool, str | None]:
        """Validate a stream URL for handover.

        Args:
            url: The stream URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "Stream URL is empty"

        if not url.startswith(("http://", "https://")):
            return (
                False,
                f"Invalid URL scheme. Expected http:// or https://, got: {url[:50]}",
            )

        # Check for common problematic patterns
        if "localhost" in url or "127.0.0.1" in url:
            return False, "Localhost URLs are not accessible from Apple TV"

        if "192.168." in url or "10.0." in url or "172.16." in url:
            # Local network - this is fine, just log a debug message
            _LOGGER.debug("Stream URL is on local network: %s", url[:100])

        return True, None

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

        For Apple TV streaming, the options are:
        1. AIRPLAY (recommended) - Uses pyatv to stream directly via AirPlay protocol
           - Works with HLS (.m3u8) and MP4 streams
           - Most reliable method
           - Requires pyatv library to be installed

        2. DIRECT - Uses media_player.play_media with the raw URL
           - May work for some HLS streams
           - Less reliable than AirPlay

        3. VLC - Does NOT work on tvOS!
           - tvOS does not support VLC URL schemes
           - Kept for compatibility but will fail

        Args:
            stream_url: The stream URL

        Returns:
            Recommended HandoverMethod
        """
        stream_format = self.detect_stream_format(stream_url)

        # Always prefer AirPlay if pyatv is available - it's the most reliable
        if PYATV_AVAILABLE:
            if stream_format in (StreamFormat.HLS, StreamFormat.MP4):
                return HandoverMethod.AIRPLAY

        # Fall back to DIRECT for HLS/MP4 if pyatv not available
        if stream_format in (StreamFormat.HLS, StreamFormat.MP4):
            return HandoverMethod.DIRECT

        # For MKV and WebM formats:
        # - VLC deep links do NOT work on tvOS
        # - AirPlay via pyatv is the only option that might work
        # - Direct playback will likely fail (unsupported format)
        if stream_format in (StreamFormat.MKV, StreamFormat.WEBM):
            if PYATV_AVAILABLE:
                _LOGGER.warning(
                    "MKV/WebM format detected. AirPlay may not support this format. "
                    "Consider using an HLS or MP4 stream instead."
                )
                return HandoverMethod.AIRPLAY
            else:
                _LOGGER.warning(
                    "MKV/WebM format detected but pyatv not installed. "
                    "Handover will likely fail. Install pyatv for AirPlay support."
                )
                return HandoverMethod.DIRECT

        # Default to AirPlay if available, otherwise DIRECT
        if PYATV_AVAILABLE:
            return HandoverMethod.AIRPLAY
        return HandoverMethod.DIRECT

    async def discover_apple_tv_devices(self, timeout: float = 5.0) -> dict[str, Any]:
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
                    timeout=int(timeout),
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
                    _LOGGER.debug(
                        "Found Apple TV: %s at %s", device.name, device.address
                    )

                _LOGGER.info(
                    "Discovered %d Apple TV device(s)", len(self._discovered_devices)
                )
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
            timeout=5,
        )

        if not devices:
            raise DeviceNotFoundError(f"Apple TV '{device_name}' no longer available")

        return devices[0]

    async def _check_airplay_feature(self, atv: Any) -> bool:
        """Check if AirPlay (PlayUrl) feature is available.

        This helper method handles multiple pyatv API versions and implementations.
        It attempts to check the feature state in the following order:
        1. Try modern API with FeatureState and FeatureName enums
        2. Try alternative attribute names
        3. Fall back to assuming available if API check fails

        Args:
            atv: PyATV device instance

        Returns:
            True if AirPlay is available, False otherwise
        """
        if not hasattr(atv, "features"):
            _LOGGER.debug(
                "Device does not have 'features' attribute, assuming AirPlay available"
            )
            return True

        # Try modern pyatv API (FeatureState and FeatureName enums)
        try:
            if hasattr(pyatv, "FeatureState") and hasattr(pyatv, "FeatureName"):
                feature_available = atv.features.in_state(
                    pyatv.FeatureState.Available,  # type: ignore[attr-defined]
                    pyatv.FeatureName.PlayUrl,  # type: ignore[attr-defined]
                )
                _LOGGER.debug(
                    "Checked AirPlay feature using modern API: %s", feature_available
                )
                return feature_available
        except (AttributeError, TypeError) as err:
            _LOGGER.debug(
                "Modern pyatv API check failed (%s), trying alternatives", err
            )

        # Try alternative: check if features has a PlayUrl attribute directly
        try:
            if hasattr(atv.features, "play_url"):
                play_url_feature = atv.features.play_url
                if hasattr(play_url_feature, "available"):
                    _LOGGER.debug("Checked AirPlay via play_url.available attribute")
                    return play_url_feature.available
        except (AttributeError, TypeError) as err:
            _LOGGER.debug(
                "Alternative pyatv API check failed (%s), trying feature list", err
            )

        # Try checking feature list
        try:
            if hasattr(atv.features, "get_feature"):
                # Some versions might have this method
                feature = atv.features.get_feature("play_url")  # type: ignore[union-attr]
                if feature is not None:
                    _LOGGER.debug("Found PlayUrl feature via get_feature method")
                    return True
        except (AttributeError, TypeError) as err:
            _LOGGER.debug(
                "Feature list check failed (%s), assuming AirPlay available", err
            )

        # Last resort: log and assume available
        _LOGGER.warning(
            "Could not determine AirPlay feature availability for pyatv, assuming available"
        )
        return True

    async def handover_via_airplay(
        self,
        device_name: str,
        stream_url: str,
        title: str | None = None,
        credentials: str | None = None,
    ) -> bool:
        """Send stream to Apple TV via AirPlay.

        Args:
            device_name: Name of the target Apple TV
            stream_url: URL of the stream to play
            title: Optional title for the stream
            credentials: Optional AirPlay credentials (overrides stored credentials)

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

        # Use provided credentials, fall back to stored credentials
        airplay_credentials = credentials or self._credentials

        try:
            # Get device configuration
            device_config = await self.get_device_by_name(device_name)

            # Apply stored credentials if available
            if airplay_credentials:
                from pyatv.const import Protocol

                _LOGGER.debug("Using stored AirPlay credentials for '%s'", device_name)
                device_config.set_credentials(Protocol.AirPlay, airplay_credentials)

            # Connect to device
            atv = await pyatv.connect(device_config, self.hass.loop)

            try:
                # Check if AirPlay (PlayUrl) is available on the device
                # This implementation handles multiple pyatv API versions
                feature_available = await self._check_airplay_feature(atv)

                if not feature_available:
                    raise HandoverError(
                        "AirPlay streaming not available on this device"
                    )

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
            raise AppleTVConnectionError(f"AirPlay handover failed: {err}") from err

    def generate_vlc_deep_link(
        self,
        stream_url: str,
        title: str | None = None,
        subtitle_url: str | None = None,
    ) -> str:
        """Generate a VLC deep link URL.

        WARNING: VLC deep links (vlc://, vlc-x-callback://) do NOT work on tvOS!
        This is a known platform limitation. The tvOS version of VLC does not
        expose URL schemes the same way the iOS version does.

        This method is kept for potential future compatibility or iOS use cases,
        but will NOT work for Apple TV handover.

        For Apple TV, use the AirPlay method instead.

        Args:
            stream_url: URL of the stream to play
            title: Optional title for display (not used)
            subtitle_url: Optional subtitle file URL (not used)

        Returns:
            VLC deep link URL (note: won't work on tvOS)
        """
        # Note: Neither vlc:// nor vlc-x-callback:// work on tvOS
        # Keeping this for reference but it will not work
        deep_link = f"vlc://{stream_url}"

        _LOGGER.warning(
            "VLC deep links do NOT work on tvOS. Use AirPlay method instead. "
            "Generated URL (will likely fail): %s",
            deep_link[:100],
        )
        return deep_link

    async def handover_via_vlc(
        self,
        device_entity_id: str,
        stream_url: str,
        title: str | None = None,
        subtitle_url: str | None = None,
    ) -> bool:
        """Attempt to send stream to Apple TV via VLC deep link.

        WARNING: This method will likely NOT work on tvOS!
        VLC deep links are not supported on tvOS - this is a known platform limitation.
        The tvOS version of VLC does not expose URL schemes.

        Use AirPlay method (handover_via_airplay) for reliable Apple TV streaming.

        Args:
            device_entity_id: Entity ID of the target media player
            stream_url: URL of the stream to play
            title: Optional title for display
            subtitle_url: Optional subtitle file URL

        Returns:
            True if the command was sent (but playback may not start)

        Raises:
            HandoverError: If handover fails
        """
        _LOGGER.warning(
            "Attempting VLC handover to '%s' - NOTE: VLC deep links do NOT work "
            "on tvOS. Use AirPlay method for reliable streaming.",
            device_entity_id,
        )

        # Validate entity_id format
        if not device_entity_id or not device_entity_id.startswith("media_player."):
            raise HandoverError(
                f"Invalid entity_id '{device_entity_id}'. VLC handover requires a valid "
                "media_player entity_id (e.g., media_player.apple_tv_living_room). "
                "Use AirPlay method for device name based handover, or provide the "
                "correct entity_id for VLC."
            )

        # Check if entity exists
        state = self.hass.states.get(device_entity_id)
        if state is None:
            raise HandoverError(
                f"Entity '{device_entity_id}' not found. Please check the entity_id "
                "in Home Assistant's Entities page."
            )

        try:
            vlc_url = self.generate_vlc_deep_link(stream_url, title, subtitle_url)

            # Use media_player.play_media to open VLC with the stream
            # The Apple TV integration will handle opening VLC via deep link
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

    async def handover_direct(
        self,
        device_entity_id: str,
        stream_url: str,
    ) -> bool:
        """Send stream URL directly to Apple TV's native player.

        This attempts to play the stream URL directly on Apple TV without
        using VLC. Works best with HLS (.m3u8) and MP4 streams.

        Note: The Apple TV integration uses HTTP GET to verify URLs before
        playback, which can fail (500 error) if:
        - The URL requires special headers or authentication
        - The server doesn't respond to HEAD/GET requests properly
        - The stream format isn't natively supported

        Args:
            device_entity_id: Entity ID of the target media player
            stream_url: URL of the stream to play

        Returns:
            True if the command was sent

        Raises:
            HandoverError: If handover fails
        """
        _LOGGER.info(
            "Starting direct handover to '%s': %s",
            device_entity_id,
            stream_url[:100],
        )

        # Validate entity_id format
        if not device_entity_id or not device_entity_id.startswith("media_player."):
            raise HandoverError(
                f"Invalid entity_id '{device_entity_id}'. Direct handover requires a valid "
                "media_player entity_id."
            )

        # Check if entity exists
        state = self.hass.states.get(device_entity_id)
        if state is None:
            raise HandoverError(f"Entity '{device_entity_id}' not found.")

        # Validate stream URL
        is_valid, validation_error = self.validate_stream_url(stream_url)
        if not is_valid:
            raise HandoverError(f"Invalid stream URL: {validation_error}")

        # Detect stream format and check compatibility
        stream_format = self.detect_stream_format(stream_url)
        content_type = self.SUPPORTED_CONTENT_TYPES.get(stream_format, "video/mp4")

        if stream_format not in (StreamFormat.HLS, StreamFormat.MP4):
            _LOGGER.warning(
                "Stream format '%s' may not be supported by Apple TV native player. "
                "Consider using AirPlay method or an HLS/MP4 stream. URL: %s",
                stream_format.value,
                stream_url[:100],
            )

        try:
            # For direct playback, use the appropriate content type
            # HLS streams work better with application/x-mpegURL
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": device_entity_id,
                    "media_content_type": content_type,
                    "media_content_id": stream_url,
                },
                blocking=True,
            )

            _LOGGER.info(
                "Successfully sent stream URL directly to '%s'", device_entity_id
            )
            return True

        except Exception as err:
            error_msg = str(err)

            # Provide more helpful error messages for common issues
            if "500" in error_msg:
                _LOGGER.error(
                    "Direct handover failed with HTTP 500: The Apple TV could not "
                    "process the stream URL. This usually means:\n"
                    "  1. The stream URL requires authentication or special headers\n"
                    "  2. The stream format (%s) is not supported by Apple TV\n"
                    "  3. The stream server doesn't respond correctly to URL verification\n"
                    "Recommendation: Use AirPlay method instead (requires pyatv).\n"
                    "Stream URL: %s",
                    stream_format.value,
                    stream_url[:150],
                )
                raise HandoverError(
                    f"Direct handover failed: Apple TV returned HTTP 500. "
                    f"The stream format ({stream_format.value}) or URL may not be supported. "
                    f"Try using AirPlay method instead (set handover_method to 'airplay' in options)."
                ) from err

            if "404" in error_msg:
                raise HandoverError(
                    "Direct handover failed: Stream URL not found (404). "
                    "Please verify the stream URL is accessible."
                ) from err

            if "timeout" in error_msg.lower():
                raise HandoverError(
                    "Direct handover failed: Connection timeout. "
                    "The stream server may be slow or unreachable from Apple TV."
                ) from err

            _LOGGER.error("Direct handover failed: %s", err)
            raise HandoverError(f"Direct handover failed: {err}") from err

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
            device_identifier: Device name (for AirPlay) or entity_id (for VLC/Direct).
                              For VLC/Direct, must be a valid media_player entity_id.
                              For AirPlay, can be the Apple TV device name.
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
                    _LOGGER.warning("AirPlay unavailable, falling back to direct")
                    method = HandoverMethod.DIRECT
                else:
                    # AirPlay needs device name, not entity_id
                    # Convert entity_id to device name if needed
                    device_name = device_identifier
                    if device_identifier.startswith("media_player."):
                        device_name = await self._entity_id_to_device_name(
                            device_identifier
                        )
                        _LOGGER.debug(
                            "Converted entity_id '%s' to device name '%s' for AirPlay",
                            device_identifier,
                            device_name,
                        )

                    await self.handover_via_airplay(device_name, stream_url, title)
                    result["success"] = True
                    result["method"] = "airplay"
                    return result

            # For VLC and Direct methods, we need a valid entity_id
            entity_id = device_identifier
            if not device_identifier.startswith("media_player."):
                entity_id = await self._find_media_player_entity(device_identifier)

            if method == HandoverMethod.VLC:
                await self.handover_via_vlc(entity_id, stream_url, title, subtitle_url)
                result["success"] = True
                result["method"] = "vlc"
                result["entity_id"] = entity_id
                return result

            if method == HandoverMethod.DIRECT:
                try:
                    await self.handover_direct(entity_id, stream_url)
                    result["success"] = True
                    result["method"] = "direct"
                    result["entity_id"] = entity_id
                    return result
                except HandoverError as direct_err:
                    # If direct fails with HTTP 500 and AirPlay is available, try AirPlay
                    if PYATV_AVAILABLE and "500" in str(direct_err):
                        _LOGGER.warning(
                            "Direct handover failed with HTTP 500, attempting AirPlay fallback"
                        )
                        try:
                            # For AirPlay, we need the device name, not entity_id
                            # Try to extract from the original identifier or entity
                            device_name = device_identifier
                            if device_identifier.startswith("media_player."):
                                # Try to get friendly name from entity state
                                state = self.hass.states.get(device_identifier)
                                if state:
                                    device_name = state.attributes.get(
                                        "friendly_name", device_identifier
                                    )

                            await self.handover_via_airplay(
                                device_name, stream_url, title
                            )
                            result["success"] = True
                            result["method"] = "airplay"
                            result["fallback"] = True
                            result["original_error"] = str(direct_err)
                            _LOGGER.info(
                                "AirPlay fallback successful after direct handover failed"
                            )
                            return result
                        except Exception as airplay_err:
                            _LOGGER.error(
                                "AirPlay fallback also failed: %s", airplay_err
                            )
                            # Re-raise the original direct error with additional context
                            raise HandoverError(
                                f"Direct handover failed ({direct_err}) and AirPlay "
                                f"fallback also failed ({airplay_err}). "
                                f"Please check your stream URL and Apple TV configuration."
                            ) from direct_err
                    # No fallback available or different error, re-raise
                    raise

        except Exception as err:
            result["error"] = str(err)
            raise

        return result

    async def _find_media_player_entity(self, device_name: str) -> str:
        """Find a media_player entity_id for a device name.

        Searches Home Assistant's entity registry for a media_player entity
        that matches the given device name.

        Args:
            device_name: The friendly name of the device (e.g., "Living Room Apple TV")

        Returns:
            The entity_id of the matching media_player

        Raises:
            HandoverError: If no matching entity is found
        """
        # Normalize the device name for comparison
        normalized_name = device_name.lower().replace(" ", "_").replace("-", "_")

        # Search through all media_player entities
        all_states = self.hass.states.async_all("media_player")

        for state in all_states:
            # Check if entity_id contains the normalized device name
            if normalized_name in state.entity_id.lower():
                _LOGGER.debug(
                    "Found media_player entity '%s' for device '%s'",
                    state.entity_id,
                    device_name,
                )
                return state.entity_id

            # Also check friendly name
            friendly_name = state.attributes.get("friendly_name", "").lower()
            if device_name.lower() in friendly_name:
                _LOGGER.debug(
                    "Found media_player entity '%s' by friendly name for device '%s'",
                    state.entity_id,
                    device_name,
                )
                return state.entity_id

        # If we have discovered devices, provide more helpful error
        if device_name in self._discovered_devices:
            raise HandoverError(
                f"Found Apple TV '{device_name}' but could not find a matching "
                f"media_player entity. For VLC handover, please provide the "
                f"entity_id directly (e.g., media_player.apple_tv_living_room). "
                f"You can find this in Home Assistant's Settings > Devices & Services > Entities."
            )

        raise HandoverError(
            f"Could not find a media_player entity for '{device_name}'. "
            f"Please provide a valid entity_id (e.g., media_player.apple_tv_living_room)."
        )

    async def _entity_id_to_device_name(self, entity_id: str) -> str:
        """Convert a media_player entity_id to an Apple TV device name.

        For AirPlay handover, we need the actual device name (e.g., "Kartoffel TV (2)")
        rather than the Home Assistant entity_id (e.g., "media_player.kartoffel_tv").

        This method:
        1. Gets the friendly_name from the entity state
        2. Discovers Apple TV devices on the network
        3. Finds a matching device by comparing names (fuzzy match)

        Args:
            entity_id: The Home Assistant entity_id (e.g., "media_player.kartoffel_tv")

        Returns:
            The Apple TV device name for pyatv

        Raises:
            HandoverError: If no matching device is found
        """
        # Get the entity's friendly name
        state = self.hass.states.get(entity_id)
        friendly_name = ""
        if state:
            friendly_name = state.attributes.get("friendly_name", "")
            _LOGGER.debug(
                "Entity '%s' has friendly_name: '%s'", entity_id, friendly_name
            )

        # Discover devices if not already done
        if not self._discovered_devices:
            await self.discover_apple_tv_devices()

        if not self._discovered_devices:
            raise HandoverError(
                f"No Apple TV devices discovered on the network. "
                f"Cannot convert entity_id '{entity_id}' to device name."
            )

        # Try to find a matching device
        # 1. First try exact match with friendly_name
        if friendly_name and friendly_name in self._discovered_devices:
            _LOGGER.debug("Exact match found for friendly_name '%s'", friendly_name)
            return friendly_name

        # 2. Try fuzzy matching - normalize both names and compare
        def normalize(name: str) -> str:
            """Normalize a name for comparison."""
            return (
                name.lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace("(", "")
                .replace(")", "")
                .replace("'", "")
            )

        # Extract base name from entity_id (e.g., "kartoffel_tv" from "media_player.kartoffel_tv")
        entity_base = entity_id.replace("media_player.", "")
        normalized_entity = normalize(entity_base)
        normalized_friendly = normalize(friendly_name) if friendly_name else ""

        best_match = None
        best_score = 0

        for device_name in self._discovered_devices:
            normalized_device = normalize(device_name)

            # Check various match conditions
            score = 0

            # Exact normalized match with friendly name
            if normalized_friendly and normalized_device == normalized_friendly:
                score = 100

            # Exact normalized match with entity base name
            elif normalized_device == normalized_entity:
                score = 90

            # Friendly name contains device name or vice versa
            elif normalized_friendly and (
                normalized_friendly in normalized_device
                or normalized_device in normalized_friendly
            ):
                score = 80

            # Entity base name in device name or vice versa
            elif (
                normalized_entity in normalized_device
                or normalized_device in normalized_entity
            ):
                score = 70

            # Partial word match
            else:
                entity_words = set(entity_base.lower().replace("_", " ").split())
                device_words = set(device_name.lower().split())
                common_words = entity_words & device_words
                if common_words:
                    score = len(common_words) * 20

            if score > best_score:
                best_score = score
                best_match = device_name
                _LOGGER.debug(
                    "New best match: '%s' with score %d (entity: '%s', friendly: '%s')",
                    device_name,
                    score,
                    entity_base,
                    friendly_name,
                )

        if best_match and best_score >= 40:
            _LOGGER.info(
                "Mapped entity_id '%s' to device name '%s' (score: %d)",
                entity_id,
                best_match,
                best_score,
            )
            return best_match

        # No match found - provide helpful error
        available_devices = ", ".join(f"'{name}'" for name in self._discovered_devices)
        raise HandoverError(
            f"Could not find Apple TV device matching entity '{entity_id}' "
            f"(friendly_name: '{friendly_name}'). "
            f"Available devices: {available_devices}. "
            f"Try configuring the Apple TV device name in the integration options."
        )
