// Tests for the logic in zap-cards.js that needs no browser.
// Run with: node --test tests/frontend/

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  VERSION,
  barPlan,
  buildDashboard,
  collectDevices,
  downsample,
  hoursOf,
  meanSource,
  niceScale,
  seriesColor,
  splitGaps,
  sumBuckets,
  text,
  timeTicks,
  unitFactor,
} from "../../custom_components/sourceful_zap/frontend/zap-cards.js";

const MINUTE = 60e3;
const HOUR = 3600e3;
const DAY = 24 * HOUR;

/* A pretend Home Assistant: entities, devices and states the strategy reads. */
function fakeHass({ language = "en", devices }) {
  const hass = { locale: { language }, entities: {}, devices: {}, states: {} };
  for (const [deviceId, device] of Object.entries(devices)) {
    hass.devices[deviceId] = { name: device.name, primary_config_entry: device.entry };
    for (const [key, state] of Object.entries(device.sensors)) {
      const entityId = `sensor.${deviceId}_${key}`;
      hass.entities[entityId] = {
        entity_id: entityId, device_id: deviceId, platform: device.platform || "sourceful_zap", translation_key: key,
      };
      if (state !== null) hass.states[entityId] = { state: String(state), attributes: {} };
    }
  }
  return hass;
}

const P1 = {
  name: "P1 Uart p1m-1",
  entry: "entry1",
  sensors: {
    power: 400, energy_import: 8000000, energy_export: 0, grid_reactive_power: -120,
    l1_power: 100, l2_power: 200, l3_power: 100, l1_current: 0.4, l2_current: 0.9, l3_current: 0.4,
    l1_voltage: 233, l2_voltage: 232, l3_voltage: 231,
  },
};
const GATEWAY = {
  name: "Zap Gateway zap-1",
  entry: "entry1",
  sensors: {
    gateway_firmware_version: "7.0.5", gateway_uptime: 1000, gateway_signal_strength: -60,
    gateway_wifi_ssid: "Home", gateway_wifi_status: "connected", gateway_temperature: 40,
    gateway_memory_free: 100, gateway_memory_percent: 60,
  },
};
const HYBRID = {
  name: "Solis 1033",
  entry: "entry2",
  sensors: {
    power: -300, grid_power: 150, inverter_power: 800, battery_soc: 80, battery_power: -300,
    energy_import: 100, energy_export: 500, energy_production: 900, battery_charge_total: 10,
    battery_discharge_total: 20, temperature: 30, battery_temperature: 25, grid_frequency: 50,
    mppt1_power: 400, mppt2_power: 300, mppt1_voltage: 350, mppt2_voltage: 340,
    battery_upper_limit: null,
  },
};

const typesOf = (cards) => cards.map((card) => card.type.replace("custom:zap-", ""));

test("version is set", () => {
  assert.match(VERSION, /^\d+\.\d+\.\d+$/);
});

test("niceScale covers the data with round steps", () => {
  assert.deepEqual(niceScale(0, 1961).ticks, [0, 500, 1000, 1500, 2000]);
  assert.deepEqual(niceScale(228.1, 236.4).ticks, [225, 230, 235, 240]);
  assert.deepEqual(niceScale(-136, -120).ticks, [-140, -135, -130, -125, -120]);
  const small = niceScale(0, 0.37);
  assert.deepEqual(small.ticks, [0, 0.1, 0.2, 0.3, 0.4]);
  assert.equal(small.decimals, 1);
  assert.equal(niceScale(49.95, 50.04).decimals, 2);
});

test("niceScale handles a flat line and bad input", () => {
  const flat = niceScale(5, 5);
  assert.ok(flat.min <= 5 && flat.max >= 5 && flat.max > flat.min);
  const zero = niceScale(0, 0);
  assert.equal(zero.min, 0);
  assert.ok(zero.max > 0);
  const bad = niceScale(NaN, Infinity);
  assert.ok(Number.isFinite(bad.min) && Number.isFinite(bad.max));
  for (const [lo, hi] of [[0, 1], [3, 987654], [-0.004, 0.003], [1e-6, 2e-6]]) {
    const scale = niceScale(lo, hi);
    assert.ok(scale.min <= lo && scale.max >= hi, `${lo}..${hi}`);
    assert.ok(scale.ticks.length >= 2 && scale.ticks.length <= 12, `${lo}..${hi}: ${scale.ticks.length} ticks`);
  }
});

