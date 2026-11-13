# Changelog

All notable changes to the Sourceful Zap Home Assistant integration.

## [1.1.3] - 2026-11-13

### Fixed

- A DER the Zap does not publish to the backend gets its sensors. `enabled` in
  `/ders` is the Zap's publish flag, not whether it reads the DER, and a DER the
  Zap detects starts unpublished. A freshly added inverter therefore showed no
  PV sensors. Sensors are still created only once a value arrives.
- The manual setup form keeps the IP address and polling interval after a
  failed attempt, so a typo can be fixed without typing everything again.

## [1.1.2] - 2026-11-04

### Added

- PV input sensors: MPPT 1 and 2 Voltage, Current and Power, from the `mppt`
  array firmware 7.x sends. Current and power are positive while generating.
- L1-L3 Voltage, Current and Power from the inverter's AC output when the device
  has no grid meter. Current and power are positive while supplying. A grid
  meter on the same device keeps these sensors.

### Changed

- A device sensor is created when its first value arrives, without a reload.
  An inverter with no grid meter no longer gets meter sensors that can never have
  a value, because `/ders` lists a meter it never reads. A sensor that has had a
  value stays, and shows unavailable when the value stops.
- Existing installs: sensors that never had a value stay in Home Assistant until
  you delete them. They are marked as no longer provided.

### Documentation

- README and test docs rewritten. HACS now shows the corrected install steps.
- `hacs.json`: minimum Home Assistant version raised from 2024.1.0 to 2025.2.0,
  the first version that can load this integration.

## [1.1.1] - 2026-11-02

### Fixed

- Sensors get their names. The integration shipped without
  `translations/en.json`, so names fell back to the device class: L1, L2 and
  L3 power were all "Power", four gateway sensors had no name of their own, and
  entity IDs got suffixes such as `_power_2`. Existing installs get the new
  names and keep their entity IDs. New installs also get clean entity IDs. The
  same file carries the config flow text.
- Brand icon added, which HACS validation requires.
- The release zip no longer contains `__pycache__` files.

## [1.1.0] - 2026-11-02

### Added

- Firmware 7.x / Sourceful data model v2. The local REST payloads
  (`/api/devices/{sn}/data/json` and `/api/devices/{sn}/ders`) are detected per
  response from `version: "v2"` or from v2 keys (`solar`, `inverter`,
  `*_ac` / `*_dc`, `soc_nom_fract`). Null ac/dc variants are skipped so the
  populated side is used, and unsuffixed v1 fields are still read when the
  v2 name is absent.
- v2 `solar` maps onto the existing PV sensors. Generation stays negative on
  the wire and positive on the power sensor, matching firmware 2.3.x.
- v2 battery fields (`W_dc`, `soc_nom_fract`, `total_charge_Wh_dc`,
  `total_discharge_Wh_dc`, limits, temperature) map onto the existing battery
  sensors. Sign is unchanged from v1: positive charging, negative discharging.
- v2 grid meters, including a meter that shares a hybrid inverter with solar,
  map onto import/export, per-phase V/A/W, and frequency. A v1 `pv` payload
  still ignores its embedded meter.
- Grid power sensor for v2 hybrids, where aggregate power remains
  solar plus battery. Inverter AC power is its own sensor, positive while
  the inverter is supplying.
- Battery available charge/discharge and meter reactive power sensors when
  the device actually reports them.

### Fixed

- Firmware 2.3.x (data model v1) behaviour is unchanged: `pv` / `W` /
  `L1_W` / `SoC_nom_fract` and the P1 meter still parse as before, and
  `p1_uart` devices still do not get a grid frequency sensor.

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
