# SDK Migration & Breaking Changes

Everything about moving an existing Homey app forward: the complete SDK v2 → v3 API mapping, the
Node.js 22 runtime upgrade, the Homey v6 (BLE) changelog, and the rules + code patterns for shipping
changes to a **live** app without breaking users' devices and Flows.

Related: `references/app-and-manifest.md` (manifest keys, Homey Compose), `references/capabilities.md`
(capability ids and options), `references/flow-cards.md` (card definitions), `references/pairing.md`
(`PairSession`), `references/wireless-zwave.md` / `references/wireless-zigbee.md` (driver libraries),
`references/cli-and-tooling.md` (CLI, validation, ESM, TypeScript), `references/publishing.md`
(Test/Live channels, rollbacks), `references/ecosystem-and-ci.md` (npm package versions).

---

## 1. Is my change breaking?

The official list of situations that "might result in breaking existing functionality for users":

| Change | Breaking? | Safe strategy |
| --- | --- | --- |
| Removing a driver capability | **Yes** | Remove from the manifest only; keep the capability listener. §6.3 |
| Adding a driver capability | **Yes** (paired devices don't get it) | Add to manifest **and** guarded `addCapability()` in `onInit`. §6.2 |
| Changing or removing a Flow card | **Yes** | `"deprecated": true` + new card; keep the old run listener. §6.5 |
| Changing a driver's device class | **Yes** | Guarded `setClass()`; accept that class-dependent Flows may break. §6.6 |
| Removing a driver | **Yes** | `"deprecated": true` on the driver manifest. §6.7 |
| Renaming a driver folder (= driver id) | **Yes** | Don't. Deprecate the old driver and add a new one. §6.7 |

> Publishing breaking changes is in general **not allowed**. Homey users expect that their devices and
> Flows continue to work after an app update, and almost all users have automatic app updates enabled.

Two SDK notes that drive the patterns below:

* `Device#addCapability()`, `Device#removeCapability()` and `Device#setCapabilityOptions()` are all
  documented as **"an expensive method so use it only when needed"** — always guard them.
* `Device#removeCapability()` and `Device#setClass()` are documented as: *"Any Flow that depends on
  this capability / class will become broken."*

---

## 2. SDK v2 → v3: manifest and preconditions

SDK v3 was introduced in **Homey 5.0.0**. It removes the dual callback/promise support and allows
`async/await` everywhere.

```json
{
  "sdk": 3,
  "compatibility": ">=5.0.0"
}
```

`sdk` in the app manifest schema is a number, minimum `1`, maximum `3`, default `3`.

| Fact | Detail |
| --- | --- |
| SDK v1 | **Discontinued.** Apps using SDK v1 are disabled starting with Homey 5.0.0. |
| SDK v2 | Still loads on old firmware, but is not supported on Homey Cloud and cannot use the v3 libraries. |
| Homey Cloud | **Only SDK v3 is supported on Homey Cloud.** Make the app SDK v3 before adding `"platforms": ["local", "cloud"]`. |
| Zigbee | Zigbee apps built for SDK v2 **must** be updated to SDK v3 to run on Homey v5.0.0 and higher (new Zigbee stack). |

### 2.1 Library replacements

The SDK v2 versions of the Homey app libraries are **not** compatible with SDK v3.

| SDK v2 package | SDK v3 package | Notes |
| --- | --- | --- |
| `homey-meshdriver` (Z-Wave) | `homey-zwavedriver` | Z-Wave only. Breaking changes kept to a minimum. §2.12 |
| `homey-meshdriver` (Zigbee) | `homey-zigbeedriver` + `zigbee-clusters` | Zigbee only. `zigbee-clusters` holds all cluster definitions and supports custom clusters. §2.13 |
| `homey-oauth2app` | `homey-oauth2app` (SDK v3 release) | Upgrade to a version that supports SDK v3. |
| `homey-rfdriver` | `homey-rfdriver` (SDK v3 release) | The current module explicitly "requires Homey Apps SDK v3". |
| `homey-log` | `homey-log` (SDK v3 release) | See `references/ecosystem-and-ci.md` for exact versions. |

```bash
npm install --save homey-zigbeedriver zigbee-clusters
npm uninstall homey-meshdriver
```

---

## 3. SDK v2 → v3: the Homey instance moved

In SDK v2 you accessed managers through the module: `const Homey = require('homey'); Homey.ManagerFlow…`.
In SDK v3 the `homey` module only exports the **classes** (`Homey.App`, `Homey.Driver`, `Homey.Device`),
plus `Homey.env` and `Homey.manifest`. Every manager lives on **`this.homey`**, a property set on your
App, Driver and Device instances (and passed into API handlers).

### 3.1 Complete manager mapping

The rule is mechanical: `Homey.<ManagerClass>` → `this.homey.<property>`.

| SDK v2 | SDK v3 | Class |
| --- | --- | --- |
| `Homey.ManagerApi` | `this.homey.api` | `ManagerApi` |
| `Homey.ManagerApps` | `this.homey.apps` | `ManagerApps` |
| `Homey.ManagerArp` | `this.homey.arp` | `ManagerArp` |
| `Homey.ManagerAudio` | `this.homey.audio` | `ManagerAudio` |
| `Homey.ManagerBLE` | `this.homey.ble` | `ManagerBLE` |
| `Homey.ManagerClock` | `this.homey.clock` | `ManagerClock` |
| `Homey.ManagerCloud` | `this.homey.cloud` | `ManagerCloud` |
| `Homey.ManagerCron` | **removed** — use `this.homey.setTimeout` / `setInterval` | — |
| `Homey.ManagerDiscovery` | `this.homey.discovery` | `ManagerDiscovery` |
| `Homey.ManagerDrivers` | `this.homey.drivers` | `ManagerDrivers` |
| `Homey.ManagerFlow` | `this.homey.flow` | `ManagerFlow` |
| `Homey.ManagerGeolocation` | `this.homey.geolocation` | `ManagerGeolocation` |
| `Homey.ManagerI18n` | `this.homey.i18n` (and the shortcut `this.homey.__()`) | `ManagerI18n` |
| `Homey.ManagerImages` | `this.homey.images` | `ManagerImages` |
| `Homey.ManagerInsights` | `this.homey.insights` | `ManagerInsights` |
| `Homey.ManagerLedring` | `this.homey.ledring` | `ManagerLedring` |
| `Homey.ManagerNFC` | `this.homey.nfc` | `ManagerNFC` |
| `Homey.ManagerNotifications` | `this.homey.notifications` | `ManagerNotifications` |
| `Homey.ManagerRF` | `this.homey.rf` | `ManagerRF` |
| `Homey.ManagerSettings` | `this.homey.settings` | `ManagerSettings` |
| `Homey.ManagerSpeechInput` | `this.homey.speechInput` | `ManagerSpeechInput` |
| `Homey.ManagerSpeechOutput` | `this.homey.speechOutput` | `ManagerSpeechOutput` |
| `Homey.ManagerZigBee` | `this.homey.zigbee` | `ManagerZigBee` |
| `Homey.ManagerZwave` | `this.homey.zwave` | `ManagerZwave` |

Non-manager members that also moved onto the instance: `this.homey.app` (pointer to the App instance),
`this.homey.manifest`, `this.homey.env`, `this.homey.version`, `this.homey.platform`,
`this.homey.platformVersion`, `this.homey.platformFeatures`, `this.homey.hasFeature()`,
`this.homey.hasPermission()`, `this.homey.log()`, `this.homey.error()`,
`this.homey.setTimeout/setInterval/clearTimeout/clearInterval`, and the events `unload`, `memwarn`,
`cpuwarn`.

> `Homey.env` and `Homey.manifest` remain available on the **module** as well — they are the only two
> non-class exports that survived.

### 3.2 No more create-and-register

Resources are no longer constructed with `new` and `register()`; you ask a manager for them.

| SDK v2 | SDK v3 |
| --- | --- |
| `new Homey.FlowCardTrigger('id').register()` | `this.homey.flow.getTriggerCard('id')` |
| `new Homey.FlowCardTriggerDevice('id').register()` | `this.homey.flow.getDeviceTriggerCard('id')` |
| `new Homey.FlowCardCondition('id').register()` | `this.homey.flow.getConditionCard('id')` |
| `new Homey.FlowCardAction('id').register()` | `this.homey.flow.getActionCard('id')` |
| `new Homey.FlowToken(...).register()` | `await this.homey.flow.createToken(...)` / `getToken()` / `unregisterToken()` |
| `new Homey.Image(); image.register()` | `await this.homey.images.createImage()` (also `getImage()`, `unregisterImage()`) |
| `Homey.ManagerInsights` log APIs (callback-style) | `await this.homey.insights.createLog(id, options)` (also `getLog()`, `getLogs()`, `deleteLog()`) |

**Before (SDK v2):**

```javascript
const Homey = require('homey');

class Driver extends Homey.Driver {
  onInit() {
    this.rainingCondition = new Homey.FlowCardCondition('is_raining');
    this.rainingCondition.register();

    this.myImage = new Homey.Image();
    this.myImage.setUrl('https://www.example.com/image.png');
    this.myImage.register().catch(this.error);
  }
}

module.exports = Driver;
```

**After (SDK v3):**

```javascript
'use strict';

const Homey = require('homey');

class Driver extends Homey.Driver {

  async onInit() {
    this.rainingCondition = this.homey.flow.getConditionCard('is_raining');

    this.myImage = await this.homey.images.createImage();
    this.myImage.setUrl('https://www.example.com/image.png');
  }

}

module.exports = Driver;
```

> **Do not rely on global state.** Define all variables as properties on your App, Driver or Device
> instance. Global scope (anything outside a class) should only contain constants.

### 3.3 Flow cards in SDK v3

```javascript
'use strict';

const Homey = require('homey');

class Driver extends Homey.Driver {

  async onInit() {
    // Action card
    this.homey.flow.getActionCard('show_notification')
      .registerRunListener(async (args) => {
        return args.tv.createToast(args.message);
      });

    // Device trigger card
    this._flowTriggerAppLaunched = this.homey.flow.getDeviceTriggerCard('app_launched')
      .registerRunListener(async (args, state) => {
        return args.application.id === state.id;
      });

    // Autocomplete for the `application` argument
    this._flowTriggerAppLaunched.registerArgumentAutocompleteListener('application',
      async (query, args) => {
        return args.tv.autocompleteApplicationArgument(query);
      });
  }

  triggerAppLaunchedFlow(device, tokens, state) {
    this._flowTriggerAppLaunched
      .trigger(device, tokens, state)
      .catch(this.error);
  }

}

module.exports = Driver;
```

Card instance methods in v3: `registerRunListener()`, `registerArgumentAutocompleteListener()` and
`getArgument()` on the `FlowCard` base class; `getArgumentValues()` on `FlowCardAction`,
`FlowCardCondition`, `FlowCardTrigger` and `FlowCardTriggerDevice`; plus `trigger()` on trigger cards
— `FlowCardTrigger#trigger(tokens?, state?)` and `FlowCardTriggerDevice#trigger(device, tokens?,
state?)`.

> `update` is an **event**, not a method: `card.on('update', …)` fires when the user changes the card
> (e.g. saves a Flow). There is no `card.update()`.

### 3.4 Web API moved into the manifest

Routes are declared in the App Manifest instead of `api.js`, and the handler receives `homey` as an
argument (you can no longer `require('homey')` to reach it).

```json
{
  "api": {
    "getSomething": { "method": "GET", "path": "/" },
    "addSomething": { "method": "POST", "path": "/" },
    "updateSomething": { "method": "PUT", "path": "/:id" },
    "deleteSomething": { "method": "DELETE", "path": "/:id" }
  }
}
```

```javascript
'use strict';

module.exports = {
  async getSomething({ homey, query }) {
    const result = await homey.app.getSomething();
    return result;
  },
  async addSomething({ homey, body }) {
    return homey.app.addSomething(body);
  },
  async updateSomething({ homey, params, body }) {
    return homey.app.updateSomething(params.id, body);
  },
  async deleteSomething({ homey, params }) {
    return homey.app.deleteSomething(params.id);
  },
};
```

Route options: `method` (`"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, or an array), `path`, and `public`
(default `false`). See `references/web-api-and-realtime.md`.

### 3.5 Consistent APIs — methods became properties

| SDK v2 | SDK v3 |
| --- | --- |
| `driver.getManifest()` | `driver.manifest` |
| `device.getDriver()` | `device.driver` |
| `onSettings(oldSettings, newSettings, changedKeys, callback)` | `async onSettings({ oldSettings, newSettings, changedKeys })` |

```javascript
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {

  async onSettings({ oldSettings, newSettings, changedKeys }) {
    if (changedKeys.includes('poll_interval')) {
      this.log('poll interval changed', oldSettings.poll_interval, '->', newSettings.poll_interval);
      this._restartPolling(newSettings.poll_interval);
    }
    // Optionally return a string to display a custom message to the user.
  }

}

module.exports = Device;
```

`onSettings` returns `Promise.<(string|void)>` — the returned string is shown to the user.

### 3.6 Promise-only APIs

All methods that previously supported both a callback and a Promise are **Promise-only** in v3.

**Pairing socket → `PairSession`.** The argument to `Driver#onPair()` used to be an `EventEmitter`
whose `.on()` handlers received a callback as last argument. It is now a `PairSession` with
`.setHandler()`, which may return a Promise.

```javascript
// SDK v2
onPair(socket) {
  socket.on('my_event', (data, callback) => {
    this.log('data', data);
    callback(null, 'reply');
  });
}
```

```javascript
// SDK v3
onPair(session) {
  session.setHandler('my_event', async (data) => {
    this.log('data', data);
    return 'reply';
  });
}
```

`PairSession` methods: `setHandler()`, `emit()`, `showView()`, `nextView()`, `prevView()`, `done()`.

**`onPairListDevices` → async, returns the array.**

```javascript
// SDK v2
onPairListDevices(data, callback) {
  const discoveryStrategy = this.getDiscoveryStrategy();
  const discoveryResults = Object.values(discoveryStrategy.getDiscoveryResults());
  const devices = discoveryResults.map(discoveryResult => ({
    name: discoveryResult.txt.name,
    data: { id: discoveryResult.id },
  }));
  callback(null, devices);
}
```

```javascript
// SDK v3
async onPairListDevices() {
  const discoveryStrategy = this.getDiscoveryStrategy();
  const discoveryResults = Object.values(discoveryStrategy.getDiscoveryResults());

  return discoveryResults.map(discoveryResult => ({
    name: discoveryResult.txt.name,
    data: { id: discoveryResult.id },
  }));
}
```

**App settings views and custom pair views** support *both* callbacks and Promises in v3. The
documentation shows Promises; **callbacks will be removed in a later SDK version**, so port them now.

### 3.7 `onInit()` ordering changed

In SDK v2, `Driver#onInit()` and `Device#onInit()` ran **before** `App#onInit()`. In SDK v3 the order
is top-down:

1. `App#onInit()`
2. `Driver#onInit()` (`driver-one`)
3. `Device#onInit()`
4. `Driver#onInit()` (`driver-two`)
5. `Device#onInit()`

**Consequence:** inside `App#onInit()` you **cannot** access drivers — `this.homey.drivers.getDriver()`
will throw. Set up shared data/classes on the App instance instead and read them from Driver/Device
`onInit` through `this.homey.app`.

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    // OK: prepare shared state here.
    this.cloudClient = new CloudClient({ token: this.homey.settings.get('token') });
    // NOT OK here: this.homey.drivers.getDriver('my_driver') throws.
    this.log('MyApp has been initialized');
  }

}

