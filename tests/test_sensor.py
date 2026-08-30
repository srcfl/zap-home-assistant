"""Test Zap Energy sensors."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.sourceful_zap.const import DOMAIN
from custom_components.sourceful_zap.sensor import should_create_sensor

GATEWAY = "zap-gateway-12345"


async def setup_integration(hass, mock_config_entry, api):
    """Set up the integration with a mocked API client."""
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=api):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()


def get_entity_id(hass, unique_id):
    """Resolve an entity id from its unique id, or None if not registered."""
    entity_registry = er.async_get(hass)
    return entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id)


def get_state(hass, unique_id):
    """Return the state object for a sensor with the given unique id."""
    entity_id = get_entity_id(hass, unique_id)
    assert entity_id is not None, f"No entity registered for {unique_id}"
    return hass.states.get(entity_id)


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test sensor entities are created correctly for a PV device."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    prefix = f"sourceful_zap_{GATEWAY}_solaredge_INV001"

    # PV device sensors
    assert get_entity_id(hass, f"{prefix}_power") is not None
    assert get_entity_id(hass, f"{prefix}_energy_production") is not None
    assert get_entity_id(hass, f"{prefix}_temperature") is not None

    # Sensors that make no sense for a PV-only device are not created
    assert get_entity_id(hass, f"{prefix}_battery_soc") is None
    assert get_entity_id(hass, f"{prefix}_energy_import") is None
    assert get_entity_id(hass, f"{prefix}_energy_export") is None
    assert get_entity_id(hass, f"{prefix}_l1_voltage") is None
    assert get_entity_id(hass, f"{prefix}_grid_frequency") is None

    # Gateway diagnostic sensors
    for key in (
        "gateway_uptime",
        "gateway_temperature",
        "gateway_memory_percent",
        "gateway_memory_free",
        "gateway_firmware_version",
        "gateway_wifi_status",
        "gateway_wifi_ssid",
        "gateway_signal_strength",
    ):
        assert get_entity_id(hass, f"sourceful_zap_{GATEWAY}_{key}") is not None


async def test_power_sensor_state(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test power sensor state and attributes."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    # Fixture PV W is -2500; the coordinator flips the sign
    state = get_state(hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_power")
    assert state is not None
    assert state.state == "2500.0"
    assert state.attributes["device_class"] == SensorDeviceClass.POWER
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == UnitOfPower.WATT


async def test_energy_production_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test energy production sensor state and attributes."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    state = get_state(
        hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_energy_production"
    )
    assert state is not None
    assert state.state == "50900524.0"
    assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert state.attributes["unit_of_measurement"] == UnitOfEnergy.WATT_HOUR


async def test_energy_import_export_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api_p1_meter
):
    """Test energy import/export sensor states for a P1 meter."""
    await setup_integration(hass, mock_config_entry, mock_zap_api_p1_meter)

    prefix = f"sourceful_zap_{GATEWAY}_p1_uart_p1m-00003c7f387506dc"

    import_state = get_state(hass, f"{prefix}_energy_import")
    assert import_state is not None
    assert import_state.state == "73447080.0"
    assert import_state.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert import_state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert import_state.attributes["unit_of_measurement"] == UnitOfEnergy.WATT_HOUR

    export_state = get_state(hass, f"{prefix}_energy_export")
    assert export_state is not None
    assert export_state.state == "16450102.0"


async def test_p1_meter_phase_sensors(
    hass: HomeAssistant, mock_config_entry, mock_zap_api_p1_meter
):
    """Test per-phase sensor states for a P1 meter."""
    await setup_integration(hass, mock_config_entry, mock_zap_api_p1_meter)

    prefix = f"sourceful_zap_{GATEWAY}_p1_uart_p1m-00003c7f387506dc"

    assert get_state(hass, f"{prefix}_power").state == "24.0"
    assert get_state(hass, f"{prefix}_l1_voltage").state == "231.7"
    assert get_state(hass, f"{prefix}_l1_current").state == "1.0"
    assert get_state(hass, f"{prefix}_l1_power").state == "119.0"
    assert get_state(hass, f"{prefix}_l2_voltage").state == "232.2"
    assert get_state(hass, f"{prefix}_l3_current").state == "-0.7"
    assert get_state(hass, f"{prefix}_l3_power").state == "-167.0"


async def test_grid_frequency_not_created_for_p1_meter(
    hass: HomeAssistant, mock_config_entry, mock_zap_api_p1_meter
):
    """Test grid frequency sensor is not created for p1_uart devices."""
    await setup_integration(hass, mock_config_entry, mock_zap_api_p1_meter)

    prefix = f"sourceful_zap_{GATEWAY}_p1_uart_p1m-00003c7f387506dc"
    assert get_entity_id(hass, f"{prefix}_grid_frequency") is None


def test_should_create_sensor_rules():
    """Test the should_create_sensor rules directly."""
    # Grid frequency: standalone meter yes, p1_uart never, PV never
    assert should_create_sensor("grid_frequency", ["meter"], "modbus_tcp") is True
    assert should_create_sensor("grid_frequency", ["meter"], "p1_uart") is False
    assert should_create_sensor("grid_frequency", ["pv", "meter"], "modbus_tcp") is False

    # Battery sensors need a battery DER
    assert should_create_sensor("battery_soc", ["battery"]) is True
    assert should_create_sensor("battery_soc", ["pv"]) is False

    # PV-only sensors
    assert should_create_sensor("energy_production", ["pv"]) is True
    assert should_create_sensor("energy_production", ["meter"]) is False
    assert should_create_sensor("temperature", ["pv"]) is True

    # Meter sensors are suppressed on PV devices with embedded meters
    assert should_create_sensor("energy_import", ["meter"]) is True
    assert should_create_sensor("energy_import", ["pv", "meter"]) is False
    assert should_create_sensor("l1_voltage", ["meter"]) is True
    assert should_create_sensor("l1_voltage", ["pv", "meter"]) is False

    # Power needs at least one DER
    assert should_create_sensor("power", ["meter"]) is True
    assert should_create_sensor("power", []) is False

    # Unknown keys are never created
    assert should_create_sensor("bogus", ["pv", "battery", "meter"]) is False


async def test_battery_sensor_states(
    hass: HomeAssistant, mock_config_entry, mock_zap_api_battery
):
    """Test battery sensor states and attributes."""
    await setup_integration(hass, mock_config_entry, mock_zap_api_battery)

    prefix = f"sourceful_zap_{GATEWAY}_pixii_BAT001"

    soc_state = get_state(hass, f"{prefix}_battery_soc")
    assert soc_state is not None
    assert soc_state.state == "66.3"
    assert soc_state.attributes["device_class"] == SensorDeviceClass.BATTERY
    assert soc_state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert soc_state.attributes["unit_of_measurement"] == PERCENTAGE

    power_state = get_state(hass, f"{prefix}_battery_power")
    assert power_state.state == "-1040.0"
    assert power_state.attributes["device_class"] == SensorDeviceClass.POWER
    assert power_state.attributes["unit_of_measurement"] == UnitOfPower.WATT

    assert get_state(hass, f"{prefix}_battery_voltage").state == "52.82"
    assert get_state(hass, f"{prefix}_battery_current").state == "-21.3"
    assert get_state(hass, f"{prefix}_battery_charge_total").state == "5261000.0"
    assert get_state(hass, f"{prefix}_battery_discharge_total").state == "4389000.0"
    assert get_state(hass, f"{prefix}_battery_temperature").state == "28.0"

    # Battery DER metadata ends up as extra attributes on the power sensor
    agg_power = get_state(hass, f"{prefix}_power")
    assert agg_power.state == "-1040.0"
    assert agg_power.attributes["rated_power"] == 5000.0
    assert agg_power.attributes["capacity"] == 10000.0


async def test_temperature_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test temperature sensor state and attributes."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    state = get_state(hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_temperature")
    assert state is not None
    assert state.state == "45.5"
    assert state.attributes["device_class"] == SensorDeviceClass.TEMPERATURE
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS


async def test_gateway_sensor_states(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test gateway diagnostic sensor states from firmware v2.3.15 data."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    prefix = f"sourceful_zap_{GATEWAY}"

    assert get_state(hass, f"{prefix}_gateway_uptime").state == "177"
    assert get_state(hass, f"{prefix}_gateway_temperature").state == "0.0"
    assert get_state(hass, f"{prefix}_gateway_memory_percent").state == "66.6433"
    assert get_state(hass, f"{prefix}_gateway_memory_free").state == "78.0"
    assert get_state(hass, f"{prefix}_gateway_firmware_version").state == "2.3.15"
    assert get_state(hass, f"{prefix}_gateway_wifi_status").state == "connected"
    assert get_state(hass, f"{prefix}_gateway_wifi_ssid").state == "MyNetwork"

    signal_state = get_state(hass, f"{prefix}_gateway_signal_strength")
    assert signal_state.state == "-84.0"
    assert (
        signal_state.attributes["device_class"] == SensorDeviceClass.SIGNAL_STRENGTH
    )
    assert (
        signal_state.attributes["unit_of_measurement"]
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )


async def test_sensor_extra_attributes(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors include extra state attributes."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    state = get_state(hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_power")
    assert state is not None
    # rated_power comes from the PV data (rated_power_W)
    assert state.attributes["rated_power"] == 8000.0


async def test_sensor_availability_on_success(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors are available when data is present."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    prefix = f"sourceful_zap_{GATEWAY}_solaredge_INV001"
    for key in ("power", "energy_production", "temperature"):
        assert get_state(hass, f"{prefix}_{key}").state != "unavailable"


async def test_sensor_unavailable_on_missing_data(
    hass: HomeAssistant, mock_config_entry
):
    """Test sensors become unavailable when data is missing."""
    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP12345",
                "sn": "ZAP12345",
                "name": "Meter ZAP12345",
                "model": "meter",
                "type": "modbus_tcp",
                "profile": "meter",
                "connection_status": True,
                "ders": [{"type": "meter", "enabled": True}],
            }
        ]
    )
    # Return empty data
    mock_api.get_device_data = AsyncMock(return_value={})
    mock_api.get_device_ders = AsyncMock(return_value={})
    mock_api.get_system_info = AsyncMock(return_value={})

    await setup_integration(hass, mock_config_entry, mock_api)

    prefix = f"sourceful_zap_{GATEWAY}_meter_ZAP12345"

    # Sensors without data should be unavailable
    assert get_state(hass, f"{prefix}_power").state == "unavailable"
    assert get_state(hass, f"{prefix}_energy_import").state == "unavailable"


async def test_sensor_update(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test sensor state updates when coordinator refreshes."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    unique_id = f"sourceful_zap_{GATEWAY}_solaredge_INV001_power"

    # Initial state
    assert get_state(hass, unique_id).state == "2500.0"

    # Update mock data (negative W = producing)
    mock_zap_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": -3000.0,
                "total_generation_Wh": 50900700,
            },
        }
    )

    # Trigger coordinator update
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinators"][
        "INV001"
    ]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Check updated state
    assert get_state(hass, unique_id).state == "3000.0"
    energy_state = get_state(
        hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_energy_production"
    )
    assert energy_state.state == "50900700.0"


async def test_sensor_device_info(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors have correct device info."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    entity_registry = er.async_get(hass)
    entity_id = get_entity_id(hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_power")
    power_entity = entity_registry.async_get(entity_id)

    assert power_entity is not None
    assert power_entity.device_id is not None


async def test_sensor_has_entity_name(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors use the has_entity_name pattern."""
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    entity_registry = er.async_get(hass)
    entity_id = get_entity_id(hass, f"sourceful_zap_{GATEWAY}_solaredge_INV001_power")
    power_entity = entity_registry.async_get(entity_id)

    assert power_entity is not None
    assert power_entity.has_entity_name is True


