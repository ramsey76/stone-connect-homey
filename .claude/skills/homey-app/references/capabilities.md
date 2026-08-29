# Capabilities

A capability is one typed, named state or action of a device (`onoff`, `dim`, `measure_temperature`).
Homey ships 184 **system capabilities**, generates Flow cards and UI components for each of them, and lets an app
declare its own **custom capabilities**. This file is the complete reference: the system-capability table, every
`capabilitiesOptions` key, sub-capabilities, the custom-capability schema, and the `Device` capability API.
Drivers and the `Device` class: `references/drivers-and-devices.md`. Flow cards: `references/flow-cards.md`.
Energy specifics: `references/energy.md`.

## Declaring capabilities

`capabilities` is a required string array on every driver manifest entry. It can be overridden per device during
pairing (`capabilities` / `capabilitiesOptions` on the device object returned by `onPairListDevices()`).

```json
{
  "name": { "en": "My Driver" },
  "class": "light",
  "capabilities": ["onoff", "dim", "measure_temperature.inside"],
  "capabilitiesOptions": {
    "dim": { "preventInsights": true },
    "measure_temperature.inside": { "title": { "en": "Inside" } }
  },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  }
}
```

Value types are `boolean`, `number`, `string` and `enum`. A capability value is always one of
`boolean | number | string | null`; `null` means "unknown". `getCapabilityValue()` returns `null` for an unknown
value — never `undefined` and never a type-appropriate default.

## Keeping Homey and the device in sync

Capabilities are synchronised **both ways** and the two directions use different APIs:

| Direction | API | Use for |
| --- | --- | --- |
| device → Homey | `Device#setCapabilityValue(capabilityId, value)` | The physical device changed (poll result, push event, external switch). |
| Homey → device | `Device#registerCapabilityListener(capabilityId, listener)` | The user or a Flow *requests* a state change. Throw from the listener to report failure. |

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDevice extends Homey.Device {

  async onInit() {
    // Homey → device
    this.registerCapabilityListener('onoff', async (value, opts) => {
      await DeviceApi.setMyDeviceState({ on: value });
    });

    // device → Homey
    DeviceApi.on('state-changed', (isOn) => {
      this.setCapabilityValue('onoff', isOn).catch(this.error);
    });
  }

}

module.exports = MyDevice;
```

---

## Device capability API

| Method | Returns | Notes |
| --- | --- | --- |
| `getCapabilities()` | `Array<string>` | The device's capability ids, including sub-capabilities. |
| `hasCapability(capabilityId)` | `boolean` | |
| `addCapability(capabilityId)` | `async` | **Expensive — use only when needed.** |
| `removeCapability(capabilityId)` | `async` | **Expensive.** Any Flow that depends on this capability becomes broken. |
| `getCapabilityValue(capabilityId)` | `any` | `null` when unknown. |
| `setCapabilityValue(capabilityId, value)` | `Promise<void>` | Only two arguments — there is no `opts` parameter. |
| `getCapabilityOptions(capabilityId)` | `any` | The merged options object for that capability. |
| `setCapabilityOptions(capabilityId, options)` | `async` | **Expensive — use only when needed.** |
| `registerCapabilityListener(capabilityId, listener)` | — | Invoked when a state change is *requested*. |
| `registerMultipleCapabilityListener(capabilityIds, listener, timeout)` | — | Debounced multi-capability listener; `timeout` defaults to `250` ms. |
| `triggerCapabilityListener(capabilityId, value, opts)` | `Promise<any>` | Runs the registered listener programmatically **and updates the capability value**. |
| `getState()` | `any` | All capability values as one object. |

Callback type definitions:

| Typedef | Signature | Arguments |
| --- | --- | --- |
| `Device.CapabilityCallback` | `(value, opts) => Promise<void> \| void` | `value`: the new value. `opts`: object with optional properties, e.g. `{ duration: 300 }`. |
| `Device.MultipleCapabilityCallback` | `(capabilityValues, capabilityOptions) => Promise<void> \| void` | `capabilityValues`: `{ dim: 0.5 }`. `capabilityOptions`: per-capability options, e.g. `{ dim: { duration: 300 } }`. |

```javascript
this.registerCapabilityListener('dim', async (value, opts) => {
  this.log('value', value);
  this.log('opts', opts);
});

this.registerMultipleCapabilityListener(
  ['dim', 'light_hue', 'light_saturation'],
  async (capabilityValues, capabilityOptions) => {
    this.log('capabilityValues', capabilityValues);
    this.log('capabilityOptions', capabilityOptions);
  },
  500,
);
```

### registerMultipleCapabilityListener and its debounce

The third argument is the debounce window in milliseconds (default `250`). Within that window every requested
capability change is collected and the listener is called **once** with all of them. Only the capabilities that
actually changed appear in `capabilityValues` — always guard with `typeof x !== 'undefined'` (or destructure with
defaults) before using a value.

Use it whenever sending two commands to the device would cause a visible glitch: `onoff` + `dim` on a light,
colour capabilities on a bulb, `windowcoverings_state` + `windowcoverings_set` on a motor.

### triggerCapabilityListener

Runs your own registered listener as if Homey had requested the change, and updates the stored capability value.
Use it to route a custom Flow action card through the same code path as the UI:

```javascript
this.homey.flow.getActionCard('boost').registerRunListener(async ({ device }) => {
  await device.triggerCapabilityListener('onoff', true, { duration: 5000 });
});
```

### registerReportListener

`registerReportListener` is **not** a `Homey.Device` method. It belongs to the Zigbee mesh driver of SDK v2 and is
**deprecated in SDK v3 in favour of a `BoundCluster` implementation** — see
`references/wireless-zigbee.md`. Do not call it on a plain `Homey.Device`.

### Adding capabilities to already-paired devices (guarded migration)

`addCapability()`, `removeCapability()` and `setCapabilityOptions()` are explicitly documented as expensive. Never
run them unconditionally in `onInit()`. Gate the migration behind a store flag so it runs exactly once per device,
and guard each call with `hasCapability()`:

```javascript
'use strict';

const Homey = require('homey');

const MIGRATION_KEY = 'migrated_v2';

class MyDevice extends Homey.Device {

  async onInit() {
    await this.migrate();
    this.registerCapabilityListener('onoff', this.onCapabilityOnoff.bind(this));
  }

  async migrate() {
    if (this.getStoreValue(MIGRATION_KEY)) return;

    if (!this.hasCapability('measure_power')) {
      await this.addCapability('measure_power');
    }
    if (this.hasCapability('meter_power.legacy')) {
      await this.removeCapability('meter_power.legacy');
    }
    await this.setCapabilityOptions('measure_temperature', { min: -20, max: 60 });

    await this.setStoreValue(MIGRATION_KEY, true);
  }

  async onCapabilityOnoff(value, opts) {
    // ...
  }

}

