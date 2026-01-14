"""Common fixtures for Zap Energy tests.

Note: Tests require Linux/macOS or WSL to run properly.
Windows is not supported due to pytest-homeassistant-custom-component
compatibility issues with the Windows asyncio ProactorEventLoop.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sourceful_zap.const import CONF_POLLING_INTERVAL, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_POLLING_INTERVAL: 10,
        },
        unique_id="zap-gateway-12345",
        title="Sourceful Zap zap-gateway-12345",
    )


@pytest.fixture
def mock_zap_api():
    """Return a mock Zap API client with realistic data structure."""
    api = MagicMock()

    # GET /api/devices response
    api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "INV001",
                "name": "SolarEdge Inverter",
                "model": "solaredge",
                "manufacturer": "Sourceful Energy",
                "connection_status": True,
                "last_harvest": "2026-01-07T12:00:00Z",
                "ders": [
                    {"type": "pv", "enabled": True, "rated_power": 8000},
                    {"type": "meter", "enabled": True},
                ],
            }
        ]
    )

    # GET /api/devices/{sn}/data/json response - PV with meter
    api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "timestamp": 1768373017865,
                "read_time_ms": 1826,
                "make": "solaredge",
                "W": 2500,
                "rated_power_W": 8000,
                "mppt1_V": 350.5,
                "mppt1_A": 7.2,
                "mppt2_V": 345.0,
                "mppt2_A": 6.8,
                "heatsink_C": 45.5,
                "total_generation_Wh": 50900524,
                "lower_limit_W": 0,
                "upper_limit_W": 8000,
            },
            "meter": {
                "type": "meter",
                "timestamp": 1768373017865,
                "read_time_ms": 1826,
                "make": "solaredge",
                "W": -1500,
                "Hz": 50.02,
                "L1_V": 230.5,
                "L1_A": 5.2,
                "L1_W": -500,
                "L2_V": 231.0,
                "L2_A": 4.8,
                "L2_W": -500,
                "L3_V": 229.8,
                "L3_A": 5.0,
                "L3_W": -500,
                "total_export_Wh": 35000000,
                "total_import_Wh": 12000000,
            },
            "version": "v0",
            "format": "json",
        }
    )

    # GET /api/devices/{sn}/ders response
    api.get_device_ders = AsyncMock(
        return_value={
            "sn": "INV001",
            "ders": [
                {
                    "type": "pv",
                    "enabled": True,
                    "rated_power": 8000,
                    "installed_power": 7500,
                },
            ],
        }
    )

    # GET /api/system response
    api.get_system_info = AsyncMock(
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
                    "localIP": "192.168.1.248",
                    "ssid": "MyNetwork",
                    "rssi": -47,
                },
            },
        }
    )

    api.test_connection = AsyncMock(return_value=True)
    api.base_url = "http://192.168.1.100/api"

    return api


@pytest.fixture
def mock_zap_api_battery():
    """Return a mock Zap API client for battery device."""
    api = MagicMock()

    api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "BAT001",
                "name": "Pixii Battery",
                "model": "pixii",
                "manufacturer": "Sourceful Energy",
                "connection_status": True,
                "ders": [
                    {"type": "battery", "enabled": True, "capacity": 10000},
                ],
            }
        ]
    )

    api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "timestamp": 1768372960205,
                "read_time_ms": 325,
                "make": "pixii",
                "W": -1040,
                "V": 52.82,
                "A": -21.3,
                "SoC_nom_fract": 0.663,
                "heatsink_C": 28,
                "total_discharge_Wh": 4389000,
                "total_charge_Wh": 5261000,
                "upper_limit_W": 10000,
                "lower_limit_W": -10000,
            },
            "version": "v0",
            "format": "json",
        }
    )

    api.get_device_ders = AsyncMock(
        return_value={
            "sn": "BAT001",
            "ders": [
                {
                    "type": "battery",
                    "enabled": True,
                    "rated_power": 5000,
                    "capacity": 10000,
                },
            ],
        }
    )

    api.get_system_info = AsyncMock(
        return_value={
            "zap": {
                "deviceId": "zap-gateway-12345",
                "firmwareVersion": "1.8.50",
            },
        }
    )

    api.test_connection = AsyncMock(return_value=True)
    api.base_url = "http://192.168.1.100/api"

    return api


@pytest.fixture
def mock_zap_api_p1_meter():
    """Return a mock Zap API client for P1 meter device."""
    api = MagicMock()

    api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "P1METER001",
                "name": "Sagemcom Meter",
                "model": "sagemcom",
                "type": "p1_uart",
                "manufacturer": "Sourceful Energy",
                "connection_status": True,
                "ders": [
                    {"type": "meter", "enabled": True},
                ],
            }
        ]
    )

    api.get_device_data = AsyncMock(
        return_value={
            "meter": {
                "type": "meter",
                "timestamp": 1768373081457,
                "read_time_ms": 1,
                "make": "sagemcom",
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
            "version": "v0",
            "format": "p1_uart",
        }
    )

    api.get_device_ders = AsyncMock(
        return_value={
            "sn": "P1METER001",
            "ders": [
                {"type": "meter", "enabled": True},
            ],
        }
    )

    api.get_system_info = AsyncMock(
        return_value={
            "zap": {
                "deviceId": "zap-gateway-12345",
                "firmwareVersion": "1.8.50",
            },
        }
    )

    api.test_connection = AsyncMock(return_value=True)
    api.base_url = "http://192.168.1.100/api"

    return api


@pytest.fixture
def mock_zap_api_error():
    """Return a mock Zap API client that raises errors."""
    from custom_components.sourceful_zap.api import ZapConnectionError

    api = MagicMock()
    api.get_devices = AsyncMock(side_effect=ZapConnectionError("Connection failed"))
    api.test_connection = AsyncMock(return_value=False)
    return api
