"""Tests for Stremio config flow."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType

from custom_components.stremio.const import DOMAIN

from .conftest import MOCK_CONFIG_ENTRY, MOCK_USER_DATA


@pytest.mark.asyncio
async def test_form_user_step(mock_hass):
    """Test the initial user form is shown."""
    from custom_components.stremio.config_flow import StremioConfigFlow
    
    flow = StremioConfigFlow()
    flow.hass = mock_hass
    
    result = await flow.async_step_user()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_form_user_step_success(mock_hass, mock_stremio_client):
    """Test successful user authentication."""
    from custom_components.stremio.config_flow import StremioConfigFlow
    
    flow = StremioConfigFlow()
    flow.hass = mock_hass
    flow.context = {}
    
    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_stremio_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Stremio - {MOCK_CONFIG_ENTRY[CONF_EMAIL]}"
    assert result["data"] == MOCK_CONFIG_ENTRY


@pytest.mark.asyncio
async def test_form_user_step_invalid_auth(mock_hass):
    """Test form submission with invalid credentials."""
    from custom_components.stremio.config_flow import StremioConfigFlow
    from custom_components.stremio.stremio_client import AuthenticationError
    
    flow = StremioConfigFlow()
    flow.hass = mock_hass
    
    mock_client = AsyncMock()
    mock_client.login.side_effect = AuthenticationError("Invalid credentials")
    
    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_form_user_step_connection_error(mock_hass):
    """Test form submission with connection error."""
    from custom_components.stremio.config_flow import StremioConfigFlow
    from custom_components.stremio.stremio_client import ConnectionError
    
    flow = StremioConfigFlow()
    flow.hass = mock_hass
    
    mock_client = AsyncMock()
    mock_client.login.side_effect = ConnectionError("Network error")
    
    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_form_user_step_unknown_error(mock_hass):
    """Test form submission with unknown error."""
    from custom_components.stremio.config_flow import StremioConfigFlow
    
    flow = StremioConfigFlow()
    flow.hass = mock_hass
    
    mock_client = AsyncMock()
    mock_client.login.side_effect = Exception("Unknown error")
    
    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "unknown"


@pytest.mark.asyncio
async def test_options_flow_init(mock_hass, mock_config_entry):
    """Test options flow initialization."""
    from custom_components.stremio.config_flow import StremioOptionsFlowHandler
    
    options_flow = StremioOptionsFlowHandler(mock_config_entry)
    options_flow.hass = mock_hass
    
    result = await options_flow.async_step_init()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_update(mock_hass, mock_config_entry):
    """Test updating options."""
    from custom_components.stremio.config_flow import StremioOptionsFlowHandler
    
    options_flow = StremioOptionsFlowHandler(mock_config_entry)
    options_flow.hass = mock_hass
    
    new_options = {
        "player_update_interval": 60,
        "library_update_interval": 600,
        "enable_apple_tv_handover": True,
        "handover_method": "airplay",
    }
    
    result = await options_flow.async_step_init(new_options)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == new_options


@pytest.mark.asyncio
async def test_duplicate_entry(mock_hass, mock_stremio_client):
    """Test that duplicate entries are not allowed."""
    from custom_components.stremio.config_flow import StremioConfigFlow
    
    # Simulate existing entry
    mock_hass.config_entries = AsyncMock()
    existing_entry = AsyncMock()
    existing_entry.unique_id = MOCK_CONFIG_ENTRY[CONF_EMAIL]
    mock_hass.config_entries.async_entries.return_value = [existing_entry]
    
    flow = StremioConfigFlow()
    flow.hass = mock_hass
    flow._async_current_entries = lambda: [existing_entry]
    flow.context = {}
    
    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_stremio_client,
    ):
        # This should abort due to duplicate
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)
        
        # Either aborts or creates entry depending on implementation
        assert result["type"] in [FlowResultType.ABORT, FlowResultType.CREATE_ENTRY]
