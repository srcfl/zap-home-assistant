"""Data update coordinator for Zap Energy integration."""

from __future__ import annotations

from datetime import timedelta
import logging
import math
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZapApiClient, ZapApiError
from .const import DOMAIN, MODBUS_INVALID_VALUES, OVERFLOW_THRESHOLD

_LOGGER = logging.getLogger(__name__)


def validate_numeric(
    value: Any,
    field_name: str = "",
    min_value: float | None = None,
    max_value: float | None = None,
    reject_overflow: bool = False,
) -> float | None:
    """Validate and convert a numeric value from the API.

    Filters out invalid Modbus sentinel values, NaN, Inf, and overflow values.

    Args:
        value: Raw value from API
        field_name: Field name for debug logging
        min_value: Minimum valid value (optional)
        max_value: Maximum valid value (optional)
        reject_overflow: If True, reject values near uint32 max

    Returns:
        Valid float value or None if invalid

    """
    if value is None:
        return None

    try:
        num = float(value)
    except (ValueError, TypeError):
        _LOGGER.debug("Cannot convert %s value %r to float", field_name, value)
        return None

    # Check for NaN or Infinity
    if math.isnan(num) or math.isinf(num):
        _LOGGER.debug("Invalid %s value: %s (NaN or Inf)", field_name, num)
        return None

    # Check for Modbus sentinel values
    if num in MODBUS_INVALID_VALUES:
        _LOGGER.debug("Invalid %s value: %s (Modbus sentinel)", field_name, num)
        return None

    # Check for values with very large exponents (like 6.5535e+06)
    # Energy totals can legitimately be in millions of Wh, but current/voltage shouldn't be
    energy_fields = (
        "total_generation_Wh", "total_import_Wh", "total_export_Wh",
        "total_charge_Wh", "total_discharge_Wh"
    )
    if abs(num) > 1e6 and field_name not in energy_fields:
        if "Wh" not in field_name:
            _LOGGER.debug("Suspicious %s value: %s (unexpectedly large)", field_name, num)
            return None

    # Check for overflow values (near uint32 max)
    if reject_overflow and abs(num) > OVERFLOW_THRESHOLD:
        _LOGGER.debug("Invalid %s value: %s (overflow)", field_name, num)
        return None

    # Check min/max bounds
    if min_value is not None and num < min_value:
        _LOGGER.debug("Invalid %s value: %s (below min %s)", field_name, num, min_value)
        return None
    if max_value is not None and num > max_value:
        _LOGGER.debug("Invalid %s value: %s (above max %s)", field_name, num, max_value)
        return None

    return num


class ZapDeviceData(TypedDict, total=False):
    """Type definition for Zap device data."""

    serial_number: str
    power: float | None
    energy_import: float | None
    energy_production: float | None
    energy_export: float | None
    battery_soc: float | None
    battery_power: float | None
    battery_voltage: float | None
    battery_current: float | None
    battery_charge_total: float | None
    battery_discharge_total: float | None
    temperature: float | None
    signal_strength: float | None
    rated_power: float | None
    capacity: float | None
    firmware_version: str | None
    connection_status: str | None
    last_harvest: str | None
    # Per-phase meter measurements
    l1_voltage: float | None
    l1_current: float | None
    l1_power: float | None
    l2_voltage: float | None
    l2_current: float | None
    l2_power: float | None
    l3_voltage: float | None
    l3_current: float | None
    l3_power: float | None
    # Grid frequency
    grid_frequency: float | None
    # Device makes/manufacturers
    meter_make: str | None
    pv_make: str | None
    battery_make: str | None
    # Battery limits
    battery_upper_limit: float | None
    battery_lower_limit: float | None
    # Battery temperature (separate from PV temperature)
    battery_temperature: float | None
    # PV power limits
    pv_upper_limit: float | None
    pv_lower_limit: float | None


