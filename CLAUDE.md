# CLAUDE.md - Sourceful Zap Home Assistant Integration

## What is the Zap?

The Zap is Sourceful's **universal local coordination gateway** - a ~$20 ESP32-based device that provides the missing layer between cloud platforms and physical energy devices.

**The coordination gap:** Cloud APIs respond in 2-5 seconds. The grid needs millisecond response. This gap crashed the Iberian grid in April 2025. Local execution is the only architecture that works.

## Protocols

| Protocol | Use Case |
|----------|----------|
| P1 | European smart meters |
| Modbus TCP | Inverters, batteries |
| Modbus RTU (RS-485) | Direct serial control |
| MQTT | Local IoT |
| OCPP | EV charging |
| REST API | Full device control (docs coming) |

## Repository State

- `main` - Clean, ready for new integration
- `legacy-v0.1` - Working P1-only integration (preserved)

## New Integration Architecture

```
custom_components/sourceful_zap/
├── __init__.py           # Config entry setup
├── config_flow.py        # UI configuration
├── coordinator.py        # DataUpdateCoordinator
├── sensor.py             # Sensor entities
├── switch.py             # Control entities
├── const.py              # Constants
├── strings.json          # Translations
└── protocols/
    ├── p1.py             # P1 meter reading
    ├── modbus_tcp.py     # Modbus TCP
    ├── modbus_rtu.py     # Modbus RTU
    ├── mqtt.py           # MQTT
    └── rest.py           # REST API
```

## Key Principles

1. **Physics before code** - Grid needs millisecond response
2. **Local over cloud** - Default to local, cloud is opt-in
3. **Simple over clever** - If proud of cleverness, simplify
4. **Edge control <200ms** - Non-negotiable

## Device APIs

**System info:**
```
GET /api/system
```

**P1 data (legacy):**
```
GET /api/data/p1/obis
```

**New REST API:** Docs coming from @damo

## Context

The energy grid must balance every second. With 50M+ distributed energy resources across Europe, coordination is critical. Cloud APIs are too slow.

The Zap is the local execution layer enabling:
- Fast Frequency Response (sub-second)
- V2G coordination
- Grid services that actually pay

Read: "The Coordination Gap" whitepaper
