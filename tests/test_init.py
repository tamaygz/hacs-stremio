"""Tests for Stremio integration __init__.py module."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.stremio.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry_success(mock_hass, mock_config_entry, mock_stremio_client):
    """Test successful setup of config entry."""
    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_stremio_client,
    ), patch(
        "custom_components.stremio.StremioDataUpdateCoordinator",
    ) as mock_coordinator_class:
        # Configure coordinator mock
        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        from custom_components.stremio import async_setup_entry
        
        result = await async_setup_entry(mock_hass, mock_config_entry)
        
        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_setup_entry_auth_failure(mock_hass, mock_config_entry):
    """Test setup failure due to authentication error."""
    from custom_components.stremio.stremio_client import StremioAuthError
    
    mock_client = AsyncMock()
    mock_client.login.side_effect = StremioAuthError("Invalid credentials")
    
    with patch(
        "custom_components.stremio.StremioClient",
        return_value=mock_client,
    ):
        from custom_components.stremio import async_setup_entry
        
        with pytest.raises(Exception):  # ConfigEntryAuthFailed
            await async_setup_entry(mock_hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_unload_entry(mock_hass, mock_config_entry, mock_coordinator):
    """Test unloading config entry."""
    # Setup mock data
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coordinator,
        }
    }
    mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    
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
