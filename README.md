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

- Home Assistant 2025.2 or newer. Tested on 2025.2.5 and 2026.10.1.
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

## Dashboard

The integration adds a **Sourceful Zap** dashboard to the sidebar. Your browser builds it from the sensors of your Zap, so it shows what you have: a grid meter gets power, energy and per-phase charts, and solar, a battery, an inverter and an EV charger get their own. Each Zap gets a view, and each device on it a section.

- **Reload the page first.** After you install or update the integration, reload the browser page (or restart the companion app) so the cards load.
- **Time range.** The buttons at the top set the range for every chart and sparkline: 1 h, 6 h, 24 h, 7 d or 30 d. **Custom** takes a from and a to. A preset is remembered in the browser; a custom range lasts for the tab's session.
- **Hover.** Pointing at one chart shows a crosshair and the values in all of them.
- **Look.** The dashboard has its own dark look, whatever theme you use.
- **Hide it.** Open the integration, choose **Configure** and clear **Show the Sourceful Zap dashboard in the sidebar**. The cards stay available.

The dashboard lives at `/sourceful-zap`. If you already have a dashboard there, it uses `/sourceful-zap-dashboard`.

Charts read Home Assistant's recorder. Ranges up to 6 hours use the recorded states, ranges up to 3 days use 5-minute statistics, and longer ranges use hourly statistics. Home Assistant keeps the first two for about ten days, so an older custom range is shown per hour.

### Your own dashboard

The built-in dashboard cannot be edited. To change it, make a copy:

1. Go to **Settings → Dashboards → Add dashboard** and choose **Sourceful Zap**.
2. Open the new dashboard, press the pencil and choose **Take control**.

A dashboard can also use the strategy in YAML. `appearance: theme` makes the cards follow your Home Assistant theme instead of the dark look:

```yaml
strategy:
  type: custom:sourceful-zap
  appearance: theme
```

### Cards

The cards are in the card picker under custom cards, and work on any dashboard and with any entity. They are configured in YAML.

**`custom:zap-stat-card`** shows a value, a second line and a sparkline.

```yaml
type: custom:zap-stat-card
entity: sensor.p1_uart_power
name: Power now
unit: W
zero: true
hours: range
secondary:
  - entity: sensor.p1_uart_l1_current
    unit: A
    decimals: 1
```

| Option | Default | Meaning |
|--------|---------|---------|
| `entity` | required | The entity to show |
| `name` | entity name | Label |
| `unit` | entity unit | Unit to show. W, kW and MW convert between each other, as do Wh, kWh and MWh. |
| `decimals` | `0` | Decimals of the value |
| `mode` | `state` | `state`, `today` (change since midnight, for an energy counter), `duration` (seconds as days and hours) or `text` |
| `hero` | `false` | A larger figure, for the one number a view leads with |
| `graph` | `true` | Sparkline, for `mode: state` |
| `hours` | `1` | Sparkline window in hours, or `range` to follow the range picker |
| `zero` | `false` | The sparkline starts at zero and gets a wash under the line |
| `color` | `neutral` | `blue`, `orange`, `aqua`, `yellow`, `magenta`, `green`, `violet`, `red`, `neutral` or a CSS color |
| `key` | `false` | A color key beside the label |
| `secondary` | none | Second line: a list of `entity`, with optional `unit`, `decimals`, `label`, `map` (texts for states) and `status` (`good` or `warning` per state) |
| `secondary_layout` | `inline` | `inline` or `rows` |
| `appearance` | `theme` | `zap` for the dark look |

**`custom:zap-chart-card`** shows lines, an area or energy bars over time.

```yaml
type: custom:zap-chart-card
title: Power per phase
kind: line
unit: W
zero: true
series:
  - entity: sensor.p1_uart_l1_power
    name: L1
    color: blue
  - entity: sensor.p1_uart_l2_power
    name: L2
    color: orange
```

| Option | Default | Meaning |
|--------|---------|---------|
| `series` | required | A list of `entity`, with optional `name` and `color` |
| `title` | none | Title. Bars add their width, such as "per hour". |
| `kind` | `line` | `line`, `area` or `bar`. `bar` shows how much an energy counter grew per 5 minutes, 15 minutes, hour or day, depending on the range. |
| `unit` | unit of the first entity | Unit to show, converted as for the stat card |
| `decimals` | `0` | Decimals in the readout |
| `zero` | `false` | The value axis includes zero. Bars always do. |
| `hours` | `range` | Window in hours, or `range` to follow the range picker |
| `appearance` | `theme` | `zap` for the dark look |

**`custom:zap-range-picker`** shows a title and the time range buttons. One picker sets the range for every Zap card with `hours: range` in the browser tab.

| Option | Default | Meaning |
|--------|---------|---------|
| `title`, `icon` | none | Title and an icon such as `mdi:flash` |
| `options` | `[1h, 6h, 24h, 7d, 30d]` | Presets, in hours (`h`) or days (`d`) |
| `default` | `24h` | Preset for a first visit |
| `custom` | `true` | The **Custom** button |
| `labels` | none | Texts for presets, such as `{24h: Day}` |
| `appearance` | `theme` | `zap` for the dark look |

**`custom:zap-heading-card`** shows a `title` and an `icon`. Without a title it is an empty row that starts the next cards on a new line.

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
├── dashboard.py         # Serves the cards and adds the dashboard to the sidebar
├── frontend/
│   └── zap-cards.js     # The cards and the dashboard strategy, one file, no build step
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
node --test tests/frontend/*.test.mjs
```

`zap-cards.js` is plain JavaScript that the browser loads as it is. The Node tests cover its logic: scales, units, data tiers and the dashboard the strategy builds. See [tests/README.md](tests/README.md) for more on the test suite.

### Releasing

1. Bump `version` in `manifest.json` and `VERSION` in `frontend/zap-cards.js`, and add a section for the version to `CHANGELOG.md`.
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
