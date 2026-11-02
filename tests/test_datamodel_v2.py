"""Firmware 7.x / Sourceful data model v2 parsing.

Fixtures are the local REST bodies. The captured cloud proxy wrapped these
in {code, response, latency_ms}; the Zap's own API returns the inner object.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.util.dt import utc_from_timestamp

from custom_components.sourceful_zap.datamodel import (
    is_data_model_v2,
    parse_device_data,
)
from tests.test_sensor import GATEWAY, get_entity_id, get_state, setup_integration

FIXTURES = Path(__file__).parent / "fixtures"
SOLIS_SN = "1033060242040054"
P1_SN = "p1m-0000788327eef648"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


SOLIS_DATA = _load("fw7_solis_data.json")
SOLIS_DERS = _load("fw7_solis_ders.json")
P1_DATA = _load("fw7_p1_data.json")
P1_DERS = _load("fw7_p1_ders.json")


def test_v2_detection_uses_version_or_key_presence():
    """v2 is explicit version or v2-only keys; v1 field names stay v1."""
    assert is_data_model_v2(SOLIS_DATA) is True
    assert is_data_model_v2(P1_DATA) is True
    assert is_data_model_v2({"solar": {"W_dc": -10}}) is True
    assert is_data_model_v2({"battery": {"soc_nom_fract": 0.4, "W_dc": -1}}) is True
    assert is_data_model_v2({"version": "v1", "pv": {"W": -10}}) is False
    assert (
        is_data_model_v2({"battery": {"W": -10, "SoC_nom_fract": 0.5}, "version": "v0"})
        is False
    )


def test_solis_v2_payload_maps_onto_existing_sensors():
    """Live fw 7.0.3 Solis hybrid: solar + battery + meter + inverter."""
    data, der_types = parse_device_data(SOLIS_DATA, SOLIS_DERS, SOLIS_SN)

    assert der_types == ["solar", "battery", "meter", "inverter"]

    # Night capture: solar W_dc is 0, battery is discharging 881 W.
    # Aggregate power is solar (sign flipped) + battery, not the grid meter
    # and not the inverter (that would double-count).
    assert data["power"] == -881.0
    assert data["energy_production"] == 15786000.0
    assert data["pv_make"] == "solis"

    assert data["battery_power"] == -881.0
    assert data["battery_soc"] == pytest.approx(24.0)
    assert data["battery_voltage"] == 450.6
    assert data["battery_current"] == -1.9
    assert data["battery_charge_total"] == 7211000.0
    assert data["battery_discharge_total"] == 6267000.0
    assert data["battery_upper_limit"] == 8000.0
    assert data["battery_lower_limit"] == -8000.0
    assert data["battery_temperature"] == 0.0
    assert data["battery_available_charge"] == 11400.0
    assert data["battery_available_discharge"] == 2100.0
    assert data["battery_make"] == "solis"

    # Inverter AC power is negative on the wire while supplying.
    assert data["inverter_power"] == 890.0
    # Inverter temperature fills the general temperature sensor; solar has none.
    assert data["temperature"] == 29.1
    # Inverter nameplate, from telemetry, wins over the battery DER rating.
    assert data["rated_power"] == 10000.0
    assert data["capacity"] == 15000.0

    # Grid meter is parsed even though solar is present (unlike v1 embedded meters).
    assert data["grid_power"] == 168.0
    assert data["energy_import"] == 13840540.0
    assert data["energy_export"] == 16381280.0
    assert data["meter_make"] == "solis"
    assert data["l1_voltage"] == 230.3
    assert data["l1_current"] == -0.82
    assert data["l1_power"] == -96.0
    assert data["l2_voltage"] == 230.3
    assert data["l2_current"] == -1.18
    assert data["l2_power"] == -168.0
    assert data["l3_voltage"] == 229.7
    assert data["l3_current"] == 1.95
    assert data["l3_power"] == 432.0
    # Meter Hz wins over the inverter's 49.98.
    assert data["grid_frequency"] == 49.97
    assert "grid_reactive_power" not in data

    expected_harvest = utc_from_timestamp(1793643288096 / 1000).isoformat()
    assert data["last_harvest"] == expected_harvest


def test_solis_solar_production_sign_matches_v1():
    """A generating array is negative on the wire and positive in HA."""
    payload = deepcopy(SOLIS_DATA)
    payload["solar"]["W_dc"] = -4200
    data, _der_types = parse_device_data(payload, SOLIS_DERS, SOLIS_SN)
    # 4200 W production + battery discharging 881 W.
    assert data["power"] == pytest.approx(4200.0 - 881.0)


def test_p1_v2_payload_maps_meter_fields():
    """Live fw 7.0.3 P1 meter. Hz is null, so there is no grid frequency."""
    data, der_types = parse_device_data(P1_DATA, P1_DERS, P1_SN)

    assert der_types == ["meter"]
    assert data["power"] == 169.0
    assert "grid_power" not in data
    assert data["energy_import"] == 57805594.0
    assert data["energy_export"] == 7409377.0
    assert data["l1_voltage"] == 230.5
    assert data["l1_current"] == -0.7
    assert data["l1_power"] == -97.0
    assert data["l2_voltage"] == 230.3
    assert data["l2_current"] == -1.1
    assert data["l2_power"] == -168.0
    assert data["l3_voltage"] == 229.9
    assert data["l3_current"] == 2.3
    assert data["l3_power"] == 369.0
    assert data["grid_reactive_power"] == -638.0
    assert data["meter_make"] == "p1"
    assert "grid_frequency" not in data
    assert "battery_soc" not in data
    assert "energy_production" not in data


def test_v2_falls_back_to_v1_field_names_when_suffixed_values_are_null():
    """Null W_dc / l1_W_ac must not hide a populated legacy field."""
    payload = {
        "version": "v2",
        "solar": {
            "W_dc": None,
            "W_ac": None,
            "W": -1500,
            "total_generation_Wh_dc": None,
            "total_generation_Wh": 42,
        },
        "meter": {
            "W_ac": None,
            "W": 42,
            "l1_W_ac": None,
            "L1_W": 10,
            "l1_V_ac": None,
            "L1_V": 230,
            "Hz": None,
        },
    }
    data, _der_types = parse_device_data(payload, None, "SN")
    assert data["power"] == 1500.0
    assert data["energy_production"] == 42.0
    # Meter-only alongside solar? solar block is present, so meter watts are
    # grid power rather than the aggregate. v2 + solar suppresses aggregate.
    assert data["grid_power"] == 42.0
    assert data["l1_power"] == 10.0
    assert data["l1_voltage"] == 230.0
    assert "grid_frequency" not in data


def test_v2_detected_from_keys_when_version_field_is_missing():
    """Key presence is enough when firmware omits version."""
    payload = {
        "battery": {
            "W_ac": None,
            "W_dc": 250,
            "V_ac": None,
            "V_dc": 400.5,
            "soc_nom_fract": 0.5,
        }
    }
    assert is_data_model_v2(payload) is True
    data, _der_types = parse_device_data(payload, None, "SN")
    assert data["battery_power"] == 250.0
    assert data["power"] == 250.0
    assert data["battery_voltage"] == 400.5
    assert data["battery_soc"] == pytest.approx(50.0)


def test_v2_invalid_numbers_are_filtered():
    """NaN and uint32-overflow energy values are dropped on v2 keys too."""
    payload = {
        "version": "v2",
        "meter": {
            "W_ac": 10,
            "l1_W_ac": float("nan"),
            "total_import_Wh_ac": 1000,
            "total_export_Wh_ac": 4294836224,
        },
    }
    data, _der_types = parse_device_data(payload, None, "SN")
    assert data["power"] == 10.0
    assert data["energy_import"] == 1000.0
    assert "l1_power" not in data
    assert "energy_export" not in data


def test_v2_der_metadata_rated_power_and_capacity_keys():
    """DER metadata uses rated_power_W_* and capacity_Wh_* on firmware 7."""
    ders = {
        "sn": "SN",
        "ders": [
            {"type": "solar", "enabled": True, "installed_power_W_dc": 8000},
            {
                "type": "battery",
                "enabled": True,
                "rated_power_W_dc": 5000,
                "capacity_Wh_dc": 15000,
            },
        ],
    }
    data, der_types = parse_device_data({}, ders, "SN")
    assert der_types == ["solar", "battery"]
    # installed_power is not a rated-power field; the battery rating is.
    assert data["rated_power"] == 5000.0
    assert data["capacity"] == 15000.0


def test_null_dc_uses_ac_and_inverter_frequency_fills_a_meter_without_hz():
    """The unused ac/dc side is null; the other side is the measurement."""
    payload = {
        "version": "v2",
        "solar": {"W_dc": -100, "temperature_C": 41.5},
        "battery": {"W_dc": None, "W_ac": -40, "A_dc": None, "A_ac": -2.5},
        "inverter": {"Hz": 50.01, "temperature_C": 60, "W_ac": None},
        "meter": {"Hz": None, "W_ac": 15},
    }
    data, _der_types = parse_device_data(payload, None, "SN")
    assert data["battery_power"] == -40.0
    assert data["battery_current"] == -2.5
    # Solar generation flipped, plus the AC-coupled battery.
    assert data["power"] == pytest.approx(100.0 - 40.0)
    # Solar temperature wins over the inverter temperature.
    assert data["temperature"] == 41.5
    # Meter has no Hz, so the inverter frequency is kept.
    assert data["grid_frequency"] == 50.01
    assert "inverter_power" not in data


def test_disabled_der_and_non_numeric_values_are_ignored():
    """Disabled DER entries and garbage numbers do not become sensors."""
    ders = {
        "ders": [
            "nope",
            {"enabled": False, "type": "solar", "rated_power_W_dc": 999},
            {"type": "meter", "enabled": True},
        ]
    }
    payload = {
        "version": "v2",
        "meter": {"W_ac": "not-a-number", "l1_A_ac": 1e7, "l1_V_ac": 230},
    }
    data, der_types = parse_device_data(payload, ders, "SN")
    assert der_types == ["meter"]
    assert "power" not in data
    assert "l1_current" not in data
    assert data["l1_voltage"] == 230.0
    assert "rated_power" not in data


def test_ev_charger_port_power_is_parsed():
    """ev_charger_port is optional on v2; positive watts mean charging."""
    payload = {
        "version": "v2",
        "ev_charger_port": {"W_ac": 7400, "W_dc": None, "type": "ev_charger_port"},
    }
    data, _der_types = parse_device_data(payload, None, "SN")
    assert data["ev_charger_power"] == 7400.0
    assert data["power"] == 7400.0


def _api(devices, data, ders, system=None):
    api = MagicMock()
    api.get_devices = AsyncMock(return_value=devices)
    api.get_device_data = AsyncMock(return_value=data)
    api.get_device_ders = AsyncMock(return_value=ders)
    api.get_system_info = AsyncMock(
        return_value=system
        or {
            "uptimeSeconds": 10,
            "zap": {
                "deviceId": GATEWAY,
                "firmwareVersion": "7.0.3",
                "network": {"wifiStatus": "connected", "ssid": "lab", "rssi": -40},
            },
        }
    )
    api.test_connection = AsyncMock(return_value=True)
    return api


async def test_solis_v2_sensors_are_created(hass, mock_config_entry):
    """Hybrid inverter entities follow the /ders types, not a v1 pv list."""
    api = _api(
        devices=[
            {
                "serial_number": SOLIS_SN,
                "sn": SOLIS_SN,
                "name": "Solis",
                "model": "solis",
                "type": "modbus_tcp",
                "profile": "solis",
                "connection_status": True,
                # Device list omits DERs; /ders is what sensor setup must use.
                "ders": [],
            }
        ],
        data=SOLIS_DATA,
        ders=SOLIS_DERS,
    )
    await setup_integration(hass, mock_config_entry, api)

    prefix = f"sourceful_zap_{GATEWAY}_solis_{SOLIS_SN}"
    assert get_state(hass, f"{prefix}_power").state == "-881.0"
    assert get_state(hass, f"{prefix}_energy_production").state == "15786000.0"
    assert get_state(hass, f"{prefix}_battery_soc").state == "24.0"
    assert get_state(hass, f"{prefix}_battery_power").state == "-881.0"
    assert get_state(hass, f"{prefix}_battery_available_charge").state == "11400.0"
    assert get_state(hass, f"{prefix}_battery_available_discharge").state == "2100.0"
    assert get_state(hass, f"{prefix}_inverter_power").state == "890.0"
    assert get_state(hass, f"{prefix}_grid_power").state == "168.0"
    assert get_state(hass, f"{prefix}_energy_import").state == "13840540.0"
    assert get_state(hass, f"{prefix}_energy_export").state == "16381280.0"
    assert get_state(hass, f"{prefix}_l1_power").state == "-96.0"
    assert get_state(hass, f"{prefix}_l3_voltage").state == "229.7"
    assert get_state(hass, f"{prefix}_grid_frequency").state == "49.97"
    assert get_state(hass, f"{prefix}_temperature").state == "29.1"
    assert get_entity_id(hass, f"{prefix}_grid_reactive_power") is None

    power = get_state(hass, f"{prefix}_power")
    assert power.attributes["rated_power"] == 10000.0
    assert power.attributes["capacity"] == 15000.0
    assert get_state(
        hass, f"sourceful_zap_{GATEWAY}_gateway_firmware_version"
    ).state == ("7.0.3")


async def test_p1_v2_sensors(hass, mock_config_entry):
    """v2 P1 meter keeps phase and energy sensors and still skips Hz."""
    api = _api(
        devices=[
            {
                "serial_number": P1_SN,
                "sn": P1_SN,
                "name": "P1",
                "model": "p1_uart",
                "type": "p1_uart",
                "profile": "p1_uart",
                "connection_status": True,
                "ders": [{"type": "meter", "enabled": True}],
            }
        ],
        data=P1_DATA,
        ders=P1_DERS,
    )
    await setup_integration(hass, mock_config_entry, api)

    prefix = f"sourceful_zap_{GATEWAY}_p1_uart_{P1_SN}"
    assert get_state(hass, f"{prefix}_power").state == "169.0"
    assert get_state(hass, f"{prefix}_energy_import").state == "57805594.0"
    assert get_state(hass, f"{prefix}_l2_power").state == "-168.0"
    assert get_state(hass, f"{prefix}_grid_reactive_power").state == "-638.0"
    assert get_entity_id(hass, f"{prefix}_grid_frequency") is None
    assert get_entity_id(hass, f"{prefix}_grid_power") is None
    assert get_entity_id(hass, f"{prefix}_energy_production") is None
    assert get_entity_id(hass, f"{prefix}_inverter_power") is None