test("timeTicks stay inside the window, on round clock times", () => {
  const end = new Date(2026, 10, 14, 0, 16).getTime();
  const day = timeTicks(end - DAY, end, 900);
  assert.equal(day.step, 2 * HOUR);
  assert.ok(day.ticks.length >= 6 && day.ticks.length <= 13);
  for (const tick of day.ticks) {
    assert.ok(tick.t >= end - DAY && tick.t <= end);
    const at = new Date(tick.t);
    assert.equal(at.getMinutes(), 0);
    assert.equal(at.getHours() % 2, 0);
    assert.equal(tick.major, at.getHours() === 0);
  }
  assert.equal(day.ticks.filter((tick) => tick.major).length, 1);

  const week = timeTicks(end - 7 * DAY, end, 300);
  assert.ok(week.step >= DAY);
  for (const tick of week.ticks) assert.equal(new Date(tick.t).getHours(), 0);

  const hour = timeTicks(end - HOUR, end, 600);
  assert.ok(hour.step <= 15 * MINUTE);
  assert.ok(hour.ticks.length >= 3);
});

test("units convert within power and within energy only", () => {
  assert.equal(unitFactor("Wh", "kWh"), 0.001);
  assert.equal(unitFactor("kWh", "Wh"), 1000);
  assert.equal(unitFactor("kW", "W"), 1000);
  assert.equal(unitFactor("W", "W"), 1);
  assert.equal(unitFactor("W", "kWh"), 1);
  assert.equal(unitFactor("V", "W"), 1);
  assert.equal(unitFactor("", "W"), 1);
});

test("range keys are hours or days", () => {
  assert.equal(hoursOf("6h"), 6);
  assert.equal(hoursOf("7d"), 168);
  assert.ok(Number.isNaN(hoursOf("custom")));
  assert.ok(Number.isNaN(hoursOf("7w")));
});

test("lines read raw states for short ranges and statistics for long or old ones", () => {
  const now = Date.UTC(2026, 10, 14, 12);
  assert.equal(meanSource(now - HOUR, now, now), "history");
  assert.equal(meanSource(now - 6 * HOUR, now, now), "history");
  assert.equal(meanSource(now - DAY, now, now), "5minute");
  assert.equal(meanSource(now - 7 * DAY, now, now), "hour");
  // Two hours, three weeks ago: the raw states are gone
  assert.equal(meanSource(now - 21 * DAY, now - 21 * DAY + 2 * HOUR, now), "hour");
});

test("energy bars get wider with the range", () => {
  const now = Date.UTC(2026, 10, 14, 12);
  assert.deepEqual(barPlan(now - HOUR, now, now), { period: "5minute", bucket: 5 * MINUTE, label: "per_5min" });
  assert.deepEqual(barPlan(now - 6 * HOUR, now, now), { period: "5minute", bucket: 15 * MINUTE, label: "per_15min" });
  assert.deepEqual(barPlan(now - DAY, now, now), { period: "5minute", bucket: HOUR, label: "per_hour" });
  assert.deepEqual(barPlan(now - 7 * DAY, now, now), { period: "hour", bucket: DAY, label: "per_day" });
  // Old ranges have hourly statistics only
  assert.deepEqual(barPlan(now - 21 * DAY, now - 20 * DAY, now), { period: "hour", bucket: HOUR, label: "per_hour" });
});

test("sumBuckets adds statistics rows into clock-aligned bars", () => {
  const start = new Date(2026, 10, 13, 14, 0).getTime();
  const rows = [];
  for (let i = 0; i < 12; i += 1) rows.push({ t0: start + i * 5 * MINUTE, t1: start + (i + 1) * 5 * MINUTE, v: 1 });
  const quarters = sumBuckets(rows, 15 * MINUTE);
  assert.equal(quarters.length, 4);
  assert.deepEqual(quarters.map((row) => row.v), [3, 3, 3, 3]);
  assert.equal(quarters[0].t0, start);
  assert.equal(quarters[1].t0, start + 15 * MINUTE);
  assert.deepEqual(sumBuckets(rows, HOUR), [{ t0: start, t1: start + HOUR, v: 12 }]);
  // Rows as wide as the bar pass through
  assert.equal(sumBuckets(rows, 5 * MINUTE).length, 12);

  const midnight = new Date(2026, 10, 13).getTime();
  const hours = [];
  for (let i = 20; i < 28; i += 1) hours.push({ t0: midnight + i * HOUR, t1: midnight + (i + 1) * HOUR, v: 2 });
  const days = sumBuckets(hours, DAY);
  assert.deepEqual(days.map((row) => [row.t0, row.v]), [[midnight, 8], [midnight + DAY, 8]]);
});