module.exports = MyDevice;
```

Capabilities must be added **before** the listener that uses them is registered, otherwise
`registerCapabilityListener()` targets a capability the device does not have yet.

---

## Full system capability table (184)

Generated from `athombv/node-homey-lib` v2.51.4 — the package `homey app validate` uses, and the same data behind
the [Device Capability Reference](https://apps-sdk-v3.developer.homey.app/tutorial-device-capabilities.html).

Legend: **get**/**set** = `getable`/`setable`. **QA** = `uiQuickAction`, offered as a quick action on the device
tile. **Ins** = logged to Insights by default (`insights: true`). **min Homey** = the capability's
`minCompatibility`; the app manifest's `compatibility` range must allow at least that version or
`homey app validate` fails with `capability: <id> is not available for compatibility <range>`.
Number capabilities in `%` with `min 0, max 1` take a **fraction**, not 0–100.

| id | type | get | set | units | range / values | uiComponent | QA | Ins | min Homey | title — meaning |
| --- | --- | :-: | :-: | --- | --- | --- | :-: | :-: | --- | --- |
| `onoff` | boolean | y | y |  |  | `toggle` | y | y |  | Turned on |
| `dim` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  |  |  | Dim level |
| `light_hue` | number | y | y |  | min 0, max 1, 2 dec | `color` |  |  |  | Hue |
| `light_saturation` | number | y | y |  | min 0, max 1, 2 dec | `color` |  |  |  | Color saturation |
| `light_temperature` | number | y | y |  | min 0, max 1, 2 dec | `color` |  |  |  | Color temperature |
| `light_mode` | enum | y | y |  | `color` `temperature` | `color` |  |  |  | Light mode — Switch between color or temperature mode |
| `vacuumcleaner_state` | enum | y | y |  | `cleaning` `spot_cleaning` `docked` `charging` `stopped` | `picker` |  |  |  | Vacuum cleaner state |
| `thermostat_mode` | enum | y | y |  | `auto` `heat` `cool` `off` | `picker` |  |  |  | Thermostat mode — Mode of the thermostat |
| `target_temperature` | number | y | y | °C | min 4, max 35, 1 dec | `thermostat` |  | y |  | Target temperature |
| `measure_temperature` | number | y | – | °C | 1 dec | `sensor` |  | y |  | Temperature — Temperature in degrees Celsius (°C) |
| `measure_co` | number | y | – | ppm | 2 dec | `sensor` |  | y |  | CO — CO in Parts-per-million (ppm) |
| `measure_co2` | number | y | – | ppm | 2 dec | `sensor` |  | y |  | CO₂ — CO₂ in Parts-per-million (ppm) |
| `measure_pm25` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y |  | PM2.5 — Atmospheric particulate matter (μg/m³) |
| `measure_humidity` | number | y | – | % | 2 dec | `sensor` |  | y |  | Humidity — Humidity in percent (%) |
| `measure_pressure` | number | y | – | mbar | 0 dec | `sensor` |  | y |  | Pressure — Pressure in millibar (mbar) |
| `measure_noise` | number | y | – | dB | 2 dec | `sensor` |  | y |  | Noise — Noise in decibel (dB) |
| `measure_rain` | number | y | – | mm | 2 dec | `sensor` |  | y |  | Rain — Rain in millimeter (mm) |
| `measure_wind_strength` | number | y | – | km/h | 2 dec | `sensor` |  | y |  | Wind strength — Wind Strength in kilometer per hour (km/h) |
| `measure_wind_angle` | number | y | – | ° | 2 dec | `sensor` |  | y |  | Wind angle — Wind angle in degrees (°) |
| `measure_gust_strength` | number | y | – | km/h | 2 dec | `sensor` |  | y |  | Gust strength — Gust strength in kilometer per hour (km/h) |
| `measure_gust_angle` | number | y | – | ° | 2 dec | `sensor` |  | y |  | Gust angle — Gust angle in degrees (°) |
| `measure_battery` | number | y | – | % | min 0, max 100, 2 dec | `battery` |  | y |  | Battery — Battery charge in percentage (%) |
| `measure_power` | number | y | – | W | 2 dec | `sensor` |  | y |  | Power — Power in watt (W) |
| `measure_voltage` | number | y | – | V | 2 dec | `sensor` |  | y |  | Voltage — Voltage (V) |
| `measure_current` | number | y | – | A | 2 dec | `sensor` |  | y |  | Current — Electric current (A) |
| `measure_luminance` | number | y | – | lx | 2 dec | `sensor` |  | y |  | Luminance — Luminance in Lux (lx) |
| `measure_ultraviolet` | number | y | – | UVI | 2 dec | `sensor` |  | y |  | Ultraviolet — Ultraviolet in UV index (UVI) |
| `measure_water` | number | y | – | L/min | 2 dec | `sensor` |  | y |  | Water flow — Water flow in liters per minute (L/min) |
| `alarm_generic` | boolean | y | – |  |  | `sensor` |  | y |  | Generic Alarm |
| `alarm_motion` | boolean | y | – |  |  | `sensor` |  | y |  | Motion Alarm |
| `alarm_contact` | boolean | y | – |  |  | `sensor` |  | y |  | Contact Alarm — Contact sensor, e.g. for windows (true/false) |
| `alarm_co` | boolean | y | – |  |  | `sensor` |  | y |  | CO Alarm — True when dangerous CO values have been detected |
| `alarm_co2` | boolean | y | – |  |  | `sensor` |  | y |  | CO₂ Alarm — True when dangerous CO₂ values have been detected |
| `alarm_pm25` | boolean | y | – |  |  | `sensor` |  | y |  | PM2.5 Alarm — True when PM2.5 values exceeds threshold |
| `alarm_tamper` | boolean | y | – |  |  | `sensor` |  | y |  | Tamper Alarm — True when tampering has been detected |
| `alarm_smoke` | boolean | y | – |  |  | `sensor` |  | y |  | Smoke Alarm — True when smoke has been detected |
| `alarm_fire` | boolean | y | – |  |  | `sensor` |  | y |  | Fire Alarm — True when fire has been detected |
| `alarm_heat` | boolean | y | – |  |  | `sensor` |  | y |  | Heat Alarm — True when extreme heat has been detected |
| `alarm_water` | boolean | y | – |  |  | `sensor` |  | y |  | Water Alarm — True when water has been detected |
| `alarm_battery` | boolean | y | – |  |  | `battery` |  | y |  | Battery Alarm — True when there is a battery warning |
| `alarm_night` | boolean | y | – |  |  | `sensor` |  | y |  | Night Alarm — True when it is night |
| `meter_power` | number | y | – | kWh | 2 dec | `sensor` |  | y |  | Energy — Energy usage in kilowatt-hour (kWh) |
| `meter_water` | number | y | – | m³ | min 0, 3 dec | `sensor` |  | y |  | Water meter — Water usage in cubic meter (m³) |
| `meter_gas` | number | y | – | m³ | min 0, 2 dec | `sensor` |  | y |  | Gas meter — Gas usage in cubic meter (m³) |
| `meter_rain` | number | y | – | m³ | 2 dec | `sensor` |  | y |  | Rain meter — Rain in cubic meter (m³) |
| `homealarm_state` | enum | y | y |  | `armed` `disarmed` `partially_armed` | `picker` |  |  |  | Home alarm state |
| `volume_set` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  |  |  | Set volume — Volume |
| `volume_up` | boolean | – | y |  |  | `button` |  |  |  | Volume up |
| `volume_down` | boolean | – | y |  |  | `button` |  |  |  | Volume down |
| `volume_mute` | boolean | y | y |  |  | `button` |  |  |  | Volume muted |
| `channel_up` | boolean | – | y |  |  | `button` |  |  |  | Channel up |
| `channel_down` | boolean | – | y |  |  | `button` |  |  |  | Channel down |
| `locked` | boolean | y | y |  |  | `toggle` |  | y |  | Locked — True when the lock is locked |
| `lock_mode` | enum | y | y |  | `always_locked` `always_unlocked` `locked_until_unlock` | `picker` |  |  |  | Lock mode |
| `garagedoor_closed` | boolean | y | y |  |  | `toggle` |  | y |  | Closed |
| `windowcoverings_state` | enum | y | y |  | `up` `idle` `down` | `ternary` |  |  |  | Window coverings state |
| `windowcoverings_tilt_up` | boolean | – | y |  |  | `button` |  |  |  | Window coverings tilt up |
| `windowcoverings_tilt_down` | boolean | – | y |  |  | `button` |  |  |  | Window coverings tilt down |
| `windowcoverings_tilt_set` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  |  |  | Window coverings tilt set |
| `windowcoverings_closed` | boolean | y | y |  |  | `toggle` |  |  |  | Closed |
| `windowcoverings_set` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  |  |  | Position — Set the position of window coverings. 0% is closed, 100% is open |
| `button` | boolean | – | y |  |  | `button` | y |  |  | Button |
| `speaker_playing` | boolean | y | y |  |  | `media` | y |  |  | Playing |
| `speaker_next` | boolean | – | y |  |  | `media` |  |  |  | Next |
| `speaker_prev` | boolean | – | y |  |  | `media` |  |  |  | Previous |
| `speaker_shuffle` | boolean | y | y |  |  | `media` |  |  |  | Shuffle |
| `speaker_repeat` | enum | y | y |  | `none` `track` `playlist` | `media` |  |  |  | Repeat |
| `speaker_artist` | string | y | – |  |  | `media` |  |  |  | Artist |
| `speaker_album` | string | y | – |  |  | `media` |  |  |  | Album |
| `speaker_track` | string | y | – |  |  | `media` |  |  |  | Track |
| `speaker_duration` | number | y | – |  |  | `media` |  |  |  | Duration |
| `speaker_position` | number | y | – |  |  | `media` |  |  |  | Position |
| `alarm_bin_full` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Bin Full Alarm — True when the bin is full |
| `alarm_bin_missing` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Bin Missing Alarm — True when the bin is missing. |
| `alarm_cleaning_pad_missing` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Cleaning Pad Missing Alarm — True when the cleaning pad is missing. |
| `alarm_cold` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Cold Alarm — True when the temperature is too low. |
| `alarm_connectivity` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Connectivity Alarm — True when disconnected from the network. |
| `alarm_door_fault` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Door Fault Alarm — True when there is an issue with the door or lock. |
| `alarm_gas` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Gas Alarm — True when gas is detected |
| `alarm_light` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Light Alarm — True when light is detected. |
| `alarm_lost` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Lost Alarm — True when the device is lost. |
| `alarm_moisture` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Moisture Alarm — True when moisture is detected. |
| `alarm_noise` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Noise Alarm — True when sound is detected. |
| `alarm_occupancy` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Occupancy Alarm — True when occupancy is detected. |
| `alarm_pm01` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | PM0.1 Alarm — True when PM0.1 values exceeds threshold |
| `alarm_pm1` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | PM1 Alarm — True when PM1 values exceeds threshold |
| `alarm_pm10` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | PM10 Alarm — True when PM10 values exceeds threshold |
| `alarm_power` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Power Alarm — True when power is detected. |
| `alarm_presence` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Presence Alarm — True when presence has been detected. |
| `alarm_problem` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Problem Alarm — True when a problem is detected. |
| `alarm_pump_device` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Pump Device Fault Alarm — True when a fault is detected in the pump device. |
| `alarm_pump_supply` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Pump Supply Fault Alarm — True when a fault is detected in the pump supply. |
| `alarm_running` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Running Alarm — True when the device is busy (e.g., printer is printing). |
| `alarm_safety` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Safety Alarm — True when unsafe. |
| `alarm_stuck` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Stuck Alarm — True when the device is stuck. |
| `alarm_tank_empty` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Tank Empty Alarm — True when the tank is empty. |
| `alarm_tank_missing` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Tank Missing Alarm — True when the tank is missing. |
| `alarm_tank_open` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Tank Open Alarm — True when the tank is open. |
| `alarm_vibration` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Vibration Alarm — True when vibration is detected. |
| `audio_output` | enum | y | y |  | `hdmi_1` `hdmi_2` `hdmi_3` `line_out` `optical` `usb` | `picker` |  |  | 12.2.0 | Audio Output — The audio output channel for a media player. |
| `battery_charging_state` | enum | y | – |  | `charging` `discharging` `idle` | `sensor` |  |  | 12.2.0 | Battery charging state — The current charging state of the battery. |
| `dishwasher_program` | enum | y | – |  | `normal` `heavy` `light` | `sensor` |  |  | 12.2.0 | Dishwasher program — The current program of the dishwasher. |
| `docked` | boolean | y | – |  |  | `sensor` |  | y | 12.2.0 | Docked — True when docked. |
| `fan_mode` | enum | y | y |  | `auto` `on` `off` | `picker` |  |  | 12.2.0 | Fan Mode |
| `fan_speed` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  | y | 12.2.0 | Fan speed — The fan speed in percentage. |
| `heater_operation_mode` | enum | y | y |  | `eco` `electric` `performance` `high_demand` `heat_pump` `gas` `off` | `picker` |  |  | 12.2.0 | Heater Operation Mode |
| `measure_hepa_filter` | number | y | – | % | min 0, max 100 | `sensor` |  |  | 12.2.0 | HEPA Filter — The HEPA filter level in percent. |
| `hot_water_mode` | enum | y | y |  | `on` `off` `eco` | `picker` |  |  | 12.2.0 | Hot water mode |
| `laundry_washer_cycles` | enum | y | y |  | `none` `normal` `extra` `max` | `picker` |  |  | 12.2.0 | Laundry washer cycles — The amount of cycles the laundry washer should perform. |
| `laundry_washer_program` | enum | y | – |  | `normal` `auto` `quick` `heavy` `whites` | `sensor` |  |  | 12.2.0 | Laundry washer program — The current program of the laundry washer. |
| `laundry_washer_speed` | enum | y | y |  | `low` `medium` `high` | `picker` |  |  | 12.2.0 | Laundry washer speed — The spin speed of the laundry washer. |
| `level_aqi` | enum | y | – |  | `good` `fair` `moderate` `poor` `very_poor` `extremely_poor` | `sensor` |  |  | 12.2.0 | Air quality level — The air quality index represented as a level. |
| `level_carbon_filter` | enum | y | – |  | `ok` `warning` `critical` | `sensor` |  |  | 12.2.0 | Carbon filter level — The level of degredation on the active carbon filter. |
| `level_ch2o` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | Formaldehyde Level — The level of formaldehyde in the air. |
| `level_co` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | CO level — The level of CO in the air. |
| `level_co2` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | CO₂ Level — The level of CO₂ in the air. |
| `level_nox` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | NOx level — The level of nitrogen oxides in the air. |
| `level_o3` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | Ozone Level — The level of ozone in the air. |
| `level_pm1` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | PM1 level — The amount of PM1 particles in the air represented by a level. |
| `level_pm01` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | PM0.1 level — The level of PM0.1 particles in the air. |
| `level_pm10` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | PM10 level — The level of PM10 particles in the air. |
| `level_pm25` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | PM2.5 Level — The level of PM2.5 particles in the air. |
| `level_radon` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | Radon Level — The level of radioactive radon gas in the air. |
| `level_so2` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | SO₂ Level — The level of sulfur dioxide in the air. |
| `level_tvoc` | enum | y | – |  | `low` `medium` `high` `critical` | `sensor` |  |  | 12.2.0 | TVOC Level — The level of total volatile organic compounds in the air. |
| `measure_aqi` | number | y | – |  | min 0, max 500 | `sensor` |  | y | 12.2.0 | Air Quality Index |
| `measure_carbon_filter` | number | y | – | % | min 0, max 100 | `sensor` |  | y | 12.2.0 | Carbon Filter — The carbon filter level in percent. |
| `measure_ch2o` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | Formaldehyde — Formaldehyde in micrograms per cubic meter (μg/m³) |
| `measure_content_volume` | number | y | – | L | 2 dec | `sensor` |  | y | 12.2.0 | Volume — The volume of the content in liters. |
| `measure_data_rate` | number | y | – | b/s | 0 dec | `sensor` |  | y | 12.2.0 | Data Rate — The data rate in bits per second. |
| `measure_data_size` | number | y | – | bytes | 0 dec | `sensor` |  | y | 12.2.0 | Data Size — The data size in bytes. |
| `measure_distance` | number | y | – | m | 2 dec | `sensor` |  | y | 12.2.0 | Distance — The distance in meters. |
| `measure_frequency` | number | y | – | Hz | 2 dec | `sensor` |  | y | 12.2.0 | Frequency — The frequency in hertz. |
| `level_hepa_filter` | enum | y | – |  | `ok` `warning` `critical` | `sensor` |  |  | 12.2.0 | HEPA filter level — The level of degredation on the HEPA filter. |
| `measure_moisture` | number | y | – | % | min 0, max 100, 2 dec | `sensor` |  | y | 12.2.0 | Moisture — The moisture level in percentage. |
| `measure_monetary` | number | y | – | € | 2 dec | `sensor` |  | y | 12.2.0 | Monetary value — The monetary value with a currency (default: €). |
| `measure_nox` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | NOx — Nitrogen Oxides in micrograms per cubic meter (μg/m³) |
| `measure_o3` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | Ozone — Ozone in micrograms per cubic meter (μg/m³) |
| `measure_odor` | number | y | – | OU | 0 dec | `sensor` |  | y | 12.2.0 | Odor — Odor concentration in odor units. |
| `measure_ph` | number | y | – |  | 2 dec | `sensor` |  | y | 12.2.0 | pH level — The pH level of a aqueous solution. |
| `measure_pm1` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | PM1 — Atmospheric particulate matter (μg/m³) |
| `measure_pm01` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | PM0.1 — Atmospheric particulate matter (μg/m³) |
| `measure_pm10` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | PM10 — Atmospheric particulate matter (μg/m³) |
| `measure_radon` | number | y | – | Bq/m³ | 2 dec | `sensor` |  | y | 12.2.0 | Radon — Radon in Becquerel per cubic meter (Bq/m³) |
| `measure_rain_intensity` | number | y | – | mm/h | 2 dec | `sensor` |  | y | 12.2.0 | Rain Intensity — The rain intensity in millimeters per hour. |
| `measure_rotation` | number | y | – | ° | 1 dec | `sensor` |  | y | 12.2.0 | Rotation — The rotation in degrees. |
| `measure_signal_strength` | number | y | – | dB | 2 dec | `sensor` |  | y | 12.2.0 | Signal Strength — The signal strength in decibels. |
| `measure_so2` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | SO₂ — Sulfur dioxide in micrograms per cubic meter (μg/m³) |
| `measure_speed` | number | y | – | m/s | 2 dec | `sensor` |  | y | 12.2.0 | Speed — The speed in meters per second. |
| `measure_tvoc` | number | y | – | μg/m³ | 2 dec | `sensor` |  | y | 12.2.0 | TVOC — Total volatile organic compounds in micrograms per cubic meter (μg/m³) |
| `measure_tvoc_index` | number | y | – |  |  | `sensor` |  | y | 12.2.0 | TVOC index — Total volatile organic compounds index |
| `measure_weight` | number | y | – | g | 2 dec | `sensor` |  | y | 12.2.0 | Weight — Generic mass in grams; weight is used instead of mass to fit with everyday language. |
| `media_input` | enum | y | y |  | `hdmi_1` `hdmi_2` `hdmi_3` `usb_1` `usb_2` `component` | `picker` |  |  | 12.2.0 | Media Input — The input channel for a media player |
| `mower_state` | enum | y | y |  | `mowing` `docked` `paused` `error` | `picker` |  |  | 12.2.0 | Mower state — The current state of the lawnmower. |
| `operational_state` | enum | y | – |  | `stopped` `running` `paused` `error` | `sensor` |  |  | 12.2.0 | Operational state — The operational state of the appliance. |
| `oscillating` | boolean | y | y |  |  | `toggle` |  | y | 12.2.0 | Oscillating — Enable or disable oscillation. |
| `pump_mode` | enum | y | y |  | `constant_pressure` `compensated_pressure` `constant_flow` `constant_speed` `constant_temperature` `automatic` | `picker` |  |  | 12.2.0 | Pump mode — Used to set which setpoint regulates the pump. |
| `pump_setpoint` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  | y | 12.2.0 | Pump setpoint — The pump setpoint in percentage. |
| `refrigerator_mode` | enum | y | y |  | `normal` `rapid_cooling` `rapid_freezing` | `picker` |  |  | 12.2.0 | Refrigerator Mode — The mode of the refrigerator. |
| `speaker_stop` | boolean | – | y |  |  | `media` |  |  | 12.2.0 | Stop |
| `swing_mode` | enum | y | y |  | `vertical` `horizontal` `both` | `picker` |  |  | 12.2.0 | Swing mode |
| `target_humidity_max` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  | y | 12.2.0 | Maximum target humidity — The high end of the target humidity level in percent. |
| `target_humidity_min` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  | y | 12.2.0 | Minimum target humidity — The low end of the target humidity level in percent. |
| `target_humidity` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  | y | 12.2.0 | Target Humidity — The target humidity level in percent. |
| `target_power` | number | y | y | W | min -25000, max 25000, step 1, 0 dec | `slider` |  | y | 12.13.0 | Target power — Target power in watt |
| `target_power_mode` | enum | y | y |  | `device` `homey` | `picker` |  |  | 12.13.0 | Target power mode — The target power control mode |
| `target_temperature_level` | enum | y | y |  | `low` `medium` `high` | `picker` |  |  | 12.2.0 | Target temperature level — The target temperature level of the appliance. |
| `target_temperature_max` | number | y | y | °C | min 4, max 35, 2 dec | `slider` |  | y | 12.2.0 | Maximum target temperature — The high end of the temperature setpoint in degrees Celsius. |
| `target_temperature_min` | number | y | y | °C | min 4, max 35, 2 dec | `slider` |  | y | 12.2.0 | Minimum target temperature — The low end of the temperature setpoint in degrees Celsius. |
| `vacuumcleaner_job_mode` | enum | y | y |  | `off` `normal` `high` `turbo` `mop` `auto` | `picker` |  |  | 12.2.0 | Vacuum cleaner job mode |
| `valve_position` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  | y | 12.2.0 | Valve position — The current position of the valve in percent. |
| `ev_charging_state` | enum | y | – |  | `plugged_in_charging` `plugged_in_discharging` `plugged_in_paused` `plugged_in` `plugged_out` | `sensor` |  |  | 12.4.5 | Charging state — The current charging state of the battery. |
| `evcharger_charging_state` | enum | y | – |  | `plugged_in_charging` `plugged_in_discharging` `plugged_in_paused` `plugged_in` `plugged_out` | `sensor` |  |  | 12.4.5 | Charging state — The current charging state of the EV charger. |
| `evcharger_charging` | boolean | y | y |  |  | `toggle` |  | y | 12.4.5 | Charging |
| `oven_mode` | enum | y | y |  | `bake` `convection` `grill` `roast` `clean` `convection_bake` `convection_roast` `warming` `proofing` `steam` | `picker` |  |  | 12.11.0 | Oven Mode — The oven mode. |
| `microwave_mode` | enum | y | y |  | `normal` `defrost` `reheat` | `picker` |  |  | 12.11.0 | Microwave Mode — The microwave mode. |
| `laundry_dryer_dryness` | enum | y | y |  | `low` `normal` `extra` `max` | `picker` |  |  | 12.11.0 | Laundry dryer dryness — The dryness setting of the laundry dryer. |
| `alarm_freeze_risk` | boolean | y | – |  |  | `sensor` |  | y | 12.11.0 | Freeze Risk Alarm — True when in the current ambient conditions water could potentially freeze. |
| `alarm_rain` | boolean | y | – |  |  | `sensor` |  | y | 12.11.0 | Rain Alarm — True when rain is detected. |
| `alarm_open` | boolean | y | – |  |  | `sensor` |  | y | 12.11.0 | Open Alarm — True when a door/window/etc... is open. |
| `cooking_time` | number | y | y | s | min 0, max 86400, 0 dec | `sensor` |  | y | 12.11.0 | Cooking Time — The cooking time in seconds that is set. When no cooking time is set, the capability should be set to `null`. |
| `power_level` | number | y | y | % | min 0, max 1, 2 dec | `slider` |  |  | 12.11.0 | Power level |
| `power_boost` | boolean | y | y |  |  | `toggle` |  | y | 12.11.0 | Power Boost — When enabled, power boost mode is active. The device may use more energy to reach its target. |
| `progress` | number | y | – | % | min 0, max 100, 2 dec | `sensor` |  | y | 12.11.0 | Progress — The the percentage of the current task that is completed. When the task is currently not active the capability should be set to `null` |

### Naming prefixes

| Prefix | Type | Meaning |
| --- | --- | --- |
| `measure_*` | number | An instantaneous measurement. Selectable by users as a device indicator. |
| `meter_*` | number | A cumulative, monotonically increasing meter reading. Selectable as a device indicator. |
| `alarm_*` | boolean | An alarm. Grouped into one warning indicator by default; `true` values flash red in the `sensor` UI component. |
| `level_*` | enum | A measurement bucketed into a qualitative level. |
| `target_*` | number/enum | A user-settable setpoint. |
| `light_*` | number/enum | Colour and colour-temperature control. |
| `speaker_*` | mixed | Media transport and metadata; rendered by the `media` UI component. |
| `windowcoverings_*` | mixed | Motorised covering control. |
| `volume_*`, `channel_*` | mixed | AV controls. |

---

## Capability options (`capabilitiesOptions`)

Capability options change the default behaviour of a capability for one driver. They are declared in the driver
manifest under `capabilitiesOptions`, keyed by the **full** capability id (including any sub-capability suffix).
They can also be supplied per device during pairing, and changed at runtime with
`Device#setCapabilityOptions(capabilityId, options)`.

