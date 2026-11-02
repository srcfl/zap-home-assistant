"""Constants for the Zap Energy integration."""

from typing import Final

# Integration domain
DOMAIN: Final = "sourceful_zap"

# Configuration keys
CONF_HOST: Final = "host"
CONF_POLLING_INTERVAL: Final = "polling_interval"

# Default values
DEFAULT_API_PATH: Final = "/api"
DEFAULT_POLLING_INTERVAL: Final = 10  # seconds
MIN_POLLING_INTERVAL: Final = 1  # seconds
GATEWAY_POLL_INTERVAL: Final = 30  # seconds, gateway system info polling


# Device information
MANUFACTURER: Final = "Sourceful Energy"
MODEL: Final = "Zap Smart Meter"

# Sensor types
SENSOR_TYPE_POWER: Final = "power"
SENSOR_TYPE_ENERGY_IMPORT: Final = "energy_import"
SENSOR_TYPE_ENERGY_EXPORT: Final = "energy_export"
SENSOR_TYPE_ENERGY_PRODUCTION: Final = "energy_production"
SENSOR_TYPE_BATTERY_SOC: Final = "battery_soc"
SENSOR_TYPE_BATTERY_POWER: Final = "battery_power"
SENSOR_TYPE_BATTERY_VOLTAGE: Final = "battery_voltage"
SENSOR_TYPE_BATTERY_CURRENT: Final = "battery_current"
SENSOR_TYPE_BATTERY_CHARGE_TOTAL: Final = "battery_charge_total"
SENSOR_TYPE_BATTERY_DISCHARGE_TOTAL: Final = "battery_discharge_total"
SENSOR_TYPE_BATTERY_TEMPERATURE: Final = "battery_temperature"
SENSOR_TYPE_TEMPERATURE: Final = "temperature"
SENSOR_TYPE_SIGNAL_STRENGTH: Final = "signal_strength"
SENSOR_TYPE_GRID_FREQUENCY: Final = "grid_frequency"
SENSOR_TYPE_MPPT1_VOLTAGE: Final = "mppt1_voltage"
SENSOR_TYPE_MPPT1_CURRENT: Final = "mppt1_current"
SENSOR_TYPE_MPPT2_VOLTAGE: Final = "mppt2_voltage"
SENSOR_TYPE_MPPT2_CURRENT: Final = "mppt2_current"

# DER (Distributed Energy Resource) types.
# Firmware 2.3.x uses pv; firmware 7.x (data model v2) uses solar and adds
# inverter. ev_charger_port is the v2 name for an EV port.
DER_TYPE_PV: Final = "pv"
DER_TYPE_SOLAR: Final = "solar"
DER_TYPE_BATTERY: Final = "battery"
DER_TYPE_METER: Final = "meter"
DER_TYPE_INVERTER: Final = "inverter"
DER_TYPE_EV_CHARGER: Final = "ev_charger"
DER_TYPE_EV_CHARGER_PORT: Final = "ev_charger_port"
DER_TYPE_V2X_CHARGER: Final = "v2x_charger"

PV_DER_TYPES: Final = frozenset({DER_TYPE_PV, DER_TYPE_SOLAR})
EV_DER_TYPES: Final = frozenset(
    {DER_TYPE_EV_CHARGER, DER_TYPE_EV_CHARGER_PORT, DER_TYPE_V2X_CHARGER}
)
# v2 DER types that sit beside a real grid meter. Aggregate power is then
# solar/battery, and grid power gets its own sensor. v1 "pv" is intentionally
# absent: those devices embed a meter that is not the grid meter.
GRID_POWER_COMPANION_DERS: Final = frozenset({DER_TYPE_SOLAR, DER_TYPE_INVERTER})

# Attributes
ATTR_SERIAL_NUMBER: Final = "serial_number"
ATTR_LAST_HARVEST: Final = "last_harvest"
ATTR_CONNECTION_STATUS: Final = "connection_status"
ATTR_RATED_POWER: Final = "rated_power"
ATTR_CAPACITY: Final = "capacity"
ATTR_FIRMWARE_VERSION: Final = "firmware_version"
ATTR_SESSION_STATE: Final = "session_state"

# Modbus sentinel values that indicate invalid/missing data
# These are common error codes from Modbus devices
MODBUS_INVALID_VALUES: Final = frozenset(
    {
        65535,  # 0xFFFF - unsigned 16-bit "no data"
        -32768,  # 0x8000 signed - invalid/error
        32768,  # 0x8000 unsigned
        32767,  # 0x7FFF - max signed 16-bit
        -32767,  # Min signed 16-bit + 1
    }
)

# Threshold for detecting overflow values (values near 2^32 are likely invalid)
OVERFLOW_THRESHOLD: Final = 4_000_000_000  # ~4 billion, near uint32 max