module.exports = MyApp;
```

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    this.client = this.homey.app.cloudClient; // available by now
  }

}

module.exports = MyDevice;
```

### 3.8 App timezone is always UTC

In SDK v3 `process.env.TZ` is **always `UTC`**. In SDK v2 the app's timezone followed the user's
setting, which caused correct apps to break when the user changed timezone.

Affected: `new Date('3/14/20')`, `Date.parse('3/14/20')`, `myDate.getHours()`, `myDate.setHours(12)`, …

Use `ManagerClock` + `Intl` when you need local time:

```javascript
const timezone = await this.homey.clock.getTimezone(); // e.g. Europe/Amsterdam
const formatter = new Intl.DateTimeFormat([], {
  timeZone: timezone,
  hour: '2-digit',
  minute: '2-digit',
  hour12: false, // Use 24-hour format
});

const timeParts = formatter.formatToParts(new Date());
const hour = timeParts.find(part => part.type === 'hour').value;
const minute = timeParts.find(part => part.type === 'minute').value;

this.log(`The time is ${hour}:${minute}`); // e.g. The time is 13:37
```

`ManagerClock` also emits `timezoneChange`.

### 3.9 `ManagerCron` removed

Use the Homey-scoped timers — identical to the native ones, but cleared automatically when the app is
removed:

