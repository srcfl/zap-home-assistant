# Sourceful Zap - Home Assistant Integration

[![hacs][hacs-badge]][hacs-url]
[![Release][release-badge]][release-url]

Home Assistant integration for the **Sourceful Zap** - a local coordination gateway for distributed energy resources. It polls the Zap's REST API over your local network.

> **Status:** Released and in use. Targeting [Home Assistant Core](https://developers.home-assistant.io/docs/creating_component_index/) inclusion with [Bronze tier](https://developers.home-assistant.io/docs/core/integration-quality-scale/) quality scale.

## About the Zap

The Zap is a ~$20 ESP32-based gateway enabling **local energy coordination** with <200ms response times - critical for grid services that cloud APIs (2-5s latency) cannot support.

**Supported protocols:** P1 · Modbus TCP/RTU · MQTT · OCPP · REST API

Learn more: [sourceful.energy](https://sourceful.energy)

## Requirements

- Home Assistant 2025.2 or newer. Last tested on 2026.10.1.
- Zap firmware 2.3.x (data model v1) or 7.x (data model v2).
- Home Assistant must be able to reach the Zap on your local network.

## Installation

### HACS

The integration is not in the HACS default store yet, so add it as a custom repository:

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/srcfl/zap-home-assistant` with the type **Integration**.
3. Download **Sourceful Zap** and restart Home Assistant.

### Manual

1. Download `sourceful_zap-<version>.zip` from the [latest release][release-url].
2. Unzip it into `custom_components/` in your Home Assistant config directory, so that you get `custom_components/sourceful_zap/manifest.json`.
3. Restart Home Assistant.

### Legacy P1 Integration

The previous P1-only integration is on the [`legacy-v0.1`](https://github.com/srcfl/zap-home-assistant/tree/legacy-v0.1) branch. The current integration supports P1 meters, so new installs should use a release.

## Setup

Home Assistant discovers Zaps on your network and shows them under **Settings → Devices & services**.

To add one yourself, choose **Add integration → Sourceful Zap**, then **Enter IP address manually** or **Scan network for devices**.

The integration polls device data every 10 seconds by default. To change this, open the integration and choose **Configure**. The minimum is 1 second. Gateway information is polled every 30 seconds.

## Sensors

Each device on the gateway gets the sensors below that it has reported a value for. A sensor appears when its first value arrives, without a reload:

| Group | Sensors | Created for |
|-------|---------|-------------|
| Power | Power | Every device |
| Grid meter | Import, Export, Reactive Power, Grid Frequency, L1-L3 Voltage, Current and Power | Grid meters. P1 meters have no Grid Frequency. |
| Grid power | Grid Power | A grid meter on the same device as v2 solar or an inverter |
| Solar | Production, Temperature, MPPT 1 and 2 Voltage, Current and Power | Solar |
| Inverter | Inverter Power, Temperature, Grid Frequency. L1-L3 Voltage, Current and Power when the device has no grid meter. | Inverters |
| Battery | Battery (state of charge), Power, Voltage, Current, Temperature, Total Charge, Total Discharge, Upper Limit, Lower Limit, Available Charge, Available Discharge | Batteries |
| EV charger | EV Charger Power | EV chargers |
| Gateway | Gateway Uptime, Gateway Temperature, Gateway Memory Usage, Gateway Memory Free, Firmware Version, WiFi Status, WiFi SSID, Signal Strength | Every gateway |

Sign conventions:

- **Grid meter:** positive while importing.
- **Solar:** positive while generating, per MPPT input too.
- **Battery:** positive while charging, negative while discharging.
- **Inverter:** positive while the inverter is supplying.

Installs from before 1.1.1 keep their entity IDs, such as `..._power_2`. Only the names changed.

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
├── api.py               # Zap REST API client
├── config_flow.py       # UI configuration
├── coordinator.py       # Data fetching
├── datamodel.py         # Parses data model v1 and v2 payloads
├── sensor.py            # Sensor entities
├── const.py             # Constants
├── strings.json         # Source strings
├── translations/en.json # Strings that custom integrations load at runtime
├── icon.svg
└── brand/               # Brand icons, required by HACS validation
```

Home Assistant only reads `strings.json` when it builds core. A custom integration gets its names from `translations/en.json`, so keep the two files identical.

See [File Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure/) and [Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) docs.

### Local Development

Use Python 3.13, the same version as CI:

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements_test.txt

pytest tests/
```

See [tests/README.md](tests/README.md) for more on the test suite.

### Releasing

1. Bump `version` in `manifest.json` and add a section for it to `CHANGELOG.md`.
2. Merge to `main` and wait for CI to pass.
3. Push the tag `vX.Y.Z` from `main`. The release workflow runs hassfest and the tests, builds the zip, and publishes the release with the changelog section as its notes.

## Contributing

Join the discussion on [Discord](https://discord.com/invite/srcful).

## License

MIT - see [LICENSE](LICENSE)

---

**Sourceful Labs AB** · Kalmar, Sweden 🇸🇪

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz/
[release-badge]: https://img.shields.io/github/v/release/srcfl/zap-home-assistant
[release-url]: https://github.com/srcfl/zap-home-assistant/releases/latest