test("downsample keeps the mean and never returns more points than asked", () => {
  const points = [];
  for (let i = 0; i < 1000; i += 1) points.push({ t: i * 1000, v: i % 2 ? 10 : 20 });
  const few = downsample(points, 0, 1000e3, 100);
  assert.ok(few.length <= 100);
  for (const point of few) assert.ok(point.v > 14 && point.v < 16, `bucket mean ${point.v}`);
  for (let i = 1; i < few.length; i += 1) assert.ok(few[i].t > few[i - 1].t);
  assert.equal(downsample(points.slice(0, 50), 0, 50e3, 100).length, 50);
});

test("splitGaps breaks a line where the data stops", () => {
  const points = [];
  for (let i = 0; i < 20; i += 1) points.push({ t: i * 10e3, v: 1 });
  for (let i = 0; i < 20; i += 1) points.push({ t: HOUR + i * 10e3, v: 1 });
  const parts = splitGaps(points);
  assert.deepEqual(parts.map((part) => part.length), [20, 20]);
  assert.equal(splitGaps(points.slice(0, 20)).length, 1);
  assert.equal(splitGaps([]).length, 1);
});

test("splitGaps keeps sparse statistics and their dense raw tail as one line", () => {
  // Three 5-minute means, then raw states every 10 seconds
  const points = [{ t: 0, v: 1 }, { t: 5 * MINUTE, v: 1 }, { t: 10 * MINUTE, v: 1 }];
  for (let i = 1; i <= 60; i += 1) points.push({ t: 12 * MINUTE + i * 10e3, v: 1 });
  assert.deepEqual(splitGaps(points).map((part) => part.length), [1, 1, 1, 60], "without the spacing the means fall apart");
  assert.equal(splitGaps(points, 5 * MINUTE).length, 1);
  // A real outage still splits
  const outage = [...points, { t: 3 * HOUR, v: 1 }, { t: 3 * HOUR + 10e3, v: 1 }];
  assert.equal(splitGaps(outage, 5 * MINUTE).length, 2);
});

test("series colors come from the palette slots, stepped for the surface", () => {
  assert.equal(seriesColor("blue", 0, true), "#3987e5");
  assert.equal(seriesColor("blue", 0, false), "#2a78d6");
  assert.equal(seriesColor(undefined, 1, true), "#d95926");
  assert.equal(seriesColor("#123456", 0, true), "#123456");
  assert.equal(seriesColor(undefined, 8, true), seriesColor(undefined, 0, true));
});

test("text falls back to English", () => {
  assert.equal(text({ locale: { language: "sv" } }, "apply"), "Använd");
  assert.equal(text({ locale: { language: "sv-SE" } }, "apply"), "Använd");
  assert.equal(text({ locale: { language: "de" } }, "apply"), "Apply");
  assert.equal(text(undefined, "apply"), "Apply");
  assert.equal(text({ language: "en" }, "not_a_key"), "not_a_key");
});

test("collectDevices groups sensors by Zap and ignores other integrations", () => {
  const hass = fakeHass({
    devices: {
      meter: P1, gateway: GATEWAY, hybrid: HYBRID,
      other: { name: "Other", entry: "x", platform: "shelly", sensors: { power: 1 } },
    },
  });
  const groups = collectDevices(hass);
  assert.equal(groups.length, 2);
  const [solis, zap] = groups;
  assert.equal(solis.gateway, null);
  assert.deepEqual(solis.devices.map((device) => device.name), ["Solis 1033"]);
  assert.equal(zap.gateway.name, "Zap Gateway zap-1");
  assert.deepEqual(zap.devices.map((device) => device.name), ["P1 Uart p1m-1"]);
  assert.equal(zap.devices[0].roles.l2_power, "sensor.meter_l2_power");
  // A sensor without a state, such as a disabled one, is left out
  assert.equal(solis.devices[0].roles.battery_upper_limit, undefined);
});