```javascript
this._interval = this.homey.setInterval(() => {
  this._poll().catch(this.error);
}, 60 * 1000);

this._timeout = this.homey.setTimeout(() => this.log('later'), 5000);

this.homey.clearInterval(this._interval);
this.homey.clearTimeout(this._timeout);
```

Alternative: `this.homey.on('unload', () => clearInterval(myInterval));`

### 3.10 Removed deprecated Image APIs

`Image.format`, `Image.getFormat()`, `Image.getBuffer()` and `Image.setBuffer()` are **removed**.

The complete v3 `Image` surface is: `setUrl(url)`, `setPath(path)`, `setStream(source)`,
`getStream()` (async, resolves to a `NodeJS.ReadableStream` carrying `Image.ImageStreamMetadata`),
`pipe(stream)` (async, pipes into a `NodeJS.WritableStream` and resolves to the metadata),
`update()` (async, "notify that the image's contents have changed") and `unregister()` (async,
shorthand for `ManagerImages#unregisterImage`). `Image.ImageStreamMetadata` is
`{ filename: string, contentType: string, contentLength?: number }`. (`setStream()` requires Homey
v2.2.0 or higher.) See `references/advanced-features.md`.

### 3.11 Capability change: `zoneActivity`

`alarm_contact` and `alarm_motion` activate a zone when the alarm triggers. As of Homey v5.0.0 this can
be disabled with the **`zoneActivity`** capability option (boolean, defaults to `true`). The
capabilities documentation lists the option for `alarm_motion`, `alarm_contact`, `alarm_vibration`,
`alarm_occupancy` and `alarm_presence`.

```json
{
  "capabilitiesOptions": {
    "alarm_motion": { "zoneActivity": false }
  }
}
```

### 3.12 Z-Wave: MeshDriver → ZwaveDriver

Z-Wave node interaction is Promise-only:

```javascript
// SDK v2 + homey-meshdriver
const { ZwaveDevice } = require('homey-meshdriver');

class Device extends ZwaveDevice {
  onMeshInit() {
    this.node.CommandClass.COMMAND_CLASS_BASIC.BASIC_SET({ Value: true }, (err, result) => {
      // command has been executed
    });
  }
}
```

```javascript
// SDK v3 + homey-zwavedriver
'use strict';

const { ZwaveDevice } = require('homey-zwavedriver');

class Device extends ZwaveDevice {

  async onNodeInit() {
    await this.node.CommandClass.COMMAND_CLASS_BASIC.BASIC_SET({ Value: true });
    // command has been executed
  }

}

module.exports = Device;
```

**`homey-zwavedriver` deprecations / breaking changes vs `homey-meshdriver`** (non-exhaustive, per the
library README):

| Change | Replacement |
| --- | --- |
| `MeshDevice` removed | `ZwaveDevice` |
| `onMeshInit()` deprecated | `onNodeInit()` |
| `calculateZwaveDimDuration` deprecated | `calculateDimDuration` |
| `ZwaveMeteringDevice`, `ZwaveLockDevice` | **removed** |

**`associationGroups` behaviour changed in Homey v5.0.0** (more predictable):

| Driver manifest | Homey v5.0.0 – v13.1.x behaviour |
| --- | --- |
| `"associationGroups": []` | **Removes** the default association group 1 (Z-Wave Plus lifeline). |
| `associationGroups` not specified | **Sets** the default association group 1 (Z-Wave Plus lifeline). |

Audit every driver that either omits `associationGroups` or sets it to an empty array before shipping
the v3 update.

> **Superseded as of Homey v13.2.0.** The Z-Wave documentation now states that *Homey is always added
> to association group 1, the Lifeline group* — the empty-array opt-out no longer works. Explicitly:
> "in Homey before 13.2.0 it was possible to opt-out of the Lifeline association (group 1) by
> providing an empty array. As of version 13.2.0 the Lifeline association is always added." Treat the
> table above as the v5–v13.1 rule and do not rely on `[]` to suppress the lifeline on current
> firmware.

> Related, later change: from v13.2.0 Homey automatically determines whether to add a regular or a
> multi-channel association, and `associationGroupsMultiChannel` is handled the same way as
> `associationGroups` (Homey picks the correct association command class automatically). It exists for
> backwards compatibility — prefer `associationGroups` and set `"compatibility": ">=13.2.0"`.

### 3.13 Zigbee: MeshDriver → ZigbeeDriver

Homey v5.0.0 ships a Zigbee stack built from scratch; **SDK v2 Zigbee apps must be updated to SDK v3**.

**Driver manifest changes.** Add the `endpoints` property (the endpoint definition). The device
identification properties were reduced to only two required keys:

| Keep | Remove |
| --- | --- |
| `productId` | `deviceId` |
| `manufacturerId` | `profileId` |

