# Z-Wave

Building Z-Wave drivers for Homey Apps SDK v3: the `zwave` block in `driver.compose.json`, the
`homey-zwavedriver` library (`ZwaveDevice`, `ZwaveLightDevice`), configuration parameters, multi-channel
endpoints, the raw `this.homey.zwave` API and OTA firmware updates.

Related: `references/wireless-zigbee.md`, `references/drivers-and-devices.md`, `references/flow-cards.md`.

## Model

Z-Wave is built around **Command Classes** — groups of **Commands**. Commands fall in three categories:

| Category | Meaning | Example |
| --- | --- | --- |
| `*_SET` | update a value on the device | `BASIC_SET({ Value: true })` |
| `*_GET` | request the current value; the device answers with a report | `BASIC_GET()` |
| `*_REPORT` | the device tells Homey the current value | `BASIC_REPORT` → `{ Value: true }` |

In code, command classes are reached as `node.CommandClass.COMMAND_CLASS_<NAME>` and commands as
functions on that object. In `homey-zwavedriver` the `COMMAND_CLASS_` prefix is **dropped**: you pass
`'SWITCH_BINARY'`, not `'COMMAND_CLASS_SWITCH_BINARY'`.

Command Class reference: <https://z-wavealliance.org/development-resources-overview/z-wave-command-classes/>

## Getting started

```bash
npm install homey-zwavedriver
```

`homey app driver create` has a Z-Wave branch: it offers to `npm install homey-zwavedriver`, then prompts for
Manufacturer ID (decimal), Product Type ID (decimal, comma-separated for multiple), Product ID (decimal,
comma-separated), Z-Wave Alliance Product ID, Z-Wave Alliance Product Documentation URL, an inclusion
description and an exclusion description. It writes `drivers/<id>/driver.compose.json` with
`"connectivity": ["zwave"]` plus the `zwave` object, and `driver.settings.compose.json` when settings were
produced.

`homey-zwavedriver` is **SDK v3 only**. Its SDK v2 predecessor was `homey-meshdriver`.

Deprecations relative to `homey-meshdriver`:

| Removed / deprecated | Replacement |
| --- | --- |
| `MeshDevice` | `ZwaveDevice` |
| `onMeshInit()` | `onNodeInit()` |
| `calculateZwaveDimDuration` | `calculateDimDuration` |
| `ZwaveMeteringDevice`, `ZwaveLockDevice` | removed (no replacement class) |

## Finding the device IDs

To create a driver you need `manufacturerId`, `productTypeId` and `productId`. Pair the device as a **Basic
Z-Wave Device** first; after pairing the three values appear in the device settings. An app driver is selected
during pairing only when **all three** IDs match.

Values are **decimal**, not hex. Z-Wave Alliance product data: <https://products.z-wavealliance.org/>

## `driver.compose.json` → `zwave`

```json
{
  "name": { "en": "My Driver" },
  "class": "light",
  "capabilities": ["onoff"],
  "platforms": ["local", "cloud"],
  "connectivity": ["zwave"],
  "zwave": {
    "manufacturerId": 271,
    "productTypeId": [256],
    "productId": [260],
    "learnmode": {
      "image": "/drivers/<driver_id>/assets/learnmode.svg",
      "instruction": { "en": "Press the button on your device three times" }
    }
  }
}
```

