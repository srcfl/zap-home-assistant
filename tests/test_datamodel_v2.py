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
from homeassistant.helpers import entity_registry as er
from homeassistant.util.dt import utc_from_timestamp

from custom_components.sourceful_zap.const import DOMAIN
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
# A 5 kW three-phase SMA inverter with no SMA Energy Meter, on firmware 7.0.3.
SMA_DATA = _load("fw7_sma_data.json")
SMA_DERS = _load("fw7_sma_ders.json")
SMA_SN = SMA_DERS["sn"]
SMA_INVERTER = {
    "type": "inverter",
    "make": "sma",
    "timestamp": 1793793785918,
    "W_ac": -2617,
    "Hz": 50.0,
    "temperature_C": 38.9,
    "rated_power_W_ac": 5000,
    "l1_V_ac": 233.05,
    "l2_V_ac": 229.32,
    "l3_V_ac": 231.39,
    "l1_A_ac": -3.681,
    "l2_A_ac": -3.686,
    "l3_A_ac": -3.698,
    "l1_W_ac": -878,
    "l2_W_ac": -865,
    "l3_W_ac": -874,
}


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


def test_mppt_inputs_read_positive_while_generating():
    """Each PV input keeps its voltage; current and power flip like power."""
    data, _ = parse_device_data(SMA_DATA, SMA_DERS, SMA_SN)

    assert data["mppt1_voltage"] == 353.96
    assert data["mppt1_current"] == 4.036
    assert data["mppt1_power"] == 1428.58
    assert data["mppt2_voltage"] == 354.55
    assert data["mppt2_current"] == 4.032
    assert data["mppt2_power"] == 1429.55


def test_mppt_tolerates_nulls_zeros_and_bad_shapes():
    """Unread inputs stay out, a 0 stays +0, and odd payloads are ignored."""
    payload = {
        "version": "v2",
        "solar": {
            "mppt": [
                {"V_dc": 0, "A_dc": 0, "W_dc": 0},
                {"V_dc": None, "A_dc": None, "W_dc": None},
                {"V_dc": 300, "A_dc": -1, "W_dc": -300},
            ]
        },
    }
    data, _ = parse_device_data(payload, {}, "sn")
    assert data["mppt1_voltage"] == 0
    assert str(data["mppt1_current"]) == "0.0"
    assert str(data["mppt1_power"]) == "0.0"
    assert "mppt2_voltage" not in data
    # A third input has no sensor
    assert "mppt3_voltage" not in data

    for odd in (None, "x", ["x"]):
        data, _ = parse_device_data({"version": "v2", "solar": {"mppt": odd}}, {}, "sn")
        assert "mppt1_voltage" not in data


def test_inverter_phases_fill_phase_sensors_when_there_is_no_meter():
    """The AC output stage reads positive while supplying, phases included."""
    payload = {**deepcopy(SMA_DATA), "inverter": SMA_INVERTER}
    data, _ = parse_device_data(payload, SMA_DERS, SMA_SN)

    assert data["inverter_power"] == 2617
    assert data["grid_frequency"] == 50.0
    assert data["temperature"] == 38.9
    assert data["rated_power"] == 5000
    assert data["l1_voltage"] == 233.05
    assert data["l2_current"] == 3.686
    assert data["l3_power"] == 874


def test_inverter_phases_do_not_replace_the_grid_meter():
    """With a grid meter the phase sensors stay the meter's, signs included."""
    payload = {
        "version": "v2",
        "inverter": SMA_INVERTER,
        "meter": {"W_ac": 100, "l1_V_ac": 240.0, "l1_W_ac": 40},
    }
    data, _ = parse_device_data(payload, {}, "sn")

    assert data["l1_voltage"] == 240.0
    assert data["l1_power"] == 40
    # What the meter did not read is not filled from the inverter
    assert "l2_voltage" not in data
    assert "l3_power" not in data
    assert data["inverter_power"] == 2617


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


def _sma_device():
    return {
        "serial_number": SMA_SN,
        "sn": SMA_SN,
        "name": "SMA",
        "model": "sma",
        "type": "modbus_tcp",
        "profile": "sma",
        "connection_status": True,
        "ders": SMA_DERS["ders"],
    }