Discover the endpoint definition with the **"interview"** button in the
[Zigbee developer tools](https://tools.developer.homey.app/tools/zigbee). Do **not** assume the
endpoint ids you used before are the same — an incorrect endpoint definition results in a
non-functioning device. The endpoint definition is currently dynamic, so it does not require a repair
to be updated on the device (this might change in the future).

**Class swap.** For lights it is a one-line import change:

```javascript
// before
const { ZigBeeLightDevice } = require('homey-meshdriver');
// after
const { ZigBeeLightDevice } = require('homey-zigbeedriver');
```

**`homey-zigbeedriver` deprecations / breaking changes vs `homey-meshdriver`** (non-exhaustive):

| Change | Replacement |
| --- | --- |
| `MeshDevice` removed | `ZigBeeDevice` |
| `onMeshInit()` deprecated | `onNodeInit()` |
| `this.node.on('online')` removed | `this.onEndDeviceAnnounce()` |
| `getClusterEndpoint` | now returns `null` if not found |
| `cluster` property was a string (e.g. `genOnOff`) | now an object from `const { CLUSTER } = require('zigbee-clusters');` |
| `registerReportListener` deprecated | `BoundCluster` implementation |
| `registerAttrReportListener` deprecated | `configureAttributeReporting` |
| `calculateZigbeeDimDuration` renamed | `calculateLevelControlTransitionTime` (plus new `calculateColorControlTransitionTime` for the `colorControl` cluster) |
| `ZigBeeXYLightDevice` removed | `ZigBeeLightDevice` (auto-detects hue/saturation vs XY-only) |

New capabilities in `homey-zigbeedriver`: **bindings and groups**, and **custom clusters**. Reference
migrated app: [`com.ikea.tradfri`](https://github.com/athombv/com.ikea.tradfri-example).

### 3.14 SDK v2 → v3 checklist

```
[ ] app.json / .homeycompose/app.json: "sdk": 3, "compatibility": ">=5.0.0"
[ ] Replace every Homey.ManagerX with this.homey.x
[ ] Delete every .register() on Flow cards / Images / Tokens; use manager getters/factories
[ ] Move API routes from api.js into the manifest "api" object; destructure { homey, ... }
[ ] driver.getManifest() -> driver.manifest ; device.getDriver() -> device.driver
[ ] onSettings(...) -> async onSettings({ oldSettings, newSettings, changedKeys })
[ ] onPair(socket).on(...) -> onPair(session).setHandler(...)
[ ] onPairListDevices(data, callback) -> async onPairListDevices()
[ ] Remove callbacks from every SDK call; add .catch(this.error) to fire-and-forget promises
[ ] Move driver lookups out of App#onInit()
[ ] Audit date/time code for the UTC default; use this.homey.clock.getTimezone() + Intl
[ ] Replace ManagerCron with this.homey.setTimeout / setInterval
[ ] Replace Image.setBuffer()/getBuffer()/getFormat()/format
[ ] Swap homey-meshdriver for homey-zwavedriver and/or homey-zigbeedriver + zigbee-clusters
[ ] Zigbee: add "endpoints", drop deviceId/profileId, re-interview the device
[ ] Z-Wave: re-check associationGroups ([] removes lifeline group 1 on v5.0.0-v13.1.x;
    from v13.2.0 the lifeline is always added and [] no longer opts out)
[ ] Upgrade homey-oauth2app / homey-rfdriver / homey-log to SDK v3 releases
[ ] Move global mutable state onto App/Driver/Device instances
[ ] homey app validate --level publish
```

---

## 4. Node.js 22 upgrade

Homey Apps run in a **Node.js v22** environment as of **Homey v12.9.0**, upgraded from Node.js v16 and
v18.

### 4.1 Node.js version matrix

| Platform | Homey version range | Node.js |
| --- | --- | --- |
| Homey Pro (2016–2019) | `< v7.4.0` | v12 |
| Homey Pro (2016–2019) | `>= v7.4.0 && < v12.9.0` | v16 |
| Homey Pro (2016–2019) | `>= v12.9.0` | v22 |
| Homey Pro (Early 2023) | `< v12.9.0` | v18 |
| Homey Pro (Early 2023) | `>= v12.9.0` | v22 |
| Homey Pro (mini) | `< v12.9.0` | v18 |
| Homey Pro (mini) | `>= v12.9.0` | v22 |
| Homey Cloud | `>= v12.9.0` | v22 |

> **Homey Cloud cutover:** Homey Cloud apps migrate to Node.js 22 **only after you publish a new
> version after December 2nd, 2025**. Earlier versions keep running on the previous Node.js version.
> Practical consequence: a Cloud app that has not been republished since that date is still on the old
> runtime — the first republish is where Node-22 regressions surface.

The Homey **CLI** itself is a separate concern: the getting-started requirements list **Node.js v24 or
higher** on your workstation. Do not assume a stdlib feature from your local Node is present on Homey.
See `references/cli-and-tooling.md`.

### 4.2 Known issue — `socket hang up` / `ECONNRESET` with `node-fetch`

Node.js 19 changed keep-alive socket management. With `node-fetch` this surfaces as `ECONNRESET`,
particularly against services that aggressively close idle connections:

```
FetchError: request to <> failed, reason: socket hang up
    at ClientRequest.<anonymous> (file:///app/node_modules/node-fetch/src/index.js:109:11)
    at ClientRequest.emit (node:events:519:28)
    at emitErrorEvent (node:_http_client:105:11)
    at Socket.socketOnEnd (node:_http_client:542:5)
    at Socket.emit (node:events:531:35)
    at endReadableNT (node:internal/streams/readable:1698:12)
    at process.processTicksAndRejections (node:internal/process/task_queues:90:21) {
  type: 'system',
  errno: 'ECONNRESET',
  code: 'ECONNRESET',
  erroredSysCall: undefined
}
```

**Solution 1 — custom HTTP Agent (recommended when staying on `node-fetch`):**

```javascript
const fetch = require('node-fetch');
const http = require('http');
const https = require('https');

// Create an agent with keep-alive enabled
const httpAgent = new http.Agent({ keepAlive: true });
const httpsAgent = new https.Agent({ keepAlive: true });

fetch('https://example.com/api', {
  agent: (_parsedURL) => (_parsedURL.protocol === 'http:' ? httpAgent : httpsAgent),
});
```

**Solution 2 — switch to built-in `fetch` (recommended for new code):** Node.js 18+ ships a native
global `fetch()` that handles socket management automatically and needs no dependency.

```javascript
// No imports needed, fetch is globally available
const response = await fetch('https://example.com/api');
const data = await response.json();
```

Upstream issue: <https://github.com/node-fetch/node-fetch/issues/1735>

### 4.3 Known issue — missing `Host` header causes `400 Bad Request`

As of Node.js 20 the default HTTP server **requires** a `Host` header on incoming requests; without it
it answers `400 Bad Request`. Either add the header at the client, or disable the requirement:

```javascript
http.createServer({ requireHostHeader: false });
```

Reference: <https://github.com/athombv/com.athom.homeyduino/pull/60>

### 4.4 Known issue — `Maximum call stack size exceeded` with `node-homey-api`

`socket.io` uses native Node.js sockets, which behave differently as of Node.js 22. Closing the socket
connection can throw:

```
Maximum call stack size exceeded {"stack":"RangeError: Maximum call stack size exceeded
    at emitInitScript (node:internal/async_hooks:495:24)
    at process.nextTick (node:internal/process/task_queues:143:5)
    at emitUncaughtException (node:internal/event_target:1090:11)
    at [nodejs.internal.kHybridDispatch] (node:internal/event_target:824:9)
    at WebSocket.dispatchEvent (node:internal/event_target:751:26)
    at fireEvent (node:internal/deps/undici/undici:11340:14)
    at failWebsocketConnection (node:internal/deps/undici/undici:11421:9)
    at closeWebSocketConnection (node:internal/deps/undici/undici:11692:9)
    at WebSocket.close (node:internal/deps/undici/undici:12352:9)
    at WS.doClose (file:///../node_modules/engine.io-client/build/esm-debug/transports/websocket.js:83:21)"}
```

**Solution:** update `node-homey-api` to **3.14.17 or newer**.

### 4.5 Node 22 review checklist

```
[ ] Replace node-fetch with the global fetch, or pass a keep-alive http(s).Agent
[ ] Bump homey-api / node-homey-api to >= 3.14.17
[ ] Any embedded http.createServer: confirm clients send a Host header
[ ] Re-test native/compiled npm modules against Node 22
[ ] Homey Cloud: republish after 2025-12-02 to actually move onto Node 22, then re-test
```

---

## 5. Homey v6.0.0 changelog (BLE)

Homey v6.0.0 is a Bluetooth Low Energy SDK update. **No breaking changes** — BLE apps that worked on
Homey v5.0.0 keep working on v6.0.0.

### 5.1 BLE notifications (new)

```javascript
// Subscribe to notifications
await characteristic.subscribeToNotifications((data) => {
  this.log('I received a notification: ', data);
});

// Wait for 5 seconds
await wait(5000);

// Unsubscribe from the notifications
await characteristic.unsubscribeFromNotifications();
```

### 5.2 `disconnect` event reintroduced

```javascript
peripheral.on('disconnect', () => {
  this.log('Disconnected from peripheral: ', peripheral.uuid);
});
```

The event is **not guaranteed to trigger** on every disconnect (BLE devices may turn off their radio
while keeping an active connection), but if it *does* fire, the peripheral is guaranteed to be
disconnected.

### 5.3 Caching / lifetime changes

| Behaviour | v6.0.0 |
| --- | --- |
| Discovery results cache | kept for **at least 30 seconds** |
| Auto-disconnect after 60 s | **removed** — a peripheral stays connected until the app using it closes, the corresponding device is removed by the user, or `peripheral.disconnect()` is called explicitly |
| `peripheral.state` | assumed unchanged until the SDK sees evidence otherwise, so it may still read `connected` after a silent disconnect |

### 5.4 (Deprecation) 16-bit UUID convention

```
// 128bit UUID
'0000ABCD-0000-1000-8000-00805F9B34FB'

// 16bit UUID (Deprecated)
'ABCD'
```

From Homey v6.0.0, Homey uses **long (128-bit) UUIDs** for all BLE devices by default, to give
consistent results across Homey models. Short UUIDs are still supported and current apps keep working —
but write new code against the long form.

---

## 6. Shipping changes to a live app

### 6.1 Compatibility ranges and feature detection

`compatibility` is a semver **range** of Homey versions the app supports; the documented minimum is
`">=5.0.0"`. Raise it only as far as you must — every bump drops users on older firmware.

| Feature you want to use | Minimum `compatibility` |
| --- | --- |
| SDK v3 | `>=5.0.0` |
| Enum capability option `values` (custom enum titles) | `>=12.0.1` |
| ESM (`.mjs` files) | `>=12.0.1` |
| Widgets / dashboards | `>=12.3.0` |
| `Device#setLastSeenAt()` | `>=12.6.1` |
| `Homey#hasFeature()` | `>=12.7.1` |
| Node.js 22 runtime | `>=12.9.0` |
| Python runtime (`"runtime": "python"`) | `>=13.0.0` |
| `associationGroups` auto multi-channel selection | `>=13.2.0` |

**Runtime detection instead of a compatibility bump.** Three read-only properties plus one method:

| API | Values |
| --- | --- |
| `this.homey.platform` | `'local'` \| `'cloud'` |
| `this.homey.platformVersion` | `1` \| `2` (may be `undefined` on older Homey Pro versions) |
| `this.homey.platformFeatures` | `Array.<string>` — features supported by this Homey |
| `this.homey.hasFeature(feature)` | `boolean`; feature is one of `speaker`, `ledring`, `nfc`, `camera-streaming`, `matter`. **Available since Homey v12.7.1.** |

| Product | `platform` | `platformVersion` |
| --- | --- | --- |
| Homey Cloud | `cloud` | `1` |
| Homey (Early 2016) | `local` | `1` |
| Homey (Early 2018) | `local` | `1` |
| Homey (Early 2019) | `local` | `1` |
| Homey Pro (Early 2019) | `local` | `1` |
| Homey Pro (Early 2023) | `local` | `2` |
| Homey Pro mini (2025) | `local` | `2` |
| Homey Pro (2026) | `local` | `2` |
| Homey Self-Hosted Server | `local` | `2` |

> On older software versions either `platform` or `platformVersion` may be `undefined`. In that case,
> assume `platform === 'local'` and `platformVersion === 1`.

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const platform = this.homey.platform ?? 'local';
    const platformVersion = this.homey.platformVersion ?? 1;
    this.log('running on', platform, 'v', platformVersion);

    // hasFeature() itself only exists on Homey >= 12.7.1 — guard the call.
    const hasLedring = typeof this.homey.hasFeature === 'function'
      && this.homey.hasFeature('ledring');

    if (hasLedring) {
      this.log('LED ring available');
    }
  }

}

