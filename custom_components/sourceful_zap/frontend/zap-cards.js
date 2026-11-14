/*
 * Sourceful Zap cards and dashboard for Home Assistant.
 *
 * The integration serves this file and loads it in the frontend. It has no
 * dependencies and no build step. It defines:
 *
 *   custom:zap-stat-card      a value, a second line and a sparkline
 *   custom:zap-chart-card     lines, an area or energy bars over time
 *   custom:zap-range-picker   a title and one time range for the whole view
 *   custom:zap-heading-card   a title
 *   strategy custom:sourceful-zap   a dashboard built from the Zap's sensors
 *
 * Card options are described in the README.
 */

export const VERSION = "1.2.0";

const DOMAIN = "sourceful_zap";
const MINUTE = 60e3;
const HOUR = 3600e3;
const DAY = 24 * HOUR;
const DEFAULT_RANGE = "24h";
/* Home Assistant keeps raw states and 5-minute statistics about ten days. */
const DETAIL_DAYS = 9;

const Base = globalThis.HTMLElement || class {};

/* ------------------------------------------------------------------ */
/* Text                                                                 */
/* ------------------------------------------------------------------ */

const TEXT = {
  en: {
    range: "Time range",
    custom: "Custom",
    custom_range: "Custom time range",
    from: "From",
    to: "To",
    cancel: "Cancel",
    apply: "Apply",
    err_both: "Enter both from and to.",
    err_order: "To must be at least 5 minutes after from, and not in the future.",
    err_long: "The range can be at most one year.",
    no_data: "No data for this period",
    since: "since",
    per_5min: "per 5 min",
    per_15min: "per 15 min",
    per_hour: "per hour",
    per_day: "per day",
    total: "Total",
    connected: "Connected",
    disconnected: "Disconnected",
    used: "used",
    no_devices: "No Sourceful Zap sensors were found. Add a Zap under Settings, Devices & services.",
    power_now: "Power now",
    power: "Power",
    grid_power: "Grid power",
    inverter_power: "Inverter power",
    battery: "Battery",
    battery_power: "Battery power",
    battery_voltage: "Battery voltage",
    battery_current: "Battery current",
    battery_temperature: "Battery temperature",
    ev_power: "EV charger",
    reactive_power: "Reactive power",
    frequency: "Frequency",
    temperature: "Temperature",
    import_today: "Import today",
    export_today: "Export today",
    production_today: "Production today",
    charged_today: "Charged today",
    discharged_today: "Discharged today",
    import: "Import",
    export: "Export",
    production: "Production",
    charged: "Charged",
    discharged: "Discharged",
    energy: "Energy",
    power_per_phase: "Power per phase",
    current_per_phase: "Current per phase",
    voltage_per_phase: "Voltage per phase",
    power_flows: "Power flows",
    grid: "Grid",
    inverter: "Inverter",
    ev: "EV charger",
    soc: "State of charge",
    mppt_power: "Solar input power",
    mppt_voltage: "Solar input voltage",
    mppt_current: "Solar input current",
    gateway: "Zap gateway",
    firmware: "Firmware",
    uptime: "Uptime",
    wifi_signal: "Wi-Fi signal",
    free_memory: "Free memory",
  },
  sv: {
    range: "Tidsintervall",
    custom: "Eget",
    custom_range: "Eget tidsintervall",
    from: "Från",
    to: "Till",
    cancel: "Avbryt",
    apply: "Använd",
    err_both: "Ange både från och till.",
    err_order: "Till måste vara minst 5 minuter efter från, och inte i framtiden.",
    err_long: "Intervallet får vara högst ett år.",
    no_data: "Ingen data för perioden",
    since: "sedan",
    per_5min: "per 5 min",
    per_15min: "per 15 min",
    per_hour: "per timme",
    per_day: "per dygn",
    total: "Totalt",
    connected: "Ansluten",
    disconnected: "Frånkopplad",
    used: "använt",
    no_devices: "Inga sensorer från Sourceful Zap hittades. Lägg till en Zap under Inställningar, Enheter och tjänster.",
    power_now: "Effekt just nu",
    power: "Effekt",
    grid_power: "Näteffekt",
    inverter_power: "Växelriktareffekt",
    battery: "Batteri",
    battery_power: "Batterieffekt",
    battery_voltage: "Batterispänning",
    battery_current: "Batteriström",
    battery_temperature: "Batteritemperatur",
    ev_power: "Elbilsladdare",
    reactive_power: "Reaktiv effekt",
    frequency: "Frekvens",
    temperature: "Temperatur",
    import_today: "Import idag",
    export_today: "Export idag",
    production_today: "Produktion idag",
    charged_today: "Laddat idag",
    discharged_today: "Urladdat idag",
    import: "Import",
    export: "Export",
    production: "Produktion",
    charged: "Laddat",
    discharged: "Urladdat",
    energy: "Energi",
    power_per_phase: "Effekt per fas",
    current_per_phase: "Ström per fas",
    voltage_per_phase: "Spänning per fas",
    power_flows: "Effektflöden",
    grid: "Nät",
    inverter: "Växelriktare",
    ev: "Elbilsladdare",
    soc: "Laddnivå",
    mppt_power: "Effekt per solingång",
    mppt_voltage: "Spänning per solingång",
    mppt_current: "Ström per solingång",
    gateway: "Zap-gateway",
    firmware: "Firmware",
    uptime: "Drifttid",
    wifi_signal: "Wi-Fi-signal",
    free_memory: "Ledigt minne",
  },
};

export function language(hass) {
  return String((hass && ((hass.locale && hass.locale.language) || hass.language)) || "en");
}

export function text(hass, key) {
  const table = TEXT[language(hass).split("-")[0]] || TEXT.en;
  return table[key] !== undefined ? table[key] : TEXT.en[key] !== undefined ? TEXT.en[key] : key;
}

function formatNumber(hass, value, decimals) {
  try {
    return new Intl.NumberFormat(language(hass), {
      minimumFractionDigits: decimals, maximumFractionDigits: decimals,
    }).format(value);
  } catch (err) {
    return value.toFixed(decimals);
  }
}

/* Home Assistant's own 12 or 24 hour setting, when the user has chosen one. */
function hour12(hass) {
  const setting = hass && hass.locale && hass.locale.time_format;
  if (setting === "12") return true;
  if (setting === "24") return false;
  return undefined;
}

function formatDate(hass, ms, options) {
  try {
    return new Intl.DateTimeFormat(language(hass), { hour12: hour12(hass), ...options }).format(new Date(ms));
  } catch (err) {
    return new Date(ms).toLocaleString();
  }
}

const CLOCK = { hour: "2-digit", minute: "2-digit" };
const DAY_MONTH = { day: "numeric", month: "short" };

/* ------------------------------------------------------------------ */
/* Small helpers                                                        */
/* ------------------------------------------------------------------ */

function el(tag, cls, content) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (content !== undefined) node.textContent = content;
  return node;
}

function svg(tag, attrs) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
  return node;
}

function moreInfo(node, entityId) {
  node.dispatchEvent(new CustomEvent("hass-more-info", {
    bubbles: true, composed: true, detail: { entityId },
  }));
}

/* ------------------------------------------------------------------ */
/* Colors                                                               */
/* ------------------------------------------------------------------ */

/*
 * One palette, stepped for light and for dark surfaces. A series names a slot
 * and keeps it everywhere, so L1 is the same blue in every chart.
 */
const PALETTE = {
  light: {
    blue: "#2a78d6", orange: "#eb6834", aqua: "#1baf7a", yellow: "#eda100",
    magenta: "#e87ba4", green: "#008300", violet: "#6250d6", red: "#e34948", neutral: "#898781",
  },
  dark: {
    blue: "#3987e5", orange: "#d95926", aqua: "#199e70", yellow: "#c98500",
    magenta: "#d55181", green: "#008300", violet: "#9085e9", red: "#e66767", neutral: "#8e909c",
  },
};
const SLOTS = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"];

export function seriesColor(color, index, dark) {
  const palette = dark ? PALETTE.dark : PALETTE.light;
  if (color && palette[color]) return palette[color];
  if (color) return color;
  return palette[SLOTS[index % SLOTS.length]];
}

/*
 * `appearance: zap` gives a card its own dark panel look, whatever theme Home
 * Assistant uses. It redefines the theme variables the card reads.
 */
const APPEARANCE_STYLE = `
  :host([zap]) {
    --ha-card-background: #181b1f;
    --card-background-color: #181b1f;
    --ha-card-border-radius: 4px;
    --ha-card-border-width: 1px;
    --ha-card-border-color: rgba(204, 204, 220, 0.12);
    --ha-card-box-shadow: none;
    --primary-background-color: #111217;
    --primary-text-color: #d5d6e0;
    --secondary-text-color: #9fa1ae;
    --divider-color: rgba(204, 204, 220, 0.12);
    --primary-color: #6e9fff;
    color-scheme: dark;
  }
`;
const FONT = 'var(--ha-font-family-body, system-ui, -apple-system, "Segoe UI", sans-serif)';
const WARNING_ICON = "M12 2 1 21h22L12 2Zm1 15h-2v-2h2v2Zm0-4h-2V9h2v4Z";
const GOOD_ICON = "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm-1.6 14.6-4-4 1.4-1.4 2.6 2.6 5.8-5.8 1.4 1.4-7.2 7.2Z";

function isDark(card) {
  if (card._config && card._config.appearance === "zap") return true;
  const hass = card._hass;
  return Boolean(hass && hass.themes && hass.themes.darkMode);
}

/* ------------------------------------------------------------------ */
/* Units                                                                */
/* ------------------------------------------------------------------ */

const UNITS = {
  mW: ["power", 1e-3], W: ["power", 1], kW: ["power", 1e3], MW: ["power", 1e6], GW: ["power", 1e9],
  Wh: ["energy", 1], kWh: ["energy", 1e3], MWh: ["energy", 1e6], GWh: ["energy", 1e9],
};

/* What to multiply a value in `from` with to get it in `to`. 1 when the units are not related. */
export function unitFactor(from, to) {
  const a = UNITS[from];
  const b = UNITS[to];
  if (!a || !b || a[0] !== b[0]) return 1;
  return a[1] / b[1];
}

function stateUnit(hass, entity) {
  const state = hass && hass.states[entity];
  return (state && state.attributes && state.attributes.unit_of_measurement) || "";
}

function numericState(hass, entity) {
  const state = hass && hass.states[entity];
  if (!state || state.state === "unavailable" || state.state === "unknown" || state.state === "") return null;
  const value = Number(state.state);
  return Number.isFinite(value) ? value : null;
}

/* ------------------------------------------------------------------ */
/* Time range, shared by every card of a view                           */
/* ------------------------------------------------------------------ */

