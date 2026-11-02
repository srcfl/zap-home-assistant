# CLAUDE.md

## Project

Home Assistant integration for the Sourceful Zap gateway. Targeting HA Core inclusion at Bronze tier.

## The Zap

ESP32-based local coordination gateway (~$20 BOM). Enables <200ms device control vs 2-5s cloud latency.

**Protocols:** P1, Modbus TCP/RTU, MQTT, OCPP, REST API (docs pending)

## HA Integration Standards

Follow official docs - don't reinvent:

| Component | Documentation |
|-----------|---------------|
| Structure | [File Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure/) |
| Manifest | [Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) |
| Config Flow | [Config Entries](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) |
| Data Fetching | [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data/) |
| Entities | [Entity](https://developers.home-assistant.io/docs/core/entity/) |
| Testing | [Testing](https://developers.home-assistant.io/docs/development_testing/) |
| Quality Scale | [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) |

## Bronze Tier Checklist

Minimum for Core inclusion:

- [x] Config flow (no YAML)
- [x] Proper entity naming
- [x] DataUpdateCoordinator
- [x] Error handling
- [x] Tests with >80% coverage
- [x] Translations (`strings.json` and `translations/en.json`)
- [ ] Diagnostics support

## Device API

The endpoints the integration uses, in `api.py`:

```
GET /api/system                    # Gateway info
GET /api/devices                   # Devices on the gateway
GET /api/devices/{sn}/data/json    # Live data, data model v1 or v2
GET /api/devices/{sn}/ders         # DER metadata
```

`datamodel.py` detects the data model per response. Firmware 2.3.x sends v1 and firmware 7.x sends v2.

## Translations

Custom integrations load names from `translations/en.json`. `strings.json` is only read when Home Assistant builds core. Keep the two files identical, or sensors fall back to device class names.

## Branches and releases

- `main` - Current integration
- `legacy-v0.1` - Old P1-only integration

Pushing a `vX.Y.Z` tag from `main` publishes a release. Bump `manifest.json` and `CHANGELOG.md` first. See "Releasing" in `README.md`.

## Principles

1. Physics before code - <200ms edge control is non-negotiable
2. Local over cloud - Default local, cloud opt-in
3. Follow HA patterns - Don't be clever, be standard
