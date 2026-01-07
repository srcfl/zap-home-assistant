# Sourceful Zap - Home Assistant Integration

> **🚧 NEW INTEGRATION COMING**
>
> This integration is being rebuilt from scratch to support the full capabilities of the Sourceful Zap gateway.
>
> **The Zap is not just a P1 reader** - it's a universal local coordination gateway for distributed energy resources.

## What is the Zap?

The **Sourceful Zap** is a ~$20 ESP32-based gateway that provides the missing layer between cloud platforms and physical energy devices. It enables **millisecond-level local control** that cloud APIs simply cannot achieve.

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

## Current Status

| Component | Status |
|-----------|--------|
| Legacy P1 integration | ✅ Works (see `legacy-v0.1` branch) |
| New multi-protocol integration | 🚧 In development |
| REST API support | 🚧 Waiting for API docs |
| Config flow (UI setup) | 🚧 Planned |
| Multi-device support | 🚧 Planned |

## For Existing Users

The legacy P1 integration continues to work. Install via HACS or see the `legacy-v0.1` branch.

```yaml
# Legacy configuration (still works)
sensor:
  - platform: sourceful_zap
    host: zap.local
```

## New Integration Goals

The new integration will be built for the full Zap capability:

- **Config Flow** - UI-based setup, no YAML required
- **Multi-device** - Support multiple Zaps per installation
- **Multi-protocol** - P1, Modbus, MQTT, REST
- **Device Registry** - Proper HA device/entity management
- **Diagnostics** - Built-in troubleshooting
- **Full test coverage** - Ready for HA core submission

## Get Involved

- **Discord**: [#dev channel](https://discord.com/invite/srcful) - where the action is
- **API Docs**: Coming soon from the Sourceful team
- **Whitepaper**: [The Coordination Gap](https://sourceful.energy) - why this matters

## About Sourceful

Sourceful is building **Local Coordination Infrastructure** - the physical rails that make distributed energy work. The Zap is the gateway that enables millisecond control at the edge, creating value from the 50+ million distributed energy resources across Europe.

**This isn't software optimization. It's infrastructure.**

Learn more at [sourceful.energy](https://sourceful.energy)

---

## Legacy Documentation

<details>
<summary>Click to expand legacy P1-only documentation</summary>

### Legacy Installation (HACS)

1. Open HACS in Home Assistant
2. Go to "Integrations" → Custom repositories
3. Add this repository URL, select "Integration"
4. Search for "Sourceful Energy Zap" and install
5. Restart Home Assistant

### Legacy Configuration

```yaml
sensor:
  - platform: sourceful_zap
    host: zap.local
    scan_interval: 10
```

### Legacy Sensors

The P1-only integration creates 35+ sensors:
- Energy import/export (kWh)
- Power import/export (kW)
- Per-phase voltage, current, power
- Reactive power
- Device diagnostics (temp, WiFi, uptime)

### Legacy Troubleshooting

1. Verify Zap is accessible: `http://zap.local/api/data/p1/obis`
2. Check HA logs: `grep sourceful_zap home-assistant.log`
3. Enable debug logging:
   ```yaml
   logger:
     logs:
       custom_components.sourceful_zap: debug
   ```

</details>

---

## Credits

- **Sourceful Labs AB** - Kalmar, Sweden 🇸🇪
- Thanks to community contributors: @erikarenhill, @Vamsi-aki

## License

MIT License - see [LICENSE](LICENSE)