export function hoursOf(key) {
  const match = /^(\d+)([hd])$/.exec(String(key));
  if (!match) return NaN;
  return Number(match[1]) * (match[2] === "d" ? 24 : 1);
}

function storage(kind) {
  try { return globalThis[kind] || null; } catch (err) { return null; }
}

/*
 * The chosen range: a preset such as "24h", or "custom" with a from and a to.
 * A preset is remembered in this browser. A custom range is fixed in time, so
 * it only lasts for the tab's session and a later visit starts on the preset.
 */
export const range = {
  storageKey: "zap-dashboard-range",
  customKey: "zap-dashboard-range-custom",
  value: null,
  custom: null,
  listeners: new Set(),
  _read(kind, key) {
    try { return storage(kind).getItem(key); } catch (err) { return null; }
  },
  _write(kind, key, value) {
    try {
      if (value === null) storage(kind).removeItem(key);
      else storage(kind).setItem(key, value);
    } catch (err) { /* private mode */ }
  },
  get() {
    if (this.value === null) {
      const stored = this._read("localStorage", this.storageKey);
      this.value = Number.isFinite(hoursOf(stored)) ? stored : DEFAULT_RANGE;
      const [from, to] = String(this._read("sessionStorage", this.customKey) || "").split(":").map(Number);
      if (Number.isFinite(from) && Number.isFinite(to) && to > from) {
        this.custom = { from, to };
        this.value = "custom";
      }
    }
    return this.value;
  },
  isCustom() {
    return this.get() === "custom" && Boolean(this.custom);
  },
  hours() {
    if (this.isCustom()) return (this.custom.to - this.custom.from) / HOUR;
    return hoursOf(this.get());
  },
  set(value) {
    if (!Number.isFinite(hoursOf(value)) || (value === this.get() && !this.isCustom())) return;
    this.value = value;
    this.custom = null;
    this._write("localStorage", this.storageKey, value);
    this._write("sessionStorage", this.customKey, null);
    this._notify();
  },
  setCustom(from, to) {
    if (!Number.isFinite(from) || !Number.isFinite(to) || to <= from) return;
    this.get();
    this.custom = { from, to };
    this.value = "custom";
    this._write("sessionStorage", this.customKey, `${from}:${to}`);
    this._notify();
  },
  _notify() {
    for (const listener of [...this.listeners]) listener(this.value);
  },
};

/* The window a card shows: the shared range, or the card's own `hours`. */
function windowOf(hours) {
  if (hours === undefined || hours === "range") {
    if (range.isCustom()) return { start: range.custom.from, end: range.custom.to, fixed: true };
    const end = Date.now();
    return { start: end - (range.hours() || 24) * HOUR, end, fixed: false };
  }
  const end = Date.now();
  const length = Number(hours);
  return { start: end - (Number.isFinite(length) && length > 0 ? length : 1) * HOUR, end, fixed: false };
}

/* The time under the pointer, shared by every chart of a view. */
const hover = {
  listeners: new Set(),
  source: null,
  set(state, source) {
    this.source = state ? source : null;
    for (const listener of [...this.listeners]) listener(state);
  },
  clear(source) {
    if (this.source === source) this.set(null, null);
  },
};

/* ------------------------------------------------------------------ */
/* Data                                                                 */
/* ------------------------------------------------------------------ */

/* Where a line of mean values comes from: raw states, or recorder statistics. */
export function meanSource(start, end, now = Date.now()) {
  const hours = (end - start) / HOUR;
  if ((now - start) / DAY > DETAIL_DAYS) return "hour";
  if (hours <= 6) return "history";
  return hours <= 72 ? "5minute" : "hour";
}

/*
 * How energy bars are cut: the bar width, and the statistics to sum into it.
 * Finer statistics than the bar let the newest bar grow before its period ends.
 */
export function barPlan(start, end, now = Date.now()) {
  const hours = (end - start) / HOUR;
  const detail = (now - start) / DAY <= DETAIL_DAYS;
  if (detail && hours <= 3) return { period: "5minute", bucket: 5 * MINUTE, label: "per_5min" };
  if (detail && hours <= 12) return { period: "5minute", bucket: 15 * MINUTE, label: "per_15min" };
  if (hours <= 72) return { period: detail ? "5minute" : "hour", bucket: HOUR, label: "per_hour" };
  return { period: "hour", bucket: DAY, label: "per_day" };
}

function fetchHistory(hass, entity, start, end) {
  return hass.callWS({
    type: "history/history_during_period",
    start_time: new Date(start).toISOString(),
    end_time: new Date(end).toISOString(),
    entity_ids: [entity],
    minimal_response: true,
    no_attributes: true,
    significant_changes_only: false,
  }).then((result) => {
    const points = [];
    for (const row of (result && result[entity]) || []) {
      const value = Number(row.s);
      if (row.s !== "" && row.s !== null && Number.isFinite(value)) points.push({ t: row.lu * 1000, v: value });
    }
    return points;
  });
}

/* Statistics come back in the entity's current unit, like its states. */
function fetchStatistics(hass, entity, start, end, period, type) {
  return hass.callWS({
    type: "recorder/statistics_during_period",
    start_time: new Date(start).toISOString(),
    end_time: new Date(end).toISOString(),
    statistic_ids: [entity],
    period,
    types: [type],
  }).then((result) => {
    const rows = [];
    for (const row of (result && result[entity]) || []) {
      const value = row[type];
      if (value !== null && value !== undefined && Number.isFinite(Number(value))) {
        rows.push({ t0: Number(row.start), t1: Number(row.end), v: Number(value) });
      }
    }
    return rows;
  });
}

/*
 * A line for [start, end]: points {t, v} in the entity's unit.
 *
 * Statistics end at the last full period, and a new install has none yet.
 * Raw states fill in what is newer, so the line always reaches the present.
 */
function fetchMean(hass, entity, start, end) {
  const source = meanSource(start, end);
  if (source === "history") return fetchHistory(hass, entity, start, end).then((points) => ({ source, points }));
  return fetchStatistics(hass, entity, start, end, source, "mean").then((rows) => {
    const points = rows.map((row) => ({ t: (row.t0 + row.t1) / 2, v: row.v }));
    const covered = rows.length ? rows[rows.length - 1].t1 : Math.max(start, end - DAY);
    if (end - covered <= MINUTE || Date.now() - covered > DETAIL_DAYS * DAY) return { source, points };
    return fetchHistory(hass, entity, covered, end)
      .then((tail) => ({ source, points: [...points, ...tail.filter((p) => p.t > covered)] }))
      .catch(() => ({ source, points }));
  });
}

/* Sum statistics rows into buckets of `bucket` ms, aligned to local midnight. */
export function sumBuckets(rows, bucket) {
  const out = [];
  for (const row of rows) {
    if (row.t1 - row.t0 >= bucket - 1) { out.push({ ...row }); continue; }
    const midnight = new Date(row.t0);
    midnight.setHours(0, 0, 0, 0);
    const t0 = midnight.getTime() + Math.floor((row.t0 - midnight.getTime()) / bucket) * bucket;
    const last = out[out.length - 1];
    if (last && last.t0 === t0) last.v += row.v;
    else out.push({ t0, t1: t0 + bucket, v: row.v });
  }
  return out;
}

/* Average points into at most `max` equal buckets over [start, end]. */
export function downsample(points, start, end, max) {
  if (points.length <= max) return points;
  const width = (end - start) / max;
  const out = [];
  let count = 0;
  let sumT = 0;
  let sumV = 0;
  let edge = start + width;
  const flush = () => {
    if (count) out.push({ t: sumT / count, v: sumV / count });
    count = 0; sumT = 0; sumV = 0;
  };
  for (const point of points) {
    while (point.t > edge) { flush(); edge += width; }
    count += 1; sumT += point.t; sumV += point.v;
  }
  flush();
  return out;
}

/*
 * Split a line where the data stops for much longer than usual, so an outage
 * shows as a gap. `spacing` is how far apart the source's points normally are:
 * statistics come every 5 minutes or every hour, with newer raw states after them.
 */
export function splitGaps(points, spacing = 0) {
  if (points.length < 3) return [points];
  const steps = [];
  for (let i = 1; i < points.length; i += 1) steps.push(points[i].t - points[i - 1].t);
  steps.sort((a, b) => a - b);
  const limit = Math.max(steps[Math.floor(steps.length / 2)] * 4, spacing * 3, 2 * MINUTE);
  const parts = [];
  let part = [points[0]];
  for (let i = 1; i < points.length; i += 1) {
    if (points[i].t - points[i - 1].t > limit) { parts.push(part); part = []; }
    part.push(points[i]);
  }
  parts.push(part);
  return parts;
}

/* ------------------------------------------------------------------ */
/* Scales                                                               */
/* ------------------------------------------------------------------ */

/* A y axis with round steps that covers [lo, hi]. */
export function niceScale(lo, hi, target = 4) {
  if (!Number.isFinite(lo) || !Number.isFinite(hi)) { lo = 0; hi = 1; }
  if (hi < lo) [lo, hi] = [hi, lo];
  if (hi === lo) {
    const pad = Math.abs(hi) > 0 ? Math.abs(hi) * 0.1 : 1;
    hi += pad;
    if (lo !== 0) lo -= pad;
  }
  const rough = (hi - lo) / target;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const unit = rough / magnitude;
  const step = (unit <= 1 ? 1 : unit <= 2 ? 2 : unit <= 5 ? 5 : 10) * magnitude;
  const decimals = Math.max(0, Math.ceil(-Math.log10(step) - 1e-9));
  const round = (value) => Number(value.toFixed(Math.min(12, decimals + 2)));
  const min = round(Math.floor(lo / step + 1e-9) * step);
  const max = round(Math.ceil(hi / step - 1e-9) * step);
  const ticks = [];
  for (let i = 0; min + i * step <= max + step * 1e-6; i += 1) ticks.push(round(min + i * step));
  return { min, max, step, ticks, decimals: Math.min(decimals, 6) };
}

const TICK_STEPS = [
  5 * MINUTE, 10 * MINUTE, 15 * MINUTE, 30 * MINUTE, HOUR, 2 * HOUR, 3 * HOUR, 6 * HOUR, 12 * HOUR,
  DAY, 2 * DAY, 7 * DAY, 14 * DAY, 30 * DAY, 90 * DAY,
];

