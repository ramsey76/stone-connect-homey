# Energy & Homey Energy

How a driver feeds Homey Energy: the `energy` object in `driver.compose.json`, the power/energy capabilities
(`measure_power`, `meter_power`, `meter_gas`, `meter_water`, `measure_battery`, `target_power`), the per-device-class
Energy roles (solar panel, smart plug, home battery, EV charger, EV, cumulative meter), and every validation rule the
CLI enforces. Capability options and sub-capabilities: `references/capabilities.md`. Driver manifest and device
classes: `references/drivers-and-devices.md`. Flow cards: `references/flow-cards.md`.

---

## Capabilities that feed Homey Energy

| Capability | Type | Units | Range / precision | Getable | Setable | Min. Homey | Role in Energy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `measure_power` | number | `W` | `decimals: 2` | yes | no | — | Instantaneous power usage/generation in watts. |
| `meter_power` | number | `kWh` | `decimals: 2` | yes | no | — | Energy in kilowatt-hours. Cumulative unless documented otherwise. |
| `meter_gas` | number | `m³` | `min: 0`, `decimals: 2` | yes | no | — | Total gas consumed. Read by Homey when `energy.cumulative` is set. |
| `meter_water` | number | `m³` | `min: 0`, `decimals: 3` | yes | no | — | Total water consumed. Read by Homey when `energy.cumulative` is set. |
| `measure_battery` | number | `%` | `min: 0`, `max: 100`, `decimals: 2` | yes | no | — | State of charge. Required on home batteries and EVs. |
| `alarm_battery` | boolean | — | — | yes | no | — | Low-battery alarm. Alternative to `measure_battery`. |
| `target_power` | number | `W` | `min: -25000`, `max: 25000`, `step: 1`, `decimals: 0` | yes | **yes** | `12.13.0` | Requested power level (control). `uiComponent: slider`. |
| `target_power_mode` | enum | — | `device` \| `homey` | yes | **yes** | `12.13.0` | Who controls power management. `uiComponent: picker`. |
| `evcharger_charging` | boolean | — | — | yes | **yes** | `12.4.5` | Start/stop charging switch on an EV charger. |
| `evcharger_charging_state` | enum | — | see values below | yes | no | `12.4.5` | Reported EV-charger state. |
| `ev_charging_state` | enum | — | see values below | yes | no | `12.4.5` | Reported charging state of an EV (`class: car`). |
| `battery_charging_state` | enum | — | `charging` \| `discharging` \| `idle` | yes | no | `12.2.0` | Fallback for home batteries without `measure_power`. |
| `onoff` | boolean | — | — | yes | yes | — | Drives approximation when `measure_power` is absent. |
| `dim` | number | `%` | `min: 0`, `max: 1`, `decimals: 2` | yes | yes | — | Refines approximation (brightness weighting). |

Enum values:

| Capability | `id` | Title (en) |
| --- | --- | --- |
| `evcharger_charging_state` / `ev_charging_state` | `plugged_in_charging` | Charging |
| | `plugged_in_discharging` | Discharging |
| | `plugged_in_paused` | Paused |
| | `plugged_in` | Plugged in |
| | `plugged_out` | Not plugged in |
| `battery_charging_state` | `charging` | Charging |
| | `discharging` | Discharging |
| | `idle` | Idle |
| `target_power_mode` | `device` | Automatic |
| | `homey` | Homey |

`measure_voltage` (`V`), `measure_current` (`A`), `alarm_power`, `power_boost` and `power_level` exist as system
capabilities but are **not** read by Homey Energy — do not use them as a substitute for `measure_power` /
`meter_power`.

### Measure Power

