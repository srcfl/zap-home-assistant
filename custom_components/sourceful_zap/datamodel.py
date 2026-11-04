"""Map Zap local REST payloads onto integration sensor values.

Firmware 2.3.x emits Sourceful data model v1 (DER keys ``pv`` / ``battery`` /
``meter``, unsuffixed fields such as ``W`` and ``L1_W``). Firmware 7.x emits
data model v2 (``version`` ``v2``, DER keys ``solar`` / ``battery`` / ``meter``
/ ``inverter``, suffixed fields such as ``W_ac`` / ``W_dc``). Unused ac/dc
variants are JSON null and must not hide the populated side.

Sign convention is the Sourceful one on both generations, and the Home
Assistant values follow the v1 integration behaviour:

* solar/pv power is negative while generating; the power sensor stores the
  negated value so production reads positive
* battery power is positive while charging and negative while discharging;
  it is stored as reported and included in aggregate power
* meter power is positive for import and negative for export
* inverter AC power is negative while the inverter is supplying; ``inverter_power``
  is negated so output reads positive, and it is not added to aggregate power
  because solar and battery already account for that energy
* a PV input's current and power are negative while generating; the MPPT sensors
  negate them so production reads positive, like the power sensor
* an inverter's phase current and power are negated like ``inverter_power``. They
  fill the L1-L3 sensors only on a device with no grid meter
"""

from __future__ import annotations

import logging
import math
from typing import Any, TypedDict, cast

from homeassistant.util.dt import utc_from_timestamp

from .const import MODBUS_INVALID_VALUES, OVERFLOW_THRESHOLD

_LOGGER = logging.getLogger(__name__)

# v2 names a PV array "solar". v1 calls it "pv".
PV_BLOCK_KEYS: tuple[str, ...] = ("solar", "pv")
EV_BLOCK_KEYS: tuple[str, ...] = ("ev_charger_port", "ev_charger", "v2x_charger")

_W_DC_FIRST: tuple[str, ...] = ("W_dc", "W_ac", "W")
_W_AC_FIRST: tuple[str, ...] = ("W_ac", "W_dc", "W")
_V_DC_FIRST: tuple[str, ...] = ("V_dc", "V_ac", "V")
_A_DC_FIRST: tuple[str, ...] = ("A_dc", "A_ac", "A")
_TEMP_KEYS: tuple[str, ...] = ("temperature_C", "heatsink_C")
_SOC_KEYS: tuple[str, ...] = ("soc_nom_fract", "SoC_nom_fract")
_UPPER_DC_FIRST: tuple[str, ...] = (
    "upper_limit_W_dc",
    "upper_limit_W_ac",
    "upper_limit_W",
)
_LOWER_DC_FIRST: tuple[str, ...] = (
    "lower_limit_W_dc",
    "lower_limit_W_ac",
    "lower_limit_W",
)
_RATED_DC_FIRST: tuple[str, ...] = (
    "rated_power_W_dc",
    "rated_power_W_ac",
    "rated_power_W",
    "rated_power",
)
_RATED_AC_FIRST: tuple[str, ...] = (
    "rated_power_W_ac",
    "rated_power_W_dc",
    "rated_power_W",
    "rated_power",
)
# The Zap reads at most two PV inputs.
_MPPT_INPUTS = 2
_DER_RATED_KEYS: tuple[str, ...] = (
    "rated_power",
    "rated_power_W",
    "rated_power_W_ac",
    "rated_power_W_dc",
)
_DER_CAPACITY_KEYS: tuple[str, ...] = (
    "capacity",
    "capacity_Wh",
    "capacity_Wh_dc",
    "capacity_Wh_ac",
)


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
    rated_power: float | None
    capacity: float | None
    firmware_version: str | None
    last_harvest: str | None
    # Per-phase meter measurements (grid when a meter block is present)
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
    # Meter total, when it is not already the aggregate power sensor
    grid_power: float | None
    grid_reactive_power: float | None
    # Device makes/manufacturers
    meter_make: str | None
    pv_make: str | None
    battery_make: str | None
    # Battery limits and remaining energy
    battery_upper_limit: float | None
    battery_lower_limit: float | None
    battery_temperature: float | None
    battery_available_charge: float | None
    battery_available_discharge: float | None
    # PV power limits
    pv_upper_limit: float | None
    pv_lower_limit: float | None
    # PV inputs, v2 only. Current and power are positive while generating.
    mppt1_voltage: float | None
    mppt1_current: float | None
    mppt1_power: float | None
    mppt2_voltage: float | None
    mppt2_current: float | None
    mppt2_power: float | None
    # v2-only measurements
    inverter_power: float | None
    ev_charger_power: float | None


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
        "total_generation_Wh",
        "total_import_Wh",
        "total_export_Wh",
        "total_charge_Wh",
        "total_discharge_Wh",
        "available_charge_Wh",
        "available_discharge_Wh",
    )
    if abs(num) > 1e6 and field_name not in energy_fields:
        if "Wh" not in field_name:
            _LOGGER.debug(
                "Suspicious %s value: %s (unexpectedly large)", field_name, num
            )
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


