# Sourceful Energy Zap Home Assistant Custom Component

> **Completed Features & Requirements**

## 1. UI-Only Configuration

- Full **Config Flow** implemented for easy setup via Home Assistant UI
- **Options Flow** implemented for scan interval, endpoints, and device naming
- No YAML configuration required

## 2. Configuration Validation

- Hostname/IP validation
- Scan interval validation (1–3600 seconds)
- Endpoint path validation

## 3. Test Coverage

- Pytest tests added for:
  - Config Flow
  - Options Flow
  - Configuration schema
  - Setup and unload of config entry
- Ensures robust validation and safe integration

## 4. Migration Support

- Detects **existing YAML configuration**
- Provides **migration instructions** for users to move to UI setup
- Documentation updated to reflect new setup process

## 5. Energy Dashboard Integration

- Supports **total import/export sensors** for Home Assistant Energy Dashboard
- All 35+ sensors automatically created from OBIS codes

## Quick Start

1. Add integration via **Home Assistant UI** (no YAML needed)  
2. Configure host, scan interval, and endpoints  
3. Restart Home Assistant  
4. Enjoy automatic creation of sensors and energy dashboard support  

## Development & Testing

To run the integration and tests locally:

```bash
# Start Home Assistant in Docker
docker compose up -d

# Enter Home Assistant container
docker exec -it homeassistant bash

# Install pytest support for custom components
pip install pytest-homeassistant-custom-component

# List available test fixtures
pytest --fixtures | grep hass

# Run tests with short traceback and warnings suppressed
PYTHONPATH=/config pytest --tb=short -p no:warnings