```json
{
  "name": { "en": "My Driver" },
  "class": "light",
  "capabilities": ["onoff", "dim"],
  "capabilitiesOptions": {
    "dim": { "preventInsights": true }
  }
}
```

### Options that apply to all capabilities

| Attribute | Description |
| --- | --- |
| `title` | Overwrite the capability title: `{ "en": "My Custom Title" }`. Keep a custom title to **2–3 words maximum**. |
| `titleShort` | Shorter variant of the title. **Requires `compatibility` `>=13.2.1`**; the CLI throws otherwise. |
| `preventInsights` | `true` prevents Insights from being automatically generated for this capability. |
| `preventTag` | `true` prevents a Flow Tag from being automatically generated for this capability. |

### `duration`

| Attribute | Description |
| --- | --- |
| `duration` | Set to `true` to allow users to set a duration on the Flow Action card associated with this capability. |

The configured duration is passed as the **second argument** to the capability listener (in milliseconds). It is
only present when the user actually filled it in, so always type-check.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

const DEFAULT_DIM_DURATION = 1000;

class MyDevice extends Homey.Device {

  async onInit() {
    this.registerCapabilityListener('dim', async (value, options) => {
      await DeviceApi.setMyDeviceState({
        on: value,
        duration: typeof options.duration === 'number'
          ? options.duration
          : DEFAULT_DIM_DURATION,
      });
    });
  }

}