test("the dashboard for a P1 meter has tiles, charts and the gateway", () => {
  const hass = fakeHass({ language: "sv", devices: { meter: P1, gateway: GATEWAY } });
  const board = buildDashboard(hass);
  assert.equal(board.views.length, 1);
  const [view] = board.views;
  assert.equal(view.type, "sections");
  assert.equal(view.max_columns, 3);
  assert.equal(view.background, "#111217");
  assert.equal(view.sections.length, 2);

  const [meter, gateway] = view.sections;
  assert.deepEqual(typesOf(meter.cards), [
    "range-picker", "stat-card", "stat-card", "stat-card", "stat-card", "stat-card",
    "heading-card",
    "chart-card", "chart-card", "chart-card", "chart-card", "chart-card", "chart-card",
  ]);
  assert.equal(meter.cards[0].title, "P1 Uart p1m-1");
  const tiles = meter.cards.filter((card) => card.type === "custom:zap-stat-card");
  assert.deepEqual(tiles.map((card) => card.name), ["Effekt just nu", "L1", "L2", "L3", "Import idag"]);
  assert.equal(tiles[0].hero, true);
  assert.equal(tiles[0].entity, "sensor.meter_power");
  assert.deepEqual(tiles[1].secondary.map((item) => item.entity), ["sensor.meter_l1_current", "sensor.meter_l1_voltage"]);
  assert.equal(tiles[4].mode, "today");
  // Tiles fill one row of the 36 columns
  assert.equal(tiles.reduce((sum, card) => sum + card.grid_options.columns, 0), 36);

  const charts = meter.cards.filter((card) => card.type === "custom:zap-chart-card");
  assert.deepEqual(charts.map((card) => card.title),
    ["Effekt", "Import", "Effekt per fas", "Ström per fas", "Spänning per fas", "Reaktiv effekt"]);
  assert.deepEqual(charts.map((card) => card.kind), ["area", "bar", "line", "line", "line", "line"]);
  assert.deepEqual(charts.map((card) => card.grid_options.columns), [24, 12, 12, 12, 12, 36]);
  assert.deepEqual(charts[2].series.map((item) => [item.name, item.color]),
    [["L1", "blue"], ["L2", "orange"], ["L3", "aqua"]]);
  // No export yet: the bars show import only
  assert.deepEqual(charts[1].series.map((item) => item.entity), ["sensor.meter_energy_import"]);
  for (const card of meter.cards) assert.equal(card.appearance, "zap");

  assert.deepEqual(typesOf(gateway.cards),
    ["heading-card", "stat-card", "stat-card", "stat-card", "stat-card", "stat-card"]);
  assert.equal(gateway.cards[0].title, "Zap-gateway");
  assert.equal(gateway.cards.slice(1).reduce((sum, card) => sum + card.grid_options.columns, 0), 36);
  assert.deepEqual(gateway.cards[3].secondary[1].map, { connected: "Ansluten", disconnected: "Frånkopplad" });
});

test("a hybrid inverter gets solar, battery and flow charts", () => {
  const board = buildDashboard(fakeHass({ devices: { hybrid: HYBRID } }));
  const cards = board.views[0].sections[0].cards;
  const tiles = cards.filter((card) => card.type === "custom:zap-stat-card").map((card) => card.name);
  assert.deepEqual(tiles, [
    "Power now", "Grid power", "Inverter power", "Battery",
    "Import today", "Export today", "Production today", "Charged today", "Discharged today", "Temperature",
  ]);
  const charts = cards.filter((card) => card.type === "custom:zap-chart-card");
  assert.deepEqual(charts.map((card) => card.title), [
    "Power", "Energy", "Power flows", "Frequency", "State of charge", "Battery",
    "Solar input power", "Solar input voltage", "Temperature",
  ]);
  const energy = charts[1];
  assert.equal(energy.kind, "bar");
  assert.deepEqual(energy.series.map((item) => item.name), ["Import", "Production", "Export"]);
  assert.deepEqual(charts[2].series.map((item) => item.name), ["Grid", "Inverter", "Battery"]);
  // Small charts go three to a row; the last row is stretched to fill it
  const small = charts.slice(2).map((card) => card.grid_options.columns);
  assert.deepEqual(small, [12, 12, 12, 12, 12, 12, 36]);
  // The view has no gateway: this device carries the range picker
  assert.equal(cards[0].type, "custom:zap-range-picker");
});

test("the look can follow the Home Assistant theme", () => {
  const board = buildDashboard(fakeHass({ devices: { meter: P1 } }), { appearance: "theme" });
  const [view] = board.views;
  assert.equal(view.background, undefined);
  for (const card of view.sections[0].cards) assert.equal(card.appearance, undefined);
});

test("two Zaps give two views with their own paths", () => {
  const board = buildDashboard(fakeHass({ devices: { meter: P1, gateway: GATEWAY, hybrid: HYBRID } }));
  assert.deepEqual(board.views.map((view) => view.path), ["zap-1", "zap-2"]);
  assert.deepEqual(board.views.map((view) => view.title), ["Solis 1033", "Zap Gateway zap-1"]);
});

test("a Zap with only a gateway device still gets a view with the picker", () => {
  const board = buildDashboard(fakeHass({ devices: { gateway: GATEWAY } }));
  const cards = board.views[0].sections[0].cards;
  assert.equal(cards[0].type, "custom:zap-range-picker");
  assert.equal(cards.length, 6);
});

test("no sensors gives a note instead of an empty dashboard", () => {
  const board = buildDashboard({ locale: { language: "sv" }, entities: {}, devices: {}, states: {} });
  assert.equal(board.views.length, 1);
  assert.equal(board.views[0].cards[0].type, "markdown");
  assert.match(board.views[0].cards[0].content, /Sourceful Zap/);
});
