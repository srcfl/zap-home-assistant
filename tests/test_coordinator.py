"""Test Zap Energy data update coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sourceful_zap.api import ZapApiError
from custom_components.sourceful_zap.coordinator import ZapDataUpdateCoordinator


async def test_coordinator_init(hass, mock_zap_api):
    """Test coordinator initialization."""
    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_zap_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    assert coordinator.api == mock_zap_api
    assert coordinator.serial_number == "ZAP12345"
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator.name == "sourceful_zap_ZAP12345"


async def test_coordinator_update_success(hass, mock_zap_api):
    """Test successful data update."""
    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_zap_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert coordinator.data["serial_number"] == "ZAP12345"
    # Power is sum of PV (1500) + meter (0) + battery (-500) = 1000
    assert coordinator.data["power"] == 1000.0
    assert coordinator.data["energy_import"] == 15000.0
    assert coordinator.data["energy_export"] == 25000.0
    assert coordinator.data["energy_production"] == 25000.0
    assert coordinator.data["battery_soc"] == 85.0
    assert coordinator.data["battery_power"] == -500.0
    assert coordinator.data["temperature"] == 45.5


async def test_coordinator_update_with_ders_data(hass, mock_zap_api):
    """Test data update includes DER metadata."""
    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_zap_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["rated_power"] == 5000.0
    assert coordinator.data["capacity"] == 10000.0


async def test_coordinator_update_pv_only(hass):
    """Test data update with PV only device."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 2500.0,
                "total_generation_Wh": 50000.0,
                "heatsink_C": 42.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["power"] == 2500.0
    assert coordinator.data["energy_production"] == 50000.0
    assert coordinator.data["temperature"] == 42.0


async def test_coordinator_update_failure(hass):
    """Test data update failure handling."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(side_effect=ZapApiError("API error"))
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator.async_config_entry_first_refresh()

    assert "Error fetching data for ZAP12345" in str(exc_info.value)


async def test_coordinator_partial_data(hass):
    """Test coordinator handles partial data correctly."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 1500.0,
                # Missing energy and other data
            }
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["serial_number"] == "ZAP12345"
    assert coordinator.data["power"] == 1500.0
    assert "energy_import" not in coordinator.data
    assert "energy_export" not in coordinator.data
    assert "battery_soc" not in coordinator.data


async def test_coordinator_energy_metrics(hass):
    """Test coordinator extracts energy metrics correctly."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "total_generation_Wh": 50000.0,
            },
            "meter": {
                "type": "meter",
                "total_import_Wh": 30000.0,
                "total_export_Wh": 20000.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["energy_production"] == 50000.0
    assert coordinator.data["energy_import"] == 30000.0
    assert coordinator.data["energy_export"] == 20000.0


async def test_coordinator_battery_metrics(hass):
    """Test coordinator extracts battery metrics correctly."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "W": 1200.0,
                "SoC_nom_fract": 0.755,
                "V": 48.5,
                "A": 24.7,
            }
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["battery_soc"] == 75.5
    assert coordinator.data["battery_power"] == 1200.0
    assert coordinator.data["battery_voltage"] == 48.5
    assert coordinator.data["battery_current"] == 24.7


async def test_coordinator_temperature_metrics(hass):
    """Test coordinator extracts temperature from PV heatsink."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "heatsink_C": 52.3,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["temperature"] == 52.3


async def test_coordinator_der_metadata(hass):
    """Test coordinator extracts DER metadata correctly."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(return_value={})
    mock_api.get_device_ders = AsyncMock(
        return_value={
            "ders": [
                {"type": "pv", "enabled": True, "rated_power": 7500.0},
                {"type": "battery", "enabled": True, "capacity": 15000.0},
            ]
        }
    )

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["rated_power"] == 7500.0
    assert coordinator.data["capacity"] == 15000.0


async def test_coordinator_custom_polling_interval(hass, mock_zap_api):
    """Test coordinator with custom polling interval."""
    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_zap_api,
        serial_number="ZAP12345",
        polling_interval=60,
    )

    assert coordinator.update_interval == timedelta(seconds=60)