/* Tick times for a time axis, on round local clock times. `major` marks a new day. */
export function timeTicks(start, end, width) {
  const room = Math.max(2, Math.floor(width / 68));
  const step = TICK_STEPS.find((candidate) => (end - start) / candidate <= room) || TICK_STEPS[TICK_STEPS.length - 1];
  const ticks = [];
  const cursor = new Date(start);
  if (step >= DAY) {
    const days = Math.round(step / DAY);
    cursor.setHours(0, 0, 0, 0);
    if (cursor.getTime() < start) cursor.setDate(cursor.getDate() + 1);
    for (let guard = 0; cursor.getTime() <= end && guard < 400; guard += 1) {
      ticks.push({ t: cursor.getTime(), major: true });
      cursor.setDate(cursor.getDate() + days);
    }
    return { step, ticks };
  }
  cursor.setHours(0, 0, 0, 0);
  if (step >= HOUR) {
    // Step in local hours, so the labels stay on round hours across a daylight saving change.
    const hours = Math.round(step / HOUR);
    for (let guard = 0; cursor.getTime() <= end && guard < 2000; guard += 1) {
      if (cursor.getTime() >= start) ticks.push({ t: cursor.getTime(), major: cursor.getHours() === 0 });
      cursor.setHours(cursor.getHours() + hours);
    }
    return { step, ticks };
  }
  let t = cursor.getTime() + Math.ceil((start - cursor.getTime()) / step) * step;
  for (let guard = 0; t <= end && guard < 2000; guard += 1, t += step) {
    const at = new Date(t);
    ticks.push({ t, major: at.getHours() === 0 && at.getMinutes() === 0 });
  }
  return { step, ticks };
}

/* ------------------------------------------------------------------ */
/* zap-heading-card and zap-range-picker                                */
/* ------------------------------------------------------------------ */

const HEADING_STYLE = `
  ${APPEARANCE_STYLE}
  :host { display: block; position: relative; height: 100%; container-type: inline-size; }
  .row {
    display: flex; align-items: flex-end; gap: 10px;
    min-height: 36px; box-sizing: border-box; padding: 4px 0 2px;
  }
  .title {
    flex: 1 1 auto; min-width: 0; display: flex; align-items: center; gap: 8px;
    color: var(--primary-text-color); font: 500 16px/30px ${FONT};
  }
  .title span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .title ha-icon { flex: none; --mdc-icon-size: 20px; color: var(--secondary-text-color); }
  .chosen {
    min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    color: var(--secondary-text-color); font: 12px/30px ${FONT};
  }
  .seg {
    flex: none; display: inline-flex; border: 1px solid var(--divider-color); border-radius: 4px; overflow: hidden;
    background: var(--ha-card-background, var(--card-background-color));
  }
  .seg button {
    appearance: none; border: 0; margin: 0; padding: 0 12px; height: 30px; min-width: 44px; cursor: pointer;
    background: transparent; color: var(--secondary-text-color); font: 500 13px/30px ${FONT}; white-space: nowrap;
  }
  .seg button + button { border-left: 1px solid var(--divider-color); }
  .seg button:hover { background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); }
  button:focus-visible, input:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
  .seg button[aria-checked="true"] {
    background: color-mix(in srgb, var(--primary-color) 18%, transparent); color: var(--primary-text-color);
  }
  .panel {
    position: fixed; inset: auto; margin: 0; padding: 12px; width: 272px; box-sizing: border-box;
    background: var(--ha-card-background, var(--card-background-color)); color: var(--primary-text-color);
    border: 1px solid var(--divider-color); border-radius: 4px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    font: 13px/18px ${FONT};
  }
  .panel.fallback { display: none; position: absolute; right: 0; top: calc(100% + 6px); z-index: 9; }
  .panel.fallback.open { display: block; }
  .panel label { display: grid; gap: 4px; margin-bottom: 10px; color: var(--secondary-text-color); font-size: 12px; }
  .panel input {
    height: 32px; padding: 0 8px; box-sizing: border-box; width: 100%;
    border: 1px solid var(--divider-color); border-radius: 3px;
    background: var(--primary-background-color); color: var(--primary-text-color); font: 13px/30px ${FONT};
  }
  .error { display: none; align-items: flex-start; gap: 6px; margin-bottom: 10px; font-size: 12px; line-height: 16px; }
  .error.on { display: flex; }
  .error svg { flex: none; width: 14px; height: 14px; margin-top: 1px; fill: #fab219; }
  .actions { display: flex; justify-content: flex-end; gap: 8px; }
  .actions button {
    appearance: none; height: 30px; padding: 0 12px; cursor: pointer; border-radius: 3px;
    border: 1px solid var(--divider-color); background: transparent; color: var(--primary-text-color);
    font: 500 13px/28px ${FONT};
  }
  .actions button:hover { background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); }
  .actions button.primary {
    border-color: var(--primary-color); background: color-mix(in srgb, var(--primary-color) 18%, transparent);
  }
  @container (max-width: 520px) {
    .row { flex-wrap: wrap; row-gap: 4px; }
    .title { flex-basis: 100%; }
    .seg { display: flex; flex: 1 1 100%; }
    .seg button { flex: 1; padding: 0 4px; min-width: 0; }
  }
`;

function toLocalInput(ms) {
  const d = new Date(ms);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

class ZapHeadingCard extends Base {
  setConfig(config) {
    this._config = { ...(config || {}) };
    this.toggleAttribute("zap", this._config.appearance === "zap");
    if (this.shadowRoot) this._render();
  }

  set hass(hass) {
    const fresh = !this._hass || language(this._hass) !== language(hass);
    this._hass = hass;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._render();
    } else if (fresh) {
      this._render();
    }
  }

  getCardSize() { return 1; }

  getGridOptions() {
    return { columns: "full", rows: "auto" };
  }

  static getStubConfig() {
    return { title: "Sourceful Zap", icon: "mdi:lightning-bolt-circle" };
  }

  _title() {
    const title = el("div", "title");
    if (this._config.icon) {
      const icon = document.createElement("ha-icon");
      icon.setAttribute("icon", this._config.icon);
      title.append(icon);
    }
    title.append(el("span", null, this._config.title || ""));
    return title;
  }

  _render() {
    const root = this.shadowRoot;
    root.textContent = "";
    // Without a title the card is an empty row: it starts the next cards on a new line.
    if (!this._config.title && !this._config.icon) return;
    const row = el("div", "row");
    row.append(this._title());
    root.append(el("style", null, HEADING_STYLE), row);
  }
}

class ZapRangePicker extends ZapHeadingCard {
  setConfig(config) {
    const merged = { options: ["1h", "6h", "24h", "7d", "30d"], default: DEFAULT_RANGE, custom: true, ...(config || {}) };
    if (!Array.isArray(merged.options) || !merged.options.length) {
      throw new Error("zap-range-picker: options must list at least one range");
    }
    const bad = merged.options.find((option) => !Number.isFinite(hoursOf(option)));
    if (bad !== undefined) throw new Error(`zap-range-picker: "${bad}" is not a range like 6h or 7d`);
    super.setConfig(merged);
    if (!range.isCustom() && !merged.options.includes(range.get())) {
      range.set(merged.options.includes(merged.default) ? merged.default : merged.options[0]);
    }
  }

  static getStubConfig() {
    return { title: "Sourceful Zap", icon: "mdi:lightning-bolt-circle" };
  }

  connectedCallback() {
    this._onRange = () => this._mark();
    range.listeners.add(this._onRange);
    this._mark();
  }

  disconnectedCallback() {
    range.listeners.delete(this._onRange);
    this._close();
  }

  _label(option) {
    const labels = this._config.labels || {};
    if (labels[option]) return labels[option];
    const match = /^(\d+)([hd])$/.exec(option);
    return `${match[1]} ${match[2]}`;
  }

  _render() {
    const root = this.shadowRoot;
    root.textContent = "";
    root.append(el("style", null, HEADING_STYLE));
    const row = el("div", "row");
    this._chosen = el("span", "chosen");
    const seg = el("div", "seg");
    seg.setAttribute("role", "radiogroup");
    seg.setAttribute("aria-label", text(this._hass, "range"));
    for (const option of this._config.options) {
      const button = el("button", null, this._label(option));
      button.type = "button";
      button.dataset.range = option;
      button.setAttribute("role", "radio");
      button.addEventListener("click", () => { this._close(); range.set(option); });
      seg.append(button);
    }
    this._customButton = null;
    if (this._config.custom) {
      const button = el("button", null, text(this._hass, "custom"));
      button.type = "button";
      button.dataset.range = "custom";
      button.setAttribute("role", "radio");
      button.setAttribute("aria-haspopup", "dialog");
      button.addEventListener("click", () => this._toggle());
      seg.append(button);
      this._customButton = button;
    }
    seg.addEventListener("keydown", (ev) => {
      const step = ev.key === "ArrowRight" ? 1 : ev.key === "ArrowLeft" ? -1 : 0;
      if (!step || range.isCustom()) return;
      const options = this._config.options;
      const next = options[(options.indexOf(range.get()) + step + options.length) % options.length];
      range.set(next);
      const button = seg.querySelector(`button[data-range="${next}"]`);
      if (button) button.focus();
      ev.preventDefault();
    });
    row.append(this._title(), this._chosen, seg);
    root.append(row);
    this._panel = null;
    if (this._config.custom) root.append(this._buildPanel());
    this._mark();
  }

  _buildPanel() {
    const panel = el("form", "panel");
    panel.setAttribute("aria-label", text(this._hass, "custom_range"));
    this._native = typeof panel.showPopover === "function";
    if (this._native) panel.setAttribute("popover", "auto");
    else panel.classList.add("fallback");

    const field = (label) => {
      const wrap = el("label", null, label);
      const input = el("input");
      input.type = "datetime-local";
      input.required = true;
      wrap.append(input);
      return { wrap, input };
    };
    const from = field(text(this._hass, "from"));
    const to = field(text(this._hass, "to"));
    this._from = from.input;
    this._to = to.input;

    this._error = el("div", "error");
    this._error.setAttribute("role", "alert");
    const icon = svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" });
    icon.append(svg("path", { d: WARNING_ICON }));
    this._errorText = el("span");
    this._error.append(icon, this._errorText);

    const actions = el("div", "actions");
    const cancel = el("button", null, text(this._hass, "cancel"));
    cancel.type = "button";
    cancel.addEventListener("click", () => this._close());
    const apply = el("button", "primary", text(this._hass, "apply"));
    apply.type = "submit";
    actions.append(cancel, apply);

    panel.append(from.wrap, to.wrap, this._error, actions);
    panel.addEventListener("submit", (ev) => { ev.preventDefault(); this._apply(); });
    panel.addEventListener("keydown", (ev) => { if (ev.key === "Escape") this._close(); });
    panel.addEventListener("toggle", () => this._mark());
    this._panel = panel;
    return panel;
  }

  get _open() {
    if (!this._panel) return false;
    if (!this._native) return this._panel.classList.contains("open");
    try { return this._panel.matches(":popover-open"); } catch (err) { return false; }
  }