`measure_power` is the instantaneous power usage **or** generation of a device in watts (W). Homey uses it
automatically for any device that has it. The sign convention depends on the device's Energy role — see
[Device-class → Energy-role mapping](#device-class--energy-role-mapping).

### Meter Power

`meter_power` (or a `meter_power` sub-capability) is energy in kilowatt-hours (kWh) and is used in two ways:

1. **Cumulative energy** — the **total** energy consumed or generated over time; values continuously and only
   increase. Reset only when the device itself is reset or reinstalled. Example: a smart meter reading 12,345 kWh
   since installation.
2. **Non-cumulative** — energy used or generated in a **specific interval**, without accumulating past values.
   Example: energy consumed in the last 24 hours, or a battery's state of charge in kWh.

Everywhere in this file `meter_power` means the **cumulative** form unless stated otherwise.

Energy calculates consumption over a period by taking the **difference** in `meter_power` over time. Periodic resets
to zero or unexpected decreases cause data loss or invalid interpretation.

### Target Power

`target_power` lets Homey control the power consumption or production of a device in watts. It enables:

* Solar power curtailment
* Smart EV charging
* Controlling home batteries

It automatically generates the Flow **action** card "Set the target power" (argument `target_power`, a `range` from
`-25000` to `25000`, `step: 1`, label `W`) and the **trigger** card "The target power changed". The action card's hint
reads: *"This also switches the target power mode to Homey. For EV chargers, charging is automatically started or
stopped."* Available as of Homey **v12.13.0**.

### Target Power Mode

`target_power_mode` controls whether Homey or the device itself is in charge of power management. It is **optional**
and only useful when the device has its own smart logic (internal scheduling, self-consumption optimization, cloud
control, app control). Without it, Homey assumes full control at all times — fine for simple devices. It
automatically generates trigger, condition and action Flow cards. Available as of Homey **v12.13.0**.

| Value | Meaning |
| --- | --- |
| `device` | **Device in control.** The device operates autonomously with its own logic (built-in scheduling, self-consumption optimization). Target power values set by Homey are ignored. **This is the default mode.** |
| `homey` | **Homey in control.** Homey actively controls the device via `target_power`; the device executes exactly what Homey requests and disables its built-in smart logic. |

* Using the **Set target power** Flow card makes Homey switch `target_power_mode` to `homey` automatically.
* When switching `homey` → `device`, the driver should discard any `target_power` setpoint and resume internal logic.

---

## The `energy` object

Defined per driver in `/drivers/<driver_id>/driver.compose.json` (compiled into `app.json` as
`drivers[].energy`).

```json
{
  "name": { "en": "My Driver" },
  "energy": {
    "meterPowerImportedCapability": "meter_power.imported",
    "meterPowerExportedCapability": "meter_power.exported"
  }
}
```

### Complete key reference

| Key | Type | Allowed values | Since | Description |
| --- | --- | --- | --- | --- |
| `approximation` | object | `{ usageOn, usageOff }` **or** `{ usageConstant }` | — | Static power-usage approximation. The two shapes are mutually exclusive (JSON-schema `oneOf`, `additionalProperties: false` on each). |
| `approximation.usageOn` | number | watts | — | Power usage while the device is on. **Required together with `usageOff`.** |
| `approximation.usageOff` | number | watts | — | Power usage while the device is off (use the stand-by value if the device has stand-by). **Required together with `usageOn`.** |
| `approximation.usageConstant` | number | watts | — | Constant power usage of a device that cannot be turned on/off (e.g. a router). Cannot be combined with `usageOn`/`usageOff`. |
| `batteries` | string[] | one or more values from the [battery list](#batteries) | — | Type and amount of batteries, e.g. `["AAA", "AAA"]`. `minItems: 1`. |
| `cumulative` | boolean | **only `true`** | — | Marks a device that measures the total power/energy of the whole home or a power group (P1 meter, current clamp, gas/water meter). |
| `cumulativeImportedCapability` | string | a `meter_power` instance | `12.3.0` | Capability holding cumulative **imported** energy (from the device's perspective). |
| `cumulativeExportedCapability` | string | a `meter_power` instance | `12.3.0` | Capability holding cumulative **exported** energy. Omit when the device only measures import. |
| `meterPowerImportedCapability` | string | a `meter_power` instance | `12.4.5` | Capability holding energy **consumed/charged** by this device. |
| `meterPowerExportedCapability` | string | a `meter_power` instance | `12.4.5` | Capability holding energy **produced/discharged** by this device. Omit when the device cannot export. |
| `homeBattery` | boolean | **only `true`** | `12.3.0` | Marks the device as a home battery. Use with `class: "battery"`. |
| `evCharger` | boolean | **only `true`** | `12.4.5` | Marks the device as an EV charger. Use with `class: "evcharger"`. |
| `electricCar` | boolean | **only `true`** | `12.4.5` | Marks the device as an EV. Use with `class: "car"`. |

These are **all** the keys the app-manifest JSON schema defines under `drivers[].energy`. There is no
`electricityDelivered`, `electricityReturned`, `home_battery` or `ev_charger` key — those names do not exist in SDK
v3; the boolean flags are camelCase (`homeBattery`, `evCharger`, `electricCar`).

`cumulativeImportedCapability` / `cumulativeExportedCapability` and
`meterPowerImportedCapability` / `meterPowerExportedCapability` are only used on **Homey Pro (Early 2023)**,
**Homey Pro mini** and **Homey Cloud**.

Read the manifest-defined configuration through `Driver#manifest` (`this.driver.manifest.energy` from a device).

By default any change to `energy` in `driver.compose.json` is applied directly to existing, already paired devices —
**except** for devices that have called `Device#setEnergy()` (see below).

---

## Dynamically changing the energy configuration: `setEnergy()` / `getEnergy()`

| Method | Signature | Notes |
| --- | --- | --- |
| `Device#getEnergy()` | `getEnergy(): any` | Returns **only** the override previously set with `setEnergy()`. It does **not** return the `energy` object from `driver.compose.json`. |
| `Device#setEnergy(energy)` | `async setEnergy(energy: object): Promise<void>` | Overwrites **all** energy properties for this device. |

Use it when the required properties depend on the specific device or its capabilities, which are not known upfront.

* You must pass the **complete** `energy` configuration — `setEnergy()` overwrites every existing property.
* Once `setEnergy()` has been called, the device **permanently disregards** the `energy` object in
  `driver.compose.json`; later edits to the manifest are no longer applied to it automatically.
* To restore the manifest configuration, call `setEnergy()` again with the object read from the driver's manifest.
* These calls are expensive/impactful. Only use them when initially configuring the device.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDevice extends Homey.Device {

  async onInit() {
    const energyConfig = this.getEnergy();

    DeviceApi.on('energy-settings', (energySettings) => {
      if (energySettings.isSmartMeter() && energyConfig.cumulative !== true) {
        this.setEnergy({
          cumulative: true,
          cumulativeImportedCapability: 'meter_power.imported',
        }).catch(this.error);
      }
    });
  }

}

module.exports = MyDevice;
```

Restoring the manifest configuration:

```javascript
async restoreEnergyFromManifest() {
  const manifestEnergy = this.driver.manifest.energy;
  if (manifestEnergy) {
    await this.setEnergy(manifestEnergy);
  }
}
```

Python equivalents: `Device.set_energy()` / `Device.get_energy()`.

---

## Power: measuring vs approximating

Two strategies determine a device's power usage:

1. **Measuring power usage** — the device provides real measurements; give it `measure_power`.
2. **Approximating power usage** — the device provides none:
   1. **Configurable power usage properties** — static values in `energy.approximation` (`usageConstant`, or
      `usageOn` + `usageOff`), applied against the device's on/off state.
   2. **Approximated `measure_power` values** — set `measure_power` yourself and flag it as an approximation with
      the `approximated` capability option.

### Measuring power usage

When a device supports `measure_power` (real-time watts), Homey automatically uses that value.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "socket",
  "capabilities": ["onoff", "measure_power"]
}
```

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDevice extends Homey.Device {

  async onInit() {
    DeviceApi.on('power-usage-changed', (watts) => {
      this.setCapabilityValue('measure_power', watts).catch(this.error);
    });
  }

}

module.exports = MyDevice;
```

### Constant power usage (`energy.approximation`)

Without `measure_power`, Homey calculates power usage from `onoff` and `dim`, and shows the user settings for the
power consumption when on, when off, or (when the device cannot be switched) constant. Homey approximates the usage
by **calculating the total on-time**, optionally weighted by the brightness level. Providing defaults in the manifest
removes the need for the user to configure them.

A light bulb that draws 15 W on and 1 W off:

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "platforms": ["local", "cloud"],
  "connectivity": "zigbee",
  "class": "light",
  "capabilities": ["onoff", "dim"],
  "energy": {
    "approximation": {
      "usageOn": 15,
      "usageOff": 1
    }
  }
}
```

`usageOn` and `usageOff` are in watts. When the device has a stand-by function, use the **stand-by** value for
`usageOff`.

A device with constant draw, e.g. a router:

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "energy": {
    "approximation": {
      "usageConstant": 5
    }
  }
}
```

The user can always overwrite these values in the device's settings.

### Dynamic power usage (`approximated` capability option)

When power usage depends on configuration (e.g. Nanoleaf panels where the user adds panels), add `measure_power`
with the `approximated: true` capability option and compute/update the value yourself. The flag tells the user the
value is an approximation, not a measurement.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "sensor",
  "capabilities": ["onoff", "measure_power"],
  "capabilitiesOptions": {
    "measure_power": {
      "approximated": true
    }
  }
}
```

**Gotcha:** the docs name this flag three different ways — the prose calls it "the `measure_power.approximation`
flag", the JSON example and the capability-options table use `approximated`, and homey-lib's `measure_power` /
`meter_power` capability definitions declare the option as `isApproximated` (`type: boolean`, `default: false`).
`capabilitiesOptions` is a free-form object in the app-manifest schema, so none of the spellings fails validation.
Use `approximated: true` — it is the spelling in both the working JSON example and the capability-options table.

---

## Energy (kWh): imported vs exported

Devices that report consumption (washing machine) or generation (solar panels, discharging home battery) should have
`meter_power` — cumulative energy in kWh over long periods.

When a device measures **both** imported and exported energy (a smart plug attached to portable solar panels, a home
battery), define `meterPowerImportedCapability` and `meterPowerExportedCapability`.

* **Imported energy** = energy consumed or charged by the device.
* **Exported energy** = energy produced or discharged by the device.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "socket",
  "capabilities": [
    "onoff",
    "measure_power",
    "meter_power.imported",
    "meter_power.exported"
  ],
  "energy": {
    "meterPowerImportedCapability": "meter_power.imported",
    "meterPowerExportedCapability": "meter_power.exported"
  }
}
```

Any capability may be used as the value of `meterPowerImportedCapability` / `meterPowerExportedCapability` as long as
it is an **instance of `meter_power`** (`meter_power` itself, or `meter_power.<suffix>`) and is present in the
driver's `capabilities` array. The same rule applies to `cumulativeImportedCapability` /
`cumulativeExportedCapability`.

Omitting these properties excludes the device from every Energy feature that requires the import/export distinction.

---

## Controlling target power

`target_power` is a **setable number capability in watts** representing the desired power level. Actual power is
reported back through `measure_power`.

| Sign | Meaning |
| --- | --- |
| Positive | Power consumption (charging), or **maximum allowed production** for solar curtailment |
| Negative | Power production (discharging) |
| Zero | Idle, or full curtailment (solar) |

When the device cannot achieve the requested target power, **throw an error from the capability listener**.

### Range and step rules

| Rule | Detail |
| --- | --- |
| Range must include zero | `min <= 0 <= max`. Every device needs to be able to idle. Never raise `min` above zero to express a minimum operating threshold. |
| Exclude range must include zero | `excludeMin <= 0 <= excludeMax`. Values exactly at the boundaries are valid; only values **strictly between** them become `0`. |
| Step rounding | Values are rounded **toward zero** to the nearest `step`, so Homey never requests more power than intended. |
| Clamping | Values outside `min`/`max` are clamped to the nearest boundary. |
| Widest range | Set `min`/`max` to the **full operating range across all configurations**. For multi-phase EV chargers: 1-phase minimum to 3-phase maximum; the driver handles phase switching internally. |

`excludeMin` / `excludeMax` are capability options on `target_power` (see `references/capabilities.md`). They define
the dead zone around zero for devices with a minimum operating power, e.g. an EV charger that needs at least 6 A
(≈ 1380 W single-phase).

`setCapabilityOptions()` can update these dynamically, but it is an expensive call — do not do it often.

### Multi-capability listener

When a Flow sets `target_power`, Homey also sets `target_power_mode` and (for EV chargers) `evcharger_charging` in
quick succession. `registerMultipleCapabilityListener` debounces them into one callback, which reduces API calls to
the physical device. Separate `registerCapabilityListener` calls are simpler but deliver each change individually.

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    this.registerMultipleCapabilityListener(
      ['target_power', 'target_power_mode'],
      async ({ target_power, target_power_mode }) => {
        // Only the changed capabilities are present in the object
        if (target_power_mode === 'device') {
          await this.enableBuiltInScheduling();
          this.log('Switched to device mode - device controls itself');
          return;
        }

        if (target_power_mode === 'homey') {
          await this.disableBuiltInScheduling();
          this.log('Switched to homey mode');
        }

        const value = target_power ?? this.getCapabilityValue('target_power') ?? 0;
        const mode = target_power_mode ?? this.getCapabilityValue('target_power_mode');

        if (mode !== 'homey') {
          this.log('Ignoring target_power - not in homey mode');
          return;
        }

        await this.applyTargetPower(value);
      },
      500, // debounce timeout in ms
    );
  }

  async applyTargetPower(value) {
    if (value >= 0) {
      await this.setChargingPower(value);
    } else {
      await this.setDischargingPower(Math.abs(value));
    }
  }

}

module.exports = MyDevice;
```

### Custom `target_power_mode` values

`target_power_mode` values may be customized in `capabilitiesOptions`. Rules:

* The array **must** include a value with `id: "homey"`.
* The array **must** include at least one non-`homey` value.
* The default `device` value may be omitted when you define your own strategy values.
* The prefix `homey_` is **reserved** and cannot be used for custom ids.
* Any non-`homey` value means the device controls its own power.

```json
{
  "capabilitiesOptions": {
    "target_power_mode": {
      "values": [
        { "id": "homey", "title": { "en": "Homey" } },
        { "id": "self_use", "title": { "en": "Self-use" } },
        { "id": "price_based", "title": { "en": "Price-based" } }
      ]
    }
  }
}
```

---

## Device-class → Energy-role mapping

| Energy role | `class` | `energy` flag | Key capabilities | `measure_power` sign convention |
| --- | --- | --- | --- | --- |
| Consumer | any | — | `measure_power`, `meter_power` | Positive = consuming |
| Solar panel | `solarpanel` | — | `measure_power`, `meter_power` | **Positive = generating**; a negative value means the panel is consuming |
| Smart plug | `socket` | — | `onoff`, `measure_power`, `meter_power` | Positive = consuming |
| Smart plug → *Solar panel* (user setting) | `socket` | — | `measure_power`, `meter_power` | **Negative = generating** (Homey inverts it automatically) |
| Smart plug → *Battery* (user setting) | `socket` | — | `measure_power`, `meter_power`, `meterPower*Capability` | Positive = charging, negative = discharging |
| Smart plug → *EV Charger* (user setting) | `socket` | — | `measure_power`, `meter_power`, `meterPower*Capability` | Positive = charging, negative = discharging |
| Home battery | `battery` | `homeBattery: true` | `measure_power`, `measure_battery` | Positive = charging, negative = discharging |
| EV charger | `evcharger` | `evCharger: true` | `measure_power`, `evcharger_charging`, `evcharger_charging_state` | Positive = charging, negative = discharging (bidirectional) |
| EV | `car` | `electricCar: true` | `measure_battery`, `ev_charging_state` | — |
| Cumulative meter | any (docs use `sensor`) | `cumulative: true` | `measure_power`, `meter_power.*`, `meter_gas`, `meter_water` | Positive = importing |
| Battery-powered device | any | `batteries: [...]` | `measure_battery` or `alarm_battery` | — |

**Multi-purpose hardware requires separate Homey devices.** When integrating hardware that combines multiple energy
functions (an EV charger with a built-in solar inverter, a hybrid inverter with battery storage), create a **separate
Homey device per function**, each with its own device class. Each class is treated differently in Energy.

---

## Solar panels

Device class `solarpanel`.

* `measure_power` must be **positive** when generating. A negative value (e.g. `-13` W) makes Homey assume the panel
  is consuming rather than generating.
* For cumulative generation to be tracked, the driver needs a `meter_power` capability set to the total generated
  energy in kWh as a **positive** value. Use `meterPowerExportedCapability` to point at a different `meter_power`
  instance for generated energy.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "solarpanel",
  "capabilities": ["measure_power", "meter_power"],
  "energy": {
    "meterPowerExportedCapability": "meter_power"
  }
}
```

`meterPowerExportedCapability` defaults to `meter_power`, so it may be omitted here.

### Solar curtailment with `target_power`

For solar inverters `target_power` acts as a **maximum production limit (cap)**, not a production target: `1500`
means "produce up to 1500 W maximum". To **disable curtailment**, set `target_power` to its `max` — the driver must
interpret that as "produce at maximum capacity".

```json
{
  "name": { "en": "Solar Inverter" },
  "class": "solarpanel",
  "capabilities": [
    "measure_power",
    "meter_power",
    "target_power",
    "target_power_mode"
  ],
  "capabilitiesOptions": {
    "target_power": {
      "min": 0,
      "max": 10000
    }
  }
}
```

* In **device** mode the inverter produces at maximum capacity using its own logic.
* In **homey** mode Homey controls curtailment:
  * `5000` → limit production to 5000 W
  * `10000` (max) → no curtailment, produce at full capacity
  * `0` → full curtailment, stop producing

```javascript
'use strict';

