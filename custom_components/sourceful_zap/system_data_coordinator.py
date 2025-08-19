import logging
from datetime import timedelta
from typing import Any

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class SystemDataCoordinator(DataUpdateCoordinator):
    """Coordinate system data fetching for Zap device information."""

    def __init__(self, hass: HomeAssistant, url: str, scan_interval: timedelta) -> None:
        """Initialize the system data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="SystemDataCoordinator",
            update_interval=scan_interval,
        )
        self.url = url
        self.session = async_get_clientsession(hass)
        self.device_info = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch system data from API."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Fetching system data from %s", self.url)
                response = await self.session.get(self.url)
                response.raise_for_status()
                data = await response.json()

                if "zap" in data:
                    self.device_info = {
                        "device_id": data["zap"].get("deviceId", "unknown"),
                        "firmware_version": data["zap"].get(
                            "firmwareVersion", "unknown"
                        ),
                        "sdk_version": data["zap"].get("sdkVersion", "unknown"),
                        "local_ip": data["zap"]
                        .get("network", {})
                        .get("localIP", "unknown"),
                    }

                _LOGGER.debug("Fetched system data successfully")
                return data

        except Exception as err:
            _LOGGER.error("Error fetching system data: %s", err)
            return {}

    def get_nested_value(self, path: str) -> Any:
        """Get nested value from data using dot notation."""
        value = self.data
        for key in path.split("."):
            try:
                value = value[key]
            except (KeyError, TypeError):
                return None
        return value