  _toggle() {
    if (this._open) { this._close(); return; }
    const now = Math.floor(Date.now() / MINUTE) * MINUTE;
    const current = range.isCustom() ? range.custom : { from: now - (range.hours() || 24) * HOUR, to: now };
    this._from.value = toLocalInput(current.from);
    this._to.value = toLocalInput(current.to);
    this._from.max = toLocalInput(now);
    this._to.max = toLocalInput(now);
    this._fail("");
    if (this._native) {
      // The top layer is not clipped by the dashboard grid. Place it under the button.
      const box = this._customButton.getBoundingClientRect();
      const width = 272;
      this._panel.style.left = `${Math.max(8, Math.min(window.innerWidth - width - 8, box.right - width))}px`;
      this._panel.style.top = `${box.bottom + 6}px`;
      this._panel.showPopover();
    } else {
      this._panel.classList.add("open");
    }
    this._from.focus();
    this._mark();
  }

  _close() {
    if (!this._panel || !this._open) return;
    if (this._native) this._panel.hidePopover();
    else this._panel.classList.remove("open");
    this._mark();
  }

  _fail(message) {
    this._errorText.textContent = message;
    this._error.classList.toggle("on", Boolean(message));
  }

  _apply() {
    const from = new Date(this._from.value).getTime();
    let to = new Date(this._to.value).getTime();
    if (!Number.isFinite(from) || !Number.isFinite(to)) { this._fail(text(this._hass, "err_both")); return; }
    to = Math.min(to, Math.floor(Date.now() / MINUTE) * MINUTE);
    if (to - from < 5 * MINUTE) { this._fail(text(this._hass, "err_order")); return; }
    if (to - from > 366 * DAY) { this._fail(text(this._hass, "err_long")); return; }
    this._close();
    range.setCustom(from, to);
  }

  _mark() {
    if (!this.shadowRoot) return;
    const custom = range.isCustom();
    for (const button of this.shadowRoot.querySelectorAll(".seg button")) {
      const on = custom ? button.dataset.range === "custom" : button.dataset.range === range.get();
      button.setAttribute("aria-checked", on ? "true" : "false");
      button.tabIndex = on ? 0 : -1;
    }
    if (this._customButton) this._customButton.setAttribute("aria-expanded", this._open ? "true" : "false");
    if (this._chosen) {
      const stamp = (ms) => formatDate(this._hass, ms, { ...DAY_MONTH, ...CLOCK });
      this._chosen.textContent = custom ? `${stamp(range.custom.from)} – ${stamp(range.custom.to)}` : "";
    }
  }
}

/* ------------------------------------------------------------------ */
/* zap-stat-card                                                        */
/* ------------------------------------------------------------------ */

const REFETCH_MS = 5 * MINUTE;
const SPARK_POINTS = 160;

const STAT_STYLE = `
  ${APPEARANCE_STYLE}
  :host { display: block; height: 100%; }
  ha-card {
    position: relative; height: 100%; box-sizing: border-box; overflow: hidden;
    display: flex; flex-direction: column;
    padding: 10px 14px 0; cursor: pointer; font-family: ${FONT};
  }
  ha-card:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
  .label {
    display: flex; align-items: center; gap: 6px; min-width: 0;
    color: var(--secondary-text-color); font-size: 13px; font-weight: 500; line-height: 18px; white-space: nowrap;
  }
  .label span:last-child { overflow: hidden; text-overflow: ellipsis; }
  .key { flex: none; width: 12px; height: 3px; border-radius: 2px; background: var(--zap-series); }
  .value {
    margin-top: 2px; color: var(--primary-text-color); font-size: 28px; font-weight: 600; line-height: 34px;
    white-space: nowrap; letter-spacing: -0.01em;
  }
  :host([hero]) .value { font-size: 48px; line-height: 52px; letter-spacing: -0.02em; }
  .unit { margin-left: 4px; color: var(--secondary-text-color); font-size: 0.5em; font-weight: 500; letter-spacing: 0; }
  :host([hero]) .unit { font-size: 0.4em; }
  .secondary {
    display: flex; flex-wrap: wrap; align-items: center; column-gap: 6px;
    color: var(--secondary-text-color); font-size: 12px; line-height: 16px;
  }
  .secondary .item { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
  .secondary.inline .item:not(:last-child)::after { content: "·"; margin-left: 2px; opacity: 0.7; }
  .secondary.rows { display: grid; grid-template-columns: max-content max-content; column-gap: 12px; margin-top: 2px; }
  .secondary.rows .item { display: contents; }
  .secondary.rows .fig { color: var(--primary-text-color); text-align: right; font-variant-numeric: tabular-nums; }
  .secondary svg { width: 13px; height: 13px; flex: none; }
  .secondary .good svg { fill: #0ca30c; }
  .secondary .warning svg { fill: #fab219; }
  .spark { position: relative; flex: 1 1 0; min-height: 20px; margin: 4px -14px 0; }
  .spark svg { position: absolute; left: 0; top: 0; width: 100%; height: 100%; overflow: visible; }
  .line { fill: none; stroke: var(--zap-series); stroke-width: 1.5; stroke-linejoin: round; stroke-linecap: round; }
  .wash { fill: var(--zap-series); opacity: 0.12; stroke: none; }
  .dot { fill: var(--zap-series); stroke: var(--ha-card-background, var(--card-background-color)); stroke-width: 2; }
  .cross { stroke: var(--secondary-text-color); stroke-width: 1; opacity: 0.6; }
  .tip {
    position: absolute; z-index: 3; top: 6px; pointer-events: none; display: none;
    padding: 3px 7px; border-radius: 3px; white-space: nowrap;
    background: var(--primary-background-color); border: 1px solid var(--divider-color);
    color: var(--secondary-text-color); font-size: 11px; line-height: 15px;
  }
  .tip b { color: var(--primary-text-color); font-weight: 600; margin-right: 6px; }
`;

class ZapStatCard extends Base {
  setConfig(config) {
    if (!config || !config.entity) throw new Error("zap-stat-card: entity is required");
    this._config = {
      mode: "state", decimals: 0, hours: 1, graph: true, zero: false,
      hero: false, key: false, secondary: [], secondary_layout: "inline", ...config,
    };
    if (!["state", "today", "duration", "text"].includes(this._config.mode)) {
      throw new Error(`zap-stat-card: mode "${this._config.mode}" is not state, today, duration or text`);
    }
    this._reset();
    this._base = undefined;
    this._baseDay = undefined;
    this._baseSince = undefined;
    this.toggleAttribute("hero", Boolean(this._config.hero));
    this.toggleAttribute("zap", this._config.appearance === "zap");
    if (this.shadowRoot) this._build();
  }

  getCardSize() { return 2; }

  getGridOptions() {
    return { columns: 6, rows: 2, min_columns: 3, min_rows: 2 };
  }

