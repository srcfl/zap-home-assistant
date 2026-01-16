"""Config flow for Zap Energy integration."""

from __future__ import annotations

import asyncio
import logging
import socket
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
    CONF_API_PATH,
    CONF_POLLING_INTERVAL,
    DEFAULT_API_PATH,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    MIN_POLLING_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_API_PATH, default=DEFAULT_API_PATH): str,
    }
)


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
        _LOGGER.info("Using first device serial as gateway ID: %s", gateway_serial)

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
        self._discovered_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None  # pylint: disable=unused-argument
    ) -> FlowResult:
        """Handle the initial step (show menu: manual or scan).

        Args:
            user_input: User-provided configuration data

        Returns:
            FlowResult with menu

        """
        return self.async_show_menu(
            step_id="user",
            menu_options=["manual", "scan"],
        )

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

            _LOGGER.info(
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

                _LOGGER.info(
                    "Device validated successfully: serial=%s, host=%s",
                    serial_number,
                    user_input[CONF_HOST]
                )

                # Update existing entry if already configured (allows changing IP/settings)
                self._abort_if_unique_id_configured(
                    updates=user_input,
                    reload_on_update=True
                )

                _LOGGER.info("Creating new entry for device %s at %s", serial_number, user_input[CONF_HOST])
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

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle network scan for Zap devices.

        Args:
            user_input: User selection from discovered devices

        Returns:
            FlowResult with discovered devices or manual entry

        """
        if user_input is not None:
            # User selected a discovered device
            selected_host = user_input["discovered_device"]
            polling_interval = user_input.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)

            # Sanitize host input
            selected_host = selected_host.strip()
            selected_host = selected_host.replace("http://", "").replace("https://", "")
            selected_host = selected_host.rstrip("/")

            data = {
                CONF_HOST: selected_host,
                CONF_POLLING_INTERVAL: polling_interval,
            }

            try:
                info = await validate_input(self.hass, data)
            except ZapConnectionError:
                return self.async_abort(reason="cannot_connect")

            await self.async_set_unique_id(info["serial_number"])
            # Update existing entry if already configured (allows changing IP/settings)
            self._abort_if_unique_id_configured(updates=data)

            return self.async_create_entry(title=info["title"], data=data)

        # Scan local network for Zap devices
        _LOGGER.info("Starting network scan for Zap devices...")

        discovered_devices = await self._scan_network()

        if not discovered_devices:
            _LOGGER.warning("No Zap devices found during network scan")
            return self.async_abort(
                reason="no_devices_found",
                description_placeholders={
                    "message": "No Zap devices found on the network. Please use manual IP entry."
                },
            )

        # Create device selection dropdown
        device_options = {
            device["host"]: f"{device['host']} ({device.get('name', 'Zap Device')})"
            for device in discovered_devices
        }

        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema(
                {
                    vol.Required("discovered_device"): vol.In(device_options),
                    vol.Optional(
                        CONF_POLLING_INTERVAL,
                        default=DEFAULT_POLLING_INTERVAL,
                    ): vol.All(cv.positive_int, vol.Range(min=MIN_POLLING_INTERVAL)),
                }
            ),
        )

    async def _scan_network(self) -> list[dict[str, Any]]:
        """Scan local network for Zap devices.

        Returns:
            List of discovered devices with host and name
        """
        import ipaddress

        discovered = []

        # Get Home Assistant's local IP to determine subnet
        try:
            # Try to get the actual host network IP (not Docker internal)
            # Method 1: Check all network interfaces for non-Docker IPs
            local_ips = []

            # Get HA network info if available
            if hasattr(self.hass, 'config') and hasattr(self.hass.config, 'api'):
                # Try to get HA's external URL host
                try:
                    from homeassistant.helpers.network import get_url
                    ha_url = get_url(self.hass, allow_internal=True, allow_external=False)
                    if ha_url:
                        from urllib.parse import urlparse
                        parsed = urlparse(ha_url)
                        if parsed.hostname:
                            local_ips.append(parsed.hostname)
                            _LOGGER.debug("Got HA URL host: %s", parsed.hostname)
                except Exception as err:
                    _LOGGER.debug("Could not get HA URL: %s", err)

            # Method 2: Connect to external address to determine route
            # This works even in Docker by finding the route to external network
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.1)
                # Connect to a public DNS server (doesn't actually send data)
                s.connect(('8.8.8.8', 80))
                route_ip = s.getsockname()[0]
                s.close()
                if route_ip and not route_ip.startswith('127.'):
                    local_ips.append(route_ip)
                    _LOGGER.debug("Got IP from route check: %s", route_ip)
            except Exception as err:
                _LOGGER.debug("Route check failed: %s", err)

            # Method 3: Fallback to hostname resolution
            if not local_ips:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                local_ips.append(local_ip)
                _LOGGER.debug("Fallback to hostname IP: %s", local_ip)

            # Use first non-Docker IP (prefer 192.168.x.x or 10.x.x.x)
            local_ip = None
            for ip in local_ips:
                if ip.startswith('192.168.') or ip.startswith('10.'):
                    local_ip = ip
                    break

            if not local_ip and local_ips:
                local_ip = local_ips[0]

            if not local_ip:
                _LOGGER.error("Could not determine local network IP")
                return []

            _LOGGER.info("Using local IP for network scan: %s", local_ip)

            # Create subnet to scan (e.g., 192.168.1.0/24)
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            _LOGGER.info("Scanning network: %s (254 hosts)", network)

            # Scan entire /24 subnet (all 254 hosts)
            scan_range = list(network.hosts())
            total_hosts = len(scan_range)

            _LOGGER.info("Starting scan of %d IP addresses...", total_hosts)

            # Scan IPs in parallel (batches of 50 for faster scanning)
            batch_size = 50
            for i in range(0, len(scan_range), batch_size):
                batch = scan_range[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(scan_range) + batch_size - 1) // batch_size

                _LOGGER.info(
                    "Scanning batch %d/%d (IPs %d-%d of %d)",
                    batch_num,
                    total_batches,
                    i + 1,
                    min(i + batch_size, total_hosts),
                    total_hosts
                )

                tasks = [self._check_host(str(ip)) for ip in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, dict) and result:
                        discovered.append(result)
                        _LOGGER.info("Found Zap device at %s", result["host"])

        except Exception as err:
            _LOGGER.error("Error during network scan: %s", err)

        _LOGGER.info("Network scan complete. Found %d Zap device(s)", len(discovered))
        return discovered

    async def _check_host(self, host: str) -> dict[str, Any] | None:
        """Check if a host is a Zap device.

        Args:
            host: IP address to check

        Returns:
            Device info dict if Zap device found, None otherwise
        """
        try:
            # Use 5s timeout for scanning (allows for slow network responses)
            api = ZapApiClient(host, self.hass, api_path=DEFAULT_API_PATH, timeout=5)

            # First, verify this is a Zap device by checking /api/system
            system_info = await api.get_system_info()

            # Check if response contains "zap" property (can be dict or string)
            if not system_info:
                return None

            # Zap property can be a dict or a string/version number
            has_zap = "zap" in system_info

            if not has_zap:
                _LOGGER.debug("Host %s responded but no 'zap' property found", host)
                return None

            zap_info = system_info.get("zap", {})
            if isinstance(zap_info, dict):
                device_id = zap_info.get("deviceId", "unknown")
            else:
                device_id = str(zap_info)

            _LOGGER.info("✓ Found Zap gateway at %s (ID: %s)", host, device_id)

            # Now get devices to verify gateway has devices
            devices = await api.get_devices()

            if devices:
                device_count = len(devices)
                _LOGGER.info("  Gateway has %d device(s) connected", device_count)

                # Return gateway info with device count
                return {
                    "host": host,
                    "name": f"Zap Gateway ({device_count} devices)",
                    "device_count": device_count,
                }
            else:
                _LOGGER.warning("Found Zap at %s but no devices connected", host)
                return None

        except asyncio.TimeoutError:
            # Timeout - likely no device at this IP, skip silently
            _LOGGER.debug("Timeout checking %s", host)
        except Exception as err:
            # Log connection errors for known Zap IPs only
            if "192.168.1.248" in host:
                _LOGGER.warning("Error checking known Zap at %s: %s", host, err)
            else:
                _LOGGER.debug("Host %s check failed: %s", host, err)

        return None

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
        _LOGGER.info("Zeroconf discovered potential Zap device at %s", host)

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

            _LOGGER.info(
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
