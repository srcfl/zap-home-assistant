"""Test Zap Energy config flow."""

import asyncio
from ipaddress import ip_address
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sourceful_zap.api import ZapConnectionError
from custom_components.sourceful_zap.config_flow import (
    ZapEnergyConfigFlow,
    validate_input,
)
from custom_components.sourceful_zap.const import (
    CONF_POLLING_INTERVAL,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
)


def make_zeroconf_info(
    hostname="zap-gateway.local.", name="zap-gateway._http._tcp.local."
):
    """Build ZeroconfServiceInfo with the current constructor signature."""
    return ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.100"),
        ip_addresses=[ip_address("192.168.1.100")],
        hostname=hostname,
        name=name,
        port=80,
        properties={},
        type="_http._tcp.local.",
    )


async def test_user_flow_shows_menu(hass: HomeAssistant):
    """Test user flow shows menu with manual and scan options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "user"
    assert "manual" in result["menu_options"]
    assert "scan" in result["menu_options"]


async def test_manual_flow_success(hass: HomeAssistant, mock_zap_api):
    """Test successful manual configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select manual entry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sourceful Zap zap-gateway-12345"
    assert result["data"][CONF_HOST] == "192.168.1.100"


async def test_manual_flow_cannot_connect(hass: HomeAssistant):
    """Test manual flow with connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=False)

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_manual_flow_connection_exception(hass: HomeAssistant):
    """Test manual flow with connection exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(
        side_effect=ZapConnectionError("Connection failed")
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_manual_flow_no_devices(hass: HomeAssistant):
    """Test manual flow when no devices found on gateway."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(return_value={"zap": {"deviceId": "zap-123"}})
    mock_api.get_devices = AsyncMock(return_value=[])

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_manual_flow_unexpected_exception(hass: HomeAssistant):
    """Test manual flow with unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(side_effect=Exception("Unexpected error"))

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "unknown"}


