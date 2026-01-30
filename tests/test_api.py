"""Test Zap Energy API client."""

import asyncio

import aiohttp
import pytest
from homeassistant.core import HomeAssistant

from custom_components.sourceful_zap.api import (
    ZapApiClient,
    ZapApiError,
    ZapConnectionError,
)


async def test_init(hass: HomeAssistant):
    """Test API client initialization."""
    api = ZapApiClient("192.168.1.100", hass)

    assert api.host == "192.168.1.100"
    assert api.base_url == "http://192.168.1.100/api"


async def test_init_strips_trailing_slash(hass: HomeAssistant):
    """Test API client strips trailing slash from host."""
    api = ZapApiClient("192.168.1.100/", hass)

    assert api.host == "192.168.1.100"
    assert api.base_url == "http://192.168.1.100/api"


async def test_get_devices_success(hass: HomeAssistant, aioclient_mock):
    """Test successful device list retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json={
            "count": 1,
            "devices": [
                {
                    "sn": "ZAP12345",
                    "profile": "solaredge",
                    "type": "modbus_tcp",
                    "connected": True,
                    "last_harvest": 1761832393075,
                    "ders": [{"type": "pv", "enabled": True}],
                }
            ],
        },
    )

    api = ZapApiClient("192.168.1.100", hass)
    devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0]["serial_number"] == "ZAP12345"
    assert devices[0]["name"] == "Solaredge ZAP12345"
    assert devices[0]["model"] == "solaredge"
    assert devices[0]["connection_status"] is True


async def test_get_devices_legacy_format(hass: HomeAssistant, aioclient_mock):
    """Test get_devices with legacy list format."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json=[
            {
                "serial_number": "ZAP12345",
                "name": "Zap Device",
                "manufacturer": "Sourceful Energy",
                "model": "Zap Smart Meter",
                "connected": True,
            }
        ],
    )

    api = ZapApiClient("192.168.1.100", hass)
    devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0]["serial_number"] == "ZAP12345"


async def test_get_devices_no_serial_number(hass: HomeAssistant, aioclient_mock):
    """Test get_devices filters out devices without serial numbers."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json={
            "count": 3,
            "devices": [
                {"sn": "ZAP12345", "profile": "solaredge"},
                {"profile": "sungrow"},  # No serial number
                {"sn": "ZAP67890", "profile": "pixii"},
            ],
        },
    )

    api = ZapApiClient("192.168.1.100", hass)
    devices = await api.get_devices()

    assert len(devices) == 2
    assert devices[0]["serial_number"] == "ZAP12345"
    assert devices[1]["serial_number"] == "ZAP67890"


async def test_get_devices_not_dict_or_list(hass: HomeAssistant, aioclient_mock):
    """Test get_devices returns empty list when response is not a dict or list."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json="invalid",
    )

    api = ZapApiClient("192.168.1.100", hass)
    devices = await api.get_devices()

    assert devices == []


async def test_get_device_data_success(hass: HomeAssistant, aioclient_mock):
    """Test successful device data retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices/ZAP12345/data/json",
        json={
            "pv": {
                "W": 1500,
                "total_generation_Wh": 25000000,
                "heatsink_C": 45.5,
            },
            "meter": {
                "W": -800,
                "total_import_Wh": 15000000,
                "total_export_Wh": 20000000,
            },
        },
    )

    api = ZapApiClient("192.168.1.100", hass)
    data = await api.get_device_data("ZAP12345")

    assert data["pv"]["W"] == 1500
    assert data["pv"]["total_generation_Wh"] == 25000000
    assert data["meter"]["total_import_Wh"] == 15000000


async def test_get_device_ders_success(hass: HomeAssistant, aioclient_mock):
    """Test successful device DER metadata retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices/ZAP12345/ders",
        json={
            "sn": "ZAP12345",
            "ders": [
                {"type": "pv", "enabled": True, "rated_power": 5000},
                {"type": "battery", "enabled": True, "capacity": 10000},
            ],
        },
    )

    api = ZapApiClient("192.168.1.100", hass)
    data = await api.get_device_ders("ZAP12345")

    assert data["ders"][0]["rated_power"] == 5000
    assert data["ders"][1]["capacity"] == 10000


async def test_get_system_info_success(hass: HomeAssistant, aioclient_mock):
    """Test successful system info retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100/api/system",
        json={
            "uptime_seconds": 123456,
            "temperature_celsius": 45.5,
            "zap": {
                "deviceId": "zap-12345",
                "firmwareVersion": "1.2.3",
            },
        },
    )

    api = ZapApiClient("192.168.1.100", hass)
    data = await api.get_system_info()

    assert data["uptime_seconds"] == 123456
    assert data["temperature_celsius"] == 45.5
    assert data["zap"]["firmwareVersion"] == "1.2.3"


async def test_request_timeout(hass: HomeAssistant, aioclient_mock):
    """Test request timeout error handling."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        exc=asyncio.TimeoutError(),
    )

    api = ZapApiClient("192.168.1.100", hass)
    with pytest.raises(ZapConnectionError) as exc_info:
        await api.get_devices()

    assert "Timeout connecting to" in str(exc_info.value)


