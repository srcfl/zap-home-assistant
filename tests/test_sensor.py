"""Test Zap Energy sensors."""

from unittest.mock import patch

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


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test sensor entities are created correctly."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Check that all sensor entities are created
    entity_registry = er.async_get(hass)

    # Power sensor
    power_entity = entity_registry.async_get("sensor.zap_zap12345_power")
    assert power_entity is not None
    assert power_entity.unique_id == "ZAP12345_power"

    # Energy import sensor
    energy_import_entity = entity_registry.async_get(
        "sensor.zap_zap12345_energy_import"
    )
    assert energy_import_entity is not None
    assert energy_import_entity.unique_id == "ZAP12345_energy_import"

    # Energy export sensor
    energy_export_entity = entity_registry.async_get(
        "sensor.zap_zap12345_energy_export"
    )
    assert energy_export_entity is not None
    assert energy_export_entity.unique_id == "ZAP12345_energy_export"

    # Battery SOC sensor
    battery_soc_entity = entity_registry.async_get("sensor.zap_zap12345_battery_soc")
    assert battery_soc_entity is not None
    assert battery_soc_entity.unique_id == "ZAP12345_battery_soc"

    # Battery power sensor
    battery_power_entity = entity_registry.async_get(
        "sensor.zap_zap12345_battery_power"
    )
    assert battery_power_entity is not None
    assert battery_power_entity.unique_id == "ZAP12345_battery_power"

    # Temperature sensor
    temperature_entity = entity_registry.async_get("sensor.zap_zap12345_temperature")
    assert temperature_entity is not None
    assert temperature_entity.unique_id == "ZAP12345_temperature"

    # Signal strength sensor
    signal_entity = entity_registry.async_get("sensor.zap_zap12345_signal_strength")
    assert signal_entity is not None
    assert signal_entity.unique_id == "ZAP12345_signal_strength"


async def test_power_sensor_state(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test power sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_power")
    assert state is not None
    assert state.state == "1500.0"
    assert state.attributes["device_class"] == SensorDeviceClass.POWER
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == UnitOfPower.WATT


async def test_energy_import_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test energy import sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_energy_import")
    assert state is not None
    assert state.state == "15000.0"
    assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert state.attributes["unit_of_measurement"] == UnitOfEnergy.WATT_HOUR


async def test_energy_export_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test energy export sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_energy_export")
    assert state is not None
    assert state.state == "25000.0"
    assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert state.attributes["unit_of_measurement"] == UnitOfEnergy.WATT_HOUR


async def test_battery_soc_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test battery state of charge sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_battery_soc")
    assert state is not None
    assert state.state == "85.0"
    assert state.attributes["device_class"] == SensorDeviceClass.BATTERY
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == PERCENTAGE


async def test_battery_power_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test battery power sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_battery_power")
    assert state is not None
    assert state.state == "-500.0"
    assert state.attributes["device_class"] == SensorDeviceClass.POWER
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == UnitOfPower.WATT


async def test_temperature_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test temperature sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_temperature")
    assert state is not None
    assert state.state == "45.5"
    assert state.attributes["device_class"] == SensorDeviceClass.TEMPERATURE
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS


async def test_signal_strength_sensor_state(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test signal strength sensor state and attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_signal_strength")
    assert state is not None
    assert state.state == "-67.0"
    assert state.attributes["device_class"] == SensorDeviceClass.SIGNAL_STRENGTH
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert (
        state.attributes["unit_of_measurement"]
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )


async def test_sensor_extra_attributes(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors include extra state attributes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zap_zap12345_power")
    assert state is not None
    assert state.attributes["connection_status"] == "Connected"
    assert state.attributes["last_harvest"] == "2026-01-07T12:00:00Z"
    assert state.attributes["rated_power"] == 5000.0
    assert state.attributes["capacity"] == 10000.0


async def test_sensor_availability_on_success(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors are available when data is present."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # All sensors should be available
    power_state = hass.states.get("sensor.zap_zap12345_power")
    assert power_state.state != "unavailable"

    energy_state = hass.states.get("sensor.zap_zap12345_energy_import")
    assert energy_state.state != "unavailable"

    battery_state = hass.states.get("sensor.zap_zap12345_battery_soc")
    assert battery_state.state != "unavailable"


async def test_sensor_unavailable_on_missing_data(
    hass: HomeAssistant, mock_config_entry
):
    """Test sensors become unavailable when data is missing."""
    from unittest.mock import AsyncMock, MagicMock

    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP12345",
                "name": "Zap Device",
            }
        ]
    )
    # Return empty data
    mock_api.get_device_data = AsyncMock(return_value={})
    mock_api.get_device_ders = AsyncMock(return_value={})

    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=mock_api):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Sensors without data should be unavailable
    power_state = hass.states.get("sensor.zap_zap12345_power")
    assert power_state.state == "unavailable"

    energy_state = hass.states.get("sensor.zap_zap12345_energy_import")
    assert energy_state.state == "unavailable"


