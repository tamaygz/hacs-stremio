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
from homeassistant.helpers.typing import ConfigType

# Try to import StaticPathConfig (HA 2024.6+), fallback for older versions
try:
    from homeassistant.components.http import StaticPathConfig

    HAS_STATIC_PATH_CONFIG = True
except ImportError:
    HAS_STATIC_PATH_CONFIG = False

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
from .services import async_setup_services, async_unload_services
from .stremio_client import StremioAuthError, StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
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

    Args:
        hass: Home Assistant instance
    """
    # Get path to www folder
    www_path = Path(__file__).parent / "www"

    if not www_path.exists():
        _LOGGER.warning("Frontend resources not found at %s", www_path)
        return

    # Register static path for card resources
    # Use StaticPathConfig if available (HA 2024.6+), otherwise use legacy method
    if HAS_STATIC_PATH_CONFIG:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    url_path="/stremio_cards",
                    path=str(www_path),
                    cache_headers=True,
                )
            ]
        )
    else:
        # Legacy method for older HA versions
        hass.http.register_static_path(
            "/stremio_cards",
            str(www_path),
            cache_headers=True,
        )

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

    # Initialize Stremio client
    client = StremioClient(email=email, password=password)

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

    # Remove data from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

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