async def test_request_client_error(hass: HomeAssistant, aioclient_mock):
    """Test request client error handling."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        exc=aiohttp.ClientError("Connection failed"),
    )

    api = ZapApiClient("192.168.1.100", hass)
    with pytest.raises(ZapConnectionError) as exc_info:
        await api.get_devices()

    assert "Failed to connect to" in str(exc_info.value)


async def test_request_connector_error(hass: HomeAssistant, aioclient_mock):
    """Test request connection refused error handling."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        exc=aiohttp.ClientConnectorError(
            connection_key=None,
            os_error=OSError("Connection refused"),
        ),
    )

    api = ZapApiClient("192.168.1.100", hass)
    with pytest.raises(ZapConnectionError) as exc_info:
        await api.get_devices()

    assert "Cannot reach" in str(exc_info.value)


async def test_request_http_error(hass: HomeAssistant, aioclient_mock):
    """Test request HTTP error handling."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        status=404,
    )

    api = ZapApiClient("192.168.1.100", hass)
    with pytest.raises(ZapConnectionError):
        await api.get_devices()


async def test_request_500_error(hass: HomeAssistant, aioclient_mock):
    """Test request handles 500 server error."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices/ZAP12345/data/json",
        status=500,
    )

    api = ZapApiClient("192.168.1.100", hass)
    with pytest.raises(ZapConnectionError):
        await api.get_device_data("ZAP12345")


async def test_test_connection_success(hass: HomeAssistant, aioclient_mock):
    """Test successful connection test."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json={"count": 1, "devices": [{"sn": "ZAP12345"}]},
    )

    api = ZapApiClient("192.168.1.100", hass)
    result = await api.test_connection()

    assert result is True


async def test_test_connection_failure(hass: HomeAssistant, aioclient_mock):
    """Test connection test with failure."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        exc=aiohttp.ClientError("Connection failed"),
    )

    api = ZapApiClient("192.168.1.100", hass)
    result = await api.test_connection()

    assert result is False


async def test_test_connection_timeout(hass: HomeAssistant, aioclient_mock):
    """Test connection test with timeout."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        exc=asyncio.TimeoutError(),
    )

    api = ZapApiClient("192.168.1.100", hass)
    result = await api.test_connection()

    assert result is False


async def test_get_devices_empty_list(hass: HomeAssistant, aioclient_mock):
    """Test get_devices with empty response."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json={"count": 0, "devices": []},
    )

    api = ZapApiClient("192.168.1.100", hass)
    devices = await api.get_devices()

    assert devices == []


async def test_get_device_data_with_special_serial(hass: HomeAssistant, aioclient_mock):
    """Test get_device_data with special characters in serial number."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices/ZAP-12345/data/json",
        json={"pv": {"W": 1500}},
    )

    api = ZapApiClient("192.168.1.100", hass)
    data = await api.get_device_data("ZAP-12345")

    assert data["pv"]["W"] == 1500


async def test_api_base_exception():
    """Test ZapApiError base exception can be raised."""
    with pytest.raises(ZapApiError):
        raise ZapApiError("Test error")


async def test_connection_error_inheritance():
    """Test ZapConnectionError inherits from ZapApiError."""
    with pytest.raises(ZapApiError):
        raise ZapConnectionError("Connection error")


async def test_get_devices_with_minimal_device_data(hass: HomeAssistant, aioclient_mock):
    """Test get_devices with minimal device data."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json={
            "count": 1,
            "devices": [
                {
                    "sn": "ZAP12345",
                    # Only serial number, no other fields
                }
            ],
        },
    )

    api = ZapApiClient("192.168.1.100", hass)
    devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0]["serial_number"] == "ZAP12345"
    assert devices[0]["model"] == "Zap Smart Meter"


async def test_custom_api_path(hass: HomeAssistant, aioclient_mock):
    """Test API client with custom API path."""
    aioclient_mock.get(
        "http://192.168.1.100/custom/devices",
        json={"count": 0, "devices": []},
    )

    api = ZapApiClient("192.168.1.100", hass, api_path="/custom")
    devices = await api.get_devices()

    assert api.base_url == "http://192.168.1.100/custom"
    assert devices == []


async def test_custom_timeout(hass: HomeAssistant, aioclient_mock):
    """Test API client with custom timeout."""
    aioclient_mock.get(
        "http://192.168.1.100/api/devices",
        json={"count": 0, "devices": []},
    )

    api = ZapApiClient("192.168.1.100", hass, timeout=30)
    await api.get_devices()

    assert api._timeout == 30  # pylint: disable=protected-access