module.exports = MyDevice;
```

When you enable `duration` through capability options you must **also** add `"duration": true` to each action Flow
card that should support it in `driver.flow.compose.json`:

```json
{
  "actions": [
    { "id": "on", "highlight": true, "duration": true, "title": { "en": "Turn on" } }
  ]
}
```

### Boolean capability options

Apply to boolean capabilities such as `onoff`, `windowcoverings_closed`, `garagedoor_closed`, `alarm_generic` and
`button`.

| Attribute | Description |
| --- | --- |
| `insightsTitleTrue` | Translation object describing the title when shown in a Timeline (value `true`). |
| `insightsTitleFalse` | Translation object describing the title when shown in a Timeline (value `false`). |
| `titleTrue` | Translation object describing the title when shown in a `sensor` UI component. |
| `titleFalse` | Translation object describing the title when shown in a `sensor` UI component. |

### Number capability options

Apply to number capabilities such as the `measure_*` capabilities.

| Attribute | Description |
| --- | --- |
| `units` | Translation object of the capability's units. If set to `"°C"` Homey can automatically convert the value to Fahrenheit. |
| `decimals` | The number of decimals to show in the UI. |
| `min` | A minimum for the capability value. |
| `max` | A maximum for the capability value. |
| `step` | A step size of the capability value. |

### Enum capability options

| Attribute | Description |
| --- | --- |
| `values` | An array of objects, each with a unique `id` and a `title` translation object. |

```json
"capabilitiesOptions": {
  "thermostat_mode": {
    "values": [
      { "id": "heat", "title": { "en": "Heat", "nl": "Verhitten" } },
      { "id": "cool", "title": { "en": "Cool", "nl": "Koelen" } }
    ]
  }
}
```

Overriding `values` is only available since **Homey v12.0.1** — raise the app's `compatibility` accordingly.

### Zone activity capability options

Some capabilities mark their device's zone active when their value changes.
Applies to `alarm_motion`, `alarm_contact`, `alarm_vibration`, `alarm_occupancy` and `alarm_presence`.

| Attribute | Description |
| --- | --- |
| `zoneActivity` | Controls whether changes to this capability value also trigger the zone to become active. Set to `false` to disable zone activity for this capability. |

**Gotcha — the documented scope is wider than the declared scope.** The documentation page lists all five
capabilities above, but `homey-lib` v2.51.4 only declares the `zoneActivity` option on **`alarm_motion`** and
**`alarm_contact`**. Setting it on `alarm_vibration`, `alarm_occupancy` or `alarm_presence` will not fail
validation (`capabilitiesOptions` is untyped), but do not rely on it having an effect there.

### Homey Energy capability options

Apply to `measure_power`:

| Attribute | Description |
| --- | --- |
| `approximated` | Shows the user that this power-usage measurement might not be accurate. Use it when the driver *calculates* `measure_power` rather than reading it from the device (e.g. Nanoleaf panels whose count the user changes). See `references/energy.md`. |

Apply to `target_power`:

| Attribute | Description |
| --- | --- |
| `excludeMin` | Lower bound of the exclude range (number). Values between `excludeMin` and `excludeMax` become 0. Must satisfy `excludeMin <= 0`. |
| `excludeMax` | Upper bound of the exclude range (number). Values between `excludeMin` and `excludeMax` become 0. Must satisfy `excludeMax >= 0`. |

Validation rules the CLI enforces for `target_power` (and any `target_power.*` sub-capability):

- `min`/`max` must include 0 (`min <= 0 <= max`) — every device needs an idle state.
- `excludeMin`/`excludeMax` must include 0 (`excludeMin <= 0 <= excludeMax`).
- Values are rounded **toward zero** to the nearest `step`; values inside the exclude range become 0; values outside
  `min`/`max` are clamped to the nearest boundary.

```json
"capabilitiesOptions": {
  "target_power": {
    "min": 0,
    "max": 11040,
    "step": 230,
    "excludeMin": 0,
    "excludeMax": 1380
  }
}
```

For `target_power_mode`, a custom `values` array must include `homey` and at least one non-`homey` value. The
default `device` value can be omitted if you define your own strategy values (e.g. `self_use`, `price_based`). The
prefix `homey_` is reserved and rejected by the CLI.

### Light device capability options

Apply to `onoff`:

| Attribute | Description |
| --- | --- |
| `setOnDim` | Set to `false` to prevent the `onoff` capability from being set when the `dim` capability is updated by a Flow action card. Homey then sends only a `dim` capability set instead of both. |
| `greyout` | When this capability is `false`, give a visual hint to grey out the device. Default `false`. |

### `getable`

Apply to `onoff` and `volume_mute`:

| Attribute | Description |
| --- | --- |
| `getable` | Set to `false` to make the `onoff` or `volume_mute` capability **stateless**. The device's `quickAction` is disabled, UI components are updated, and some Flow cards are added/removed. |

Available as of **Homey v7.2.1**. Adding `getable: false` to an existing driver **breaks users' Flows**, because it
removes a number of Flow cards belonging to the `onoff` / `volume_mute` capabilities.

### `maintenanceAction`

| Attribute | Description |
| --- | --- |
| `maintenanceAction` | `true` turns a `button`-derived capability into a maintenance action. |
| `title` | Required alongside `maintenanceAction`. Button label. |
| `desc` | Optional description shown under the button. |

See [Maintenance actions](#maintenance-actions) below.

### Options declared by the capability definition itself

`homey-lib` declares these on the capability, on top of the generic options above:

| capability | option | type | default |
| --- | --- | --- | --- |
| `onoff` | `setOnDim` | boolean | `true` |
| `onoff` | `greyout` | boolean | `false` |
| `measure_power` | `isApproximated` | boolean | `false` |
| `meter_power` | `isApproximated` | boolean | `false` |
| `alarm_motion` | `zoneActivity` | boolean | `true` |
| `alarm_contact` | `zoneActivity` | boolean | `true` |

**Gotcha:** the capability definition names the approximation flag `isApproximated`, while the official
documentation instructs you to write `approximated: true` in `capabilitiesOptions`. `capabilitiesOptions` is an
untyped object in the app schema, so **neither spelling fails validation** — follow the documentation and use
`approximated`.

### Translating capability options

`capabilitiesOptions[].title`, `.titleShort` and `.units` are translatable. Either write full translation objects
inline, or keep one file per language under **`/.homeycompose/locales/<lang>.json`** and let Homey Compose merge
them. The `$capabilities` / `$drivers` merge step only runs for languages that have a file in
`/.homeycompose/locales/` — a plain `/locales/<lang>.json` is still shipped as translations for
`this.homey.__()`, but its `$drivers` / `$capabilities` keys are **not** merged into `app.json`:

```json
{
  "$drivers": {
    "my_driver": {
      "capabilitiesOptions": {
        "measure_temperature.inside": { "title": "Binnen", "units": "°C" }
      }
    }
  },
  "$capabilities": {
    "my_numeric_capability": { "title": "Mijn numerieke mogelijkheid", "units": "Cb" }
  }
}
```

---

## Sub-capabilities — using the same capability more than once

Append a dot plus an identifier to reuse a capability on one device, e.g. `measure_temperature.inside` and
`measure_temperature.outside`.

```json
{
  "capabilities": [
    "measure_temperature.inside",
    "measure_temperature.outside",
    "onoff.socket1",
    "onoff.socket2"
  ],
  "capabilitiesOptions": {
    "measure_temperature.inside": { "title": { "en": "Inside" } },
    "measure_temperature.outside": { "title": { "en": "Outside" } },
    "onoff.socket1": { "title": { "en": "Socket 1" } },
    "onoff.socket2": { "title": { "en": "Socket 2" } }
  }
}
```

Rules:

- The part before the first `.` must be a valid system or app capability id. Validation, type, min/max and UI
  component are inherited from that base capability.
- Register listeners and set values with the **full** id: `this.registerCapabilityListener('onoff.socket1', …)`,
  `this.setCapabilityValue('measure_temperature.inside', 21.5)`. There is no automatic fan-out from the base id.
- `capabilitiesOptions` keys use the full sub-capability id too.
- **Flow Cards are not automatically generated for sub-capabilities** — you must create those cards yourself in
  `driver.flow.compose.json`. See `references/flow-cards.md`.
- Always give a sub-capability a `title` capability option; without one the UI shows several identically-named
  components.
- For the `thermostat` UI component, `target_temperature.<suffix>` and `measure_temperature.<suffix>` must use the
  **same suffix** to be displayed together.
- A **custom capability id may not contain a `.`** — the CLI throws
  `Invalid capability: <id>\nCharacter '.' is reserved for subcapabilities.`

---

## Custom capabilities

When no system capability fits, declare your own. With Homey Compose, one JSON file per capability under
`/.homeycompose/capabilities/<id>.json`; the filename becomes the capability id (override with `$id`). Compose
merges them into the app manifest's `capabilities` object.

```json
// /.homeycompose/capabilities/my_boolean_capability.json
{
  "type": "boolean",
  "title": { "en": "My Boolean capability" },
  "getable": true,
  "setable": true,
  "uiComponent": "toggle",
  "uiQuickAction": true,
  "icon": "/assets/my_boolean_capability.svg"
}
```

```json
// /.homeycompose/capabilities/my_numeric_capability.json
{
  "type": "number",
  "title": { "en": "My Numeric capability" },
  "uiComponent": "slider",
  "getable": true,
  "setable": false,
  "units": { "en": "Cb" },
  "min": 0,
  "max": 30,
  "step": 0.5
}
```

```json
// /drivers/my_driver/driver.compose.json
{
  "name": { "en": "My Driver" },
  "class": "other",
  "capabilities": ["onoff", "my_boolean_capability", "my_numeric_capability"],
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  }
}
```

### Full custom-capability schema

Validated by `homey app validate` against the `homey-lib` capability JSON schema. `title` and `type` are
**required**, and at least one of `getable` / `setable` must be present.

| Property | Type | Applies to | Description |
| --- | --- | --- | --- |
| `title` | i18n object \| string | all | **Required.** Capability title. |
| `titleShort` | i18n object \| string | all | Shorter title variant. |
| `desc` | i18n object \| string | all | Description of the capability. |
| `type` | `"boolean"` \| `"number"` \| `"string"` \| `"enum"` | all | **Required.** |
| `getable` | boolean | all | Default `true`. At least one of `getable`/`setable` must be specified. |
| `setable` | boolean | all | Default `true`. |
| `icon` | string | all | Path to an SVG, e.g. `/assets/my_capability.svg`. The file must exist — the CLI checks case-sensitively. |
| `insights` | boolean | all | Log values to Insights. |
| `insightsTitleTrue` | i18n object | boolean | Title shown in a Timeline when the value is `true`. |
| `insightsTitleFalse` | i18n object | boolean | Title shown in a Timeline when the value is `false`. |
| `chartType` | `"line"` \| `"area"` \| `"stepLine"` \| `"column"` \| `"spline"` \| `"splineArea"` \| `"scatter"` | number | Insights chart style. Only two are used by system capabilities: `stepLine` (20 capabilities — `dim`, `light_hue`, `light_saturation`, `light_temperature`, `power_level`, `progress`, `volume_set`, `windowcoverings_set`, `measure_current`, `measure_gust_angle`, `measure_gust_strength`, `measure_power`, `measure_voltage`, `measure_water`, `target_power`, `target_temperature`, `target_temperature_min`/`_max`, `target_humidity_min`/`_max`) and `spline` (46, the remaining `measure_*`/`meter_*` readings). Capabilities without a `chartType` fall back to Homey's default. |
| `decimals` | number | number | Decimals to show in the UI. |
| `min` | number | number | Minimum value. |
| `max` | number | number | Maximum value. |
| `step` | number (≥ 0) | number | Step size. |
| `units` | i18n object \| string | number | Units, e.g. `{ "en": "Cb" }`. Use `"°C"` to opt into Homey's automatic Fahrenheit conversion. |
| `values` | array | enum | **Required for `enum`.** `[{ "id": "option1", "title": { "en": "First option" } }]`. For a `ternary` UI component the three values must have the ids `up`, `idle` and `down`. |
| `uiComponent` | one of the ten component names, or `null` | all | See below. Omit to let Homey pick automatically. |
| `uiQuickAction` | boolean | boolean | Let the user quick-toggle the capability's value from the UI. |
| `uiState` | boolean | all | Present in the schema; not used by any system capability and not covered by the prose documentation. |

The schema allows additional properties, so app-specific keys do not fail validation — but only the keys above (and
`$id` / `$flow`, handled by Homey Compose) are interpreted.

Translations for `title`, `titleShort` and `units` of a custom capability can live in
`/.homeycompose/locales/<lang>.json` under `$capabilities.<id>`.

### Custom capabilities that shadow a system id

From Homey Pro (Early 2023) firmware **12.2.0** onwards, a custom capability whose id equals a system capability id
**no longer produces the system Flow cards** (matching the behaviour of Homey Pro 2016-2019). Two fixes:

1. **Easiest:** delete the custom capability from `/.homeycompose/capabilities/` so Homey uses the system capability
   and generates the system Flow cards again.
2. **Keep the custom capability** (when it genuinely differs) and re-declare the Flow cards with the *same Flow card
   ids* in each affected driver's `driver.flow.compose.json`, then register the matching run listeners in
   `App#onInit()`:

The complete set of run listeners documented for the affected capabilities — register these in `App#onInit()`
(`/app.js`). Only register the ones whose capability you actually shadow:

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    // --- alarm_contact ---
    this.homey.flow.getConditionCard('alarm_contact')
      .registerRunListener((args, state) => args.device.getCapabilityValue('alarm_contact'));

    // --- alarm_generic ---
    this.homey.flow.getConditionCard('alarm_generic')
      .registerRunListener((args, state) => args.device.getCapabilityValue('alarm_generic'));

    // --- alarm_motion ---
    this.homey.flow.getConditionCard('alarm_motion')
      .registerRunListener((args, state) => args.device.getCapabilityValue('alarm_motion'));

    // --- alarm_smoke ---
    this.homey.flow.getConditionCard('alarm_smoke')
      .registerRunListener((args, state) => args.device.getCapabilityValue('alarm_smoke'));

    // --- alarm_tamper ---
    this.homey.flow.getConditionCard('alarm_tamper')
      .registerRunListener((args, state) => args.device.getCapabilityValue('alarm_tamper'));

    // --- homealarm_state ---
    this.homey.flow.getDeviceTriggerCard('homealarm_state_changed')
      .registerRunListener((args, state) => args.device.getCapabilityValue('homealarm_state') === args.state);
    this.homey.flow.getConditionCard('homealarm_state_is')
      .registerRunListener((args, state) => args.device.getCapabilityValue('homealarm_state') === args.state);
    this.homey.flow.getActionCard('set_homealarm_state')
      .registerRunListener((args, state) => args.device.setCapabilityValue('homealarm_state', args.state));

    // --- onoff (note: `open` / `close` are the variants used by door- and valve-like classes) ---
    this.homey.flow.getConditionCard('on')
      .registerRunListener((args, state) => args.device.getCapabilityValue('onoff'));
    this.homey.flow.getConditionCard('open')
      .registerRunListener((args, state) => args.device.getCapabilityValue('onoff'));
    this.homey.flow.getActionCard('on')
      .registerRunListener((args, state) => args.device.setCapabilityValue('onoff', true));
    this.homey.flow.getActionCard('off')
      .registerRunListener((args, state) => args.device.setCapabilityValue('onoff', false));
    this.homey.flow.getActionCard('toggle')
      .registerRunListener((args, state) => {
        const value = args.device.getCapabilityValue('onoff');
        return args.device.setCapabilityValue('onoff', !value);
      });
    this.homey.flow.getActionCard('open')
      .registerRunListener((args, state) => args.device.setCapabilityValue('onoff', true));
    this.homey.flow.getActionCard('close')
      .registerRunListener((args, state) => args.device.setCapabilityValue('onoff', false));

    // --- target_temperature ---
    this.homey.flow.getActionCard('target_temperature_set')
      .registerRunListener((args, state) => args.device.setCapabilityValue('target_temperature', args.target_temperature));

    // --- thermostat_mode ---
    this.homey.flow.getDeviceTriggerCard('thermostat_mode_changed')
      .registerRunListener((args, state) => args.device.getCapabilityValue('thermostat_mode') === args.thermostat_mode);
    this.homey.flow.getConditionCard('thermostat_mode_is')
      .registerRunListener((args, state) => args.device.getCapabilityValue('thermostat_mode') === args.thermostat_mode);
    this.homey.flow.getActionCard('thermostat_mode_set')
      .registerRunListener((args, state) => args.device.setCapabilityValue('thermostat_mode', args.thermostat_mode));
  }

}

