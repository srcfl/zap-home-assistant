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

- [ ] Config flow (no YAML)
- [ ] Proper entity naming
- [ ] DataUpdateCoordinator
- [ ] Error handling
- [ ] Tests with >80% coverage
- [ ] Translations (strings.json)
- [ ] Diagnostics support

## Device API

```
GET /api/system          # Device info
GET /api/data/p1/obis    # P1 meter data (legacy)
# REST API docs pending from @damo
```

## Branches

- `main` - New integration (WIP)
- `legacy-v0.1` - Working P1-only integration

## Principles

1. Physics before code - <200ms edge control is non-negotiable
2. Local over cloud - Default local, cloud opt-in
3. Follow HA patterns - Don't be clever, be standard
