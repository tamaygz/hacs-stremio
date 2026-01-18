"""Config flow for Stremio integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_PIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ADDON_STREAM_ORDER,
    CONF_APPLE_TV_CREDENTIALS,
    CONF_APPLE_TV_DEVICE,
    CONF_APPLE_TV_ENTITY_ID,
    CONF_APPLE_TV_IDENTIFIER,
    CONF_AUTH_KEY,
    CONF_DEFAULT_CATALOG_SOURCE,
    CONF_ENABLE_APPLE_TV_HANDOVER,
    CONF_HANDOVER_METHOD,
    CONF_LIBRARY_SCAN_INTERVAL,
    CONF_PLAYER_SCAN_INTERVAL,
    CONF_POLLING_GATE_ENTITIES,
    CONF_RESET_ADDON_ORDER,
    CONF_SHOW_COPY_URL,
    CONF_STREAM_QUALITY_PREFERENCE,
    DEFAULT_ADDON_STREAM_ORDER,
    DEFAULT_APPLE_TV_DEVICE,
    DEFAULT_APPLE_TV_ENTITY_ID,
    DEFAULT_CATALOG_SOURCE,
    DEFAULT_ENABLE_APPLE_TV_HANDOVER,
    DEFAULT_HANDOVER_METHOD,
    DEFAULT_LIBRARY_SCAN_INTERVAL,
    DEFAULT_PLAYER_SCAN_INTERVAL,
    DEFAULT_POLLING_GATE_ENTITIES,
    DEFAULT_SHOW_COPY_URL,
    DEFAULT_STREAM_QUALITY_PREFERENCE,
    DOMAIN,
    HANDOVER_METHOD_AIRPLAY,
    HANDOVER_METHODS,
    STREAM_QUALITY_OPTIONS,
)
from .dashboard_helper import async_create_testing_dashboard
from .stremio_client import StremioAuthError, StremioClient, StremioConnectionError

_LOGGER = logging.getLogger(__name__)

# Try to import pyatv for Apple TV pairing
try:
    import pyatv
    from pyatv.const import PairingRequirement, Protocol

    PYATV_AVAILABLE = True
except ImportError:
    PYATV_AVAILABLE = False
    _LOGGER.debug("pyatv not installed, Apple TV pairing will not be available")

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

    client = StremioClient(email, password)
    try:
        auth_key = await client.async_authenticate()

        if not auth_key:
            raise InvalidAuth("Authentication failed - no auth key received")

        # Validate the auth key by fetching user profile
        user = await client.async_get_user()

        if not user or not user.get("email"):
            raise InvalidAuth("Failed to fetch user profile")

        return {
            "title": user["email"],
            CONF_AUTH_KEY: auth_key,
            CONF_EMAIL: email,
        }

    except StremioAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise InvalidAuth from err
    except StremioConnectionError as err:
        _LOGGER.error("Connection failed: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during authentication: %s", err)
        raise CannotConnect from err
    finally:
        await client.async_close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
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
        self._config_entry = config_entry
        # State for Apple TV pairing flow
        self._discovered_devices: dict[str, Any] = {}
        self._selected_device: str | None = None
        self._atv_config: Any = None
        self._pairing: Any = None
        self._pending_options: dict[str, Any] = {}
        # Available addons fetched from API
        self._available_addons: list[dict[str, Any]] = []
        self._addon_names: list[str] = []
        # Track if user wants to create testing dashboard
        self._create_dashboard: bool = False

    async def _fetch_available_addons(self) -> None:
        """Fetch available addons from the Stremio API."""
        try:
            # Access the client from hass.data
            entry_data = self.hass.data.get(DOMAIN, {}).get(
                self._config_entry.entry_id, {}
            )
            client = entry_data.get("client")

            if client:
                # Get addon collection from client
                addon_collection = await client.async_get_addon_collection()
                if addon_collection:
                    self._available_addons = addon_collection
                    # Extract addon names (use transportName or manifest.name)
                    self._addon_names = []
                    for addon in addon_collection:
                        manifest = addon.get("manifest", {})
                        name = addon.get("transportName") or manifest.get("name", "")
                        if name:
                            self._addon_names.append(name)
                    _LOGGER.debug(
                        "Fetched %d addons: %s",
                        len(self._addon_names),
                        self._addon_names,
                    )
        except Exception as err:
            _LOGGER.warning("Failed to fetch addons: %s", err)
            self._available_addons = []
            self._addon_names = []

    def _build_addon_selector_options(
        self,
    ) -> list[selector.SelectOptionDict]:
        """Build options list for the addon selector."""
        options: list[selector.SelectOptionDict] = []
        seen: set[str] = set()

        for addon in self._available_addons:
            manifest = addon.get("manifest", {})
            addon_id = manifest.get("id", "")
            name = addon.get("transportName") or manifest.get("name", "")
            version = manifest.get("version", "")
            description = manifest.get("description", "")

            # Skip duplicates and empty names
            if not name or name in seen:
                continue
            seen.add(name)

            # Build display label
            label = name
            if version:
                label = f"{name} (v{version})"

            options.append(
                selector.SelectOptionDict(
                    value=name,
                    label=label,
                )
            )

        return options

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options - step 1: basic settings."""
        errors: dict[str, str] = {}

        # Fetch available addons if not already loaded
        if not self._available_addons:
            await self._fetch_available_addons()

        if user_input is not None:
            # Store the options for later
            self._pending_options = user_input

            # Handle reset addon order checkbox
            reset_order = user_input.pop(CONF_RESET_ADDON_ORDER, False)
            if reset_order:
                self._pending_options[CONF_ADDON_STREAM_ORDER] = []
            else:
                # Handle empty selection which may be omitted from user_input
                if CONF_ADDON_STREAM_ORDER not in user_input:
                    self._pending_options[CONF_ADDON_STREAM_ORDER] = []

            # Check if user wants to create testing dashboard
            self._create_dashboard = user_input.pop("create_testing_dashboard", False)

            # Check if we need to configure Apple TV
            enable_handover = user_input.get(
                CONF_ENABLE_APPLE_TV_HANDOVER, DEFAULT_ENABLE_APPLE_TV_HANDOVER
            )
            method = user_input.get(CONF_HANDOVER_METHOD, DEFAULT_HANDOVER_METHOD)

            # If AirPlay is enabled and pyatv is available, proceed to device selection
            if enable_handover and method in (HANDOVER_METHOD_AIRPLAY, "auto"):
                if not PYATV_AVAILABLE:
                    # pyatv not installed - show warning and continue with manual config
                    return await self.async_step_pyatv_missing()
                return await self.async_step_apple_tv_discover()

            # No Apple TV config needed, save options
            return self._create_options_entry()

        # Build addon options for the selector
        addon_options = self._build_addon_selector_options()

        # Get current addon order preference
        current_order = self._config_entry.options.get(
            CONF_ADDON_STREAM_ORDER, DEFAULT_ADDON_STREAM_ORDER
        )
        # Handle legacy string format (convert to list if needed)
        if isinstance(current_order, str):
            current_order = [
                name.strip() for name in current_order.split("\n") if name.strip()
            ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PLAYER_SCAN_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_PLAYER_SCAN_INTERVAL, DEFAULT_PLAYER_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_LIBRARY_SCAN_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_LIBRARY_SCAN_INTERVAL, DEFAULT_LIBRARY_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                    vol.Optional(
                        CONF_POLLING_GATE_ENTITIES,
                        default=self._config_entry.options.get(
                            CONF_POLLING_GATE_ENTITIES, DEFAULT_POLLING_GATE_ENTITIES
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[
                                "media_player",
                                "binary_sensor",
                                "switch",
                                "input_boolean",
                            ],
                            multiple=True,
                        ),
                    ),
                    vol.Optional(
                        CONF_ENABLE_APPLE_TV_HANDOVER,
                        default=self._config_entry.options.get(
                            CONF_ENABLE_APPLE_TV_HANDOVER,
                            DEFAULT_ENABLE_APPLE_TV_HANDOVER,
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_HANDOVER_METHOD,
                        default=self._config_entry.options.get(
                            CONF_HANDOVER_METHOD, DEFAULT_HANDOVER_METHOD
                        ),
                    ): vol.In(HANDOVER_METHODS),
                    vol.Optional(
                        CONF_APPLE_TV_ENTITY_ID,
                        default=self._config_entry.options.get(
                            CONF_APPLE_TV_ENTITY_ID, DEFAULT_APPLE_TV_ENTITY_ID
                        ),
                        description={
                            "suggested_value": self._config_entry.options.get(
                                CONF_APPLE_TV_ENTITY_ID, ""
                            )
                        },
                    ): str,
                    vol.Optional(
                        CONF_SHOW_COPY_URL,
                        default=self._config_entry.options.get(
                            CONF_SHOW_COPY_URL, DEFAULT_SHOW_COPY_URL
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_DEFAULT_CATALOG_SOURCE,
                        default=self._config_entry.options.get(
                            CONF_DEFAULT_CATALOG_SOURCE, DEFAULT_CATALOG_SOURCE
                        ),
                    ): str,
                    vol.Optional(
                        CONF_ADDON_STREAM_ORDER,
                        default=current_order,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=addon_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                            sort=False,  # Preserve user's selection order
                        ),
                    ),
                    vol.Optional(
                        CONF_RESET_ADDON_ORDER,
                        default=False,
                    ): bool,
                    vol.Optional(
                        CONF_STREAM_QUALITY_PREFERENCE,
                        default=self._config_entry.options.get(
                            CONF_STREAM_QUALITY_PREFERENCE,
                            DEFAULT_STREAM_QUALITY_PREFERENCE,
                        ),
                    ): vol.In(STREAM_QUALITY_OPTIONS),
                    vol.Optional(
                        "create_testing_dashboard",
                        default=False,
                    ): bool,
                }
            ),
            errors=errors,
            description_placeholders={
                "dashboard_info": "Creates a comprehensive testing dashboard with all Stremio card types"
            },
        )

    async def async_step_pyatv_missing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Inform user that pyatv is not installed."""
        if user_input is not None:
            # Continue with manual device name entry
            return await self.async_step_apple_tv_manual()

        return self.async_show_form(step_id="pyatv_missing")

    async def async_step_apple_tv_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual Apple TV configuration (when pyatv not available)."""
        if user_input is not None:
            self._pending_options[CONF_APPLE_TV_DEVICE] = user_input.get(
                CONF_APPLE_TV_DEVICE, ""
            )
            return self._create_options_entry()

        return self.async_show_form(
            step_id="apple_tv_manual",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_APPLE_TV_DEVICE,
                        default=self._config_entry.options.get(
                            CONF_APPLE_TV_DEVICE, DEFAULT_APPLE_TV_DEVICE
                        ),
                    ): str,
                }
            ),
        )

    async def async_step_apple_tv_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Discover and select Apple TV device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_device = user_input.get("device")
            if selected_device and selected_device in self._discovered_devices:
                self._selected_device = selected_device
                device_info = self._discovered_devices[selected_device]
                self._atv_config = device_info.get("config")

                # Store device info in pending options
                self._pending_options[CONF_APPLE_TV_DEVICE] = selected_device
                self._pending_options[CONF_APPLE_TV_IDENTIFIER] = device_info.get(
                    "identifier"
                )

                # Check if pairing is required
                return await self._check_pairing_requirement()
            else:
                errors["base"] = "device_not_found"

        # Discover devices
        try:
            await self._discover_apple_tv_devices()
        except Exception as err:
            _LOGGER.error("Failed to discover Apple TV devices: %s", err)
            errors["base"] = "discovery_failed"

        if not self._discovered_devices:
            errors["base"] = "no_devices_found"

        # Build device selection dropdown
        device_options = {
            name: f"{name} ({info.get('address', 'unknown')})"
            for name, info in self._discovered_devices.items()
        }

        # Add option to enter manually
        device_options["__manual__"] = "Enter device name manually..."

        return self.async_show_form(
            step_id="apple_tv_discover",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(device_options),
                }
            ),
            errors=errors,
            description_placeholders={
                "device_count": str(len(self._discovered_devices))
            },
        )

    async def _discover_apple_tv_devices(self) -> None:
        """Discover Apple TV devices on the network."""
        if not PYATV_AVAILABLE:
            return

        _LOGGER.debug("Scanning for Apple TV devices...")
        devices = await pyatv.scan(self.hass.loop, timeout=5)

        self._discovered_devices = {}
        for device in devices:
            self._discovered_devices[device.name] = {
                "name": device.name,
                "address": str(device.address),
                "identifier": device.identifier,
                "config": device,
                "services": [str(s.protocol) for s in device.services],
            }
            _LOGGER.debug(
                "Found Apple TV: %s at %s (services: %s)",
                device.name,
                device.address,
                [str(s.protocol) for s in device.services],
            )

    async def _check_pairing_requirement(self) -> FlowResult:
        """Check if pairing is required for the selected device."""
        if not PYATV_AVAILABLE or not self._atv_config:
            return self._create_options_entry()

        # Check if we have existing credentials
        existing_credentials = self._config_entry.options.get(CONF_APPLE_TV_CREDENTIALS)
        existing_identifier = self._config_entry.options.get(CONF_APPLE_TV_IDENTIFIER)

        # If same device and we have credentials, skip pairing
        current_identifier = self._pending_options.get(CONF_APPLE_TV_IDENTIFIER)
        if (
            existing_credentials
            and existing_identifier
            and existing_identifier == current_identifier
        ):
            _LOGGER.debug(
                "Using existing credentials for Apple TV '%s'", self._selected_device
            )
            self._pending_options[CONF_APPLE_TV_CREDENTIALS] = existing_credentials
            return self._create_options_entry()

        # Check AirPlay service for pairing requirement
        airplay_service = self._atv_config.get_service(Protocol.AirPlay)
        if airplay_service is None:
            _LOGGER.warning(
                "Apple TV '%s' does not have AirPlay service", self._selected_device
            )
            return self._create_options_entry()

        pairing_req = airplay_service.pairing
        _LOGGER.debug(
            "Apple TV '%s' AirPlay pairing requirement: %s",
            self._selected_device,
            pairing_req,
        )

        if pairing_req == PairingRequirement.NotNeeded:
            _LOGGER.debug("Pairing not required for '%s'", self._selected_device)
            return self._create_options_entry()

        if pairing_req == PairingRequirement.Unsupported:
            _LOGGER.debug("Pairing not supported for '%s'", self._selected_device)
            return self._create_options_entry()

        if pairing_req == PairingRequirement.Disabled:
            return await self.async_step_pairing_disabled()

        # Pairing is required (Mandatory or Optional)
        return await self.async_step_apple_tv_pair_start()

    async def async_step_pairing_disabled(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Inform user that pairing is disabled on the device."""
        if user_input is not None:
            # User acknowledged, continue without credentials
            return self._create_options_entry()

        return self.async_show_form(
            step_id="pairing_disabled",
            description_placeholders={"device": self._selected_device or "Unknown"},
        )

    async def async_step_apple_tv_pair_start(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Start the pairing process with Apple TV."""
        if not PYATV_AVAILABLE or not self._atv_config:
            return self._create_options_entry()

        errors: dict[str, str] = {}

        try:
            # Start pairing
            session = async_get_clientsession(self.hass)
            self._pairing = await pyatv.pair(
                self._atv_config,
                Protocol.AirPlay,
                self.hass.loop,
                session=session,
                name="Home Assistant Stremio",
            )
            await self._pairing.begin()

            # Check if device provides PIN (most common for Apple TV)
            if self._pairing.device_provides_pin:
                return await self.async_step_apple_tv_pair_pin()
            else:
                # Rare case: we provide PIN, device enters it
                return await self.async_step_apple_tv_pair_pin_device()

        except Exception as err:
            _LOGGER.error("Failed to start pairing: %s", err)
            errors["base"] = "pairing_start_failed"
            await self._cleanup_pairing()
            # Fall through to show error and continue
            return self._create_options_entry()

    async def async_step_apple_tv_pair_pin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle PIN entry for Apple TV pairing (device shows PIN)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = user_input.get(CONF_PIN)
            if pin and self._pairing:
                try:
                    self._pairing.pin(pin)
                    await self._pairing.finish()

                    if self._pairing.has_paired:
                        # Store credentials
                        credentials = self._pairing.service.credentials
                        self._pending_options[CONF_APPLE_TV_CREDENTIALS] = credentials
                        _LOGGER.info(
                            "Successfully paired with Apple TV '%s'",
                            self._selected_device,
                        )
                    else:
                        _LOGGER.warning(
                            "Pairing completed but device reports not paired"
                        )

                    await self._cleanup_pairing()
                    return self._create_options_entry()

                except Exception as err:
                    _LOGGER.error("Pairing failed: %s", err)
                    if "invalid" in str(err).lower() or "pin" in str(err).lower():
                        errors["base"] = "invalid_pin"
                    else:
                        errors["base"] = "pairing_failed"

        return self.async_show_form(
            step_id="apple_tv_pair_pin",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PIN): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=9999)
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"device": self._selected_device or "Apple TV"},
        )

    async def async_step_apple_tv_pair_pin_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle pairing when user must enter PIN on device."""
        import random

        if user_input is not None and self._pairing:
            try:
                await self._pairing.finish()

                if self._pairing.has_paired:
                    credentials = self._pairing.service.credentials
                    self._pending_options[CONF_APPLE_TV_CREDENTIALS] = credentials
                    _LOGGER.info(
                        "Successfully paired with Apple TV '%s'", self._selected_device
                    )

                await self._cleanup_pairing()
                return self._create_options_entry()

            except Exception as err:
                _LOGGER.error("Pairing failed: %s", err)
                await self._cleanup_pairing()
                return self._create_options_entry()

        # Generate random PIN for user to enter on device
        pin = random.randint(1000, 9999)
        if self._pairing:
            self._pairing.pin(pin)

        return self.async_show_form(
            step_id="apple_tv_pair_pin_device",
            description_placeholders={
                "device": self._selected_device or "Apple TV",
                "pin": str(pin),
            },
        )

    async def _cleanup_pairing(self) -> None:
        """Clean up pairing resources."""
        if self._pairing:
            try:
                await self._pairing.close()
            except Exception as err:
                _LOGGER.debug("Error closing pairing: %s", err)
            self._pairing = None

    def _create_options_entry(self) -> FlowResult:
        """Create the options entry with all collected data."""
        # If user requested dashboard creation, do it now
        if self._create_dashboard:
            # Try to find the media player entity
            try:
                from homeassistant.helpers import entity_registry as er
                
                entity_registry = er.async_get(self.hass)
                entity_id = None
                
                for entity in entity_registry.entities.values():
                    if (
                        entity.config_entry_id == self._config_entry.entry_id
                        and entity.domain == "media_player"
                    ):
                        entity_id = entity.entity_id
                        break

                if entity_id:
                    _LOGGER.info(
                        "Creating testing dashboard for entity: %s", entity_id
                    )
                    # Schedule the dashboard creation
                    self.hass.async_create_task(
                        async_create_testing_dashboard(self.hass, entity_id)
                    )
                else:
                    _LOGGER.warning(
                        "Could not find media player entity ID for dashboard creation"
                    )
            except Exception as err:
                _LOGGER.error("Error setting up dashboard creation: %s", err)

        return self.async_create_entry(title="", data=self._pending_options)
