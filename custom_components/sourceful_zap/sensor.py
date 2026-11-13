"""Sensor platform for Zap Energy integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
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
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfInformation,
    UnitOfPower,
    UnitOfReactivePower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DER_TYPE_BATTERY,
    DER_TYPE_INVERTER,
    DER_TYPE_METER,
    DER_TYPE_PV,
    DOMAIN,
    EV_DER_TYPES,
    GRID_POWER_COMPANION_DERS,
    PV_DER_TYPES,
)
from .coordinator import (
    ZapDataUpdateCoordinator,
    ZapDeviceData,
    ZapGatewayCoordinator,
    ZapGatewayData,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ZapSensorEntityDescription(SensorEntityDescription):
    """Describes Zap sensor entity."""

    value_fn: Callable[[ZapDeviceData], StateType] | None = None
    available_fn: Callable[[ZapDeviceData], bool] | None = None


@dataclass(frozen=True, kw_only=True)
class ZapGatewaySensorEntityDescription(SensorEntityDescription):
    """Describes Zap gateway sensor entity."""

    value_fn: Callable[[ZapGatewayData], StateType] | None = None
    available_fn: Callable[[ZapGatewayData], bool] | None = None


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
        key="grid_power",
        translation_key="grid_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("grid_power"),
        available_fn=lambda data: data.get("grid_power") is not None,
    ),
    ZapSensorEntityDescription(
        key="inverter_power",
        translation_key="inverter_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("inverter_power"),
        available_fn=lambda data: data.get("inverter_power") is not None,
    ),
    ZapSensorEntityDescription(
        key="ev_charger_power",
        translation_key="ev_charger_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("ev_charger_power"),
        available_fn=lambda data: data.get("ev_charger_power") is not None,
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
        key="battery_available_charge",
        translation_key="battery_available_charge",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("battery_available_charge"),
        available_fn=lambda data: data.get("battery_available_charge") is not None,
    ),
    ZapSensorEntityDescription(
        key="battery_available_discharge",
        translation_key="battery_available_discharge",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("battery_available_discharge"),
        available_fn=lambda data: data.get("battery_available_discharge") is not None,
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
    ZapSensorEntityDescription(
        key="grid_reactive_power",
        translation_key="grid_reactive_power",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("grid_reactive_power"),
        available_fn=lambda data: data.get("grid_reactive_power") is not None,
    ),
    # PV inputs
    ZapSensorEntityDescription(
        key="mppt1_voltage",
        translation_key="mppt1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("mppt1_voltage"),
        available_fn=lambda data: data.get("mppt1_voltage") is not None,
    ),
    ZapSensorEntityDescription(
        key="mppt1_current",
        translation_key="mppt1_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("mppt1_current"),
        available_fn=lambda data: data.get("mppt1_current") is not None,
    ),
    ZapSensorEntityDescription(
        key="mppt1_power",
        translation_key="mppt1_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("mppt1_power"),
        available_fn=lambda data: data.get("mppt1_power") is not None,
    ),
    ZapSensorEntityDescription(
        key="mppt2_voltage",
        translation_key="mppt2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("mppt2_voltage"),
        available_fn=lambda data: data.get("mppt2_voltage") is not None,
    ),
    ZapSensorEntityDescription(
        key="mppt2_current",
        translation_key="mppt2_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("mppt2_current"),
        available_fn=lambda data: data.get("mppt2_current") is not None,
    ),
    ZapSensorEntityDescription(
        key="mppt2_power",
        translation_key="mppt2_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("mppt2_power"),
        available_fn=lambda data: data.get("mppt2_power") is not None,
    ),
)

GATEWAY_SENSOR_TYPES: tuple[ZapGatewaySensorEntityDescription, ...] = (
    ZapGatewaySensorEntityDescription(
        key="gateway_uptime",
        translation_key="gateway_uptime",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("uptime_seconds"),
        available_fn=lambda data: data.get("uptime_seconds") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_temperature",
        translation_key="gateway_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("gateway_temperature"),
        available_fn=lambda data: data.get("gateway_temperature") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_memory_percent",
        translation_key="gateway_memory_percent",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("memory_percent"),
        available_fn=lambda data: data.get("memory_percent") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_memory_free",
        translation_key="gateway_memory_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("memory_free"),
        available_fn=lambda data: data.get("memory_free") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_firmware_version",
        translation_key="gateway_firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("firmware_version"),
        available_fn=lambda data: data.get("firmware_version") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_wifi_status",
        translation_key="gateway_wifi_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("wifi_status"),
        available_fn=lambda data: data.get("wifi_status") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_wifi_ssid",
        translation_key="gateway_wifi_ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("wifi_ssid"),
        available_fn=lambda data: data.get("wifi_ssid") is not None,
    ),
    ZapGatewaySensorEntityDescription(
        key="gateway_signal_strength",
        translation_key="gateway_signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("signal_strength"),
        available_fn=lambda data: data.get("signal_strength") is not None,
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

    # Get device list to check DERs
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    devices = await api.get_devices()

    # Create a map of serial number to DER types and device info
    device_info_map: dict[str, dict[str, Any]] = {}
    for device in devices:
        serial = device.get("serial_number")
        ders = device.get("ders", [])
        # `enabled` is the Zap's publish-to-backend flag, not whether the DER
        # is read, so a DER the Zap does not publish still gets its sensors.
        der_types = [der.get("type") for der in ders if der.get("type")]
        # Get device profile/model for entity naming
        profile = device.get("model", "").replace(" ", "_").lower()
        device_info_map[serial] = {
            "der_types": der_types,
            "profile": profile,
            "type": device.get("type"),
        }
        _LOGGER.debug("Device %s has DERs: %s, profile: %s", serial, der_types, profile)

    added: set[tuple[str, str]] = set()

    def new_device_sensors(
        serial_number: str, coordinator: ZapDataUpdateCoordinator
    ) -> list[SensorEntity]:
        """Return the device's sensors whose first value has just been reported.

        ``/ders`` lists what a device is configured with, and that can include
        a DER it never reads: an inverter with no grid meter still lists a
        meter. So a sensor is created at its first value, not from ``/ders``
        alone, and one that has had a value stays and shows unavailable.
        """
        device_info = device_info_map.get(serial_number, {})
        # /ders is authoritative (firmware 7 names solar/inverter there).
        # Fall back to the device list when that response had no DER array.
        der_types = coordinator.der_types or device_info.get("der_types", [])
        snapshot = coordinator.data or {}

        new_sensors: list[SensorEntity] = []
        for description in SENSOR_TYPES:
            sensor_id = (serial_number, description.key)
            if (
                sensor_id in added
                or snapshot.get(description.key) is None
                or not should_create_sensor(
                    description.key, der_types, device_info.get("type")
                )
            ):
                continue
            added.add(sensor_id)
            new_sensors.append(
                ZapSensor(
                    coordinator,
                    description,
                    serial_number,
                    device_info.get("profile", "device"),
                    gateway_serial,
                )
            )
        return new_sensors

    def add_new_device_sensors(
        serial_number: str, coordinator: ZapDataUpdateCoordinator
    ) -> None:
        """Add sensors whose values started to arrive after setup."""
        if new_sensors := new_device_sensors(serial_number, coordinator):
            async_add_entities(new_sensors)

    entities: list[SensorEntity] = []
    for serial_number, coordinator in coordinators.items():
        entities.extend(new_device_sensors(serial_number, coordinator))
        entry.async_on_unload(
            coordinator.async_add_listener(
                partial(add_new_device_sensors, serial_number, coordinator)
            )
        )

    # Create gateway sensor entities
    gateway_coordinator: ZapGatewayCoordinator = hass.data[DOMAIN][entry.entry_id][
        "gateway_coordinator"
    ]
    for gw_description in GATEWAY_SENSOR_TYPES:
        entities.append(
            ZapGatewaySensor(
                gateway_coordinator,
                gw_description,
                gateway_serial,
            )
        )

    async_add_entities(entities)


def should_create_sensor(
    sensor_key: str, der_types: list[str], device_type: str | None = None
) -> bool:
    """Determine if a sensor should be created based on device DERs.

    v1 DER type ``pv`` and v2 type ``solar`` both mean a PV array. A v1 ``pv``
    device may embed a meter object that is not the grid meter, so meter
    sensors stay suppressed when ``pv`` is present. v2 ``solar`` devices
    report a real grid meter alongside the array, so meter sensors are kept.

    p1_uart meters never report Hz. An inverter's L1-L3 values fill the phase
    sensors when the device has no grid meter.

    Args:
        sensor_key: Sensor type key
        der_types: List of DER types for the device

    Returns:
        True if sensor should be created

    """
    ders = set(der_types)
    has_pv_v1 = DER_TYPE_PV in ders
    has_meter = DER_TYPE_METER in ders and not has_pv_v1

    if sensor_key in (
        "battery_soc",
        "battery_voltage",
        "battery_current",
        "battery_charge_total",
        "battery_discharge_total",
        "battery_upper_limit",
        "battery_lower_limit",
        "battery_power",
        "battery_temperature",
        "battery_available_charge",
        "battery_available_discharge",
    ):
        return DER_TYPE_BATTERY in ders

    if sensor_key == "energy_production":
        return bool(ders & PV_DER_TYPES)

    # Inverter temperature covers v2 hybrids whose solar block has no temp.
    if sensor_key == "temperature":
        return bool(ders & PV_DER_TYPES) or DER_TYPE_INVERTER in ders

    if sensor_key == "grid_frequency":
        if device_type == "p1_uart":
            return False
        if DER_TYPE_INVERTER in ders:
            return True
        return has_meter

    if sensor_key in ("energy_import", "energy_export", "grid_reactive_power"):
        return has_meter

    if sensor_key in (
        "l1_voltage",
        "l1_current",
        "l1_power",
        "l2_voltage",
        "l2_current",
        "l2_power",
        "l3_voltage",
        "l3_current",
        "l3_power",
    ):
        return has_meter or DER_TYPE_INVERTER in ders

    if sensor_key in (
        "mppt1_voltage",
        "mppt1_current",
        "mppt1_power",
        "mppt2_voltage",
        "mppt2_current",
        "mppt2_power",
    ):
        return bool(ders & PV_DER_TYPES)

    if sensor_key == "grid_power":
        return has_meter and bool(ders & GRID_POWER_COMPANION_DERS)

    if sensor_key == "inverter_power":
        return DER_TYPE_INVERTER in ders

    if sensor_key == "ev_charger_power":
        return bool(ders & EV_DER_TYPES)

    if sensor_key == "power":
        return len(ders) > 0

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
            object_id = (
                f"sourceful_zap_{device_profile}_{serial_number}_{description.key}"
            )
        else:
            object_id = f"sourceful_zap_{serial_number}_{description.key}"

        self._attr_unique_id = object_id

        _LOGGER.debug(
            "Created sensor unique_id: %s (gateway=%s, profile=%s, device=%s, sensor=%s)",
            object_id,
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
        attributes: dict[str, Any] = {}

        data = self.coordinator.data

        if last_harvest := data.get("last_harvest"):
            attributes["last_harvest"] = last_harvest

        if rated_power := data.get("rated_power"):
            attributes["rated_power"] = rated_power

        if capacity := data.get("capacity"):
            attributes["capacity"] = capacity

        return attributes


class ZapGatewaySensor(CoordinatorEntity[ZapGatewayCoordinator], SensorEntity):
    """Representation of a Zap gateway sensor."""

    entity_description: ZapGatewaySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZapGatewayCoordinator,
        description: ZapGatewaySensorEntityDescription,
        gateway_serial: str,
    ) -> None:
        """Initialize the gateway sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"sourceful_zap_{gateway_serial}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, gateway_serial)},
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        if self.entity_description.available_fn:
            return self.entity_description.available_fn(self.coordinator.data)
        return True