const Homey = require('homey');

class MySolarInverter extends Homey.Device {

  async onInit() {
    this.registerCapabilityListener('target_power', async (value) => {
      const mode = this.getCapabilityValue('target_power_mode');
      if (mode !== 'homey') return;
      await this.applyTargetPower(value);
    });

    this.registerCapabilityListener('target_power_mode', async (mode) => {
      if (mode === 'homey') {
        const value = this.getCapabilityValue('target_power');
        await this.applyTargetPower(value);
      } else {
        // "device" mode: disable curtailment, produce at maximum
        await this.disableCurtailment();
      }
    });
  }

  async applyTargetPower(value) {
    const capabilityOptions = this.getCapabilityOptions('target_power');
    const maxPower = capabilityOptions.max;

    if (value >= maxPower) {
      await this.disableCurtailment();
      this.log('Curtailment disabled, producing at maximum');
    } else {
      await this.setCurtailmentLimit(value);
      this.log(`Curtailment set to ${value}W`);
    }
  }

}

module.exports = MySolarInverter;
```

---

## Smart plugs (`socket`)

Devices with class `socket` can measure power and energy being consumed and generated. The user can pick a different
device class in the **What's plugged in?** setting — among others `solarpanel`, `battery` and `evcharger`. Support
those three explicitly:

### Solar panel plugged in

The generated power must be set as a **negative** value, e.g. `setCapabilityValue('measure_power', -200)`; Homey
inverts it automatically. This is the **opposite** of the regular `solarpanel` device class. The user also gets the
[Invert power measurement](#invert-power-measurement) setting to flip the sign manually.

Homey uses `meter_power` for generated energy; use `meterPowerExportedCapability` to point at a different
`meter_power` instance.

### Battery plugged in

Small portable home batteries can be charged/discharged through a smart plug.

* `measure_power` **positive** when the plug is consuming (charging the battery).
* `measure_power` **negative** when producing (discharging the battery).
* `meter_power` is used for charged energy by default. To register charged and discharged energy separately, define
  `meterPowerImportedCapability` and `meterPowerExportedCapability`.

### EV charger plugged in

Choosing "EV Charger" in **What's plugged in?** includes the plug's measurements in Energy as if it were an EV
charger.

* `measure_power` **positive** when consuming (charging the EV).
* `measure_power` **negative** when producing (discharging the EV).
* `meter_power` is used for charged energy by default; add `meterPowerImportedCapability` and (if applicable)
  `meterPowerExportedCapability` for separate tracking.

---

## Cumulative measuring devices

P1 meters, current clamps and similar devices measure the **total** power and energy usage of a home or a power
group. They are the highest-level measuring devices in a home: every other power-consuming or -generating device is
measured by them. Mark them with `cumulative: true`.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "sensor",
  "capabilities": ["measure_power"],
  "energy": {
    "cumulative": true
  }
}
```