module.exports = MyApp;
```

Note the argument names differ per card: `homealarm_state` cards read `args.state`, the `thermostat_mode` cards
read `args.thermostat_mode`, and `target_temperature_set` reads `args.target_temperature`.

When several drivers need the same device Flow card, put the definition in `/.homeycompose/flow/actions/<id>.json`
and add a `device` argument with a `filter`:

```json
{
  "title": { "en": "Disco mode" },
  "args": [
    { "type": "device", "name": "device", "filter": "driver_id=my_driver" }
  ]
}
```

### Device indicators

The Homey web and mobile apps show an indicator next to the device icon. Custom boolean and number capabilities
participate too.

- **Boolean** capabilities starting with `alarm_` are grouped by default into a single warning icon that lights up
  when any of them is `true`. Users can instead pin one specific alarm capability. `alarm_battery` shows an "empty
  battery" icon instead of an exclamation mark.
- **Number** capabilities are shown as a numeric value plus their unit. Users can select capabilities starting with
  `measure_` or `meter_`. `measure_battery` always renders as a battery icon instead of a number.
- Users **cannot** select or override the default indicator when the device class is `thermostat`, `light`, `lock`
  or `speaker`.

---

## UI components

Every system capability has a UI component. Homey picks one automatically for custom capabilities; override with
`uiComponent`.

| `uiComponent` | Accepts | Notes |
| --- | --- | --- |
| `"toggle"` | one `boolean` capability | Look varies per capability. |
| `"slider"` | one `number` capability | Look varies per capability. |
| `"sensor"` | multiple `number`, `enum`, `string` or `boolean` capabilities | Booleans that are `true` and begin with `alarm_` flash red. |
| `"thermostat"` | `target_temperature`, optionally `measure_temperature` | Sub-capability suffixes must match to be grouped. |
| `"media"` | `speaker_playing`, `speaker_next`, `speaker_prev`, `speaker_shuffle`, `speaker_repeat` | Also shows album art set with `Device#setAlbumArtImage(image)`. (The docs page links this to `Device#setAlbumArt()` — **no such method exists**; the SDK v3 `Device` class only has `setAlbumArtImage`.) |
| `"color"` | `light_hue`, `light_saturation`, `light_temperature`, `light_mode` | |
| `"battery"` | either `measure_battery` or `alarm_battery` | Never both — see below. |
| `"picker"` | one `enum` capability | Value titles must fit on one line; max 3 words. |
| `"ternary"` | one `enum` capability with exactly three values | For motorised components; the three values should have the ids `up`, `idle`, `down`. |
| `"button"` | one or more `boolean` capabilities | Most buttons are stateless; a stateful button needs the capability to be both `setable` and `getable`. Related buttons such as `volume_up`/`volume_down` are grouped. |
| `null` | — | Hides the UI component entirely. |

---

## Maintenance actions

Requires Homey **v3.1.0** and Homey Smartphone App **v3.0.1**. A maintenance action must be a capability that
extends the system capability `button` (i.e. a `button.<suffix>` sub-capability). Mark it with
`maintenanceAction: true` plus a `title` (and optionally `desc`). The button moves to
*Device settings → Maintenance actions* and its `uiComponent` is hidden from the device view. Pressing it triggers
the registered capability listener; throwing from the listener surfaces the error to the user.

```json
{
  "name": { "en": "P1 Meter" },
  "capabilities": ["meter_power", "measure_power", "button.calibrate", "button.reset_meter"],
  "capabilitiesOptions": {
    "button.calibrate": {
      "maintenanceAction": true,
      "title": { "en": "Start calibration" },
      "desc": { "en": "Start the sensor calibration process." }
    },
    "button.reset_meter": {
      "maintenanceAction": true,
      "title": { "en": "Reset power meter" },
      "desc": { "en": "Reset the accumulated power usage (kWh), this can not be restored." }
    }
  }
}
```

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    this.registerCapabilityListener('button.reset_meter', async () => {
      // Maintenance action button was pressed
    });

    this.registerCapabilityListener('button.calibrate', async () => {
      throw new Error('Something went wrong');
    });
  }

}

