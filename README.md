# Sourceful Zap - Home Assistant Integration

> **🚧 NEW INTEGRATION COMING**
>
> This repo is being prepared for a new integration built from scratch.
>
> **Looking for the working P1 integration?** → Use the [`legacy-v0.1`](https://github.com/srcfl/zap-home-assistant/tree/legacy-v0.1) branch

## What is the Zap?

The **Sourceful Zap** is a ~$20 ESP32-based gateway that provides the missing layer between cloud platforms and physical energy devices. It enables **millisecond-level local control** that cloud APIs simply cannot achieve.

**The Zap is NOT just a P1 reader** - it's a universal local coordination gateway.

```
THE COORDINATION GAP:

┌─────────────┐
│   Cloud     │  ← 2-5 second response (too slow for grid services)
│   Platforms │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    ZAP      │  ← LOCAL EXECUTION LAYER
│  Gateway    │     <200ms response
│             │     Works offline
│             │     Real device control
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Devices    │  ← Inverters, batteries, EVs, meters
└─────────────┘
```

### Protocols Supported

| Protocol | Use Case |
|----------|----------|
| **P1** | European smart meters (180M+ installed) |
| **Modbus TCP** | Inverters, batteries, industrial equipment |
| **Modbus RTU (RS-485)** | Direct serial device control |
| **MQTT** | Local IoT communication |
| **OCPP** | EV charging stations |
| **REST API** | Coming soon - full device control |

### Why Local Execution Matters

The grid must balance **every second**. Cloud APIs respond in 2-5 seconds minimum. That gap crashed the Iberian grid in April 2025 - 15GW disappeared in 5 seconds, 60 million people lost power.

**Local execution is the only architecture that works for:**
- Fast Frequency Response (sub-second)
- V2G coordination (real-time)
- Grid services that actually pay

## Status

| What | Where |
|------|-------|
| **Legacy P1 integration** | [`legacy-v0.1` branch](https://github.com/srcfl/zap-home-assistant/tree/legacy-v0.1) |
| **New integration** | Coming to `main` when REST API docs are ready |

## New Integration Goals

The new integration will support the full Zap capability:

- **Config Flow** - UI-based setup, no YAML
- **Multi-device** - Multiple Zaps per installation
- **Multi-protocol** - P1, Modbus, MQTT, REST
- **Device Registry** - Proper HA device/entity management
- **Diagnostics** - Built-in troubleshooting
- **Full test coverage** - Ready for HA core submission

## Get Involved

- **Discord**: [#dev channel](https://discord.com/invite/srcful)
- **API Docs**: Coming soon
- **Whitepaper**: [The Coordination Gap](https://sourceful.energy)

## About Sourceful

Sourceful is building **Local Coordination Infrastructure** - the physical rails that make distributed energy work. The Zap enables millisecond control at the edge, creating value from 50+ million distributed energy resources across Europe.

**This isn't software optimization. It's infrastructure.**

Learn more at [sourceful.energy](https://sourceful.energy)

---

## Credits

- **Sourceful Labs AB** - Kalmar, Sweden 🇸🇪
- Thanks to community contributors: @erikarenhill, @Vamsi-aki

## License

MIT License - see [LICENSE](LICENSE)
