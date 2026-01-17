"""Tests for Stremio integration __init__.py module."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.stremio.const import DOMAIN, CONF_AUTH_KEY


@pytest.mark.asyncio
async def test_async_setup_entry_success(mock_hass, mock_config_entry):
    """Test successful setup of config entry."""
    # Create mock client
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(return_value="test_auth_key")
    mock_client.async_close = AsyncMock()
    
    # Create mock coordinator
    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    
    # Setup mock hass.config_entries
    mock_hass.config_entries = MagicMock()
    mock_hass.config_entries.async_forward_entry_setups = AsyncMock()
    
    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ), patch(
        "custom_components.stremio.StremioDataUpdateCoordinator",
        return_value=mock_coordinator,
    ), patch(
        "custom_components.stremio.async_setup_services",
        new_callable=AsyncMock,
    ):
        from custom_components.stremio import async_setup_entry
        
        result = await async_setup_entry(mock_hass, mock_config_entry)
        
        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_setup_entry_auth_failure(mock_hass, mock_config_entry):
    """Test setup failure due to authentication error."""
    from custom_components.stremio.stremio_client import StremioAuthError
    
    # Create mock client that fails authentication
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(side_effect=StremioAuthError("Invalid credentials"))
    mock_client.async_close = AsyncMock()
    
    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ):
        from custom_components.stremio import async_setup_entry
        
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(mock_hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_connection_failure(mock_hass, mock_config_entry):
    """Test setup failure due to connection error."""
    from custom_components.stremio.stremio_client import StremioConnectionError
    
    # Create mock client that fails connection
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(side_effect=StremioConnectionError("Connection failed"))
    mock_client.async_close = AsyncMock()
    
    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ):
        from custom_components.stremio import async_setup_entry
        
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(mock_hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_unload_entry(mock_hass, mock_config_entry, mock_coordinator):
    """Test unloading config entry."""
    # Create mock client
    mock_client = AsyncMock()
    mock_client.async_close = AsyncMock()
    
    # Setup mock data
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coordinator,
            "client": mock_client,
        }
    }
    mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    
    with patch(
        "custom_components.stremio.async_unload_services",
        new_callable=AsyncMock,
    ):
        from custom_components.stremio import async_unload_entry
        
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data.get(DOMAIN, {})


@pytest.mark.asyncio
async def test_async_reload_entry(mock_hass, mock_config_entry):
    """Test reloading config entry."""
    mock_hass.config_entries.async_reload = AsyncMock()
    
    from custom_components.stremio import async_reload_entry
    
    await async_reload_entry(mock_hass, mock_config_entry)
    
    mock_hass.config_entries.async_reload.assert_called_once_with(
        mock_config_entry.entry_id
    )
