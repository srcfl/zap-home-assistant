# CLAUDE.md - Sourceful Zap Home Assistant Integration

## Status: LEGACY

This integration is functional but in **maintenance mode**. A new integration is being developed from scratch with the updated Zap REST API.

**Do not add new features to this codebase.** Only critical bug fixes should be considered.

## What This Is

A Home Assistant custom integration for the **Sourceful Energy Zap** P1 meter reader. Reads smart meter data via local HTTP API and creates 35+ sensors for energy monitoring.

## Quick Commands

```bash
# Validate locally
python validate.py

# Format code
python -m black custom_components/
```

## Architecture

```
custom_components/sourceful_zap/
├── __init__.py              # HA setup/teardown entry points
├── manifest.json            # Integration metadata
├── const.py                 # Constants (domain, defaults)
├── sensor.py                # Platform setup, creates all sensors
├── p1_coordinator.py        # Fetches P1 data from /api/data/p1/obis
├── p1_sensor.py             # P1 sensor entity class
├── system_data_coordinator.py  # Fetches system info from /api/system
├── system_sensor.py         # System sensor entity class
├── obis_definitions.py      # OBIS code → sensor mappings (25 sensors)
└── system_sensor_definitions.py  # System sensor definitions (12 sensors)
```

### Data Flow

1. **P1DataCoordinator** polls `http://{host}/api/data/p1/obis` every scan_interval
2. OBIS codes are parsed via regex from the response
3. **P1Sensor** entities read values from coordinator data
4. **SystemDataCoordinator** polls `http://{host}/api/system` for device info
5. **SystemSensor** entities expose device diagnostics

### Key Patterns

- **Local polling only** - no cloud dependency
- **Coordinator pattern** - single fetch serves multiple sensors
- **YAML platform config** - legacy pattern, not config flow
- **No external dependencies** - uses only HA built-ins

## Known Technical Debt (Not Being Fixed Here)

These will be addressed in the new integration:

- YAML-only configuration (no config flow)
- Single device support only
- No tests
- Manual Throttle instead of DataUpdateCoordinator
- No diagnostics support

## Device API

**P1 Data**: `GET /api/data/p1/obis`
```json
{
  "status": "success",
  "data": ["1-0:1.8.0(00061825.061*kWh)", ...]
}
```

**System Info**: `GET /api/system`
```json
{
  "temperature_celsius": 31.2,
  "zap": { "deviceId": "...", "firmwareVersion": "0.1.4" }
}
```

## New Integration Plans

A new integration will replace this one, built from scratch with:
- Updated REST API (docs coming from @damo)
- Config flow from day one
- Multi-device support built-in
- Full test coverage
- Home Assistant core compliance from the start

The legacy code is preserved in the `legacy-v0.1` branch.
