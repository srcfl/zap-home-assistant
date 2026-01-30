"""Test ZapGatewayCoordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sourceful_zap.api import ZapApiError
from custom_components.sourceful_zap.coordinator import ZapGatewayCoordinator


async def test_gateway_coordinator_init(hass):
    """Test gateway coordinator initialization."""
    mock_api = MagicMock()
    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)

    assert coordinator.api == mock_api
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator.name == "sourceful_zap_gateway"


async def test_gateway_coordinator_full_data(hass):
    """Test gateway coordinator parses full system info."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "time_utc_sec": 1767797371,
            "uptime_seconds": 16975,
            "temperature_celsius": 42,
            "memory_kb": {
                "total": 252.633,
                "free": 67.5781,
                "percent_used": 73.2505,
            },
            "zap": {
                "deviceId": "zap-gateway-12345",
                "firmwareVersion": "1.8.50",
                "network": {
                    "localIP": "192.168.1.100",
                    "ssid": "MyNetwork",
                    "rssi": -47,
                    "wifiStatus": "connected",
                },
            },
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["uptime_seconds"] == 16975
    assert coordinator.data["gateway_temperature"] == 42.0
    assert coordinator.data["memory_percent"] == 73.2505
    assert coordinator.data["memory_free"] == 67.5781
    assert coordinator.data["firmware_version"] == "1.8.50"
    assert coordinator.data["wifi_ssid"] == "MyNetwork"
    assert coordinator.data["wifi_status"] == "connected"
    assert coordinator.data["signal_strength"] == -47.0


async def test_gateway_coordinator_empty_response(hass):
    """Test gateway coordinator handles empty system info."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(return_value={})

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data == {}


async def test_gateway_coordinator_none_response(hass):
    """Test gateway coordinator handles None system info."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(return_value=None)

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data == {}


async def test_gateway_coordinator_api_error(hass):
    """Test gateway coordinator handles API error."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(side_effect=ZapApiError("Failed"))

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)

    with pytest.raises(Exception):
        await coordinator.async_config_entry_first_refresh()

    assert not coordinator.last_update_success


async def test_gateway_coordinator_invalid_temperature(hass):
    """Test gateway coordinator filters invalid temperature."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "temperature_celsius": 200,  # Out of range
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert "gateway_temperature" not in coordinator.data


async def test_gateway_coordinator_invalid_rssi(hass):
    """Test gateway coordinator filters invalid RSSI."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "zap": {
                "network": {
                    "rssi": 10,  # Positive RSSI is invalid
                },
            },
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert "signal_strength" not in coordinator.data


async def test_gateway_coordinator_invalid_memory_percent(hass):
    """Test gateway coordinator filters invalid memory percent."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "memory_kb": {
                "percent_used": 150,  # Over 100%
            },
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert "memory_percent" not in coordinator.data


async def test_gateway_coordinator_invalid_uptime_type(hass):
    """Test gateway coordinator handles non-numeric uptime."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "uptime_seconds": "not_a_number",
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert "uptime_seconds" not in coordinator.data


async def test_gateway_coordinator_memory_not_dict(hass):
    """Test gateway coordinator handles non-dict memory."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "memory_kb": "invalid",
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert "memory_percent" not in coordinator.data
    assert "memory_free" not in coordinator.data


async def test_gateway_coordinator_zap_not_dict(hass):
    """Test gateway coordinator handles non-dict zap info."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "zap": "version_string",
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert "firmware_version" not in coordinator.data


async def test_gateway_coordinator_partial_network(hass):
    """Test gateway coordinator with partial network info."""
    mock_api = MagicMock()
    mock_api.get_system_info = AsyncMock(
        return_value={
            "zap": {
                "firmwareVersion": "1.8.50",
                # No network key
            },
        }
    )

    coordinator = ZapGatewayCoordinator(hass=hass, api=mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["firmware_version"] == "1.8.50"
    assert "signal_strength" not in coordinator.data
    assert "wifi_ssid" not in coordinator.data