### Full property table

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `manufacturerId` | `number` \| `number[]` | yes | Manufacturer ID, decimal. |
| `productTypeId` | `number` \| `number[]` | yes | Product Type ID(s), decimal. Array to support several devices in one driver. |
| `productId` | `number` \| `number[]` | yes | Product ID(s), decimal. Array to support several devices in one driver. |
| `learnmode` | `object` | no | `{ instruction: <i18n>, image: <path> }`. `instruction` is required inside the object. Customises the built-in Z-Wave pair wizard. |
| `unlearnmode` † | `object` | no | Same shape as `learnmode`; customises the unpair (exclusion) wizard. Written by `homey app driver create`. |
| `requireSecure` † | `boolean` | no | Opt into **S0** (legacy) secure inclusion. See [Security](#security). |
| `defaultConfiguration` | `array` | no | `[{ id, size, value }]` — configuration parameters written after pairing. |
| `associationGroups` | `number[]` | no | Association group numbers Homey adds itself to after pairing. |
| `associationGroupsMultiChannel` | `number[]` | no | Legacy pre-v13.2.0 multi-channel association groups. Handled identically to `associationGroups` today. |
| `associationGroupsOptions` | `object` | no | Keyed by group number **as a string**: `{ "3": { "hint": <i18n> } }`. (The app schema declares this as a flat `{ properties: { hint } }` object, which is a schema bug — the docs and shipped apps such as `com.danalock-example` use the group-number keying, and since the object is not `additionalProperties: false` both validate.) |
| `wakeUpInterval` | `number` | no | Desired wake-up interval in **seconds**; allowed range **30 – 16777215** (30 s – 194 days). The schema declares only `type: "number"` — the range is a runtime/documentation constraint, not something `homey app validate` checks. |
| `multiChannelNodes` † | `object` | no | Endpoint definitions, keyed by endpoint id. See [Multi channel nodes](#multi-channel-nodes). |
| `productDocumentation` † | `string` | no | URL to the manufacturer/Z-Wave Alliance product manual (used by `com.danalock-example`). |
| `zwaveAllianceProductId` † | `number` \| `string` | no | Z-Wave Alliance product id (the four-digit id in the `products.z-wavealliance.org` URL). Written by `homey app driver create` (as the raw **string** the user typed, it is not parsed to a number). |
| `zwaveAllianceProductDocumentation` † | `string` | no | URL of the Z-Wave Alliance product manual. Written by `homey app driver create`. |

> **Schema discrepancy (†).** The `zwaveDevice` definition in the app schema declares exactly nine
> properties: `manufacturerId`, `productTypeId`, `productId`, `learnmode`, `associationGroups`,
> `associationGroupsMultiChannel`, `associationGroupsOptions`, `wakeUpInterval` and
> `defaultConfiguration`. The rows marked † are **absent from the schema** even though the SDK
> documentation describes them, the CLI writes them (`unlearnmode`, `zwaveAllianceProductId`,
> `zwaveAllianceProductDocumentation`) and shipped Athom example apps use them (`requireSecure` and
> `productDocumentation` in `com.danalock-example`, `multiChannelNodes` in `com.fibaro-example`).
> They validate only because `zwaveDevice` is **not** `additionalProperties: false`. `multiChannelNodes`
> is the odd one out: the schema *does* contain a `multiChannelNodes` sub-schema, but it is nested one
> level too deep — inside `defaultConfiguration.items.properties` instead of at the `zwave` level — and
> even there it is written as `{ "type": "object", "items": { … } }`, where `items` is meaningless for
> an object, so endpoint objects are never validated at all.

The `zwave` object is **not** `additionalProperties: false` in the app schema, so unknown keys validate; only
the keys above are honoured by Homey and the CLI. This is also why legacy/typo keys survive in published
apps — `com.fibaro-example` still ships `includeSecure`, `associationGroupOptions` (missing `s`) and
`__comment`, and `com.danalock-example` ships `pid` and `imageRemotePath`. None of those do anything; do
not copy them.

> **Warning:** several of these properties (`learnmode`, `defaultConfiguration`, `associationGroups`,
> `wakeUpInterval`, `multiChannelNodes`, `requireSecure`) configure behaviour **during pairing**. Changing them
> requires removing and re-adding existing devices before the change takes effect.

### Learn mode / unlearn mode

```json
"zwave": {
  "manufacturerId": 270,
  "productTypeId": 9,
  "productId": 1,
  "learnmode": {
    "image": "/drivers/danalock_v3/assets/learnmode.svg",
    "instruction": {
      "en": "Press the pair button on top of the Danalock V3 with a small pin, pairing will start within 5 seconds."
    }
  },
  "unlearnmode": {
    "image": "/drivers/danalock_v3/assets/learnmode.svg",
    "instruction": {
      "en": "Press the pair button on top of the Danalock V3 with a small pin, the device will be removed within 5 seconds."
    }
  }
}
```

All Z-Wave devices pair through Homey's built-in Z-Wave pair wizard — you do not write `pair` views for
inclusion. Most devices are excluded the same way they are included; supply `unlearnmode` only when the
exclusion procedure differs or benefits from its own image.

### Security

Two security schemes exist: **Security 0 (S0, legacy)** and **Security 2 (S2)**.

- S2 has several key classes: **Access**, **Authenticated**, **Unauthenticated** (plus S0). The encryption
  algorithm is identical; the key class only decides which devices know which key.
- Homey grants **all** S2 keys a device requests.
- **Homey Pro (2016–2019)** grants only the **highest requested** key.
- Homey uses S2 automatically when the device supports it. Because S0 adds substantial communication
  overhead it is **not** used by default — your app must opt in with `requireSecure`.

Set `requireSecure: true` when the device only exposes functionality over secure communication (e.g. a door
lock that refuses `COMMAND_CLASS_LOCK` unencrypted). Check the device's technical specification for which
command classes require security.

```json
{
  "name": { "en": "My Lock" },
  "class": "lock",
  "capabilities": ["locked"],
  "zwave": {
    "manufacturerId": 270,
    "productTypeId": [8],
    "productId": [2],
    "requireSecure": true
  }
}
```

The current secure state of a paired node is exposed as the read-only device setting `zw_secure`
(`ZwaveDevice#printNodeSummary()` logs it).

### Default device configuration

After pairing, Homey writes the listed configuration parameters so they are guaranteed to hold the value
your driver expects.

```json
"zwave": {
  "manufacturerId": 271,
  "productTypeId": [256],
  "productId": [260],
  "defaultConfiguration": [
    { "id": 3, "size": 1, "value": 123 }
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `id` | `number` | Configuration parameter number. Required. |
| `size` | `1` \| `2` \| `4` | Parameter length in bytes. Required. |
| `value` | `number` \| `string` | Value to write. Required. |

`value` is a **signed** integer whose range follows `size`. As printed in the official documentation:

- size = 1 → -128 … 127
- size = 2 → -32768 … -32767  *(documentation typo; the real signed 16-bit range is -32768 … 32767)*
- size = 4 → -2147483648 … 2147483647

### Association groups

Association groups link Z-Wave devices directly so they can talk without a controller. Homey often has to be
a member of a group to receive status updates — e.g. devices that send "central scene activation" only to
their **Lifeline** (group 1).

- Homey is **always** added to association group **1 (Lifeline)**. That is how Homey learns a device was
  factory reset: the node is removed and the device is marked Unavailable.
- Add extra group numbers to `associationGroups`; Homey decides by itself whether to use a regular or a
  multi-channel association.
- `associationGroupsMultiChannel` is handled exactly like `associationGroups` (Homey joins those groups too,
  using the correct association command class). It exists for backwards compatibility — prefer
  `associationGroups` and set the app `compatibility` to `>=13.2.0`.
- When the device supports `COMMAND_CLASS_ASSOCIATION_GRP_INFO` (most modern devices do), Homey derives the
  per-group hint in device settings automatically. Override or supply it with `associationGroupsOptions`.
- Users can configure device-to-device associations in the device settings UI.

```json
"zwave": {
  "manufacturerId": 271,
  "productTypeId": [256],
  "productId": [260],
  "associationGroups": [1, 3],
  "associationGroupsOptions": {
    "3": { "hint": { "en": "On/off signals from input 3" } }
  }
}
```

**Before Homey v13.2.0:** Homey did not pick regular vs. multi-channel automatically — multi-channel
associations had to be listed in `associationGroupsMultiChannel`. It was also possible to opt out of the
Lifeline association by passing an empty array; since v13.2.0 the Lifeline association is **always** added.

Homey stores the members of each association group in reserved `zw_`-prefixed device settings
(observed in the field as `zw_group_<n>`, e.g. `zw_group_1`). These ids are **not** documented and do
not appear in the app schema, the SDK reference or `homey-zwavedriver` — treat reading them
(`this.getSetting('zw_group_1')`) as unsupported and subject to change. The supported route is the
device settings UI, where users manage device-to-device associations themselves.

### Battery device wake-up interval

Battery ("sleepy") nodes transmit at any time but only listen periodically. The listening cadence is the
**wake up interval**. The manufacturer default is usually fine; override it only when necessary and only with
a value the device actually supports.

```json
"zwave": {
  "manufacturerId": 271,
  "productTypeId": [256],
  "productId": [260],
  "wakeUpInterval": 900
}
```

Range accepted by Homey: **30 – 16777215** seconds.

### Multi channel nodes

A Z-Wave node can implement a given command class only once, so a device with two switches cannot expose
`COMMAND_CLASS_SWITCH_BINARY` twice on the root node. **Multi Channel Nodes** solve this: a node contains
several **endpoints**, each effectively its own Z-Wave node with its own command classes.

List the endpoints you want surfaced as separate Homey devices in `multiChannelNodes`, keyed by endpoint id.

```json
"zwave": {
  "manufacturerId": 271,
  "productTypeId": [256],
  "productId": [260],
  "multiChannelNodes": {
    "1": {
      "name": { "en": "MultiChannel device 1" },
      "class": "socket",
      "capabilities": ["onoff", "measure_power", "meter_power"],
      "icon": "/drivers/<driver_id>/assets/icon-multichannelnode1.svg",
      "settings": []
    }
  }
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | i18n object | yes | Name of the sub-device. |
| `class` | `string` | yes | Device class of the sub-device. |
| `capabilities` | `string[]` | yes | Capabilities of the sub-device. |
| `icon` | `string` | no | Path to an icon for the sub-device. |
| `settings` | `array` | no | Overrides the driver's settings for this endpoint; takes the same values as regular device settings. `[]` removes the inherited settings. |

Each listed endpoint appears as an extra device in the user's device overview after pairing.

> **Schema discrepancy.** None of the above is enforced. The app schema's only `multiChannelNodes`
> sub-schema sits inside `defaultConfiguration.items.properties` (see the note under the property table),
> requires `class`, `capabilities` and `name`, and knows `icon` — but not `settings`. Because it is
> misplaced *and* declared as an object with an `items` keyword, `homey app validate` checks nothing here.
> Typos in an endpoint's `class` or `capabilities` therefore surface only at runtime.

## Device settings ↔ configuration parameters

Map a device setting onto a Z-Wave configuration parameter by adding a `zwave` object to the setting in
`driver.settings.compose.json`. `ZwaveDevice#onSettings()` then performs the `CONFIGURATION_SET` for you.

```json
[
  {
    "id": "minimum_brightness",
    "type": "number",
    "label": { "en": "Minimum brightness level" },
    "value": 1,
    "attr": { "min": 1, "max": 98 },
    "hint": { "en": "This parameter determines the minimal brightness." },
    "zwave": {
      "index": 13,
      "size": 1
    }
  }
]
```

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `index` | `number` | yes | — | Z-Wave configuration **parameter number**. |
| `size` | `1` \| `2` \| `4` | yes | — | Parameter length in bytes. |
| `signed` | `boolean` | no | `true` | Whether the value is written as a signed integer. Set `false` for unsigned parameters. |

Those three are the complete `zwaveSetting` definition; `index` and `size` are its `required` list and
`size` is an `enum` of `1`, `2`, `4` (any other number is a schema error, not just a runtime problem).
`zwaveSetting` is not `additionalProperties: false`, so extra keys slip through unvalidated and unused.

The schema attaches `zwave` to **every** driver-setting type — `text` / `password` / `textarea` / `label`,
`number` / `slider`, `radio` / `dropdown`, `checkbox` and `group` — not only to `number`. In practice use
`number`, `dropdown`/`radio` and `checkbox`; a `zwave` object on a `group` is meaningless because groups
carry no value of their own (their `children` are flattened and validated individually).

```json
"zwave": { "index": 13, "size": 1, "signed": false }
```

Validation performed by `homey app validate`:

- `index` and `size` must both be numbers, otherwise: `Missing property in "zwave" at <driverId>, <settingId>`.
- If the setting declares `attr.max` (or `max`), the max is checked against the parameter size, after being
  divided by `attr.step` when `step > 1`:
  - signed: max must be ≤ `2^(size*8)/2 - 1` (127 / 32767 / 2147483647) → error `Value cannot be signed: …`
  - unsigned: max must be ≤ `2^(size*8) - 1` (255 / 65535 / 4294967295) → error `Max value out of bounds: …`
- Duplicate `zwave.index` values inside one driver produce the warning
  `drivers.<id>: duplicate zwave setting index <n>`.
- Settings nested inside a `type: "group"` are flattened and validated too.

### Reserved setting-id prefixes

Setting ids must **not** start with any of these; `zw_` is the Z-Wave one and Homey owns it:

`homey:`, `zw_`, `zb_`, `mtr_`, `thread_`, `zone_`, `energy_`, `satellite_mode_`, `homekit_`

Homey populates read-only `zw_*` settings on every Z-Wave device. `ZwaveDevice#printNodeSummary()` and
`printNode()` read `zw_application_version`, `zw_application_sub_version`, `zw_hardware_version`,
`zw_secure`, and `zw_application_version_<n>` / `zw_application_sub_version_<n>` for additional
firmware targets.

## `homey-zwavedriver`

Extend `ZwaveDevice` instead of `Homey.Device`. When the node is ready, `onNodeInit({ node })` is called;
register all capabilities there.

```javascript
'use strict';

const { ZwaveDevice } = require('homey-zwavedriver');

class MyZwaveDevice extends ZwaveDevice {

  async onNodeInit({ node }) {
    // `node` is also available as `this.node` once onNodeInit has been invoked.
    this.registerCapability('onoff', 'SWITCH_BINARY');
    this.registerCapability('dim', 'SWITCH_MULTILEVEL');
    this.registerCapability('measure_power', 'METER');
    this.registerCapability('meter_power', 'METER');
  }

}

module.exports = MyZwaveDevice;
```

### Lifecycle

| Member | Notes |
| --- | --- |
| `onNodeInit({ node })` | Override this. Called after `this.homey.zwave.getNode(this)` resolves. |
| `onMeshInit()` | Deprecated since v1.0.0 (homey-meshdriver legacy). Still invoked, just before `onNodeInit`. |
| `onInit()` | Implemented by `ZwaveDevice` — calls `super.onInit()`, gets the node, logs `printNodeSummary()`, then calls `onMeshInit()` and `onNodeInit({ node })`. If `getNode()` rejects, the device is set unavailable with the error. |
| `onDeleted()` | Implemented by `ZwaveDevice` — removes all node listeners, clears all poll timeouts and removes report listeners on all command classes and multi-channel nodes. |
| `onSettings({ oldSettings, newSettings, changedKeys })` | Implemented by `ZwaveDevice` — see below. |
| `this.node` | The `ZwaveNode` instance. |
| `this.thermostatSetpointType` | Instance property, default `'Heating 1'`; used by the `target_temperature` ↔ `THERMOSTAT_SETPOINT` system parser. |
| `this.customSaveMessage` | Optional `object` (i18n, needs at least `en`) or `function(oldSettings, newSettings, changedKeys)` returning one. Shown to the user after saving settings. |

**`onSettings` behaviour in `ZwaveDevice`:** for every changed key it (1) reconfigures the poll interval if
the key is a `getOpts.pollInterval` setting id, (2) executes `configurationSet()` when the manifest setting
has a `zwave` object, (3) otherwise calls a parser registered with `registerSetting()` if one exists, (4) does
nothing at all otherwise. Failures are collected and the promise rejects with a concatenation of
`failed_to_set_<key>_to_<value>_size_<size>` strings. On success it resolves with the save message; for an
offline battery node the message defaults to *"Settings will be saved during the next automatic wakeup of
this device, this might take a while. Activate 'learn mode' on the device to update settings immediately."*

### `registerCapability(capabilityId, commandClassId, userOpts)`

Maps a Homey capability onto a Z-Wave Command Class. `commandClassId` omits the `COMMAND_CLASS_` prefix.

| Option | Type | Description |
| --- | --- | --- |
| `get` | `string` | Command used to get a value (e.g. `'BASIC_GET'`). |
| `getParser` | `Function` | Called before a GET; must return the payload object. |
| `getOpts.getOnStart` | `boolean` | Get the value on app start. Avoid unless the device never reports the value on its own. **Not for battery devices** — the library logs `do not use getOnStart for battery devices` and skips it. |
| `getOpts.getOnOnline` | `boolean` | Battery devices only: get the value when the node wakes up. Also fires immediately if the node is already online. |
| `getOpts.pollInterval` | `number` \| `string` | Poll interval in ms. A **string** is treated as a device-setting id whose value is used (e.g. `'poll_interval'`), and changing that setting re-arms the poll. |
| `getOpts.pollMultiplication` | `number` | Multiplier applied to `pollInterval` (e.g. `1000` for seconds, `60000` for minutes, `3600000` for hours). |
| `set` | `string` | Command used to set a value (e.g. `'BASIC_SET'`). |
| `setParser` | `Function(value, opts)` | Called on set; must return the payload object. Return `null` to skip the set — the set resolves with the string `'IGNORED'` and nothing is transmitted. Returning a `Promise` short-circuits: the promise itself is returned and no command is sent. |
| `setOpts.fn` | `Function(value, opts)` | Called on `process.nextTick` after `setCapabilityValue` resolved. |
| `report` | `string` | Command that reports the value (e.g. `'BASIC_REPORT'`). |
| `reportParser` | `Function(report)` | Called on report; return the capability value, or `null` to ignore this report. |
| `reportParserOverride` | `boolean` | When `true` **and** `reportParser` is a function, `reportParser` wins over every versioned system parser. Assumed `false` when absent. |
| `multiChannelNodeId` | `number` | Register this capability on a multi-channel endpoint instead of the root node. |

`userOpts` are merged **over** the system options found in the library's `/system/capabilities` tree. Lookup
order for the system options:

1. `system/capabilities/<capabilityId>/<deviceClass>/<commandClassId>.js`
2. `system/capabilities/<rootCapabilityId>/<deviceClass>/<commandClassId>.js` (root of a sub-capability like `onoff.output1`)
3. `system/capabilities/<capabilityId>/<commandClassId>.js`
4. `system/capabilities/<rootCapabilityId>/<commandClassId>.js`

If the node (or the requested multi-channel endpoint) does not implement the command class,
`registerCapability` logs `CommandClass: <id> in main node undefined` (or the multi-channel variant) and
returns without registering anything.

### Versioned parsers

Append a version suffix to any parser to bind it to a Command Class version: `getParserV3`, `setParserV2`,
`reportParserV4`, … At runtime the library reads `node.CommandClass.COMMAND_CLASS_<X>.version` and walks
**down** from that version to 1, taking the first matching `<type>ParserV<n>`; if none matches it falls back
to the unversioned `<type>Parser`.

```javascript
this.registerCapability('onoff', 'SWITCH_BINARY', {
  setParserV1: (value) => ({ 'Switch Value': value ? 'on/enable' : 'off/disable' }),
  setParserV2: (value, options) => ({
    'Target Value': value ? 'on/enable' : 'off/disable',
    Duration: 'Default',
  }),
  reportParserV2: (report) => {
    if (report && report['Current Value'] === 'on/enable') return true;
    if (report && report['Current Value'] === 'off/disable') return false;
    return null;
  },
});
```

### Custom parser example with polling

```javascript
'use strict';

const { ZwaveDevice, Util } = require('homey-zwavedriver');

class MyDimmer extends ZwaveDevice {

  async onNodeInit({ node }) {
    this.registerCapability('onoff', 'SWITCH_BINARY', {
      getOpts: { getOnStart: true },
    });

    this.registerCapability('dim', 'SWITCH_MULTILEVEL', {
      setParserV2: (value, opts) => ({
        Value: Math.round(value * 99),
        'Dimming Duration': Object.prototype.hasOwnProperty.call(opts, 'duration')
          ? Util.calculateDimDuration(opts.duration)
          : 'Factory default',
      }),
      reportParserV1: (report) => {
        if (!report || !report['Value (Raw)']) return null;
        if (report['Value (Raw)'][0] === 255) return 1;
        return report['Value (Raw)'][0] / 99;
      },
    });

    // Poll measure_power every `poll_interval` seconds (setting id, multiplied to ms)
    this.registerCapability('measure_power', 'METER', {
      getOpts: {
        pollInterval: 'poll_interval',
        pollMultiplication: 1000,
      },
    });
  }

}

module.exports = MyDimmer;
```

### System capability → Command Class map

Every pair below is implemented in `homey-zwavedriver@2.x` (`lib/system/capabilities/`). Registering one of
these needs no options at all. `Class` is the device-class-specific override folder.

| Capability | Class | Command Class | get | set | report | getOpts | Versioned parsers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `alarm_co` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_co` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_co` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_co2` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_co2` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_co2` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_contact` | — | `BASIC` | — | — | `BASIC_SET` | — | — |
| `alarm_contact` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_contact` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_contact` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_heat` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_heat` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_heat` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_motion` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_motion` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_smoke` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_smoke` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_smoke` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_tamper` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_tamper` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_tamper` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `alarm_water` | — | `NOTIFICATION` | `NOTIFICATION_GET` | — | `NOTIFICATION_REPORT` | — | — |
| `alarm_water` | — | `SENSOR_ALARM` | `SENSOR_ALARM_GET` | — | `SENSOR_ALARM_REPORT` | — | — |
| `alarm_water` | — | `SENSOR_BINARY` | `SENSOR_BINARY_GET` | — | `SENSOR_BINARY_REPORT` | — | reportV1, reportV2 |
| `dim` | — | `BASIC` | `BASIC_GET` | `BASIC_SET` | `BASIC_REPORT` | — | reportV1, reportV2 |
| `dim` | — | `SWITCH_MULTILEVEL` | `SWITCH_MULTILEVEL_GET` | `SWITCH_MULTILEVEL_SET` | `SWITCH_MULTILEVEL_REPORT` | `getOnStart` | reportV1, reportV4, setV1, setV2, setV4 |
| `dim` | `windowcoverings` | `SWITCH_MULTILEVEL` | `SWITCH_MULTILEVEL_GET` | `SWITCH_MULTILEVEL_SET` | `SWITCH_MULTILEVEL_REPORT` | `getOnStart` | reportV1, reportV4, setV1, setV2, setV4 |
| `locked` | — | `DOOR_LOCK` | `DOOR_LOCK_OPERATION_GET` | `DOOR_LOCK_OPERATION_SET` | `DOOR_LOCK_OPERATION_REPORT` | `getOnOnline` | reportV2, setV2 |
| `locked` | — | `NOTIFICATION` | — | — | `NOTIFICATION_REPORT` | — | — |
| `measure_battery` | — | `BATTERY` | `BATTERY_GET` | — | `BATTERY_REPORT` | `getOnOnline` | — |
| `measure_co` | — | `SENSOR_MULTILEVEL` | — | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_co2` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_current` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV3, getV4, reportV3, reportV4 |
| `measure_current` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_humidity` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_luminance` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_noise` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_pm2.5` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_power` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV2, getV4, reportV1, reportV2, reportV3, reportV4 |
| `measure_power` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_temperature` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | `getOnStart` + `getOnOnline` | — |
| `measure_ultraviolet` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_voltage` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV3, getV4, reportV3, reportV4 |
| `measure_voltage` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `measure_water` | — | `SENSOR_MULTILEVEL` | `SENSOR_MULTILEVEL_GET` | — | `SENSOR_MULTILEVEL_REPORT` | — | — |
| `meter_gas` | — | `METER` | `METER_GET` | — | `METER_REPORT` | — | getV2, getV4, reportV1, reportV2, reportV3 |
| `meter_power` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV2, getV4, reportV1, reportV2, reportV3, reportV4 |
| `meter_power.export` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV2, getV4, reportV1, reportV2, reportV3 |
| `meter_power.import` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV2, getV4, reportV1, reportV2, reportV3 |
| `meter_water` | — | `METER` | `METER_GET` | — | `METER_REPORT` | — | getV2, getV4, reportV1, reportV2, reportV3 |
| `onoff` | — | `BASIC` | `BASIC_GET` | `BASIC_SET` | `BASIC_REPORT` | — | reportV1, reportV2 |
| `onoff` | — | `BASIC_SET` | — | — | `BASIC_SET` | — | — |
| `onoff` | — | `SWITCH_BINARY` | `SWITCH_BINARY_GET` | `SWITCH_BINARY_SET` | `SWITCH_BINARY_REPORT` | `getOnStart` | reportV1, reportV2, setV1, setV2 |
| `onoff` | — | `SWITCH_MULTILEVEL` | `SWITCH_MULTILEVEL_GET` | `SWITCH_MULTILEVEL_SET` | `SWITCH_MULTILEVEL_REPORT` | — | reportV1, reportV4, setV2, setV4 |
| `powerFactor` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV3, getV4, reportV3, reportV4 |
| `powerReactive` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV3, getV4, reportV3, reportV4 |
| `powerTotalApparent` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV2, getV4, reportV3, reportV4 |
| `powerTotalReactive` | — | `METER` | `METER_GET` | — | `METER_REPORT` | `getOnStart` | getV4, reportV3, reportV4 |
| `target_temperature` | — | `THERMOSTAT_SETPOINT` | `THERMOSTAT_SETPOINT_GET` | `THERMOSTAT_SETPOINT_SET` | `THERMOSTAT_SETPOINT_REPORT` | `getOnStart` | — |
| `windowcoverings_set` | — | `SOUND_SWITCH` | `SOUND_SWITCH_CONFIGURATION_GET` | `SOUND_SWITCH_CONFIGURATION_SET` | `SOUND_SWITCH_CONFIGURATION_REPORT` | `getOnStart` | reportV1, setV1 |
| `windowcoverings_set` | — | `SWITCH_MULTILEVEL` | `SWITCH_MULTILEVEL_GET` | `SWITCH_MULTILEVEL_SET` | `SWITCH_MULTILEVEL_REPORT` | `getOnStart` | reportV1, reportV4, setV1, setV2, setV4 |
| `windowcoverings_state` | — | `SWITCH_BINARY` | `SWITCH_BINARY_GET` | `SWITCH_BINARY_SET` | `SWITCH_BINARY_REPORT` | — | setV1, setV2 |
| `windowcoverings_tilt_set` | — | `SWITCH_BINARY` | `SWITCH_BINARY_GET` | `SWITCH_BINARY_SET` | `SWITCH_BINARY_REPORT` | — | setV1, setV2 |
| `windowcoverings_tilt_set` | — | `SWITCH_MULTILEVEL` | `SWITCH_MULTILEVEL_GET` | `SWITCH_MULTILEVEL_SET` | `SWITCH_MULTILEVEL_REPORT` | `getOnStart` | reportV1, reportV4, setV1, setV2, setV4 |

Side effects worth knowing:

- `dim` ↔ `SWITCH_MULTILEVEL` and `dim` ↔ `BASIC` also write the `onoff` capability (when present) from both
  the set parser and the report parser.
- `measure_battery` ↔ `BATTERY` also writes `alarm_battery` (when present): `true` when
  `Battery Level === 'battery low warning'` (the capability itself then reports `1`), `false` when a
  `Battery Level (Raw)` byte is present (that byte is returned as the percentage). Any other report
  returns `null` and touches neither capability.
- `target_temperature` ↔ `THERMOSTAT_SETPOINT` uses `this.thermostatSetpointType` (default `'Heating 1'`) as
  the `Setpoint Type` for both get and set.
- `measure_temperature` ↔ `SENSOR_MULTILEVEL` converts Fahrenheit (`Level.Scale === 1`) to Celsius and drops
  the sentinel value `-999.9`.
- Window-covering inversion runs off two `type: "checkbox"` device settings, and they are **not**
  distributed the way the names suggest:
  - `invertWindowCoveringsDirection` — read by `dim` ↔ `SWITCH_MULTILEVEL` (`windowcoverings` class
    override), `windowcoverings_set` ↔ `SWITCH_MULTILEVEL`, `windowcoverings_state` ↔ `SWITCH_BINARY`
    **and** `windowcoverings_tilt_set` ↔ `SWITCH_BINARY`.
  - `invertWindowCoveringsTiltDirection` — read by `windowcoverings_tilt_set` ↔ `SWITCH_MULTILEVEL`
    only.

  Level capabilities invert with `1 - value`; `windowcoverings_state` ↔ `SWITCH_BINARY` instead swaps
  which of `'on/enable'` / `'off/disable'` means `'up'` and `'down'`, and remembers the last position
  in `this.windowCoveringsPosition` so that `'idle'` toggles it.

### Built-in Command Class payload parsers

Before your `reportParser` runs, the incoming payload is enriched for four Command Classes. Use these
`(Parsed)` fields instead of decoding buffers yourself.

| Command Class | Added fields |
| --- | --- |
| `METER` | `Properties1['Meter Type (Parsed)']` `{ value, name }`, `Properties1['Rate Type (Parsed)']` `{ value, name }`, `Meter Value (Parsed)` (scaled number), `Previous Meter Value (Parsed)`. Also repairs the v3+ `Scale 2` / `Previous Meter Value` split when the combined scale is not `7`. |
| `NOTIFICATION` | `Event (Parsed)` (and the identical `Event (Parsed 2)`) — the human-readable event name resolved from notification type + event code. |
| `SENSOR_ALARM` | `Bit Mask (Parsed)` — object keyed by `General Purpose Alarm`, `Smoke Alarm`, `CO Alarm`, `CO2 Alarm`, `Heat Alarm`, `Water Leak Alarm` with boolean values. |
| `SENSOR_MULTILEVEL` | `Sensor Value (Parsed)` — `Sensor Value` read as a signed big-endian int of `Level.Size` bytes, divided by `10 ** Level.Precision`. |

### `registerSetting(settingId, parserFn)`

Register a custom parser for a device setting. `parserFn(value, zwaveObj)` receives the new setting value and
the setting's `zwave` object from the manifest, and must return a `Buffer`, `number` or `boolean`. Non-buffer
returns are passed through the system parser afterwards; if that still does not yield a `Buffer` the write
rejects with `invalid_buffer`. The final buffer length must equal `zwave.size`, otherwise the write rejects
with `invalid_buffer_length`. (When `onSettings` drives a **non**-Z-Wave setting — one without a `zwave`
object — the registered parser is simply called as `parserFn(value)` and its return value is discarded.)

```javascript
this.registerSetting('s1_kwh_report', (newValue) => {
  const kwh = Buffer.alloc(2);
  kwh.writeUIntBE(Math.round(newValue * 100), 0, 2);
  return kwh;
});
```

The **system setting parser** (used when no custom parser is registered) does:

- `boolean` → `Buffer.from([1])` / `Buffer.from([0])`
- `number` (or numeric string) → `Buffer.alloc(size)` with `writeIntBE` when `signed !== false`, else
  `writeUIntBE`
- `Buffer` → passed through unchanged

### Configuration parameters at runtime

```javascript
// Write a parameter. `useSettingParser` defaults to true.
await this.configurationSet({ index: 13, size: 1, signed: false }, 40);

// Or reference a manifest setting id — index/size/signed are read from its `zwave` object.
await this.configurationSet({ id: 'minimum_brightness' }, 12);

// Read a parameter back.
const report = await this.configurationGet({ index: 13 });
```

| Method | Signature | Notes |
| --- | --- | --- |
| `configurationSet(options, value)` | `options: { index, size, id, signed?, useSettingParser? }` | Needs `index` **or** `id`. With `index` you must also pass `size`. With `id` and no `size`/`index`/`signed`, they are read from the manifest setting. Rejects with `missing_setting_index_or_id`, `missing_setting_size`, `invalid_setting_id`, `missing_valid_zwave_setting_object`, `missing_command_class_configuration` or `invalid_value_type`. For an **offline battery node** the promise resolves immediately and the write is queued for the next wake-up. |
| `configurationGet(options)` | `options: { index }` | Rejects with `missing_index`, `cannot_get_parameter_from_battery_node` (offline battery node) or `missing_command_class_configuration`. |
| `getManifestSettings()` | `→ any[]` | Flattened settings array (groups expanded). |
| `getManifestSetting(id)` | `→ object \| Error` | One setting object from the manifest. |

Under the hood `configurationSet` emits:

```javascript
COMMAND_CLASS_CONFIGURATION.CONFIGURATION_SET({
  'Parameter Number': index,
  Level: { Size: size, Default: false },
  'Configuration Value': parsedValueBuffer,
});
```

### Report listeners

```javascript
this.registerReportListener('CENTRAL_SCENE', 'CENTRAL_SCENE_NOTIFICATION', (report) => {
  this.log('scene', report.Properties1['Key Attributes'], 'button', report['Scene Number']);
});

this.registerMultiChannelReportListener(2, 'METER', 'METER_REPORT', (report) => {
  this.log('endpoint 2 meter', report['Meter Value (Parsed)']);
});
```

| Method | Description |
| --- | --- |
| `registerReportListener(commandClassId, commandId, triggerFn)` | Root node. `triggerFn(report)`. Logs `Invalid commandClass: <id>` and returns if the node lacks the class. |
| `registerMultiChannelReportListener(multiChannelNodeId, commandClassId, commandId, triggerFn)` | Same, on an endpoint. Logs `Invalid multi channel node <id>` when the endpoint does not exist. |

**`CENTRAL_SCENE_NOTIFICATION` special handling** in `registerReportListener`: duplicate echoes with the same
`Sequence Number` are dropped, and the numeric `Properties1['Key Attributes']` is rewritten to a string:

| Value | String |
| --- | --- |
| 0 | `Key Pressed 1 time` |
| 1 | `Key Released` |
| 2 | `Key Held Down` |
| 3 | `Key Pressed 2 times` |
| 4 | `Key Pressed 3 times` |
| 5 | `Key Pressed 4 times` |
| 6 | `Key Pressed 5 times` |

Anything else logs `Received unknown central scene notification report`.

### Multi-channel endpoints in code

`this.node.isMultiChannelNode` tells a sub-device apart from the root device — both run the **same**
`device.js`. Register root-node capabilities against endpoints with `multiChannelNodeId`.

```javascript
'use strict';

const { ZwaveDevice } = require('homey-zwavedriver');

class FibaroDoubleSwitch extends ZwaveDevice {

  async onNodeInit({ node }) {
    if (!this.node.isMultiChannelNode) {
      // Root device: bind to endpoint 1
      this.registerCapability('onoff', 'SWITCH_BINARY', { multiChannelNodeId: 1 });
      this.registerCapability('measure_power', 'METER', { multiChannelNodeId: 1 });
      this.registerCapability('meter_power', 'METER', { multiChannelNodeId: 1 });

      if (this.hasCommandClass('CENTRAL_SCENE')) {
        this.registerReportListener('CENTRAL_SCENE', 'CENTRAL_SCENE_NOTIFICATION', (report) => {
          this.log('scene', report['Scene Number'], report.Properties1['Key Attributes']);
        });
      }
    } else {
      // Sub-device (endpoint 2): capabilities resolve on its own node
      this.registerCapability('onoff', 'SWITCH_BINARY');
      if (this.hasCapability('meter_power')) this.registerCapability('meter_power', 'METER');
      if (this.hasCapability('measure_power')) this.registerCapability('measure_power', 'METER');
    }
  }

}

module.exports = FibaroDoubleSwitch;
```

### Utility methods on `ZwaveDevice`

| Method | Returns | Description |
| --- | --- | --- |
| `hasCommandClass(commandClassId, { multiChannelNodeId })` | `boolean` | Whether the root node (or the endpoint) implements the class. Throws `multi_channel_node_id_must_be_number` if the option is not a number. |
| `getCommandClass(commandClassId, { multiChannelNodeId })` | `ZwaveCommandClass \| Error` | The raw command-class object, or an `Error` (`missing_command_class_<id>` / `multi_channel_node_<n>_is_missing_command_class_<id>`). |
| `getMultiChannelNodeIdsByDeviceClassGeneric(deviceClassGeneric)` | `number[]` | Endpoint ids whose `deviceClassGeneric` matches. |
| `executeCapabilitySetCommand(capabilityId, commandClassId, value, opts)` | `Promise<any>` | Runs the registered set command manually. |
| `refreshCapabilityValue(capabilityId, commandClassId)` | `Promise<any>` | One-shot GET + report parse. For repeated refreshes use `getOpts.pollInterval` instead. |
| `meterReset({ multiChannelNodeId }, options)` | `Promise<void>` | `METER_RESET`. For `COMMAND_CLASS_METER` version ≥ 6 and an empty `options`, a default payload resetting the electric kWh meter to `0` is used. Throws `missing_meter_reset_command`, or the result when it is not `TRANSMIT_COMPLETE_OK`. |
| `printNodeSummary()` | `void` | One-line summary (node id, manufacturer/product ids, firmware & hardware version, secure flag, battery). Called automatically on init. |
| `printNode()` | `void` | Full dump: device classes, every Command Class with its `version` and its commands, plus all multi-channel nodes. |
| `enableDebug()` / `disableDebug()` | `void` | Log every incoming report on the root node and on all multi-channel nodes. |

### Set-command results

`_setCapabilityValue` (invoked through the capability listener) returns:

- `'IGNORED'` when the set parser returned `null`
- `'TRANSMIT_QUEUED'` when the node is a battery node that is currently offline — the command is sent later
  and errors are logged as `queued setCapabilityValue (<capabilityId>) failed`
- otherwise the raw command result

### `Util` helpers

```javascript
const { Util } = require('homey-zwavedriver');
```

| Helper | Description |
| --- | --- |
| `calculateDimDuration(durationMs, { maxValue })` | Milliseconds → Z-Wave duration byte. `0–127` s maps 1:1; `128–253` means 1–126 minutes; `254` is the max; a non-number returns `0xff` (factory default). `maxValue` defaults to `254`. |
| `calculateZwaveDimDuration(durationMs, opts)` | Deprecated since v1.0.0 alias of `calculateDimDuration`. |
| `mapValueRange(inputStart, inputEnd, outputStart, outputEnd, input)` | Linear range remap, clamped to the input range. Returns `null` if any argument is not a number. |
| `convertRGBToCIE`, `convertHSVToCIE`, `convertHSVToRGB`, `convertRGBToHSV` | Colour-space conversions. |

### `ZwaveLightDevice`

For `class: "light"` devices with `COMMAND_CLASS_SWITCH_COLOR`. It implements the full expected light
behaviour, so usually you only call `super.onNodeInit({ node })`.

```javascript
'use strict';

const { ZwaveLightDevice } = require('homey-zwavedriver');

class MyRgbwLight extends ZwaveLightDevice {

  async onNodeInit({ node }) {
    await super.onNodeInit({ node });
    // extra driver-specific code here
  }

}

module.exports = MyRgbwLight;
```

Requirements and behaviour:

- The driver **must** have all of `onoff`, `dim`, `light_mode`, `light_hue`, `light_saturation`,
  `light_temperature`; a missing one logs `Missing capability: <id>` and aborts init.
- `onoff` + `dim` bind to `SWITCH_MULTILEVEL` when present, otherwise fall back to `BASIC`.
- `light_hue` + `light_saturation` are handled by a `registerMultipleCapabilityListener`, converted with
  `Util.convertHSVToRGB` and written via `SWITCH_COLOR_SET` (components `0`=warm, `1`=cold, `2`=red,
  `3`=green, `4`=blue).
- `light_temperature` maps to warm `= value * 255` and cold `= (1 - value) * 255`.
- `light_mode` is registered on `SWITCH_COLOR` with `set: 'SWITCH_COLOR_SET'`.
- Durations are supported for `dim` (SWITCH_MULTILEVEL ≥ V2), `light_hue`, `light_saturation` and
  `light_temperature` (SWITCH_COLOR ≥ V2); the factory default duration byte is `255`.
- On boot it reads all five colour components with `SWITCH_COLOR_GET` and derives `light_mode`,
  `light_hue` / `light_saturation` or `light_temperature`.

Recommended `capabilitiesOptions` in `driver.compose.json`:

```json
"capabilitiesOptions": {
  "onoff": { "setOnDim": false },
  "dim": { "opts": { "duration": true } },
  "light_hue": { "opts": { "duration": true } },
  "light_saturation": { "opts": { "duration": true } },
  "light_temperature": { "opts": { "duration": true } }
}
```

## Raw Z-Wave API

Use `homey-zwavedriver` where possible; drop to the raw API only when you must.

### `ManagerZwave` — `this.homey.zwave`

| Method | Returns | Description |
| --- | --- | --- |
| `getNode(device)` | `Promise<ZwaveNode>` | Create a `ZwaveNode` instance for a `Device`. |

### `ZwaveNode`

| Property | Type | Description |
| --- | --- | --- |
| `battery` | `boolean` | Whether the node is battery operated. |
| `CommandClass` | `Object<string, ZwaveCommandClass>` | Command class instances, keyed `COMMAND_CLASS_<NAME>`. |
| `MultiChannelNodes` | `Object<string, ZwaveNode>` | Endpoint nodes, keyed by endpoint id. |
| `deviceClassBasic` | `string` | Basic device class. |
| `deviceClassGeneric` | `string` | Generic device class. |
| `deviceClassSpecific` | `string` | Specific device class. |
| `firmwareId` | `number` | Firmware identifier. |
| `isMultiChannelNode` | `boolean` | Whether this node is a multi-channel (endpoint) node. |
| `multiChannelNodeId` | `number` | Endpoint id, when this is a multi-channel node. |
| `manufacturerId` | `Object` | Manufacturer id in its `.value` property. |
| `productId` | `Object` | Product id in its `.value` property. |
| `productTypeId` | `Object` | Product type id in its `.value` property. |
| `nodeId` | `number` | Node id within the Z-Wave network. |
| `online` | `boolean` | Whether the node is online. |

| Method | Returns | Description |
| --- | --- | --- |
| `sendCommand({ commandClassId, commandId, params })` | `Promise<void>` | Send a raw command. `commandClassId` and `commandId` are numbers; `params` is an optional `Buffer`. |

| Event | Payload | Description |
| --- | --- | --- |
| `nif` | `Buffer` | A Node Information Frame was sent. |
| `online` | `boolean` | A battery node changed online/offline status. |
| `unknownReport` | `Buffer` | The node received an unknown command. |

### `ZwaveCommandClass`

Commands are function properties on the instance (their names depend on the Command Class). The instance also
carries a `version` number. It emits one event:

| Event | Parameters | Description |
| --- | --- | --- |
| `report` | `(command, report)` — `command` is `{ value: number, name: string }`, `report` is the payload object (contents depend on the Command Class) | A report was received. |

```javascript
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {

  async onInit() {
    const node = await this.homey.zwave.getNode(this);

    // Send a command
    await node.CommandClass.COMMAND_CLASS_BASIC.BASIC_SET({ Value: true });

    // Get the BASIC status
    node.CommandClass.COMMAND_CLASS_BASIC.BASIC_GET()
      .then((result) => {
        if (result.Value) {
          this.log('Device is turned on');
        } else {
          this.log('Device is turned off');
        }
      })
      .catch(this.error);

    // Battery nodes emit 'online' when available; you have ~10s to send commands
    node.on('online', (online) => {
      this.log(online ? 'Device is online' : 'Device is offline');
    });

    // Report events
    node.CommandClass.COMMAND_CLASS_BASIC.on('report', (command, report) => {
      this.log(command.name); // e.g. BASIC_REPORT
      this.log(report);       // e.g. { Value: true }
    });
  }

}

module.exports = Device;
```

### TypeScript and Python

The same manager exists in the TypeScript and Python runtimes. In TypeScript the command classes are
untyped by default; cast through the `ZwaveCommandClass` interface exported from `homey`:

```typescript
// /drivers/<driver_id>/device.mts
import Homey, { ZwaveCommandClass } from 'homey';

interface CommandClassBasic extends ZwaveCommandClass {
  BASIC_GET: () => Promise<{ Value: boolean }>;
  BASIC_SET: (args: { Value: unknown }) => Promise<void>;
}

export default class Device extends Homey.Device {

  async onInit(): Promise<void> {
    const node = await this.homey.zwave.getNode(this);
    const basic = node.CommandClass['COMMAND_CLASS_BASIC'] as CommandClassBasic;

    const result = await basic.BASIC_GET();
    this.log(result.Value ? 'Device is turned on' : 'Device is turned off');

    node.on('online', (online: boolean) => this.log(online ? 'online' : 'offline'));
    node.CommandClass['COMMAND_CLASS_BASIC'].on('report', (command, report) => {
      this.log(command.name, report);
    });
  }

}
```

Python uses snake_case and does not expose commands as attributes — send them by name:

```python
# /drivers/<driver_id>/device.py
from homey import device


class Device(device.Device):
    async def on_init(self) -> None:
        node = await self.homey.zwave.get_node(self)

        await node.command_classes["COMMAND_CLASS_BASIC"].send_command(
            "BASIC_SET", {"Value": True}
        )

        def on_report(command, report) -> None:
            self.log(command.name)  # e.g. BASIC_REPORT
            self.log(report)        # e.g. { Value: true }

        node.command_classes["COMMAND_CLASS_BASIC"].on("report", on_report)


homey_export = Device
```

| Concept | JavaScript | Python |
| --- | --- | --- |
| Get the node | `await this.homey.zwave.getNode(this)` | `await self.homey.zwave.get_node(self)` |
| Command class map | `node.CommandClass['COMMAND_CLASS_X']` | `node.command_classes["COMMAND_CLASS_X"]` |
| Send a command | `cc.BASIC_SET({ Value: true })` | `await cc.send_command("BASIC_SET", {"Value": True})` |
| Events | `node.on('online', fn)` / `cc.on('report', fn)` | `node.on("online", fn)` / `cc.on("report", fn)` |

`homey-zwavedriver` is a Node.js module, so Python drivers must use the raw API above. TypeScript
drivers run on Node and can require it, but it ships no type declarations.

## Flow card device filters

Restrict a Flow card to root nodes or to multi-channel sub-devices with the `$filter` property in
`driver.flow.compose.json`:

```json
{
  "triggers": [
    { "id": "scene_s1", "title": { "en": "Left switch scene (S1)" }, "$filter": "flags=zwaveRoot" }
  ],
  "actions": [
    { "id": "endpoint_action", "title": { "en": "Endpoint action" }, "$filter": "flags=zwaveMultiChannel" }
  ]
}
```

| Filter | Targets |
| --- | --- |
| `flags=zwaveRoot` | Root node devices only. |
| `flags=zwaveMultiChannel` | Multi-channel node devices only. |

Filters combine with `&`, alternatives with `|`, multi-value requirements with `,` — e.g.
`"class=socket|light&capabilities=onoff,dim"`.

## OTA firmware updates

Homey implements the **Firmware Update Metadata Command Class**: your app ships the firmware files and Homey
installs them.

> Supported since Homey firmware **v13.2.0**, on Homey Pro (Early 2023, 2026, mini), Homey Self-Hosted Server
> and Homey Cloud. Users need Homey Mobile App **v9.10.0** or higher to start updates.

### Generating the manifest with the CLI

```bash
homey app driver firmware --driver ./drivers/<driver_id> --firmware ./AwesomeSensor_v1.3.4.bin
```

Requires `homey` CLI **v4.3.0** or higher, and a Homey Compose app (the command offers to migrate otherwise).
Both flags are mandatory; `--firmware` may be repeated for multi-target updates. The driver must have a
`zwave` (or `zigbee`) object, otherwise:
`Driver <id> is not a Zigbee or Z-Wave driver. Firmware updates are only supported for Zigbee or Z-Wave drivers.`

The command prompts for, in order:

1. **Changelog** (non-empty string).
2. *"Should this update only apply to devices within a certain firmware version range?"* → if yes, a semver
   constraint for `applicableTo` (e.g. `<2.0.0`), validated with `semver.validRange`.
3. Which **manufacturer IDs**, **product type IDs** and **product IDs** from the driver manifest this update
   targets (multi-select, defaults to all).
4. The **version** of the firmware update (must be valid semver).
5. Per file: the **chip target ID** (integer 0–255, default `0`) and the **region** (list, default
   *None/Global*).
6. On a **new** file only: *"Does this device go into a sleep mode?"* → if yes, a wake instruction, stored as
   `wakeInstruction: { en: … }`.

It copies each firmware file to `/drivers/<driver_id>/assets/firmware/<file name>`, computes the `sha256`
integrity and the byte `size`, appends the update to `driver.firmware.compose.json` and prints
`Firmware update created in ...`.

### `driver.firmware.compose.json`

Homey Compose merges this file into the compiled `app.json` as `drivers[].firmwareUpdates`.

```json
{
  "wakeInstruction": {
    "en": "Hold the internal button for three seconds."
  },
  "updates": [
    {
      "version": "1.3.0",
      "changelog": {
        "en": "- Fixes issue X\n- Adds feature Y\n- Deprecates feature Z"
      },
      "applicableTo": "<2.0.0",
      "device": {
        "manufacturerId": 1234,
        "productTypeId": [1, 2],
        "productId": [3, 4]
      },
      "files": [
        {
          "targetId": 0,
          "size": 262144,
          "name": "AwesomeSensor_v1.3.4.bin",
          "integrity": "sha256:dac89981aeb5352a8ddce9fbb5ab3ad5bff88d17e2f7937cc90947301ccfedd2"
        }
      ]
    }
  ]
}
```

#### Root fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `updates` | `array` (min 1) | yes | All firmware updates for this driver's devices. |
| `wakeInstruction` | i18n object | no | How the user makes a Sleepy End Device (battery device) active to start the update. Not needed for always-on devices. |
| `reportTimeout` | `number` | no | Present in the app schema; not covered by the public documentation. |
| `minWaitTime` | `number` | no | Present in the app schema; not covered by the public documentation. |
| `verifyPostUpdateWithNop` | `false` | no | Present in the app schema; only the value `false` is accepted. |
| `nopRetryInterval` | `number` | no | Present in the app schema; not covered by the public documentation. |
| `nopMaxRetries` | `number` | no | Present in the app schema; not covered by the public documentation. |

The root object is `additionalProperties: false` — those six keys plus `updates` are all that is accepted.
`wakeInstruction` is an `i18nObject`, which the schema defines as *either* a non-empty plain string *or* an
object that must contain `en`; the CLI always writes the object form.

#### `updates[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `version` | `string` | yes | Firmware version, `<major>.<minor>.<patch>`. Must be valid semver. |
| `changelog` | i18n object \| `string` | yes | Short description of the changes. As an object it must contain at least `en`; a bare non-empty string is also valid (`i18nObject` is a `oneOf`), and `homey app validate` accepts both. |
| `device` | `object` | yes | Which devices this update targets. |
| `files` | `array` (min 1) | yes | The firmware files of this update. |
| `applicableTo` | `string` | no | Semver **range** deciding whether the device's current version can install this update (e.g. `>1.2.3`). Must be a valid semver range. |

`additionalProperties: false` — no other keys are accepted. The schema types `version` and `applicableTo` as
plain strings; the semver / semver-range checks are done by `homey app validate` (homey-lib), not by the
schema. The Zigbee-only per-update keys have no Z-Wave equivalent here — do not carry them over.

#### `updates[].device`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `manufacturerId` | `number` \| `number[]` | yes | Must be a subset of the driver's `zwave.manufacturerId`. |
| `productTypeId` | `number` \| `number[]` | yes | Must be a subset of the driver's `zwave.productTypeId`. |
| `productId` | `number` \| `number[]` | yes | Must be a subset of the driver's `zwave.productId`. |
| `hardwareVersion` | `number` \| `number[]` | no | Restricts the update to specific hardware versions; must match the device's hardware version reported through the Version Command Class. |

`additionalProperties: false` — those four keys only. A driver can target multiple devices; `device` narrows
an update to a subset of them. Note the schema itself does not enforce the subset relation with the driver's
`zwave.*` ids — `homey app validate` does (see below).

#### `updates[].files[]`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `targetId` | `number` | yes | Target chip of this file. `0` when there is only one file. CLI accepts 0–255. |
| `name` | `string` | yes | File name only, **no sub-directories**. The file lives in `/drivers/<driver_id>/assets/firmware/<name>`. |
| `size` | `number` | yes | File size in bytes; must match the file on disk exactly. |
| `integrity` | `string` | yes | `<hash_name>:<hex_encoded_hash>`. |
| `region` | `string` | no | Z-Wave region this file applies to. Omit for a global file. |

`additionalProperties: false` — those five keys only. `targetId` is a plain `number` in the schema (the
0–255 bound is the CLI prompt's own validation), and `region` is a plain `string` with **no enum**, so the
region table below is the CLI's picker list rather than a schema constraint — a typo like `"eu"` validates.
The Zigbee file keys (`manufacturerCode`, `imageType`, `fileVersion`, …) belong to
`zigbee-firmware-update-file` and are rejected here.

Supported `integrity` hash names: `sha256`, `sha384`, `sha512`, `sha512-256`, `sha3-256`, `sha3-384`,
`sha3-512`, `blake2b512`, `blake2s256`. Pattern: `^(blake2b512|blake2s256|sha256|sha384|sha512|sha512-256|sha3-256|sha3-384|sha3-512):[0-9a-fA-F]+$`

#### Regions

| Value | Region | Frequencies |
| --- | --- | --- |
| `ANZ` | Australia / New Zealand | 919.8 MHz / 921.4 MHz |
| `CN` | China | 868.4 MHz |
| `EU` | Europe | 868.4 MHz / 869.85 MHz |
| `HK` | Hong Kong | 919.8 MHz |
| `IL` | Israel | 916 MHz |
| `IN` | India | 865.2 MHz |
| `JP` | Japan | 922.5 MHz / 923.9 MHz / 926.3 MHz |
| `KR` | Korea | 920.9 MHz / 921.7 MHz / 923.1 MHz |
| `RU` | Russia | 869 MHz |
| `US` | United States of America | 908.4 MHz / 916 MHz |

A `US_LR` entry (United States, Z-Wave *and* Long Range) exists in the CLI source but is commented out, so
the prompt never offers it. Since the schema does not constrain `region`, hand-writing `"US_LR"` passes
validation — do not, unless Athom has confirmed Homey handles it.

> **Danger:** omitting `region` when it is required can make Homey install a firmware for the wrong region,
> rendering the device unusable in the user's region.

### How Homey reads the device's current version

| Device support | Derivation | Format |
| --- | --- | --- |
| `VERSION_ZWAVE_SOFTWARE_GET` | `Application Version` field of `VERSION_ZWAVE_SOFTWARE_REPORT` | `<byte_1>.<byte_2>.<byte_3>` |
| only `VERSION_GET` | `Application Version` and `Application Sub Version` of `VERSION_REPORT`; patch is always `0` | `<application_version>.<application_sub_version>.0` |

### Update selection

1. `updates[].device` must match the device's reported `manufacturerId`, `productTypeId` and `productId`.
2. One of the update's files must match the currently used Z-Wave region.
3. The device's current version must satisfy the update's `applicableTo`.

If multiple updates match, the one with the highest `version` wins.

**Multiple files:** for devices with more than one updatable chip, add several files with different
`targetId`s. Homey sends the next `targetId` automatically once the previous transfer completed.

### Validation performed by `homey app validate`

- `firmwareUpdates` requires the driver to have a `zwave` (or `zigbee`) object.
- `version` must be valid semver; `applicableTo` must be a valid semver range.
- `changelog` must be a string or contain `changelog.en`.
- `files` must contain at least one entry.
- `device.manufacturerId` / `productTypeId` / `productId` must each be non-empty **and** be subsets of the
  driver's `zwave.*` values, otherwise:
  `... has a <field> that does not match the driver zwave.<field>`.
- `files[].name` must not contain (sub)directories.
- The file must exist at `/drivers/<driver_id>/assets/firmware/<name>` (case-sensitive).
- The file's actual `integrity` and byte `size` must match — otherwise `integrity mismatch` /
  `size mismatch: expected <n>, got <m>`.
- Two files in one update may not share the same `targetId` + `region` combination:
  `... has multiple files with the same targetId and region`.

Homey performs **no** pre-processing and **no** format validation of the binary — Z-Wave has no
specification-defined firmware file format. The file you ship must be directly transferable to the device.

Firmware files are stored separately from your app when you upload it; Homey downloads a file only when it
starts installing an update.

### Update failures

Homey treats an update as failed when:

- **Explicit abort** — the device reports an error status during image transfer.
- **Stalled transfer** — the device stops requesting firmware chunks before the transfer completes.
- **No reconnection** — the device does not rejoin the Z-Wave network in time after the file transferred.

The user is notified on the firmware-update screen and can retry.

### Before shipping firmware

- **Device targeting:** verify every file maps to the correct device(s). A wrong file can cause irreversible
  damage or brick the device.
- **End-to-end testing:** run the complete update flow on the real hardware — initiate, transfer, complete.
- **Validation before release:** never ship an untested firmware update.

## Gotchas

- **`homey-zwavedriver` is SDK v3 only.** The SDK v2 predecessor is `homey-meshdriver`. Do not mix them.
- **Drop the `COMMAND_CLASS_` prefix** for `homey-zwavedriver` (`'SWITCH_BINARY'`), but keep it for raw node
  access (`node.CommandClass.COMMAND_CLASS_SWITCH_BINARY`).
- **`requireSecure` opts into S0 only.** S2 is used automatically whenever the device supports it; setting
  `requireSecure: true` is about legacy Security 0 and adds significant communication overhead. Homey Pro
  (2016–2019) grants only the highest requested S2 key, not all of them.
- **Pairing-time properties need re-pairing.** `learnmode`, `defaultConfiguration`, `associationGroups`,
  `wakeUpInterval`, `multiChannelNodes` and `requireSecure` are applied during inclusion — existing devices
  must be removed and re-added for changes to take effect.
- **Half the `zwave` block is unvalidated.** The `zwaveDevice` schema only declares `manufacturerId`,
  `productTypeId`, `productId`, `learnmode`, `associationGroups`, `associationGroupsMultiChannel`,
  `associationGroupsOptions`, `wakeUpInterval` and `defaultConfiguration`, and it is not
  `additionalProperties: false`. `requireSecure`, `unlearnmode`, `multiChannelNodes`,
  `productDocumentation` and the `zwaveAlliance*` keys — and any typo in them — pass `homey app validate`
  silently. Spell them yourself, character for character; a misspelled `requireSecure` simply never applies.
- **Never `getOnStart` on battery devices.** The library refuses it and logs
  `do not use getOnStart for battery devices`. Use `getOnOnline` instead.
- **Battery-node writes are queued, not sent.** When `node.battery === true && node.online === false`,
  `configurationSet()` resolves immediately and capability sets return `'TRANSMIT_QUEUED'`; the command
  actually reaches the device on its next wake-up. `configurationGet()` on an offline battery node rejects
  with `cannot_get_parameter_from_battery_node`.
- **Setting values are signed by default.** `zwave.signed` defaults to `true`. A parameter documented as
  `0–255` in a 1-byte field needs `"signed": false`, or validation fails with `Value cannot be signed: …`.
- **Setting ids may not start with `zw_`** (nor `homey:`, `zb_`, `mtr_`, `thread_`, `zone_`, `energy_`,
  `satellite_mode_`, `homekit_`). Homey owns `zw_*` and populates them itself.
- **Duplicate `zwave.index` in one driver** produces a validation warning; each configuration parameter may be
  mapped once.
- **`ZwaveDevice` already implements `onSettings()` and `onDeleted()`.** If you override either, call
  `super` — otherwise configuration writes stop working, or node listeners and poll timeouts leak.
- **A report parser returning `null` is a no-op**, not a value. Use `null` to ignore reports that don't apply
  (wrong scale, wrong sensor type, wrong notification event) — the system parsers rely on this heavily.
- **`reportParser` does not automatically override the system parser.** Versioned system parsers
  (`reportParserV1`…`V4`) win unless you pass `reportParserOverride: true` alongside your `reportParser`.
- **Root and endpoint share one `device.js`.** Branch on `this.node.isMultiChannelNode`, and use
  `{ multiChannelNodeId: n }` to bind root-device capabilities to an endpoint.
- **`registerCapability` fails silently-ish** when the command class is missing: it logs
  `CommandClass: <id> in main node undefined` and returns. Guard with `hasCommandClass()` where the device
  line varies.
- **Use the built-in `(Parsed)` fields.** `Meter Value (Parsed)`, `Sensor Value (Parsed)`,
  `Event (Parsed)` and `Bit Mask (Parsed)` are added before your report parser runs; decoding the raw buffers
  yourself duplicates scale/precision logic.
- **`CENTRAL_SCENE_NOTIFICATION` echoes are de-duplicated** by `Sequence Number` and `Key Attributes` is
  rewritten to a string — write Flow argument ids like `'Key Pressed 2 times'`, not numbers.
- **Multi-channel drivers need Flow filters.** Without `"$filter": "flags=zwaveRoot"` (or
  `flags=zwaveMultiChannel`) scene/meter cards show up on every endpoint.
- **`homey app driver firmware` fills in `size`, `name` and `integrity`** — you supply `targetId`, region,
  version, changelog and (optionally) `applicableTo`. Editing the binary afterwards without regenerating
  breaks validation with an integrity/size mismatch.
- **Firmware `size` must match the file byte-for-byte.** Homey validates the on-disk size for Z-Wave (there is
  no OTA header to check, unlike Zigbee).
- **Homey Cloud supports Z-Wave.** `"connectivity": ["zwave"]` is allowed for `"platforms": ["cloud"]`
  drivers. The connectivity values `lan`, `matter` and `rf868` are the ones rejected on `cloud`
  (`Platform 'cloud' does not support 'lan', 'matter' or 'rf868'.`).
- **`this.homey.setTimeout` / `this.homey.setInterval`** — use the Homey-scoped timers so they are cleared on
  uninit; always `.catch(this.error)` promises started in `onNodeInit`.

## Example apps

- <https://github.com/athombv/com.fibaro-example> — multi-channel nodes, central scene, meter reset,
  `registerSetting`
- <https://github.com/athombv/com.danalock-example> — `requireSecure`, `productDocumentation`, lock

## Sources

- <https://apps.developer.homey.app/wireless/z-wave>
- <https://apps.developer.homey.app/wireless/z-wave/z-wave-firmware-updates>
- <https://apps.developer.homey.app/the-basics/devices/settings>
- <https://apps.developer.homey.app/the-basics/flow>
- <https://apps-sdk-v3.developer.homey.app/ManagerZwave.html>
- <https://apps-sdk-v3.developer.homey.app/ZwaveNode.html>
- <https://apps-sdk-v3.developer.homey.app/ZwaveCommandClass.html>
- <https://athombv.github.io/node-homey-zwavedriver/> (`ZwaveDevice`, `ZwaveLightDevice`, `Util`)
- <https://github.com/athombv/node-homey-zwavedriver>
- <https://z-wavealliance.org/development-resources-overview/z-wave-command-classes/>
- <https://z-wavealliance.org/development-resources-overview/specification-for-developers/>
- <https://products.z-wavealliance.org/>
