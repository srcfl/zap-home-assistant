"""Unit tests for sensor entity classes (no full HA setup needed)."""

from unittest.mock import MagicMock, PropertyMock

from custom_components.sourceful_zap.sensor import (
    GATEWAY_SENSOR_TYPES,
    SENSOR_TYPES,
    ZapGatewaySensor,
    ZapGatewaySensorEntityDescription,
    ZapSensor,
    ZapSensorEntityDescription,
)


def _make_device_coordinator(data, last_update_success=True):
    """Create a mock device coordinator."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = last_update_success
    # CoordinatorEntity.__init__ calls super().__init__ which accesses coordinator
    return coordinator


def _make_gateway_coordinator(data, last_update_success=True):
    """Create a mock gateway coordinator."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = last_update_success
    return coordinator


class TestZapSensorDescriptions:
    """Test SENSOR_TYPES definitions."""

    def test_all_sensor_types_have_value_fn(self):
        for desc in SENSOR_TYPES:
            assert desc.value_fn is not None, f"{desc.key} missing value_fn"

    def test_all_sensor_types_have_available_fn(self):
        for desc in SENSOR_TYPES:
            assert desc.available_fn is not None, f"{desc.key} missing available_fn"

    def test_power_sensor_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "power")
        assert desc.value_fn({"power": 1500}) == 1500
        assert desc.value_fn({}) is None

    def test_energy_import_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "energy_import")
        assert desc.value_fn({"energy_import": 50000}) == 50000
        assert desc.value_fn({}) is None

    def test_energy_production_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "energy_production")
        assert desc.value_fn({"energy_production": 30000}) == 30000

    def test_energy_export_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "energy_export")
        assert desc.value_fn({"energy_export": 20000}) == 20000

    def test_battery_soc_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_soc")
        assert desc.value_fn({"battery_soc": 75.5}) == 75.5

    def test_battery_voltage_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_voltage")
        assert desc.value_fn({"battery_voltage": 48.5}) == 48.5

    def test_battery_current_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_current")
        assert desc.value_fn({"battery_current": -21.3}) == -21.3

    def test_battery_charge_total_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_charge_total")
        assert desc.value_fn({"battery_charge_total": 5261000}) == 5261000

    def test_battery_discharge_total_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_discharge_total")
        assert desc.value_fn({"battery_discharge_total": 4389000}) == 4389000

    def test_battery_upper_limit_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_upper_limit")
        assert desc.value_fn({"battery_upper_limit": 10000}) == 10000

    def test_battery_lower_limit_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_lower_limit")
        assert desc.value_fn({"battery_lower_limit": -10000}) == -10000

    def test_temperature_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "temperature")
        assert desc.value_fn({"temperature": 45.5}) == 45.5

    def test_battery_power_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_power")
        assert desc.value_fn({"battery_power": -500}) == -500

    def test_battery_temperature_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "battery_temperature")
        assert desc.value_fn({"battery_temperature": 28.0}) == 28.0

    def test_grid_frequency_value_fn(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "grid_frequency")
        assert desc.value_fn({"grid_frequency": 50.02}) == 50.02

    def test_phase_voltage_value_fns(self):
        for phase in ["l1", "l2", "l3"]:
            key = f"{phase}_voltage"
            desc = next(d for d in SENSOR_TYPES if d.key == key)
            assert desc.value_fn({key: 230.0}) == 230.0

    def test_phase_current_value_fns(self):
        for phase in ["l1", "l2", "l3"]:
            key = f"{phase}_current"
            desc = next(d for d in SENSOR_TYPES if d.key == key)
            assert desc.value_fn({key: 2.1}) == 2.1

    def test_phase_power_value_fns(self):
        for phase in ["l1", "l2", "l3"]:
            key = f"{phase}_power"
            desc = next(d for d in SENSOR_TYPES if d.key == key)
            assert desc.value_fn({key: 418}) == 418

    def test_available_fn_returns_true_when_present(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "power")
        assert desc.available_fn({"power": 1500}) is True

    def test_available_fn_returns_false_when_missing(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "power")
        assert desc.available_fn({}) is False

    def test_available_fn_returns_false_when_none(self):
        desc = next(d for d in SENSOR_TYPES if d.key == "power")
        assert desc.available_fn({"power": None}) is False


class TestGatewaySensorDescriptions:
    """Test GATEWAY_SENSOR_TYPES definitions."""

    def test_all_gateway_types_have_value_fn(self):
        for desc in GATEWAY_SENSOR_TYPES:
            assert desc.value_fn is not None, f"{desc.key} missing value_fn"

    def test_all_gateway_types_have_available_fn(self):
        for desc in GATEWAY_SENSOR_TYPES:
            assert desc.available_fn is not None, f"{desc.key} missing available_fn"

    def test_uptime_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_uptime")
        assert desc.value_fn({"uptime_seconds": 16975}) == 16975

    def test_gateway_temperature_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_temperature")
        assert desc.value_fn({"gateway_temperature": 42.0}) == 42.0

    def test_memory_percent_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_memory_percent")
        assert desc.value_fn({"memory_percent": 73.25}) == 73.25

    def test_memory_free_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_memory_free")
        assert desc.value_fn({"memory_free": 67.5}) == 67.5

    def test_firmware_version_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_firmware_version")
        assert desc.value_fn({"firmware_version": "1.8.50"}) == "1.8.50"

    def test_wifi_status_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_wifi_status")
        assert desc.value_fn({"wifi_status": "connected"}) == "connected"

    def test_wifi_ssid_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_wifi_ssid")
        assert desc.value_fn({"wifi_ssid": "MyNetwork"}) == "MyNetwork"

    def test_signal_strength_value_fn(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_signal_strength")
        assert desc.value_fn({"signal_strength": -47}) == -47

    def test_gateway_available_fn_present(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_uptime")
        assert desc.available_fn({"uptime_seconds": 100}) is True

    def test_gateway_available_fn_missing(self):
        desc = next(d for d in GATEWAY_SENSOR_TYPES if d.key == "gateway_uptime")
        assert desc.available_fn({}) is False

    def test_gateway_sensor_count(self):
        """Verify expected number of gateway sensor types."""
        assert len(GATEWAY_SENSOR_TYPES) == 8

    def test_device_sensor_count(self):
        """Verify expected number of device sensor types."""
        assert len(SENSOR_TYPES) == 24
