"""Sensor platform for Zap Energy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZapDataUpdateCoordinator, ZapDeviceData

_LOGGER = logging.getLogger(__name__)


@dataclass
class ZapSensorEntityDescription(SensorEntityDescription):
    """Describes Zap sensor entity."""

    value_fn: Callable[[ZapDeviceData], StateType] | None = None
    available_fn: Callable[[ZapDeviceData], bool] | None = None


SENSOR_TYPES: tuple[ZapSensorEntityDescription, ...] = (
    ZapSensorEntityDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("power"),
        available_fn=lambda data: data.get("power") is not None,
    ),
    ZapSensorEntityDescription(
        key="energy_import",
        translation_key="energy_import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("energy_import"),
        available_fn=lambda data: data.get("energy_import") is not None,
    ),
    ZapSensorEntityDescription(
        key="energy_production",
        translation_key="energy_production",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("energy_production"),
        available_fn=lambda data: data.get("energy_production") is not None,
    ),
    ZapSensorEntityDescription(
        key="energy_export",
        translation_key="energy_export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("energy_export"),
        available_fn=lambda data: data.get("energy_export") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("battery_soc"),
        available_fn=lambda data: data.get("battery_soc") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("battery_voltage"),
        available_fn=lambda data: data.get("battery_voltage") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_current",
        translation_key="battery_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("battery_current"),
        available_fn=lambda data: data.get("battery_current") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_charge_total",
        translation_key="battery_charge_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("battery_charge_total"),
        available_fn=lambda data: data.get("battery_charge_total") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_discharge_total",
        translation_key="battery_discharge_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("battery_discharge_total"),
        available_fn=lambda data: data.get("battery_discharge_total") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_upper_limit",
        translation_key="battery_upper_limit",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_registry_enabled_default=False,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("battery_upper_limit"),
        available_fn=lambda data: data.get("battery_upper_limit") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_lower_limit",
        translation_key="battery_lower_limit",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_registry_enabled_default=False,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("battery_lower_limit"),
        available_fn=lambda data: data.get("battery_lower_limit") is not None,
    ),
    ZapSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("temperature"),
        available_fn=lambda data: data.get("temperature") is not None,
    ),
    ZapSensorEntityDescription(
        key="signal_strength",
        translation_key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_registry_enabled_default=False,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("signal_strength"),
        available_fn=lambda data: data.get("signal_strength") is not None,
    ),
    # L1 Phase measurements
    ZapSensorEntityDescription(
        key="l1_voltage",
        translation_key="l1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("l1_voltage"),
        available_fn=lambda data: data.get("l1_voltage") is not None,
    ),
    ZapSensorEntityDescription(
        key="l1_current",
        translation_key="l1_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("l1_current"),
        available_fn=lambda data: data.get("l1_current") is not None,
    ),
    ZapSensorEntityDescription(
        key="l1_power",
        translation_key="l1_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("l1_power"),
        available_fn=lambda data: data.get("l1_power") is not None,
    ),
    # L2 Phase measurements
    ZapSensorEntityDescription(
        key="l2_voltage",
        translation_key="l2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("l2_voltage"),
        available_fn=lambda data: data.get("l2_voltage") is not None,
    ),
    ZapSensorEntityDescription(
        key="l2_current",
        translation_key="l2_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("l2_current"),
        available_fn=lambda data: data.get("l2_current") is not None,
    ),
    ZapSensorEntityDescription(
        key="l2_power",
        translation_key="l2_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("l2_power"),
        available_fn=lambda data: data.get("l2_power") is not None,
    ),
    # L3 Phase measurements
    ZapSensorEntityDescription(
        key="l3_voltage",
        translation_key="l3_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("l3_voltage"),
        available_fn=lambda data: data.get("l3_voltage") is not None,
    ),
    ZapSensorEntityDescription(
        key="l3_current",
        translation_key="l3_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("l3_current"),
        available_fn=lambda data: data.get("l3_current") is not None,
    ),
    ZapSensorEntityDescription(
        key="l3_power",
        translation_key="l3_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("l3_power"),
        available_fn=lambda data: data.get("l3_power") is not None,
    ),
    # Battery power (separate from aggregated power)
    ZapSensorEntityDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("battery_power"),
        available_fn=lambda data: data.get("battery_power") is not None,
    ),
    # Battery temperature (separate from general/PV temperature)
    ZapSensorEntityDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("battery_temperature"),
        available_fn=lambda data: data.get("battery_temperature") is not None,
    ),
    # Grid frequency
    ZapSensorEntityDescription(
        key="grid_frequency",
        translation_key="grid_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("grid_frequency"),
        available_fn=lambda data: data.get("grid_frequency") is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zap Energy sensors from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities

    """
    coordinators: dict[str, ZapDataUpdateCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]["coordinators"]

    # Get gateway serial for entity naming
    gateway_serial = hass.data[DOMAIN][entry.entry_id]["gateway_serial"]

    entities: list[ZapSensor] = []

    # Get device list to check DERs
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    devices = await api.get_devices()

    # Create a map of serial number to DER types and device info
    device_info_map: dict[str, dict[str, Any]] = {}
    for device in devices:
        serial = device.get("serial_number")
        ders = device.get("ders", [])
        der_types = [der.get("type") for der in ders if der.get("enabled", True)]
        # Get device profile/model for entity naming
        profile = device.get("model", "").replace(" ", "_").lower()
        device_info_map[serial] = {
            "der_types": der_types,
            "profile": profile,
        }
        _LOGGER.debug("Device %s has DERs: %s, profile: %s", serial, der_types, profile)

    for serial_number, coordinator in coordinators.items():
        device_info = device_info_map.get(serial_number, {})
        der_types = device_info.get("der_types", [])
        device_profile = device_info.get("profile", "device")

        for description in SENSOR_TYPES:
            # Only create sensors that make sense for this device's DERs
            if should_create_sensor(description.key, der_types):
                entities.append(
                    ZapSensor(
                        coordinator,
                        description,
                        serial_number,
                        device_profile,
                        gateway_serial,
                    )
                )
            else:
                _LOGGER.debug(
                    "Skipping %s sensor for %s (DERs: %s)",
                    description.key,
                    serial_number,
                    der_types
                )

    async_add_entities(entities)


