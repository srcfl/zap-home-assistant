"""Extended coordinator tests for battery details, meter phases, and edge cases."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.sourceful_zap.coordinator import ZapDataUpdateCoordinator


async def test_battery_charge_discharge_totals(hass):
    """Test coordinator extracts battery charge/discharge totals."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "W": -1040,
                "total_charge_Wh": 5261000,
                "total_discharge_Wh": 4389000,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="BAT001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["battery_charge_total"] == 5261000
    assert coordinator.data["battery_discharge_total"] == 4389000


async def test_battery_limits(hass):
    """Test coordinator extracts battery power limits."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "W": 0,
                "upper_limit_W": 10000,
                "lower_limit_W": -10000,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="BAT001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["battery_upper_limit"] == 10000
    assert coordinator.data["battery_lower_limit"] == -10000


async def test_battery_temperature(hass):
    """Test coordinator extracts battery temperature."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "W": 0,
                "heatsink_C": 28.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="BAT001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["battery_temperature"] == 28.0
    # Battery temp also used as fallback for general temperature when no PV
    assert coordinator.data["temperature"] == 28.0


async def test_battery_temp_does_not_override_pv_temp(hass):
    """Test PV temperature takes priority over battery temperature."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 1000,
                "heatsink_C": 45.0,
            },
            "battery": {
                "type": "battery",
                "W": 0,
                "heatsink_C": 28.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="DEV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["temperature"] == 45.0  # PV temp
    assert coordinator.data["battery_temperature"] == 28.0


async def test_meter_phase_measurements(hass):
    """Test coordinator extracts per-phase meter measurements."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "meter": {
                "type": "meter",
                "W": -3,
                "L1_V": 229.6,
                "L1_A": 2.1,
                "L1_W": 418,
                "L2_V": 229.8,
                "L2_A": 1.0,
                "L2_W": -218,
                "L3_V": 227.3,
                "L3_A": 0.9,
                "L3_W": -203,
                "total_export_Wh": 9670222,
                "total_import_Wh": 19129172,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="P1001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["l1_voltage"] == 229.6
    assert coordinator.data["l1_current"] == 2.1
    assert coordinator.data["l1_power"] == 418
    assert coordinator.data["l2_voltage"] == 229.8
    assert coordinator.data["l2_current"] == 1.0
    assert coordinator.data["l2_power"] == -218
    assert coordinator.data["l3_voltage"] == 227.3
    assert coordinator.data["l3_current"] == 0.9
    assert coordinator.data["l3_power"] == -203
    assert coordinator.data["energy_import"] == 19129172
    assert coordinator.data["energy_export"] == 9670222


async def test_meter_grid_frequency(hass):
    """Test coordinator extracts grid frequency."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "meter": {
                "type": "meter",
                "W": 0,
                "Hz": 50.02,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="M001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["grid_frequency"] == 50.02


async def test_meter_grid_frequency_out_of_range(hass):
    """Test coordinator filters out-of-range grid frequency."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "meter": {
                "type": "meter",
                "Hz": 0.0,  # Invalid
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="M001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert "grid_frequency" not in coordinator.data


async def test_meter_ignored_when_pv_present(hass):
    """Test meter data is ignored when PV data is also present."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 2500,
                "total_generation_Wh": 50000,
            },
            "meter": {
                "type": "meter",
                "W": -800,
                "total_import_Wh": 15000,
                "total_export_Wh": 20000,
                "L1_V": 230.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="SE001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    # PV data should be used
    assert coordinator.data["energy_production"] == 50000
    # Meter data should be ignored (PV device with embedded meter)
    assert "energy_import" not in coordinator.data
    assert "energy_export" not in coordinator.data
    assert "l1_voltage" not in coordinator.data


async def test_pv_power_sign_flip(hass):
    """Test PV power is sign-flipped (API negative = production positive)."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": -3000,  # API uses negative for production
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="PV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["power"] == 3000  # Flipped sign


async def test_pv_limits(hass):
    """Test coordinator extracts PV power limits."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 1000,
                "upper_limit_W": 8000,
                "lower_limit_W": 0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="PV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["pv_upper_limit"] == 8000
    assert coordinator.data["pv_lower_limit"] == 0


async def test_device_makes(hass):
    """Test coordinator extracts device make/manufacturer info."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {"type": "pv", "make": "solaredge", "W": 0},
            "battery": {"type": "battery", "make": "pixii", "W": 0},
            "meter": {"type": "meter", "make": "sagemcom"},
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="DEV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["pv_make"] == "solaredge"
    assert coordinator.data["battery_make"] == "pixii"
    # Meter make not extracted when PV is present (meter section skipped)


async def test_meter_make_standalone(hass):
    """Test meter make is extracted for standalone meter."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "meter": {"type": "meter", "make": "sagemcom", "W": 0},
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="M001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["meter_make"] == "sagemcom"


async def test_combined_power_pv_and_battery(hass):
    """Test power is aggregated from PV and battery."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {"type": "pv", "W": -3000},  # Producing 3000W
            "battery": {"type": "battery", "W": -500},  # Charging 500W
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="DEV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    # PV flipped: 3000, battery: -500, total: 2500
    assert coordinator.data["power"] == 2500


async def test_battery_voltage_out_of_range(hass):
    """Test battery voltage out of range is filtered."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "W": 0,
                "V": 1500,  # Out of range (max 1000)
                "A": -600,  # Out of range (max 500)
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="BAT001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert "battery_voltage" not in coordinator.data
    assert "battery_current" not in coordinator.data


async def test_pv_rated_power_from_data(hass):
    """Test rated power extracted from PV data directly."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 0,
                "rated_power_W": 8000,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="PV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["rated_power"] == 8000


async def test_der_disabled_not_used_for_rated_power(hass):
    """Test disabled DERs don't contribute rated power."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(return_value={})
    mock_api.get_device_ders = AsyncMock(
        return_value={
            "ders": [
                {"type": "pv", "enabled": False, "rated_power": 5000},
                {"type": "battery", "enabled": True, "rated_power": 3000, "capacity": 10000},
            ]
        }
    )

    coordinator = ZapDataUpdateCoordinator(
        hass=hass, api=mock_api, serial_number="DEV001", polling_interval=10,
    )
    await coordinator.async_config_entry_first_refresh()

    # Disabled PV rated_power should be skipped, battery rated_power used
    assert coordinator.data["rated_power"] == 3000
    assert coordinator.data["capacity"] == 10000
