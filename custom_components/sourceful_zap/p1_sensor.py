"""P1 Sensor."""

import logging
from typing import Any

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)

from .const import DEFAULT_NAME, DOMAIN
from .p1_coordinator import P1DataCoordinator
from .system_data_coordinator import SystemDataCoordinator

_LOGGER = logging.getLogger(__name__)


class P1Sensor(SensorEntity):
    """Representation of a P1 meter sensor."""

    def __init__(
        self,
        coordinator: P1DataCoordinator,
        system_coordinator: SystemDataCoordinator,
        obis_code: str,
        sensor_name: str,
        unit: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        icon: str | None = None,
        name_prefix: str = DEFAULT_NAME,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.system_coordinator = system_coordinator
        self.obis_code = obis_code
        self._attr_name = f"{name_prefix} {sensor_name}"
        self._attr_unique_id = (
            f"{name_prefix.lower().replace(' ', '_')}_"
            f"{obis_code.replace(':', '_').replace('-', '_')}"
        )
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        self._attr_native_value = None
        self._attr_available = True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_id = self.system_coordinator.device_info.get("device_id", "unknown")
        firmware_version = self.system_coordinator.device_info.get(
            "firmware_version", "unknown"
        )

        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": "Sourceful Energy Zap",
            "manufacturer": "Sourceful Labs AB",
            "model": "Zap P1 Reader",
            "sw_version": firmware_version,
            "configuration_url": "http://zap.local/",
        }

    async def async_update(self) -> None:
        """Update the sensor."""
        await self.coordinator.async_update()

        if self.obis_code in self.coordinator.data:
            self._attr_native_value = self.coordinator.data[self.obis_code]["value"]
            self._attr_available = True
        else:
            self._attr_available = False
            _LOGGER.debug("OBIS code %s not found in data", self.obis_code)
