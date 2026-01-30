"""API client for Zap Energy devices."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10  # seconds


class ZapApiError(Exception):
    """Base exception for Zap API errors."""


class ZapConnectionError(ZapApiError):
    """Error connecting to Zap device."""


class ZapApiClient:
    """Client for interacting with Zap local REST API."""

    def __init__(
        self, host: str, hass: HomeAssistant, api_path: str = "/api", timeout: int = REQUEST_TIMEOUT
    ) -> None:
        """Initialize the API client.

        Args:
            host: IP address or hostname of Zap gateway
            hass: Home Assistant instance
            api_path: Base API path (default: "/api")
            timeout: Request timeout in seconds (default: 10)

        """
        self.host = host.rstrip("/")
        self.api_path = api_path.rstrip("/")
        self.base_url = f"http://{self.host}{self.api_path}"
        self._session = async_get_clientsession(hass)
        self._timeout = timeout

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request to Zap API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for aiohttp request

        Returns:
            JSON response data

        Raises:
            ZapConnectionError: If connection fails
            ZapApiError: If API returns error

        """
        url = f"{self.base_url}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=self._timeout)

        try:
            async with self._session.request(
                method, url, timeout=timeout, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Connection refused to Zap API at %s: %s", url, err)
            raise ZapConnectionError(
                f"Cannot reach {url}. Please verify:\n"
                f"1. Device IP is correct ({self.host})\n"
                f"2. Device is powered on and connected to network\n"
                f"3. Home Assistant can reach this network\n"
                f"4. No firewall is blocking the connection"
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Zap API at %s: %s", url, err)
            raise ZapConnectionError(f"Failed to connect to {url}: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to Zap API at %s", url)
            raise ZapConnectionError(f"Timeout connecting to {url} (waited {self._timeout}s)") from err

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get list of devices connected to Zap gateway.

        Returns:
            List of device dictionaries with serial numbers and metadata

        """
        # Use relative path without the /api prefix since it's in base_url
        response = await self._request("GET", "/devices")

        # Handle both response formats:
        # 1. Direct list (older API): [{"serial_number": "...", ...}, ...]
        # 2. Dict with devices key (current API): {"count": 3, "devices": [...]}
        device_list = []
        if isinstance(response, dict) and "devices" in response:
            device_list = response["devices"]
        elif isinstance(response, list):
            device_list = response
        else:
            _LOGGER.warning("Unexpected response format from /devices: %s", type(response))
            return []

        devices = []
        for device in device_list:
            # Serial number can be "sn" or "serial_number"
            serial_number = device.get("sn") or device.get("serial_number")
            if serial_number:
                # Use profile for name if available, otherwise type
                device_name = device.get("profile") or device.get("type", "Device")
                device_name = device_name.replace("_", " ").title()

                devices.append(
                    {
                        "serial_number": serial_number,
                        "sn": serial_number,  # Keep both for compatibility
                        "name": f"{device_name} {serial_number}",
                        "manufacturer": device.get("manufacturer", "Sourceful Energy"),
                        "model": device.get("profile") or device.get("type", "Zap Smart Meter"),
                        "type": device.get("type"),
                        "profile": device.get("profile"),
                        "connection_status": device.get("connected"),
                        "last_harvest": device.get("last_harvest"),
                        "ders": device.get("ders", []),
                    }
                )

        return devices

    async def get_device_data(self, serial_number: str) -> dict[str, Any]:
        """Get real-time data for specific device.

        Args:
            serial_number: Device serial number

        Returns:
            Dictionary with power, energy, and state data

        """
        # Use relative path without the /api prefix
        endpoint = f"/devices/{serial_number}/data/json"
        return await self._request("GET", endpoint)

    async def get_device_ders(self, serial_number: str) -> dict[str, Any]:
        """Get DER (Distributed Energy Resource) metadata for device.

        Args:
            serial_number: Device serial number

        Returns:
            Dictionary with rated power, capacity, and installed power

        """
        # Use relative path without the /api prefix
        endpoint = f"/devices/{serial_number}/ders"
        return await self._request("GET", endpoint)

    async def get_system_info(self) -> dict[str, Any]:
        """Get Zap gateway system information.

        Returns:
            Dictionary with firmware version, uptime, temperature, etc.

        """
        # Use relative path without the /api prefix
        return await self._request("GET", "/system")

    async def test_connection(self) -> bool:
        """Test connection to Zap gateway.

        Returns:
            True if connection successful, False otherwise

        """
        try:
            await self.get_devices()
            return True
        except ZapApiError:
            return False