  static getStubConfig(hass) {
    const entity = Object.keys((hass && hass.states) || {})
      .find((id) => id.startsWith("sensor.") && hass.states[id].attributes.device_class === "power");
    return { entity: entity || "sensor.example", zero: true };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._build();
    }
    this._text();
    this._live();
    this._fetchIfDue();
  }

  connectedCallback() {
    if (!this._resize && typeof ResizeObserver !== "undefined") {
      this._resize = new ResizeObserver(() => this._draw());
    }
    if (this._resize && this._spark) this._resize.observe(this._spark);
    this._onRange = () => {
      if (this._config.hours !== "range") return;
      this._reset();
      this._draw();
      if (this._hass) this._fetchIfDue();
    };
    range.listeners.add(this._onRange);
  }

  disconnectedCallback() {
    if (this._resize) this._resize.disconnect();
    range.listeners.delete(this._onRange);
  }

  _reset() {
    this._points = [];
    this._fetched = 0;
    this._fetchId = (this._fetchId || 0) + 1;
    this._fetching = false;
    this._lastSeen = undefined;
  }

  get _hasGraph() {
    return this._config.graph && this._config.mode === "state";
  }

  _unit() {
    if (this._config.unit !== undefined) return this._config.unit;
    return stateUnit(this._hass, this._config.entity);
  }

  /* From the entity's unit to the shown unit. */
  _factor() {
    return unitFactor(stateUnit(this._hass, this._config.entity), this._unit());
  }

  _build() {
    const root = this.shadowRoot;
    root.textContent = "";
    root.append(el("style", null, STAT_STYLE));
    const card = el("ha-card");
    card.tabIndex = 0;
    card.setAttribute("role", "button");

    const label = el("div", "label");
    if (this._config.key) label.append(el("span", "key"));
    this._labelText = el("span", null, "");
    label.append(this._labelText);
    this._value = el("div", "value");
    this._secondary = el("div", "secondary");
    card.append(label, this._value, this._secondary);

    this._spark = null;
    if (this._hasGraph) {
      this._spark = el("div", "spark");
      this._tip = el("div", "tip");
      card.append(this._spark, this._tip);
      card.addEventListener("pointermove", (ev) => this._hover(ev));
      card.addEventListener("pointerleave", () => this._hover(null));
      if (this._resize) this._resize.observe(this._spark);
    }
    card.addEventListener("click", () => moreInfo(this, this._config.entity));
    card.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); moreInfo(this, this._config.entity); }
    });
    this._card = card;
    root.append(card);
  }

  _duration(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d} d ${h} h`;
    if (h > 0) return `${h} h ${m} min`;
    return `${m} min`;
  }

  _text() {
    const cfg = this._config;
    const hass = this._hass;
    const state = hass.states[cfg.entity];
    const name = cfg.name || (state && state.attributes.friendly_name) || cfg.entity;
    this._labelText.textContent = name;
    this._card.style.setProperty("--zap-series", seriesColor(cfg.color || "neutral", 0, isDark(this)));

    let shown = "–";
    let unit = "";
    const raw = state ? state.state : undefined;
    const usable = state && raw !== "unavailable" && raw !== "unknown" && raw !== "";
    const number = numericState(hass, cfg.entity);
    if (usable && cfg.mode === "text") {
      shown = String(raw);
    } else if (cfg.mode === "duration" && number !== null) {
      shown = this._duration(number);
    } else if (cfg.mode === "today" && number !== null) {
      if (this._base !== undefined) {
        shown = formatNumber(hass, Math.max(0, number - this._base) * this._factor(), cfg.decimals);
        unit = this._unit();
      }
    } else if (cfg.mode === "state" && number !== null) {
      shown = formatNumber(hass, number * this._factor(), cfg.decimals);
      unit = this._unit();
    }
    this._value.textContent = shown;
    if (unit) this._value.append(el("span", "unit", unit));
    this._card.setAttribute("aria-label", `${name} ${shown} ${unit}`.trim());

    this._secondary.textContent = "";
    const rows = cfg.secondary_layout === "rows";
    this._secondary.className = `secondary ${rows ? "rows" : "inline"}`;
    if (cfg.mode === "today" && this._baseSince) {
      // No state from midnight, as on the first day: say where the count starts.
      const note = el("span", "item");
      if (rows) note.append(el("span", "name", text(hass, "since")), el("span", "fig", this._baseSince));
      else note.textContent = `${text(hass, "since")} ${this._baseSince}`;
      this._secondary.append(note);
    }
    for (const item of cfg.secondary) {
      const itemState = hass.states[item.entity];
      const value = itemState ? itemState.state : undefined;
      const node = el("span", "item");
      let figure = "–";
      if (itemState && value !== "unavailable" && value !== "unknown") {
        const n = Number(value);
        if (item.map && item.map[value] !== undefined) figure = item.map[value];
        else if (item.decimals !== undefined && Number.isFinite(n)) {
          const factor = item.unit ? unitFactor(stateUnit(hass, item.entity), item.unit) : 1;
          figure = formatNumber(hass, n * factor, item.decimals);
        } else figure = String(value);
        const status = item.status && item.status[value];
        if (status === "good" || status === "warning") {
          node.classList.add(status);
          const icon = svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" });
          icon.append(svg("path", { d: status === "good" ? GOOD_ICON : WARNING_ICON }));
          node.append(icon);
        }
      }
      const unitText = item.unit ? ` ${item.unit}` : "";
      if (rows) node.append(el("span", "name", item.label || ""), el("span", "fig", `${figure}${unitText}`));
      else node.append(document.createTextNode(`${item.label ? `${item.label} ` : ""}${figure}${unitText}`));
      this._secondary.append(node);
    }
  }

  /* Add the newest state to the sparkline between fetches. */
  _live() {
    if (!this._hasGraph) return;
    const state = this._hass.states[this._config.entity];
    if (!state || state.last_updated === this._lastSeen) return;
    this._lastSeen = state.last_updated;
    if (!this._fetched || windowOf(this._config.hours).fixed) return;
    const value = numericState(this._hass, this._config.entity);
    if (value !== null) this._points.push({ t: Date.parse(state.last_updated), v: value });
    this._draw();
  }

  _fetchIfDue() {
    const now = Date.now();
    if (this._fetching || (typeof document !== "undefined" && document.hidden)) return;
    if (this._config.mode === "today") {
      const day = new Date().toDateString();
      if (this._baseDay !== day) this._fetchBase(day);
      return;
    }
    const span = windowOf(this._config.hours);
    if (!this._hasGraph || now - this._fetched < REFETCH_MS || (span.fixed && this._fetched)) return;
    this._fetching = true;
    const id = this._fetchId;
    fetchMean(this._hass, this._config.entity, span.start, span.end)
      .then(({ points }) => {
        if (id !== this._fetchId) return;
        this._points = points;
        this._fetched = Date.now();
        this._draw();
      })
      .catch(() => { if (id === this._fetchId) this._fetched = Date.now() - REFETCH_MS + 30e3; })
      .finally(() => { if (id === this._fetchId) this._fetching = false; });
  }

  /* Today's change needs the state at local midnight. */
  _fetchBase(day) {
    this._fetching = true;
    const midnight = new Date();
    midnight.setHours(0, 0, 0, 0);
    const entity = this._config.entity;
    fetchHistory(this._hass, entity, midnight.getTime(), midnight.getTime() + MINUTE)
      .then((points) => {
        if (points.length) return { point: points[0], since: undefined };
        // Nothing recorded at midnight: fall back to the first state today.
        return fetchHistory(this._hass, entity, midnight.getTime(), Date.now()).then((all) => ({
          point: all[0],
          since: all[0] ? formatDate(this._hass, all[0].t, CLOCK) : undefined,
        }));
      })
      .then(({ point, since }) => {
        this._base = point ? point.v : undefined;
        this._baseSince = since;
        this._baseDay = day;
        this._text();
      })
      .catch(() => {})
      .finally(() => { this._fetching = false; });
  }

  _series() {
    const { start, end } = windowOf(this._config.hours);
    const factor = this._factor();
    this._points = this._points.filter((p) => p.t >= start - MINUTE);
    const points = this._points.filter((p) => p.t >= start && p.t <= end).map((p) => ({ t: p.t, v: p.v * factor }));
    return { points: downsample(points, start, end, SPARK_POINTS), start, end };
  }

  _draw() {
    if (!this._spark) return;
    const w = this._spark.clientWidth;
    const h = this._spark.clientHeight;
    this._spark.textContent = "";
    this._plot = null;
    const { points, start, end } = this._series();
    if (!w || !h || points.length < 2) return;

    let lo = Infinity;
    let hi = -Infinity;
    for (const p of points) { if (p.v < lo) lo = p.v; if (p.v > hi) hi = p.v; }
    if (this._config.zero) lo = Math.min(0, lo);
    if (hi - lo < 1e-9) { hi += 1; lo -= this._config.zero ? 0 : 1; }
    const pad = 6;  // room for the end dot when the value sits on the floor
    const x = (t) => ((t - start) / (end - start)) * (w - 7);
    const y = (v) => pad + (1 - (v - lo) / (hi - lo)) * (h - 2 * pad);

    const d = points.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
    const root = svg("svg", { viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: "none", "aria-hidden": "true" });
    const last = points[points.length - 1];
    if (this._config.zero) {
      root.append(svg("path", {
        class: "wash", d: `${d}L${x(last.t).toFixed(1)},${h}L${x(points[0].t).toFixed(1)},${h}Z`,
      }));
    }
    root.append(svg("path", { class: "line", d }));
    const cross = svg("line", { class: "cross", y1: 0, y2: h, visibility: "hidden" });
    const dot = svg("circle", { class: "dot", r: 4, cx: x(last.t).toFixed(1), cy: y(last.v).toFixed(1) });
    root.append(cross, dot);
    this._spark.append(root);
    this._plot = { points, x, y, cross, dot, last, long: end - start > DAY };
  }

  _hover(ev) {
    const plot = this._plot;
    if (!plot || !this._tip) return;
    if (!ev) {
      plot.cross.setAttribute("visibility", "hidden");
      plot.dot.setAttribute("cx", plot.x(plot.last.t).toFixed(1));
      plot.dot.setAttribute("cy", plot.y(plot.last.v).toFixed(1));
      this._tip.style.display = "none";
      return;
    }
    const px = ev.clientX - this._spark.getBoundingClientRect().left;
    let best = plot.points[0];
    for (const p of plot.points) {
      if (Math.abs(plot.x(p.t) - px) < Math.abs(plot.x(best.t) - px)) best = p;
    }
    const bx = plot.x(best.t);
    plot.cross.setAttribute("x1", bx.toFixed(1));
    plot.cross.setAttribute("x2", bx.toFixed(1));
    plot.cross.setAttribute("visibility", "visible");
    plot.dot.setAttribute("cx", bx.toFixed(1));
    plot.dot.setAttribute("cy", plot.y(best.v).toFixed(1));

    this._tip.textContent = "";
    this._tip.append(
      el("b", null, `${formatNumber(this._hass, best.v, this._config.decimals)} ${this._unit()}`.trim()),
      document.createTextNode(formatDate(this._hass, best.t, plot.long ? { ...DAY_MONTH, ...CLOCK } : CLOCK)),
    );
    this._tip.style.display = "block";
    const tipW = this._tip.offsetWidth;
    this._tip.style.left = `${Math.max(6, Math.min(this._card.clientWidth - tipW - 6, bx - tipW / 2))}px`;
  }
}

/* ------------------------------------------------------------------ */
/* zap-chart-card                                                       */
/* ------------------------------------------------------------------ */

const CHART_STYLE = `
  ${APPEARANCE_STYLE}
  :host { display: block; height: 100%; }
  ha-card {
    height: 100%; box-sizing: border-box; overflow: hidden;
    display: flex; flex-direction: column; font-family: ${FONT};
  }
  .head { flex: none; padding: 10px 14px 0; }
  .title {
    display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    color: var(--primary-text-color); font: 500 14px/20px ${FONT};
  }
  .title.link { cursor: pointer; }
  .plot { position: relative; flex: 1 1 0; min-height: 60px; margin: 2px 4px 0; touch-action: pan-y; }
  .plot svg { position: absolute; left: 0; top: 0; width: 100%; height: 100%; overflow: visible; }
  .plot.loading svg { opacity: 0.45; }
  .grid { stroke: var(--divider-color); stroke-width: 1; shape-rendering: crispEdges; }
  .tick { fill: var(--secondary-text-color); font: 11px ${FONT}; font-variant-numeric: tabular-nums; }
  .tick.major { fill: var(--primary-text-color); font-weight: 600; }
  .line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .wash { stroke: none; opacity: 0.1; }
  .empty {
    position: absolute; inset: 0; display: none; align-items: center; justify-content: center;
    color: var(--secondary-text-color); font-size: 12px;
  }
  .empty.on { display: flex; }
  .overlay { position: absolute; inset: 0; pointer-events: none; display: none; }
  .cross { position: absolute; width: 1px; background: var(--secondary-text-color); opacity: 0.7; }
  .dot {
    position: absolute; width: 8px; height: 8px; margin: -6px 0 0 -6px; border-radius: 50%;
    border: 2px solid var(--ha-card-background, var(--card-background-color));
  }
  .tip {
    position: absolute; padding: 5px 8px 6px; border-radius: 3px; white-space: nowrap; z-index: 2;
    background: var(--primary-background-color); border: 1px solid var(--divider-color);
    color: var(--secondary-text-color); font: 12px/17px ${FONT};
  }
  .tip .time { font-size: 11px; line-height: 15px; margin-bottom: 2px; }
  .tip .row { display: flex; align-items: center; gap: 6px; }
  .tip .key { flex: none; width: 10px; height: 2px; border-radius: 1px; }
  .tip b { color: var(--primary-text-color); font-weight: 600; font-variant-numeric: tabular-nums; }
  .legend { flex: none; display: flex; flex-wrap: wrap; gap: 2px 14px; padding: 0 14px 8px; min-height: 18px; }
  .legend button {
    appearance: none; border: 0; background: none; padding: 0; margin: 0; cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px;
    color: var(--secondary-text-color); font: 12px/18px ${FONT};
  }
  .legend button:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .legend .key { width: 12px; height: 3px; border-radius: 2px; }
  .pad { flex: none; height: 6px; }
