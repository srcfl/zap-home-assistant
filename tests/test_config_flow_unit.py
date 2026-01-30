"""Unit tests for config flow validate_input and helpers."""

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.sourceful_zap.api import ZapConnectionError

# Ensure the zeroconf module exists for import
# (older HA versions don't have homeassistant.helpers.service_info.zeroconf)
if "homeassistant.helpers.service_info" not in sys.modules:
    mod = ModuleType("homeassistant.helpers.service_info")
    sys.modules["homeassistant.helpers.service_info"] = mod
if "homeassistant.helpers.service_info.zeroconf" not in sys.modules:
    mod = ModuleType("homeassistant.helpers.service_info.zeroconf")
    mod.ZeroconfServiceInfo = MagicMock  # type: ignore[attr-defined]
    sys.modules["homeassistant.helpers.service_info.zeroconf"] = mod

from custom_components.sourceful_zap.config_flow import validate_input


async def test_validate_input_success(hass):
    """Test validate_input with successful connection."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(
        return_value={
            "zap": {"deviceId": "zap-gateway-12345"},
        }
    )
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "INV001"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "zap-gateway-12345"
    assert "Sourceful Zap" in result["title"]


async def test_validate_input_connection_failed(hass):
    """Test validate_input when connection fails."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=False)
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        with pytest.raises(ZapConnectionError):
            await validate_input(hass, {"host": "192.168.1.100"})


async def test_validate_input_no_devices(hass):
    """Test validate_input when no devices found."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(
        return_value={"zap": {"deviceId": "zap-123"}}
    )
    mock_api.get_devices = AsyncMock(return_value=[])
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        with pytest.raises(ZapConnectionError, match="No devices found"):
            await validate_input(hass, {"host": "192.168.1.100"})


async def test_validate_input_serial_from_sn_field(hass):
    """Test validate_input extracts serial from zap.sn field."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(
        return_value={"zap": {"sn": "SERIAL123"}}
    )
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "INV001"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "SERIAL123"


async def test_validate_input_serial_from_top_level(hass):
    """Test validate_input extracts serial from top-level sn field."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(
        return_value={"sn": "TOP_SERIAL"}
    )
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "INV001"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "TOP_SERIAL"


async def test_validate_input_serial_fallback_to_device(hass):
    """Test validate_input falls back to first device serial."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(
        return_value={"zap": {"firmwareVersion": "1.0"}}
    )
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "DEV_SERIAL"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "DEV_SERIAL"


async def test_validate_input_empty_system_info(hass):
    """Test validate_input with empty system info."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(return_value={})
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "FALLBACK"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "FALLBACK"


async def test_validate_input_none_system_info(hass):
    """Test validate_input with None system info."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(return_value=None)
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "FALLBACK"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "FALLBACK"


async def test_validate_input_zap_not_dict(hass):
    """Test validate_input when zap field is not a dict."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(
        return_value={"zap": "some_version_string"}
    )
    mock_api.get_devices = AsyncMock(
        return_value=[{"serial_number": "DEV001"}]
    )
    mock_api.base_url = "http://192.168.1.100/api"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await validate_input(hass, {"host": "192.168.1.100"})

    assert result["serial_number"] == "DEV001"
