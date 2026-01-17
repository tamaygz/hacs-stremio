"""The Stremio integration for Home Assistant.

This integration connects to Stremio and provides:
- Media player control
- Library sensors
- Continue watching tracking
- Apple TV handover support
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Stremio component.

    Args:
        hass: Home Assistant instance
        config: Configuration dict

    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})
    return True


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