module.exports = MyDevice;
```

Typical uses: starting a calibration process, resetting accumulated power measurements.

---

## Insights and Flow tags

- A capability with `insights: true` is logged to Insights automatically. Suppress it per driver with
  `"preventInsights": true`.
- Every capability also produces a Flow Tag automatically. Suppress it with `"preventTag": true`.
- `chartType` controls how a numeric Insights log is drawn.
- For booleans, `insightsTitleTrue` / `insightsTitleFalse` label the Timeline entries.

**Gotcha — Insights is write-only from inside an app.** `this.homey.insights` (`ManagerInsights`) exposes only
`createLog`, `deleteLog`, `getLog` and `getLogs`, and `InsightsLog` has exactly one method, `createEntry(value)`.
There is **no API to read log entries back**. `insights: true` on a capability logs values but gives your app no
way to retrieve them. If a widget or an app-settings page needs a trend, keep your own capped rolling buffer in
the device store and serve it through `api.js` — see `references/widgets.md`.

## System Flow cards generated per capability

Homey generates Flow cards (triggers, conditions and actions) for the system capabilities a driver declares —
**do not redeclare them** in `driver.flow.compose.json`. For the separate convention that applies to *custom*
capabilities, see `references/flow-cards.md`.

### The complete generated set

404 cards across 181 of the 184 system capabilities. Generated from
`homey-lib` v2.51.4 (`assets/capability/capabilities/<id>.json`, key `$flow`) — this table exists nowhere
in the documentation. A class filter means the card is only offered for devices whose `class` matches;
`|` inside a filter is an OR.

Card ids are relative to the capability, so the Flow card a user sees for `onoff` on a `light` is the
trigger `onoff_true`. Redeclaring any of these in `driver.flow.compose.json` produces a duplicate card
in the Flow editor and is a certification finding.

| capability | kind | card id | title (en) | only for class |
| --- | --- | --- | --- | --- |
| `onoff` | trigger | `onoff_true` | Turned on |  |
| `onoff` | trigger | `onoff_false` | Turned off |  |
| `onoff` | condition | `on` | Is turned !{{on\|off}} |  |
| `onoff` | condition | `open` | Is !{{open\|closed}} | `windowcoverings\|curtain\|blinds\|sunshade` |
| `onoff` | action | `on` | Turn on |  |
| `onoff` | action | `off` | Turn off |  |
| `onoff` | action | `toggle` | Toggle on or off |  |
| `onoff` | action | `open` | Open the curtain or blind | `windowcoverings\|curtain\|blinds\|sunshade` |
| `onoff` | action | `close` | Close the curtain or blind | `windowcoverings\|curtain\|blinds\|sunshade` |
| `dim` | trigger | `dim_changed` | The dim level changed |  |
| `dim` | action | `dim` | Dim to |  |
| `dim` | action | `dim_relative` | Set relative dim-level |  |
| `light_hue` | action | `hue` | Set the hue |  |
| `light_hue` | action | `color` | Set a color |  |
| `light_hue` | action | `color_random` | Set a random color |  |
| `light_saturation` | action | `saturation` | Set the saturation |  |
| `light_temperature` | action | `temperature` | Set a temperature |  |
| `vacuumcleaner_state` | trigger | `vacuumcleaner_state_changed` | The state changed to... |  |
| `vacuumcleaner_state` | condition | `vacuumcleaner_state_is` | The vacuum cleaner !{{is\|is not}} |  |
| `vacuumcleaner_state` | action | `clean` | Start cleaning |  |
| `vacuumcleaner_state` | action | `spot_clean` | Start spot cleaning |  |
| `vacuumcleaner_state` | action | `dock` | Return to dock |  |
| `vacuumcleaner_state` | action | `stop` | Stop |  |
| `thermostat_mode` | trigger | `thermostat_mode_changed` | The thermostat mode changed to |  |
| `thermostat_mode` | condition | `thermostat_mode_is` | The thermostat mode !{{is\|is not}} |  |
| `thermostat_mode` | action | `thermostat_mode_set` | Set the thermostat mode to |  |
| `target_temperature` | trigger | `target_temperature_changed` | The target temperature changed |  |
| `target_temperature` | action | `target_temperature_set` | Set the temperature |  |
| `measure_temperature` | trigger | `measure_temperature_changed` | The temperature changes |  |
| `measure_co` | trigger | `measure_co_changed` | The CO-level changed |  |
| `measure_co2` | trigger | `measure_co2_changed` | The CO₂-level changed |  |
| `measure_pm25` | trigger | `measure_pm25_changed` | The PM2.5 value changed |  |
| `measure_humidity` | trigger | `measure_humidity_changed` | The humidity changed |  |
| `measure_pressure` | trigger | `measure_pressure_changed` | The pressure changed |  |
| `measure_noise` | trigger | `measure_noise_changed` | The noise changed |  |
| `measure_rain` | trigger | `measure_rain_changed` | The rain changed |  |
| `measure_wind_strength` | trigger | `measure_wind_strength_changed` | The wind strength changed |  |
| `measure_wind_angle` | trigger | `measure_wind_angle_changed` | The wind angle changed |  |
| `measure_gust_strength` | trigger | `measure_gust_strength_changed` | The gust strength changed |  |
| `measure_gust_angle` | trigger | `measure_gust_angle_changed` | The gust angle changed |  |
| `measure_battery` | trigger | `measure_battery_changed` | The battery level changed |  |
| `measure_power` | trigger | `measure_power_changed` | The power changed |  |
| `measure_voltage` | trigger | `measure_voltage_changed` | The voltage changed |  |
| `measure_current` | trigger | `measure_current_changed` | The electric current changed |  |
| `measure_luminance` | trigger | `measure_luminance_changed` | The luminance changed |  |
| `measure_ultraviolet` | trigger | `measure_ultraviolet_changed` | The ultraviolet value changed |  |
| `measure_water` | trigger | `measure_water_changed` | The waterflow changed |  |
| `alarm_generic` | trigger | `alarm_generic_true` | The generic alarm turned on |  |
| `alarm_generic` | trigger | `alarm_generic_false` | The generic alarm turned off |  |
| `alarm_generic` | condition | `alarm_generic` | The generic alarm is !{{on\|off}} |  |
| `alarm_motion` | trigger | `alarm_motion_true` | The motion alarm turned on |  |
| `alarm_motion` | trigger | `alarm_motion_false` | The motion alarm turned off |  |
| `alarm_motion` | condition | `alarm_motion` | The motion alarm is !{{on\|off}} |  |
| `alarm_contact` | trigger | `alarm_contact_true` | The contact alarm turned on |  |
| `alarm_contact` | trigger | `alarm_contact_false` | The contact alarm turned off |  |
| `alarm_contact` | condition | `alarm_contact` | The contact alarm is !{{on\|off}} |  |
| `alarm_co` | trigger | `alarm_co_true` | The CO alarm turned on |  |
| `alarm_co` | trigger | `alarm_co_false` | The CO alarm turned off |  |
| `alarm_co` | condition | `alarm_co` | The CO alarm is !{{on\|off}} |  |
| `alarm_co2` | trigger | `alarm_co2_true` | The CO₂ alarm turned on |  |
| `alarm_co2` | trigger | `alarm_co2_false` | The CO₂ alarm turned off |  |
| `alarm_co2` | condition | `alarm_co2` | The CO₂ alarm is !{{on\|off}} |  |
| `alarm_pm25` | trigger | `alarm_pm25_true` | The PM2.5 alarm turned on |  |
| `alarm_pm25` | trigger | `alarm_pm25_false` | The PM2.5 alarm turned off |  |
| `alarm_pm25` | condition | `alarm_pm25` | The PM2.5 alarm is !{{on\|off}} |  |
| `alarm_tamper` | trigger | `alarm_tamper_true` | The tamper alarm turned on |  |
| `alarm_tamper` | trigger | `alarm_tamper_false` | The tamper alarm turned off |  |
| `alarm_tamper` | condition | `alarm_tamper` | The tamper alarm is !{{on\|off}} |  |
| `alarm_smoke` | trigger | `alarm_smoke_true` | The smoke alarm turned on |  |
| `alarm_smoke` | trigger | `alarm_smoke_false` | The smoke alarm turned off |  |
| `alarm_smoke` | condition | `alarm_smoke` | The smoke alarm is !{{on\|off}} |  |
| `alarm_fire` | trigger | `alarm_fire_true` | The fire alarm turned on |  |
| `alarm_fire` | trigger | `alarm_fire_false` | The fire alarm turned off |  |
| `alarm_fire` | condition | `alarm_fire` | The fire alarm is !{{on\|off}} |  |
| `alarm_heat` | trigger | `alarm_heat_true` | The heat alarm turned on |  |
| `alarm_heat` | trigger | `alarm_heat_false` | The heat alarm turned off |  |
| `alarm_heat` | condition | `alarm_heat` | The heat alarm is !{{on\|off}} |  |
| `alarm_water` | trigger | `alarm_water_true` | The water alarm turned on |  |
| `alarm_water` | trigger | `alarm_water_false` | The water alarm turned off |  |
| `alarm_water` | condition | `alarm_water` | The water alarm is !{{on\|off}} |  |
| `alarm_battery` | trigger | `alarm_battery_true` | The battery alarm turned on |  |
| `alarm_battery` | trigger | `alarm_battery_false` | The battery alarm turned off |  |
| `alarm_battery` | condition | `alarm_battery` | The battery alarm is !{{on\|off}} |  |
| `alarm_night` | trigger | `alarm_night_true` | The night alarm turned on |  |
| `alarm_night` | trigger | `alarm_night_false` | The night alarm turned off |  |
| `alarm_night` | condition | `alarm_night` | The night alarm is !{{on\|off}} |  |
| `meter_power` | trigger | `meter_power_changed` | The power meter changed |  |
| `meter_water` | trigger | `meter_water_changed` | The water meter changed |  |
| `meter_gas` | trigger | `meter_gas_changed` | The gas meter changed |  |
| `meter_rain` | trigger | `meter_rain_changed` | The rain meter changed |  |
| `homealarm_state` | trigger | `homealarm_state_changed` | The state changed |  |
| `homealarm_state` | condition | `homealarm_state_is` | The state is !{{\|not}} |  |
| `homealarm_state` | action | `set_homealarm_state` | Set state |  |
| `volume_set` | trigger | `volume_set_changed` | The volume changed |  |
| `volume_set` | action | `volume_set` | Set the volume to |  |
| `volume_set` | action | `volume_set_relative` | Set relative volume |  |
| `volume_up` | action | `volume_up` | Turn the volume up |  |
| `volume_down` | action | `volume_down` | Turn the volume down |  |
| `volume_mute` | action | `volume_mute` | Mute the volume |  |
| `volume_mute` | action | `volume_unmute` | Unmute the volume |  |
| `volume_mute` | action | `volume_mute_toggle` | Toggle muted volume on or off |  |
| `channel_up` | action | `channel_up` | One channel up |  |
| `channel_down` | action | `channel_down` | One channel down |  |
| `locked` | trigger | `locked_true` | Locked |  |
| `locked` | trigger | `locked_false` | Unlocked |  |
| `locked` | condition | `locked` | A lock is !{{locked\|unlocked}} |  |
| `locked` | action | `lock` | Lock |  |
| `locked` | action | `unlock` | Unlock |  |
| `lock_mode` | trigger | `lock_mode_changed` | The lock mode changed to |  |
| `lock_mode` | condition | `lock_mode_is` | The lock mode !{{is\|is not}} |  |
| `lock_mode` | action | `mode` | Set the lock mode to |  |
| `garagedoor_closed` | trigger | `garagedoor_closed_true` | Closed |  |
| `garagedoor_closed` | trigger | `garagedoor_closed_false` | Opened |  |
| `garagedoor_closed` | condition | `closed` | Is !{{closed\|open}} |  |
| `garagedoor_closed` | action | `close` | Close |  |
| `garagedoor_closed` | action | `open` | Open |  |
| `garagedoor_closed` | action | `toggle` | Toggle open or closed |  |
| `windowcoverings_state` | trigger | `windowcoverings_state_changed` | The state changed |  |
| `windowcoverings_state` | condition | `windowcoverings_state_is` | The state is !{{\|not}} |  |
| `windowcoverings_state` | action | `set_windowcoverings_state` | Set state |  |
| `windowcoverings_tilt_up` | action | `tilt_up` | Tilt up |  |
| `windowcoverings_tilt_down` | action | `tilt_down` | Tilt down |  |
| `windowcoverings_tilt_set` | trigger | `windowcoverings_tilt_set_changed` | The tilt position changed |  |
| `windowcoverings_tilt_set` | action | `windowcoverings_tilt_set` | Set the tilt position to |  |
| `windowcoverings_closed` | trigger | `windowcoverings_closed_true` | Closed |  |
| `windowcoverings_closed` | trigger | `windowcoverings_closed_false` | Opened |  |
| `windowcoverings_closed` | condition | `closed` | Are !{{closed\|opened}} |  |
| `windowcoverings_closed` | action | `close` | Close |  |
| `windowcoverings_closed` | action | `open` | Open |  |
| `windowcoverings_closed` | action | `toggle` | Toggle open or closed |  |
| `windowcoverings_set` | trigger | `windowcoverings_set_changed` | The position changed |  |
| `windowcoverings_set` | action | `windowcoverings_set` | Set the position to |  |
| `button` | action | `press` | Press the button |  |
| `speaker_playing` | trigger | `speaker_playing_true` | Started playing |  |
| `speaker_playing` | trigger | `speaker_playing_false` | Stopped playing |  |
| `speaker_playing` | condition | `is_playing` | Is !{{\|not}} playing |  |
| `speaker_playing` | action | `play` | Play |  |
| `speaker_playing` | action | `pause` | Pause |  |
| `speaker_playing` | action | `toggle_playing` | Toggle Play/Pause |  |
| `speaker_next` | action | `next` | Next |  |
| `speaker_prev` | action | `prev` | Previous |  |
| `speaker_shuffle` | action | `set_shuffle_true` | Shuffle on |  |
| `speaker_shuffle` | action | `set_shuffle_false` | Shuffle off |  |
| `speaker_repeat` | action | `set_repeat` | Repeat |  |
| `speaker_artist` | trigger | `speaker_artist_changed` | The artist changed |  |
| `speaker_album` | trigger | `speaker_album_changed` | The album changed |  |
| `speaker_track` | trigger | `speaker_track_changed` | The track changed |  |
| `alarm_bin_full` | trigger | `alarm_bin_full_true` | The bin is full |  |
| `alarm_bin_full` | trigger | `alarm_bin_full_false` | The bin is no longer full |  |
| `alarm_bin_full` | condition | `alarm_bin_full` | The bin is !{{full\|not full}} |  |
| `alarm_bin_missing` | trigger | `alarm_bin_missing_true` | The bin was removed |  |
| `alarm_bin_missing` | trigger | `alarm_bin_missing_false` | The bin was placed |  |
| `alarm_bin_missing` | condition | `alarm_bin_missing` | The bin is !{{missing\|present}} |  |
| `alarm_cleaning_pad_missing` | trigger | `alarm_cleaning_pad_missing_true` | The cleaning pad was removed |  |
| `alarm_cleaning_pad_missing` | trigger | `alarm_cleaning_pad_missing_false` | The cleaning pad was placed |  |
| `alarm_cleaning_pad_missing` | condition | `alarm_cleaning_pad_missing` | The cleaning pad is !{{missing\|present}} |  |
| `alarm_cold` | trigger | `alarm_cold_true` | The cold alarm turned on |  |
| `alarm_cold` | trigger | `alarm_cold_false` | The cold alarm turned off |  |
| `alarm_cold` | condition | `alarm_cold` | The cold alarm is !{{on\|off}} |  |
| `alarm_connectivity` | trigger | `alarm_connectivity_true` | Is disconnected |  |
| `alarm_connectivity` | trigger | `alarm_connectivity_false` | Is connected |  |
| `alarm_connectivity` | condition | `alarm_connectivity` | Is !{{connected\|disconnected}} |  |
| `alarm_door_fault` | trigger | `alarm_door_fault_true` | The door alarm turned on |  |
| `alarm_door_fault` | trigger | `alarm_door_fault_false` | The door alarm turned off |  |
| `alarm_door_fault` | condition | `alarm_door_fault` | The door alarm is !{{on\|off}} |  |
| `alarm_gas` | trigger | `alarm_gas_true` | The gas alarm turned on |  |
| `alarm_gas` | trigger | `alarm_gas_false` | The gas alarm turned off |  |
| `alarm_gas` | condition | `alarm_gas` | The gas alarm is !{{on\|off}} |  |
| `alarm_light` | trigger | `alarm_light_true` | Light is detected |  |
| `alarm_light` | trigger | `alarm_light_false` | Light is no longer detected |  |
| `alarm_light` | condition | `alarm_light` | Light !{{is\|is not}} detected |  |
| `alarm_lost` | trigger | `alarm_lost_true` | Is lost |  |
| `alarm_lost` | trigger | `alarm_lost_false` | Is no longer lost |  |
| `alarm_lost` | condition | `alarm_lost` | Is !{{lost\|not lost}} |  |
| `alarm_moisture` | trigger | `alarm_moisture_true` | The moisture alarm turned on |  |
| `alarm_moisture` | trigger | `alarm_moisture_false` | The moisture alarm turned off |  |
| `alarm_moisture` | condition | `alarm_moisture` | The moisture alarm is !{{on\|off}} |  |
| `alarm_noise` | trigger | `alarm_noise_true` | The noise alarm turned on |  |
| `alarm_noise` | trigger | `alarm_noise_false` | The noise alarm turned off |  |
| `alarm_noise` | condition | `alarm_noise` | The noise alarm is !{{on\|off}} |  |
| `alarm_occupancy` | trigger | `alarm_occupancy_true` | The occupancy alarm turned on |  |
| `alarm_occupancy` | trigger | `alarm_occupancy_false` | The occupancy alarm turned off |  |
| `alarm_occupancy` | condition | `alarm_occupancy` | Is !{{occupied\|not occupied}} |  |
| `alarm_pm01` | trigger | `alarm_pm01_true` | The PM0.1 alarm turned on |  |
| `alarm_pm01` | trigger | `alarm_pm01_false` | The PM0.1 alarm turned off |  |
| `alarm_pm01` | condition | `alarm_pm01` | The PM0.1 alarm is !{{on\|off}} |  |
| `alarm_pm1` | trigger | `alarm_pm1_true` | The PM1 alarm turned on |  |
| `alarm_pm1` | trigger | `alarm_pm1_false` | The PM1 alarm turned off |  |
| `alarm_pm1` | condition | `alarm_pm1` | The PM1 alarm is !{{on\|off}} |  |
| `alarm_pm10` | trigger | `alarm_pm10_true` | The PM10 alarm turned on |  |
| `alarm_pm10` | trigger | `alarm_pm10_false` | The PM10 alarm turned off |  |
| `alarm_pm10` | condition | `alarm_pm10` | The PM10 alarm is !{{on\|off}} |  |
| `alarm_power` | trigger | `alarm_power_true` | The power alarm turned on |  |
| `alarm_power` | trigger | `alarm_power_false` | The power alarm turned off |  |
| `alarm_power` | condition | `alarm_power` | The power alarm is !{{on\|off}} |  |
| `alarm_presence` | trigger | `alarm_presence_true` | The presence alarm turned on |  |
| `alarm_presence` | trigger | `alarm_presence_false` | The presence alarm turned off |  |
| `alarm_presence` | condition | `alarm_presence` | The presence alarm is !{{on\|off}} |  |
| `alarm_problem` | trigger | `alarm_problem_true` | A problem is detected |  |
| `alarm_problem` | trigger | `alarm_problem_false` | The problem is solved |  |
| `alarm_problem` | condition | `alarm_problem` | There !{{is\|isn't}} a problem |  |
| `alarm_pump_device` | trigger | `alarm_pump_device_true` | The pump device fault alarm turned on |  |
| `alarm_pump_device` | trigger | `alarm_pump_device_false` | The pump device fault alarm turned off |  |
| `alarm_pump_device` | condition | `alarm_pump_device` | The pump device fault alarm is !{{on\|off}} |  |
| `alarm_pump_supply` | trigger | `alarm_pump_supply_true` | A problem is detected in the pump supply |  |
| `alarm_pump_supply` | trigger | `alarm_pump_supply_false` | The problem in the pump supply is solved |  |
| `alarm_pump_supply` | condition | `alarm_pump_supply` | There !{{is\|isn't}} a problem in the pump supply |  |
| `alarm_running` | trigger | `alarm_running_true` | The running alarm turned on |  |
| `alarm_running` | trigger | `alarm_running_false` | The running alarm turned off |  |
| `alarm_running` | condition | `alarm_running` | Is !{{busy\|not busy}} |  |
| `alarm_safety` | trigger | `alarm_safety_true` | The safety alarm turned on |  |
| `alarm_safety` | trigger | `alarm_safety_false` | The safety alarm turned off |  |
| `alarm_safety` | condition | `alarm_safety` | The safety alarm is !{{on\|off}} |  |
| `alarm_stuck` | trigger | `alarm_stuck_true` | Is stuck |  |
| `alarm_stuck` | trigger | `alarm_stuck_false` | Is no longer stuck |  |
| `alarm_stuck` | condition | `alarm_stuck` | Is !{{stuck\|not stuck}} |  |
| `alarm_tank_empty` | trigger | `alarm_tank_empty_true` | The tank is empty |  |
| `alarm_tank_empty` | trigger | `alarm_tank_empty_false` | The tank is no longer empty |  |
| `alarm_tank_empty` | condition | `alarm_tank_empty` | The tank is !{{empty\|not empty}} |  |
| `alarm_tank_missing` | trigger | `alarm_tank_missing_true` | The tank is missing |  |
| `alarm_tank_missing` | trigger | `alarm_tank_missing_false` | The tank is placed |  |
| `alarm_tank_missing` | condition | `alarm_tank_missing` | Tank !{{is\|is not}} missing |  |
| `alarm_tank_open` | trigger | `alarm_tank_open_true` | The tank opens |  |
| `alarm_tank_open` | trigger | `alarm_tank_open_false` | The tank closes |  |
| `alarm_tank_open` | condition | `alarm_tank_open` | The tank is !{{open\|closed}} |  |
| `alarm_vibration` | trigger | `alarm_vibration_true` | The vibration alarm turned on |  |
| `alarm_vibration` | trigger | `alarm_vibration_false` | The vibration alarm turned off |  |
| `alarm_vibration` | condition | `alarm_vibration` | The vibration alarm is !{{on\|off}} |  |
| `audio_output` | trigger | `audio_output_changed` | The audio output changed to |  |
| `audio_output` | condition | `audio_output_is` | The audio output !{{is\|is not}} |  |
| `audio_output` | action | `set_audio_output` | Set audio output to |  |
| `battery_charging_state` | trigger | `battery_charging_state_changed` | The battery charging state changed |  |
| `battery_charging_state` | condition | `battery_charging_state_is` | The battery charging state !{{is\|is not}} |  |
| `dishwasher_program` | trigger | `dishwasher_program_changed` | The program changed to |  |
| `dishwasher_program` | condition | `dishwasher_program_is` | The program is |  |
| `docked` | trigger | `docked_true` | Has docked |  |
| `docked` | trigger | `docked_false` | Has undocked |  |
| `docked` | condition | `docked` | Is !{{docked\|not docked}} |  |
| `fan_mode` | trigger | `fan_mode_changed` | The fan mode changed to |  |
| `fan_mode` | condition | `fan_mode_is` | The fan mode !{{is\|is not}} |  |
| `fan_mode` | action | `set_fan_mode` | Set the fan mode to |  |
| `fan_speed` | trigger | `fan_speed_changed` | The fan speed changed |  |
| `fan_speed` | action | `set_fan_speed` | Set the fan speed to |  |
| `heater_operation_mode` | trigger | `heater_operation_mode_changed` | The heater operation mode changed to |  |
| `heater_operation_mode` | condition | `heater_operation_mode_is` | The heater operation mode !{{is\|is not}} |  |
| `heater_operation_mode` | action | `set_heater_operation_mode` | Set the heater operation mode to |  |
| `measure_hepa_filter` | trigger | `measure_hepa_filter_changed` | The HEPA filter level changed |  |
| `hot_water_mode` | trigger | `hot_water_mode_changed` | The hot water mode changed to |  |
| `hot_water_mode` | condition | `hot_water_mode_is` | The hot water mode !{{is\|is not}} |  |
| `hot_water_mode` | action | `set_hot_water_mode` | Set the hot water mode to |  |
| `laundry_washer_cycles` | trigger | `laundry_washer_cycles_changed` | The cycles changed to |  |
| `laundry_washer_cycles` | condition | `laundry_washer_cycles_is` | The cycles !{{is\|is not}} |  |
| `laundry_washer_cycles` | action | `set_laundry_washer_cycles` | Set the laundry washer cycles to |  |
| `laundry_washer_program` | trigger | `laundry_washer_program_changed` | The program changed to |  |
| `laundry_washer_program` | condition | `laundry_washer_program_is` | The program !{{is\|is not}} |  |
| `laundry_washer_speed` | trigger | `laundry_washer_speed_changed` | The speed changed to |  |
| `laundry_washer_speed` | condition | `laundry_washer_speed_is` | The speed !{{is\|is not}} |  |
| `laundry_washer_speed` | action | `set_laundry_washer_speed` | Set the speed to |  |
| `level_aqi` | trigger | `level_aqi_changed` | The air quality level changed to |  |
| `level_aqi` | condition | `level_aqi_is` | The air quality !{{is\|is not}} |  |
| `level_carbon_filter` | trigger | `level_carbon_filter_changed` | The carbon filter level changed to |  |
| `level_carbon_filter` | condition | `level_carbon_filter_is` | The carbon filter level !{{is\|is not}} |  |
| `level_ch2o` | trigger | `level_ch2o_changed` | The formaldehyde level changed to |  |
| `level_ch2o` | condition | `level_ch2o_is` | The formaldehyde level !{{is\|is not}} |  |
| `level_co` | trigger | `level_co_changed` | The CO level changed to |  |
| `level_co` | condition | `level_co_is` | The CO level !{{is\|is not}} |  |
| `level_co2` | trigger | `level_co2_changed` | The CO₂ level changed to |  |
| `level_co2` | condition | `level_co2_is` | The CO₂ level !{{is\|is not}} |  |
| `level_nox` | trigger | `level_nox_changed` | The NOx level changed to |  |
| `level_nox` | condition | `level_nox_is` | The NOx level !{{is\|is not}} |  |
| `level_o3` | trigger | `level_o3_changed` | The ozone level changed to |  |
| `level_o3` | condition | `level_o3_is` | The ozone level !{{is\|is not}} |  |
| `level_pm1` | trigger | `level_pm1_changed` | The PM1 level changed to |  |
| `level_pm1` | condition | `level_pm1_is` | The PM1 level !{{is\|is not}} |  |
| `level_pm01` | trigger | `level_pm01_changed` | The PM0.1 level changed to |  |
| `level_pm01` | condition | `level_pm01_is` | The PM0.1 level !{{is\|is not}} |  |
| `level_pm10` | trigger | `level_pm10_changed` | The PM10 level changed to |  |
| `level_pm10` | condition | `level_pm10_is` | The PM10 level !{{is\|is not}} |  |
| `level_pm25` | trigger | `level_pm25_changed` | The PM2.5 level changed to |  |
| `level_pm25` | condition | `level_pm25_is` | The PM2.5 level !{{is\|is not}} |  |
| `level_radon` | trigger | `level_radon_changed` | The radon level changed to |  |
| `level_radon` | condition | `level_radon_is` | The radon level !{{is\|is not}} |  |
| `level_so2` | trigger | `level_so2_changed` | The SO₂ level changed to |  |
| `level_so2` | condition | `level_so2_is` | The SO₂ level !{{is\|is not}} |  |
| `level_tvoc` | trigger | `level_tvoc_changed` | The TVOC level changed to |  |
| `level_tvoc` | condition | `level_tvoc_is` | The TVOC level !{{is\|is not}} |  |
| `measure_aqi` | trigger | `measure_aqi_changed` | The air quality index changed |  |
| `measure_carbon_filter` | trigger | `measure_carbon_filter_changed` | The carbon filter level changed |  |
| `measure_ch2o` | trigger | `measure_ch2o_changed` | The formaldehyde level changed |  |
| `measure_content_volume` | trigger | `measure_content_volume_changed` | The volume changed |  |
| `measure_data_rate` | trigger | `measure_data_rate_changed` | The data rate changed |  |
| `measure_data_size` | trigger | `measure_data_size_changed` | The data size changed |  |
| `measure_distance` | trigger | `measure_distance_changed` | The distance changed |  |
| `measure_frequency` | trigger | `measure_frequency_changed` | The frequency changed |  |
| `level_hepa_filter` | trigger | `level_hepa_filter_changed` | The HEPA filter level changed to |  |
| `level_hepa_filter` | condition | `level_hepa_filter_is` | The HEPA filter level !{{is\|is not}} |  |
| `measure_moisture` | trigger | `measure_moisture_changed` | The moisture level changed |  |
| `measure_monetary` | trigger | `measure_monetary_changed` | The monetary value changed |  |
| `measure_nox` | trigger | `measure_nox_changed` | The NOx level changed |  |
| `measure_o3` | trigger | `measure_o3_changed` | The ozone level changed |  |
| `measure_odor` | trigger | `measure_odor_changed` | The odor concentration changed |  |
| `measure_ph` | trigger | `measure_ph_changed` | The pH level changed |  |
| `measure_pm1` | trigger | `measure_pm1_changed` | The PM1 value has changed |  |
| `measure_pm01` | trigger | `measure_pm01_changed` | The PM0.1 value has changed |  |
| `measure_pm10` | trigger | `measure_pm10_changed` | The PM10 value has changed |  |
| `measure_radon` | trigger | `measure_radon_changed` | The radon level has changed |  |
| `measure_rain_intensity` | trigger | `measure_rain_intensity_changed` | The rain intensity changed |  |
| `measure_rotation` | trigger | `measure_rotation_changed` | The rotation changed |  |
| `measure_signal_strength` | trigger | `measure_signal_strength_changed` | The signal strength changed |  |
| `measure_so2` | trigger | `measure_so2_changed` | The SO₂ level has changed |  |
| `measure_speed` | trigger | `measure_speed_changed` | The speed changed |  |
| `measure_tvoc` | trigger | `measure_tvoc_changed` | The TVOC level has changed |  |
| `measure_tvoc_index` | trigger | `measure_tvoc_index_changed` | The TVOC index has changed |  |
| `measure_weight` | trigger | `measure_weight_changed` | The weight changed |  |
| `media_input` | trigger | `media_input_changed` | The media input changed to |  |
| `media_input` | condition | `media_input_is` | The media input !{{is\|is not}} |  |
| `media_input` | action | `set_media_input` | Set the media input |  |
| `mower_state` | trigger | `mower_state_changed` | The lawnmower state changed |  |
| `mower_state` | condition | `mower_state_is` | The lawnmower !{{is\|is not}} |  |
| `mower_state` | action | `mower_state_mow` | Start mowing |  |
| `mower_state` | action | `mower_state_pause` | Pause mowing |  |
| `mower_state` | action | `mower_state_dock` | Return to dock |  |
| `operational_state` | trigger | `operational_state_changed` | The operational state changed to |  |
| `operational_state` | condition | `operational_state_is` | The operational state !{{is\|is not}} |  |
| `oscillating` | trigger | `oscillating_true` | Oscillation turned on |  |
| `oscillating` | trigger | `oscillating_false` | Oscillation turned off |  |
| `oscillating` | condition | `oscillating` | Oscillation is !{{enabled\|disabled}} |  |
| `oscillating` | action | `enable_oscillating` | Enable Oscillation |  |
| `oscillating` | action | `disable_oscillating` | Disable Oscillation |  |
| `oscillating` | action | `toggle_oscillating` | Toggle Oscillation on or off |  |
| `pump_mode` | trigger | `pump_mode_changed` | The pump mode changed to |  |
| `pump_mode` | condition | `pump_mode_is` | The pump mode !{{is\|is not}} |  |
| `pump_mode` | action | `set_pump_mode` | Set the pump mode to |  |
| `pump_setpoint` | trigger | `pump_setpoint_changed` | The pump setpoint changed |  |
| `pump_setpoint` | action | `set_pump_setpoint` | Set the pump setpoint |  |
| `refrigerator_mode` | trigger | `refrigerator_mode_changed` | The refrigerator mode changed to |  |
| `refrigerator_mode` | condition | `refrigerator_mode_is` | The refrigerator mode !{{is\|is not}} |  |
| `refrigerator_mode` | action | `set_refrigerator_mode` | Set the refrigerator mode to |  |
| `speaker_stop` | action | `stop` | Stop |  |
| `swing_mode` | trigger | `swing_mode_changed` | The swing mode changed to |  |
| `swing_mode` | condition | `swing_mode_is` | The swing mode !{{is\|is not}} |  |
| `swing_mode` | action | `set_swing_mode` | Set the swing mode to |  |
| `target_humidity_max` | trigger | `target_humidity_max_changed` | The maximum target humidity has changed |  |
| `target_humidity_max` | action | `set_target_humidity_max` | Set the maximum target humidity |  |
| `target_humidity_min` | trigger | `target_humidity_min_changed` | The minimum target humidity has changed |  |
| `target_humidity_min` | action | `set_target_humidity_min` | Set the minimum target humidity |  |
| `target_humidity` | trigger | `target_humidity_changed` | The target humidity changed |  |
| `target_humidity` | action | `set_target_humidity` | Set the humidity |  |
| `target_power` | trigger | `target_power_changed` | The target power changed |  |
| `target_power` | action | `target_power_set` | Set the target power |  |
| `target_power_mode` | trigger | `target_power_mode_changed` | The target power mode changed to |  |
| `target_power_mode` | condition | `target_power_mode_is` | The target power mode !{{is\|is not}} |  |
| `target_power_mode` | action | `target_power_mode_set` | Set the target power mode to |  |
| `target_temperature_level` | trigger | `target_temperature_level_changed` | The target temperature level changed to |  |
| `target_temperature_level` | condition | `target_temperature_level_is` | The target temperature level !{{is\|is not}} |  |
| `target_temperature_level` | action | `set_target_temperature_level` | Set the target temperature level to |  |
| `target_temperature_max` | trigger | `target_temperature_max_changed` | The maximum target temperature has changed |  |
| `target_temperature_max` | action | `set_target_temperature_max` | Set the maximum target temperature |  |
| `target_temperature_min` | trigger | `target_temperature_min_changed` | The minimum target temperature has changed |  |
| `target_temperature_min` | action | `set_target_temperature_min` | Set the minimum target temperature |  |
| `vacuumcleaner_job_mode` | trigger | `vacuumcleaner_job_mode_changed` | The job mode changed to |  |
| `vacuumcleaner_job_mode` | condition | `vacuumcleaner_job_mode_is` | The job mode !{{is\|is not}} |  |
| `vacuumcleaner_job_mode` | action | `set_vacuumcleaner_job_mode` | Set the job mode to |  |
| `valve_position` | trigger | `valve_position_changed` | The valve position changed |  |
| `valve_position` | action | `set_valve_position` | Set the valve position |  |
| `ev_charging_state` | trigger | `ev_charging_state_changed` | The battery charging state changed |  |
| `ev_charging_state` | condition | `ev_charging_state_is` | The battery charging state !{{is\|is not}} |  |
| `evcharger_charging_state` | trigger | `evcharger_charging_state_changed` | The EV charger charging state changed |  |
| `evcharger_charging_state` | condition | `evcharger_charging_state_is` | The EV charger charging state !{{is\|is not}} |  |
| `evcharger_charging` | trigger | `evcharger_charging_true` | Started charging |  |
| `evcharger_charging` | trigger | `evcharger_charging_false` | Stopped charging |  |
| `evcharger_charging` | condition | `evcharger_charging` | Is !{{\|not}} charging |  |
| `evcharger_charging` | action | `evcharger_charging_start` | Start charging |  |
| `evcharger_charging` | action | `evcharger_charging_stop` | Stop charging |  |
| `oven_mode` | trigger | `oven_mode_changed` | The oven mode changed to |  |
| `oven_mode` | condition | `oven_mode_is` | The oven mode !{{is\|is not}} |  |
| `oven_mode` | action | `set_oven_mode` | Set the oven mode to |  |
| `microwave_mode` | trigger | `microwave_mode_changed` | The microwave mode changed to |  |
| `microwave_mode` | condition | `microwave_mode_is` | The microwave mode !{{is\|is not}} |  |
| `microwave_mode` | action | `set_microwave_mode` | Set the microwave mode to |  |
| `laundry_dryer_dryness` | trigger | `laundry_dryer_dryness_changed` | The dryness changed to |  |
| `laundry_dryer_dryness` | condition | `laundry_dryer_dryness_is` | The dryness !{{is\|is not}} |  |
| `laundry_dryer_dryness` | action | `set_laundry_dryer_dryness` | Set the laundry dryer dryness to |  |
| `alarm_freeze_risk` | trigger | `alarm_freeze_risk_true` | The freeze risk alarm turned on |  |
| `alarm_freeze_risk` | trigger | `alarm_freeze_risk_false` | The freeze risk alarm turned off |  |
| `alarm_freeze_risk` | condition | `alarm_freeze_risk` | The freeze risk alarm is !{{on\|off}} |  |
| `alarm_rain` | trigger | `alarm_rain_true` | The rain alarm turned on |  |
| `alarm_rain` | trigger | `alarm_rain_false` | The rain alarm turned off |  |
| `alarm_rain` | condition | `alarm_rain` | The rain alarm is !{{on\|off}} |  |
| `alarm_open` | trigger | `alarm_open_true` | The open alarm turned on |  |
| `alarm_open` | trigger | `alarm_open_false` | The open alarm turned off |  |
| `alarm_open` | condition | `alarm_open` | The open alarm is !{{on\|off}} |  |
| `cooking_time` | trigger | `cooking_time_changed` | The cooking time changed |  |
| `cooking_time` | action | `set_cooking_time` | Set the cooking time to [[cooking_time]] |  |
| `power_level` | trigger | `power_level_changed` | The power level changed |  |
| `power_level` | action | `power_level` | Set the power level to |  |
| `power_level` | action | `power_level_relative` | Set relative power level |  |
| `power_boost` | trigger | `power_boost_true` | Power boost enabled |  |
| `power_boost` | trigger | `power_boost_false` | Power boost disabled |  |
| `power_boost` | condition | `power_boost` | Power boost is !{{enabled\|disabled}} |  |
| `power_boost` | action | `enable` | Enable power boost |  |
| `power_boost` | action | `disable` | Disable power boost |  |
| `power_boost` | action | `toggle` | Toggle power boost |  |
| `progress` | trigger | `progress_changed` | The progress changed |  |

The remaining 3 capabilities declare no `$flow` block and therefore generate no cards
of their own; author Flow cards for them yourself if users need them.


---

## Best practices — lights

Device class: prefer `light` when the device *is* a light source. Use `socket` for wall plugs and for (flush)
modules that have credible non-lighting use cases; a `socket` device gets a "What's plugged in?" setting so the
user can pick a virtual class. When in doubt use `socket`, but give a device the class `light` whenever possible —
it gets the right UI components by default.

Behaviour rules for `onoff` + `dim`:

- Dragging the dim slider from 0 to non-zero while the device is off **must** turn it on (`onoff` → `true`).
- Dragging the dim slider from non-zero to 0 while the device is on **must** turn it off (`onoff` → `false`).
- If the technology can report external changes (Zigbee, Z-Wave, connected wall switches), reflect them in Homey.
- Couple and debounce `onoff` and `dim` with `registerMultipleCapabilityListener()`, because users can build Flows
  containing both an `onoff` and a `dim` action. Sending two commands would first restore the last dim level and
  then dim again.
- On a conflicting Flow (turn on + dim to 0%, or turn off + dim to 50%), **`onoff` is leading**.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyLight extends Homey.Device {

  async onInit() {
    this.registerMultipleCapabilityListener(['onoff', 'dim'], async ({ onoff, dim }) => {
      if (dim > 0 && onoff === false) {
        await DeviceApi.setOnOffAsync(false);              // turn off
      } else if (dim <= 0 && onoff === true) {
        await DeviceApi.setOnOffAsync(true);               // turn on
      } else {
        await DeviceApi.setOnOffAndDimAsync({ onoff, dim }); // one combined command
      }
    });
  }

}

module.exports = MyLight;
```