module.exports = MyApp;
```

**Per-driver and per-Flow-card platform scoping.** `platforms` (`["local"]`, `["cloud"]` or both) is
valid on the app manifest, on each driver manifest and on each Flow card, so you can keep one codebase
while hiding platform-specific pieces. Drivers additionally take `connectivity`. See
`references/homey-cloud.md`.

```json
{
  "title": { "en": "It starts raining" },
  "platforms": ["local", "cloud"]
}
```

### 6.2 Adding a capability

Add it to `/drivers/<driver_id>/driver.compose.json` for **new** pairings, then migrate already-paired
devices with a guarded `addCapability()` — they do not receive it automatically.

```javascript
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {

  async onInit() {
    if (this.hasCapability('windowcoverings_set') === false) {
      // You need to check if migration is needed
      // do not call addCapability on every init!
      await this.addCapability('windowcoverings_set');
    }
  }

}

module.exports = Device;
```

### 6.3 Removing a capability

**Preferred:** remove the capability from the driver object in the App Manifest **only**. Already-paired
devices keep it, so UI components and Flow cards keep working; new pairings simply do not get it.

> When applying this strategy you must **never** remove the capability listener for the removed
> capability — doing so *will* break functionality for already-paired devices.

**Only when the behaviour can genuinely no longer be implemented**, remove it from paired devices too:

```javascript
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {

  async onInit() {
    if (this.hasCapability('windowcoverings_state')) {
      // You need to check if migration is needed
      // do not call removeCapability on every init!
      await this.removeCapability('windowcoverings_state');
    }
  }

}

module.exports = Device;
```

> **Danger:** if the capability you remove has Flow cards, **those cards are removed too and Flows using
> them break.**

There is **no `"deprecated"` flag for capabilities** — the manifest schema only accepts `deprecated` on
Flow cards, drivers and widgets. Manifest-only removal is the capability equivalent of deprecation.

### 6.4 Changing capability options on paired devices

Manifest `capabilitiesOptions` apply at pair time. To change `min`/`max`/`decimals`/`units` etc. for
existing devices, call `setCapabilityOptions()` — guarded, because it is an expensive method.

```javascript
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {

  async onInit() {
    const options = this.getCapabilityOptions('target_temperature') || {};
    if (options.max !== 30) {
      await this.setCapabilityOptions('target_temperature', { ...options, min: 5, max: 30, step: 0.5 })
        .catch(this.error);
    }
  }

}

module.exports = Device;
```

### 6.5 Deprecating a Flow card

Use `"deprecated": true` when you want to remove a Flow card **or change how it is constructed** (adding
or removing arguments). Users can no longer pick it for new Flows; existing Flows keep working. Then
publish a *new* card with the updated functionality.

```json
{
  "title": { "en": "Flow Action Title" },
  "deprecated": true
}
```

Placed in `/.homeycompose/flow/<triggers|conditions|actions>/<id>.json` (app-wide) or
`/drivers/<driver_id>/driver.flow.compose.json` (device cards). The manifest schema accepts only the
literal value `true`.

> **Do not remove or change the Flow card run listener** — that would still break existing Flows.

### 6.6 Changing the device class

```javascript
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {

  async onInit() {
    if (this.getClass() !== 'light') {
      // You need to check if migration is needed
      // do not call setClass on every init!
      await this.setClass('light').catch(this.error);
    }
  }

}

