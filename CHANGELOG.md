# Changelog

All notable changes to the Sourceful Zap Home Assistant integration.

## [1.0.2] - 2026-08-30

### Fixed

- All config flows now use the gateway serial from `/api/system` as the
  config entry unique ID. Zeroconf previously keyed on the first device's
  serial, so the same gateway discovered via different paths could create
  duplicate entries. Existing entries, the gateway device, and its
  entities migrate automatically on setup and on rediscovery.
- The `last_harvest` sensor attribute is now populated from the newest
  DER read timestamp; the never-populated `connection_status` attribute
  was removed.

## [1.0.1] - 2026-08-30

### Fixed

- Gateway system sensors (uptime, temperature, memory used %, memory free) were
  permanently unavailable on firmware 2.x: `/api/system` emits camelCase field
  names (`uptimeSeconds`, `temperatureCelsius`, `memoryKb.*`) but the
  coordinator read snake_case. The camelCase names are now read first, with
  snake_case kept as a fallback for legacy firmware.
- `grid_frequency` sensor is no longer created for `p1_uart` meters, which
  never report Hz.
- Options flow crashed with `AttributeError` on current Home Assistant
  versions (`OptionsFlow.config_entry` became read-only in HA 2025.12).
- A Zap discovered via zeroconf when already configured now aborts with
  `already_configured` instead of `cannot_connect`.

### Changed

- Coordinators now receive the config entry explicitly
  (`DataUpdateCoordinator(config_entry=...)`), as required by current
  Home Assistant versions.
- Modernized typing throughout (`ConfigFlowResult`, frozen entity
  descriptions); mypy is clean against HA 2026.2.

## [1.0.0] - 2026-01-30

### Added

- Initial release: config flow with zeroconf discovery, per-device
  `DataUpdateCoordinator`, sensors for P1 meters (power, per-phase V/A/W,
  import/export energy), PV, battery, and gateway diagnostics.
