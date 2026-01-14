"""Test Zap Energy config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.sourceful_zap.api import ZapConnectionError
from custom_components.sourceful_zap.const import (
    CONF_POLLING_INTERVAL,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    MIN_POLLING_INTERVAL,
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
    mock_api.get_system_info = AsyncMock(
        return_value={"zap": {"deviceId": "zap-123"}}
    )
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
    discovery_info = ZeroconfServiceInfo(
        ip_address="192.168.1.100",
        ip_addresses=["192.168.1.100"],
        hostname="zap-gateway.local.",
        name="zap-gateway._http._tcp.local.",
        port=80,
        properties={},
        type="_http._tcp.local.",
    )

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
    discovery_info = ZeroconfServiceInfo(
        ip_address="192.168.1.100",
        ip_addresses=["192.168.1.100"],
        hostname="zap-gateway.local.",
        name="zap-gateway._http._tcp.local.",
        port=80,
        properties={},
        type="_http._tcp.local.",
    )

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
    discovery_info = ZeroconfServiceInfo(
        ip_address="192.168.1.100",
        ip_addresses=["192.168.1.100"],
        hostname="other-device.local.",
        name="other-device._http._tcp.local.",
        port=80,
        properties={},
        type="_http._tcp.local.",
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


async def test_zeroconf_flow_already_configured(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test zeroconf flow aborts when device already configured."""
    mock_config_entry.add_to_hass(hass)

    discovery_info = ZeroconfServiceInfo(
        ip_address="192.168.1.100",
        ip_addresses=["192.168.1.100"],
        hostname="zap-gateway.local.",
        name="zap-gateway._http._tcp.local.",
        port=80,
        properties={},
        type="_http._tcp.local.",
    )

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
    discovery_info = ZeroconfServiceInfo(
        ip_address="192.168.1.100",
        ip_addresses=["192.168.1.100"],
        hostname="zap-gateway.local.",
        name="zap-gateway._http._tcp.local.",
        port=80,
        properties={},
        type="_http._tcp.local.",
    )

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
    from custom_components.sourceful_zap.config_flow import validate_input

    with patch(
        "custom_components.sourceful_zap.config_flow.ZapApiClient",
        return_value=mock_zap_api,
    ):
        result = await validate_input(hass, {CONF_HOST: "192.168.1.100"})

    assert result["serial_number"] == "zap-gateway-12345"
    assert "Sourceful Zap" in result["title"]
