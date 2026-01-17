"""Config flow for Stremio integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from stremio_api import StremioAPIClient

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_AUTH_KEY,
    CONF_ENABLE_APPLE_TV_HANDOVER,
    CONF_HANDOVER_METHOD,
    CONF_LIBRARY_SCAN_INTERVAL,
    CONF_PLAYER_SCAN_INTERVAL,
    DEFAULT_ENABLE_APPLE_TV_HANDOVER,
    DEFAULT_HANDOVER_METHOD,
    DEFAULT_LIBRARY_SCAN_INTERVAL,
    DEFAULT_PLAYER_SCAN_INTERVAL,
    DOMAIN,
    HANDOVER_METHODS,
)

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

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
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
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


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Stremio integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PLAYER_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_PLAYER_SCAN_INTERVAL, DEFAULT_PLAYER_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_LIBRARY_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_LIBRARY_SCAN_INTERVAL, DEFAULT_LIBRARY_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                    vol.Optional(
                        CONF_ENABLE_APPLE_TV_HANDOVER,
                        default=self.config_entry.options.get(
                            CONF_ENABLE_APPLE_TV_HANDOVER, DEFAULT_ENABLE_APPLE_TV_HANDOVER
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_HANDOVER_METHOD,
                        default=self.config_entry.options.get(
                            CONF_HANDOVER_METHOD, DEFAULT_HANDOVER_METHOD
                        ),
                    ): vol.In(HANDOVER_METHODS),
                }
            ),
        )