async def test_manual_flow_already_configured(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test manual flow aborts when device already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_manual_flow_sanitizes_host(hass: HomeAssistant, mock_zap_api):
    """Test manual flow sanitizes host input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "http://192.168.1.100/",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == "192.168.1.100"


async def test_zeroconf_flow_success(hass: HomeAssistant, mock_zap_api):
    """Test successful zeroconf discovery flow."""
    discovery_info = make_zeroconf_info()

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    assert "name" in result["description_placeholders"]


async def test_zeroconf_flow_cannot_connect(hass: HomeAssistant):
    """Test zeroconf flow aborts when cannot connect."""
    discovery_info = make_zeroconf_info()

    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=False)

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_zeroconf_flow_not_zap_device(hass: HomeAssistant):
    """Test zeroconf flow aborts when device is not a Zap gateway."""
    discovery_info = make_zeroconf_info(
        hostname="other-device.local.",
        name="other-device._http._tcp.local.",
    )

    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_system_info = AsyncMock(return_value={"other": "data"})

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_zeroconf_flow_already_configured(hass: HomeAssistant, mock_zap_api):
    """Test zeroconf flow aborts when device already configured.

    The zeroconf flow uses the first device's serial number as unique id
    (unlike the manual flow, which uses the gateway serial), so the
    existing entry must carry the device serial.
    """
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        unique_id="INV001",
        title="Solaredge INV001",
    )
    existing_entry.add_to_hass(hass)

    discovery_info = make_zeroconf_info()

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_confirm_step(hass: HomeAssistant, mock_zap_api):
    """Test zeroconf confirmation step creates entry."""
    discovery_info = make_zeroconf_info()

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zeroconf_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.1.100"}


async def test_options_flow(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test options flow for updating polling interval."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_POLLING_INTERVAL: 60},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_POLLING_INTERVAL: 60}


async def test_options_flow_default_values(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test options flow shows default values."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    schema_keys = result["data_schema"].schema
    assert CONF_POLLING_INTERVAL in str(schema_keys)


async def test_options_flow_minimum_interval(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test options flow validates minimum polling interval."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Try to set interval below minimum - should raise validation error
    with pytest.raises(Exception):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_POLLING_INTERVAL: 0},
        )


async def test_validate_input_success(hass: HomeAssistant, mock_zap_api):
    """Test validate_input function with successful validation."""
    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await validate_input(hass, {CONF_HOST: "192.168.1.100"})

    assert result["serial_number"] == "zap-gateway-12345"
    assert "Sourceful Zap" in result["title"]


def make_api(system_info=None, devices=None):
    """Build a mock API client with the given responses."""
    api = MagicMock()
    api.test_connection = AsyncMock(return_value=True)
    api.get_system_info = AsyncMock(return_value=system_info)
    api.get_devices = AsyncMock(return_value=devices if devices is not None else [])
    api.base_url = "http://192.168.1.100/api"
    return api


def make_flow(hass):
    """Build a config flow instance bound to hass."""
    flow = ZapEnergyConfigFlow()
    flow.hass = hass
    return flow


async def test_validate_input_no_system_info_uses_device_serial(hass: HomeAssistant):
    """Test validate_input falls back to the first device serial."""
    api = make_api(system_info=None, devices=[{"serial_number": "INV001"}])

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await validate_input(hass, {CONF_HOST: "192.168.1.100"})

    assert result["serial_number"] == "INV001"
    assert result["title"] == "Sourceful Zap INV001"


async def test_validate_input_zap_string_top_level_serial(hass: HomeAssistant):
    """Test validate_input reads a top-level serial when zap is a string."""
    api = make_api(
        system_info={"zap": "2.3.15", "sn": "TOP123"},
        devices=[{"serial_number": "INV001"}],
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await validate_input(hass, {CONF_HOST: "192.168.1.100"})

    assert result["serial_number"] == "TOP123"


async def test_validate_input_zap_dict_without_serial(hass: HomeAssistant):
    """Test validate_input with a zap dict that has no serial fields."""
    api = make_api(
        system_info={"zap": {"platform": "srcful-zap-p1"}},
        devices=[{"serial_number": "INV001"}],
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await validate_input(hass, {CONF_HOST: "192.168.1.100"})

    assert result["serial_number"] == "INV001"


async def _start_scan_flow(hass):
    """Start the user flow and pick the scan menu option."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "scan"},
    )


async def test_scan_flow_no_devices_found(hass: HomeAssistant):
    """Test scan flow aborts when no devices are discovered."""
    with patch.object(ZapEnergyConfigFlow, "_scan_network", AsyncMock(return_value=[])):
        result = await _start_scan_flow(hass)

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_scan_flow_single_device_success(hass: HomeAssistant, mock_zap_api):
    """Test scan flow creates an entry for a single discovered device."""
    discovered = [
        {"host": "192.168.1.50", "name": "Zap Gateway (1 devices)", "device_count": 1}
    ]

    with patch.object(
        ZapEnergyConfigFlow, "_scan_network", AsyncMock(return_value=discovered)
    ):
        result = await _start_scan_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "scan"

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "discovered_device": "192.168.1.50",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sourceful Zap zap-gateway-12345"
    assert result["data"][CONF_HOST] == "192.168.1.50"