Setting `setOnDim: false` on `onoff` makes Homey send only a `dim` capability set (instead of both) when a Flow
changes the dim level.

Colour and temperature (`light_hue`, `light_saturation`, `light_temperature`, `light_mode`):

- Debounce them together with `onoff` and `dim` to prevent flickering.
- Changing a colour capability while the device is off **must not turn it on**. Only `onoff` and `dim` may change
  the on/off state.
- When the device is switched on externally, listen for (or poll) the colour capabilities and reflect the real
  state.
- On a conflicting Flow (turn off + set colour to red), `onoff` is leading — turn the light off.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

const lightCapabilities = [
  'onoff',
  'dim',
  'light_hue',
  'light_temperature',
  'light_saturation',
  'light_mode',
];

class MyColorLight extends Homey.Device {

  async onInit() {
    this.registerMultipleCapabilityListener(lightCapabilities, async (values) => {
      // handle the changed capabilities all at once
      await DeviceApi.setOnOffAndDimAndColorAsync(values);
    });
  }

}

module.exports = MyColorLight;
```

## Best practices — battery status

A device that reports battery does so in one of two ways:

| Capability | Use when |
| --- | --- |
| `measure_battery` | The device reports a precise battery level on a numeric scale (0–100 %). |
| `alarm_battery` | The device only signals "battery empty/low" past some threshold. |

> **Never give a driver both `measure_battery` and `alarm_battery`.** It creates duplicate UI components and Flow
> cards, and the App Store review flags it.

Battery devices must specify an `energy` object with a `batteries` array of battery-type strings. The CLI **fails
publishing** with `drivers.<id> is missing an array 'energy.batteries' because the capability <id> is being used`
when a driver has `measure_battery` or `alarm_battery` without `energy.batteries` (or `energy.homeBattery` /
`energy.electricCar`).

```json
{
  "name": { "en": "My Driver" },
  "class": "sensor",
  "capabilities": ["measure_battery"],
  "energy": { "batteries": ["AAA", "AAA"] },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  }
}
```

## Best practices — window coverings

Only use the `windowcoverings` device class when `curtain`, `blinds` or `sunshade` is not more applicable.
(The documentation page spells these `window_coverings` and `curtains`; the ids the CLI actually accepts are
`windowcoverings`, `curtain`, `blinds`, `sunshade` and `shutterblinds` — see `references/drivers-and-devices.md`.)
Relevant capabilities: `windowcoverings_state`, `windowcoverings_tilt_up`, `windowcoverings_tilt_down`,
`windowcoverings_tilt_set`, `windowcoverings_closed`, `windowcoverings_set`.

| Device can do | Give it |
| --- | --- |
| up / down / stop commands | `windowcoverings_state` (+ `windowcoverings_tilt_up` and `windowcoverings_tilt_down` for venetian horizontal tilt) |
| precise open/close level | `windowcoverings_set` (+ the tilt capabilities where applicable) |
| both precise level **and** up/down/stop | both `windowcoverings_state` and `windowcoverings_set` |

**Gotcha:** the App Store review checklist explicitly watches for `windowcoverings_state` **and**
`windowcoverings_set` together as a potential "double UI capability". It is legitimate only for the third case
above — a motor that genuinely supports both. Do not add both to a device that only does one of them.

---

## Gotchas

- **`setCapabilityValue()` takes exactly two arguments.** There is no `opts`/`duration` parameter on it in SDK v3
  (JS or Python). `opts` is the **second argument of the capability listener**, populated from the Flow card's
  duration. Passing a third argument is silently ignored.
- **`getCapabilityValue()` returns `null` when the value is unknown**, not `undefined` and not `0`/`false`. Guard
  before arithmetic, comparisons or `.toFixed()`.
- **`addCapability()`, `removeCapability()` and `setCapabilityOptions()` are expensive.** Call them only when
  something actually changed, guarded by `hasCapability()`, and never unconditionally on every `onInit()`. Adding a
  capability to already-paired devices is a **migration** — gate it behind a store flag so it runs once per device.
- **`removeCapability()` breaks every Flow that uses that capability.** So does replacing a capability with a
  sub-capability (`onoff` → `onoff.socket1`). Treat both as breaking changes.
- **Sub-capabilities get no auto-generated Flow cards.** If you split `onoff` into `onoff.socket1`/`onoff.socket2`
  you lose the system "Turn on"/"Turn off"/"Toggle" cards and must define them yourself.
- **A custom capability id may not contain a dot** — `.` is reserved for sub-capabilities and the CLI throws.
- **`minCompatibility` is enforced.** Using e.g. `fan_speed` (12.2.0), `evcharger_charging` (12.4.5),
  `power_boost` (12.11.0) or `target_power` (12.13.0) while the manifest's `compatibility` allows an older Homey
  makes `homey app validate` fail. Raise `compatibility` or pick a capability without a floor.
- **`capabilitiesOptions[].titleShort` requires `compatibility` `>=13.2.1`** — the CLI throws otherwise.
- **`capabilitiesOptions` is an untyped object in the app schema.** A misspelled option name (`decimal` instead of
  `decimals`, `unit` instead of `units`) passes `homey app validate` silently and simply does nothing. The
  internationalization docs page even says `"unit"` in prose — the real key is **`units`**.
- **Percentage capabilities are fractions.** Exactly eleven `%` capabilities are `min 0, max 1`: `dim`,
  `fan_speed`, `power_level`, `pump_setpoint`, `target_humidity`, `target_humidity_min`, `target_humidity_max`,
  `valve_position`, `volume_set`, `windowcoverings_set` and `windowcoverings_tilt_set`. Five are 0–100:
  `measure_battery`, `measure_carbon_filter`, `measure_hepa_filter`, `measure_moisture` and `progress`.
  (`measure_humidity` is also `%` but declares no `min`/`max`; treat it as 0–100.) Sending 50 to `dim` is not 50 %.
- **Always work in Celsius.** Homey converts to Fahrenheit itself when `units` is `"°C"`; converting yourself
  double-converts.
- **`getable: false` on an existing driver breaks users' Flows** — it removes Flow cards belonging to `onoff` /
  `volume_mute`. Only ship it on new drivers.
- **Insights is write-only at runtime.** `ManagerInsights` / `InsightsLog` offer no read API, so `insights: true`
  gives your app no history to read back. Keep a capped buffer in the device store instead.
- **Fire-and-forget `setCapabilityValue()` needs `.catch(this.error)`.** An unhandled rejection can take the whole
  app down (fatal on Homey Cloud), and `setCapabilityValue()` rejects for an unknown capability id (the Python SDK
  documents the same call as raising `NotFound`).
- **Register capability listeners in `Device#onInit()`, once per device** — and after any `addCapability()`
  migration, otherwise the capability does not exist yet when the listener is registered.