async def test_coordinator_multiple_updates(hass, mock_zap_api):
    """Test coordinator handles multiple update cycles."""
    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_zap_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    # First update
    await coordinator.async_config_entry_first_refresh()
    first_power = coordinator.data["power"]

    # Change mock data
    mock_zap_api.get_device_data.return_value = {
        "pv": {
            "type": "pv",
            "W": 2000.0,
            "total_generation_Wh": 26000.0,
        },
        "meter": {
            "type": "meter",
            "total_export_Wh": 22000.0,
        },
    }

    # Second update
    await coordinator.async_refresh()
    second_data = coordinator.data

    assert first_power == 1000.0  # 1500 + 0 + (-500)
    assert second_data["power"] == 2000.0
    assert second_data["energy_export"] == 22000.0


async def test_coordinator_type_conversion(hass):
    """Test coordinator converts string values to floats."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": "1500.5",
                "total_generation_Wh": "25000.7",
            },
            "battery": {
                "type": "battery",
                "SoC_nom_fract": "0.853",
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(
        return_value={
            "ders": [
                {"type": "pv", "enabled": True, "rated_power": "5000.0"},
            ]
        }
    )

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert isinstance(coordinator.data["power"], float)
    assert coordinator.data["power"] == 1500.5
    assert isinstance(coordinator.data["energy_production"], float)
    assert coordinator.data["energy_production"] == 25000.7
    assert isinstance(coordinator.data["battery_soc"], float)
    assert coordinator.data["battery_soc"] == 85.3
    assert isinstance(coordinator.data["rated_power"], float)
    assert coordinator.data["rated_power"] == 5000.0


async def test_coordinator_empty_device_data(hass):
    """Test coordinator handles empty device data."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(return_value={})
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["serial_number"] == "ZAP12345"
    # Only serial number should be present
    assert len([k for k in coordinator.data.keys() if k != "serial_number"]) == 0