def is_data_model_v2(payload: dict[str, Any]) -> bool:
    """Return True when a local REST body is Sourceful data model v2.

    Detection is per response: an explicit ``version`` of ``v2``, or v2-only
    DER keys / suffixed measurement keys when the version field is absent.
    """
    version = payload.get("version")
    if isinstance(version, str) and version.lower() == "v2":
        return True
    if any(key in payload for key in ("solar", "inverter", "ev_charger_port")):
        return True
    for block in payload.values():
        if not isinstance(block, dict):
            continue
        for key in block:
            if not isinstance(key, str):
                continue
            if key == "soc_nom_fract" or key.endswith(("_ac", "_dc")):
                return True
    return False


def enabled_der_types(device_ders_response: dict[str, Any] | None) -> list[str]:
    """Return enabled DER type names from a ``/ders`` response."""
    if not device_ders_response:
        return []
    ders = device_ders_response.get("ders")
    if not isinstance(ders, list):
        return []
    types: list[str] = []
    for der in ders:
        if not isinstance(der, dict):
            continue
        der_type = der.get("type")
        if not der_type or der.get("enabled", True) is False:
            continue
        types.append(str(der_type))
    return types


def parse_device_data(
    device_data: dict[str, Any],
    device_ders_response: dict[str, Any] | None,
    serial_number: str,
) -> tuple[ZapDeviceData, list[str]]:
    """Parse one ``/data/json`` body plus its ``/ders`` metadata.

    Returns the sensor snapshot and the enabled DER types from ``/ders``.
    """
    data: ZapDeviceData = {"serial_number": serial_number}
    if not isinstance(device_data, dict):
        device_data = {}

    v2 = is_data_model_v2(device_data)
    _LOGGER.debug("Parsing %s as data model %s", serial_number, "v2" if v2 else "v1")

    meter_block = _block(device_data, "meter")
    _apply_solar(data, _block(device_data, *PV_BLOCK_KEYS))
    _apply_inverter(
        data, _block(device_data, "inverter"), include_phases=meter_block is None
    )
    _apply_battery(data, _block(device_data, "battery"))
    # v1 PV payloads ship an embedded meter that is not the grid meter.
    # Ignore that object entirely. v2 meters next to solar are the grid meter.
    if meter_block is not None and (v2 or "pv" not in device_data):
        _apply_meter(
            data,
            meter_block,
            include_in_aggregate=_include_meter_in_aggregate(device_data, v2),
        )
    _apply_ev(data, _block(device_data, *EV_BLOCK_KEYS))
    _apply_der_metadata(data, device_ders_response)
    _apply_last_harvest(data, device_data)

    return data, enabled_der_types(device_ders_response)


def _block(payload: dict[str, Any], *keys: str) -> dict[str, Any] | None:
    """Return the first dict block stored under one of ``keys``."""
    for key in keys:
        block = payload.get(key)
        if isinstance(block, dict):
            return block
    return None


def _first_present(block: dict[str, Any], *keys: str) -> Any:
    """Return the first value that is present and not JSON null.

    Zero is a real measurement. Null means that ac/dc variant is unused.
    """
    for key in keys:
        if key in block and block[key] is not None:
            return block[key]
    return None