- **Never both `measure_battery` and `alarm_battery`** on one driver, and never `measure_battery`/`alarm_battery`
  without `energy.batteries` — the second one blocks publishing outright.
- **Uncoupled `onoff`/`dim` listeners cause visible flicker.** Two separate `registerCapabilityListener()` calls on
  a light is the single most common review complaint; use `registerMultipleCapabilityListener()`.
- **Unavailable devices block all capabilities and Flow actions.** A `setCapabilityValue()` from a poll loop still
  works, but user/Flow-initiated capability sets are refused while `setUnavailable()` is in effect.
- **Timers around capability polling must use `this.homey.setTimeout` / `setInterval`** and be cleared in
  `onDeleted()` and `onUninit()`; plain globals leak on Homey Cloud.

---

## Sources

- <https://apps.developer.homey.app/the-basics/devices/capabilities>
- <https://apps.developer.homey.app/the-basics/devices/best-practices/lights>
- <https://apps.developer.homey.app/the-basics/devices/best-practices/battery-status>
- <https://apps.developer.homey.app/the-basics/devices/best-practices/window-coverings>
- <https://apps.developer.homey.app/the-basics/devices/energy>
- <https://apps.developer.homey.app/upgrade-guides/device-capabilities>
- <https://apps.developer.homey.app/the-basics/app/internationalization>
- <https://apps-sdk-v3.developer.homey.app/tutorial-device-capabilities.html>
- <https://apps-sdk-v3.developer.homey.app/Device.html>
- <https://apps-sdk-v3.developer.homey.app/ManagerInsights.html>
- <https://apps-sdk-v3.developer.homey.app/InsightsLog.html>
