"""Common fixtures for Zap Energy tests.

Fixture data mirrors real firmware v2.3.15 responses captured live.

Note: Tests require Linux/macOS or WSL to run properly.
Windows is not supported due to pytest-homeassistant-custom-component
compatibility issues with the Windows asyncio ProactorEventLoop.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sourceful_zap.const import CONF_POLLING_INTERVAL, DOMAIN

# GET /api/system response shape from firmware v2.3.15 (camelCase keys).
# deviceId is kept aligned with mock_config_entry's unique_id.
SYSTEM_INFO_CURRENT = {
    "timeUtcSec": 1788076361,
    "uptimeSeconds": 177,
    "temperatureCelsius": 0,
    "backend": "mainnet",
    "memoryKb": {
        "total": 233.836,
        "free": 78,
        "used": 155.836,
        "percentUsed": 66.6433,
        "min": 45.2461,
        "largest": 48,
    },
    "processesAverage": {"last1min": 0, "last5min": 0, "last15min": 0},
    "logging": {"enabled": True, "level": 6},
    "zap": {
        "deviceId": "zap-gateway-12345",
        "platform": "srcful-zap-p1",
        "cpuFreqMHz": 160,
        "flashSizeMB": 0,
        "sdkVersion": "v5.5",
        "firmwareVersion": "2.3.15",
        "network": {
            "wifiMac": "DC:06:75:38:7F:3C",
            "wifiStatus": "connected",
            "wifiConnected": True,
            "localIP": "192.168.1.100",
            "ssid": "MyNetwork",
            "rssi": -84,
            "internetConnected": True,
            "mqttConnected": True,
        },
    },
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations,
):  # pylint: disable=unused-argument
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
    """Return a mock Zap API client for a PV inverter device.

    get_devices returns the normalized form produced by
    ZapApiClient.get_devices; the data/ders/system responses mirror the
    raw firmware payloads.
    """
    api = MagicMock()

    api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "INV001",
                "sn": "INV001",
                "name": "Solaredge INV001",
                "manufacturer": "Sourceful Energy",
                "model": "solaredge",
                "type": "modbus_tcp",
                "profile": "solaredge",
                "connection_status": True,
                "last_harvest": 1788076352635,
                "ders": [{"type": "pv", "enabled": True}],
            }
        ]
    )

    # GET /api/devices/{sn}/data/json - PV device.
    # API convention: negative W means the PV is producing.
    api.get_device_data = AsyncMock(
        return_value={
            "pv": {
                "type": "pv",
                "timestamp": 1788076412694,
                "read_time_ms": 1826,
                "make": "solaredge",
                "W": -2500,
                "rated_power_W": 8000,
                "heatsink_C": 45.5,
                "total_generation_Wh": 50900524,
                "lower_limit_W": 0,
                "upper_limit_W": 8000,
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

    # GET /api/system response (firmware v2.3.15 camelCase shape)
    api.get_system_info = AsyncMock(return_value=dict(SYSTEM_INFO_CURRENT))

    api.test_connection = AsyncMock(return_value=True)
    api.base_url = "http://192.168.1.100/api"

    return api


@pytest.fixture
def mock_zap_api_battery():
    """Return a mock Zap API client for a battery device."""
    api = MagicMock()

    api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "BAT001",
                "sn": "BAT001",
                "name": "Pixii BAT001",
                "manufacturer": "Sourceful Energy",
                "model": "pixii",
                "type": "modbus_tcp",
                "profile": "pixii",
                "connection_status": True,
                "last_harvest": 1788076352635,
                "ders": [{"type": "battery", "enabled": True, "capacity": 10000}],
            }
        ]
    )

    api.get_device_data = AsyncMock(
        return_value={
            "battery": {
                "type": "battery",
                "timestamp": 1788076412694,
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

    api.get_system_info = AsyncMock(return_value=dict(SYSTEM_INFO_CURRENT))

    api.test_connection = AsyncMock(return_value=True)
    api.base_url = "http://192.168.1.100/api"

    return api


@pytest.fixture
def mock_zap_api_p1_meter():
    """Return a mock Zap API client for a P1 meter device.

    Data mirrors a live capture from firmware v2.3.15.
    """
    api = MagicMock()

    api.get_devices = AsyncMock(
        return_value=[
            {
                "serial_number": "p1m-00003c7f387506dc",
                "sn": "p1m-00003c7f387506dc",
                "name": "P1 Uart p1m-00003c7f387506dc",
                "manufacturer": "generic",
                "model": "p1_uart",
                "type": "p1_uart",
                "profile": None,
                "connection_status": True,
                "last_harvest": 1788076352635,
                "ders": [{"type": "meter", "enabled": True}],
            }
        ]
    )

    api.get_device_data = AsyncMock(
        return_value={
            "meter": {
                "type": "meter",
                "timestamp": 1788076412694,
                "read_time_ms": 1,
                "make": "generic",
                "W": 24,
                "L1_V": 231.7,
                "L1_A": 1,
                "L1_W": 119,
                "L2_V": 232.2,
                "L2_A": 0.8,
                "L2_W": 74,
                "L3_V": 233.5,
                "L3_A": -0.7,
                "L3_W": -167,
                "total_export_Wh": 16450102,
                "total_import_Wh": 73447080,
            },
            "version": "v1",
            "format": "p1_uart",
        }
    )

    api.get_device_ders = AsyncMock(
        return_value={
            "sn": "p1m-00003c7f387506dc",
            "ders": [{"type": "meter", "enabled": True}],
        }
    )

    api.get_system_info = AsyncMock(return_value=dict(SYSTEM_INFO_CURRENT))

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