def should_create_sensor(sensor_key: str, der_types: list[str]) -> bool:
    """Determine if a sensor should be created based on device DERs.

    Based on actual API response formats:
    - Battery: W, V, A, SoC_nom_fract, heatsink_C, total_charge/discharge_Wh, upper/lower_limit_W
    - PV: W, rated_power_W, mppt1/2_V/A, heatsink_C, total_generation_Wh
    - PV meter: W, Hz, L1/2/3_V/A/W, total_import/export_Wh
    - p1_uart meter: W, L1/2/3_V/A/W, total_import/export_Wh (NO Hz, NO heatsink_C)

    Args:
        sensor_key: Sensor type key
        der_types: List of DER types for the device

    Returns:
        True if sensor should be created

    """
    # === Battery sensors (only battery devices) ===
    # Battery has: W, V, A, SoC_nom_fract, heatsink_C, total_charge/discharge_Wh, limits
    if sensor_key in ("battery_soc", "battery_voltage", "battery_current",
                      "battery_charge_total", "battery_discharge_total",
                      "battery_upper_limit", "battery_lower_limit",
                      "battery_power", "battery_temperature"):
        return "battery" in der_types

    # === PV-only sensors ===
    # PV has: total_generation_Wh, heatsink_C
    if sensor_key == "energy_production":
        return "pv" in der_types

    if sensor_key == "temperature":
        return "pv" in der_types

    # === Standalone meter-only sensors ===
    # Grid frequency only available from standalone meter devices (not PV)
    if sensor_key == "grid_frequency":
        return "meter" in der_types and "pv" not in der_types

    # === Meter sensors (standalone meter only, NOT PV devices) ===
    # PV devices may have embedded meter but we only use PV data for those
    # Standalone meter (p1_uart) has: L1/2/3_V/A/W, total_import/export_Wh
    if sensor_key in ("energy_import", "energy_export"):
        return "meter" in der_types and "pv" not in der_types

    if sensor_key in ("l1_voltage", "l1_current", "l1_power",
                      "l2_voltage", "l2_current", "l2_power",
                      "l3_voltage", "l3_current", "l3_power"):
        return "meter" in der_types and "pv" not in der_types

    # === Universal sensors ===
    # Power is aggregated from all DER types
    if sensor_key == "power":
        return len(der_types) > 0

    # === Unsupported sensors ===
    # Signal strength not available in any data endpoint
    if sensor_key == "signal_strength":
        return False

    # Default: don't create
    return False


class ZapSensor(CoordinatorEntity[ZapDataUpdateCoordinator], SensorEntity):
    """Representation of a Zap Energy sensor."""

    entity_description: ZapSensorEntityDescription
    _attr_has_entity_name = True
    _gateway_serial: str
    _device_profile: str

    def __init__(
        self,
        coordinator: ZapDataUpdateCoordinator,
        description: ZapSensorEntityDescription,
        serial_number: str,
        device_profile: str = "",
        gateway_serial: str = "",
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator
            description: Sensor entity description
            serial_number: Device serial number
            device_profile: Device profile/model name
            gateway_serial: Gateway serial number

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._serial_number = serial_number
        self._gateway_serial = gateway_serial
        self._device_profile = device_profile

        # Set unique ID and suggested entity_id with format:
        # sourceful_zap_{gateway_serial}_{device_profile}_{device_serial}_{sensorname}
        if gateway_serial and device_profile:
            object_id = f"sourceful_zap_{gateway_serial}_{device_profile}_{serial_number}_{description.key}"
        elif device_profile:
            object_id = f"sourceful_zap_{device_profile}_{serial_number}_{description.key}"
        else:
            object_id = f"sourceful_zap_{serial_number}_{description.key}"

        self._attr_unique_id = object_id
        # Suggest the object_id for entity registry
        self.entity_id = f"sensor.{object_id}"

        _LOGGER.debug(
            "Created sensor entity_id: %s (gateway=%s, profile=%s, device=%s, sensor=%s)",
            self.entity_id,
            gateway_serial,
            device_profile,
            serial_number,
            description.key,
        )

        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial_number)},
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor.

        Returns:
            Sensor state value

        """
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available.

        Returns:
            True if sensor data is available

        """
        if not self.coordinator.last_update_success:
            return False

        if self.entity_description.available_fn:
            return self.entity_description.available_fn(self.coordinator.data)

        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary of extra attributes

        """
        attributes = {}

        data = self.coordinator.data

        if connection_status := data.get("connection_status"):
            attributes["connection_status"] = connection_status

        if last_harvest := data.get("last_harvest"):
            attributes["last_harvest"] = last_harvest

        if rated_power := data.get("rated_power"):
            attributes["rated_power"] = rated_power

        if capacity := data.get("capacity"):
            attributes["capacity"] = capacity

        return attributes
