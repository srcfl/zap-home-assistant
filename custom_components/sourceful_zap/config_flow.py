"""Config flow for Zap Energy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import ZapApiClient, ZapConnectionError
from .const import (
    CONF_POLLING_INTERVAL,
    DEFAULT_API_PATH,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    MIN_POLLING_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input and test connection.

    Args:
        hass: Home Assistant instance
        data: User input data with host

    Returns:
        Dictionary with device info (serial number, title)

    Raises:
        ZapConnectionError: If connection fails

    """
    host = data[CONF_HOST]

    _LOGGER.debug(
        "Attempting to connect to Zap gateway at %s with API path %s",
        host,
        DEFAULT_API_PATH
    )

    api = ZapApiClient(host, hass, api_path=DEFAULT_API_PATH)

    _LOGGER.debug("Testing connection to %s", api.base_url)

    # Test connection
    if not await api.test_connection():
        _LOGGER.error("Failed to connect to Zap gateway at %s", api.base_url)
        raise ZapConnectionError("Cannot connect to Zap gateway")

    # Get system info to extract gateway serial number
    _LOGGER.debug("Connection successful, fetching system info")
    system_info = await api.get_system_info()
    _LOGGER.debug("System info response: %s", system_info)

    # Try to get gateway serial from system info with multiple fallbacks
    gateway_serial = None

    # Try different possible locations for serial number
    if system_info:
        zap_info = system_info.get("zap")
        if isinstance(zap_info, dict):
            # Try common serial number fields
            gateway_serial = (
                zap_info.get("sn") or
                zap_info.get("serial_number") or
                zap_info.get("serialNumber") or
                zap_info.get("deviceId")
            )

        # Also check top-level fields
        if not gateway_serial:
            gateway_serial = (
                system_info.get("sn") or
                system_info.get("serial_number") or
                system_info.get("serialNumber")
            )

    # If still no serial, use first device's serial as gateway identifier
    if not gateway_serial:
        _LOGGER.warning("Could not find gateway serial in system info, will use first device serial")

    _LOGGER.debug("Gateway serial from system: %s", gateway_serial)

    # Get devices to verify gateway has devices
    devices = await api.get_devices()
    if not devices:
        _LOGGER.warning("No devices found on gateway at %s", api.base_url)
        raise ZapConnectionError("No devices found on gateway")

    _LOGGER.debug("Found %d device(s)", len(devices))

    # If we couldn't find a gateway serial, use the first device's serial
    if not gateway_serial:
        gateway_serial = devices[0].get("serial_number")
        _LOGGER.debug("Using first device serial as gateway ID: %s", gateway_serial)

    return {
        "serial_number": gateway_serial,
        "title": f"Sourceful Zap {gateway_serial}",
    }


class ZapEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zap Energy."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.

        Args:
            user_input: User-provided configuration data

        Returns:
            FlowResult with form or entry creation

        """
        return await self.async_step_manual(user_input)

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual IP entry.

        Args:
            user_input: User-provided configuration data

        Returns:
            FlowResult with form or entry creation

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Sanitize host input: remove protocols, trailing slashes
            host = user_input[CONF_HOST].strip()
            host = host.replace("http://", "").replace("https://", "")
            host = host.rstrip("/")
            user_input[CONF_HOST] = host

            _LOGGER.debug(
                "Manual entry: User entered host=%s, polling_interval=%s",
                host,
                user_input.get(CONF_POLLING_INTERVAL)
            )

            try:
                info = await validate_input(self.hass, user_input)
            except ZapConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during validation")
                errors["base"] = "unknown"
            else:
                # Set unique ID to prevent duplicate entries
                serial_number = info["serial_number"]
                await self.async_set_unique_id(serial_number)

                _LOGGER.debug(
                    "Device validated successfully: serial=%s, host=%s",
                    serial_number,
                    user_input[CONF_HOST]
                )

                # Update existing entry if already configured (allows changing IP/settings)
                self._abort_if_unique_id_configured(
                    updates=user_input,
                    reload_on_update=True
                )

                _LOGGER.debug("Creating new entry for device %s at %s", serial_number, user_input[CONF_HOST])
                return self.async_create_entry(title=info["title"], data=user_input)

        # Manual entry form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=""): str,
                vol.Optional(
                    CONF_POLLING_INTERVAL,
                    default=DEFAULT_POLLING_INTERVAL,
                ): vol.All(cv.positive_int, vol.Range(min=MIN_POLLING_INTERVAL)),
            }
        )

        return self.async_show_form(
            step_id="manual", data_schema=data_schema, errors=errors
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery.

        Args:
            discovery_info: Zeroconf discovery information

        Returns:
            FlowResult with form or abort

        """
        host = str(discovery_info.ip_address)
        _LOGGER.debug("Zeroconf discovered potential Zap device at %s", host)

        # Store discovery info for later use
        self._discovery_info = {
            CONF_HOST: host,
            "name": discovery_info.name,
        }

        # Validate connection
        try:
            api = ZapApiClient(host, self.hass, api_path=DEFAULT_API_PATH)

            if not await api.test_connection():
                _LOGGER.debug("Zeroconf device at %s failed connection test", host)
                return self.async_abort(reason="cannot_connect")

            # Verify this is a Zap device
            system_info = await api.get_system_info()
            if not system_info or "zap" not in system_info:
                _LOGGER.debug("Device at %s is not a Zap gateway", host)
                return self.async_abort(reason="cannot_connect")

            # Get devices
            devices = await api.get_devices()
            if not devices:
                _LOGGER.debug("No devices found on Zap gateway at %s", host)
                return self.async_abort(reason="cannot_connect")

            # Get serial number for unique ID
            first_device = devices[0]
            serial_number = first_device.get("serial_number")
            device_name = first_device.get("name", f"Zap {serial_number}")

            self._discovery_info["serial_number"] = serial_number
            self._discovery_info["device_name"] = device_name

            # Set unique ID and abort if already configured
            await self.async_set_unique_id(serial_number)
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})

            _LOGGER.debug(
                "Zeroconf: Found Zap device %s (%s) at %s",
                device_name,
                serial_number,
                host,
            )

            return self.async_show_form(
                step_id="zeroconf_confirm",
                description_placeholders={"name": device_name},
            )

        except ZapConnectionError as err:
            _LOGGER.debug("Zeroconf connection error: %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception as err:
            _LOGGER.debug("Zeroconf unexpected error: %s", err)
            return self.async_abort(reason="cannot_connect")

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle zeroconf confirmation step.

        Args:
            user_input: User confirmation

        Returns:
            FlowResult with entry creation

        """
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.get("device_name", "Zap Device"),
                data={CONF_HOST: self._discovery_info[CONF_HOST]},
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._discovery_info.get("device_name", "Zap Device")
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ZapEnergyOptionsFlowHandler:
        """Get the options flow handler.

        Args:
            config_entry: Config entry instance

        Returns:
            Options flow handler

        """
        return ZapEnergyOptionsFlowHandler(config_entry)


class ZapEnergyOptionsFlowHandler(config_entries.OptionsFlow):  # pylint: disable=too-few-public-methods
    """Handle options flow for Zap Energy integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        Args:
            config_entry: Config entry instance

        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.

        Args:
            user_input: User-provided options

        Returns:
            FlowResult with form or entry update

        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLLING_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
                        ),
                    ): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_POLLING_INTERVAL),
                    ),
                }
            ),
        )
