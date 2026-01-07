# CLAUDE.md - Sourceful Zap Home Assistant Integration

## What is the Zap?

The Zap is NOT just a P1 reader. It's Sourceful's **universal local coordination gateway** - a ~$20 ESP32-based device that provides the missing layer between cloud platforms and physical energy devices.

**The coordination gap:** Cloud APIs respond in 2-5 seconds. The grid needs millisecond response. This gap crashed the Iberian grid in April 2025. Local execution is the only architecture that works.

## Protocols

| Protocol | Use Case | Status |
|----------|----------|--------|
| P1 | European smart meters | ✅ Legacy support |
| Modbus TCP | Inverters, batteries | 🚧 New integration |
| Modbus RTU (RS-485) | Direct serial control | 🚧 New integration |
| MQTT | Local IoT | 🚧 New integration |
| OCPP | EV charging | 🚧 Future |
| REST API | Full device control | 🚧 Docs coming |

## Repository Structure

```
├── custom_components/sourceful_zap/  # Legacy P1-only integration
├── legacy-v0.1 branch                # Preserved legacy code
└── main branch                       # New multi-protocol integration
```

## Legacy Code (P1 Only)

The `legacy-v0.1` branch contains the working P1-only integration:
- YAML platform configuration
- P1 OBIS code parsing
- 35+ sensors for energy monitoring
- Works with HACS

**Do not add features to legacy.** The new integration will replace it.

## New Integration Architecture (Planned)

```
custom_components/sourceful_zap/
├── __init__.py           # Config entry setup
├── config_flow.py        # UI configuration
├── coordinator.py        # DataUpdateCoordinator
├── sensor.py             # Sensor entities
├── switch.py             # Control entities (Modbus write)
├── const.py              # Constants
├── protocols/
│   ├── p1.py             # P1 meter reading
│   ├── modbus_tcp.py     # Modbus TCP client
│   ├── modbus_rtu.py     # Modbus RTU (RS-485)
│   ├── mqtt.py           # MQTT integration
│   └── rest.py           # REST API client
└── strings.json          # Translations
```

## Development Commands

```bash
# Format
python -m black custom_components/

# Lint
python -m flake8 custom_components/
python -m pylint custom_components/

# Type check
python -m mypy custom_components/

# Validate
python validate.py
```

## Device APIs

**Legacy P1 endpoint:**
```
GET /api/data/p1/obis
→ OBIS codes from smart meter
```

**System info:**
```
GET /api/system
→ Device ID, firmware, temp, WiFi, memory
```

**New REST API:** Documentation coming from @damo

## Key Principles

From Sourceful Engineering:

1. **Physics before code** - Grid needs millisecond response, cloud can't provide it
2. **Local over cloud** - Default to local execution, cloud is opt-in
3. **Simple over clever** - If you're proud of how clever it is, simplify
4. **Edge control <200ms** - Non-negotiable for grid services

## Context: Why This Matters

The energy grid must balance every second. With 50M+ distributed energy resources (solar, batteries, EVs) across Europe, coordination is the critical challenge. Cloud APIs are too slow.

The Zap is the local execution layer that makes distributed energy work - enabling:
- Fast Frequency Response (sub-second)
- V2G coordination
- Grid services that actually pay

Read the whitepaper: "The Coordination Gap"