async def test_scan_flow_many_devices_cannot_connect(hass: HomeAssistant):
    """Test scan flow lists many devices and aborts when validation fails."""
    discovered = [
        {"host": "192.168.1.50", "name": "Zap Gateway (1 devices)", "device_count": 1},
        {"host": "192.168.1.60", "name": "Zap Gateway (2 devices)", "device_count": 2},
    ]

    with patch.object(
        ZapEnergyConfigFlow, "_scan_network", AsyncMock(return_value=discovered)
    ):
        result = await _start_scan_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "scan"
    assert "192.168.1.50" in str(result["data_schema"].schema)
    assert "192.168.1.60" in str(result["data_schema"].schema)

    failing_api = MagicMock()
    failing_api.test_connection = AsyncMock(
        side_effect=ZapConnectionError("Connection failed")
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=failing_api,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "discovered_device": "192.168.1.60",
                CONF_POLLING_INTERVAL: DEFAULT_POLLING_INTERVAL,
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_scan_network_finds_devices(hass: HomeAssistant):
    """Test network scan discovers a device across the subnet."""
    flow = make_flow(hass)

    sock = MagicMock()
    sock.getsockname.return_value = ("192.168.1.23", 54321)
    mock_socket_module = MagicMock()
    mock_socket_module.socket.return_value = sock

    device = {"host": "192.168.1.5", "name": "Zap Gateway (1 devices)"}

    def fake_check_host(host):
        if host == "192.168.1.5":
            return device
        if host == "192.168.1.6":
            raise OSError("boom")
        return None

    with (
        patch(
            "homeassistant.helpers.network.get_url",
            return_value="http://192.168.1.77:8123",
        ),
        patch(
            "custom_components.sourceful_zap.config_flow.socket",
            mock_socket_module,
        ),
        patch.object(
            ZapEnergyConfigFlow, "_check_host", AsyncMock(side_effect=fake_check_host)
        ) as mock_check,
    ):
        result = await flow._scan_network()

    assert result == [device]
    assert mock_check.call_count == 254


async def test_scan_network_fallback_to_hostname(hass: HomeAssistant):
    """Test network scan falls back to hostname resolution."""
    flow = make_flow(hass)

    sock = MagicMock()
    sock.getsockname.return_value = ("127.0.0.1", 54321)
    mock_socket_module = MagicMock()
    mock_socket_module.socket.return_value = sock
    mock_socket_module.gethostname.return_value = "ha-test"
    mock_socket_module.gethostbyname.return_value = "172.17.0.5"

    with (
        patch(
            "homeassistant.helpers.network.get_url",
            side_effect=RuntimeError("no url"),
        ),
        patch(
            "custom_components.sourceful_zap.config_flow.socket",
            mock_socket_module,
        ),
        patch.object(
            ZapEnergyConfigFlow, "_check_host", AsyncMock(return_value=None)
        ) as mock_check,
    ):
        result = await flow._scan_network()

    assert result == []
    mock_socket_module.gethostbyname.assert_called_once_with("ha-test")
    assert mock_check.call_count == 254


async def test_scan_network_no_usable_ip(hass: HomeAssistant):
    """Test network scan gives up when no local IP can be determined."""
    flow = make_flow(hass)

    mock_socket_module = MagicMock()
    mock_socket_module.socket.side_effect = OSError("no network")
    mock_socket_module.gethostbyname.return_value = ""

    with (
        patch("homeassistant.helpers.network.get_url", return_value="http://"),
        patch(
            "custom_components.sourceful_zap.config_flow.socket",
            mock_socket_module,
        ),
        patch.object(
            ZapEnergyConfigFlow, "_check_host", AsyncMock(return_value=None)
        ) as mock_check,
    ):
        result = await flow._scan_network()

    assert result == []
    mock_check.assert_not_called()


async def test_scan_network_unexpected_error(hass: HomeAssistant):
    """Test network scan returns nothing when IP detection blows up."""
    flow = make_flow(hass)

    mock_socket_module = MagicMock()
    mock_socket_module.socket.side_effect = OSError("no network")
    mock_socket_module.gethostbyname.side_effect = OSError("no dns")

    with (
        patch("homeassistant.helpers.network.get_url", return_value=""),
        patch(
            "custom_components.sourceful_zap.config_flow.socket",
            mock_socket_module,
        ),
        patch.object(
            ZapEnergyConfigFlow, "_check_host", AsyncMock(return_value=None)
        ) as mock_check,
    ):
        result = await flow._scan_network()

    assert result == []
    mock_check.assert_not_called()


async def test_scan_network_without_hass_config(hass: HomeAssistant):
    """Test network scan skips HA URL detection without hass.config."""
    flow = ZapEnergyConfigFlow()
    flow.hass = SimpleNamespace()

    sock = MagicMock()
    sock.getsockname.return_value = ("10.0.0.7", 54321)
    mock_socket_module = MagicMock()
    mock_socket_module.socket.return_value = sock

    with (
        patch(
            "custom_components.sourceful_zap.config_flow.socket",
            mock_socket_module,
        ),
        patch.object(
            ZapEnergyConfigFlow, "_check_host", AsyncMock(return_value=None)
        ) as mock_check,
    ):
        result = await flow._scan_network()

    assert result == []
    assert mock_check.call_count == 254


async def test_check_host_finds_gateway(hass: HomeAssistant):
    """Test host check returns gateway info for a Zap device."""
    flow = make_flow(hass)
    api = make_api(
        system_info={"zap": {"deviceId": "zap-123"}},
        devices=[{"serial_number": "INV001"}, {"serial_number": "INV002"}],
    )

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await flow._check_host("192.168.1.5")

    assert result == {
        "host": "192.168.1.5",
        "name": "Zap Gateway (2 devices)",
        "device_count": 2,
    }


async def test_check_host_zap_string_no_devices(hass: HomeAssistant):
    """Test host check with a string zap property and no devices."""
    flow = make_flow(hass)
    api = make_api(system_info={"zap": "2.3.15"}, devices=[])

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await flow._check_host("192.168.1.5")

    assert result is None


async def test_check_host_empty_system_info(hass: HomeAssistant):
    """Test host check returns None when system info is empty."""
    flow = make_flow(hass)
    api = make_api(system_info=None)

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await flow._check_host("192.168.1.5")

    assert result is None


async def test_check_host_no_zap_property(hass: HomeAssistant):
    """Test host check returns None when 'zap' is missing."""
    flow = make_flow(hass)
    api = make_api(system_info={"other": "data"})

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await flow._check_host("192.168.1.5")

    assert result is None


async def test_check_host_timeout(hass: HomeAssistant):
    """Test host check returns None on timeout."""
    flow = make_flow(hass)
    api = MagicMock()
    api.get_system_info = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await flow._check_host("192.168.1.5")

    assert result is None


async def test_check_host_unexpected_error(hass: HomeAssistant):
    """Test host check returns None on unexpected errors."""
    flow = make_flow(hass)
    api = MagicMock()
    api.get_system_info = AsyncMock(side_effect=ValueError("bad json"))

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await flow._check_host("192.168.1.5")

    assert result is None


async def test_zeroconf_flow_no_devices(hass: HomeAssistant):
    """Test zeroconf flow aborts when the gateway has no devices."""
    api = make_api(system_info={"zap": {"deviceId": "zap-123"}}, devices=[])

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=make_zeroconf_info(),
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_zeroconf_flow_connection_error(hass: HomeAssistant):
    """Test zeroconf flow aborts on a connection error."""
    api = MagicMock()
    api.test_connection = AsyncMock(side_effect=ZapConnectionError("Connection failed"))

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=make_zeroconf_info(),
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_zeroconf_flow_unexpected_error(hass: HomeAssistant):
    """Test zeroconf flow aborts on an unexpected error."""
    api = MagicMock()
    api.test_connection = AsyncMock(side_effect=ValueError("boom"))

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=make_zeroconf_info(),
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_zeroconf_confirm_shows_form_without_input(
    hass: HomeAssistant, mock_zap_api
):
    """Test zeroconf confirmation step re-shows the form without input."""
    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=make_zeroconf_info(),
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zeroconf_confirm"

        result = await hass.config_entries.flow.async_configure(result["flow_id"])

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zeroconf_confirm"
        assert result["description_placeholders"] == {"name": "Solaredge INV001"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.1.100"}
