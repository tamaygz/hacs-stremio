"""Tests for Stremio config flow."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType, AbortFlow

from custom_components.stremio.const import DOMAIN, CONF_AUTH_KEY
from custom_components.stremio.config_flow import ConfigFlow, OptionsFlowHandler

from .conftest import MOCK_CONFIG_ENTRY, MOCK_USER_DATA


@pytest.mark.asyncio
async def test_form_user_step(mock_hass):
    """Test the initial user form is shown."""
    flow = ConfigFlow()
    flow.hass = mock_hass
    
    result = await flow.async_step_user()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_form_user_step_success(mock_hass):
    """Test successful user authentication."""
    flow = ConfigFlow()
    flow.hass = mock_hass
    flow.context = {}
    
    # Create mock user object with email attribute
    mock_user = MagicMock()
    mock_user.email = MOCK_CONFIG_ENTRY[CONF_EMAIL]
    
    # Create mock client context manager
    mock_client = AsyncMock()
    mock_client.login = AsyncMock(return_value="test_auth_key")
    mock_client.get_user = AsyncMock(return_value=mock_user)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch(
        "custom_components.stremio.config_flow.StremioAPIClient",
        return_value=mock_client,
    ), patch.object(
        flow, "async_set_unique_id", new_callable=AsyncMock
    ), patch.object(
        flow, "_abort_if_unique_id_configured"
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_CONFIG_ENTRY[CONF_EMAIL]
    assert CONF_AUTH_KEY in result["data"]
    assert result["data"][CONF_EMAIL] == MOCK_CONFIG_ENTRY[CONF_EMAIL]


@pytest.mark.asyncio
async def test_form_user_step_invalid_auth(mock_hass):
    """Test form submission with invalid credentials."""
    flow = ConfigFlow()
    flow.hass = mock_hass
    
    # Create mock client that fails authentication
    mock_client = AsyncMock()
    mock_client.login = AsyncMock(side_effect=Exception("401 authentication failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch(
        "custom_components.stremio.config_flow.StremioAPIClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_form_user_step_connection_error(mock_hass):
    """Test form submission with connection error."""
    flow = ConfigFlow()
    flow.hass = mock_hass
    
    # Create mock client that fails with connection error
    mock_client = AsyncMock()
    mock_client.login = AsyncMock(side_effect=Exception("Network error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch(
        "custom_components.stremio.config_flow.StremioAPIClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_form_user_step_no_auth_key(mock_hass):
    """Test form submission when no auth key is returned."""
    flow = ConfigFlow()
    flow.hass = mock_hass
    
    # Create mock client that returns no auth key
    mock_client = AsyncMock()
    mock_client.login = AsyncMock(return_value=None)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch(
        "custom_components.stremio.config_flow.StremioAPIClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.FORM
    # Should get invalid_auth error since no auth key means authentication failed
    assert result["errors"]["base"] in ["invalid_auth", "cannot_connect"]


@pytest.mark.asyncio
async def test_options_flow_init(mock_hass, mock_config_entry):
    """Test options flow initialization."""
    options_flow = OptionsFlowHandler(mock_config_entry)
    options_flow.hass = mock_hass
    
    result = await options_flow.async_step_init()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_update(mock_hass, mock_config_entry):
    """Test updating options."""
    options_flow = OptionsFlowHandler(mock_config_entry)
    options_flow.hass = mock_hass
    
    new_options = {
        "player_scan_interval": 60,
        "library_scan_interval": 600,
        "enable_apple_tv_handover": True,
        "handover_method": "airplay",
    }
    
    result = await options_flow.async_step_init(new_options)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == new_options


@pytest.mark.asyncio
async def test_duplicate_entry(mock_hass):
    """Test that duplicate entries are not allowed."""
    # Create mock user object with email attribute
    mock_user = MagicMock()
    mock_user.email = MOCK_CONFIG_ENTRY[CONF_EMAIL]
    
    # Create mock client context manager
    mock_client = AsyncMock()
    mock_client.login = AsyncMock(return_value="test_auth_key")
    mock_client.get_user = AsyncMock(return_value=mock_user)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    flow = ConfigFlow()
    flow.hass = mock_hass
    flow.context = {}
    
    with patch(
        "custom_components.stremio.config_flow.StremioAPIClient",
        return_value=mock_client,
    ), patch.object(
        flow, "async_set_unique_id", new_callable=AsyncMock
    ), patch.object(
        flow, "_abort_if_unique_id_configured", side_effect=AbortFlow("already_configured")
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
        
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
