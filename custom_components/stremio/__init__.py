"""The Stremio integration for Home Assistant.

This integration connects to Stremio and provides:
- Media player control
- Library sensors
- Continue watching tracking
- Apple TV handover support
- Custom Lovelace cards
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

# Try to import StaticPathConfig for modern HA versions (2024.6+)
try:
    from homeassistant.components.http import (  # type: ignore[import, attr-defined]
        StaticPathConfig,
    )

    HAS_STATIC_PATH_CONFIG = True
except ImportError:
    HAS_STATIC_PATH_CONFIG = False
    StaticPathConfig = None  # type: ignore[assignment, misc]

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
from .services import async_setup_services, async_unload_services
from .stremio_client import StremioAuthError, StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)

# This integration is config entry only - no YAML configuration
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
]

# Frontend resources
LOVELACE_CARD_URL = "/stremio_cards/stremio-card-bundle.js"
LOVELACE_PLAYER_CARD_URL = "/stremio_cards/stremio-player-card.js"
LOVELACE_LIBRARY_CARD_URL = "/stremio_cards/stremio-library-card.js"
LOVELACE_DIALOG_URL = "/stremio_cards/stremio-stream-dialog.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stremio component.

    Args:
        hass: Home Assistant instance
        config: Configuration dict

    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})

    # Register frontend resources
    await _async_register_frontend(hass)

    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend resources for Lovelace cards.

    Supports multiple Home Assistant versions by attempting to use the modern
    StaticPathConfig API (HA 2024.6+) and falling back to the legacy method.

    Args:
        hass: Home Assistant instance
    """
    # Get path to www folder
    www_path = Path(__file__).parent / "www"

    if not www_path.exists():
        _LOGGER.warning("Frontend resources not found at %s", www_path)
        return

    # Register static path for card resources
    # Try modern approach first (HA 2024.6+)
    if HAS_STATIC_PATH_CONFIG and StaticPathConfig is not None:
        try:
            _LOGGER.debug(
                "Using modern StaticPathConfig for HA 2024.6+ to register frontend resources"
            )
            # For modern HA versions, use async_register_static_paths
            if hasattr(hass.http, "async_register_static_paths"):
                await hass.http.async_register_static_paths(  # type: ignore[attr-defined]
                    [
                        StaticPathConfig(  # type: ignore[name-defined]
                            url_path="/stremio_cards",
                            path=str(www_path),
                        )
                    ]
                )
                _LOGGER.info(
                    "Registered static path for Stremio frontend (async method)"
                )
            else:
                # Fallback to sync method if available
                if hasattr(hass.http, "register_static_path"):
                    hass.http.register_static_path(
                        "/stremio_cards",
                        str(www_path),
                    )
                    _LOGGER.info(
                        "Registered static path for Stremio frontend (sync method)"
                    )
                else:
                    _LOGGER.warning(
                        "No suitable static path registration method found in HA"
                    )
        except Exception as err:
            _LOGGER.warning(
                "Failed to register static path using modern method: %s, trying fallback",
                err,
            )
            # Try fallback method
            try:
                hass.http.register_static_path(
                    "/stremio_cards",
                    str(www_path),
                )
                _LOGGER.info(
                    "Registered static path for Stremio frontend (fallback method)"
                )
            except Exception as fallback_err:
                _LOGGER.error(
                    "Failed to register static path with both methods: %s",
                    fallback_err,
                )
    else:
        # Use legacy method for older HA versions
        try:
            _LOGGER.debug("Using legacy method for older Home Assistant versions")
            hass.http.register_static_path(
                "/stremio_cards",
                str(www_path),
            )
            _LOGGER.info("Registered static path for Stremio frontend (legacy method)")
        except Exception as err:
            _LOGGER.error("Failed to register static path in legacy mode: %s", err)

    # Register Lovelace resources
    # This uses the frontend component's resource registration
    hass.data.setdefault("lovelace_resources", set())

    resources = [
        LOVELACE_PLAYER_CARD_URL,
        LOVELACE_LIBRARY_CARD_URL,
        LOVELACE_DIALOG_URL,
    ]

    for resource_url in resources:
        if resource_url not in hass.data["lovelace_resources"]:
            hass.data["lovelace_resources"].add(resource_url)
            _LOGGER.debug("Registered Lovelace resource: %s", resource_url)

    _LOGGER.info("Stremio frontend resources registered")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stremio from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to set up

    Returns:
        True if setup was successful

    Raises:
        ConfigEntryAuthFailed: When authentication fails
        ConfigEntryNotReady: When connection fails
    """
    _LOGGER.info("Setting up Stremio integration for %s", entry.unique_id)

    # Get credentials from config entry
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    # Get shared aiohttp session from Home Assistant
    session = async_get_clientsession(hass)

    # Initialize Stremio client with shared session
    client = StremioClient(email=email, password=password, session=session)

    try:
        # Test authentication
        await client.async_authenticate()
        _LOGGER.info("Successfully authenticated with Stremio")

    except StremioAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err

    except StremioConnectionError as err:
        _LOGGER.warning("Connection failed, will retry: %s", err)
        raise ConfigEntryNotReady(f"Connection failed: {err}") from err

    except Exception as err:
        _LOGGER.exception("Unexpected error during setup: %s", err)
        raise ConfigEntryNotReady(f"Unexpected error: {err}") from err

    # Create coordinator
    coordinator = StremioDataUpdateCoordinator(
        hass=hass,
        client=client,
        entry=entry,
    )

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and client in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    # Forward the entry to platform setup
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services (only once for the first entry)
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    # Register update listener for options flow
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Stremio integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to unload

    Returns:
        True if unload was successful
    """
    _LOGGER.info("Unloading Stremio integration for %s", entry.unique_id)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove data from hass.data and cleanup client
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)

        # Close the client to cleanup any resources
        client = data.get("client")
        if client:
            await client.async_close()

        # Unload services if no more entries
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change.

    Args:
        hass: Home Assistant instance
        entry: Config entry to reload
    """
    _LOGGER.info("Reloading Stremio integration for %s", entry.unique_id)
    await hass.config_entries.async_reload(entry.entry_id)