All power-consuming devices in Homey are **subtracted** from the total measured power usage of all `cumulative`
devices. The remaining, unaccounted-for usage is displayed as **"other"**.

### Gas and water meters

`cumulative` also applies to gas and water meters. Homey then reads:

* `meter_gas` — total gas consumed over time, in cubic metres (m³).
* `meter_water` — total water consumed over time, in cubic metres (m³).

Both must be **positive and continuously increasing**, reset only when the device is reset or reinstalled.

### Imported and exported energy

Most whole-home meters measure both directions (a P1 meter measures energy imported from the grid and energy exported
back to it). Define `cumulativeImportedCapability` and `cumulativeExportedCapability`:

* **Imported energy** = cumulative energy imported, from the device's perspective.
* **Exported energy** = cumulative energy exported, from the device's perspective.

Omit `cumulativeExportedCapability` when the device only measures imported energy. Omit **both** when the device
cannot separate the two directions at all — the device is then excluded from features that require the distinction.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "sensor",
  "capabilities": [
    "measure_power",
    "meter_power.imported",
    "meter_power.exported"
  ],
  "capabilitiesOptions": {
    "meter_power.imported": {
      "title": { "en": "Imported Energy" }
    },
    "meter_power.exported": {
      "title": { "en": "Exported Energy" }
    }
  },
  "energy": {
    "cumulative": true,
    "cumulativeImportedCapability": "meter_power.imported",
    "cumulativeExportedCapability": "meter_power.exported"
  }
}
```

---

## Home batteries

Device class `battery` plus `energy.homeBattery: true` (available as of Homey **v12.3.0**).

* `measure_power` — real-time power in watts. **Positive = consuming (charging)**, **negative = delivering power back
  to the home (discharging)**. This matches `target_power`'s convention and is the **opposite** of solar panels,
  where positive means generation.
* If the battery cannot report power, fall back to `battery_charging_state` (`charging` / `discharging` / `idle`).
  Omitting `measure_power` loses functionality in Energy.
* `measure_battery` — current state of charge.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "battery",
  "capabilities": ["measure_power", "measure_battery"],
  "energy": {
    "homeBattery": true
  }
}
```

Home batteries both consume and produce energy, so define separate import/export meters. **Imported** = energy
charged; **exported** = energy discharged. Omitting them excludes the device from features requiring that
distinction.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "battery",
  "capabilities": [
    "measure_power",
    "measure_battery",
    "meter_power.charged",
    "meter_power.discharged"
  ],
  "capabilitiesOptions": {
    "meter_power.charged": {
      "title": { "en": "Charged Energy" }
    },
    "meter_power.discharged": {
      "title": { "en": "Discharged Energy" }
    }
  },
  "energy": {
    "homeBattery": true,
    "meterPowerImportedCapability": "meter_power.charged",
    "meterPowerExportedCapability": "meter_power.discharged"
  }
}
```

### Home battery with `target_power`

Unlike EV chargers, home batteries respond **immediately** to `target_power` changes — there is no separate
start/stop capability. If the battery has a minimum charge/discharge threshold, use `excludeMin`/`excludeMax` to
define the dead zone.

```json
{
  "name": { "en": "Home Battery" },
  "class": "battery",
  "capabilities": [
    "measure_power",
    "measure_battery",
    "meter_power.charged",
    "meter_power.discharged",
    "target_power",
    "target_power_mode"
  ],
  "capabilitiesOptions": {
    "meter_power.charged": {
      "title": { "en": "Charged Energy" }
    },
    "meter_power.discharged": {
      "title": { "en": "Discharged Energy" }
    },
    "target_power": {
      "min": -5000,
      "max": 5000
    }
  },
  "energy": {
    "homeBattery": true,
    "meterPowerImportedCapability": "meter_power.charged",
    "meterPowerExportedCapability": "meter_power.discharged"
  }
}
```

* In **device** mode the battery uses its own optimization logic (self-consumption, time-of-use).
* In **homey** mode Homey directly controls power flow:
  * `3000` → charge at 3000 W
  * `0` → idle
  * `−3000` → discharge at 3000 W

```javascript
'use strict';

