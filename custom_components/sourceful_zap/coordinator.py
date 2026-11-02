"""Data update coordinator for Zap Energy integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ZapApiClient, ZapApiError
from .const import DOMAIN, GATEWAY_POLL_INTERVAL
from .datamodel import ZapDeviceData, parse_device_data, validate_numeric

_LOGGER = logging.getLogger(__name__)


class ZapGatewayData(TypedDict, total=False):
    """Type definition for Zap gateway system data."""

    uptime_seconds: int | None
    gateway_temperature: float | None
    memory_percent: float | None
    memory_free: float | None
    firmware_version: str | None
    wifi_status: str | None
    wifi_ssid: str | None
    signal_strength: float | None


class ZapGatewayCoordinator(DataUpdateCoordinator[ZapGatewayData]):
    """Coordinator for fetching gateway-level system info."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: ZapApiClient,
    ) -> None:
        """Initialize the gateway coordinator."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_gateway",
            update_interval=timedelta(seconds=GATEWAY_POLL_INTERVAL),
        )

    async def _async_update_data(self) -> ZapGatewayData:
        """Fetch gateway system info."""
        try:
            system_info = await self.api.get_system_info()
        except ZapApiError as err:
            raise UpdateFailed("Error fetching gateway system info") from err

        data: ZapGatewayData = {}

        if not system_info:
            return data

        # Uptime (firmware 2.x uses camelCase; snake_case kept as legacy fallback)
        uptime = system_info.get("uptimeSeconds", system_info.get("uptime_seconds"))
        if uptime is not None:
            try:
                data["uptime_seconds"] = int(uptime)
            except (ValueError, TypeError):
                pass

        # Temperature
        temp = validate_numeric(
            system_info.get(
                "temperatureCelsius", system_info.get("temperature_celsius")
            ),
            "gateway.temperatureCelsius",
            min_value=-40,
            max_value=150,
        )
        if temp is not None:
            data["gateway_temperature"] = temp

        # Memory
        memory = system_info.get("memoryKb", system_info.get("memory_kb", {}))
        if isinstance(memory, dict):
            pct = validate_numeric(
                memory.get("percentUsed", memory.get("percent_used")),
                "memoryKb.percentUsed",
                min_value=0,
                max_value=100,
            )
            if pct is not None:
                data["memory_percent"] = pct
            free = validate_numeric(
                memory.get("free"),
                "memoryKb.free",
                min_value=0,
            )
            if free is not None:
                data["memory_free"] = free

        # Zap info (firmware, network)
        zap_info = system_info.get("zap", {})
        if isinstance(zap_info, dict):
            fw = zap_info.get("firmwareVersion")
            if fw is not None:
                data["firmware_version"] = str(fw)

            network = zap_info.get("network", {})
            if isinstance(network, dict):
                wifi_status = network.get("wifiStatus")
                if wifi_status is not None:
                    data["wifi_status"] = str(wifi_status)

                ssid = network.get("ssid")
                if ssid is not None:
                    data["wifi_ssid"] = str(ssid)

                rssi = validate_numeric(
                    network.get("rssi"),
                    "zap.network.rssi",
                    min_value=-120,
                    max_value=0,
                )
                if rssi is not None:
                    data["signal_strength"] = rssi

        _LOGGER.debug("Gateway system data: %s", data)
        return data


class ZapDataUpdateCoordinator(DataUpdateCoordinator[ZapDeviceData]):
    """Class to manage fetching Zap device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: ZapApiClient,
        serial_number: str,
        polling_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            entry: Config entry owning this coordinator
            api: Zap API client
            serial_number: Device serial number
            polling_interval: Update interval in seconds

        """
        self.api = api
        self.serial_number = serial_number
        # Enabled DER types from the last successful /ders response.
        # Empty until the first refresh; sensor setup falls back to /devices.
        self.der_types: list[str] = []

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{serial_number}",
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self) -> ZapDeviceData:
        """Fetch data from Zap API.

        Returns:
            Structured device data

        Raises:
            UpdateFailed: If data fetch fails

        """
        try:
            device_data = await self.api.get_device_data(self.serial_number)
            device_ders_response = await self.api.get_device_ders(self.serial_number)

            _LOGGER.debug("Raw device data for %s: %s", self.serial_number, device_data)

            if not isinstance(device_data, dict):
                device_data = {}
            if not isinstance(device_ders_response, dict):
                device_ders_response = {}

            data, der_types = parse_device_data(
                device_data, device_ders_response, self.serial_number
            )
            self.der_types = der_types

            _LOGGER.debug("Parsed data for Zap device %s: %s", self.serial_number, data)
            return data

        except ZapApiError as err:
            raise UpdateFailed(f"Error fetching data for {self.serial_number}") from err