def _read_metric(
    block: dict[str, Any],
    keys: tuple[str, ...],
    field_name: str,
    **kwargs: Any,
) -> float | None:
    return validate_numeric(_first_present(block, *keys), field_name, **kwargs)


def _energy_keys(base: str, *, prefer_dc: bool) -> tuple[str, ...]:
    dc_key = f"{base}_dc"
    ac_key = f"{base}_ac"
    if prefer_dc:
        return (dc_key, ac_key, base)
    return (ac_key, dc_key, base)


def _phase_keys(phase: str, quantity: str) -> tuple[str, ...]:
    """AC-first v2 key, then DC, then the v1 ``L1_V`` spelling."""
    legacy = f"{phase.upper()}_{quantity}"
    return (
        f"{phase}_{quantity}_ac",
        f"{phase}_{quantity}_dc",
        legacy,
        f"{phase}_{quantity}",
    )


def _add_power(data: ZapDeviceData, watts: float | None) -> None:
    if watts is None:
        return
    current = data.get("power")
    data["power"] = watts if current is None else current + watts


def _set_make(data: ZapDeviceData, block: dict[str, Any], field: str) -> None:
    make = block.get("make")
    if isinstance(make, str):
        cast(dict[str, Any], data)[field] = make


def _include_meter_in_aggregate(device_data: dict[str, Any], is_v2: bool) -> bool:
    """Whether meter watts belong in the aggregate power sensor.

    v1 folds the meter in unless the payload also has a ``pv`` block. Those
    PV payloads carry an embedded meter that is not the grid meter, and the
    meter object is ignored entirely.

    v2 hybrid inverters report a real grid meter next to solar, battery, and
    inverter. That meter stays out of the aggregate (solar + battery) and is
    exposed as grid power instead. A v2 meter-only device, such as a P1
    port, still uses meter watts as aggregate power.
    """
    if not is_v2:
        return "pv" not in device_data
    return not any(
        isinstance(device_data.get(key), dict)
        for key in ("solar", "pv", "battery", "inverter")
    )