def _registered_device_sensors(hass):
    """Return the sensor keys registered for the SMA device."""
    prefix = f"sourceful_zap_{GATEWAY}_sma_{SMA_SN}_"
    return {
        entry.unique_id.removeprefix(prefix)
        for entry in er.async_get(hass).entities.values()
        if entry.unique_id.startswith(prefix)
    }


async def test_sma_without_meter_gets_only_sensors_with_values(hass, mock_config_entry):
    """/ders lists meter and inverter, but only solar is sent: no dead sensors."""
    api = _api([_sma_device()], deepcopy(SMA_DATA), SMA_DERS)
    await setup_integration(hass, mock_config_entry, api)

    assert _registered_device_sensors(hass) == {
        "power",
        "energy_production",
        "mppt1_voltage",
        "mppt1_current",
        "mppt1_power",
        "mppt2_voltage",
        "mppt2_current",
        "mppt2_power",
    }
    prefix = f"sourceful_zap_{GATEWAY}_sma_{SMA_SN}"
    assert get_state(hass, f"{prefix}_power").state == "2857.0"
    assert get_state(hass, f"{prefix}_energy_production").state == "21686913.0"
    assert get_state(hass, f"{prefix}_mppt1_voltage").state == "353.96"
    assert get_state(hass, f"{prefix}_mppt2_power").state == "1429.55"
    assert (
        get_state(hass, f"{prefix}_mppt1_power").name == "Sma 3000000001 MPPT 1 Power"
    )


async def test_sma_inverter_block_after_a_firmware_update_adds_sensors(
    hass, mock_config_entry
):
    """A firmware that starts sending inverter data needs no reload, once."""
    api = _api([_sma_device()], deepcopy(SMA_DATA), SMA_DERS)
    await setup_integration(hass, mock_config_entry, api)
    before = _registered_device_sensors(hass)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinators"][SMA_SN]

    api.get_device_data = AsyncMock(
        return_value={**deepcopy(SMA_DATA), "inverter": SMA_INVERTER}
    )
    for _ in range(3):  # Later polls must not add the same sensors again
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    added = _registered_device_sensors(hass) - before
    assert added == {
        "inverter_power",
        "temperature",
        "grid_frequency",
        "l1_voltage",
        "l1_current",
        "l1_power",
        "l2_voltage",
        "l2_current",
        "l2_power",
        "l3_voltage",
        "l3_current",
        "l3_power",
    }
    prefix = f"sourceful_zap_{GATEWAY}_sma_{SMA_SN}"
    assert get_state(hass, f"{prefix}_inverter_power").state == "2617.0"
    assert get_state(hass, f"{prefix}_temperature").state == "38.9"
    assert get_state(hass, f"{prefix}_l3_power").state == "874.0"
    # The meter the device lists is still never read
    assert "energy_import" not in _registered_device_sensors(hass)
    assert "grid_power" not in _registered_device_sensors(hass)


async def test_single_phase_inverter_gets_no_empty_phases(hass, mock_config_entry):
    """Phases an inverter never reports get no sensors."""
    inverter = {
        **SMA_INVERTER,
        "l2_V_ac": None,
        "l2_A_ac": None,
        "l2_W_ac": None,
        "l3_V_ac": None,
        "l3_A_ac": None,
        "l3_W_ac": None,
    }
    api = _api([_sma_device()], {**deepcopy(SMA_DATA), "inverter": inverter}, SMA_DERS)
    await setup_integration(hass, mock_config_entry, api)

    sensors = _registered_device_sensors(hass)
    assert {"l1_voltage", "l1_current", "l1_power"} <= sensors
    assert not {key for key in sensors if key.startswith(("l2_", "l3_"))}


async def test_unload_stops_adding_sensors(hass, mock_config_entry):
    """The listener that adds sensors goes away with the entry."""
    api = _api([_sma_device()], deepcopy(SMA_DATA), SMA_DERS)
    await setup_integration(hass, mock_config_entry, api)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinators"][SMA_SN]

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert not coordinator._listeners  # pylint: disable=protected-access
