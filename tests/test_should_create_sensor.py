"""Test should_create_sensor function directly."""

from custom_components.sourceful_zap.sensor import should_create_sensor


def test_power_requires_any_der():
    assert should_create_sensor("power", ["pv"]) is True
    assert should_create_sensor("power", ["battery"]) is True
    assert should_create_sensor("power", ["meter"]) is True
    assert should_create_sensor("power", []) is False


def test_battery_sensors_require_battery():
    battery_keys = [
        "battery_soc", "battery_voltage", "battery_current",
        "battery_charge_total", "battery_discharge_total",
        "battery_upper_limit", "battery_lower_limit",
        "battery_power", "battery_temperature",
    ]
    for key in battery_keys:
        assert should_create_sensor(key, ["battery"]) is True
        assert should_create_sensor(key, ["pv"]) is False
        assert should_create_sensor(key, ["meter"]) is False
        assert should_create_sensor(key, []) is False


def test_energy_production_requires_pv():
    assert should_create_sensor("energy_production", ["pv"]) is True
    assert should_create_sensor("energy_production", ["battery"]) is False
    assert should_create_sensor("energy_production", ["meter"]) is False


def test_temperature_requires_pv():
    assert should_create_sensor("temperature", ["pv"]) is True
    assert should_create_sensor("temperature", ["battery"]) is False


def test_energy_import_export_standalone_meter_only():
    assert should_create_sensor("energy_import", ["meter"]) is True
    assert should_create_sensor("energy_export", ["meter"]) is True
    # PV with meter should NOT create import/export
    assert should_create_sensor("energy_import", ["pv", "meter"]) is False
    assert should_create_sensor("energy_export", ["pv", "meter"]) is False
    assert should_create_sensor("energy_import", ["pv"]) is False


def test_grid_frequency_standalone_meter_only():
    assert should_create_sensor("grid_frequency", ["meter"]) is True
    assert should_create_sensor("grid_frequency", ["pv", "meter"]) is False
    assert should_create_sensor("grid_frequency", ["pv"]) is False


def test_phase_sensors_standalone_meter_only():
    phase_keys = [
        "l1_voltage", "l1_current", "l1_power",
        "l2_voltage", "l2_current", "l2_power",
        "l3_voltage", "l3_current", "l3_power",
    ]
    for key in phase_keys:
        assert should_create_sensor(key, ["meter"]) is True
        assert should_create_sensor(key, ["pv", "meter"]) is False
        assert should_create_sensor(key, ["pv"]) is False


def test_unknown_sensor_key():
    assert should_create_sensor("unknown_key", ["pv", "battery", "meter"]) is False


def test_multiple_ders():
    assert should_create_sensor("power", ["pv", "battery", "meter"]) is True
    assert should_create_sensor("battery_soc", ["pv", "battery"]) is True
    assert should_create_sensor("energy_production", ["pv", "battery"]) is True