async def test_multiple_devices(hass: HomeAssistant, mock_config_entry):
    """Test sensors are created for multiple devices."""
    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "DEV1",
                "sn": "DEV1",
                "name": "Solaredge DEV1",
                "model": "solaredge",
                "type": "modbus_tcp",
                "profile": "solaredge",
                "connection_status": True,
                "ders": [{"type": "pv", "enabled": True}],
            },
            {
                "serial_number": "DEV2",
                "sn": "DEV2",
                "name": "Sungrow DEV2",
                "model": "sungrow",
                "type": "modbus_tcp",
                "profile": "sungrow",
                "connection_status": True,
                "ders": [{"type": "pv", "enabled": True}],
            },
        ]
    )
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {"type": "pv", "W": -1500.0},
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})
    mock_api.get_system_info = AsyncMock(return_value={})

    await setup_integration(hass, mock_config_entry, mock_api)

    device1_power = get_state(hass, f"sourceful_zap_{GATEWAY}_solaredge_DEV1_power")
    device2_power = get_state(hass, f"sourceful_zap_{GATEWAY}_sungrow_DEV2_power")

    assert device1_power is not None
    assert device1_power.state == "1500.0"
    assert device2_power is not None
    assert device2_power.state == "1500.0"


async def test_sensor_suggested_display_precision(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors have correct suggested display precision.

    Modern HA stores suggested_display_precision in entity registry
    options, not in the state attributes.
    """
    await setup_integration(hass, mock_config_entry, mock_zap_api)

    entity_registry = er.async_get(hass)
    prefix = f"sourceful_zap_{GATEWAY}_solaredge_INV001"

    def precision(unique_id):
        entry = entity_registry.async_get(get_entity_id(hass, unique_id))
        return entry.options["sensor"]["suggested_display_precision"]

    # Power sensor - 0 decimal places
    assert precision(f"{prefix}_power") == 0

    # Energy sensor - 2 decimal places
    assert precision(f"{prefix}_energy_production") == 2

    # Temperature sensor - 1 decimal place
    assert precision(f"{prefix}_temperature") == 1


async def test_sensor_none_value_handling(hass: HomeAssistant, mock_config_entry):
    """Test sensors handle missing values correctly."""
    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "INV001",
                "sn": "INV001",
                "name": "Solaredge INV001",
                "model": "solaredge",
                "type": "modbus_tcp",
                "profile": "solaredge",
                "connection_status": True,
                "ders": [{"type": "pv", "enabled": True}],
            }
        ]
    )
    # PV data with power but no generation counter
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": -1500.0,
                "total_generation_Wh": None,  # Explicit None
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})
    mock_api.get_system_info = AsyncMock(return_value={})

    await setup_integration(hass, mock_config_entry, mock_api)

    prefix = f"sourceful_zap_{GATEWAY}_solaredge_INV001"

    assert get_state(hass, f"{prefix}_power").state == "1500.0"

    # Energy production should be unavailable due to the None value
    assert get_state(hass, f"{prefix}_energy_production").state == "unavailable"
