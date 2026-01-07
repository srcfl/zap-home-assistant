# Sourceful Energy Zap Home Assistant Custom Component

> **⚠️ LEGACY VERSION - NEW INTEGRATION COMING**
>
> This integration is functional but considered **legacy**. A new official integration will replace this one, built from scratch with the updated Zap REST API.
>
> **Status:**
> - ✅ Works with HACS for current users
> - ⚠️ No longer actively developed
> - 🚧 **New integration coming** - will replace this with proper multi-device support, config flow, and full HA core compliance
>
> **Existing users:** This integration will continue to work. The legacy code is preserved in the `legacy-v0.1` branch.
>
> **Want to contribute?** Join us on [Discord](https://discord.com/invite/srcful) - we're building the new integration once the updated REST API docs are released.

## About This Implementation

A custom component for Home Assistant that integrates with the [Sourceful Energy Zap](https://sourceful.energy/store/sourceful-energy-zap) P1 meter reader.

**Note:** This is a legacy reference implementation. While functional, a new integration is being developed that will:
- Use the updated Zap REST API
- Have proper config flow (UI configuration)
- Support multiple Zap devices
- Meet Home Assistant core inclusion standards from day one

The Sourceful Energy Zap is a P1 meter reader that gives you unprecedented clarity of your energy consumption to help reduce your bills. Made by [Sourceful Labs AB](https://sourceful.energy) in Kalmar, Sweden 🇸🇪, it's designed for European smart meters with standard P1 RJ12 ports.

## Features

- **Real-time monitoring** of P1 smart meter data from your Sourceful Energy Zap
- **Energy tracking** for both import and export with proper Energy Dashboard integration
- **Per-phase monitoring** (L1, L2, L3) for voltage, current, and power
- **Reactive power monitoring** for comprehensive energy analysis
- **Net power calculation** (import - export) - perfect for solar monitoring
- **Device diagnostics** including temperature, WiFi signal, memory usage, and uptime
- **Automatic device discovery** with real device ID and firmware version
- **No external power required** - the Zap draws power directly from your smart meter
- **35+ sensors** automatically created for comprehensive monitoring
- **HACS compatible** for easy installation and updates
- **Official Sourceful Energy branding** with the authentic logo and design

## Supported Sensors

### Main Energy Sensors
- Total Energy Import (kWh)
- Total Energy Export (kWh)
- Current Power Import (kW)
- Current Power Export (kW)
- Net Power (kW) - calculated sensor

### Per-Phase Sensors
- Voltage L1/L2/L3 (V)
- Current L1/L2/L3 (A)
- Power Import/Export per phase (kW)

### Reactive Power Sensors
- Total Reactive Energy Import (kVArh)
- Total Reactive Energy Export (kVArh)
- Reactive Power per phase (kVAr)

### System & Device Sensors
- Device ID - unique identifier of your Zap device
- Firmware Version - current firmware version
- Uptime - how long the device has been running (seconds)
- Temperature - internal device temperature (°C)
- Memory Usage - RAM usage percentage and absolute values (MB)
- CPU Frequency - processor speed (MHz)
- Flash Size - storage capacity (MB)
- WiFi Status - connection status
- WiFi SSID - connected network name
- WiFi Signal Strength - signal strength (dBm)
- Local IP Address - device IP on your network

## Prerequisites

### Sourceful Energy Zap Device
You need a [Sourceful Energy Zap](https://sourceful.energy/store/sourceful-energy-zap) P1 meter reader connected to your smart meter.

### Meter Compatibility
The Sourceful Energy Zap is compatible with standard P1 RJ12 smart meters in European countries. For full compatibility details, check the [official compatibility guide](https://intercom.help/sourceful-energy/en/articles/11486814-which-meters-are-compatible-with-zap).

**Supported Countries:**
🇦🇹 Austria* | 🇧🇪 Belgium | 🇩🇰 Denmark | 🇫🇮 Finland | 🇭🇺 Hungary | 🇮🇪 Ireland
🇱🇹 Lithuania | 🇱🇺 Luxembourg | 🇳🇱 Netherlands | 🇵🇹 Portugal | 🇸🇪 Sweden

*Work in progress to support encrypted data

### Setup Requirements
- Sourceful Energy Zap connected to your smart meter's P1 port
- Zap connected to your WiFi network
- Zap accessible on your local network (default hostname: `zap.local`)

## Quick Start

1. **Install via HACS** (recommended) or manually download
2. **Add to configuration.yaml**:
   ```yaml
   sensor:
     - platform: sourceful_zap
       host: zap.local
   ```
3. **Restart Home Assistant**
4. **Enjoy 35+ sensors** automatically created!

## Installation

### Method 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Search for "Sourceful Energy Zap" and install the integration
7. Restart Home Assistant

### Method 2: Manual Installation

1. Download this repository
2. Copy the `custom_components/sourceful_zap` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add the configuration to your `configuration.yaml`

## Configuration

Add the following to your `configuration.yaml`:

```yaml
sensor:
  - platform: sourceful_zap
    host: zap.local  # IP address or hostname of your Zap device
    endpoint: /api/data/p1/obis  # P1 data API endpoint (default)
    system_endpoint: /api/system  # System info API endpoint (default)
    name: Zap  # Optional: custom name prefix (default)
    scan_interval: 10  # Optional: update interval in seconds (default: 10)
```

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `host` | Yes | `zap.local` | IP address or hostname of your Zap device |
| `endpoint` | No | `/api/data/p1/obis` | P1 data API endpoint path |
| `system_endpoint` | No | `/api/system` | System information API endpoint path |
| `name` | No | `Zap` | Custom name prefix for sensors |
| `scan_interval` | No | `10` | Update interval in seconds |

## Sensor Overview

After setup, you'll have **35+ sensors** available:

### 🔋 **Energy Sensors**
- `sensor.zap_total_energy_import` - Total energy consumed (kWh)
- `sensor.zap_total_energy_export` - Total energy exported (kWh)
- `sensor.zap_current_power_import` - Current power consumption (kW)
- `sensor.zap_current_power_export` - Current power export (kW)
- `sensor.zap_net_power` - Net power (import - export, kW)

### ⚡ **Per-Phase Monitoring**
- `sensor.zap_voltage_l1/l2/l3` - Phase voltages (V)
- `sensor.zap_current_l1/l2/l3` - Phase currents (A)
- `sensor.zap_power_l1/l2/l3_import/export` - Phase power (kW)

### 🌐 **Device Status**
- `sensor.zap_device_id` - Unique device identifier
- `sensor.zap_firmware_version` - Current firmware version
- `sensor.zap_temperature` - Device temperature (°C)
- `sensor.zap_wifi_signal_strength` - WiFi signal (dBm)
- `sensor.zap_uptime` - Device uptime (seconds)

## Energy Dashboard Integration

To use with Home Assistant's Energy Dashboard:

1. Go to **Configuration** → **Energy**
2. Under **Grid consumption**, add: `sensor.zap_total_energy_import`
3. Under **Return to grid**, add: `sensor.zap_total_energy_export`
4. Save the configuration

## API Data Format

The component connects to your Sourceful Energy Zap via two local API endpoints:

### P1 Energy Data
**API Endpoint:** `http://zap.local/api/data/p1/obis` (or use your Zap's IP address)

**Response Format:**
```json
{
  "status": "success",
  "ts": 1751722190484,
  "data": [
    "0-0:1.0.0(250705142950W)",
    "1-0:1.8.0(00061825.061*kWh)",
    "1-0:2.8.0(00008702.210*kWh)",
    "1-0:3.8.0(00000259.153*kVArh)",
    "1-0:4.8.0(00009399.569*kVArh)",
    "1-0:1.7.0(0000.000*kW)",
    "1-0:2.7.0(0000.385*kW)",
    "1-0:32.7.0(231.2*V)",
    "1-0:52.7.0(235.4*V)",
    "1-0:72.7.0(235.9*V)",
    "1-0:31.7.0(001.5*A)",
    "1-0:51.7.0(-001.2*A)",
    "1-0:71.7.0(-001.5*A)",
    ...
  ]
}
```

The component automatically parses all OBIS codes from the data array and creates corresponding Home Assistant sensors.

### System Information Data
**API Endpoint:** `http://zap.local/api/system` (or use your Zap's IP address)

**Response Format:**
```json
{
  "time_utc_sec": 1751723323,
  "uptime_seconds": 86569,
  "temperature_celsius": 31.1856,
  "memory_MB": {
    "total": 0.27689,
    "available": 0.0648079,
    "free": 0.0648079,
    "used": 0.212082,
    "percent_used": 76.5943
  },
  "zap": {
    "deviceId": "zap-0000e421347506dc",
    "cpuFreqMHz": 160,
    "flashSizeMB": 4,
    "sdkVersion": "4.4.5.230722",
    "firmwareVersion": "0.1.4",
    "network": {
      "wifiStatus": "connected",
      "localIP": "192.168.1.235",
      "ssid": "your-wifi-network",
      "rssi": -49
    }
  }
}
```

The component extracts system information and creates diagnostic sensors for device monitoring and troubleshooting.

## Troubleshooting

### Common Issues

1. **No sensors appearing**: 
   - Check that the Sourceful Energy Zap is accessible at the configured host
   - Verify the Zap is connected to your WiFi network
   - Try accessing `http://zap.local/api/data/p1/obis` and `http://zap.local/api/system` in a browser

2. **Connection errors**: 
   - Ensure the Zap is on the same network as Home Assistant
   - If using IP address instead of hostname, verify the correct IP
   - Check that the P1 port on your smart meter is properly connected

3. **Sensor values not updating**: 
   - Check Home Assistant logs for any error messages
   - Verify your smart meter is [compatible](https://intercom.help/sourceful-energy/en/articles/11486814-which-meters-are-compatible-with-zap)
   - Ensure the Zap has a solid connection to your smart meter's P1 port

### Zap Device Setup

If you're having trouble with the Sourceful Energy Zap device itself:

1. **Check the connection**: Ensure the Zap is properly connected to your smart meter's P1 port (RJ12)
2. **WiFi setup**: Make sure the Zap is connected to your WiFi network
3. **Power**: The Zap draws power from the smart meter - no external power needed
4. **Meter compatibility**: Verify your meter is supported using the [official compatibility guide](https://intercom.help/sourceful-energy/en/articles/11486814-which-meters-are-compatible-with-zap)

### Network Discovery

If `zap.local` doesn't work, try:
- Finding the Zap's IP address in your router's device list
- Using network scanning tools to find the device
- Checking your router's DHCP client list for "Sourceful" or "Zap"

### Logging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.sourceful_zap: debug
```

### Checking Logs

View logs in Home Assistant:
1. Go to **Configuration** → **Logs**
2. Search for "sourceful_zap"

Or check the log file directly:
```bash
grep sourceful_zap home-assistant.log
```

## Contributing

> **Note:** This legacy integration is no longer accepting new feature contributions. A new integration is being built from scratch.

### Want to Help with the New Integration?

The new Zap Home Assistant integration will be developed fresh with:
- Updated REST API (docs coming soon)
- Config flow from day one
- Multi-device support built-in
- Full test coverage
- Home Assistant core compliance

**How to get involved:**
1. Join our [Discord](https://discord.com/invite/srcful)
2. Watch this repo - the new integration will replace the legacy code here

### About This Legacy Version

This integration works but has known technical debt:
- YAML-only configuration
- Single device support
- No tests
- Basic polling pattern

These issues will be addressed in the new integration rather than patching this one.

## Development

### Prerequisites

- Home Assistant development environment
- Python 3.9+
- Access to a Sourceful Energy Zap device
- Docker (for local validation)

### Local Validation

Before pushing changes, you can run local validation to match the GitHub Actions environment:

```bash
./validate_local.sh
```

This script uses Docker to run the same checks as the CI pipeline:
- Black code formatting
- Python syntax validation  
- JSON file validation

### Code Formatting

The project uses Black for code formatting. To format your code:

```bash
# Using Docker (matches CI environment)
docker run --rm -v $(pwd):/app -w /app python:3.10-slim bash -c "pip install black && python -m black custom_components/"

# Or if you have Black installed locally
python -m black custom_components/
```

### Testing

1. Clone this repository
2. Set up a Home Assistant development environment
3. Install the component in development mode
4. Configure with your Zap device details
5. Test functionality and sensor updates

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Community

- **Discord**: Join [#dev channel](https://discord.com/invite/srcful) for updates on the new integration
- **Issues**: Report bugs with the legacy integration
- **New Integration**: Watch this repo for announcements

## Credits

- Developed for the [Sourceful Energy Zap](https://sourceful.energy/store/sourceful-energy-zap) P1 Reader
- Sourceful Energy Zap is a product of [Sourceful Labs AB](https://sourceful.energy), Kalmar, Sweden 🇸🇪
- Official Sourceful Energy logo used with permission from [Sourceful documentation](https://docs.sourceful.energy/)
- Based on the OBIS (Object Identification System) standard for smart meter data
- Built for Home Assistant integration
- This integration is independently developed and not officially affiliated with Sourceful Labs AB

## Version History

- **0.1.0** (Legacy): Initial release with basic P1 Reader support
  - Support for all standard OBIS codes
  - Energy Dashboard integration
  - Per-phase monitoring capabilities
  - *Note: This version is now in maintenance mode. A new integration is being developed.* 