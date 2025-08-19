"""System Sensor."""

import logging
from typing import Any

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)

from .const import DEFAULT_NAME, DOMAIN
from .system_data_coordinator import SystemDataCoordinator

_LOGGER = logging.getLogger(__name__)


class SystemSensor(SensorEntity):
    """Representation of a Zap system sensor."""

    def __init__(
        self,
        coordinator: SystemDataCoordinator,
        sensor_key: str,
        sensor_name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        icon: str | None = None,
        data_path: str = "",
        name_prefix: str = DEFAULT_NAME,
    ) -> None:
        """Initialize the system sensor."""
        self.coordinator = coordinator
        self.sensor_key = sensor_key
        self.data_path = data_path
        self._attr_name = f"{name_prefix} {sensor_name}"
        self._attr_unique_id = (
            f"{name_prefix.lower().replace(' ', '_')}_system_{sensor_key}"
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
        device_id = self.coordinator.device_info.get("device_id", "unknown")
        firmware_version = self.coordinator.device_info.get(
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

        value = self.coordinator.get_nested_value(self.data_path)
        if value is not None:
            # Round floating point values to 2 decimal places
            if isinstance(value, float):
                self._attr_native_value = round(value, 2)
            else:
                self._attr_native_value = value
            self._attr_available = True
        else:
            self._attr_available = False
            _LOGGER.debug(
                "System sensor %s: No data found at path %s",
                self.sensor_key,
                self.data_path,
            )