const Homey = require('homey');

class MyHomeBattery extends Homey.Device {

  async onInit() {
    this.registerCapabilityListener('target_power', async (value) => {
      const mode = this.getCapabilityValue('target_power_mode');
      if (mode !== 'homey') return;
      await this.applyTargetPower(value);
    });

    this.registerCapabilityListener('target_power_mode', async (mode) => {
      if (mode === 'homey') {
        const value = this.getCapabilityValue('target_power');
        await this.applyTargetPower(value);
      } else {
        // "device" mode: let device firmware resume internal balancing
        await this.enableBuiltInScheduling();
      }
    });
  }

  async applyTargetPower(value) {
    if (value > 0) {
      await this.setDeviceChargingPower(value);
      this.log(`Charging at ${value}W`);
    } else if (value < 0) {
      await this.setDeviceDischargingPower(Math.abs(value));
      this.log(`Discharging at ${Math.abs(value)}W`);
    } else {
      await this.setDeviceIdle();
      this.log('Battery idle');
    }
  }

}

module.exports = MyHomeBattery;
```

---

## EV chargers

Device class `evcharger` plus `energy.evCharger: true`. The `evCharger` property and the `evcharger_charging` /
`evcharger_charging_state` capabilities are available as of Homey **v12.4.5**.

* `measure_power` — real-time power in watts. **Positive** while charging the connected EV, **negative** while
  discharging it (bidirectional chargers).
* `evcharger_charging_state` — reflects the charging state so users can act on "EV is plugged in" etc.
* `evcharger_charging` — acts as the on/off switch for charging and automatically generates Flow cards such as
  "Start charging" and "Is charging".
* `meter_power` is used for charged energy by default. Define `meterPowerImportedCapability` (charged) and
  `meterPowerExportedCapability` (discharged) to distinguish the two. Omit `meterPowerExportedCapability` when the
  charger cannot discharge.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "evcharger",
  "capabilities": [
    "measure_power",
    "evcharger_charging",
    "evcharger_charging_state",
    "meter_power.charged",
    "meter_power.discharged"
  ],
  "capabilitiesOptions": {
    "meter_power.charged": {
      "title": { "en": "Charged Energy" }
    },
    "meter_power.discharged": {
      "title": { "en": "Discharged Energy" }
    }
  },
  "energy": {
    "evCharger": true,
    "meterPowerImportedCapability": "meter_power.charged",
    "meterPowerExportedCapability": "meter_power.discharged"
  }
}
```

### Auto start/stop charging

When the **Set target power** Flow card runs, Homey automatically:

* sets `target_power_mode` to `homey`;
* sets `evcharger_charging` to `true` (positive value) or `false` (zero/negative).

### Unidirectional EV charger

```json
{
  "name": { "en": "EV Charger" },
  "class": "evcharger",
  "capabilities": [
    "measure_power",
    "evcharger_charging",
    "evcharger_charging_state",
    "meter_power",
    "target_power",
    "target_power_mode"
  ],
  "capabilitiesOptions": {
    "target_power": {
      "min": 0,
      "max": 22000,
      "step": 230,
      "excludeMin": 0,
      "excludeMax": 1380
    }
  },
  "energy": {
    "evCharger": true
  }
}
```

### Bidirectional EV charger

```json
{
  "name": { "en": "EV Charger" },
  "class": "evcharger",
  "capabilities": [
    "measure_power",
    "evcharger_charging",
    "evcharger_charging_state",
    "meter_power.charged",
    "meter_power.discharged",
    "target_power",
    "target_power_mode"
  ],
  "capabilitiesOptions": {
    "meter_power.charged": {
      "title": { "en": "Charged Energy" }
    },
    "meter_power.discharged": {
      "title": { "en": "Discharged Energy" }
    },
    "target_power": {
      "min": -11000,
      "max": 22000,
      "step": 230,
      "excludeMin": -1380,
      "excludeMax": 1380
    }
  },
  "energy": {
    "evCharger": true,
    "meterPowerImportedCapability": "meter_power.charged",
    "meterPowerExportedCapability": "meter_power.discharged"
  }
}
```

`excludeMin`/`excludeMax` handle the minimum operating threshold (6 A × 230 V = 1380 W): any value between 1 and
1379 W automatically becomes 0. `step: 230` corresponds to 1 A at 230 V, the finest granularity for single-phase
charging.

* In **device** mode the charger uses its own built-in charging logic.
* In **homey** mode Homey controls the charging rate via `target_power`; use `evcharger_charging` to start/stop.
* When charging stops, the `target_power` value is **preserved** for the next session.

### Capability value processing

| Requested | Result | Reason |
| --- | --- | --- |
| 5000 W | Charge at 4830 W | Rounded down to nearest step (230 W) |
| 1000 W | Idle (0 W) | Inside exclude range (−1380 to 1380) |
| −1000 W | Idle (0 W) | Inside exclude range |
| −5000 W | Discharge at 4830 W | Rounded toward zero to nearest step |
| 25000 W | Charge at 22000 W | Clamped to max (22000) |
| −15000 W | Discharge at 11000 W | Clamped to min (−11000) |

### Capability listeners

