"""Test Zap Energy integration setup."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sourceful_zap.api import ZapConnectionError
from custom_components.sourceful_zap.const import CONF_POLLING_INTERVAL, DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test successful setup of config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_no_devices(
    hass: HomeAssistant, mock_config_entry, mock_zap_api
):
    """Test setup fails when no devices found."""
    mock_config_entry.add_to_hass(hass)
    mock_zap_api.get_devices.return_value = []

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_setup_entry_connection_error(
    hass: HomeAssistant, mock_config_entry, mock_zap_api_error
):
    """Test setup fails on connection error."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api_error
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test unloading config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_reload_entry(hass: HomeAssistant, mock_config_entry, mock_zap_api):
    """Test reloading config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED


def _legacy_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Entry keyed on a device serial, as pre-1.0.2 zeroconf created them."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_POLLING_INTERVAL: 10},
        unique_id="INV001",
        title="Sourceful Zap INV001",
    )
    entry.add_to_hass(hass)
    return entry


async def test_setup_migrates_legacy_unique_id(hass: HomeAssistant, mock_zap_api):
    """A device-serial unique_id heals to the gateway serial on setup."""
    entry = _legacy_entry(hass)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "INV001")},
        manufacturer="Sourceful Energy",
        name="Zap Gateway INV001",
    )
    entity_registry = er.async_get(hass)
    legacy_entity = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "sourceful_zap_INV001_gateway_uptime",
        config_entry=entry,
        device_id=device.id,
    )

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.unique_id == "zap-gateway-12345"
    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, "zap-gateway-12345")})
        is not None
    )
    migrated = entity_registry.async_get(legacy_entity.entity_id)
    assert migrated.unique_id == "sourceful_zap_zap-gateway-12345_gateway_uptime"


async def test_setup_keeps_unique_id_on_duplicate_gateway(
    hass: HomeAssistant, mock_zap_api
):
    """Migration is skipped when another entry already owns the gateway serial."""
    owner = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_POLLING_INTERVAL: 10},
        unique_id="zap-gateway-12345",
        title="Sourceful Zap zap-gateway-12345",
    )
    owner.add_to_hass(hass)
    entry = _legacy_entry(hass)

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.unique_id == "INV001"


async def test_setup_survives_system_info_error_during_migration(
    hass: HomeAssistant, mock_zap_api
):
    """A failing /system call skips migration without breaking setup."""
    entry = _legacy_entry(hass)
    system_info = mock_zap_api.get_system_info.return_value
    mock_zap_api.get_system_info.side_effect = [
        ZapConnectionError("boom"),
        dict(system_info),
        dict(system_info),
        dict(system_info),
    ]

    with patch(
        "custom_components.sourceful_zap.ZapApiClient", return_value=mock_zap_api
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.unique_id == "INV001"
