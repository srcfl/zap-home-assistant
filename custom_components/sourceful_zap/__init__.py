"""The Zap Energy integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .api import ZapApiClient, ZapApiError, extract_gateway_serial
from .const import (
    CONF_HOST,
    CONF_POLLING_INTERVAL,
    DEFAULT_API_PATH,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
)
from .coordinator import ZapDataUpdateCoordinator, ZapGatewayCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zap Energy from a config entry."""
    host = entry.data[CONF_HOST]
    # Polling interval from data (config flow) or options (for backwards compatibility)
    polling_interval = entry.data.get(
        CONF_POLLING_INTERVAL,
        entry.options.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL),
    )

    # Create API client with hardcoded /api path
    api = ZapApiClient(host, hass, api_path=DEFAULT_API_PATH)

    # Verify connection and get initial data
    try:
        devices = await api.get_devices()
        if not devices:
            raise ConfigEntryNotReady(f"No devices found on Zap gateway at {host}")
        _LOGGER.info("Found %d devices on gateway at %s", len(devices), host)
    except ZapApiError as err:
        raise ConfigEntryNotReady(f"Error connecting to Zap gateway: {err}") from err

    # Self-heal entries whose unique_id predates the gateway-serial scheme
    try:
        system_info = await api.get_system_info()
    except ZapApiError:
        system_info = None
        _LOGGER.debug("Could not fetch system info for unique ID migration")
    real_serial = extract_gateway_serial(system_info)
    if real_serial and entry.unique_id != real_serial:
        conflict = any(
            other.unique_id == real_serial
            for other in hass.config_entries.async_entries(DOMAIN)
            if other.entry_id != entry.entry_id
        )
        if conflict:
            _LOGGER.warning(
                "Config entry %s duplicates gateway %s; remove one of them",
                entry.title,
                real_serial,
            )
        else:
            _migrate_gateway_identity(
                hass, entry, entry.unique_id or entry.entry_id, real_serial
            )

    # Create coordinator for each device
    coordinators: dict[str, ZapDataUpdateCoordinator] = {}
    for device in devices:
        serial_number = device["serial_number"]
        _LOGGER.info(
            "Setting up device: %s (type: %s, profile: %s)",
            serial_number,
            device.get("type"),
            device.get("profile"),
        )
        coordinator = ZapDataUpdateCoordinator(
            hass, entry, api, serial_number, polling_interval
        )

        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()

        coordinators[serial_number] = coordinator

        # Register device in device registry
        # Use device's profile/make for the device name
        device_name = device.get("profile") or device.get("type") or "Device"
        device_name = str(device_name).replace("_", " ").title()

        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, serial_number)},
            manufacturer="Sourceful Energy",
            model=device.get("model", "Zap Gateway"),
            name=f"{device_name} {serial_number}",
            sw_version=device.get("firmware_version"),
        )

    # Create gateway coordinator for system-level sensors
    gateway_serial = entry.unique_id or entry.entry_id
    gateway_coordinator = ZapGatewayCoordinator(hass, entry, api)
    await gateway_coordinator.async_config_entry_first_refresh()

    # Register gateway device
    device_registry = dr.async_get(hass)
    fw_version = None
    if gateway_coordinator.data:
        fw_version = gateway_coordinator.data.get("firmware_version")
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, gateway_serial)},
        manufacturer="Sourceful Energy",
        model="Zap Gateway",
        name=f"Zap Gateway {gateway_serial}",
        sw_version=fw_version,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
        "gateway_serial": gateway_serial,
        "gateway_coordinator": gateway_coordinator,
    }

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


def _migrate_gateway_identity(
    hass: HomeAssistant, entry: ConfigEntry, old_id: str, new_id: str
) -> None:
    """Move the config entry, gateway device, and its entities to the gateway serial."""
    hass.config_entries.async_update_entry(entry, unique_id=new_id)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, old_id)})
    if device:
        device_registry.async_update_device(
            device.id, new_identifiers={(DOMAIN, new_id)}
        )

    entity_registry = er.async_get(hass)
    old_prefix = f"sourceful_zap_{old_id}_"
    for reg_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if reg_entry.unique_id.startswith(old_prefix):
            suffix = reg_entry.unique_id[len(old_prefix) :]
            entity_registry.async_update_entity(
                reg_entry.entity_id,
                new_unique_id=f"sourceful_zap_{new_id}_{suffix}",
            )
    _LOGGER.info("Migrated gateway identity from %s to %s", old_id, new_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