```javascript
'use strict';

const Homey = require('homey');

class MyEVCharger extends Homey.Device {

  async onInit() {
    this.registerMultipleCapabilityListener(
      ['target_power', 'target_power_mode', 'evcharger_charging'],
      async ({ target_power, target_power_mode, evcharger_charging }) => {
        // All capability changes arrive as a single debounced batch.
        // Only the changed capabilities are present in the object.

        if (target_power_mode === 'device') {
          await this.enableBuiltInScheduling();
          this.log('Switched to device mode');
          return;
        }

        if (evcharger_charging === false) {
          await this.stopCharging();
          this.log('Stopped charging/discharging');
          return;
        }

        const isCharging = evcharger_charging === true
          || this.getCapabilityValue('evcharger_charging');
        const power = target_power ?? this.getCapabilityValue('target_power') ?? 0;

        if (evcharger_charging === true) {
          const amps = Math.round(Math.abs(power) / 230);
          if (power >= 0) {
            await this.startCharging(amps);
            this.log(`Started charging at ${power}W (${amps}A)`);
          } else {
            await this.startDischarging(amps);
            this.log(`Started discharging at ${Math.abs(power)}W (${amps}A)`);
          }
        } else if (target_power != null && isCharging) {
          const amps = Math.round(Math.abs(target_power) / 230);
          if (target_power > 0) {
            await this.setChargingCurrent(amps);
            this.log(`Charging power adjusted to ${target_power}W (${amps}A)`);
          } else if (target_power < 0) {
            await this.setDischargingCurrent(amps);
            this.log(`Discharging power adjusted to ${Math.abs(target_power)}W (${amps}A)`);
          } else {
            await this.setChargingCurrent(0);
            this.log('Power set to idle (0W)');
          }
        } else if (target_power !== undefined && !isCharging) {
          this.log(`Target power set to ${target_power}W, will apply when charging starts`);
        }
      },
      500, // debounce timeout in ms
    );
  }

}

module.exports = MyEVCharger;
```

### Dynamic phase configuration

When the charger switches phase configuration, update the capability options — sparingly, because
`setCapabilityOptions()` is expensive.

```javascript
async onPhaseConfigChanged(phaseMode) {
  // phaseMode: 1, 2, or 3
  const voltage = 230;
  const minAmps = 6;
  const minPower = minAmps * phaseMode * voltage;

  await this.setCapabilityOptions('target_power', {
    min: -32 * phaseMode * voltage,     // Max discharge
    max: 32 * phaseMode * voltage,      // Max charge (32A per phase)
    step: phaseMode * voltage,          // 230W, 460W, or 690W
    excludeMin: -minPower,              // -1380W, -2760W, or -4140W
    excludeMax: minPower,               // 1380W, 2760W, or 4140W
  });

  this.log(`Phase configuration changed to ${phaseMode}-phase`);
}
```

---

## EVs

Battery electric cars charged by an EV charger. Device class `car` plus `energy.electricCar: true`. The
`electricCar` property and the `ev_charging_state` capability are available as of Homey **v12.4.5**.

* `measure_battery` — current state of charge.
* `ev_charging_state` — add it when the EV can report plugged in/out, charging, discharging.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "car",
  "capabilities": ["measure_battery", "ev_charging_state"],
  "energy": {
    "electricCar": true
  }
}
```

---

## Batteries

All devices with `measure_battery` or `alarm_battery` — **except home batteries and EVs** — must declare which type
and how many batteries they use, via `energy.batteries`. This is shown to the user in the UI.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "class": "thermostat",
  "capabilities": [
    "measure_battery",
    "measure_temperature",
    "target_temperature"
  ],
  "energy": {
    "batteries": ["AAA", "AAA"]
  }
}
```

Complete list of allowed battery values (any other string fails validation):

| | | | |
| --- | --- | --- | --- |
| `LS14250` | `C` | `AA` | `AAA` |
| `AAAA` | `A23` | `A27` | `PP3` |
| `CR123A` | `CR2` | `CR1632` | `CR2032` |
| `CR2430` | `CR2450` | `CR2477` | `CR3032` |
| `CR14250` | `INTERNAL` | `OTHER` | |

Never give a driver **both** `measure_battery` and `alarm_battery` — it creates duplicate UI components and Flow
cards. Use `measure_battery` when the device reports a precise level, `alarm_battery` when it only reports a
low-battery threshold.

---

## Flow cards generated from Energy capabilities

Adding these capabilities automatically adds the following system Flow cards — never define your own duplicates.

| Capability | Type | Card id | Title (en) | Argument |
| --- | --- | --- | --- | --- |
| `measure_power` | trigger | `measure_power_changed` | The power changed | — (token `measure_power`) |
| `meter_power` | trigger | `meter_power_changed` | The power meter changed | — (token `meter_power`) |
| `meter_gas` | trigger | `meter_gas_changed` | The gas meter changed | — (token `meter_gas`) |
| `meter_water` | trigger | `meter_water_changed` | The water meter changed | — (token `meter_water`) |
| `measure_battery` | trigger | `measure_battery_changed` | The battery level changed | — (token `measure_battery`) |
| `alarm_battery` | trigger | `alarm_battery_true` | The battery alarm turned on | — |
| `alarm_battery` | trigger | `alarm_battery_false` | The battery alarm turned off | — |
| `alarm_battery` | condition | `alarm_battery` | The battery alarm is on/off | — |
| `target_power` | trigger | `target_power_changed` | The target power changed | — (token `target_power`) |
| `target_power` | action | `target_power_set` | Set the target power | `target_power` (`range`, −25000…25000, step 1, label `W`) |
| `target_power_mode` | trigger | `target_power_mode_changed` | The target power mode changed to … | `target_power_mode` (`dropdown`, capability values) |
| `target_power_mode` | condition | `target_power_mode_is` | The target power mode is / is not … | `target_power_mode` (`dropdown`) |
| `target_power_mode` | action | `target_power_mode_set` | Set the target power mode to … | `target_power_mode` (`dropdown`) |
| `evcharger_charging` | trigger | `evcharger_charging_true` | Started charging | — |
| `evcharger_charging` | trigger | `evcharger_charging_false` | Stopped charging | — |
| `evcharger_charging` | condition | `evcharger_charging` | Is / is not charging | — |
| `evcharger_charging` | action | `evcharger_charging_start` | Start charging | — |
| `evcharger_charging` | action | `evcharger_charging_stop` | Stop charging | — |
| `evcharger_charging_state` | trigger | `evcharger_charging_state_changed` | The EV charger charging state changed | `state` (`dropdown`) |
| `evcharger_charging_state` | condition | `evcharger_charging_state_is` | The EV charger charging state is / is not … | `state` (`dropdown`) |
| `ev_charging_state` | trigger | `ev_charging_state_changed` | The battery charging state changed | `state` (`dropdown`) |
| `ev_charging_state` | condition | `ev_charging_state_is` | The battery charging state is / is not … | `state` (`dropdown`) |
| `battery_charging_state` | trigger | `battery_charging_state_changed` | The battery charging state changed | `state` (`dropdown`) |
| `battery_charging_state` | condition | `battery_charging_state_is` | The battery charging state is / is not … | `state` (`dropdown`) |

The `dropdown` arguments are populated from the capability's `values` array (`"values": "$values"` in the capability
definition), so custom `target_power_mode` values automatically appear in the Flow cards.

---

## Device settings Homey adds automatically

Homey provides these settings to Energy devices under the listed conditions. They are Homey's own settings — do not
recreate them in `driver.settings.compose.json`.

