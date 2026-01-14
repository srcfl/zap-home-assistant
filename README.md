# Sourceful Zap - Home Assistant Integration

[![hacs][hacs-badge]][hacs-url]
[![Project Status: WIP][status-badge]][status-url]

Home Assistant integration for the **Sourceful Zap** - a local coordination gateway for distributed energy resources.

> **Status:** In development. Targeting [Home Assistant Core](https://developers.home-assistant.io/docs/creating_component_index/) inclusion with [Bronze tier](https://developers.home-assistant.io/docs/core/integration-quality-scale/) quality scale.

## About the Zap

The Zap is a ~$20 ESP32-based gateway enabling **local energy coordination** with <200ms response times - critical for grid services that cloud APIs (2-5s latency) cannot support.

**Supported protocols:** P1 · Modbus TCP/RTU · MQTT · OCPP · REST API

Learn more: [sourceful.energy](https://sourceful.energy)

## Installation

### HACS (Coming Soon)

Once published, install via [HACS](https://hacs.xyz/).

### Manual

```bash
# Clone to custom_components
cd ~/.homeassistant/custom_components
git clone https://github.com/srcfl/zap-home-assistant.git sourceful_zap
```

### Legacy P1 Integration

For the working P1-only integration, use the [`legacy-v0.1`](https://github.com/srcfl/zap-home-assistant/tree/legacy-v0.1) branch.

## Development

This integration follows [Home Assistant development guidelines](https://developers.home-assistant.io/docs/development_index/).

### Requirements

| Requirement | Reference |
|-------------|-----------|
| Config Flow | [Config Entries](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) |
| Coordinator | [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data/) |
| Translations | [Internationalization](https://developers.home-assistant.io/docs/internationalization/) |
| Tests | [Testing](https://developers.home-assistant.io/docs/development_testing/) |
| Quality Scale | [Bronze tier minimum](https://developers.home-assistant.io/docs/core/integration-quality-scale/) |

### Structure

```
custom_components/sourceful_zap/
├── __init__.py          # Integration setup
├── manifest.json        # Integration metadata
├── config_flow.py       # UI configuration
├── coordinator.py       # Data fetching
├── sensor.py            # Sensor entities
├── const.py             # Constants
├── strings.json         # Translations
└── translations/        # Localized strings
```

See [File Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure/) and [Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) docs.

### Local Development

```bash
# Set up dev environment
python -m venv venv
source venv/bin/activate
pip install homeassistant

# Run tests
pytest tests/
```

## Contributing

Join the discussion on [Discord](https://discord.com/invite/srcful).

## License

MIT - see [LICENSE](LICENSE)

---

**Sourceful Labs AB** · Kalmar, Sweden 🇸🇪

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz/
[status-badge]: https://img.shields.io/badge/status-WIP-yellow.svg
[status-url]: https://github.com/srcfl/zap-home-assistant
