"""Tests for Stremio integration __init__.py module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.stremio.const import CONF_AUTH_KEY, DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry_success(hass: HomeAssistant, mock_config_entry):
    """Test successful setup of config entry."""
    # Create mock client
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(return_value="test_auth_key")
    mock_client.async_close = AsyncMock()

    # Create mock coordinator
    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    # Create mock session
    mock_session = MagicMock()

    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ), patch(
        "custom_components.stremio.StremioDataUpdateCoordinator",
        return_value=mock_coordinator,
    ), patch(
        "custom_components.stremio.async_setup_services",
        new_callable=AsyncMock,
    ), patch(
        "custom_components.stremio.async_get_clientsession",
        return_value=mock_session,
    ):
        from custom_components.stremio import async_setup_entry

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_setup_entry_auth_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup failure due to authentication error."""
    from custom_components.stremio.stremio_client import StremioAuthError

    # Create mock client that fails authentication
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(
        side_effect=StremioAuthError("Invalid credentials")
    )
    mock_client.async_close = AsyncMock()

    # Create mock session
    mock_session = MagicMock()

    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ), patch(
        "custom_components.stremio.async_get_clientsession",
        return_value=mock_session,
    ):
        from custom_components.stremio import async_setup_entry

        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_connection_failure(
    hass: HomeAssistant, mock_config_entry
):
    """Test setup failure due to connection error."""
    from custom_components.stremio.stremio_client import StremioConnectionError

    # Create mock client that fails connection
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(
        side_effect=StremioConnectionError("Connection failed")
    )
    mock_client.async_close = AsyncMock()

    # Create mock session
    mock_session = MagicMock()

    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ), patch(
        "custom_components.stremio.async_get_clientsession",
        return_value=mock_session,
    ):
        from custom_components.stremio import async_setup_entry

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_unload_entry(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
):
    """Test unloading config entry."""
    # Create mock client
    mock_client = AsyncMock()
    mock_client.async_close = AsyncMock()

    # Setup mock data
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coordinator,
            "client": mock_client,
        }
    }

    with patch(
        "custom_components.stremio.async_unload_services",
        new_callable=AsyncMock,
    ):
        from custom_components.stremio import async_unload_entry

        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


@pytest.mark.asyncio
async def test_async_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test reloading config entry."""
    from custom_components.stremio import async_reload_entry

    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as mock_reload:
        await async_reload_entry(hass, mock_config_entry)

        mock_reload.assert_called_once_with(mock_config_entry.entry_id)
