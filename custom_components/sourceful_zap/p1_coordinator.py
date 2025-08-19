import logging
import re
from datetime import timedelta
from typing import Any

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class P1DataCoordinator(DataUpdateCoordinator):
    """Coordinate data fetching for all P1 sensors."""

    def __init__(self, hass: HomeAssistant, url: str, scan_interval: timedelta) -> None:
        """Initialize the data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="P1DataCoordinator",
            update_interval=scan_interval,
        )
        self.url = url
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from API."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Fetching data from %s", self.url)
                response = await self.session.get(self.url)
                response.raise_for_status()
                json_data = await response.json()

                if json_data.get("status") == "success":
                    parsed_data = self._parse_obis_data(json_data.get("data", []))
                    _LOGGER.debug("Parsed %d OBIS codes", len(parsed_data))
                    return parsed_data
                else:
                    _LOGGER.error("API returned error: %s", json_data.get("status"))
                    return {}

        except Exception as err:
            _LOGGER.error("Error fetching P1 data: %s", err)
            return {}

    def _parse_obis_data(self, data_lines: list[str]) -> dict[str, dict[str, Any]]:
        """Parse OBIS data lines into dictionary."""
        parsed = {}
        pattern = r"(\d+-\d+:\d+\.\d+\.\d+)\(([0-9.-]+)\*?([^)]*)\)"

        for line in data_lines:
            match = re.match(pattern, line)
            if match:
                obis_code = match.group(1)
                try:
                    value = float(match.group(2))
                    unit = match.group(3) if match.group(3) else None
                    parsed[obis_code] = {"value": value, "unit": unit}
                except ValueError:
                    _LOGGER.warning("Could not parse value from line: %s", line)
            elif line.startswith("0-0:1.0.0"):
                _LOGGER.debug("Timestamp: %s", line)
            else:
                _LOGGER.debug("Could not parse line: %s", line)

        return parsed
