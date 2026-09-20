"""JavaScript module registration for Stremio frontend resources.

This module handles automatic registration of custom Lovelace cards
with Home Assistant's frontend system, eliminating the need for
manual resource configuration.

Cache busting is achieved by:
1. Adding version query parameter to resource URLs (?v=X.Y.Z)
2. Using INTEGRATION_VERSION from manifest.json as the source of truth
3. Automatically updating Lovelace resources when version changes
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant

from ..const import INTEGRATION_VERSION, JSMODULES, URL_BASE

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

    @property
    def _lovelace(self) -> Any:
        """Return the lovelace data object from hass.data."""
        return self.hass.data.get("lovelace")

    @property
    def lovelace_resources(self) -> ResourceStorageCollection | None:
        """Get the Lovelace resources collection.

        Returns:
            ResourceStorageCollection or None if not available
        """
        lovelace = self._lovelace
        if lovelace is None:
            _LOGGER.debug("Lovelace data is None")
            return None

        # Modern HA (2024+): lovelace data has a resources attribute
        if hasattr(lovelace, "resources"):
            return lovelace.resources  # type: ignore[return-value]

        # Dict-based structure (older HA versions)
        if isinstance(lovelace, dict):
            return lovelace.get("resources")  # type: ignore[return-value]

        _LOGGER.debug("Could not find lovelace resources")
        return None

    @property
    def lovelace_mode(self) -> str | None:
        """Get the Lovelace mode safely.

        Returns:
            'storage', 'yaml', or None if not available
        """
        lovelace = self._lovelace
        if lovelace is None:
            return None

        if hasattr(lovelace, "mode"):
            return lovelace.mode  # type: ignore[union-attr]

        if isinstance(lovelace, dict):
            return lovelace.get("mode")

        return None

    async def async_register(self) -> None:
        """Register frontend resources."""
        await self._async_register_path()

        mode = self.lovelace_mode
        resources = self.lovelace_resources

        _LOGGER.debug(
            "Lovelace mode: %s, resources available: %s",
            mode,
            resources is not None,
        )

        if mode == "yaml":
            _LOGGER.info(
                "Lovelace is in YAML mode. Add resources manually: %s/*.js?v=%s",
                URL_BASE,
                INTEGRATION_VERSION,
            )
            return

        if resources is not None:
            await self._async_register_modules(resources)
        else:
            _LOGGER.info(
                "Lovelace resources not accessible (mode='%s'). "
                "Add resources manually if needed: %s/*.js?v=%s",
                mode or "unknown",
                URL_BASE,
                INTEGRATION_VERSION,
            )

    async def _async_register_path(self) -> None:
        """Register the static HTTP path for serving JS files."""
        frontend_path = Path(__file__).parent
        _LOGGER.info(
            "Registering Stremio frontend v%s from %s",
            INTEGRATION_VERSION,
            frontend_path,
        )

        try:
            await self.hass.http.async_register_static_paths(  # type: ignore[attr-defined]
                [StaticPathConfig(URL_BASE, str(frontend_path), False)]
            )
            _LOGGER.debug("Static path registered: %s -> %s", URL_BASE, frontend_path)
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to register static path: %s", err)

    async def _async_register_modules(
        self, resources: ResourceStorageCollection
    ) -> None:
        """Ensure resources are loaded then register or update JS modules."""
        # Explicitly load resources before reading or writing to avoid the
        # lazy-load race that can silently overwrite existing entries.
        # See: https://github.com/home-assistant/core/issues/165767
        if not resources.loaded:
            await resources.async_load()

        _LOGGER.info("Installing Stremio JavaScript modules v%s", INTEGRATION_VERSION)

        try:
            existing_resources = [
                r for r in resources.async_items() if r["url"].startswith(URL_BASE)
            ]
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to get existing resources: %s", err)
            return

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            versioned_url = f"{url}?v={module['version']}"
            registered = False

            for resource in existing_resources:
                if self._get_path(resource["url"]) != url:
                    continue

                registered = True
                current_version = self._get_version(resource["url"])
                target_version = module["version"]

                if current_version == target_version:
                    _LOGGER.debug(
                        "%s already at v%s, no update needed",
                        module["name"],
                        target_version,
                    )
                else:
                    _LOGGER.info(
                        "Updating %s from v%s to v%s",
                        module["name"],
                        current_version,
                        target_version,
                    )
                    try:
                        if isinstance(resources, ResourceStorageCollection):
                            await resources.async_update_item(
                                resource["id"],
                                {"res_type": "module", "url": versioned_url},
                            )
                            _LOGGER.info(
                                "Successfully updated %s to v%s",
                                module["name"],
                                target_version,
                            )
                        else:
                            _LOGGER.warning(
                                "Cannot persist update for %s: resources collection "
                                "is not a ResourceStorageCollection (type=%s). "
                                "The update will not survive a restart.",
                                module["name"],
                                type(resources).__name__,
                            )
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.error(
                            "Failed to update resource %s: %s", module["name"], err
                        )
                break

            if not registered:
                _LOGGER.info(
                    "Registering new resource: %s v%s",
                    module["name"],
                    module["version"],
                )
                try:
                    if isinstance(resources, ResourceStorageCollection):
                        await resources.async_create_item(
                            {"res_type": "module", "url": versioned_url}
                        )
                        _LOGGER.info(
                            "Successfully registered %s v%s",
                            module["name"],
                            module["version"],
                        )
                    elif getattr(resources, "data", None) and getattr(
                        resources.data, "append", None
                    ):
                        resources.data.append(
                            {"type": "module", "url": versioned_url}
                        )
                        _LOGGER.info(
                            "Successfully registered %s v%s (in-memory only)",
                            module["name"],
                            module["version"],
                        )
                    else:
                        _LOGGER.warning(
                            "Could not register %s: no supported registration API "
                            "on resources collection (type=%s).",
                            module["name"],
                            type(resources).__name__,
                        )
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error(
                        "Failed to register resource %s: %s", module["name"], err
                    )

    def _get_path(self, url: str) -> str:
        """Extract path without query parameters."""
        return url.split("?")[0]

    def _get_version(self, url: str) -> str:
        """Extract version from URL query parameter."""
        parts = url.split("?")
        if len(parts) > 1 and parts[1].startswith("v="):
            return parts[1].replace("v=", "")
        return "0"

    async def async_unregister(self) -> None:
        """Remove Lovelace resources from this integration."""
        resources = self.lovelace_resources
        if resources is None or not isinstance(resources, ResourceStorageCollection):
            return

        if not resources.loaded:
            await resources.async_load()

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            try:
                resource_list = [
                    r for r in resources.async_items() if r["url"].startswith(url)
                ]
                for resource in resource_list:
                    await resources.async_delete_item(resource["id"])
                    _LOGGER.info("Unregistered resource: %s", module["name"])
            except Exception as err:  # noqa: BLE001
                _LOGGER.error(
                    "Failed to unregister resource %s: %s", module["name"], err
                )