def _apply_solar(data: ZapDeviceData, block: dict[str, Any] | None) -> None:
    if block is None:
        return

    # Negative API watts = generating. Flip so the power sensor is positive
    # while the array is producing (same as v1 ``pv.W``).
    pv_power = _read_metric(block, _W_DC_FIRST, "pv.W")
    if pv_power is not None:
        _add_power(data, -pv_power)

    generation = _read_metric(
        block,
        _energy_keys("total_generation_Wh", prefer_dc=True),
        "total_generation_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if generation is not None:
        data["energy_production"] = generation

    pv_temp = _read_metric(
        block, _TEMP_KEYS, "pv.temperature_C", min_value=-40, max_value=150
    )
    if pv_temp is not None:
        data["temperature"] = pv_temp

    pv_rated = _read_metric(block, _RATED_DC_FIRST, "pv.rated_power_W", min_value=0)
    if pv_rated is not None:
        data["rated_power"] = pv_rated

    _set_make(data, block, "pv_make")

    pv_upper = _read_metric(block, _UPPER_DC_FIRST, "pv.upper_limit_W")
    if pv_upper is not None:
        data["pv_upper_limit"] = pv_upper
    pv_lower = _read_metric(block, _LOWER_DC_FIRST, "pv.lower_limit_W")
    if pv_lower is not None:
        data["pv_lower_limit"] = pv_lower

    _apply_mppt(data, block.get("mppt"))


def _apply_mppt(data: ZapDeviceData, inputs: Any) -> None:
    """Copy each PV input's DC values, with generation positive."""
    if not isinstance(inputs, list):
        return

    values = cast(dict[str, Any], data)
    for number, pv_input in enumerate(inputs[:_MPPT_INPUTS], start=1):
        if not isinstance(pv_input, dict):
            continue

        voltage = _read_metric(pv_input, ("V_dc",), f"mppt{number}.V_dc", min_value=0)
        if voltage is not None:
            values[f"mppt{number}_voltage"] = voltage

        for quantity, key in (("current", "A_dc"), ("power", "W_dc")):
            reading = _read_metric(pv_input, (key,), f"mppt{number}.{key}")
            if reading is not None:
                # 0 - x keeps a 0 reading +0.
                values[f"mppt{number}_{quantity}"] = 0.0 - reading


def _apply_battery(data: ZapDeviceData, block: dict[str, Any] | None) -> None:
    if block is None:
        return

    # Stored as reported: positive = charging, negative = discharging.
    batt_power = _read_metric(block, _W_DC_FIRST, "battery.W")
    if batt_power is not None:
        data["battery_power"] = batt_power
        _add_power(data, batt_power)

    batt_soc = _read_metric(
        block, _SOC_KEYS, "battery.soc_nom_fract", min_value=0, max_value=1
    )
    if batt_soc is not None:
        data["battery_soc"] = batt_soc * 100

    batt_voltage = _read_metric(
        block, _V_DC_FIRST, "battery.V", min_value=0, max_value=1000
    )
    if batt_voltage is not None:
        data["battery_voltage"] = batt_voltage

    batt_current = _read_metric(
        block, _A_DC_FIRST, "battery.A", min_value=-500, max_value=500
    )
    if batt_current is not None:
        data["battery_current"] = batt_current

    batt_charge = _read_metric(
        block,
        _energy_keys("total_charge_Wh", prefer_dc=True),
        "total_charge_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if batt_charge is not None:
        data["battery_charge_total"] = batt_charge

    batt_discharge = _read_metric(
        block,
        _energy_keys("total_discharge_Wh", prefer_dc=True),
        "total_discharge_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if batt_discharge is not None:
        data["battery_discharge_total"] = batt_discharge

    available_charge = _read_metric(
        block,
        _energy_keys("available_charge_Wh", prefer_dc=True),
        "available_charge_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if available_charge is not None:
        data["battery_available_charge"] = available_charge

    available_discharge = _read_metric(
        block,
        _energy_keys("available_discharge_Wh", prefer_dc=True),
        "available_discharge_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if available_discharge is not None:
        data["battery_available_discharge"] = available_discharge

    batt_temp = _read_metric(
        block, _TEMP_KEYS, "battery.temperature_C", min_value=-40, max_value=150
    )
    if batt_temp is not None:
        data["battery_temperature"] = batt_temp
        # v1 PV-less devices used the battery heatsink as the temperature
        # sensor. Do not override a solar or inverter temperature.
        if data.get("temperature") is None:
            data["temperature"] = batt_temp

    _set_make(data, block, "battery_make")

    batt_upper = _read_metric(block, _UPPER_DC_FIRST, "battery.upper_limit_W")
    if batt_upper is not None:
        data["battery_upper_limit"] = batt_upper
    batt_lower = _read_metric(block, _LOWER_DC_FIRST, "battery.lower_limit_W")
    if batt_lower is not None:
        data["battery_lower_limit"] = batt_lower


def _apply_inverter(
    data: ZapDeviceData,
    block: dict[str, Any] | None,
    *,
    include_phases: bool,
) -> None:
    if block is None:
        return

    # Negative API watts = inverter supplying AC. Flip so the sensor is
    # positive while the inverter is delivering power. Not added to aggregate
    # power; solar and battery already cover that energy.
    inverter_power = _read_metric(block, _W_AC_FIRST, "inverter.W")
    if inverter_power is not None:
        data["inverter_power"] = -inverter_power

    inv_temp = _read_metric(
        block, _TEMP_KEYS, "inverter.temperature_C", min_value=-40, max_value=150
    )
    if inv_temp is not None and data.get("temperature") is None:
        data["temperature"] = inv_temp

    if data.get("rated_power") is None:
        rated = _read_metric(
            block, _RATED_AC_FIRST, "inverter.rated_power_W", min_value=0
        )
        if rated is not None:
            data["rated_power"] = rated

    if data.get("grid_frequency") is None:
        freq = _read_metric(block, ("Hz",), "inverter.Hz", min_value=45, max_value=65)
        if freq is not None:
            data["grid_frequency"] = freq

    if include_phases:
        _apply_phases(data, block, "inverter", output_positive=True)


def _apply_meter(
    data: ZapDeviceData,
    block: dict[str, Any] | None,
    *,
    include_in_aggregate: bool,
) -> None:
    if block is None:
        return

    meter_power = _read_metric(block, _W_AC_FIRST, "meter.W")
    if meter_power is not None:
        if include_in_aggregate:
            _add_power(data, meter_power)
        else:
            data["grid_power"] = meter_power

    meter_import = _read_metric(
        block,
        _energy_keys("total_import_Wh", prefer_dc=False),
        "total_import_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if meter_import is not None:
        data["energy_import"] = meter_import

    meter_export = _read_metric(
        block,
        _energy_keys("total_export_Wh", prefer_dc=False),
        "total_export_Wh",
        min_value=0,
        reject_overflow=True,
    )
    if meter_export is not None:
        data["energy_export"] = meter_export

    # Meter frequency wins over the inverter value applied earlier.
    grid_freq = _read_metric(block, ("Hz",), "meter.Hz", min_value=45, max_value=65)
    if grid_freq is not None:
        data["grid_frequency"] = grid_freq

    _apply_phases(data, block, "meter")

    reactive = _read_metric(
        block,
        ("reactive_var_ac", "reactive_var_dc", "reactive_var"),
        "meter.reactive_var",
    )
    if reactive is not None:
        data["grid_reactive_power"] = reactive

    _set_make(data, block, "meter_make")


def _apply_phases(
    data: ZapDeviceData,
    block: dict[str, Any],
    source: str,
    *,
    output_positive: bool = False,
) -> None:
    """Copy L1/L2/L3 voltage, current, and power.

    ``output_positive`` negates current and power, for a block whose negative
    values mean supplying.
    """
    values = cast(dict[str, Any], data)
    for phase, voltage_field, current_field, power_field in (
        ("l1", "l1_voltage", "l1_current", "l1_power"),
        ("l2", "l2_voltage", "l2_current", "l2_power"),
        ("l3", "l3_voltage", "l3_current", "l3_power"),
    ):
        voltage = _read_metric(
            block,
            _phase_keys(phase, "V"),
            f"{source}.{phase.upper()}_V",
            min_value=0,
            max_value=500,
        )
        if voltage is not None:
            values[voltage_field] = voltage

        current = _read_metric(
            block,
            _phase_keys(phase, "A"),
            f"{source}.{phase.upper()}_A",
            min_value=-200,
            max_value=200,
        )
        if current is not None:
            # 0 - x keeps a 0 reading +0.
            values[current_field] = 0.0 - current if output_positive else current

        power = _read_metric(
            block, _phase_keys(phase, "W"), f"{source}.{phase.upper()}_W"
        )
        if power is not None:
            values[power_field] = 0.0 - power if output_positive else power


def _apply_ev(data: ZapDeviceData, block: dict[str, Any] | None) -> None:
    if block is None:
        return
    # Positive = charging the vehicle. Stored as reported, like battery power.
    ev_power = _read_metric(block, _W_AC_FIRST, "ev.W")
    if ev_power is not None:
        data["ev_charger_power"] = ev_power
        _add_power(data, ev_power)


def _apply_der_metadata(
    data: ZapDeviceData, device_ders_response: dict[str, Any] | None
) -> None:
    if not device_ders_response:
        return
    ders = device_ders_response.get("ders")
    if not isinstance(ders, list):
        return

    for der in ders:
        if not isinstance(der, dict):
            continue
        der_type = der.get("type")

        if der.get("enabled") and data.get("rated_power") is None:
            rated = _read_metric(der, _DER_RATED_KEYS, "der.rated_power", min_value=0)
            if rated is not None:
                data["rated_power"] = rated

        if der_type == "battery":
            capacity = _read_metric(
                der, _DER_CAPACITY_KEYS, "der.capacity", min_value=0
            )
            if capacity is not None:
                data["capacity"] = capacity


def _apply_last_harvest(data: ZapDeviceData, device_data: dict[str, Any]) -> None:
    timestamps = [
        block["timestamp"]
        for block in device_data.values()
        if isinstance(block, dict) and block.get("timestamp")
    ]
    if timestamps:
        data["last_harvest"] = utc_from_timestamp(max(timestamps) / 1000).isoformat()
