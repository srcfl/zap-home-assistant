"""Test Zap Energy API client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.sourceful_zap.api import (
    ZapApiClient,
    ZapApiError,
    ZapConnectionError,
)


async def test_init(hass):
    """Test API client initialization."""
    api = ZapApiClient("192.168.1.100", hass)

    assert api.host == "192.168.1.100"
    assert api.base_url == "http://192.168.1.100"
    assert api._session is not None


async def test_init_strips_trailing_slash(hass):
    """Test API client strips trailing slash from host."""
    api = ZapApiClient("192.168.1.100/", hass)

    assert api.host == "192.168.1.100"
    assert api.base_url == "http://192.168.1.100"


async def test_get_devices_success(hass):
    """Test successful device list retrieval."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP12345",
                "name": "Zap Device",
                "manufacturer": "Sourceful Energy",
                "model": "Zap Smart Meter",
                "connected": True,
                "last_harvest": "2026-01-07T12:00:00Z",
            }
        ]
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0]["serial_number"] == "ZAP12345"
    assert devices[0]["name"] == "Zap Device"
    assert devices[0]["manufacturer"] == "Sourceful Energy"
    assert devices[0]["model"] == "Zap Smart Meter"
    assert devices[0]["connection_status"] is True
    assert devices[0]["last_harvest"] == "2026-01-07T12:00:00Z"


async def test_get_devices_no_serial_number(hass):
    """Test get_devices filters out devices without serial numbers."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value=[
            {"serial_number": "ZAP12345", "name": "Valid Device"},
            {"name": "Invalid Device"},  # No serial number
            {"serial_number": "ZAP67890", "name": "Another Valid Device"},
        ]
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        devices = await api.get_devices()

    assert len(devices) == 2
    assert devices[0]["serial_number"] == "ZAP12345"
    assert devices[1]["serial_number"] == "ZAP67890"


async def test_get_devices_not_list(hass):
    """Test get_devices returns empty list when response is not a list."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value={"error": "Invalid response"})
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        devices = await api.get_devices()

    assert devices == []


async def test_get_device_data_success(hass):
    """Test successful device data retrieval."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "power": 1500.0,
            "total_generation": 25000.0,
            "total_consumption": 15000.0,
            "state_of_charge": 85.0,
            "battery_power": -500.0,
            "temperature": 45.5,
            "rssi": -67.0,
        }
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        data = await api.get_device_data("ZAP12345")

    assert data["power"] == 1500.0
    assert data["total_generation"] == 25000.0
    assert data["total_consumption"] == 15000.0
    assert data["state_of_charge"] == 85.0


async def test_get_device_ders_success(hass):
    """Test successful device DER metadata retrieval."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "rated_power": 5000.0,
            "capacity": 10000.0,
        }
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        data = await api.get_device_ders("ZAP12345")

    assert data["rated_power"] == 5000.0
    assert data["capacity"] == 10000.0


async def test_get_system_info_success(hass):
    """Test successful system info retrieval."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "firmware_version": "1.2.3",
            "uptime": 123456,
            "temperature": 45.5,
        }
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        data = await api.get_system_info()

    assert data["firmware_version"] == "1.2.3"
    assert data["uptime"] == 123456
    assert data["temperature"] == 45.5


async def test_request_timeout(hass):
    """Test request timeout error handling."""
    api = ZapApiClient("192.168.1.100", hass)

    with patch.object(
        api._session, "request", side_effect=asyncio.TimeoutError()
    ):
        with pytest.raises(ZapConnectionError) as exc_info:
            await api.get_devices()

    assert "Timeout connecting to" in str(exc_info.value)


async def test_request_client_error(hass):
    """Test request client error handling."""
    api = ZapApiClient("192.168.1.100", hass)

    with patch.object(
        api._session, "request", side_effect=aiohttp.ClientError("Connection failed")
    ):
        with pytest.raises(ZapConnectionError) as exc_info:
            await api.get_devices()

    assert "Failed to connect to" in str(exc_info.value)


async def test_request_http_error(hass):
    """Test request HTTP error handling."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=404,
            message="Not Found",
        )
    )

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        with pytest.raises(ZapConnectionError) as exc_info:
            await api.get_devices()

    assert "Failed to connect to" in str(exc_info.value)


async def test_request_500_error(hass):
    """Test request handles 500 server error."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Internal Server Error",
        )
    )

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        with pytest.raises(ZapConnectionError):
            await api.get_device_data("ZAP12345")


async def test_test_connection_success(hass):
    """Test successful connection test."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value=[{"serial_number": "ZAP12345", "name": "Zap Device"}]
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        result = await api.test_connection()

    assert result is True


async def test_test_connection_failure(hass):
    """Test connection test with failure."""
    api = ZapApiClient("192.168.1.100", hass)

    with patch.object(
        api._session, "request", side_effect=aiohttp.ClientError("Connection failed")
    ):
        result = await api.test_connection()

    assert result is False


async def test_test_connection_timeout(hass):
    """Test connection test with timeout."""
    api = ZapApiClient("192.168.1.100", hass)

    with patch.object(api._session, "request", side_effect=asyncio.TimeoutError()):
        result = await api.test_connection()

    assert result is False


async def test_request_includes_timeout(hass):
    """Test that requests include timeout configuration."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=[])
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ) as mock_request:
        await api.get_devices()

    # Verify timeout was passed to request
    call_args = mock_request.call_args
    assert "timeout" in call_args.kwargs
    assert isinstance(call_args.kwargs["timeout"], aiohttp.ClientTimeout)


async def test_get_devices_empty_list(hass):
    """Test get_devices with empty response."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=[])
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        devices = await api.get_devices()

    assert devices == []


async def test_get_device_data_with_special_serial(hass):
    """Test get_device_data with special characters in serial number."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value={"power": 1500.0})
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ) as mock_request:
        await api.get_device_data("ZAP-12345")

    # Verify correct endpoint was called
    call_args = mock_request.call_args
    assert "/api/devices/ZAP-12345/data/json" in call_args.args[1]


async def test_api_base_exception(hass):
    """Test ZapApiError base exception can be raised."""
    with pytest.raises(ZapApiError):
        raise ZapApiError("Test error")


async def test_connection_error_inheritance(hass):
    """Test ZapConnectionError inherits from ZapApiError."""
    with pytest.raises(ZapApiError):
        raise ZapConnectionError("Connection error")


async def test_get_devices_with_minimal_device_data(hass):
    """Test get_devices with minimal device data."""
    api = ZapApiClient("192.168.1.100", hass)

    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value=[
            {
                "serial_number": "ZAP12345",
                # Only serial number, no other fields
            }
        ]
    )
    mock_response.raise_for_status = MagicMock()

    with patch.object(
        api._session, "request", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    ):
        devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0]["serial_number"] == "ZAP12345"
    assert devices[0]["name"] is None
    assert devices[0]["manufacturer"] is None
    assert devices[0]["model"] is None