class ZapDataUpdateCoordinator(DataUpdateCoordinator[ZapDeviceData]):
    """Class to manage fetching Zap device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ZapApiClient,
        serial_number: str,
        polling_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: Zap API client
            serial_number: Device serial number
            polling_interval: Update interval in seconds

        """
        self.api = api
        self.serial_number = serial_number

        super().__init__(
            hass,
            _LOGGER,
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
            # Fetch device data and DER metadata
            device_data = await self.api.get_device_data(self.serial_number)
            device_ders_response = await self.api.get_device_ders(self.serial_number)

            _LOGGER.debug(
                "Raw device data for %s: %s",
                self.serial_number,
                device_data
            )

            # Parse and structure data
            data: ZapDeviceData = {
                "serial_number": self.serial_number,
            }

            # Data is nested by DER type: {"pv": {...}, "battery": {...}, "meter": {...}}

            # Extract PV metrics
            if "pv" in device_data:
                pv_data = device_data["pv"]

                # PV power: Sourceful API uses negative for production, flip sign
                pv_power = validate_numeric(pv_data.get("W"), "pv.W")
                if pv_power is not None:
                    pv_power = -pv_power  # Flip sign: negative API value = positive production
                    if data.get("power") is None:
                        data["power"] = pv_power
                    else:
                        data["power"] += pv_power

                # PV total generation = production (not export!)
                # Use reject_overflow to filter out uint32 overflow values
                pv_generation = validate_numeric(
                    pv_data.get("total_generation_Wh"),
                    "total_generation_Wh",
                    min_value=0,
                    reject_overflow=True,
                )
                if pv_generation is not None:
                    data["energy_production"] = pv_generation

                # PV temperature from heatsink (valid range: -40 to 150°C)
                pv_temp = validate_numeric(
                    pv_data.get("heatsink_C"),
                    "pv.heatsink_C",
                    min_value=-40,
                    max_value=150,
                )
                if pv_temp is not None:
                    data["temperature"] = pv_temp

                # PV rated power
                pv_rated = validate_numeric(pv_data.get("rated_power_W"), "pv.rated_power_W", min_value=0)
                if pv_rated is not None:
                    data["rated_power"] = pv_rated

                # PV make/manufacturer
                if "make" in pv_data:
                    data["pv_make"] = pv_data["make"]

                # PV power limits
                pv_upper = validate_numeric(pv_data.get("upper_limit_W"), "pv.upper_limit_W")
                if pv_upper is not None:
                    data["pv_upper_limit"] = pv_upper

                pv_lower = validate_numeric(pv_data.get("lower_limit_W"), "pv.lower_limit_W")
                if pv_lower is not None:
                    data["pv_lower_limit"] = pv_lower

            # Extract Battery metrics
            if "battery" in device_data:
                battery_data = device_data["battery"]

                # Battery power (positive = discharging, negative = charging)
                batt_power = validate_numeric(battery_data.get("W"), "battery.W")
                if batt_power is not None:
                    data["battery_power"] = batt_power
                    # Add battery power to total power
                    if data.get("power") is None:
                        data["power"] = batt_power
                    else:
                        data["power"] += batt_power

                # Battery SOC is a fraction (0-1), convert to percentage
                batt_soc_fract = validate_numeric(
                    battery_data.get("SoC_nom_fract"),
                    "battery.SoC_nom_fract",
                    min_value=0,
                    max_value=1,
                )
                if batt_soc_fract is not None:
                    data["battery_soc"] = batt_soc_fract * 100

                # Battery voltage (valid range: 0-1000V for most systems)
                batt_voltage = validate_numeric(
                    battery_data.get("V"),
                    "battery.V",
                    min_value=0,
                    max_value=1000,
                )
                if batt_voltage is not None:
                    data["battery_voltage"] = batt_voltage

                # Battery current (reasonable range: -500 to 500A)
                batt_current = validate_numeric(
                    battery_data.get("A"),
                    "battery.A",
                    min_value=-500,
                    max_value=500,
                )
                if batt_current is not None:
                    data["battery_current"] = batt_current

                # Battery energy counters
                batt_charge = validate_numeric(
                    battery_data.get("total_charge_Wh"),
                    "total_charge_Wh",
                    min_value=0,
                    reject_overflow=True,
                )
                if batt_charge is not None:
                    data["battery_charge_total"] = batt_charge

                batt_discharge = validate_numeric(
                    battery_data.get("total_discharge_Wh"),
                    "total_discharge_Wh",
                    min_value=0,
                    reject_overflow=True,
                )
                if batt_discharge is not None:
                    data["battery_discharge_total"] = batt_discharge

                # Battery temperature from heatsink (valid range: -40 to 150°C)
                batt_temp = validate_numeric(
                    battery_data.get("heatsink_C"),
                    "battery.heatsink_C",
                    min_value=-40,
                    max_value=150,
                )
                if batt_temp is not None:
                    # Store battery-specific temperature
                    data["battery_temperature"] = batt_temp
                    # Also use as fallback for general temperature if PV not present
                    if data.get("temperature") is None:
                        data["temperature"] = batt_temp

                # Battery make/manufacturer
                if "make" in battery_data:
                    data["battery_make"] = battery_data["make"]

                # Battery power limits
                batt_upper = validate_numeric(battery_data.get("upper_limit_W"), "battery.upper_limit_W")
                if batt_upper is not None:
                    data["battery_upper_limit"] = batt_upper

                batt_lower = validate_numeric(battery_data.get("lower_limit_W"), "battery.lower_limit_W")
                if batt_lower is not None:
                    data["battery_lower_limit"] = batt_lower

            # Extract Meter metrics (only for standalone meter devices, not PV with embedded meter)
            # PV devices may have an embedded meter object, but we only use PV data for those
            if "meter" in device_data and "pv" not in device_data:
                meter_data = device_data["meter"]

                # Meter shows grid import (positive) or export (negative)
                meter_power = validate_numeric(meter_data.get("W"), "meter.W")
                if meter_power is not None:
                    if data.get("power") is None:
                        data["power"] = meter_power
                    else:
                        data["power"] += meter_power

                # Meter import/export counters (reject overflow values)
                meter_import = validate_numeric(
                    meter_data.get("total_import_Wh"),
                    "total_import_Wh",
                    min_value=0,
                    reject_overflow=True,
                )
                if meter_import is not None:
                    data["energy_import"] = meter_import

                meter_export = validate_numeric(
                    meter_data.get("total_export_Wh"),
                    "total_export_Wh",
                    min_value=0,
                    reject_overflow=True,
                )
                if meter_export is not None:
                    data["energy_export"] = meter_export

                # Grid frequency (valid range: 45-65 Hz covers most grids)
                grid_freq = validate_numeric(
                    meter_data.get("Hz"),
                    "meter.Hz",
                    min_value=45,
                    max_value=65,
                )
                if grid_freq is not None:
                    data["grid_frequency"] = grid_freq

                # Per-phase measurements (L1, L2, L3)
                # Voltage: valid range 0-500V for residential/commercial
                l1_v = validate_numeric(meter_data.get("L1_V"), "meter.L1_V", min_value=0, max_value=500)
                if l1_v is not None:
                    data["l1_voltage"] = l1_v

                # Current: reasonable range -200 to 200A
                l1_a = validate_numeric(meter_data.get("L1_A"), "meter.L1_A", min_value=-200, max_value=200)
                if l1_a is not None:
                    data["l1_current"] = l1_a

                # Power per phase
                l1_w = validate_numeric(meter_data.get("L1_W"), "meter.L1_W")
                if l1_w is not None:
                    data["l1_power"] = l1_w

                l2_v = validate_numeric(meter_data.get("L2_V"), "meter.L2_V", min_value=0, max_value=500)
                if l2_v is not None:
                    data["l2_voltage"] = l2_v

                l2_a = validate_numeric(meter_data.get("L2_A"), "meter.L2_A", min_value=-200, max_value=200)
                if l2_a is not None:
                    data["l2_current"] = l2_a

                l2_w = validate_numeric(meter_data.get("L2_W"), "meter.L2_W")
                if l2_w is not None:
                    data["l2_power"] = l2_w

                l3_v = validate_numeric(meter_data.get("L3_V"), "meter.L3_V", min_value=0, max_value=500)
                if l3_v is not None:
                    data["l3_voltage"] = l3_v

                l3_a = validate_numeric(meter_data.get("L3_A"), "meter.L3_A", min_value=-200, max_value=200)
                if l3_a is not None:
                    data["l3_current"] = l3_a

                l3_w = validate_numeric(meter_data.get("L3_W"), "meter.L3_W")
                if l3_w is not None:
                    data["l3_power"] = l3_w

                # Meter make
                if "make" in meter_data:
                    data["meter_make"] = meter_data["make"]

            # Extract DER metadata from device_ders
            if device_ders_response and "ders" in device_ders_response:
                for der in device_ders_response["ders"]:
                    der_type = der.get("type")

                    # Get rated power from first enabled DER
                    if der.get("enabled") and "rated_power" in der:
                        if data.get("rated_power") is None:
                            rated = validate_numeric(der["rated_power"], "der.rated_power", min_value=0)
                            if rated is not None:
                                data["rated_power"] = rated

                    # Get capacity from battery DER
                    if der_type == "battery" and "capacity" in der:
                        capacity = validate_numeric(der["capacity"], "der.capacity", min_value=0)
                        if capacity is not None:
                            data["capacity"] = capacity

            _LOGGER.debug(
                "Parsed data for Zap device %s: %s", self.serial_number, data
            )

            return data

        except ZapApiError as err:
            raise UpdateFailed(f"Error fetching data for {self.serial_number}") from err
