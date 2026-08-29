# Zigbee (Homey Apps SDK v3)

Everything needed to build a Zigbee driver for Homey: the `zigbee` object in `driver.compose.json`,
`homey-zigbeedriver` (`ZigBeeDevice`, `ZigBeeLightDevice`, `ZigBeeDriver`), the `zigbee-clusters`
ZCL layer (`ZCLNode`, `CLUSTER`, `BoundCluster`, custom clusters), the raw Zigbee API, the Zigbee
Developer Tools + interview workflow, Zigbee OTA firmware updates, and the SDK v2 → v3 migration.
Siblings: `references/wireless-lan-discovery.md`, `references/drivers-and-devices.md`,
`references/app-and-manifest.md`, `references/cli-and-tooling.md`.

---

## 1. Zigbee concepts

| Concept | Meaning |
| --- | --- |
| **Endpoint** | A numbered container on a node holding clusters. Keys of `zigbee.endpoints` in the manifest. |
| **Cluster** | A capability of a Zigbee device (e.g. `onOff`, `levelControl`). Has attributes + commands. |
| **Server cluster** | The entity that *stores* the attributes of a cluster. |
| **Client cluster** | The entity that *affects or manipulates* those attributes. |
| **Attribute** | A cluster property that can be read, written and reported to bound nodes (e.g. `currentLevel`). |
| **Command** | An action on a cluster (e.g. `moveToLevel`). Travels client→server (Homey → bulb) or server→client (remote → Homey). |
| **Binding** | A link created from Homey to a cluster on a node so the node may send commands/reports to Homey. Declared per endpoint via `bindings` in the manifest. |
| **BoundCluster** | Your app-side implementation (`zigbee-clusters`) that receives commands sent *to* Homey. |
| **Group** | Broadcast address several nodes listen on (Zigbee's equivalent of Z-Wave association groups). Created via the device's Find-and-Bind / commissioning procedure. |
| **Router** | Mains-powered node that routes messages and extends the mesh. |
| **End Device** | Node that does not route. Usually battery powered. |
| **SED** | Sleepy End Device — an End Device that sleeps and only polls its parent Router periodically. |

Node structure: `Node → Endpoint 1..n → Cluster → { Commands, Attributes }`.

**Group-broadcast listening differs per platform:**

| Platform | Behaviour |
| --- | --- |
| Homey Pro (2016—2019), Homey Bridge | Listens to **all** group broadcasts on the network. |
| Homey Pro (2023 — 2026), Homey Pro mini | Listens only to **group ID 0** and groups advertised by Touchlink via `getGroups`. |

**Sleepy End Devices (SEDs):** may not answer soon, or at all. Most devices stay awake for a short
period directly after pairing — that is the only moment reliable communication is guaranteed.
Because the parent Router buffers only a few messages and the SED fetches one per wake-up, **issue
one request at a time**. A SED is identified by the "Receive When Idle" flag in the Zigbee developer
tools, or programmatically via `this.node.receiveWhenIdle` on `ZigBeeNode`.

Full protocol reference: [Zigbee Cluster Specification (PDF)](https://etc.athom.com/zigbee_cluster_specification.pdf).
Working example app: <https://github.com/athombv/com.ikea.tradfri-example>.

---

## 2. Workflow: physical device → driver

1. **Pair the device as "Basic Zigbee Device"** in Homey. Pairing is fully handled by Homey — you
   **cannot** implement pair views for Zigbee (same as Z-Wave).
2. Read `manufacturerName` and `productId` from the device settings, or from the **Nodes Table** in
   the [Zigbee Developer Tools](https://tools.developer.homey.app/tools/zigbee) (columns
   *Manufacturer* → `manufacturerName`, *Model ID* → `productId`).
3. Press **Interview** on the node to dump its endpoints/clusters/commands/attributes as JSON.
   For SEDs this can take a while; the node must be online.
4. Write the `zigbee` object in `/drivers/<driver_id>/driver.compose.json`.
5. Implement `/drivers/<driver_id>/device.js` extending `ZigBeeDevice` (or `ZigBeeLightDevice`).

---

## 3. Zigbee Developer Tools

<https://tools.developer.homey.app/tools/zigbee>

### Nodes Table columns

| Column | Meaning |
| --- | --- |
| Node ID | Random number identifying the node in the table. |
| IEEE Address | Unique identifier of the Zigbee device. |
| Network Address | Current network address of the node. |
| Type | `Router` (mains-powered repeater) or `EndDevice` (battery, mostly asleep). |
| Online | Updated by the refresh button; whether the node answers a ping request. |
| Receive When Idle | Only routers can receive while idle; `false` ⇒ sleepy device. |
| Manufacturer | The `manufacturerName` for your driver manifest. |
| Model ID | The `productId` for your driver manifest. |
| Route | Last known route used to reach the node (not necessarily the shortest path). |

- **Interview** — produces a JSON structure of the node: `modelId`, `manufacturerName`,
  `endpointDescriptors` (endpoints + supported clusters), and `endpoints` (per-cluster commands,
  attributes and attribute reporting configurations).
- **Refresh Nodes** — pings all router nodes to update *Online*. Slow and puts load on the network.

### System Information

| Field | Meaning |
| --- | --- |
| Channel | Current channel; also a selector to change it. |
| Pan ID | Personal Area Network ID of this Homey's Zigbee network. |
| Extended PAN ID | Extended Personal Area Network ID. |
| IEEE Address | Homey's unique identifier on the Zigbee network. |
| Network Key | Key used to encrypt all Zigbee traffic on Homey. |
| Network Address | Always `0` — Homey is the coordinator. |
| Current Command | What Homey's Zigbee chip is currently busy with (e.g. an extended interview). |

**Changing the channel** is radical: all Zigbee routers must be online so they receive the change
message; it can take up to 10 minutes and some devices may need to be re-paired.

---

## 4. Dependencies

```bash
npm install --save homey-zigbeedriver zigbee-clusters
```

- `zigbee-clusters` is a **peerDependency** of `homey-zigbeedriver` (`^2.1.2 || ^3.0.2` for
  `homey-zigbeedriver@2.2.17`) — it must be installed with a compatible version.
- `homey-zigbeedriver` requires **Homey Apps SDK v3**.
- **`zigbee-clusters` is currently not available for Python apps.** Python apps can only use the raw
  Zigbee API (`self.homey.zigbee.get_node()` + `send_frame`/`handle_frame`).

Three API levels, each built on the previous one:

| Level | Package | Use when |
| --- | --- | --- |
| 1 | `homey-zigbeedriver` | Almost always. Maps Homey capabilities ↔ Zigbee clusters. |
| 2 | `zigbee-clusters` | Advanced: bound clusters, custom clusters, direct ZCL calls. |
| 3 | Zigbee API (`this.homey.zigbee`) | Raw frames. Not advised; present as an escape hatch. |

---

## 5. `driver.compose.json` — the `zigbee` object

```json
{
  "name": { "en": "My Driver" },
  "class": "socket",
  "capabilities": ["onoff", "dim"],
  "platforms": ["local", "cloud"],
  "connectivity": ["zigbee"],
  "zigbee": {
    "manufacturerName": "DummyManuf",
    "productId": ["control outlet 123"],
    "endpoints": {
      "1": {
        "clusters": [0, 4, 5, 6],
        "bindings": [6]
      }
    },
    "learnmode": {
      "image": "/drivers/my_driver/assets/learnmode.svg",
      "instruction": { "en": "Press the button on your device three times" }
    }
  }
}
```

### Schema (homey-lib `zigbeeDevice`)

Required: `manufacturerName`, `productId`, `endpoints`.

| Key | Type | Notes |
| --- | --- | --- |
| `manufacturerName` | string \| string[] | Manufacturer id used to identify the device. |
| `productId` | string \| string[] | Product id(s). Use an array when one driver targets several very similar devices. |
| `endpoints` | object, keys must match `^[0-9]+$` | Endpoint definition. **Only endpoints and clusters listed here become available on the `ZCLNode`.** Each endpoint object is `additionalProperties: false` — the *only* allowed keys are `clusters` and `bindings`, both optional. |
| `endpoints.<id>.clusters` | number[] | Cluster ids implemented **as client** — clusters you send commands to / read attributes from on the remote node. |
| `endpoints.<id>.bindings` | number[] | Cluster ids implemented **as server** — clusters you want to *receive* commands on. A bind request is made to the node during pairing for each entry. Required for attribute reporting on that cluster. |
| `learnmode` | object | `instruction` is **required** (Translation Object); `image` is an optional path string. These are the only two properties the schema declares, but the object is **not** sealed (`additionalProperties` unset), so stray keys pass silently. |
| `devices` | object | Sub-device definitions (see §5.2). Documented but **not part of the `zigbeeDevice` schema** — it validates only because `zigbeeDevice` does not set `additionalProperties: false`. |

Those four (`manufacturerName`, `productId`, `endpoints`, `learnmode`) are the *complete* property
list of the `zigbeeDevice` definition — there is nothing else to set inside the `zigbee` object.

Driver-level siblings you almost always set with it: `"connectivity": ["zigbee"]` (schema enum:
`lan`, `cloud`, `ble`, `zwave`, `zigbee`, `infrared`, `rf433`, `rf868`, `matter`) and
`"platforms"` (schema enum: `cloud`, `local`).

> **Discrepancy — the Zigbee permission.** In practice a Zigbee driver declares **no** app
> permission: Homey grants Zigbee access per paired device on the basis of the driver's `zigbee`
> object, and the published permissions guide lists no Zigbee entry. *However*, homey-lib's
> authoritative permission list (`assets/app/permissions.json`, 13 entries) **does** contain
> `homey:wireless:zigbee` — "Send and receive Zigbee for specific devices" — so it is a real
> permission id, not an internal-only one. The manifest schema types `permissions` as a plain
> `string[]`, so it neither requires nor rejects it. Keep omitting it unless Athom's review asks
> otherwise, but do not be surprised to see it in a published app manifest.

**Removed in SDK v3:** `deviceId` and `profileId` are no longer used to identify a Zigbee device —
delete them. Only `manufacturerName` (v2 called it `manufacturerId`) and `productId` remain, plus
the new mandatory `endpoints`.

### 5.1 Multi-device drivers (several products in one driver)

```json
{
  "zigbee": {
    "manufacturerName": ["IKEA of Sweden", "IKEA of Sweden AB"],
    "productId": ["TRADFRI bulb E27 W opal 1000lm", "TRADFRI bulb E14 W op/ch 400lm"],
    "endpoints": { "1": { "clusters": [0, 3, 4, 5, 6, 8], "bindings": [8] } }
  }
}
```

Any (`manufacturerName`, `productId`) combination in the two arrays matches the driver. Use
`ZigBeeDevice#energyMap` (§6.7) to give each `productId` its own energy object.

### 5.2 Sub devices (one physical node → multiple Homey devices)

> Requires Homey **v5.0.0+** and `homey-zigbeedriver@1.6.0+`. The driver **must** extend
> `ZigBeeDriver`.

```json
{
  "name": { "en": "My Driver" },
  "class": "socket",
  "capabilities": ["onoff", "dim"],
  "zigbee": {
    "manufacturerName": "DummyManuf",
    "productId": ["control outlet 123"],
    "endpoints": { "1": { "clusters": [0, 4, 5, 6], "bindings": [6] } },
    "devices": {
      "secondOutlet": {
        "class": "light",
        "capabilities": ["onoff"],
        "name": { "en": "Second Outlet" },
        "settings": []
      }
    }
  }
}
```

- Each key of `devices` becomes `subDeviceId` in the device's **data object**:
  `const { subDeviceId } = this.getData();`.
- A sub device may contain any property the root device can (`class`, `name`, `capabilities`, …);
  omitted properties are copied from the root device. Add `"settings": []` if the sub device should
  **not** inherit the root device's settings.
- All `Device` instances of one node share the **same `ZCLNode`** instance and can access all
  endpoints. `ZigBeeDriver`'s only job is holding that cache: `_zclNodes = new Map()` keyed by the
  device data `token`. That is why the driver must extend it — `ZigBeeDevice#onInit` throws
  `Driver <id> must extend ZigBeeDriver when using Zigbee sub devices` otherwise.
- Prefer a single Homey device per physical device; only split when it genuinely improves UX
  (e.g. a socket with multiple outputs).
- Flow cards can target sub devices with `"$filter": "flags=zigbeeSubDevice"`.

Split the implementation with `Driver#onMapDeviceClass()`:

```javascript
// /drivers/<driver_id>/driver.js
'use strict';

const { ZigBeeDriver } = require('homey-zigbeedriver');

const RootDevice = require('./device.js');
const SecondOutletDevice = require('./secondOutlet.device.js');

class MyDriver extends ZigBeeDriver {

  onMapDeviceClass(device) {
    if (device.getData().subDeviceId === 'secondOutlet') return SecondOutletDevice;
    return RootDevice;
  }

}

module.exports = MyDriver;
```

### 5.3 IAS Zone (Intruder Alarm Systems)

As of Homey **v13.1.2**, Homey performs full IAS Zone enrollment automatically. Just add cluster id
`1280` to the endpoint's `clusters` array. `onZoneEnrollRequest` events are **no longer forwarded to
apps**, and Homey always assigns `zoneId: 0`. Listen to `zoneStatusChangeNotification` via a
`BoundCluster` for alarm state (see §9.6).

---

## 6. `homey-zigbeedriver` — `ZigBeeDevice`

`ZigBeeDevice extends Homey.Device`. `homey-zigbeedriver` exports `ZigBeeDevice`, `ZigBeeDriver`,
`ZigBeeLightDevice` and `Util`.

```javascript
// /drivers/<driver_id>/device.js
'use strict';

const { ZigBeeDevice } = require('homey-zigbeedriver');
const { CLUSTER } = require('zigbee-clusters');

class MyZigBeeDevice extends ZigBeeDevice {

  async onNodeInit({ zclNode, node }) {
    this.registerCapability('onoff', CLUSTER.ON_OFF);
    this.registerCapability('dim', CLUSTER.LEVEL_CONTROL);
  }

}

module.exports = MyZigBeeDevice;
```

### 6.1 Lifecycle

| Method | When |
| --- | --- |
| `onNodeInit({ zclNode, node })` | **Override this.** Called when the `ZCLNode` is ready. `node` is the `Homey.ZigBeeNode`. |
| `onEndDeviceAnnounce()` | Node sent an end-device-announce indication. For sleepy devices it means the node is temporarily awake; for mains devices usually a re-power. Default implementation logs. |
| `onDeleted()` | Removes all node/zclNode/endpoint/cluster listeners and clears poll intervals. If you override, call `super.onDeleted()`. |
| `onInit()` | Internal. Do not override without calling `super.onInit()`. In order: `super.onInit()` → throws `Driver <id> must extend ZigBeeDriver when using Zigbee sub devices` if `isSubDevice()` and the driver is not a `ZigBeeDriver` → migrates the `configuredAttributeReporting` store → `this.homey.zigbee.getNode(this)` → binds the `endDeviceAnnounce` listener → `updateEnergyConfiguration()` → re-uses the driver's shared `ZCLNode` for this node token or creates one → `setAvailable()` → `onMeshInit()` → `onNodeInit({ zclNode, node })` → sets the store key `zb_first_init` to `false`. |
| `onMeshInit()` | **Deprecated** since v1.0.0 (legacy from `homey-meshdriver`). Use `onNodeInit()`. |
| `isFirstInit()` | `true` only on the first init after the device was added (backed by store key `zb_first_init`). |
| `isSubDevice()` | `true` when `this.getData().subDeviceId` is a string. |

Note that `onInit` does **not** await the `getNode(…)` chain — it starts it and attaches a `.catch`
that only logs `Error: could not initialize node`. A throwing `onNodeInit` therefore leaves the
device *available* but half-initialized, and `zb_first_init` stays `true` so the next init retries
the first-init work.

**Best practice — do not initiate communication in `onInit`/`onNodeInit`.** Zigbee may not be ready
yet; queuing many requests at app start causes bottlenecks. Up to `homey-zigbeedriver@2.1.3` an
uncaught request promise makes the device **unavailable** with a "Zigbee was not ready" error;
2.1.4+ prevents unavailability but `onNodeInit` may not complete as expected.

```javascript
// DO — always catch. Return a fallback object if you destructure the result,
// otherwise the rejected path yields `undefined` and destructuring throws.
const { onOff } = await zclNode.endpoints[1].clusters.onOff
  .readAttributes(['onOff'])
  .catch(err => { this.error(err); return {}; });

// DON'T — uncaught promise
const value = await zclNode.endpoints[1].clusters.onOff.readAttributes(['onOff']);
```

Restrict genuinely-needed reads to the first init:

```javascript
async onNodeInit({ zclNode }) {
  if (this.isFirstInit() === true) {
    const { onOff } = await zclNode.endpoints[1].clusters.onOff
      .readAttributes(['onOff'])
      .catch(err => { this.error(err); return {}; });
  }
}
```

### 6.2 `registerCapability(capabilityId, cluster, clusterCapabilityConfiguration?)`

Maps a Homey capability to a Zigbee cluster. `cluster` must be a **ClusterSpecification** object
(`{ NAME, ID }`) — i.e. one of the `CLUSTER.*` constants from `zigbee-clusters`, never a string.
The user configuration **extends and overrides** the system configuration (see §6.4).

`ClusterCapabilityConfiguration` fields:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `get` | string | `null` | Cluster attribute (from `Cluster.ATTRIBUTES`) fetched by `readAttributes` when the capability value must be read. |
| `set` | string \| `(value, opts) => string` | `null` | Cluster command (from `Cluster.COMMANDS`) executed when the capability is set. A function is called with `(value, opts)` and must return the command name. |
| `setParser` | `(setValue, opts) => object \| null \| Promise` | — | Builds the command arguments object. Returning `null` **skips** executing the command. |
| `report` | string | `null` | Cluster attribute; incoming reports of it trigger `reportParser`. |
| `reportParser` | `(reportValue) => any \| null \| Promise` | — | Converts the reported value to a capability value. Returning `null` leaves the capability value unchanged. Returning an `Error` is also treated as "no value". |
| `endpoint` | number | *auto* | `ZCLNode` endpoint used for this configuration. When you do **not** pass a number, `registerCapability` resolves it with `getClusterEndpoint(cluster)` — the first endpoint that has the cluster — and **throws `missing_cluster`** if the cluster is on no endpoint. (The internal defaults object lists `1`, but the merge always overwrites it.) |
| `getOpts` | object | `{}` | See below. |
| `getOpts.getOnStart` | boolean | `false` | Read `get` when the `ZCLNode` initializes **and** the capability value is `null` **and** `node.receiveWhenIdle === true` (non-sleepy only). |
| `getOpts.getOnOnline` | boolean | `false` | Read `get` whenever the node sends an end device announce (sleepy devices can answer right after that). |
| `getOpts.pollInterval` | number \| string | — | Number: poll interval in **ms** (values < 1 are ignored). String: a device **setting key** whose value is the interval in ms. |
| `reportOpts.configureAttributeReporting` | `{ minInterval, maxInterval, minChange }` | — | On **first init only**, configures attribute reporting for the `report` attribute on the resolved `endpoint`. All three fields must be present **and** `report` must be a string **and** `reportParser` a function, otherwise the block is silently skipped. On failure it retries and then re-schedules for the next end device announce. |

```javascript
this.registerCapability('onoff', CLUSTER.ON_OFF, {
  set: value => (value ? 'setOn' : 'setOff'),
  setParser(setValue) { return {}; },
  get: 'onOff',
  report: 'onOff',
  reportParser(report) { return report === true; },
  reportOpts: {
    configureAttributeReporting: {
      minInterval: 3600,   // minimally once every hour
      maxInterval: 60000,  // maximally once every ~16 hours
      minChange: 1,
    },
  },
  endpoint: 1,
  getOpts: {
    getOnStart: true,
    getOnOnline: true,
    pollInterval: 30000,   // ms
  },
});
```

On the **first init** after pairing, `registerCapability` additionally performs a one-off
`getClusterCapabilityValue` for every configuration that defines `get`; on failure it retries on the
next end device announce.

### 6.3 `registerMultipleCapabilities(configs, listener)`

Registers several capabilities at once; changes are **debounced 500 ms** and delivered to one
listener so a single Zigbee command can serve them all.

```javascript
this.registerMultipleCapabilities([
  {
    capabilityId: 'onoff',
    cluster: CLUSTER.ON_OFF,
    userOpts: {
      setParser(setValue) { /* override the system parser */ },
    },
  },
  { capabilityId: 'dim', cluster: CLUSTER.LEVEL_CONTROL },
], (valueObj, optsObj) => {
  // Debounced event when one or more capabilities changed
});
```

- Entry keys: `capabilityId`, `cluster`, `userOpts`. (`capability` / `opts` are legacy aliases still
  accepted, to be removed in the next major version.)
- If the listener returns a falsy value or an `Error`, the library **falls back** to calling
  `setClusterCapabilityValue()` for each changed capability individually.

### 6.4 System capability configurations

`homey-zigbeedriver` ships default cluster↔capability mappings in `lib/system/capabilities`.
`registerCapability` merges your configuration on top of them. A system configuration exists **only**
for the (capability, cluster) pairs listed below — `lib/system/capabilities/<capabilityId>/<cluster
NAME>.js`. Register any other pair and you must supply the whole configuration yourself (no error is
raised; the file is simply not found).

All 28 shipped configurations (`homey-zigbeedriver@2.2.17`):

| Capability | Cluster | `get` / `report` attribute | `set` command | `getOpts` | Parser notes |
| --- | --- | --- | --- | --- | --- |
| `onoff` | `onOff` | `onOff` | `value => value ? 'setOn' : 'setOff'` | `getOnStart` | `setParser` returns `{}`; report is pass-through. |
| `dim` | `levelControl` | `currentLevel` | `moveToLevelWithOnOff` | `getOnStart` | set: `level = round(value × 254)`, `transitionTime = calculateLevelControlTransitionTime(opts)`, and it **also** sets the `onoff` capability to `value > 0`. report: `value / 254`. |
| `light_hue` | `colorControl` | — | `moveToColor` | — | HSV→CIE xy × 65536, saturation taken from the current `light_saturation` value (fallback `1`). |
| `light_saturation` | `colorControl` | — | `moveToColor` | — | HSV→CIE xy × 65536, hue taken from the current `light_hue` value (fallback `1`). |
| `light_temperature` | `colorControl` | `colorTemperatureMireds` | `moveToColorTemperature` | `getOnStart`, `getOnOnline` | Maps `0–1` over store values `colorTempMin`/`colorTempMax` (and back on report). Those store values must exist. |
| `light_mode` | `colorControl` | `colorMode` | `moveToColorTemperature` | `getOnStart`, `getOnOnline` | The `setParser` sends `moveToColorTemperature` or `moveToHueAndSaturation` **itself** and returns `null` so the declared `set` command is never executed. report: `currentHueAndCurrentSaturation`/`currentXAndCurrentY` → `'color'`, anything else → `'temperature'`. |
| `measure_battery` | `powerConfiguration` | `batteryPercentageRemaining` | — | — | `Math.round(value / 2)`; returns `null` when `value > 200` or `value === 255`. |
| `alarm_battery` | `powerConfiguration` | `batteryPercentageRemaining` | — | — | `Math.round(value / 2) <= (this.getSetting('batteryThreshold') \|\| this.batteryThreshold \|\| 1)`; `null` when `value > 200` or `value === 255`. |
| `alarm_contact` | `binaryInput` | `presentValue` | — | — | Pass-through. |
| `alarm_contact` | `occupancySensing` | `occupancy` | — | — | `value === 1`. |
| `alarm_motion` | `binaryInput` | `presentValue` | — | — | Pass-through. |
| `alarm_motion` | `occupancySensing` | `occupancy` | — | — | `value === 1`. |
| `alarm_heat` | `binaryInput` | `presentValue` | — | — | Pass-through. |
| `alarm_smoke` | `binaryInput` | `presentValue` | — | — | Pass-through. |
| `alarm_water` | `binaryInput` | `presentValue` | — | — | Pass-through. |
| `measure_temperature` | `temperatureMeasurement` | `measuredValue` | — | — | `value / 100`, rounded to 0.1. |
| `measure_temperature` | `deviceTemperature` | `currentTemperature` | — | — | **Pass-through, no division** — `deviceTemperature` already reports °C. |
| `measure_humidity` | `relativeHumidity` | `measuredValue` | — | — | `value / 100`, rounded to 0.1. |
| `measure_luminance` | `illuminanceMeasurement` | `measuredValue` | — | — | `Math.round(10 ** ((value − 1) / 10000))`. |
| `measure_pressure` | `pressureMeasurement` | `measuredValue` | — | — | Returns the raw value (kPa×10 == mbar); `0x8000` ⇒ `null`. |
| `measure_water` | `flowMeasurement` | `measuredValue` | — | — | `(value / 10) / 16.6667` l/min, rounded to 0.1. |
| `measure_power` | `electricalMeasurement` | `activePower` | — | `getOnStart` | `value × (this.activePowerFactor \|\| 1)`; negative ⇒ `null`. |
| `measure_current` | `electricalMeasurement` | `rmsCurrent` | — | `getOnStart` | `value × (this.acCurrentFactor \|\| 1)`; negative ⇒ `null`. |
| `measure_voltage` | `electricalMeasurement` | `rmsVoltage` | — | `getOnStart` | `value × (this.acVoltageFactor \|\| 1)`; negative ⇒ `null`. |
| `meter_power` | `metering` | `currentSummationDelivered` | — | `getOnStart` | `value × (this.meteringFactor \|\| 1)`; negative ⇒ `null`. |
| `windowcoverings_set` | `windowCovering` | `currentPositionLiftPercentage` | `goToLiftPercentage` | `getOnStart` | `0`/`1` are sent as `downClose`/`upOpen` and the parser returns `null`; otherwise `percentageLiftValue = round(map(0–1 → 0–100))`. Honours `this.invertPercentageLiftValue`. A 5000 ms debounce suppresses reports caused by Homey's own set. Report `< 0` or `> 100` ⇒ `null`. |
| `windowcoverings_state` | `windowCovering` | — | `upOpen` / `stop` / `downClose` | — | Maps `up`/`idle`/`down`; `setParser` returns `{}`. No `get`/`report`. |
| `windowcoverings_tilt_set` | `windowCovering` | `currentPositionTiltPercentage` | `goToTiltPercentage` | `getOnStart` | set: `percentageTiltValue = value × 100`; report: `value / 100`. |

Multiplier/divisor attributes are **not** read automatically — the factor silently defaults to `1`.
Set it yourself in `onNodeInit`:

```javascript
if (typeof this.activePowerFactor !== 'number') {
  const endpointId = this.getClusterEndpoint(CLUSTER.ELECTRICAL_MEASUREMENT);
  const { acPowerMultiplier, acPowerDivisor } = await zclNode.endpoints[endpointId]
    .clusters[CLUSTER.ELECTRICAL_MEASUREMENT.NAME]
    .readAttributes(['acPowerMultiplier', 'acPowerDivisor'])
    .catch(err => { this.error(err); return {}; });

  // Guard: a failed read leaves both undefined, which would set the factor to NaN
  if (typeof acPowerMultiplier === 'number' && typeof acPowerDivisor === 'number' && acPowerDivisor !== 0) {
    this.activePowerFactor = acPowerMultiplier / acPowerDivisor;
  }
}
```

The same pattern applies with `acCurrentMultiplier`/`acCurrentDivisor` →`this.acCurrentFactor`,
`acVoltageMultiplier`/`acVoltageDivisor` → `this.acVoltageFactor`, and `multiplier`/`divisor` on
`metering` → `this.meteringFactor`.

### 6.5 Attribute reporting

`configureAttributeReporting(AttributeReportingConfiguration[])` → `Promise`

| Field | Type | Default | Rules |
| --- | --- | --- | --- |
| `cluster` | ClusterSpecification | — | Required, e.g. `CLUSTER.COLOR_CONTROL`. |
| `attributeName` | string | — | Required, e.g. `'currentHue'`. |
| `minInterval` | number (s) | `0` | Range 0–65535. `< 0` throws `RangeError('invalid_min_interval_value')`. |
| `maxInterval` | number (s) | — | Range 0–65535. The implemented check is `maxInterval !== 0 && (maxInterval < 60 \|\| maxInterval < minInterval)` ⇒ `Error('invalid_max_interval_value')`, so it must be `0` **or** `≥ 60` **and** `≥ minInterval` (the JSDoc phrases this as "larger than 60"; `60` itself is accepted). `65535` = stop reporting. `maxInterval: 0` + `minInterval: 65535` = revert to the device's default configuration. |
| `minChange` | number | `1` | Minimum change that triggers a report. Irrelevant for discrete (non-analog) data types — `zigbee-clusters` strips it automatically. Forced to `0` when `maxInterval === 0 && minInterval === 65535`. |
| `endpointId` | number | `1` | Endpoint index. Unlike `registerCapability`'s `endpoint`, this is **not** auto-resolved — it is `1` unless you pass a number. |

```javascript
'use strict';

const { ZigBeeDevice } = require('homey-zigbeedriver');
const { CLUSTER } = require('zigbee-clusters');

class MySensor extends ZigBeeDevice {

  async onNodeInit({ zclNode }) {
    // 1) Configure reporting directly (batch per cluster/endpoint!)
    await this.configureAttributeReporting([
      {
        endpointId: 1,
        cluster: CLUSTER.COLOR_CONTROL,
        attributeName: 'currentHue',
        minInterval: 0,
        maxInterval: 300,
        minChange: 10,
      },
      {
        endpointId: 1,
        cluster: CLUSTER.COLOR_CONTROL,
        attributeName: 'currentSaturation',
        minInterval: 0,
        maxInterval: 300,
        minChange: 10,
      },
    ]).catch(err => this.error(err));

    // 2) Listen for the reports
    zclNode.endpoints[1].clusters.colorControl.on('attr.currentHue', currentHue => {
      this.log('currentHue', currentHue);
    });

    // 3) Or configure it as part of a capability registration
    this.registerCapability('dim', CLUSTER.LEVEL_CONTROL, {
      reportOpts: {
        configureAttributeReporting: {
          minInterval: 0,
          maxInterval: 60000,
          minChange: 5,
        },
      },
    });
  }

}

module.exports = MySensor;
```

Behaviour details:
- Configurations are **grouped by endpoint + cluster** so each cluster needs only one remote call —
  important for sleepy devices. Always pass all attributes of one cluster in a single call.
- Each `configureReporting` call is wrapped with a **2× retry** (`Util.wrapAsyncWithRetry(fn, 2)`).
- The validation above runs **before** any radio traffic, and it throws synchronously out of the
  returned promise — a single bad entry aborts the whole call.
- Successful configurations are persisted in the device **store** under
  `configuredAttributeReporting` (a flat array), each entry carrying `lastUpdated`, `clusterName`,
  `attributeName`, `endpointId`. Re-configuring the same endpoint/cluster/attribute replaces the
  previous entry.
- A **binding** is usually required first: add the cluster id to `bindings` in the manifest.
- Configuring attribute reporting on sleepy end devices is **recommended** — it gives Homey a
  periodic heartbeat proving the device is still on the network.

### 6.6 Other `ZigBeeDevice` methods

| Method | Description |
| --- | --- |
| `getClusterEndpoint(cluster)` | First endpoint id that has this cluster as **input cluster**, or `null`. Output clusters are not discoverable this way. |
| `parseAttributeReport(capabilityId, cluster, payload)` | Runs the configured `reportParser` on `payload`, updates the capability value, returns the parsed value or `null`. |
| `getClusterCapabilityValue(capabilityId, cluster)` | `readAttributes([get])` on the configured endpoint, then parses and stores the value. |
| `setClusterCapabilityValue(capabilityId, cluster, value, opts = {})` | Runs `setParser`, then executes the `set` command. Returns `null` if the parser returned `null`. |
| `printNode()` | Logs the node token, `Receive when idle` and every endpoint + cluster name of the node. |
| `getSwBuildId({ endpointId = 1, skipCache = false } = {})` | Async. Resolution order when `skipCache === false`: (1) the `zw_sb_build_id` device setting if it is a string — note the `zw_` prefix, it really is the Z-Wave-named system setting and it wins over the cache; (2) the store key `__swBuildId`; (3) a `readAttributes(['swBuildId'])` on the `basic` cluster. The result is always written back to `__swBuildId`. Throws if the attribute is missing or not a string. |
| `scheduleForNextEndDeviceAnnounce(method)` | Returns a promise that runs `method()` once, on the node's next `endDeviceAnnounce`. Used internally for the retry paths. |
| `updateEnergyConfiguration()` | Applies `energyMap` (see §6.7). Called automatically during `onInit`. No-op on Homey firmware without `getEnergy`. |
| `isSubDevice()` | `true` when `this.getData().subDeviceId` is a string. |
| `triggerFlow({ id, tokens = {}, state = {} })` | Async. Triggers a device Flow trigger card via `this.homey.flow.getDeviceTriggerCard(id)`. Throws `expected_flow_id_string` / `failed_to_get_device_trigger_card`. |
| `enableDebug()` / `disableDebug()` / `debug(...args)` | Per-device debug logging (prefixed `[dbg]`), off by default. |
| `registerReportListener()` | Throws. Use a `BoundCluster`. |
| `registerAttrReportListener()` | Throws. Use `configureAttributeReporting`. |

### 6.7 `energyMap` — per-`productId` energy objects

```javascript
class ZigBeeBulb extends ZigBeeDevice {

  get energyMap() {
    return {
      'TRADFRI bulb E14 W op/ch 400lm': { approximation: { usageOff: 0, usageOn: 10 } },
      'TRADFRI bulb E27 RGB 1000lm': { approximation: { usageOff: 0, usageOn: 18 } },
    };
  }

}
```

Keyed by the device setting `zb_product_id`. Applied automatically during `onInit` via
`updateEnergyConfiguration()`, which calls `setEnergy({ ...this.getEnergy(), ...energyMap[id] })`.
The spread is **shallow**: a nested object such as `approximation` is replaced wholesale, so provide
all relevant energy settings for that key — treat it as fully overriding the manifest's `energy`
object. No-op when the setting is absent, when no key matches, or on firmware where
`this.getEnergy` does not exist.

### 6.8 `Util` helpers (`require('homey-zigbeedriver').Util`)

The complete export surface of `lib/util` (18 members):

| Function | Description |
| --- | --- |
| `calculateLevelControlTransitionTime(opts = {})` | `opts.duration` (ms) → tenths of a second, clamped 0–65534. Without a numeric `duration` returns `0xFFFF` (use the device's `onOffTransitionTime`). |
| `calculateColorControlTransitionTime(opts = {})` | `opts.duration` (ms) → tenths of a second, clamped 0–65535. Without a numeric `duration` returns `0` (instant). |
| `calculateZigBeeDimDuration(opts, settings)` | **Deprecated** since v1.0.0 — ignores `settings` and delegates to `calculateLevelControlTransitionTime`. |
| `mapValueRange(origStart, origEnd, newStart, newEnd, value)` | Linear range mapping. |
| `limitValue(value, min, max)` | Clamp. |
| `convertHSVToCIE({ hue, saturation, value })` | → `{ x, y, Y }`. |
| `convertCIEToHSV({ x, y, Y })` | → `{ hue, saturation, value }`. |
| `mapTemperatureToHueSaturation(temperature)` | → `{ hue, saturation, value }`. |
| `wait(ms)` | Promise-based sleep. |
| `debounce(fn, interval, immediate = false)` / `throttle(fn, interval)` | Plain JS helpers. |
| `wrapAsyncWithRetry(method, times = 1, interval = 0)` | Retry wrapper. `method` must be a zero-arg function returning a promise; `interval` may be a number (ms) or `retryCount => ms`. Throws `expected_function` / `expected_times_number` / `expected_interval_number_or_function`. |
| `assertClusterSpecification(cluster)` | Throws unless `cluster` is a `{ NAME, ID }` object — this is what rejects `registerCapability('onoff', 'onOff')`. |
| `assertCapabilityId(capabilityId, hasCapability)` | Throws when the id is not a string or the device lacks the capability. |
| `assertZCLNode(zclNode, endpointId, cluster)` | Throws when the `ZCLNode`, endpoint or cluster is missing. |
| `recursiveDeepCopy(object)` | Deep copy used to clone system capability configurations. |
| `__(language, localeKey)` | Internal locale lookup for the library's own error strings. |
| `debugZigbeeClusters(flag, namespaces)` | **Deprecated** since 1.5.0 — logs a warning and forwards to `debug` from `zigbee-clusters`. |

---

## 7. `ZigBeeLightDevice`

For bulbs and spots. Handles `onoff`, `dim`, `light_mode`, `light_hue`, `light_saturation` and
`light_temperature` out of the box using `levelControl` (`moveToLevelWithOnOff`) and `colorControl`
(`moveToHueAndSaturation`, `moveToHue`, `moveToColor`, `moveToColorTemperature`).

```javascript
'use strict';

const { ZigBeeLightDevice } = require('homey-zigbeedriver');

class ZigBeeBulb extends ZigBeeLightDevice {

  async onNodeInit({ zclNode, node }) {
    await super.onNodeInit({ zclNode, node });
    // Custom logic here
  }

}

module.exports = ZigBeeBulb;
```

`onNodeInit({ zclNode, supportsHueAndSaturation, supportsColorTemperature })` — the two booleans are
optional overrides for devices whose `colorCapabilities` attribute does not advertise
`hueAndSaturation` / `colorTemperature` although the commands do work.

| Member | Description |
| --- | --- |
| `supportsHueAndSaturation` (getter) | Override value, else store value `colorCapabilities.hueAndSaturation`. |
| `supportsColorTemperature` (getter) | Override value, else store value `colorCapabilities.colorTemperature`. |
| `colorTemperatureRange` (getter) | `{ min: store colorTempMin, max: store colorTempMax }`. |
| `levelControlCluster` / `onOffCluster` / `colorControlCluster` (getters) | Resolve the cluster on the endpoint found by `getClusterEndpoint`; throw `missing_level_control_cluster` / `missing_on_off_cluster` / `missing_color_control_cluster`. |
| `readColorControlAttributes()` | Reads `colorCapabilities`, `colorTemperatureMireds`, `colorTempPhysicalMinMireds`, `colorTempPhysicalMaxMireds`, `currentHue`, `currentSaturation`, `colorMode`, `currentX`, `currentY` and stores `colorCapabilities` (`hueAndSaturation`, `enhancedHue`, `colorLoop`, `xy`, `colorTemperature`), `colorTempMin`, `colorTempMax`, `colorClusterConfigured`. Called from `onNodeInit` **only** when the store value `colorClusterConfigured` is falsy and the device has at least one color capability; it swallows its own errors. |
| `registerColorCapabilities({ zclNode })` | Registers whichever of `light_hue`, `light_saturation`, `light_temperature`, `light_mode` the device has as one debounced `registerMultipleCapabilities` group. |
| `changeOnOff(onoff)` | `setOn`/`setOff`. On `false` sets `dim` to `0`; on `true` waits 1 s, reads `currentLevel` and sets `dim` to `max(0.01, currentLevel / 254)`. |
| `changeDimLevel(dim, opts)` | `moveToLevelWithOnOff` with `level = round(dim × 254)`, then syncs `onoff` (`false` when `dim === 0`, `true` when it was `false` and `dim > 0`). |
| `changeColorTemperature(temperature, opts)` | Sets `light_mode` to `'temperature'`, then `moveToColorTemperature` mapped over `colorTemperatureRange`. Without `colorTemperature` support it logs a warning and falls back to `mapTemperatureToHueSaturation` + `moveToColor`. |
| `changeColor({ hue, saturation, value }, opts)` | `moveToHueAndSaturation` (×254) when `supportsHueAndSaturation`, else HSV→CIE + `moveToColor`. Missing `hue`/`saturation` fall back to the current capability values. |
| `onEndDeviceAnnounce()` | Reads `currentLevel` → updates `dim` + `onoff`; if `levelControl` is absent, reads `onOff` instead. Then reads `currentSaturation`, `currentHue`, `colorMode`, `colorTemperatureMireds` and updates `light_hue`/`light_saturation`/`light_mode`/`light_temperature`. Every step is skipped when the cluster is missing. |

Notes:
- `ZigBeeXYLightDevice` was **removed** — `ZigBeeLightDevice` auto-detects hue/saturation vs XY.
- Color/temperature commands that fail with `FAILURE` are rethrown as
  "Make sure the device is turned on before changing its color/color temperature."
- If a device does not support `colorTemperature`, do **not** add the `light_temperature`
  capability; the legacy HSV fake-temperature path yields skewed colors.

---

## 8. `zigbee-clusters` — ZCL layer

Exports: `Cluster`, `BoundCluster`, `ZCLNode`, `zclTypes`, `zclFrames`, `ZCLDataTypes`,
`ZCLDataType`, `ZCLStruct`, `ZCLError`, `CLUSTER`, `debug`, `ZIGBEE_PROFILE_ID`,
`ZIGBEE_DEVICE_ID`, `IAS_ZONE_TYPE`, plus all 47 cluster classes:

`BasicCluster`, `PowerConfigurationCluster`, `DeviceTemperatureCluster`, `IdentifyCluster`,
`GroupsCluster`, `ScenesCluster`, `OnOffCluster`, `OnOffSwitchCluster`, `LevelControlCluster`,
`AlarmsCluster`, `TimeCluster`, `AnalogInputCluster`, `AnalogOutputCluster`, `AnalogValueCluster`,
`BinaryInputCluster`, `BinaryOutputCluster`, `BinaryValueCluster`, `MultistateInputCluster`,
`MultistateOutputCluster`, `MultistateValueCluster`, `OTACluster`, `PowerProfileCluster`,
`PollControlCluster`, `ShadeConfigurationCluster`, `DoorLockCluster`, `WindowCoveringCluster`,
`ThermostatCluster`, `ThermostatUserInterfaceConfigurationCluster`,
`PumpConfigurationAndControlCluster`, `FanControlCluster`, `DehumidificationControlCluster`,
`ColorControlCluster`, `BallastConfigurationCluster`, `IlluminanceMeasurementCluster`,
`IlluminanceLevelSensingCluster`, `TemperatureMeasurementCluster`, `PressureMeasurementCluster`,
`FlowMeasurementCluster`, `RelativeHumidityCluster`, `OccupancySensingCluster`, `IASZoneCluster`,
`IASACECluster`, `IASWDCluster`, `MeteringCluster`, `ElectricalMeasurementCluster`,
`DiagnosticsCluster`, `TouchLinkCluster`.

Note the asymmetry: there are **47 cluster classes but only 46 `CLUSTER` constants** —
`dehumidificationControl` (515) is registered and exported as a class, but has **no**
`CLUSTER.DEHUMIDIFICATION_CONTROL` entry. Reach it via `Cluster.getCluster(515)` or the exported
class; you cannot pass it to `registerCapability` as a `CLUSTER.*` constant.

### 8.1 Access paths

```javascript
zclNode.endpoints[1].clusters.onOff                       // by property name
zclNode.endpoints[1].clusters[CLUSTER.ON_OFF.NAME]        // equivalent, safer
zclNode.endpoints[1].bindings[CLUSTER.IAS_ZONE.NAME]      // registered BoundCluster instances
```

`Endpoint` holds `clusters` (client-side, instantiated from the endpoint descriptor's
`inputClusters`, i.e. the manifest `clusters` list) and `bindings` (server-side). Only
endpoints/clusters declared in the manifest exist on the `ZCLNode`, and a listed id that
`zigbee-clusters` does not implement is silently skipped — so a missing cluster surfaces as
`undefined`, never as an error.

### 8.2 Sending commands

```javascript
await zclNode.endpoints[1].clusters.onOff.toggle();

await zclNode.endpoints[1].clusters.levelControl.moveToLevel(
  { level: 100, transitionTime: 2000 },
  {
    // Optional. Set false only for devices that violate the spec and never
    // send a default response. `false` makes the call fire-and-forget.
    waitForResponse: true,
    // Optional. Default response timeout is 10000 ms; starts after the frame
    // was sent and a low-level ack was received.
    timeout: 5000,
    // Optional. Sets the ZCL header's "Disable Default Response" flag, so the
    // node only sends a default response on error. Workaround for nodes that
    // send both a default response and a real response (violates ZCL §2.5.12.2).
    // The real response is still awaited.
    disableDefaultResponse: false,
  },
);
```

The three option keys are `waitForResponse`, `timeout` and `disableDefaultResponse`; anything else
is ignored. A command whose own `frameControl` already contains `disableDefaultResponse` never waits
for a response. When the node answers with a default response whose status is not `SUCCESS`, the
promise rejects with that status string as the error message (e.g. `FAILURE`, `UNSUPPORTED_ATTRIBUTE`).

### 8.3 Cluster instance methods

| Method | Signature | Notes |
| --- | --- | --- |
| `readAttributes(attributes, opts?)` | `Array<string \| number>` → `Promise<{ [name]: value }>` | **Must** be an array (since `zigbee-clusters@2.0.0`) — a non-array throws immediately. Numeric ids allowed (integers 0–0xFFFF); an unknown *string* throws `TypeError: <x> is not a valid attribute of <cluster>`. Empty array reads all known attributes (including the ZCL globals). `opts.timeout` in ms. Do not mix regular and manufacturer-specific attributes. **Only records with status `SUCCESS` end up in the result object** — an attribute the device does not support is simply absent, not an error. |
| `writeAttributes(attributes = {}, opts?)` | `{ name: value }` | Throws `TypeError` on unknown attribute names. |
| `configureReporting(attributes = {}, opts?)` | `{ attrName: { minInterval, maxInterval, minChange } }` | Defaults `minInterval: 0`, `maxInterval: 0xffff`, `minChange: 1`. `minChange` is stripped for non-analog types. Throws with the ZCL status when a report is not `SUCCESS`. |
| `readReportingConfiguration(attributes = [], opts?)` | ids or names | Returns `[{ status, direction, attributeId, attributeDataType, minInterval, maxInterval, minChange, timeoutPeriod }]` for the `'reported'` direction. |
| `discoverAttributes(opts?)` | — | Array of attribute names (or numeric ids when unknown). |
| `discoverAttributesExtended(opts?)` | — | Array of objects with attribute names as keys. |
| `discoverCommandsGenerated({ startValue = 0, maxResults = 250 }, opts?)` | — | Command ids the remote cluster generates. |
| `discoverCommandsReceived({ startValue = 0, maxResults = 255 }, opts?)` | — | Command ids the remote cluster receives. |

Attribute reports arrive as `attr.<attributeName>` events on the cluster instance:

```javascript
zclNode.endpoints[1].clusters.colorControl
  .on('attr.currentSaturation', currentSaturation => { /* … */ });
```

### 8.4 `CLUSTER` constants (`zigbee-clusters@3.5.0`)

`CLUSTER.<KEY>` → `{ NAME, ID, ATTRIBUTES, COMMANDS }`. The **ID** column is what goes into
`zigbee.endpoints.<id>.clusters` / `bindings` in the manifest. All 46 constants, sorted by id:

| Constant | `NAME` | ID (dec) | ID (hex) |
| --- | --- | --- | --- |
| `CLUSTER.BASIC` | `basic` | 0 | 0x0000 |
| `CLUSTER.POWER_CONFIGURATION` | `powerConfiguration` | 1 | 0x0001 |
| `CLUSTER.DEVICE_TEMPERATURE` | `deviceTemperature` | 2 | 0x0002 |
| `CLUSTER.IDENTIFY` | `identify` | 3 | 0x0003 |
| `CLUSTER.GROUPS` | `groups` | 4 | 0x0004 |
| `CLUSTER.SCENES` | `scenes` | 5 | 0x0005 |
| `CLUSTER.ON_OFF` | `onOff` | 6 | 0x0006 |
| `CLUSTER.ON_OFF_SWITCH` | `onOffSwitch` | 7 | 0x0007 |
| `CLUSTER.LEVEL_CONTROL` | `levelControl` | 8 | 0x0008 |
| `CLUSTER.ALARMS` | `alarms` | 9 | 0x0009 |
| `CLUSTER.TIME` | `time` | 10 | 0x000A |
| `CLUSTER.ANALOG_INPUT` | `analogInput` | 12 | 0x000C |
| `CLUSTER.ANALOG_OUTPUT` | `analogOutput` | 13 | 0x000D |
| `CLUSTER.ANALOG_VALUE` | `analogValue` | 14 | 0x000E |
| `CLUSTER.BINARY_INPUT` | `binaryInput` | 15 | 0x000F |
| `CLUSTER.BINARY_OUTPUT` | `binaryOutput` | 16 | 0x0010 |
| `CLUSTER.BINARY_VALUE` | `binaryValue` | 17 | 0x0011 |
| `CLUSTER.MULTI_STATE_INPUT` | `multistateInput` | 18 | 0x0012 |
| `CLUSTER.MULTI_STATE_OUTPUT` | `multistateOutput` | 19 | 0x0013 |
| `CLUSTER.MULTI_STATE_VALUE` | `multistateValue` | 20 | 0x0014 |
| `CLUSTER.OTA` | `ota` | 25 | 0x0019 |
| `CLUSTER.POWER_PROFILE` | `powerProfile` | 26 | 0x001A |
| `CLUSTER.POLL_CONTROL` | `pollControl` | 32 | 0x0020 |
| `CLUSTER.SHADE_CONFIGURATION` | `shadeConfiguration` | 256 | 0x0100 |
| `CLUSTER.DOOR_LOCK` | `doorLock` | 257 | 0x0101 |
| `CLUSTER.WINDOW_COVERING` | `windowCovering` | 258 | 0x0102 |
| `CLUSTER.PUMP_CONFIGURATION_AND_CONTROL` | `pumpConfigurationAndControl` | 512 | 0x0200 |
| `CLUSTER.THERMOSTAT` | `thermostat` | 513 | 0x0201 |
| `CLUSTER.FAN_CONTROL` | `fanControl` | 514 | 0x0202 |
| `CLUSTER.THERMOSTAT_UI_CONFIGURATION` | `thermostatUserInterfaceConfiguration` | 516 | 0x0204 |
| `CLUSTER.COLOR_CONTROL` | `colorControl` | 768 | 0x0300 |
| `CLUSTER.BALLAST_CONFIGURATION` | `ballastConfiguration` | 769 | 0x0301 |
| `CLUSTER.ILLUMINANCE_MEASUREMENT` | `illuminanceMeasurement` | 1024 | 0x0400 |
| `CLUSTER.ILLUMINANCE_LEVEL_SENSING` | `illuminanceLevelSensing` | 1025 | 0x0401 |
| `CLUSTER.TEMPERATURE_MEASUREMENT` | `temperatureMeasurement` | 1026 | 0x0402 |
| `CLUSTER.PRESSURE_MEASUREMENT` | `pressureMeasurement` | 1027 | 0x0403 |
| `CLUSTER.FLOW_MEASUREMENT` | `flowMeasurement` | 1028 | 0x0404 |
| `CLUSTER.RELATIVE_HUMIDITY_MEASUREMENT` | `relativeHumidity` | 1029 | 0x0405 |
| `CLUSTER.OCCUPANCY_SENSING` | `occupancySensing` | 1030 | 0x0406 |
| `CLUSTER.IAS_ZONE` | `iasZone` | 1280 | 0x0500 |
| `CLUSTER.IAS_ACE` | `iasACE` | 1281 | 0x0501 |
| `CLUSTER.IAS_WD` | `iasWD` | 1282 | 0x0502 |
| `CLUSTER.METERING` | `metering` | 1794 | 0x0702 |
| `CLUSTER.ELECTRICAL_MEASUREMENT` | `electricalMeasurement` | 2820 | 0x0B04 |
| `CLUSTER.DIAGNOSTICS` | `diagnostics` | 2821 | 0x0B05 |
| `CLUSTER.TOUCHLINK` | `touchlink` | 4096 | 0x1000 |

### 8.5 Command signatures (most used clusters)

| Cluster | Command | Arguments |
| --- | --- | --- |
| `onOff` | `setOff` (0), `setOn` (1), `toggle` (2), `onWithRecallGlobalScene` (65) | none |
| `onOff` | `offWithEffect` (64) | `effectIdentifier`, `effectVariant` |
| `onOff` | `onWithTimedOff` (66) | `onOffControl`, `onTime`, `offWaitTime` |
| `levelControl` | `moveToLevel` (0), `moveToLevelWithOnOff` (4) | `level`, `transitionTime` |
| `levelControl` | `move` (1), `moveWithOnOff` (5) | `moveMode`, `rate` |
| `levelControl` | `step` (2), `stepWithOnOff` (6) | `mode`, `stepSize`, `transitionTime` |
| `levelControl` | `stop` (3), `stopWithOnOff` (7) | none |
| `colorControl` | `moveToHue` (0) | `hue`, `direction`, `transitionTime` |
| `colorControl` | `moveToSaturation` (3) | `saturation`, `transitionTime` |
| `colorControl` | `moveToHueAndSaturation` (6) | `hue`, `saturation`, `transitionTime` |
| `colorControl` | `moveToColor` (7) | `colorX`, `colorY`, `transitionTime` |
| `colorControl` | `moveToColorTemperature` (10) | `colorTemperature`, `transitionTime` |
| `colorControl` | `colorLoopSet` (68) | `updateFlags`, `action`, `direction`, `time`, `startHue` |
| `windowCovering` | `upOpen` (0), `downClose` (1), `stop` (2) | none |
| `windowCovering` | `goToLiftValue` (4) | `liftValue` |
| `windowCovering` | `goToLiftPercentage` (5) | `percentageLiftValue` |
| `windowCovering` | `goToTiltValue` (7) | `tiltValue` |
| `windowCovering` | `goToTiltPercentage` (8) | `percentageTiltValue` |
| `identify` | `identify` (0) | `identifyTime` |
| `identify` | `identifyQuery` (1) | none (has response) |
| `identify` | `triggerEffect` (64) | `effectIdentifier`, `effectVariant` |
| `groups` | `addGroup` (0), `addGroupIfIdentify` (5) | `groupId`, `groupName` |
| `groups` | `viewGroup` (1), `removeGroup` (3) | `groupId` |
| `groups` | `getGroupMembership` (2) | `groupIds` |
| `groups` | `removeAllGroups` (4) | none |
| `iasZone` | `zoneStatusChangeNotification` (0, server→client) | `zoneStatus`, `extendedStatus`, `zoneId`, `delay` |
| `iasZone` | `zoneEnrollRequest` (1, server→client) | `zoneType`, `manufacturerCode` |
| `iasZone` | `zoneEnrollResponse` (0, client→server) | `enrollResponseCode`, `zoneId` |
| `iasZone` | `initiateNormalOperationMode` (1, client→server) | none |
| `thermostat` | `setSetpoint` (0) | `mode`, `amount` |
| `pollControl` | `fastPollStop` (1) | none |
| `pollControl` | `setLongPollInterval` (2) / `setShortPollInterval` (3) | `newLongPollInterval` / `newShortPollInterval` |
| `alarms` | `resetAllAlarms` (1), `getAlarm` (2), `resetAlarmLog` (3) | none |
| `basic` | `factoryReset` (0) | none |
| `touchlink` | `getGroups` (65) | `startIdx` (has response) |

### 8.6 Constants

```javascript
const { ZIGBEE_PROFILE_ID, ZIGBEE_DEVICE_ID, IAS_ZONE_TYPE } = require('zigbee-clusters');
```

`ZIGBEE_PROFILE_ID`: `INDUSTRIAL_PLANT_MONITORING` 257, `HOME_AUTOMATION` 260,
`COMMERCIAL_BUILDING_AUTOMATION` 261, `TELECOM_APPLICATIONS` 263,
`PERSONAL_HOME_AND_HOSPITAL_CARE` 264, `ADVANCED_METERING_INITIATIVE` 265.

`IAS_ZONE_TYPE`: `STANDARD_CIE` 0, `MOTION_SENSOR` 13, `CONTACT_SWITCH` 21, `FIRE_SENSOR` 40,
`WATER_SENSOR` 42, `CARBON_MONOXIDE_SENSOR` 43, `PERSONAL_EMERGENCY_DEVICE` 44,
`VIBRATION_MOVEMENT_SENSOR` 45, `REMOTE_CONTROL` 271, `KEY_FOB` 277, `KEYPAD` 541,
`STANDARD_WARNING_DEVICE` 549, `GLASS_BREAK_SENSOR` 550, `SECURITY_REPEATER` 553,
`INVALID_ZONE_TYPE` 65535.

`ZIGBEE_DEVICE_ID` is nested one level deep (`ZIGBEE_DEVICE_ID.<GROUP>.<NAME>`), complete:

| Group | Members (dec / hex) |
| --- | --- |
| `GENERIC` | `ON_OFF_SWITCH` 0/0x0000, `LEVEL_CONTROL_SWITCH` 1/0x0001, `ON_OFF_OUTPUT` 2/0x0002, `LEVEL_CONTROLLABLE_OUTPUT` 3/0x0003, `SCENE_SELECTOR` 4/0x0004, `CONFIGURATION_TOOL` 5/0x0005, `REMOTE_CONTROL` 6/0x0006, `COMBINED_INTERFACE` 7/0x0007, `RANGE_EXTENDER` 8/0x0008, `MAINS_POWER_OUTLET` 9/0x0009, `DOOR_LOCK` 10/0x000A, `DOOR_LOCK_CONTROLLER` 11/0x000B, `SIMPLE_SENSOR` 12/0x000C, `CONSUMPTION_AWARENESS_DEVICE` 13/0x000D, `HOME_GATEWAY` 80/0x0050, `SMART_PLUG` 81/0x0051, `WHITE_GOODS` 82/0x0052, `METER_INTERFACE` 83/0x0053 |
| `LIGHTING` | `ON_OFF_LIGHT` 256/0x0100, `DIMMABLE_LIGHT` 257/0x0101, `COLOR_DIMMABLE_LIGHT` 258/0x0102, `ON_OFF_LIGHT_SWITCH` 259/0x0103, `DIMMER_SWITCH` 260/0x0104, `COLOR_DIMMER_SWITCH` 261/0x0105, `LIGHT_SENSOR` 262/0x0106, `OCCUPANCY_SENSOR` 263/0x0107 |
| `CLOSURES` | `SHADE` 512/0x0200, `SHADE_CONTROLLER` 513/0x0201, `WINDOW_COVERING_DEVICE` 514/0x0202, `WINDOW_COVERING_CONTROLLER` 515/0x0203 |
| `HVAC` | `HEATING_COOLING_UNIT` 768/0x0300, `THERMOSTAT` 769/0x0301, `TEMPERATURE_SENSOR` 770/0x0302, `PUMP` 771/0x0303, `PUMP_CONTROLLER` 772/0x0304, `PRESSURE_SENSOR` 773/0x0305, `FLOW_SENSOR` 774/0x0306 |
| `INTRUDER_ALARM_SYSTEMS` | `IAS_CONTROL_INDICATING_EQUIPMENT` 1024/0x0400, `IAS_ANCILLARY_CONTROL_EQUIPMENT` 1025/0x0401, `IAS_ZONE` 1026/0x0402, `IAS_WARNING_DEVICE` 1027/0x0403 |

These constants are informational only — SDK v3 no longer uses `profileId`/`deviceId` to match a
driver (see §13).

---

## 9. Bindings, bound clusters and custom clusters

### 9.1 Bound clusters (receiving commands from a node)

Needed for remotes, buttons, IAS sensors, and any node that *sends* to Homey.

```javascript
// /lib/LevelControlBoundCluster.js
'use strict';

const { BoundCluster } = require('zigbee-clusters');

class LevelControlBoundCluster extends BoundCluster {

  constructor({ onMove }) {
    super();
    this._onMove = onMove;
  }

  // Method name === the `move` command in zigbee-clusters/lib/clusters/levelControl.js;
  // the payload equals LevelControlCluster.COMMANDS.move.args
  move(payload) {
    this._onMove(payload);
  }

}

module.exports = LevelControlBoundCluster;
```

```javascript
// /drivers/<driver_id>/device.js
'use strict';

const { ZigBeeDevice } = require('homey-zigbeedriver');
const { CLUSTER } = require('zigbee-clusters');

const LevelControlBoundCluster = require('../../lib/LevelControlBoundCluster');

class MyRemote extends ZigBeeDevice {

  async onNodeInit({ zclNode }) {
    zclNode.endpoints[1].bind(CLUSTER.LEVEL_CONTROL.NAME, new LevelControlBoundCluster({
      onMove: payload => {
        this.log('move', payload);
      },
    }));
  }

}

module.exports = MyRemote;
```

- Add the cluster id to `bindings` in the manifest so the bind request is made during pairing.
- `Endpoint#bind(clusterName, boundClusterInstance)` registers the implementation. It throws
  `TypeError` when the cluster name is unknown, or when the second argument is not an instance of
  `BoundCluster`. `Endpoint#unbind(clusterName)` replaces it with a plain cluster instance.
- Registered instances live on `zclNode.endpoints[x].bindings[clusterName]`. An incoming
  client→server frame for a cluster with no binding is answered with an error default response
  (`binding_unavailable`).
- A `BoundCluster` also answers `readAttributes` from the node by exposing `this[attributeName]`;
  attributes it does not define are answered with status `FAILURE`. `writeAttributes` only succeeds
  for properties that have a **setter** (`not_settable` otherwise).
- `discoverCommandsReceived` reports exactly the command names you implemented as methods.

### 9.2 Custom clusters (manufacturer-specific)

Extend an existing cluster class and re-register it before any `ZCLNode` is created.

```javascript
// /lib/IkeaSpecificSceneCluster.js
'use strict';

const { ScenesCluster, ZCLDataTypes } = require('zigbee-clusters');

class IkeaSpecificSceneCluster extends ScenesCluster {

  static get COMMANDS() {
    return {
      ...super.COMMANDS,
      ikeaSceneMove: {
        id: 0x08,
        manufacturerId: 0x117c,
        args: {
          mode: ZCLDataTypes.enum8({ up: 0, down: 1 }),
          transitionTime: ZCLDataTypes.uint16,
        },
      },
    };
  }

  static get ATTRIBUTES() {
    return {
      manufAttribute: { id: 0, type: ZCLDataTypes.uint8, manufacturerId: 0x1234 },
    };
  }

}

module.exports = IkeaSpecificSceneCluster;
```

```javascript
'use strict';

const { Cluster } = require('zigbee-clusters');

const IkeaSpecificSceneCluster = require('../../lib/IkeaSpecificSceneCluster');

// Must be added before it becomes available on any ZCLNode instance
Cluster.addCluster(IkeaSpecificSceneCluster);

// …then
await zclNode.endpoints[1].clusters.scenes.ikeaSceneMove({ mode: 0, transitionTime: 10 });
```

**Never mix manufacturer-specific and regular attributes in one `readAttributes` /
`writeAttributes` / `configureReporting` call.** The same technique applies to `BoundCluster`s when
a node sends manufacturer-specific commands to Homey.

### 9.3 Implementing a whole new cluster

```javascript
'use strict';

const { Cluster, ZCLDataTypes } = require('zigbee-clusters');

const ATTRIBUTES = {
  onOff: { id: 0, type: ZCLDataTypes.bool },
};

const COMMANDS = {
  toggle: { id: 2 },
  onWithTimedOff: {
    id: 66,
    // Optional: two commands may share an id if both declare a direction.
    // direction: Cluster.DIRECTION_SERVER_TO_CLIENT
    args: {
      onOffControl: ZCLDataTypes.uint8,
      onTime: ZCLDataTypes.uint16,
      offWaitTime: ZCLDataTypes.uint16,
    },
  },
};

class OnOffCluster extends Cluster {

  static get ID() { return 6; }
  static get NAME() { return 'onOff'; }
  static get ATTRIBUTES() { return ATTRIBUTES; }
  static get COMMANDS() { return COMMANDS; }

}

Cluster.addCluster(OnOffCluster);

module.exports = OnOffCluster;
```

`Cluster` statics: `addCluster(clusterClass)`, `removeCluster(clusterIdOrName)`,
`getCluster(clusterIdOrName)`, `DIRECTION_SERVER_TO_CLIENT` / `DIRECTION_CLIENT_TO_SERVER`.
A command may declare `response: { id, args }` (the response id defaults to the command id), plus
`manufacturerId`, `frameControl`, `global` and `encodeMissingFieldsBehavior`.
`addCluster` also merges the ZCL global attributes/commands into `Cluster.attributes` /
`Cluster.commands` — that is why `readAttributes([])` can read more than the cluster's own
`ATTRIBUTES`.

`ZCLDataTypes` keys: `noData`, `data8`, `data16`, `data24`, `data32`, `data40`, `data48`, `data56`,
`data64`, `bool`, `map8`, `map16`, `map24`, `map32`, `map40`, `map48`, `map56`, `map64`, `uint8`,
`uint16`, `uint24`, `uint32`, `uint40`, `uint48`, `int8`, `int16`, `int24`, `int32`, `int40`,
`int48`, `enum8`, `enum16`, `enum32`, `single`, `double`, `octstr`, `string`, `EUI48`, `EUI64`,
`key128`, `uint4`, `enum4`, `map4`, `buffer`, `buffer8`, `buffer16`, `Array0`, `Array8`,
`FixedString`, `enum8Status`. Composite arguments use `ZCLStruct`.

---

## 10. Raw Zigbee API (`this.homey.zigbee`)

Only when `homey-zigbeedriver` and `zigbee-clusters` genuinely cannot do the job.

**ManagerZigBee** (`this.homey.zigbee`):

| Method | Signature |
| --- | --- |
| `getNode(device)` | `async (Device) => Promise<ZigBeeNode>` |

**ZigBeeNode** (never constructed directly):

| Member | Type | Description |
| --- | --- | --- |
| `ieeeAddress` | string (readonly) | The node's IEEE address. Available since Homey **v12.3.0**. |
| `manufacturerName` | string (readonly) | The node's manufacturer name. |
| `productId` | string (readonly) | The node's product id. |
| `handleFrame(endpointId, clusterId, frame, meta)` | `async (number, number, Buffer, object) => Promise<void>` | Called when a frame is received. **Must be overridden — it throws otherwise.** |
| `sendFrame(endpointId, clusterId, frame)` | `async (number, number, Buffer) => Promise<void>` | Sends a raw ZCL frame `Buffer`. |
| `receiveWhenIdle` | boolean | **Not in the published `ZigBeeNode` API reference**, but real and relied on: `homey-zigbeedriver` reads `this.node.receiveWhenIdle` to skip `getOnStart` for sleepy nodes, and the docs say a SED can be identified "programmatically as a property of `ZigBeeNode`". |
| `'endDeviceAnnounce'` event | — | Also undocumented in the API reference; `homey-zigbeedriver` does `this.node.on('endDeviceAnnounce', …)` to drive `onEndDeviceAnnounce()`, `getOnOnline` and its retry paths. `ZigBeeNode` is an `EventEmitter` (`removeAllListeners()` is called in `onDeleted()`). |

The published `ManagerZigBee` / `ZigBeeNode` reference documents **only** `getNode`, `ieeeAddress`,
`manufacturerName`, `productId`, `handleFrame` and `sendFrame` — everything else above is inferred
from `homey-zigbeedriver`'s use of it.

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    const node = await this.homey.zigbee.getNode(this);

    node.handleFrame = (endpointId, clusterId, frame, meta) => {
      if (endpointId === 1 && clusterId === 6) {
        // Frame from endpoint 1, cluster 'onOff'
      }
    };

    // Turn on: frame control, transaction sequence number, command id
    await node.sendFrame(1, 6, Buffer.from([1, 0, 1])).catch(this.error);
    // Turn off
    await node.sendFrame(1, 6, Buffer.from([1, 1, 0])).catch(this.error);
  }

}

module.exports = MyDevice;
```

Using `zigbee-clusters` without `homey-zigbeedriver`:

```javascript
'use strict';

const Homey = require('homey');
const { ZCLNode, CLUSTER } = require('zigbee-clusters');

class MyDevice extends Homey.Device {

  async onInit() {
    const node = await this.homey.zigbee.getNode(this);
    const zclNode = new ZCLNode(node);
    await zclNode.endpoints[1].clusters[CLUSTER.ON_OFF.NAME].toggle().catch(this.error);
  }

}

module.exports = MyDevice;
```

`new ZCLNode(node)` overwrites `node.handleFrame` and proxies `sendFrame`.

---

## 11. Debugging

```javascript
'use strict';

const { ZigBeeDevice } = require('homey-zigbeedriver');
const { debug } = require('zigbee-clusters');

// Log all relevant Zigbee communication. Do NOT ship this enabled.
debug(true);

class MyDevice extends ZigBeeDevice {}

module.exports = MyDevice;
```

`debug(flag = true, namespaces = '*')` — `namespaces` follows the `debug` npm module syntax
(e.g. `'zigbee-clusters:bound-cluster:*'`). Example output:

```
2020-08-07T13:04:30.933Z zigbee-clusters:cluster ep: 1, cl: illuminanceMeasurement (1024) received frame reportAttributes illuminanceMeasurement.reportAttributes {
  attributes: <Buffer 00 00 21 7e 00>
}
```

Also useful: `this.enableDebug()` + `this.printNode()` inside `onNodeInit` to dump the node's
endpoints, clusters and `Receive when idle` flag.

### Running the app

```bash
homey app run                # default: local Docker container attached to the selected Homey
homey app run --remote       # upload to the Homey and run there (slower rebuilds)
homey app run --clean        # wipe userdata/paired devices first — use when testing pairing
```

| Flag | Alias | Default | Description |
| --- | --- | --- | --- |
| `--remote` | `-r` | `false` | Run on the Homey instead of Docker. **Automatically enabled on Homey Pro (2016—2019)**, which cannot use Docker. |
| `--clean` | `-c` | `false` | Delete all userdata, paired devices and settings before running. |
| `--skip-build` | `-s` | `false` | Skip the build step. |
| `--link-modules` | `-l` | `""` | Comma-separated local Node.js modules to link (Docker mode only) — handy for hacking on a local `zigbee-clusters` checkout. |
| `--network` | `-n` | `bridge` | Docker network mode; must match a name from `docker network ls` (Docker mode only). |
| `--docker-socket-path` | — | — | Path to the Docker socket. |
| `--find-links` | — | — | Extra location to search for candidate Python package distributions (Python apps only). |

`Ctrl+C` uninstalls the app from Homey. Changing `zigbee.endpoints` does **not** require re-pairing:
the endpoint definition is currently dynamic and is updated on the device without a repair (the docs
warn this may change in the future).

---

## 12. Zigbee OTA firmware updates

Homey implements the Zigbee **Over-the-Air Upgrade** cluster; your app only supplies the firmware
files and metadata, Homey performs the transfer.

> Supported since Homey firmware **v13.2.0**, on Homey Pro (Early 2023, 2026, mini), Homey
> Self-Hosted Server and Homey Cloud. Users need Homey Mobile App **v9.10.0+** to start updates.

File: `/drivers/<driver_id>/driver.firmware.compose.json` (composed into the driver's
`firmwareUpdates` key in `app.json`). Firmware binaries live in
`/drivers/<driver_id>/assets/firmware/<name>`.

```json
{
  "wakeInstruction": {
    "en": "Hold the internal button for three seconds."
  },
  "updates": [
    {
      "changelog": {
        "en": "- Fixes issue X\n- Adds feature Y\n- Deprecates feature Z"
      },
      "device": {
        "manufacturerName": "Company XYZ",
        "productId": ["AwesomeSensor", "AwesomeSensor Rev B"]
      },
      "files": [
        {
          "fileVersion": 1234,
          "imageType": 1000,
          "manufacturerCode": 5678,
          "size": 262144,
          "name": "AwesomeSensor_v1.3.4.bin",
          "integrity": "sha256:dac89981aeb5352a8ddce9fbb5ab3ad5bff88d17e2f7937cc90947301ccfedd2"
        }
      ]
    }
  ]
}
```

### Top level

All **four** schema objects involved are `additionalProperties: false`, so an unknown key fails
validation: `zigbee-firmware-updates` (top level), `zigbee-firmware-update` (`updates[]`),
`zigbee-firmware-update-device` (`updates[].device`) and `zigbee-firmware-update-file`
(`updates[].files[]`). Contrast `zigbeeDevice` in §5, which is *not* sealed.

The driver-level key is `firmwareUpdates`, typed as
`oneOf: [zigbee-firmware-updates, zwave-firmware-updates]`. Both branches are sealed and both
require `updates`, so an object that mixes Zigbee tuning keys with Z-Wave ones (e.g.
`maxImageBlockSize` next to `minWaitTime`) matches **neither** branch and fails with a confusing
`oneOf` error rather than a pointed "unknown key" message.

| Key | Required | Type | Description |
| --- | --- | --- | --- |
| `updates` | yes | array (min 1) | All firmware updates for this driver's devices. |
| `wakeInstruction` | no | Translation Object | How the user wakes a Sleepy End Device to start the update. Not needed for mains devices. |
| `queryNextImageTimeout` | no | number | Protocol tuning (accepted by the manifest schema). |
| `minImageBlockPeriod` | no | number | Protocol tuning. |
| `maxImageBlockSize` | no | number | Protocol tuning. |
| `imageBlockRequestTimeout` | no | number | Protocol tuning. |
| `upgradeEndRequestTimeout` | no | number | Protocol tuning. |
| `upgradeEndDelay` | no | number | Protocol tuning. |
| `postUpgradeAnnounceTimeout` | no | number | Protocol tuning. |

### `updates[]`

| Key | Required | Type | Description |
| --- | --- | --- | --- |
| `changelog` | yes | Translation Object | Short description of the changes. |
| `device` | yes | object | `zigbee-firmware-update-device`: `{ manufacturerName, productId }` — both **required**, each `string \| string[]`, and the object is sealed (no other key allowed). Lets one driver ship updates for only a subset of its supported devices. |
| `files` | yes | array (min 1) | Firmware files in this update. |

### `updates[].files[]`

| Key | Required | Type | Description |
| --- | --- | --- | --- |
| `fileVersion` | yes | number | Firmware file version; higher = newer (per ZCL spec). |
| `imageType` | yes | number | Manufacturer-specific image type (per ZCL spec). |
| `manufacturerCode` | yes | number | Assigned manufacturer code (per ZCL spec). |
| `size` | yes | number | File size in bytes. |
| `name` | yes | string | File name; must exist at `/drivers/<driver_id>/assets/firmware/<name>`. |
| `integrity` | yes | string | `<hash_name>:<hex>`, schema pattern `^(blake2b512\|blake2s256\|sha256\|sha384\|sha512\|sha512-256\|sha3-256\|sha3-384\|sha3-512):[0-9a-fA-F]+$`. |
| `minFileVersion` | no | number | Minimum currently-reported file version. |
| `maxFileVersion` | no | number | Maximum currently-reported file version. |
| `minHardwareVersion` | no | number | Minimum reported hardware version. |
| `maxHardwareVersion` | no | number | Maximum reported hardware version. |

### CLI

```bash
homey app driver firmware --driver ./drivers/my-plug --firmware ./firmware/v1.2.3.bin
```

Requires `homey` CLI **v4.3.0+**. Both `--driver` and `--firmware` are mandatory; `--firmware` is an
array option, so it may be repeated. What the command does, in order:

1. Requires the app to use **Homey Compose** (offers to migrate otherwise).
2. Reads `<driver>/driver.compose.json` and refuses drivers that have neither a `zigbee` nor a
   `zwave` object.
3. Validates the **Zigbee OTA header** of every `--firmware` file before touching anything.
4. Prompts for the changelog and whether the update should be limited to a device firmware-version
   range; if yes, prompts per file for `minFileVersion` / `maxFileVersion` (32-bit unsigned ints).
5. Prompts (checkbox lists, pre-filled from the driver's `zigbee.manufacturerName` /
   `zigbee.productId`) for the `updates[].device` targeting.
6. Copies each file into `/drivers/<driver_id>/assets/firmware/`.
7. Derives `fileVersion`, `imageType`, `manufacturerCode`, `size` (the header's `totalImageSize`),
   `minHardwareVersion`, `maxHardwareVersion` and `name` from the OTA header/file name, and computes
   the `sha256` `integrity` hash.
8. On a **newly created** `driver.firmware.compose.json` only, asks whether the device sleeps and
   stores the answer as `wakeInstruction`.
9. Appends the update to `updates[]` and writes the file.

Everything is written in English only (`{ "en": … }`); translate afterwards.

### Update selection

The device sends `queryNextImageRequest` with `manufacturerCode`, `imageType`, `fileVersion` and
optionally `hardwareVersion`. Homey picks a file when:

1. `updates[].device` matches the device's reported manufacturer name and product id;
2. one of the update's files matches the reported `manufacturerCode` and `imageType`;
3. the optional `min/maxFileVersion` and `min/maxHardwareVersion` bounds match; and
4. the file's `fileVersion` is **higher** than the device's current `fileVersion`.

If several updates match, the one with the highest `fileVersion` wins.

**Multiple files per update:** a device that also updates a second chip sends another
`queryNextImageRequest` with a different `manufacturerCode`/`imageType`/`fileVersion`. Put those
secondary images in the **same** `updates[].files` list so the process continues without user
interaction.

### Failure modes

| Case | Meaning |
| --- | --- |
| Explicit abort | The device reports an error status during image transfer. |
| Stalled transfer | The device stops requesting firmware chunks before completion. |
| No reconnection | The device does not rejoin the Zigbee network in time after the file transferred. |

The user is notified on the firmware update screen and can retry.

**Before shipping firmware:** verify each file is mapped to the correct device (a wrong image can
brick it irreversibly), test the full update flow end-to-end on the real hardware, and never publish
an untested update. Firmware files are stored separately from the app after upload and downloaded by
Homey only when an update actually starts.

---

## 13. SDK v2 → v3 Zigbee migration

```bash
npm install --save homey-zigbeedriver zigbee-clusters
npm uninstall homey-meshdriver
```

### Manifest mapping

| SDK v2 (`homey-meshdriver`) | SDK v3 |
| --- | --- |
| `manufacturerId` | `manufacturerName` |
| `productId` | `productId` (unchanged) |
| `deviceId` | **remove** |
| `profileId` | **remove** |
| — | `endpoints` — **new and required**; get it from the *interview* button in the Zigbee Developer Tools |

> The upgrade-guide page still names the surviving key `manufacturerId`. That is a documentation
> slip: homey-lib's `zigbeeDevice` schema requires `manufacturerName`, `productId` **and**
> `endpoints`. Use `manufacturerName`.

Do **not** assume the endpoint ids you used before are still valid — an incorrect endpoint
definition yields a non-functioning device. The endpoint definition is currently *dynamic*: it does
not require a repair to be updated on the device (this may change in the future).

### Code mapping

| SDK v2 | SDK v3 | Note |
| --- | --- | --- |
| `require('homey-meshdriver')` | `require('homey-zigbeedriver')` | |
| `MeshDevice` | `ZigBeeDevice` | Removed. |
| `onMeshInit()` | `onNodeInit({ zclNode, node })` | Deprecated but still called. |
| `this.node.on('online')` | `this.onEndDeviceAnnounce()` | Removed. |
| `cluster: 'genOnOff'` (string) | `CLUSTER.ON_OFF` object from `zigbee-clusters` | Cluster is now `{ NAME, ID }`. |
| `registerReportListener()` | `BoundCluster` implementation | Now throws. |
| `registerAttrReportListener()` | `configureAttributeReporting()` | Now throws. |
| `calculateZigbeeDimDuration()` | `calculateLevelControlTransitionTime()` | Plus new `calculateColorControlTransitionTime()` for `colorControl`. |
| `getClusterEndpoint()` returned a default | returns `null` when not found | Check for `null`. |
| `ZigBeeXYLightDevice` | `ZigBeeLightDevice` | Auto-detects hue/saturation vs XY. |
| `ZigBeeLightDevice` from meshdriver | `ZigBeeLightDevice` from `homey-zigbeedriver` | Import swap is often the whole migration. |

Reference migrated app: <https://github.com/athombv/com.ikea.tradfri-example>.
`homey-zigbeedriver@2.0.0` breaking change: `windowcoverings_set` values are **no longer inverted**.
`zigbee-clusters@2.0.0`: `readAttributes` takes an **array**. `zigbee-clusters@3.0.0` renamed
`iasZone` `zoneType` enum keys: `cabonMonoxideSensor`→`carbonMonoxideSensor`, `keyfob`→`keyFob`,
`standard`→`standardCIE`, `invalid`→`invalidZoneType`, `keyPad`→`keypad`, and added
`doorWindowHandle` (0x0016).

---

## 14. Gotchas

- **Never communicate with the node in `onInit`/`onNodeInit` unless you must.** Zigbee may not be
  ready; unhandled request promises make the device unavailable ("Zigbee was not ready") up to
  `homey-zigbeedriver@2.1.3`, and can leave `onNodeInit` incomplete in 2.1.4+. Always
  `.catch(err => this.error(err))` — an unhandled rejection can crash the app.
- **Only endpoints and clusters listed in `zigbee.endpoints` exist on the `ZCLNode`.** A missing
  cluster id in the manifest shows up as `undefined` on `zclNode.endpoints[x].clusters`, not as a
  Zigbee error.
- **Attribute reporting needs a binding.** Add the cluster id to `bindings` (not just `clusters`),
  otherwise `configureReporting` fails or the reports never arrive.
- **`maxInterval` must be `0` or `≥ 60` and `≥ minInterval`**, otherwise
  `configureAttributeReporting` throws `invalid_max_interval_value` before touching the radio; a
  negative `minInterval` throws `RangeError('invalid_min_interval_value')`. (The JSDoc says "larger
  than 60"; the implemented check is `maxInterval < 60`, so exactly `60` passes.)
- **Batch attribute-reporting configurations per cluster/endpoint** in one
  `configureAttributeReporting([...])` call — each cluster then needs only one round trip. Critical
  for battery devices.
- **Configure attribute reporting on sleepy end devices** so Homey gets a periodic heartbeat proving
  the device is still on the network.
- **One request at a time for SEDs.** The parent router buffers only a few messages and the SED
  fetches one per wake-up.
- **IAS Zone (`1280`) auto-enrolls from Homey v13.1.2.** `onZoneEnrollRequest` is no longer forwarded
  to apps and Homey always assigns `zoneId: 0` — do not implement enrollment yourself.
- **Group broadcasts:** Homey Pro (2023—2026) and Pro mini only listen to group ID `0` and Touchlink
  groups; Homey Pro (2016—2019) and Homey Bridge listen to all groups.
- **`cluster` must be a `CLUSTER.*` object, not a string.** `registerCapability('onoff', 'onOff')`
  fails the `assertClusterSpecification` check.
- **Device settings may not start with `zb_`** — it is a reserved setting-id prefix (the full set in
  homey-lib is `homey:`, `zw_`, `zb_`, `mtr_`, `thread_`, `zone_`, `energy_`, `satellite_mode_`,
  `homekit_`). `homey app validate` emits a `console.warn`
  ("cannot start with reserved prefix") rather than failing outright — treat it as an error anyway,
  the id collides with the system settings. `zb_product_id` in particular is the system setting
  `energyMap` keys on, and `zw_sb_build_id` is the one `getSwBuildId()` reads.
- **Sub devices require `Driver extends ZigBeeDriver`.** Otherwise `ZigBeeDevice#onInit` throws
  "Driver <id> must extend ZigBeeDriver when using Zigbee sub devices".
- **Give sub devices `"settings": []`** if they should not inherit the root device's settings.
- **You cannot write custom pair views for Zigbee.** Pairing is fully handled by Homey; only
  `learnmode` (`instruction` + optional `image`) is yours.
- **`learnmode.instruction` is required** by the schema; `image` is optional.
- **Do not ship `debug(true)`** from `zigbee-clusters` in a published app.
- **Never mix manufacturer-specific and regular attributes** in a single `readAttributes`,
  `writeAttributes` or `configureReporting` call.
- **`readAttributes` drops attributes the device answers with a non-`SUCCESS` status** — they are
  simply missing from the result object, so always guard before destructuring/arithmetic instead of
  assuming a number came back.
- **`.catch()` that returns nothing breaks destructuring.** `const { x } = await p.catch(...)`
  throws a `TypeError` on the rejected path; return `{}` from the catch.
- **`Cluster.addCluster()` must run before any `ZCLNode` is created**, otherwise the custom cluster
  is not available on the node.
- **Multiplier/divisor factors are not read automatically** — `measure_power`, `measure_current`,
  `measure_voltage` and `meter_power` default their factor to `1` until you set
  `this.activePowerFactor` / `this.acCurrentFactor` / `this.acVoltageFactor` /
  `this.meteringFactor`.
- **`light_temperature` needs the store values `colorTempMin` and `colorTempMax`** (read from
  `colorTempPhysicalMinMireds` / `colorTempPhysicalMaxMireds`). `ZigBeeLightDevice` does this for
  you; a plain `ZigBeeDevice` does not.
- **Do not add `light_temperature` to devices without `colorTemperature` support** — the legacy HSV
  fallback produces skewed colors.
- **Override `handleFrame` when using the raw API** — the default implementation throws.
- **A Zigbee driver declares no app permission in practice**, but it must declare
  `"connectivity": ["zigbee"]`. Mind the discrepancy in §5: homey-lib *does* ship a
  `homey:wireless:zigbee` permission (1 of its 13) even though the published permissions guide omits
  it, and the manifest schema types `permissions` as a plain `string[]` that validates either way.
- **`registerCapability` resolves the endpoint for you** with `getClusterEndpoint(cluster)` unless
  you pass `endpoint: <number>`, and **throws `missing_cluster`** when the cluster is on no endpoint
  of the `ZCLNode` — which is what you get when the cluster id is missing from `zigbee.endpoints`.
  `configureAttributeReporting`'s `endpointId` does *not* auto-resolve; it defaults to `1`.
- **`CLUSTER` has 46 entries but 47 cluster classes ship** — `dehumidificationControl` (515) has no
  `CLUSTER.*` constant.
- **Zigbee works on Homey Cloud / Homey Bridge** (`zigbee` is an allowed `connectivity` value there),
  unlike `lan` and `rf868`. Cloud apps still face the multi-tenancy rules — no global mutable state.
- **Do not put a protocol name in the app name** — "Zigbee", "Z-Wave", "433 MHz", "Infrared" are
  disallowed in App Store names.
- **Zigbee OTA can brick devices.** Verify targeting and test the full flow on real hardware before
  publishing an update.

---

## 15. Appendix — attributes & commands per cluster (`zigbee-clusters@3.5.0`)

Attribute names are what you pass to `readAttributes` / `configureReporting` / `get` / `report`;
command names are the methods on `zclNode.endpoints[x].clusters[y]` and the handler names in a
`BoundCluster`. Clusters listed with none defined exist as ids only — extend them with a custom
cluster if you need their contents.

- **`basic` (0)** — attrs: `zclVersion`, `appVersion`, `stackVersion`, `hwVersion`,
  `manufacturerName`, `modelId`, `dateCode`, `powerSource`, `appProfileVersion`, `locationDesc`,
  `physicalEnv`, `deviceEnabled`, `alarmMask`, `disableLocalConfig`, `swBuildId`. cmds:
  `factoryReset`.
- **`powerConfiguration` (1)** — attrs: `batteryVoltage`, `batteryPercentageRemaining`,
  `batterySize`, `batteryQuantity`, `batteryRatedVoltage`, `batteryVoltageMinThreshold`,
  `batteryAlarmState`. cmds: none.
- **`deviceTemperature` (2)** — attrs: `currentTemperature`, `minTempExperienced`,
  `maxTempExperienced`, `overTempTotalDwell`, `deviceTempAlarmMask`, `lowTempThreshold`,
  `highTempThreshold`, `lowTempDwellTripPoint`, `highTempDwellTripPoint`. cmds: none.
- **`identify` (3)** — attrs: `identifyTime`. cmds: `identify`, `identifyQuery`, `triggerEffect`.
- **`groups` (4)** — attrs: `nameSupport`. cmds: `addGroup`, `viewGroup`, `getGroupMembership`,
  `removeGroup`, `removeAllGroups`, `addGroupIfIdentify`.
- **`scenes` (5)** — none defined (extend `ScenesCluster` for manufacturer scene commands).
- **`onOff` (6)** — attrs: `onOff`, `globalSceneControl`, `onTime`, `offWaitTime`, `startUpOnOff`.
  cmds: `setOff`, `setOn`, `toggle`, `offWithEffect`, `onWithRecallGlobalScene`, `onWithTimedOff`.
- **`onOffSwitch` (7)** — none defined.
- **`levelControl` (8)** — attrs: `currentLevel`, `remainingTime`, `onOffTransitionTime`, `onLevel`,
  `onTransitionTime`, `offTransitionTime`, `defaultMoveRate`, `startUpCurrentLevel`. cmds:
  `moveToLevel`, `move`, `step`, `stop`, `moveToLevelWithOnOff`, `moveWithOnOff`, `stepWithOnOff`,
  `stopWithOnOff`.
- **`alarms` (9)** — attrs: none. cmds: `resetAllAlarms`, `getAlarm`, `resetAlarmLog`.
- **`time` (10)** — none defined.
- **`analogInput` (12)** — attrs: `description`, `maxPresentValue`, `minPresentValue`,
  `outOfService`, `presentValue`, `reliability`, `resolution`, `statusFlags`, `applicationType`.
- **`analogOutput` (13)** — as `analogInput` plus `relinquishDefault`.
- **`analogValue` (14)** — attrs: `description`, `outOfService`, `presentValue`, `reliability`,
  `relinquishDefault`, `statusFlags`, `applicationType`.
- **`binaryInput` (15)** — attrs: `activeText`, `description`, `inactiveText`, `outOfService`,
  `polarity`, `presentValue`, `reliability`, `statusFlags`, `applicationType`.
- **`binaryOutput` (16)** / **`binaryValue` (17)** — as `binaryInput` plus `minimumOffTime`,
  `minimumOnTime`, `relinquishDefault`.
- **`multistateInput` (18)** — attrs: `description`, `numberOfStates`, `outOfService`,
  `presentValue`, `reliability`, `statusFlags`, `applicationType`.
- **`multistateOutput` (19)** / **`multistateValue` (20)** — as `multistateInput` plus
  `relinquishDefault`.
- **`ota` (25)** — attrs: `upgradeServerID`, `fileOffset`, `currentFileVersion`,
  `currentZigBeeStackVersion`, `downloadedFileVersion`, `downloadedZigBeeStackVersion`,
  `imageUpgradeStatus`, `manufacturerID`, `imageTypeID`, `minimumBlockPeriod`, `imageStamp`,
  `upgradeActivationPolicy`, `upgradeTimeoutPolicy`. cmds: `imageNotify`, `queryNextImageRequest`,
  `imageBlockRequest`, `imagePageRequest`, `imageBlockResponse`, `upgradeEndRequest`,
  `upgradeEndResponse`, `queryDeviceSpecificFileRequest`. (Homey drives this cluster itself — see
  §12; apps should not implement it.)
- **`powerProfile` (26)** — none defined.
- **`pollControl` (32)** — attrs: `checkInInterval`, `longPollInterval`, `shortPollInterval`,
  `fastPollTimeout`, `checkInIntervalMin`, `longPollIntervalMin`, `fastPollTimeoutMax`. cmds:
  `fastPollStop`, `setLongPollInterval`, `setShortPollInterval`.
- **`shadeConfiguration` (256)** — none defined.
- **`doorLock` (257)** — attrs (43): `lockState`, `lockType`, `actuatorEnabled`, `doorState`,
  `doorOpenEvents`, `doorClosedEvents`, `openPeriod`, `numberOfLogRecordsSupported`,
  `numberOfTotalUsersSupported`, `numberOfPINUsersSupported`, `numberOfRFIDUsersSupported`,
  `numberOfWeekDaySchedulesSupportedPerUser`, `numberOfYearDaySchedulesSupportedPerUser`,
  `numberOfHolidaySchedulesSupported`, `maxPINCodeLength`, `minPINCodeLength`, `maxRFIDCodeLength`,
  `minRFIDCodeLength`, `enableLogging`, `language`, `ledSettings`, `autoRelockTime`, `soundVolume`,
  `operatingMode`, `supportedOperatingModes`, `defaultConfigurationRegister`,
  `enableLocalProgramming`, `enableOneTouchLocking`, `enableInsideStatusLED`,
  `enablePrivacyModeButton`, `wrongCodeEntryLimit`, `userCodeTemporaryDisableTime`,
  `sendPINOverTheAir`, `requirePINforRFOperation`, `securityLevel`, `alarmMask`,
  `keypadOperationEventMask`, `rfOperationEventMask`, `manualOperationEventMask`,
  `rfidOperationEventMask`, `keypadProgrammingEventMask`, `rfProgrammingEventMask`,
  `rfidProgrammingEventMask`. cmds (28): `lockDoor`, `unlockDoor`, `toggle`, `unlockWithTimeout`,
  `getLogRecord`, `operationEventNotification`, `programmingEventNotification`, plus
  `set`/`get`/`clear` families for `PINCode` (+`clearAllPINCodes`), `RFIDCode`
  (+`clearAllRFIDCodes`), `UserStatus`, `UserType`, `WeekDaySchedule`, `YearDaySchedule` and
  `HolidaySchedule`.
- **`windowCovering` (258)** — attrs: `windowCoveringType`, `physicalClosedLimitLift`,
  `physicalClosedLimitTilt`, `currentPositionLift`, `currentPositionTilt`, `numberofActuationsLift`,
  `numberofActuationsTilt`, `configStatus`, `currentPositionLiftPercentage`,
  `currentPositionTiltPercentage`, `installedOpenLimitLift`, `installedClosedLimitLift`,
  `installedOpenLimitTilt`, `installedClosedLimitTilt`, `velocityLift`, `accelerationTimeLift`,
  `decelerationTimeLift`, `mode`, `intermediateSetpointsLift`, `intermediateSetpointsTilt`. cmds:
  `upOpen`, `downClose`, `stop`, `goToLiftValue`, `goToLiftPercentage`, `goToTiltValue`,
  `goToTiltPercentage`.
- **`pumpConfigurationAndControl` (512)**, **`fanControl` (514)**, **`dehumidificationControl`
  (515)** — none defined. `dehumidificationControl` additionally has **no `CLUSTER` constant** (see
  §8) — use `Cluster.getCluster(515)` or the exported `DehumidificationControlCluster` class.
- **`thermostat` (513)** — attrs: `localTemperature`, `outdoorTemperature`, `occupancy`,
  `absMinHeatSetpointLimit`, `absMaxHeatSetpointLimit`, `absMinCoolSetpointLimit`,
  `absMaxCoolSetpointLimit`, `pICoolingDemand`, `pIHeatingDemand`, `localTemperatureCalibration`,
  `occupiedCoolingSetpoint`, `occupiedHeatingSetpoint`, `unoccupiedCoolingSetpoint`,
  `unoccupiedHeatingSetpoint`, `minHeatSetpointLimit`, `maxHeatSetpointLimit`,
  `minCoolSetpointLimit`, `maxCoolSetpointLimit`, `minSetpointDeadBand`, `remoteSensing`,
  `controlSequenceOfOperation`, `systemMode`, `alarmMask`, `runningMode`. cmds: `setSetpoint`.
- **`thermostatUserInterfaceConfiguration` (516)** — attrs: `temperatureDisplayMode`,
  `keypadLockout`, `scheduleProgrammingVisibility`.
- **`colorControl` (768)** — attrs: `currentHue`, `currentSaturation`, `currentX`, `currentY`,
  `colorTemperatureMireds`, `colorMode`, `options`, `enhancedCurrentHue`, `enhancedColorMode`,
  `colorLoopActive`, `colorLoopDirection`, `colorLoopTime`, `colorLoopStartEnhancedHue`,
  `colorLoopStoredEnhancedHue`, `colorCapabilities`, `colorTempPhysicalMinMireds`,
  `colorTempPhysicalMaxMireds`, `startUpColorTemperatureMireds`. cmds: `moveToHue`,
  `moveToSaturation`, `moveToHueAndSaturation`, `moveToColor`, `moveToColorTemperature`,
  `colorLoopSet`.
- **`ballastConfiguration` (769)** — attrs: `physicalMinLevel`, `physicalMaxLevel`, `ballastStatus`,
  `minLevel`, `maxLevel`, `powerOnLevel`, `powerOnFadeTime`, `intrinsicBallastFactor`,
  `ballastFactorAdjustment`, `lampQuantity`, `lampType`, `lampManufacturer`, `lampRatedHours`,
  `lampBurnHours`, `lampAlarmMode`, `lampBurnHoursTripPoint`.
- **`illuminanceMeasurement` (1024)** — attrs: `measuredValue`, `minMeasuredValue`,
  `maxMeasuredValue`, `tolerance`, `lightSensorType`.
- **`illuminanceLevelSensing` (1025)** — attrs: `levelStatus`, `lightSensorType`,
  `illuminanceTargetLevel`.
- **`temperatureMeasurement` (1026)** — attrs: `measuredValue`, `minMeasuredValue`,
  `maxMeasuredValue`.
- **`pressureMeasurement` (1027)** — attrs: `measuredValue`, `minMeasuredValue`, `maxMeasuredValue`,
  `tolerance`, `scaledValue`, `minScaledValue`, `maxScaledValue`, `scaledTolerance`, `scale`.
- **`flowMeasurement` (1028)** / **`relativeHumidity` (1029)** — attrs: `measuredValue`,
  `minMeasuredValue`, `maxMeasuredValue`, `tolerance`.
- **`occupancySensing` (1030)** — attrs: `occupancy`, `occupancySensorType`,
  `occupancySensorTypeBitmap`, `pirOccupiedToUnoccupiedDelay`, `pirUnoccupiedToOccupiedDelay`,
  `pirUnoccupiedToOccupiedThreshold`, `ultrasonicOccupiedToUnoccupiedDelay`,
  `ultrasonicUnoccupiedToOccupiedDelay`, `ultrasonicUnoccupiedToOccupiedThreshold`,
  `physicalContactOccupiedToUnoccupiedDelay`, `physicalContactUnoccupiedToOccupiedDelay`,
  `physicalContactUnoccupiedToOccupiedThreshold`.
- **`iasZone` (1280)** — attrs: `zoneState` (`enum8` `notEnrolled`/`enrolled`), `zoneType`
  (`enum16`), `zoneStatus`, `iasCIEAddress` (`EUI64`), `zoneId` (`uint8`). cmds:
  `zoneStatusChangeNotification`, `zoneEnrollResponse`, `zoneEnrollRequest`,
  `initiateNormalOperationMode` — note `zoneStatusChangeNotification`/`zoneEnrollResponse` share
  command id `0x00` and `zoneEnrollRequest`/`initiateNormalOperationMode` share `0x01`; they are
  disambiguated by `direction`.
  `zoneStatus` is a `map16` with flags: `alarm1`, `alarm2`, `tamper`, `battery`,
  `supervisionReports`, `restoreReports`, `trouble`, `acMains`, `test`, `batteryDefect`.
  `zoneType` values (identical for the attribute and the `zoneEnrollRequest` argument since
  `zigbee-clusters@3.0.0`): `standardCIE` 0x0000, `motionSensor` 0x000D, `contactSwitch` 0x0015,
  `doorWindowHandle` 0x0016, `fireSensor` 0x0028, `waterSensor` 0x002A, `carbonMonoxideSensor`
  0x002B, `personalEmergencyDevice` 0x002C, `vibrationMovementSensor` 0x002D, `remoteControl`
  0x010F, `keyFob` 0x0115, `keypad` 0x021D, `standardWarningDevice` 0x0225, `glassBreakSensor`
  0x0226, `securityRepeater` 0x0229, `invalidZoneType` 0xFFFF.
  `zoneEnrollResponse.enrollResponseCode`: `success` 0, `notSupported` 1, `noEnrollPermit` 2,
  `tooManyZones` 3.
- **`iasACE` (1281)**, **`iasWD` (1282)**, **`diagnostics` (2821)** — none defined.
- **`metering` (1794)** — 173 attributes, no commands. 96 of them are pure block-summation series:
  `currentNoTierBlock<1..16>SummationDelivered` (16),
  `currentNoTierBlock<1..16>SummationReceived` (16) and
  `currentTier<1..4>Block<1..16>SummationDelivered` (64). The other 77, in full:
  `currentSummationDelivered`, `currentSummationReceived`, `currentMaxDemandDelivered`,
  `currentMaxDemandReceived`, `dftSummation`, `dailyFreezeTime`, `powerFactor`,
  `readingSnapShotTime`, `currentMaxDemandDeliveredTime`, `currentMaxDemandReceivedTime`,
  `defaultUpdatePeriod`, `fastPollUpdatePeriod`, `currentBlockPeriodConsumptionDelivered`,
  `dailyConsumptionTarget`, `currentTier<1..4>SummationDelivered`,
  `currentTier<1..4>SummationReceived` (8), `status`, `remainingBatteryLife`, `hoursInOperation`,
  `hoursInFault`, `multiplier`, `divisor`, `siteId`, `meterSerialNumber`, `moduleSerialNumber`,
  `operatingTariffLabelDelivered`, `operatingTariffLabelReceived`, `customerIdNumber`,
  `instantaneousDemand`, `currentDayConsumptionDelivered`, `currentDayConsumptionReceived`,
  `previousDayConsumptionDelivered`, `previousDayConsumptionReceived`,
  `currentPartialProfileIntervalStartTimeDelivered`,
  `currentPartialProfileIntervalStartTimeReceived`, `currentPartialProfileIntervalValueDelivered`,
  `currentPartialProfileIntervalValueReceived`, `currentDayMaxPressure`, `currentDayMinPressure`,
  `previousDayMaxPressure`, `previousDayMinPressure`, `currentDayMaxDemand`, `previousDayMaxDemand`,
  `currentMonthMaxDemand`, `currentYearMaxDemand`, `currentDayMaxEnergyCarrierDemand`,
  `previousDayMaxEnergyCarrierDemand`, `currentMonthMaxEnergyCarrierDemand`,
  `currentMonthMinEnergyCarrierDemand`, `currentYearMaxEnergyCarrierDemand`,
  `currentYearMinEnergyCarrierDemand`, `maxNumberOfPeriodsDelivered`, `currentDemandDelivered`,
  `demandLimit`, `demandIntegrationPeriod`, `numberOfDemandSubintervals`, `demandLimitArmDuration`,
  `billToDateDelivered`, `billToDateTimeStampDelivered`, `projectedBillDelivered`,
  `projectedBillTimeStampDelivered`, `billToDateReceived`, `billToDateTimeStampReceived`,
  `projectedBillReceived`, `projectedBillTimeStampReceived`,
  `proposedChangeSupplyImplementationTime`, `uncontrolledFlowThreshold`,
  `uncontrolledFlowMultiplier`, `uncontrolledFlowDivisor`, `flowStabilisationPeriod`,
  `flowMeasurementPeriod`. Source: `zigbee-clusters/lib/clusters/metering.js`.
- **`electricalMeasurement` (2820)** — attrs: `measurementType`, `acFrequency`,
  `measuredPhase1stHarmonicCurrent`, `acFrequencyMultiplier`, `acFrequencyDivisor`,
  `phaseHarmonicCurrentMultiplier`, `rmsVoltage`, `rmsCurrent`, `activePower`, `reactivePower`,
  `acVoltageMultiplier`, `acVoltageDivisor`, `acCurrentMultiplier`, `acCurrentDivisor`,
  `acPowerMultiplier`, `acPowerDivisor`, `acAlarmsMask`, `acVoltageOverload`, `acCurrentOverload`,
  `acActivePowerOverload`.
- **`touchlink` (4096)** — cmds: `getGroups`.

---

## Sources

- <https://apps.developer.homey.app/wireless/zigbee>
- <https://apps.developer.homey.app/wireless/zigbee/zigbee-firmware-updates>
- <https://apps.developer.homey.app/guides/tools/zigbee>
- <https://apps.developer.homey.app/upgrade-guides/upgrading-to-sdk-v3/upgrading-zigbee>
- <https://apps-sdk-v3.developer.homey.app/ManagerZigBee.html>
- <https://apps-sdk-v3.developer.homey.app/ZigBeeNode.html>
- <https://athombv.github.io/node-homey-zigbeedriver/> (`homey-zigbeedriver@2.2.17`)
- <https://github.com/athombv/node-zigbee-clusters> (`zigbee-clusters@3.5.0`)
- <https://etc.athom.com/zigbee_cluster_specification.pdf>
- <https://github.com/athombv/com.ikea.tradfri-example>
- <https://tools.developer.homey.app/tools/zigbee>