module.exports = Device;
```

> Some Flow cards depend on a device class; changing it **will** break those Flows for users.

If different physical devices under one driver need different Device subclasses, prefer
`Driver#onMapDeviceClass(device)` — it runs before the device instance is inited and returns the class
to use (synchronous only; the temporary `device` lives for a single tick):

```javascript
onMapDeviceClass(device) {
  if (device.hasCapability('dim')) {
    return MyDeviceDim;
  }
  return MyDevice;
}
```

### 6.7 Deprecating a driver, and why you cannot rename one

When no additive migration keeps the driver working, deprecate the whole driver. Paired devices keep
functioning; the driver disappears from the *Add Device* list.

```json
{
  "name": { "en": "My Driver" },
  "deprecated": true,
  "capabilities": ["onoff", "dim"]
}
```

**Driver renames.** Homey Compose sets `driverJson.id` from the **folder name** under `/drivers/`.
Renaming the folder therefore mints a *new* driver id, and every device paired under the old id is
orphaned. The supported pattern is a side-by-side migration:

```
1. Create /drivers/<new_id>/ with the new manifest and code.
2. Add "deprecated": true to /drivers/<old_id>/driver.compose.json.
3. Keep the old driver's device.js working (capabilities, listeners, Flow run listeners) indefinitely.
4. Re-declare every Flow card the old driver owned on the new driver, with NEW card ids;
   leave the old cards in place (optionally "deprecated": true).
5. Ask users to re-pair on the new driver via the changelog / app settings.
```

The same reasoning applies to Flow card ids and custom capability ids: the id **is** the contract with
the user's saved Flows.

### 6.8 Guarded, versioned device migrations with the store

`onInit` runs on every app start, so any one-shot migration needs a persistent flag. The Device store is
the right place: `getStoreValue(key)`, `setStoreValue(key, value)` (async), `unsetStoreValue(key)`
(async), plus `getStore()` and `getStoreKeys()`.

```javascript
'use strict';

const Homey = require('homey');

const MIGRATION_VERSION = 3;

class Device extends Homey.Device {

  async onInit() {
    await this._migrate().catch(this.error);
    // ... normal init
  }

  async _migrate() {
    const from = this.getStoreValue('migrationVersion') || 0;
    if (from >= MIGRATION_VERSION) return;

    if (from < 1) {
      // v1: split the old combined meter into two capabilities
      if (!this.hasCapability('meter_power')) {
        await this.addCapability('meter_power');
      }
    }

    if (from < 2) {
      // v2: the vendor id moved from settings to the store
      const legacyId = this.getSetting('device_id');
      if (legacyId) {
        await this.setStoreValue('deviceId', legacyId);
      }
    }

    if (from < 3) {
      // v3: this model is a light, not a socket
      if (this.getClass() !== 'light') {
        await this.setClass('light');
      }
    }

    await this.setStoreValue('migrationVersion', MIGRATION_VERSION);
    this.log(`migrated device from v${from} to v${MIGRATION_VERSION}`);
  }

}

module.exports = Device;
```

Rules for this pattern:

* **Never** call `addCapability` / `removeCapability` / `setCapabilityOptions` / `setClass`
  unconditionally on every init. The first three are documented as *"an expensive method so use it
  only when needed"*; `setClass()` is not labelled expensive but is documented as breaking every Flow
  that depends on the class, so it needs the same guard.
* Write the flag **after** the migration steps succeed, so a crash mid-migration retries next boot.
* Make each step idempotent anyway (`hasCapability`, `getClass`, value comparison) — a store write can
  fail.
* Keep old migration branches forever: a user may update from any historical version in one jump.
* `.catch(this.error)` the whole migration so a failure never prevents the device from initialising.

### 6.9 App-level one-shot migrations

The same pattern at app scope uses `ManagerSettings` (`this.homey.settings.get/set/unset/getKeys`).
Remember the SDK v3 ordering: `App#onInit()` runs **before** any driver exists, so app migrations must
not touch `this.homey.drivers`.

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const appMigration = this.homey.settings.get('appMigration') || 0;
    if (appMigration < 1) {
      const legacy = this.homey.settings.get('api_key');
      if (legacy) {
        this.homey.settings.set('credentials', { apiKey: legacy });
        this.homey.settings.unset('api_key');
      }
      this.homey.settings.set('appMigration', 1);
    }
  }

}

module.exports = MyApp;
```

### 6.10 Custom capabilities that shadow a system id (Homey ≥ 12.2.0)

From version 12.2.0, Homey Pro (Early) 2023 favours **custom** capabilities over system capabilities,
matching Homey Pro 2016–2019. Previously, a custom capability sharing an id with a system capability
still got **system Flow cards** generated; after the change those cards are no longer available.

Two migration strategies:

1. **Easiest:** delete the custom capability from `/.homeycompose/capabilities/` so Homey uses the
   system capability and generates the system Flow cards again.
2. **Keep the custom capability** (when it genuinely differs) and add a `flow.compose.json` to the
   affected drivers containing Flow cards with the **same Flow card ids** as the system cards, then
   register the matching run listeners in `app.js`. Example listener shapes:

```javascript
this.homey.flow.getConditionCard('alarm_contact').registerRunListener((args, state) => {
  return args.device.getCapabilityValue('alarm_contact');
});

this.homey.flow.getDeviceTriggerCard('thermostat_mode_changed').registerRunListener((args, state) => {
  return args.device.getCapabilityValue('thermostat_mode') === args.thermostat_mode;
});

