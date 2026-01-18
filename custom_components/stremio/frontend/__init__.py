"""JavaScript module registration for Stremio frontend resources.

This module handles automatic registration of custom Lovelace cards
with Home Assistant's frontend system, eliminating the need for
manual resource configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

# Try to import StaticPathConfig for modern HA versions (2024.6+)
try:
    from homeassistant.components.http import StaticPathConfig  # type: ignore[attr-defined]

    HAS_STATIC_PATH_CONFIG = True
except ImportError:
    HAS_STATIC_PATH_CONFIG = False
    StaticPathConfig = None  # type: ignore[assignment, misc]

from ..const import JSMODULES, URL_BASE

if TYPE_CHECKING:
    from homeassistant.components.lovelace import LovelaceData

_LOGGER = logging.getLogger(__name__)


class JSModuleRegistration:
    """Registers JavaScript modules in Home Assistant.

    This class handles:
    - Static HTTP path registration for serving JS files
    - Automatic Lovelace resource registration (storage mode)
    - Version management for cache busting
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the registrar.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self.lovelace: LovelaceData | None = self.hass.data.get("lovelace")

    async def async_register(self) -> None:
        """Register frontend resources."""
        await self._async_register_path()

        # Only register modules if Lovelace is in storage mode
        if self.lovelace and self.lovelace.mode == "storage":
            await self._async_wait_for_lovelace_resources()
        else:
            _LOGGER.info(
                "Lovelace is in YAML mode. Add resources manually: %s/*.js",
                URL_BASE,
            )

    async def _async_register_path(self) -> None:
        """Register the static HTTP path for serving JS files."""
        frontend_path = Path(__file__).parent

        # Try modern method first (HA 2024.6+)
        if HAS_STATIC_PATH_CONFIG and StaticPathConfig is not None:
            try:
                await self.hass.http.async_register_static_paths(  # type: ignore[attr-defined]
                    [StaticPathConfig(URL_BASE, str(frontend_path), False)]
                )
                _LOGGER.debug(
                    "Static path registered: %s -> %s", URL_BASE, frontend_path
                )
                return
            except (RuntimeError, AttributeError) as err:
                _LOGGER.debug("Modern registration failed: %s, trying fallback", err)

        # Fallback for older Home Assistant versions
        try:
            self.hass.http.register_static_path(URL_BASE, str(frontend_path))  # type: ignore[attr-defined]
            _LOGGER.debug(
                "Static path registered (legacy): %s -> %s",
                URL_BASE,
                frontend_path,
            )
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to register static path: %s", err)

    async def _async_wait_for_lovelace_resources(self) -> None:
        """Wait for Lovelace resources to load before registering modules."""
        if not self.lovelace:
            return

        async def _check_loaded(_now: Any) -> None:
            if self.lovelace and self.lovelace.resources.loaded:
                await self._async_register_modules()
            else:
                _LOGGER.debug("Lovelace resources not loaded, retrying in 5s")
                async_call_later(self.hass, 5, _check_loaded)

        await _check_loaded(0)

    async def _async_register_modules(self) -> None:
        """Register or update JavaScript modules in Lovelace resources."""
        if not self.lovelace:
            return

        _LOGGER.debug("Installing Stremio JavaScript modules")

        # Get existing resources from this integration
        existing_resources = [
            r
            for r in self.lovelace.resources.async_items()
            if r["url"].startswith(URL_BASE)
        ]

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            registered = False

            for resource in existing_resources:
                if self._get_path(resource["url"]) == url:
                    registered = True
                    # Check if update needed
                    if self._get_version(resource["url"]) != module["version"]:
                        _LOGGER.info(
                            "Updating %s to version %s",
                            module["name"],
                            module["version"],
                        )
                        await self.lovelace.resources.async_update_item(
                            resource["id"],
                            {
                                "res_type": "module",
                                "url": f"{url}?v={module['version']}",
                            },
                        )
                    break

            if not registered:
                _LOGGER.info(
                    "Registering %s version %s",
                    module["name"],
                    module["version"],
                )
                await self.lovelace.resources.async_create_item(
                    {
                        "res_type": "module",
                        "url": f"{url}?v={module['version']}",
                    }
                )

    def _get_path(self, url: str) -> str:
        """Extract path without query parameters.

        Args:
            url: Full URL with potential query string

        Returns:
            URL path without query parameters
        """
        return url.split("?")[0]

    def _get_version(self, url: str) -> str:
        """Extract version from URL query parameter.

        Args:
            url: URL with potential version query param

        Returns:
            Version string or "0" if not found
        """
        parts = url.split("?")
        if len(parts) > 1 and parts[1].startswith("v="):
            return parts[1].replace("v=", "")
        return "0"

    async def async_unregister(self) -> None:
        """Remove Lovelace resources from this integration."""
        if not self.lovelace or self.lovelace.mode != "storage":
            return

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            resources = [
                r
                for r in self.lovelace.resources.async_items()
                if r["url"].startswith(url)
            ]
            for resource in resources:
                await self.lovelace.resources.async_delete_item(resource["id"])
                _LOGGER.info("Unregistered resource: %s", module["name"])