| Setting | Shown when | Default | Effect |
| --- | --- | --- | --- |
| **Always on** | device class `socket` **and** `onoff` capability | disabled | Homey prevents the user from turning the device off; an error is returned when attempted. |
| **Exclude from Energy** | device has `meter_power` or `measure_power`, **or** device class `solarpanel` (or *Solar panel* in *What's plugged in?*), **or** the device is marked `cumulative` | disabled | The device disappears from Zone Control Energy and is left out of future Energy reports (existing reports are unchanged). |
| **Tracks total home energy consumption** | device is marked `cumulative` | **enabled** | Keeps the device treated as a highest-level measuring device in the home. Disabling it demotes it to a regular energy-measuring device. |
| **Invert power measurement** | device class `socket` **and** the user selected "Solar panel" in *What's plugged in?* | — | Inverts the sign of `measure_power` so produced power is displayed correctly. |
| **Power usage when off** | device does **not** have `measure_power` **and does** have `onoff` | `energy.approximation.usageOff` | Used to approximate consumption. |
| **Power usage when on** | device does **not** have `measure_power` **and does** have `onoff` | `energy.approximation.usageOn` | Used to approximate consumption. |
| **Constant power usage** | device has **none** of `measure_power`, `onoff`, `measure_battery`, `alarm_battery`; **and** no `energy.batteries`; **and** its class is not in the excluded list below | `energy.approximation.usageConstant` | Used to approximate consumption. |

Device classes that never get the **Constant power usage** setting:

`button`, `windowcoverings`, `blinds`, `curtain`, `sunshade`, `kettle`, `coffeemachine`, `remote`, `solarpanel`,
`vacuumcleaner`, `thermostat`

**Gotcha:** `energy_` is a **reserved device-setting id prefix** (alongside `homey:`, `zw_`, `zb_`, `mtr_`,
`thread_`, `zone_`, `satellite_mode_`, `homekit_`). The CLI warns for every setting id starting with it, including
inside `group` children. Namespace your own energy-related setting ids differently. See
`references/drivers-and-devices.md`.

---

## Appearing in Homey Energy — checklist

| Goal | Requirement |
| --- | --- |
| Device shows live power | `measure_power` capability, **or** `onoff` (+ optional `dim`) with `energy.approximation` so Homey can approximate. |
| Device contributes kWh totals | A `meter_power` instance whose value only increases (cumulative). |
| Device counted as whole-home/group meter | `energy.cumulative: true`; user leaves *Tracks total home energy consumption* enabled. |
| Import/export split (grid) | `energy.cumulative: true` + `cumulativeImportedCapability` (+ `cumulativeExportedCapability`). Homey Pro (Early 2023), Homey Pro mini and Homey Cloud only. |
| Import/export split (device) | `meterPowerImportedCapability` (+ `meterPowerExportedCapability`). Homey Pro (Early 2023), Homey Pro mini and Homey Cloud only. |
| Recognised as solar | `class: "solarpanel"` (positive `measure_power`) or a `socket` device with *Solar panel* selected (negative `measure_power`). |
| Recognised as home battery | `class: "battery"` + `energy.homeBattery: true` + `measure_battery`. |
| Recognised as EV charger | `class: "evcharger"` + `energy.evCharger: true`. |
| Recognised as EV | `class: "car"` + `energy.electricCar: true` + `measure_battery`. |
| Gas / water totals | `energy.cumulative: true` + `meter_gas` and/or `meter_water`, positive and monotonically increasing. |
| Controllable by Homey Energy | `target_power` (and optionally `target_power_mode`), `min <= 0 <= max`. |
| Device excluded | User enables *Exclude from Energy*, or the device is missing the capabilities above. |

---

## Validation rules the CLI enforces

`homey app validate [--level debug|publish|verified]`. Everything below is checked on `drivers[].energy` and the
energy-related `capabilitiesOptions`.

### Errors (validation fails)

| Rule | Message / behaviour |
| --- | --- |
| `energy.batteries` entries must come from the allowed list | `drivers.<id> invalid 'battery': <value>. Allowed values: LS14250, C, AA, …` |
| `cumulativeImportedCapability` must be a `meter_power` instance | `drivers.<id> has 'cumulativeImportedCapability': '<value>' but only instances of 'meter_power' are allowed.` |
| `cumulativeExportedCapability` must be a `meter_power` instance | `drivers.<id> has 'cumulativeExportedCapability': '<value>' but only instances of 'meter_power' are allowed.` |
| `meterPowerImportedCapability` must be a `meter_power` instance | `drivers.<id> has 'meterPowerImportedCapability': '<value>' but only instances of 'meter_power' are allowed.` |
| `meterPowerExportedCapability` must be a `meter_power` instance | `drivers.<id> has 'meterPowerExportedCapability': '<value>' but only instances of 'meter_power' are allowed.` |
| `target_power` range must include 0 | `drivers.<id>.capabilitiesOptions.<cap>.min/max must include 0 (min <= 0 <= max) to allow idle state` |
| `target_power` exclude range must include 0 | `drivers.<id>.capabilitiesOptions.<cap>.excludeMin/excludeMax must include 0 (excludeMin <= 0 <= excludeMax)` |
| `target_power_mode.values` must contain `homey` | `drivers.<id>.capabilitiesOptions.<cap>.values must include "homey" value` |
| `target_power_mode.values` must contain a non-`homey` value | `drivers.<id>.capabilitiesOptions.<cap>.values must include at least one non-homey value` |
| `target_power_mode.values` ids may not start with `homey_` | `drivers.<id>.capabilitiesOptions.<cap>.values custom values cannot use reserved prefix "homey_": <id>` |
| Battery capability without battery metadata (**`--level publish` / `verified` only**) | `drivers.<id> is missing an array 'energy.batteries' because the capability <measure_battery\|alarm_battery> is being used.` Satisfied by `energy.batteries`, `energy.homeBattery` **or** `energy.electricCar`. |
| Capability `minCompatibility` | Using `target_power` / `target_power_mode` requires app `compatibility` ≥ `12.13.0`; `evcharger_charging`, `evcharger_charging_state`, `ev_charging_state` require ≥ `12.4.5`; `battery_charging_state` requires ≥ `12.2.0`. Otherwise: `drivers.<id> capability: <cap> is not available for compatibility <range>, requires minimum: <version>` |
| Class `minCompatibility` | `battery`, `evcharger`, `car` all require app `compatibility` ≥ `12.0.0`. Otherwise: `drivers.<id> driver class: <class> is not available for compatibility <range>, requires minimum: <version>` |
| `capabilitiesOptions` entry must be an object | `drivers.<id>.capabilitiesOptions.<cap> must be an object` (rejects `null`, arrays and primitives). |
| Schema — boolean flags | `cumulative`, `homeBattery`, `evCharger`, `electricCar` are `"enum": [true]`. Writing `false` **fails schema validation**; remove the key instead. |
| Schema — `approximation` shape | `oneOf`: either `{ usageOn, usageOff }` (both required, nothing else) or `{ usageConstant }` (required, nothing else). Mixing them, or supplying only `usageOn`, fails. |
| Schema — `batteries` | `type: array`, `minItems: 1`, items `type: string`. |

`Capability.isInstanceOfId(x, 'meter_power')` is `true` for exactly `meter_power` and for anything starting with
`meter_power.` — so `meter_power.imported`, `meter_power.charged`, `meter_power.foo` all pass. The same matcher gates
the `target_power` / `target_power_mode` option checks, so they also run on sub-capabilities such as
`target_power.phase1`.

Omitted bounds default to `0` in both range checks: the `min`/`max` check reads a missing `min` (or `max`) as `0`, so
`{"max": 22000}` alone and `{"min": -5000}` alone both pass. The `excludeMin`/`excludeMax` check only runs when **at
least one** of the two is a number, and treats the missing one as `0`.

### Warnings (validation still passes)

| Rule | Message |
| --- | --- |
| `cumulative: true` + a `meter_power` instance, no `cumulativeImportedCapability` | `Warning: drivers.<id> has energy.cumulative set to true, but is missing 'cumulativeImportedCapability'.` |
| `cumulative: true` + a `meter_power` instance, no `cumulativeExportedCapability` | `Warning: drivers.<id> has energy.cumulative set to true, but is missing 'cumulativeExportedCapability'.` |
| `homeBattery: true` + a `meter_power` instance, no `meterPowerImportedCapability` | `Warning: drivers.<id> has energy.homeBattery set to true, but is missing 'meterPowerImportedCapability'.` |
| `homeBattery: true` + a `meter_power` instance, no `meterPowerExportedCapability` | `Warning: drivers.<id> has energy.homeBattery set to true, but is missing 'meterPowerExportedCapability'.` |
| `evCharger: true` + a `meter_power` instance, no `meterPowerImportedCapability` | `Warning: drivers.<id> has energy.evCharger set to true, but is missing 'meterPowerImportedCapability'.` |

These warnings only fire when the driver already declares at least one `meter_power` instance in `capabilities`.
There is **no** warning for `evCharger` + missing `meterPowerExportedCapability` — a unidirectional charger is a
legitimate configuration.

---

## Gotchas

- **`getEnergy()` does not return the manifest's `energy` object.** It returns **only** an override previously set
  with `setEnergy()`. To read the manifest configuration, use `this.driver.manifest.energy`.
- **`setEnergy()` is a permanent opt-out of the manifest.** After the first call for a device, later edits to
  `energy` in `driver.compose.json` are no longer applied to that device automatically. Restore it explicitly by
  calling `setEnergy(this.driver.manifest.energy)`.
- **`setEnergy()` overwrites everything.** It is not a merge — always pass the complete configuration.
- **`setEnergy()` / `setCapabilityOptions()` are expensive.** Only call them while initially configuring a device,
  never on every `onInit()` and never in a polling loop.
- **The boolean energy flags accept only `true`.** `"cumulative": false`, `"homeBattery": false`,
  `"evCharger": false` and `"electricCar": false` all fail schema validation — delete the key instead. Same pattern
  as `"deprecated": false` on the driver manifest.
- **`usageConstant` cannot be combined with `usageOn`/`usageOff`,** and `usageOn`/`usageOff` must be supplied
  together. The schema's `oneOf` + `additionalProperties: false` rejects every mixed shape.
- **Sign conventions differ per role, and the smart-plug case is inverted.** `solarpanel` class: positive = producing.
  A `socket` device set to *Solar panel* by the user: **negative** = producing. Home batteries and EV chargers:
  positive = charging/consuming, negative = discharging/producing. Getting this wrong silently reverses the whole
  Energy graph.
- **`meter_power` must never decrease or reset.** Energy derives consumption from the delta over time; resets to zero
  or unexpected drops cause data loss and invalid interpretation. If your source resets (e.g. a daily counter), keep
  your own monotonic running total and publish that instead.
- **Import/export capabilities only take effect on Homey Pro (Early 2023), Homey Pro mini and Homey Cloud** — the
  original Homey Pro ignores `cumulativeImportedCapability` / `cumulativeExportedCapability` (v12.3.0+) and
  `meterPowerImportedCapability` / `meterPowerExportedCapability` (v12.4.5+).
- **Omitting the import/export properties silently drops features.** The device is excluded from everything that
  needs the distinction (charged vs discharged, imported vs exported) instead of failing loudly.
- **`target_power` min/max must include 0.** Never encode a minimum operating threshold by raising `min` above 0 —
  the CLI rejects it. Use `excludeMin`/`excludeMax` for the dead zone; every device must be able to idle.
- **Only values strictly inside the exclude range become 0.** Values exactly on `excludeMin`/`excludeMax` are valid
  setpoints.
- **`target_power` values are rounded toward zero,** never away from it, so Homey never requests more power than
  intended. Combine this with `step` deliberately (`step: 230` = 1 A at 230 V).
- **Multi-purpose hardware must be split into multiple Homey devices** (one per energy function, each with its own
  class). A single device cannot be both an EV charger and a solar inverter.
- **Never give a driver both `measure_battery` and `alarm_battery`** — duplicate UI components and Flow cards.
- **`energy.batteries` is required at publish level** for any driver using `measure_battery` or `alarm_battery`,
  unless the driver sets `homeBattery` or `electricCar`. It passes at `--level debug` and then fails at
  `--level publish` — validate with the publish level before shipping.
- **Home batteries and EVs must NOT declare `energy.batteries`** — they are excluded from that requirement by
  `homeBattery` / `electricCar`.
- **A capability referenced by `meterPower*Capability` / `cumulative*Capability` must also be listed in the driver's
  `capabilities` array.** The CLI only checks that the value is a `meter_power` instance, so a typo like
  `meter_power.imprted` passes validation and silently produces no data at runtime.
- **`target_power_mode` defaults to `device`,** meaning the device ignores Homey's setpoints until something switches
  it to `homey`. The **Set target power** Flow card does that switch automatically; your own code must not assume
  `homey` mode.
- **Throw from the `target_power` capability listener when the setpoint cannot be reached** — that is the documented
  failure channel.
- **`energy_` is a reserved device-setting id prefix.** Homey's own energy settings live there; the CLI warns on any
  collision.
- **Fire-and-forget energy writes need `.catch(this.error)`.** `setCapabilityValue('measure_power', …)` inside an
  event handler is the classic unhandled-rejection source; an unhandled rejection can take the whole app down.
- **Insights are write-only from inside the app.** You can push `measure_power` / `meter_power` values but you cannot
  read historical Energy or Insights data back through the App SDK — keep your own rolling buffer in the device store
  if you need history. See `references/advanced-features.md`.

---

## Sources

- <https://apps.developer.homey.app/the-basics/devices/energy>
- <https://apps.developer.homey.app/the-basics/devices/capabilities>
- <https://apps.developer.homey.app/the-basics/devices/best-practices/battery-status>
- <https://apps.developer.homey.app/the-basics/devices>
- <https://apps.developer.homey.app/the-basics/devices/settings>
- <https://apps.developer.homey.app/app-store/publishing>
- <https://apps-sdk-v3.developer.homey.app/Device.html>
- <https://python-apps-sdk-v3.developer.homey.app/device.html>
