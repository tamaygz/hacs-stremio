"""Config flow for Stremio integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from stremio_api import StremioAPIClient

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_AUTH_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    email = data[CONF_EMAIL]
    password = data[CONF_PASSWORD]

    try:
        async with StremioAPIClient(auth_key=None) as client:
            auth_key = await client.login(email, password)
            
            if not auth_key:
                raise InvalidAuth("Authentication failed - no auth key received")
            
            # Validate the auth key by fetching user profile
            async with StremioAPIClient(auth_key=auth_key) as validated_client:
                user = await validated_client.get_user()
                
                if not user or not hasattr(user, "email"):
                    raise InvalidAuth("Failed to fetch user profile")

                return {
                    "title": user.email,
                    CONF_AUTH_KEY: auth_key,
                    CONF_EMAIL: email,
                }
                
    except Exception as err:
        _LOGGER.exception("Unexpected error during authentication: %s", err)
        if "401" in str(err) or "authentication" in str(err).lower():
            raise InvalidAuth from err
        raise CannotConnect from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stremio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on email to prevent duplicate entries
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_AUTH_KEY: info[CONF_AUTH_KEY],
                        CONF_EMAIL: info[CONF_EMAIL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
