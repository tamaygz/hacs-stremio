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

    def _refresh_lovelace_data(self) -> Any:
        """Re-read the lovelace data object from hass.data.

        Called immediately before any read or write operation so that
        late-initialisation cases (lovelace populated after __init__)
        are always reflected.
        """
        return self.hass.data.get("lovelace")

    @property
    def _lovelace(self) -> Any:
        """Return the lovelace data object from hass.data."""
        return self._refresh_lovelace_data()

    @property
    def lovelace_resources(self) -> ResourceStorageCollection | None:
        """Get the Lovelace resources collection.

        Returns:
            ResourceStorageCollection or None if not available
        """
        lovelace = self._lovelace
        if lovelace is None:
            _LOGGER.debug("Lovelace data is None (hass.data['lovelace'] not set)")
            return None

        _LOGGER.debug("Lovelace data type: %s", type(lovelace).__name__)

        # Modern HA (2024+): lovelace data has a resources attribute
        if hasattr(lovelace, "resources"):
            resources = lovelace.resources
            _LOGGER.debug(
                "Lovelace resources type (attribute): %s",
                type(resources).__name__,
            )
            return resources  # type: ignore[return-value]

        # Dict-based structure (older HA versions)
        if isinstance(lovelace, dict):
            resources = lovelace.get("resources")
            _LOGGER.debug(
                "Lovelace resources type (dict key): %s",
                type(resources).__name__ if resources is not None else "None",
            )
            return resources  # type: ignore[return-value]

        _LOGGER.debug(
            "Could not find lovelace resources in object of type %s",
            type(lovelace).__name__,
        )
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
            "Lovelace mode: %s, resources type: %s",
            mode,
            type(resources).__name__ if resources is not None else "None",
        )

        if mode == "yaml":
            _LOGGER.info(
                "Lovelace is in YAML mode. Add resources manually: %s/*.js?v=%s",
                URL_BASE,
                INTEGRATION_VERSION,
            )
            return

        if isinstance(resources, ResourceStorageCollection):
            await self._async_register_modules(resources)
        else:
            _LOGGER.warning(
                "Lovelace resources not accessible "
                "(mode='%s', resources_type='%s'). "
                "Add resources manually if needed: %s/*.js?v=%s",
                mode or "unknown",
                type(resources).__name__ if resources is not None else "None",
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
        # Load resources before reading or writing to avoid the lazy-load race
        # that can silently overwrite existing entries. async_load() is safe to
        # call unconditionally — the underlying Store caches data in memory.
        # See: https://github.com/home-assistant/core/issues/165767
        _LOGGER.debug("Loading Lovelace resource store before registration")
        await resources.async_load()

        all_resources = list(resources.async_items())
        _LOGGER.debug(
            "Lovelace resource store loaded: %d total resource(s)", len(all_resources)
        )

        _LOGGER.info("Installing Stremio JavaScript modules v%s", INTEGRATION_VERSION)

        try:
            existing_resources = [
                r for r in all_resources if r["url"].startswith(URL_BASE)
            ]
            _LOGGER.debug(
                "Found %d existing Stremio resource(s): %s",
                len(existing_resources),
                [r["url"] for r in existing_resources],
            )
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
                        await resources.async_update_item(
                            resource["id"],
                            {"res_type": "module", "url": versioned_url},
                        )
                        _LOGGER.info(
                            "Successfully updated %s to v%s",
                            module["name"],
                            target_version,
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
                    await resources.async_create_item(
                        {"res_type": "module", "url": versioned_url}
                    )
                    _LOGGER.info(
                        "Successfully registered %s v%s",
                        module["name"],
                        module["version"],
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
            _LOGGER.debug(
                "Skipping unregister: resources type is %s",
                type(resources).__name__ if resources is not None else "None",
            )
            return

        _LOGGER.debug("Loading Lovelace resource store before unregistration")
        await resources.async_load()

        all_resources = list(resources.async_items())
        _LOGGER.debug(
            "Lovelace resource store loaded: %d total resource(s)", len(all_resources)
        )

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            try:
                resource_list = [r for r in all_resources if r["url"].startswith(url)]
                _LOGGER.debug(
                    "Found %d resource(s) to unregister for %s",
                    len(resource_list),
                    module["name"],
                )
                for resource in resource_list:
                    await resources.async_delete_item(resource["id"])
                    _LOGGER.info(
                        "Unregistered resource: %s (url=%s)",
                        module["name"],
                        resource["url"],
                    )
            except Exception as err:  # noqa: BLE001
                _LOGGER.error(
                    "Failed to unregister resource %s: %s", module["name"], err
                )