`;

const KINDS = ["line", "area", "bar"];

class ZapChartCard extends Base {
  setConfig(config) {
    if (!config || !Array.isArray(config.series) || !config.series.length) {
      throw new Error("zap-chart-card: series must list at least one entity");
    }
    if (config.series.some((item) => !item || !item.entity)) {
      throw new Error("zap-chart-card: every series needs an entity");
    }
    const merged = { kind: "line", decimals: 0, zero: false, hours: "range", ...config };
    if (!KINDS.includes(merged.kind)) throw new Error(`zap-chart-card: kind "${merged.kind}" is not line, area or bar`);
    this._config = merged;
    this._data = null;
    this._fetchId = (this._fetchId || 0) + 1;
    this._loading = false;
    this.toggleAttribute("zap", merged.appearance === "zap");
    if (this.shadowRoot) {
      this._build();
      if (this._hass) this._load();
    }
  }

  getCardSize() { return 5; }

  getGridOptions() {
    return { columns: 12, rows: 5, min_columns: 6, min_rows: 3 };
  }

  static getStubConfig(hass) {
    const entity = Object.keys((hass && hass.states) || {})
      .find((id) => id.startsWith("sensor.") && hass.states[id].attributes.device_class === "power");
    return { title: "Power", kind: "area", zero: true, series: [{ entity: entity || "sensor.example" }] };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._build();
    }
    this._tick();
  }

  connectedCallback() {
    if (!this._resize && typeof ResizeObserver !== "undefined") {
      this._resize = new ResizeObserver(() => this._draw());
    }
    if (this._resize && this._plot) this._resize.observe(this._plot);
    this._onRange = () => { if (this._config.hours === "range" && this._hass) this._load(); };
    this._onHover = (state) => this._showHover(state);
    range.listeners.add(this._onRange);
    hover.listeners.add(this._onHover);
  }

  disconnectedCallback() {
    if (this._resize) this._resize.disconnect();
    range.listeners.delete(this._onRange);
    hover.listeners.delete(this._onHover);
    clearTimeout(this._leaveTimer);
    this._stopHover();
  }

  _unit() {
    if (this._config.unit !== undefined) return this._config.unit;
    return stateUnit(this._hass, this._config.series[0].entity);
  }

  _factor(entity) {
    return unitFactor(stateUnit(this._hass, entity), this._unit());
  }

  _name(item) {
    if (item.name) return item.name;
    const state = this._hass && this._hass.states[item.entity];
    return (state && state.attributes.friendly_name) || item.entity;
  }

  _build() {
    const root = this.shadowRoot;
    const series = this._config.series;
    root.textContent = "";
    root.append(el("style", null, CHART_STYLE));
    const card = el("ha-card");

    const head = el("div", "head");
    this._title = el("span", "title", this._config.title || "");
    if (series.length === 1) {
      this._title.classList.add("link");
      this._title.addEventListener("click", () => moreInfo(this, series[0].entity));
    }
    head.append(this._title);

    this._plot = el("div", "plot");
    this._svg = svg("svg", { role: "img" });
    this._empty = el("div", "empty");
    this._overlay = el("div", "overlay");
    this._plot.append(this._svg, this._empty, this._overlay);
    this._plot.addEventListener("pointermove", (ev) => this._pointer(ev));
    this._plot.addEventListener("pointerdown", (ev) => this._pointer(ev));
    this._plot.addEventListener("pointerleave", (ev) => this._leave(ev));
    this._plot.addEventListener("pointercancel", (ev) => this._leave(ev));
    if (this._resize) this._resize.observe(this._plot);

    card.append(head, this._plot);
    this._keys = [];
    if (series.length > 1) {
      const legend = el("div", "legend");
      for (const item of series) {
        const button = el("button");
        button.type = "button";
        const key = el("span", "key");
        const name = el("span");
        button.append(key, name);
        button.addEventListener("click", () => moreInfo(this, item.entity));
        legend.append(button);
        this._keys.push({ key, name, item });
      }
      card.append(legend);
    } else {
      card.append(el("div", "pad"));
    }
    root.append(card);
    this._view = null;
  }

  /* Called on every Home Assistant update: load, refresh and slide the window. */
  _tick() {
    const now = Date.now();
    if (!this._data) {
      if (!this._loading) this._load();
      return;
    }
    if (this._loading || this._data.fixed) return;
    const age = now - this._data.fetched;
    if (age > (this._data.source === "hour" ? 15 * MINUTE : REFETCH_MS)) {
      if (typeof document === "undefined" || !document.hidden) this._load();
      return;
    }
    let grew = false;
    if (this._config.kind !== "bar") {
      this._config.series.forEach((item, index) => {
        const state = this._hass.states[item.entity];
        const value = numericState(this._hass, item.entity);
        if (!state || value === null) return;
        const points = this._data.series[index];
        const t = Date.parse(state.last_updated);
        if (points.length && points[points.length - 1].t >= t) return;
        points.push({ t, v: value * this._factor(item.entity) });
        grew = true;
      });
    }
    if (grew || now - (this._drawn || 0) > 15e3) this._draw();
  }

  _load() {
    const hass = this._hass;
    const span = windowOf(this._config.hours);
    const id = (this._fetchId = (this._fetchId || 0) + 1);
    this._loading = true;
    if (this._plot) this._plot.classList.add("loading");
    let work;
    if (this._config.kind === "bar") {
      const plan = barPlan(span.start, span.end);
      work = Promise.all(this._config.series.map((item) => {
        const factor = this._factor(item.entity);
        return fetchStatistics(hass, item.entity, span.start - plan.bucket, span.end, plan.period, "change")
          .then((rows) => sumBuckets(rows, plan.bucket).map((row) => ({ ...row, v: row.v * factor })));
      })).then((series) => ({ source: plan.period, plan, series }));
    } else {
      work = Promise.all(this._config.series.map((item) => {
        const factor = this._factor(item.entity);
        return fetchMean(hass, item.entity, span.start, span.end)
          .then((result) => ({ source: result.source, points: result.points.map((p) => ({ t: p.t, v: p.v * factor })) }));
      })).then((results) => ({ source: results[0].source, series: results.map((result) => result.points) }));
    }
    work
      .then((data) => {
        if (id !== this._fetchId) return;
        this._data = { ...data, fetched: Date.now(), fixed: span.fixed, failed: false };
      })
      .catch(() => {
        if (id !== this._fetchId) return;
        // Keep what is drawn and try again in half a minute.
        this._data = this._data
          ? { ...this._data, fetched: Date.now() - REFETCH_MS + 30e3 }
          : { source: "history", series: this._config.series.map(() => []), fetched: Date.now() - REFETCH_MS + 30e3, fixed: false, failed: true };
      })
      .finally(() => {
        if (id !== this._fetchId) return;
        this._loading = false;
        if (this._plot) this._plot.classList.remove("loading");
        this._draw();
      });
  }

  _draw() {
    this._paint();
    this._showHover(this._hoverState);
  }

  _paint() {
    if (!this._plot || !this._hass) return;
    const width = this._plot.clientWidth;
    const height = this._plot.clientHeight;
    const data = this._data;
    this._drawn = Date.now();
    this._view = null;
    if (!width || !height || !data) return;

    const hass = this._hass;
    const dark = isDark(this);
    const cfg = this._config;
    const bars = cfg.kind === "bar";
    const span = windowOf(cfg.hours);
    const colors = cfg.series.map((item, index) => seriesColor(item.color, index, dark));
    this._keys.forEach(({ key, name, item }, index) => {
      key.style.background = colors[index];
      name.textContent = this._name(item);
    });
    this._title.textContent = bars && data.plan
      ? `${cfg.title || ""} ${text(hass, data.plan.label)}`.trim()
      : cfg.title || "";
    this._svg.setAttribute("aria-label", this._title.textContent);

    // What is inside the window.
    const maxPoints = Math.max(120, Math.min(900, Math.round(width)));
    const series = data.series.map((points) => (bars
      ? points.filter((row) => row.t1 > span.start && row.t0 < span.end)
      : downsample(points.filter((p) => p.t >= span.start && p.t <= span.end), span.start, span.end, maxPoints)));
    let lo = Infinity;
    let hi = -Infinity;
    for (const points of series) {
      for (const p of points) { if (p.v < lo) lo = p.v; if (p.v > hi) hi = p.v; }
    }
    const none = !Number.isFinite(lo);
    this._empty.textContent = text(hass, "no_data");
    this._empty.classList.toggle("on", none && !this._loading);
    this._svg.textContent = "";
    if (none) return;
    if (cfg.zero || bars) { lo = Math.min(0, lo); hi = Math.max(0, hi); }

    const scale = niceScale(lo, hi, height < 150 ? 3 : 4);
    const labels = scale.ticks.map((value) => formatNumber(hass, value, scale.decimals));
    const left = Math.max(...labels.map((label) => label.length)) * 6.4 + 14;
    const right = 12;
    const top = 8;
    const bottom = 22;
    const plotW = Math.max(10, width - left - right);
    const plotH = Math.max(10, height - top - bottom);
    const x = (t) => left + ((t - span.start) / (span.end - span.start)) * plotW;
    const y = (v) => top + (1 - (v - scale.min) / (scale.max - scale.min)) * plotH;

    const frame = svg("g");
    scale.ticks.forEach((value, index) => {
      const at = Math.round(y(value)) + 0.5;
      frame.append(svg("line", { class: "grid", x1: left, x2: left + plotW, y1: at, y2: at }));
      const label = svg("text", { class: "tick", x: left - 7, y: at, "text-anchor": "end", dy: "0.32em" });
      label.textContent = labels[index];
      frame.append(label);
    });
    const { step, ticks } = timeTicks(span.start, span.end, plotW);
    for (const tick of ticks) {
      const at = x(tick.t);
      if (at < left - 1 || at > left + plotW - 14) continue;
      const day = tick.major || step >= DAY;
      const label = svg("text", {
        class: `tick${tick.major && step < DAY ? " major" : ""}`, x: at, y: height - 6, "text-anchor": "middle",
      });
      label.textContent = formatDate(hass, tick.t, day ? DAY_MONTH : CLOCK);
      frame.append(label);
    }
    this._svg.append(frame);

    const zeroY = y(Math.max(scale.min, Math.min(0, scale.max)));
    const marks = svg("g");
    series.forEach((points, index) => {
      const color = colors[index];
      if (bars) {
        const count = series.length;
        for (const row of points) {
          const x0 = x(row.t0);
          const x1 = x(row.t1);
          const group = Math.max(count, Math.min((24 + 2) * count - 2, (x1 - x0) * 0.66));
          const barW = Math.max(1, (group - 2 * (count - 1)) / count);
          const bx = (x0 + x1) / 2 - group / 2 + index * (barW + 2);
          if (bx + barW < left || bx > left + plotW) continue;
          const tip = y(row.v);
          const h = Math.abs(zeroY - tip);
          if (h < 0.5) continue;
          const r = Math.min(3, barW / 2, h);
          const up = tip < zeroY;
          const d = up
            ? `M${bx},${zeroY}V${tip + r}Q${bx},${tip} ${bx + r},${tip}H${bx + barW - r}Q${bx + barW},${tip} ${bx + barW},${tip + r}V${zeroY}Z`
            : `M${bx},${zeroY}V${tip - r}Q${bx},${tip} ${bx + r},${tip}H${bx + barW - r}Q${bx + barW},${tip} ${bx + barW},${tip - r}V${zeroY}Z`;
          marks.append(svg("path", { d, fill: color }));
        }
        return;
      }
      const spacing = data.source === "hour" ? HOUR : data.source === "5minute" ? 5 * MINUTE : 0;
      for (const part of splitGaps(points, spacing)) {
        if (!part.length) continue;
        const d = part.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
        if (cfg.kind === "area" && part.length > 1) {
          marks.append(svg("path", {
            class: "wash", fill: color,
            d: `${d}L${x(part[part.length - 1].t).toFixed(1)},${zeroY}L${x(part[0].t).toFixed(1)},${zeroY}Z`,
          }));
        }
        if (part.length === 1) {
          marks.append(svg("circle", { cx: x(part[0].t).toFixed(1), cy: y(part[0].v).toFixed(1), r: 1.5, fill: color }));
        } else {
          marks.append(svg("path", { class: "line", d, stroke: color }));
        }
      }
    });
    this._svg.append(marks);
    this._view = { span, series, colors, x, y, left, top, plotW, plotH, width, bars, bucket: data.plan && data.plan.bucket };
  }

  /* ---- crosshair shared with the other charts ----------------------- */

  _pointer(ev) {
    clearTimeout(this._leaveTimer);
    const view = this._view;
    if (!view) return;
    const fraction = (ev.clientX - this._plot.getBoundingClientRect().left - view.left) / view.plotW;
    if (fraction < 0 || fraction > 1) { this._stopHover(); return; }
    this._pending = view.span.start + fraction * (view.span.end - view.span.start);
    if (this._frame) return;
    this._frame = requestAnimationFrame(() => {
      this._frame = 0;
      hover.set({ t: this._pending }, this);
    });
  }

  _stopHover() {
    if (this._frame) cancelAnimationFrame(this._frame);
    this._frame = 0;
    hover.clear(this);
  }

  _leave(ev) {
    clearTimeout(this._leaveTimer);
    if (ev.pointerType === "touch") {
      // A touch ends when the finger lifts; keep the readout a moment.
      this._leaveTimer = setTimeout(() => this._stopHover(), 2500);
    } else {
      this._stopHover();
    }
  }

  /* The point a line shows at time t: the nearest one, unless the data has a gap there. */
  _nearest(points, t) {
    if (!points.length) return null;
    let lo = 0;
    let hi = points.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (points[mid].t <= t) lo = mid; else hi = mid - 1;
    }
    let pick = lo;
    if (pick + 1 < points.length && Math.abs(points[pick + 1].t - t) < Math.abs(points[pick].t - t)) pick += 1;
    const reach = Math.max((this._view.span.end - this._view.span.start) / 40, 2 * MINUTE);
    return Math.abs(points[pick].t - t) <= reach ? points[pick] : null;
  }

  _showHover(state) {
    this._hoverState = state || null;
    const overlay = this._overlay;
    if (!overlay) return;
    overlay.textContent = "";
    overlay.style.display = "none";
    const view = this._view;
    if (!state || !view || state.t < view.span.start || state.t > view.span.end) return;

    const hass = this._hass;
    const cfg = this._config;
    const rows = [];
    let stamp = null;
    view.series.forEach((points, index) => {
      const hit = view.bars
        ? points.find((row) => row.t0 <= state.t && state.t < row.t1)
        : this._nearest(points, state.t);
      if (!hit) return;
      if (stamp === null) stamp = view.bars ? hit.t0 : hit.t;
      rows.push({
        name: this._name(cfg.series[index]),
        color: view.colors[index],
        figure: `${formatNumber(hass, hit.v, cfg.decimals)} ${this._unit()}`.trim(),
        x: view.bars ? null : view.x(hit.t),
        y: view.bars ? null : view.y(hit.v),
      });
    });

    const at = view.x(state.t);
    const cross = el("div", "cross");
    cross.style.left = `${at}px`;
    cross.style.top = `${view.top}px`;
    cross.style.height = `${view.plotH}px`;
    overlay.append(cross);
    overlay.style.display = "block";
    if (!rows.length) return;

    for (const row of rows) {
      if (row.y === null) continue;
      const dot = el("div", "dot");
      dot.style.left = `${row.x}px`;
      dot.style.top = `${row.y}px`;
      dot.style.background = row.color;
      overlay.append(dot);
    }

    const long = view.span.end - view.span.start > 36 * HOUR;
    let when = { weekday: "short", ...CLOCK };
    if (view.bars && view.bucket >= DAY) when = { weekday: "short", ...DAY_MONTH };
    else if (long) when = { ...DAY_MONTH, ...CLOCK };
    const tip = el("div", "tip");
    tip.append(el("div", "time", formatDate(hass, stamp, when)));
    for (const row of rows) {
      const line = el("div", "row");
      const key = el("span", "key");
      key.style.background = row.color;
      line.append(key, el("b", null, row.figure));
      if (rows.length > 1) line.append(el("span", null, row.name));
      tip.append(line);
    }
    overlay.append(tip);
    const tipW = tip.offsetWidth;
    const gap = 10;
    tip.style.left = `${at + gap + tipW <= view.width - 4 ? at + gap : Math.max(4, at - gap - tipW)}px`;
    tip.style.top = `${view.top + 4}px`;
  }
}

/* ------------------------------------------------------------------ */
/* Dashboard strategy: custom:sourceful-zap                             */
/* ------------------------------------------------------------------ */

/*
 * The integration names every sensor with a translation key (power,
 * l1_voltage, energy_import, ...). The dashboard is built from those keys, so
 * it does not depend on entity ids.
 */
export function collectDevices(hass) {
  const devices = new Map();
  for (const entry of Object.values((hass && hass.entities) || {})) {
    if (entry.platform !== DOMAIN || entry.hidden || !entry.device_id || !entry.translation_key) continue;
    if (!hass.states[entry.entity_id]) continue;
    let device = devices.get(entry.device_id);
    if (!device) {
      const info = (hass.devices || {})[entry.device_id] || {};
      device = {
        id: entry.device_id,
        name: info.name_by_user || info.name || "Zap",
        entry: info.primary_config_entry || (info.config_entries || [])[0] || entry.device_id,
        roles: {},
      };
      devices.set(entry.device_id, device);
    }
    device.roles[entry.translation_key] = entry.entity_id;
  }
  const groups = new Map();
  for (const device of devices.values()) {
    if (!groups.has(device.entry)) groups.set(device.entry, { gateway: null, devices: [] });
    const group = groups.get(device.entry);
    if (Object.keys(device.roles).some((role) => role.startsWith("gateway_"))) group.gateway = device;
    else group.devices.push(device);
  }
  const rank = (device) => (device.roles.energy_import || device.roles.l1_voltage ? 0 : 1);
  const list = [...groups.values()];
  for (const group of list) {
    group.devices.sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name));
  }
  const label = (group) => (group.gateway || group.devices[0] || { name: "" }).name;
  return list.sort((a, b) => label(a).localeCompare(label(b)));
}

function deviceIcon(roles) {
  if (roles.energy_import || roles.l1_voltage) return "mdi:transmission-tower";
  if (roles.battery_soc || roles.battery_power) return "mdi:battery";
  if (roles.energy_production || roles.mppt1_power) return "mdi:solar-power-variant";
  if (roles.ev_charger_power) return "mdi:ev-station";
  if (roles.inverter_power) return "mdi:current-ac";
  return "mdi:flash";
}

function deviceCards(hass, device, withPicker, look) {
  const roles = device.roles;
  const say = (key) => text(hass, key);
  const cards = [];
  const tile = (entity, options, columns = 6) => ({
    type: "custom:zap-stat-card", entity, hours: "range", ...look, ...options,
    grid_options: { columns, rows: 2 },
  });
  const chart = (title, kind, series, options, columns = 12, rows = 5) => ({
    type: "custom:zap-chart-card", title, kind, series, ...look, ...options,
    grid_options: { columns, rows },
  });
  // The view is three columns wide: 36 grid columns. Small charts go three to a
  // row, and the last row is stretched so it has no hole.
  const small = [];
  const have = (list) => list.filter((item) => item.entity);

  cards.push({
    type: withPicker ? "custom:zap-range-picker" : "custom:zap-heading-card",
    title: device.name,
    icon: deviceIcon(roles),
    ...look,
    grid_options: { columns: "full", rows: "auto" },
  });

  // --- Tiles ---------------------------------------------------------
  if (roles.power) {
    cards.push(tile(roles.power, {
      name: say("power_now"), unit: "W", hero: withPicker, color: "yellow", zero: true,
    }, withPicker ? 12 : 6));
  }
  const phases = [["l1", "L1", "blue"], ["l2", "L2", "orange"], ["l3", "L3", "aqua"]];
  for (const [key, name, color] of phases) {
    const power = roles[`${key}_power`];
    const current = roles[`${key}_current`];
    const voltage = roles[`${key}_voltage`];
    const base = { name, key: true, color };
    if (power) {
      cards.push(tile(power, {
        ...base, unit: "W", zero: true,
        secondary: have([{ entity: current, unit: "A", decimals: 1 }, { entity: voltage, unit: "V", decimals: 0 }]),
      }));
    } else if (current) {
      cards.push(tile(current, {
        ...base, unit: "A", decimals: 1, zero: true,
        secondary: have([{ entity: voltage, unit: "V", decimals: 0 }]),
      }));
    } else if (voltage) {
      cards.push(tile(voltage, { ...base, unit: "V", decimals: 1 }));
    }
  }
  if (roles.grid_power) {
    cards.push(tile(roles.grid_power, { name: say("grid_power"), unit: "W", color: "blue", zero: true }));
  }
  if (roles.inverter_power) {
    cards.push(tile(roles.inverter_power, { name: say("inverter_power"), unit: "W", color: "violet", zero: true }));
  }
  if (roles.battery_soc) {
    cards.push(tile(roles.battery_soc, {
      name: say("battery"), unit: "%", color: "magenta", zero: true,
      secondary: have([{ entity: roles.battery_power, unit: "W", decimals: 0 }]),
    }));
  } else if (roles.battery_power) {
    cards.push(tile(roles.battery_power, { name: say("battery_power"), unit: "W", color: "magenta", zero: true }));
  }
  if (roles.ev_charger_power) {
    cards.push(tile(roles.ev_charger_power, { name: say("ev_power"), unit: "W", color: "green", zero: true }));
  }
  const today = (entity, name) => tile(entity, {
    name, mode: "today", unit: "kWh", decimals: 2, graph: false, secondary_layout: "rows",
    secondary: [{ entity, label: say("total"), unit: "kWh", decimals: 1 }],
  });
  if (roles.energy_import) cards.push(today(roles.energy_import, say("import_today")));
  if (roles.energy_export && (numericState(hass, roles.energy_export) || 0) > 0) {
    cards.push(today(roles.energy_export, say("export_today")));
  }
  if (roles.energy_production) cards.push(today(roles.energy_production, say("production_today")));
  if (roles.battery_charge_total) cards.push(today(roles.battery_charge_total, say("charged_today")));
  if (roles.battery_discharge_total) cards.push(today(roles.battery_discharge_total, say("discharged_today")));
  if (roles.temperature) {
    cards.push(tile(roles.temperature, { name: say("temperature"), decimals: 1 }));
  }

  // --- Charts --------------------------------------------------------
  // A heading card without a title is an empty row: the charts start on a new line.
  cards.push({ type: "custom:zap-heading-card", ...look, grid_options: { columns: "full", rows: "auto" } });
  const wide = [];
  if (roles.power) {
    wide.push(chart(say("power"), "area", [{ entity: roles.power, name: say("power"), color: "yellow" }],
      { unit: "W", zero: true }, 24, 6));
  }
  const energy = have([
    { entity: roles.energy_import, name: say("import"), color: "yellow" },
    { entity: roles.energy_production, name: say("production"), color: "orange" },
    { entity: (numericState(hass, roles.energy_export) || 0) > 0 ? roles.energy_export : undefined, name: say("export"), color: "violet" },
  ]);
  if (energy.length) {
    const title = energy.length === 1 ? energy[0].name : say("energy");
    wide.push(chart(title, "bar", energy, { unit: "kWh", decimals: 2 }, 12, 6));
  }
  if (wide.length === 1) wide[0].grid_options.columns = 36;
  cards.push(...wide);
  const flows = have([
    { entity: roles.grid_power, name: say("grid"), color: "blue" },
    { entity: roles.inverter_power, name: say("inverter"), color: "violet" },
    { entity: roles.battery_power, name: say("battery"), color: "magenta" },
    { entity: roles.ev_charger_power, name: say("ev"), color: "green" },
  ]);
  if (flows.length > 1) {
    small.push(chart(say("power_flows"), "line", flows, { unit: "W", zero: true }));
  } else if (flows.length === 1 && !roles.battery_soc) {
    small.push(chart(flows[0].name, "line", flows, { unit: "W", zero: true }));
  }
  const perPhase = (suffix) => have(phases.map(([key, name, color]) => ({ entity: roles[`${key}_${suffix}`], name, color })));
  if (perPhase("power").length) {
    small.push(chart(say("power_per_phase"), "line", perPhase("power"), { unit: "W", zero: true }));
  }
  if (perPhase("current").length) {
    small.push(chart(say("current_per_phase"), "line", perPhase("current"), { unit: "A", decimals: 1, zero: true }));
  }
  if (perPhase("voltage").length) {
    small.push(chart(say("voltage_per_phase"), "line", perPhase("voltage"), { unit: "V", decimals: 1 }));
  }
  if (roles.grid_reactive_power) {
    small.push(chart(say("reactive_power"), "line",
      [{ entity: roles.grid_reactive_power, name: say("reactive_power"), color: "neutral" }], { unit: "var" }));
  }
  if (roles.grid_frequency) {
    small.push(chart(say("frequency"), "line",
      [{ entity: roles.grid_frequency, name: say("frequency"), color: "neutral" }], { unit: "Hz", decimals: 2 }));
  }
  if (roles.battery_soc) {
    small.push(chart(say("soc"), "area",
      [{ entity: roles.battery_soc, name: say("soc"), color: "magenta" }], { unit: "%", zero: true }));
  }
  if (roles.battery_power && flows.length < 2) {
    small.push(chart(say("battery_power"), "line",
      [{ entity: roles.battery_power, name: say("battery_power"), color: "magenta" }], { unit: "W", zero: true }));
  }
  const cycle = have([
    { entity: roles.battery_charge_total, name: say("charged"), color: "magenta" },
    { entity: roles.battery_discharge_total, name: say("discharged"), color: "violet" },
  ]);
  if (cycle.length) small.push(chart(say("battery"), "bar", cycle, { unit: "kWh", decimals: 2 }));
  if (roles.battery_voltage) {
    small.push(chart(say("battery_voltage"), "line",
      [{ entity: roles.battery_voltage, name: say("battery_voltage"), color: "neutral" }], { unit: "V", decimals: 1 }));
  }
  if (roles.battery_current) {
    small.push(chart(say("battery_current"), "line",
      [{ entity: roles.battery_current, name: say("battery_current"), color: "neutral" }], { unit: "A", decimals: 1 }));
  }
  const inputs = (suffix) => have([
    { entity: roles[`mppt1_${suffix}`], name: "MPPT 1", color: "blue" },
    { entity: roles[`mppt2_${suffix}`], name: "MPPT 2", color: "orange" },
  ]);
  if (inputs("power").length) small.push(chart(say("mppt_power"), "line", inputs("power"), { unit: "W", zero: true }));
  if (inputs("voltage").length) small.push(chart(say("mppt_voltage"), "line", inputs("voltage"), { unit: "V", decimals: 1 }));
  if (inputs("current").length) small.push(chart(say("mppt_current"), "line", inputs("current"), { unit: "A", decimals: 1, zero: true }));
  const heat = have([
    { entity: roles.temperature, name: say("temperature"), color: "neutral" },
    { entity: roles.battery_temperature, name: say("battery"), color: "magenta" },
  ]);
  if (heat.length) small.push(chart(say("temperature"), "line", heat, { decimals: 1 }));
  const last = small.length % 3;
  small.slice(small.length - last).forEach((card) => { card.grid_options.columns = 36 / last; });
  cards.push(...small);
  return cards;
}

function gatewayCards(hass, gateway, withPicker, look) {
  const roles = gateway.roles;
  const say = (key) => text(hass, key);
  const tile = (entity, options, columns) => ({
    type: "custom:zap-stat-card", entity, ...look, ...options, grid_options: { columns, rows: 2 },
  });
  const cards = [{
    type: withPicker ? "custom:zap-range-picker" : "custom:zap-heading-card",
    title: say("gateway"),
    icon: "mdi:chip",
    ...look,
    grid_options: { columns: "full", rows: "auto" },
  }];
  if (roles.gateway_firmware_version) {
    cards.push(tile(roles.gateway_firmware_version, { name: say("firmware"), mode: "text" }, 6));
  }
  if (roles.gateway_uptime) {
    cards.push(tile(roles.gateway_uptime, { name: say("uptime"), mode: "duration" }, 6));
  }
  if (roles.gateway_signal_strength) {
    const secondary = [];
    if (roles.gateway_wifi_ssid) secondary.push({ entity: roles.gateway_wifi_ssid });
    if (roles.gateway_wifi_status) {
      secondary.push({
        entity: roles.gateway_wifi_status,
        map: { connected: say("connected"), disconnected: say("disconnected") },
        status: { connected: "good", disconnected: "warning" },
      });
    }
    cards.push(tile(roles.gateway_signal_strength, { name: say("wifi_signal"), hours: "range", secondary }, 12));
  }
  if (roles.gateway_temperature) {
    cards.push(tile(roles.gateway_temperature, { name: say("temperature"), decimals: 1, hours: "range" }, 6));
  }
  if (roles.gateway_memory_free) {
    const secondary = roles.gateway_memory_percent
      ? [{ entity: roles.gateway_memory_percent, decimals: 0, unit: `% ${say("used")}` }]
      : [];
    cards.push(tile(roles.gateway_memory_free, { name: say("free_memory"), hours: "range", secondary }, 6));
  }
  return cards;
}

/* The whole dashboard: one view per Zap, one section per device on it. */
export function buildDashboard(hass, config = {}) {
  const zap = config.appearance !== "theme";
  const look = zap ? { appearance: "zap" } : {};
  const groups = collectDevices(hass);
  if (!groups.length) {
    return {
      title: "Sourceful Zap",
      views: [{ title: "Sourceful Zap", cards: [{ type: "markdown", content: text(hass, "no_devices") }] }],
    };
  }
  const views = groups.map((group, index) => {
    const sections = group.devices.map((device, at) => ({
      type: "grid", column_span: 3, cards: deviceCards(hass, device, at === 0, look),
    }));
    if (group.gateway && Object.keys(group.gateway.roles).length) {
      sections.push({
        type: "grid", column_span: 3, cards: gatewayCards(hass, group.gateway, !group.devices.length, look),
      });
    }
    const view = {
      title: (group.gateway || group.devices[0]).name,
      path: `zap-${index + 1}`,
      type: "sections",
      max_columns: 3,
      sections,
    };
    if (zap) view.background = "#111217";
    return view;
  });
  return { title: "Sourceful Zap", views };
}

class ZapDashboardStrategy extends Base {
  static async generate(config, hass) {
    return buildDashboard(hass, config || {});
  }
}

/* ------------------------------------------------------------------ */

if (typeof customElements !== "undefined" && typeof window !== "undefined") {
  const cards = [
    ["zap-stat-card", ZapStatCard, "Zap stat card", "A value, a second line and a sparkline."],
    ["zap-chart-card", ZapChartCard, "Zap chart card", "Lines, an area or energy bars over time."],
    ["zap-range-picker", ZapRangePicker, "Zap range picker", "A title and one time range for every Zap card of the view."],
    ["zap-heading-card", ZapHeadingCard, "Zap heading card", "A title for a group of Zap cards."],
  ];
  window.customCards = window.customCards || [];
  for (const [tag, cls, name, description] of cards) {
    if (customElements.get(tag)) continue;
    customElements.define(tag, cls);
    window.customCards.push({ type: tag, name, description, preview: false });
  }
  if (!customElements.get("ll-strategy-dashboard-sourceful-zap")) {
    customElements.define("ll-strategy-dashboard-sourceful-zap", ZapDashboardStrategy);
    window.customStrategies = window.customStrategies || [];
    window.customStrategies.push({
      type: "sourceful-zap",
      strategyType: "dashboard",
      name: "Sourceful Zap",
      description: "Power, energy and phases for every device on your Zap, built from your sensors.",
      documentationURL: "https://github.com/srcfl/zap-home-assistant#dashboard",
    });
  }
  console.info(`Sourceful Zap cards ${VERSION}`);
}
