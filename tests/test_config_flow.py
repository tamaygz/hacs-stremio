"""Tests for Stremio config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow, FlowResultType

from custom_components.stremio.config_flow import ConfigFlow, OptionsFlowHandler
from custom_components.stremio.const import CONF_AUTH_KEY, DOMAIN

from .conftest import MOCK_CONFIG_ENTRY, MOCK_USER_DATA


@pytest.mark.asyncio
async def test_form_user_step(hass: HomeAssistant):
    """Test the initial user form is shown."""
    flow = ConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.FORM  # type: ignore[index]
    assert result["step_id"] == "user"  # type: ignore[index]
    assert result["errors"] == {}  # type: ignore[index]


@pytest.mark.asyncio
async def test_form_user_step_success(hass: HomeAssistant):
    """Test successful user authentication."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}

    # Create mock client
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(return_value="test_auth_key")
    mock_client.async_get_user = AsyncMock(
        return_value={"email": MOCK_CONFIG_ENTRY[CONF_EMAIL]}
    )
    mock_client.async_close = AsyncMock()

    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ), patch.object(flow, "async_set_unique_id", new_callable=AsyncMock), patch.object(
        flow, "_abort_if_unique_id_configured"
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)

    assert result["type"] == FlowResultType.CREATE_ENTRY  # type: ignore[index]
    assert result["title"] == MOCK_CONFIG_ENTRY[CONF_EMAIL]  # type: ignore[index]
    assert CONF_AUTH_KEY in result["data"]  # type: ignore[index]
    assert result["data"][CONF_EMAIL] == MOCK_CONFIG_ENTRY[CONF_EMAIL]  # type: ignore[index]


@pytest.mark.asyncio
async def test_form_user_step_invalid_auth(hass: HomeAssistant):
    """Test form submission with invalid credentials."""
    from custom_components.stremio.stremio_client import StremioAuthError

    flow = ConfigFlow()
    flow.hass = hass

    # Create mock client that fails authentication
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(
        side_effect=StremioAuthError("401 authentication failed")
    )
    mock_client.async_close = AsyncMock()

    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)

    assert result["type"] == FlowResultType.FORM  # type: ignore[index]
    assert result["errors"]["base"] == "invalid_auth"  # type: ignore[index]


@pytest.mark.asyncio
async def test_form_user_step_connection_error(hass: HomeAssistant):
    """Test form submission with connection error."""
    from custom_components.stremio.stremio_client import StremioConnectionError

    flow = ConfigFlow()
    flow.hass = hass

    # Create mock client that fails with connection error
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(
        side_effect=StremioConnectionError("Network error")
    )
    mock_client.async_close = AsyncMock()

    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)

    assert result["type"] == FlowResultType.FORM  # type: ignore[index]
    assert result["errors"]["base"] == "cannot_connect"  # type: ignore[index]


@pytest.mark.asyncio
async def test_form_user_step_no_auth_key(hass: HomeAssistant):
    """Test form submission when no auth key is returned."""
    flow = ConfigFlow()
    flow.hass = hass

    # Create mock client that returns no auth key
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(return_value=None)
    mock_client.async_close = AsyncMock()

    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ):
        result = await flow.async_step_user(MOCK_CONFIG_ENTRY)

    assert result["type"] == FlowResultType.FORM  # type: ignore[index]
    # Should get invalid_auth error since no auth key means authentication failed
    assert result["errors"]["base"] in ["invalid_auth", "cannot_connect"]  # type: ignore[index]


@pytest.mark.asyncio
async def test_options_flow_init(hass: HomeAssistant, mock_config_entry):
    """Test options flow initialization."""
    options_flow = OptionsFlowHandler(mock_config_entry)
    options_flow.hass = hass

    result = await options_flow.async_step_init()

    assert result["type"] == FlowResultType.FORM  # type: ignore[index]
    assert result["step_id"] == "init"  # type: ignore[index]


@pytest.mark.asyncio
async def test_options_flow_update(hass: HomeAssistant, mock_config_entry):
    """Test updating options."""
    options_flow = OptionsFlowHandler(mock_config_entry)
    options_flow.hass = hass

    new_options = {
        "player_scan_interval": 60,
        "library_scan_interval": 600,
        "enable_apple_tv_handover": True,
        "handover_method": "airplay",
    }

    result = await options_flow.async_step_init(new_options)

    assert result["type"] == FlowResultType.CREATE_ENTRY  # type: ignore[index]
    assert result["data"] == new_options  # type: ignore[index]


@pytest.mark.asyncio
async def test_duplicate_entry(hass: HomeAssistant):
    """Test that duplicate entries are not allowed."""
    # Create mock client
    mock_client = AsyncMock()
    mock_client.async_authenticate = AsyncMock(return_value="test_auth_key")
    mock_client.async_get_user = AsyncMock(
        return_value={"email": MOCK_CONFIG_ENTRY[CONF_EMAIL]}
    )
    mock_client.async_close = AsyncMock()

    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}

    with patch(
        "custom_components.stremio.config_flow.StremioClient",
        return_value=mock_client,
    ), patch.object(flow, "async_set_unique_id", new_callable=AsyncMock), patch.object(
        flow,
        "_abort_if_unique_id_configured",
        side_effect=AbortFlow("already_configured"),
    ):
        # The AbortFlow exception should propagate up - the framework handles it
        with pytest.raises(AbortFlow) as exc_info:
            await flow.async_step_user(MOCK_CONFIG_ENTRY)

        assert exc_info.value.reason == "already_configured"