async def test_coordinator_negative_battery_power(hass):
    """Test coordinator handles negative battery power (charging)."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "W": -1500.0,  # Negative = charging
            }
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["battery_power"] == -1500.0


async def test_coordinator_zero_values(hass):
    """Test coordinator handles zero values correctly."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 0.0,
                "total_generation_Wh": 0.0,
            },
            "battery": {
                "type": "battery",
                "SoC_nom_fract": 0.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["power"] == 0.0
    assert coordinator.data["energy_production"] == 0.0
    assert coordinator.data["battery_soc"] == 0.0


async def test_coordinator_ders_failure_partial_success(hass):
    """Test coordinator succeeds even if DERs fetch fails."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {"type": "pv", "W": 1500.0},
        }
    )
    mock_api.get_device_ders = AsyncMock(side_effect=ZapApiError("DER fetch failed"))

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    # Should fail because we catch ZapApiError in general
    with pytest.raises(UpdateFailed):
        await coordinator.async_config_entry_first_refresh()


async def test_coordinator_filters_nan_values(hass):
    """Test coordinator filters NaN values from SolarEdge devices."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 1500.0,
                "total_generation_Wh": 50000.0,
            },
            "meter": {
                "type": "meter",
                "W": 0.0,
                "L1_W": float("nan"),  # NaN from SolarEdge
                "L2_W": float("-inf"),  # -Inf from SolarEdge
                "L3_W": float("inf"),   # Inf
                "total_import_Wh": 1000.0,
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    # Valid values should be present
    assert coordinator.data["power"] == 1500.0
    assert coordinator.data["energy_production"] == 50000.0
    assert coordinator.data["energy_import"] == 1000.0

    # NaN/Inf values should be filtered out
    assert "l1_power" not in coordinator.data
    assert "l2_power" not in coordinator.data
    assert "l3_power" not in coordinator.data


async def test_coordinator_filters_modbus_sentinel_values(hass):
    """Test coordinator filters Modbus sentinel values (65535, -32768, etc.)."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 2000.0,
                "total_generation_Wh": 50000.0,
            },
            "meter": {
                "type": "meter",
                "L1_V": -32768,   # Modbus error sentinel
                "L2_V": 65535,    # Modbus "no data" sentinel
                "L3_V": 230.5,    # Valid voltage
                "L3_A": 32768,    # Modbus unsigned error
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    # Sentinel values should be filtered
    assert "l1_voltage" not in coordinator.data
    assert "l2_voltage" not in coordinator.data
    assert "l3_current" not in coordinator.data

    # Valid values should be present
    assert coordinator.data["l3_voltage"] == 230.5


async def test_coordinator_filters_overflow_energy_values(hass):
    """Test coordinator filters overflow energy values near uint32 max."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 1000.0,
                "total_generation_Wh": 50000.0,  # Valid
            },
            "meter": {
                "type": "meter",
                "total_import_Wh": 2922119168,   # Could be valid (~2922 MWh)
                "total_export_Wh": 4294836224,   # Near uint32 max - invalid
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    # Valid generation should be present
    assert coordinator.data["energy_production"] == 50000.0

    # Overflow value near uint32 max should be filtered
    assert "energy_export" not in coordinator.data

    # Value under threshold should be present
    assert coordinator.data["energy_import"] == 2922119168


async def test_coordinator_filters_out_of_range_temperature(hass):
    """Test coordinator filters temperature values outside valid range."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "W": 1000.0,
                "heatsink_C": 200.0,  # Too hot - invalid
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    # Out of range temperature should be filtered
    assert "temperature" not in coordinator.data


async def test_coordinator_filters_out_of_range_voltage(hass):
    """Test coordinator filters voltage values outside valid range."""
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "meter": {
                "type": "meter",
                "L1_V": 600.0,    # Too high - invalid
                "L2_V": -10.0,   # Negative - invalid
                "L3_V": 240.0,   # Valid
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="ZAP12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    # Out of range voltages should be filtered
    assert "l1_voltage" not in coordinator.data
    assert "l2_voltage" not in coordinator.data

    # Valid voltage should be present
    assert coordinator.data["l3_voltage"] == 240.0


async def test_coordinator_solaredge_realistic_data(hass):
    """Test coordinator with realistic SolarEdge data containing invalid values."""
    # This mirrors actual SolarEdge API response with mixed valid/invalid data
    mock_api = MagicMock()
    mock_api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "timestamp": 1768344114810,
                "make": "solaredge",
                "W": 0.0,  # Nighttime - 0 power is valid
                "mppt1_V": 65535,  # Invalid sentinel
                "mppt1_A": 6553500.0,  # Invalid - way too high
                "heatsink_C": 0.0,  # Edge case but valid
                "total_generation_Wh": 50900524,  # ~50.9 MWh - valid
            },
            "meter": {
                "type": "meter",
                "make": "solaredge",
                "W": 0.0,
                "L1_V": -32768,  # Invalid sentinel
                "L1_A": 0.0,
                "L1_W": float("nan"),  # Invalid NaN
                "L2_W": float("-inf"),  # Invalid -Inf
                "total_export_Wh": 4294836224,  # Near uint32 max - invalid
                "total_import_Wh": 100000,  # Valid
            },
        }
    )
    mock_api.get_device_ders = AsyncMock(return_value={})

    coordinator = ZapDataUpdateCoordinator(
        hass=hass,
        api=mock_api,
        serial_number="SE12345",
        polling_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    # Valid values should be extracted
    assert coordinator.data["power"] == 0.0
    assert coordinator.data["energy_production"] == 50900524
    assert coordinator.data["energy_import"] == 100000
    assert coordinator.data["temperature"] == 0.0

    # Invalid values should be filtered
    assert "l1_voltage" not in coordinator.data
    assert "l1_power" not in coordinator.data
    assert "l2_power" not in coordinator.data
    assert "energy_export" not in coordinator.data