this.homey.flow.getActionCard('target_temperature_set').registerRunListener((args, state) => {
  return args.device.setCapabilityValue('target_temperature', args.target_temperature);
});
```

When several drivers need the same device Flow card, define it once in `.homeycompose` and scope it with
a `device` argument filter:

```json
{
  "title": { "en": "Disco mode" },
  "args": [
    { "type": "device", "name": "device", "filter": "driver_id=my_driver" }
  ]
}
```

If you enabled `duration` through capability options, also add `"duration": true` to each action card
that should support it:

```json
{
  "actions": [
    { "id": "on", "highlight": true, "duration": true, "title": { "en": "Turn on" } }
  ]
}
```

See `references/capabilities.md` for the full system-capability list and the affected ids.

### 6.11 Rolling back a bad release

Homey **never downgrades apps**. If a published version broke users:

* Re-submit an **older build with a higher version number** — that is the only way to undo a release.
* Version numbers are semver; a user is auto-updated whenever a higher version is available.
* Patching *Live* while a newer *Test* build exists: submitting a version **lower** than the current
  Test version replaces the Test version. Example: Live `1.0.0`, Test `2.0.0`; submit `1.0.1` → it
  becomes Test, `2.0.0` becomes unavailable (existing 2.0.0 users keep it); promote `1.0.1` to Live;
  to bring the old Test branch back, resubmit it as `2.0.1` (higher than any version ever released).
* Pre-release versions such as `1.0.0-rc.1` are **not allowed**.
* Document the change with the standard changelog verbs: **Added**, **Changed**, **Deprecated**,
  **Removed**, **Fixed**, **Security**.

See `references/publishing.md` for the full Test/Live workflow.

---

## 7. Gotchas

**Gotcha — breaking changes are effectively forbidden, not merely discouraged.** Almost all users have
automatic app updates enabled, so a breaking release lands on every install without consent. Prefer
additive, guarded migrations executed in `onInit`.

**Gotcha — `addCapability()` on every init is a performance bug.** The SDK marks
`addCapability`/`removeCapability`/`setCapabilityOptions` as expensive. Always gate on
`hasCapability()` / a value comparison / a store flag.

**Gotcha — removing a capability silently deletes its Flow cards.** Manifest-only removal (keep the
listener) is almost always the right call; `removeCapability()` is for when the behaviour is genuinely
gone.

**Gotcha — a deprecated Flow card still needs its run listener.** `"deprecated": true` only hides the
card from the picker. Delete the listener and every existing Flow using it breaks.

**Gotcha — there is no `deprecated` flag for capabilities.** The manifest schema allows `deprecated`
only on Flow cards, drivers and widgets, and for Flow cards/drivers only the literal value `true`.

**Gotcha — the driver id is the folder name.** Homey Compose assigns `driver.id` from
`/drivers/<folder>/`. Renaming the folder orphans every paired device. Deprecate + add new instead.

**Gotcha — you cannot reach drivers from `App#onInit()` in SDK v3.** The ordering flipped versus SDK v2;
`this.homey.drivers.getDriver()` throws there. Publish shared state on the App instance and read it via
`this.homey.app` from Driver/Device `onInit`.

**Gotcha — SDK v3 apps always run in UTC.** Every `getHours()`/`new Date('3/14/20')` in ported v2 code
is suspect. Use `await this.homey.clock.getTimezone()` with `Intl.DateTimeFormat`.

**Gotcha — `getSetting()` / `getSettings()` return the OLD value inside `onSettings()`.** Settings are
persisted only after your `onSettings` resolves — read `newSettings` from the destructured event
argument, never `this.getSetting(...)`. (Full device-settings detail in
`references/drivers-and-devices.md`.)

**Gotcha — `associationGroups: []` changed meaning twice.** From Homey v5.0.0 an empty array *removes*
lifeline group 1 while omitting the key *adds* it; from Homey v13.2.0 the Lifeline association is
**always** added and the empty-array opt-out is gone. Re-audit every Z-Wave driver during the v3 port,
and again if you raise `compatibility` to `>=13.2.0`.

**Gotcha — Zigbee endpoint ids are not what they used to be.** Re-run the Zigbee devtools "interview"
per device; a wrong `endpoints` definition yields a device that pairs but does nothing.

**Gotcha — Homey Cloud apps do not move to Node 22 until you republish.** Publishing after
2025-12-02 is what triggers the runtime switch, so the first post-cutover release is where
`node-fetch`/`socket.io` issues appear. Test that release deliberately.

**Gotcha — two different Node versions are in play.** The CLI requires Node.js v24+ on your workstation;
the app runs on Node.js v22 on Homey. A stdlib feature that works locally may not exist on-device.

**Gotcha — `hasFeature()` does not exist below Homey v12.7.1.** If your `compatibility` range starts
lower, check `typeof this.homey.hasFeature === 'function'` before calling it.

**Gotcha — `platform` / `platformVersion` can be `undefined`.** Default them to `'local'` / `1`.

**Gotcha — callbacks in app-settings and custom pair views are on borrowed time.** They still work in
SDK v3, but the docs state they will be removed in a later SDK version. Port to Promises now.

**Gotcha — a higher version number is the only rollback.** Homey never downgrades an installed app, so
"undo the release" always means republishing older code under a *newer* version.

---

## Sources

* <https://apps.developer.homey.app/upgrade-guides/upgrading-to-sdk-v3>
* <https://apps.developer.homey.app/upgrade-guides/upgrading-to-sdk-v3/upgrading-zigbee>
* <https://apps.developer.homey.app/upgrade-guides/node-22>
* <https://apps.developer.homey.app/upgrade-guides/changelog-homey-6>
* <https://apps.developer.homey.app/upgrade-guides/device-capabilities>
* <https://apps.developer.homey.app/guides/how-to-breaking-changes>
* <https://apps.developer.homey.app/the-basics/app> (Node.js version matrix)
* <https://apps.developer.homey.app/the-basics/app/manifest>
* <https://apps.developer.homey.app/the-basics/devices> (driver `deprecated`)
* <https://apps.developer.homey.app/the-basics/devices/capabilities> (`zoneActivity`, enum `values`)
* <https://apps.developer.homey.app/the-basics/flow> (Flow card `deprecated`)
* <https://apps.developer.homey.app/guides/homey-cloud> (`platforms`, SDK v3 requirement)
* <https://apps.developer.homey.app/app-store/updates> (versioning, Test/Live, rollback)
* <https://apps.developer.homey.app/advanced/web-api>
* <https://apps.developer.homey.app/advanced/images> (`Image` delivery types, `setStream()` ≥ v2.2.0)
* <https://apps.developer.homey.app/advanced/homey-compose>
* <https://apps.developer.homey.app/wireless/z-wave> (`associationGroups` from Homey v13.2.0)
* <https://apps.developer.homey.app/the-basics/getting-started> (CLI requires Node.js v24+)
* <https://apps-sdk-v3.developer.homey.app> (Homey, App, Driver, Device, PairSession, Image, Flow*)
* <https://athombv.github.io/node-homey-zwavedriver/>
* <https://athombv.github.io/node-homey-zigbeedriver/>
* <https://athombv.github.io/node-zigbee-clusters/>