async def test_sensor_update(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test sensor state updates when coordinator refreshes."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Initial state
    state = hass.states.get("sensor.zap_zap12345_power")
    assert state.state == "1500.0"

    # Update mock data
    from unittest.mock import AsyncMock

    mock_zap_api.get_device_data = AsyncMock(
        return_value={
            "power": 2500.0,
            "total_generation": 26000.0,
            "total_consumption": 16000.0,
        }
    )

    # Trigger coordinator update
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinators"][
        "ZAP12345"
    ]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Check updated state
    state = hass.states.get("sensor.zap_zap12345_power")
    assert state.state == "2500.0"

    energy_state = hass.states.get("sensor.zap_zap12345_energy_export")
    assert energy_state.state == "26000.0"


async def test_sensor_device_info(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors have correct device info."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    power_entity = entity_registry.async_get("sensor.zap_zap12345_power")

    assert power_entity is not None
    assert power_entity.device_id is not None


async def test_sensor_has_entity_name(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors use has_entity_name pattern."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Entity IDs should be in format: sensor.{device_name}_{entity_name}
    power_state = hass.states.get("sensor.zap_zap12345_power")
    assert power_state is not None


async def test_signal_strength_disabled_by_default(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test signal strength sensor is disabled by default."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    signal_entity = entity_registry.async_get("sensor.zap_zap12345_signal_strength")

    assert signal_entity is not None
    assert signal_entity.disabled_by is not None


async def test_multiple_devices(hass: HomeAssistant, mock_config_entry):
    """Test sensors are created for multiple devices."""
    from unittest.mock import AsyncMock, MagicMock

    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP11111",
                "name": "Device 1",
            },
            {
                "serial_number": "ZAP22222",
                "name": "Device 2",
            },
        ]
    )
    mock_api.get_device_data = AsyncMock(
        return_value={
            "power": 1500.0,
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=mock_api):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Check entities for both devices
    device1_power = hass.states.get("sensor.device_1_power")
    device2_power = hass.states.get("sensor.device_2_power")

    assert device1_power is not None
    assert device2_power is not None


async def test_sensor_suggested_display_precision(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test sensors have correct suggested display precision."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Power sensor - 0 decimal places
    power_state = hass.states.get("sensor.zap_zap12345_power")
    assert power_state.attributes.get("suggested_display_precision") == 0

    # Energy sensor - 2 decimal places
    energy_state = hass.states.get("sensor.zap_zap12345_energy_import")
    assert energy_state.attributes.get("suggested_display_precision") == 2

    # Temperature sensor - 1 decimal place
    temp_state = hass.states.get("sensor.zap_zap12345_temperature")
    assert temp_state.attributes.get("suggested_display_precision") == 1


async def test_sensor_with_session_state_attribute(
    hass: HomeAssistant, mock_config_entry
):
    """Test battery sensors include session_state attribute."""
    from unittest.mock import AsyncMock, MagicMock

    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP12345",
                "name": "Zap Device",
            }
        ]
    )
    mock_api.get_device_data = AsyncMock(
        return_value={
            "power": 1500.0,
            "battery_power": -500.0,
            "state_of_charge": 85.0,
            "session_state": "charging",
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=mock_api):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    battery_state = hass.states.get("sensor.zap_zap12345_battery_power")
    assert battery_state is not None
    assert battery_state.attributes.get("session_state") == "charging"


async def test_sensor_none_value_handling(hass: HomeAssistant, mock_config_entry):
    """Test sensors handle None values correctly."""
    from unittest.mock import AsyncMock, MagicMock

    mock_api = MagicMock()
    mock_api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP12345",
                "name": "Zap Device",
            }
        ]
    )
    # Return data with explicit None values
    mock_api.get_device_data = AsyncMock(
        return_value={
            "power": 1500.0,
            "total_generation": None,  # Explicit None
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.sourceful_zap.ZapApiClient", return_value=mock_api):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    power_state = hass.states.get("sensor.zap_zap12345_power")
    assert power_state.state == "1500.0"

    # Energy export should be unavailable due to None value
    energy_state = hass.states.get("sensor.zap_zap12345_energy_export")
    assert energy_state.state == "unavailable"
