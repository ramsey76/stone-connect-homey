# Drivers & Devices

Every paired device is a `Device` instance owned by a `Driver` instance. All `Driver` classes of an app are
instantiated on app start — even when zero devices are paired — because the driver owns pairing and driver-level
Flow cards. This file covers both class APIs, the `driver.compose.json` manifest, the complete device-class list
and the device-settings schema. Capabilities live in `references/capabilities.md`, energy in `references/energy.md`,
pairing/repair in `references/pairing.md`, LAN discovery strategies in `references/wireless-lan-discovery.md`.

## File layout

```
com.athom.example/
└─ drivers/
   └─ <driver_id>/
      ├─ assets/
      │  ├─ icon.svg                      # driver icon (fixed location)
      │  └─ images/{small,large,xlarge}.png
      ├─ pair/                            # optional custom pairing views (*.html)
      ├─ repair/                          # optional custom repair views (*.html)
      ├─ driver.js                        # class extends Homey.Driver
      ├─ device.js                        # class extends Homey.Device
      ├─ driver.compose.json              # driver manifest
      ├─ driver.settings.compose.json     # → drivers[].settings
      ├─ driver.pair.compose.json         # → drivers[].pair
      ├─ driver.repair.compose.json       # → drivers[].repair
      ├─ driver.flow.compose.json         # → driver-scoped Flow cards
      └─ driver.firmware.compose.json     # → drivers[].firmwareUpdates
```

TypeScript apps use `driver.mts` / `device.mts`; Python apps `driver.py` / `device.py` with `homey_export = Driver`.
The `homey` CLI also accepts `driver.mjs` / `driver.cjs` / `device.mjs` / `device.cjs`.

Scaffold a driver interactively (requires Homey Compose; the CLI offers to migrate if the app has none):

```bash
homey app driver create
```

The wizard asks for the driver name, driver id, device class (picked from the full class list), capabilities and
wireless type, then writes `drivers/<driver_id>/driver.compose.json` with `name`, `class`, `capabilities`,
`platforms`, `connectivity`, `images` (using the `{{driverAssetsPath}}` placeholder), plus `driver.js`, `device.js`
and the `assets/` + `assets/images/` folders. Matter drivers get no `driver.js`/`device.js` — apps cannot add
functionality to Matter devices.

---

## Driver class

`/drivers/<driver_id>/driver.js` must export a class extending `Homey.Driver`. Methods prefixed with `on` are meant
to be overridden. **Overwriting the constructor is not allowed** — do initialisation in `onInit()`.

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  async onInit() {
    this.log('MyDriver has been initialized');

    const showToastActionCard = this.homey.flow.getActionCard('show_toast');
    showToastActionCard.registerRunListener(async ({ device, message }) => {
      await device.createToast(message);
    });
  }

  async onPairListDevices() {
    return [
      {
        name: 'Foo Device',
        data: { id: 'abcd1234' },
      },
    ];
  }

}

module.exports = MyDriver;
```

### Driver instance properties

| Property | Type | Description |
| --- | --- | --- |
| `this.homey` | `Homey` | The Homey instance of this driver (access to all managers) |
| `this.manifest` | `any` | The driver's manifest — its `app.json` `drivers[]` entry |

Inherited from `SimpleClass`: `this.log(...args)` (emits `__log`) and `this.error(...args)` (emits `__error`).

### Driver methods

| Method | Returns | Description |
| --- | --- | --- |
| `onInit()` | `async` | Called when the driver is inited (app start). |
| `onUninit()` | `async` | Called when the driver is destroyed. |
| `ready()` | `Promise<void>` | Resolves when the Driver is ready, i.e. `onInit()` has run. |
| `getDevice(deviceData)` | `Device` | Get a `Device` instance by its `data` object, exactly as provided during pairing. |
| `getDevices()` | `Array<Device>` | All `Device` instances of this driver. |
| `getDiscoveryStrategy()` | `DiscoveryStrategy` | The driver's discovery strategy, when `discovery` is set in the manifest. |
| `onPair(session)` | — | Called when a pair session starts. `session` is a `PairSession` (bi-directional socket to the front-end). See `references/pairing.md`. |
| `onPairListDevices()` | `Promise<Array<any>>` | Called when no custom `onPair()` is defined and the default is used. Return the list of devices ready to be paired. |
| `onRepair(session, device)` | — | Similar to `onPair`, but for repairing an already-paired `device`. See `references/pairing.md`. |
| `onMapDeviceClass(device)` | `class` | When this method exists it is called *before* initing the device instance. Return a class that extends `Device`. |

**Gotcha:** there is no `getDeviceById()` on `Driver` — the only lookups are `getDevice(deviceData)` (needs the exact
`data` object) and `getDevices()`. To find a device by an arbitrary property, iterate `getDevices()` and compare
`device.getData()` / `device.getStoreValue()` yourself.

```javascript
const device = this.getDevices().find((d) => d.getData().id === wantedId);
```

### onMapDeviceClass — one driver, several Device subclasses

`onMapDeviceClass(device)` receives a **temporary** `Device` instance so you can inspect properties before deciding
which class to use. That temporary instance **exists for a single tick and does not support async methods** — only
synchronous getters such as `hasCapability()`, `getData()`, `getStoreValue()`, `getSettings()`.

```javascript
'use strict';

const Homey = require('homey');
const MyDevice = require('./device');
const MyDeviceDim = require('./device-dim');

class MyDriver extends Homey.Driver {

  onMapDeviceClass(device) {
    if (device.hasCapability('dim')) {
      return MyDeviceDim;
    }
    return MyDevice;
  }

}

module.exports = MyDriver;
```

### Reaching drivers from anywhere: ManagerDrivers

`this.homey.drivers` is a `ManagerDrivers` instance, available in `App`, `Driver`, `Device` and API handlers.

| Method | Returns | Description |
| --- | --- | --- |
| `getDriver(driverId)` | `Driver` | Get a `Driver` instance by its ID, as defined in `app.json` (the folder name under `/drivers/`). |
| `getDrivers()` | `Object<string, Driver>` | All `Driver` instances keyed by driver ID. |

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const driver = this.homey.drivers.getDriver('my_driver');
    await driver.ready();

    for (const device of driver.getDevices()) {
      this.log('device:', device.getName());
    }

    for (const [driverId, d] of Object.entries(this.homey.drivers.getDrivers())) {
      this.log(driverId, d.getDevices().length);
    }
  }

}

module.exports = MyApp;
```

---

## Device class

`/drivers/<driver_id>/device.js` must export a class extending `Homey.Device` (or any custom class returned from
`Driver#onMapDeviceClass`). Methods prefixed with `on` are meant to be overridden. **Overwriting the constructor is
not allowed.**

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDevice extends Homey.Device {

  async onInit() {
    this.log('Device init');
    this.log('Name:', this.getName());
    this.log('Class:', this.getClass());

    this.registerCapabilityListener('onoff', this.onCapabilityOnoff.bind(this));

    this.pollInterval = this.homey.setInterval(() => {
      this.poll().catch(this.error);
    }, this.getSetting('poll_interval') * 1000);
  }

  async onCapabilityOnoff(value, opts) {
    // ... set value on the real device, e.g.
    // await DeviceApi.setState({ on: value });
    // or throw to report failure back to the user / Flow:
    // throw new Error('Switching the device failed!');
  }

  async poll() {
    const state = await DeviceApi.getState();
    await this.setCapabilityValue('onoff', state.on);
    await this.setLastSeenAt();
  }

  async onAdded() {
    this.log('Device added');
  }

  async onRenamed(name) {
    await DeviceApi.setName(name);
  }

  async onSettings({ oldSettings, newSettings, changedKeys }) {
    if (changedKeys.includes('poll_interval')) {
      this.homey.clearInterval(this.pollInterval);
      this.pollInterval = this.homey.setInterval(() => {
        this.poll().catch(this.error);
      }, newSettings.poll_interval * 1000);
    }
  }

  async onDeleted() {
    this.homey.clearInterval(this.pollInterval);
  }

  async onUninit() {
    this.homey.clearInterval(this.pollInterval);
  }

  // custom method, callable from a driver-level Flow card run listener
  async createToast(message) {
    await DeviceApi.createToast(message);
  }

}

module.exports = MyDevice;
```

### Device instance properties

| Property | Type | Description |
| --- | --- | --- |
| `this.driver` | `Driver` | The device's driver instance |
| `this.homey` | `Homey` | The Homey instance of this app |

Plus `this.log()` / `this.error()` from `SimpleClass`.

### Device lifecycle methods

| Method | Async | Called when |
| --- | --- | --- |
| `onInit()` | yes | The device is loaded and properties such as name, capabilities and state are available. |
| `onAdded()` | — | The user adds the device — called just after pairing. |
| `onRenamed(name)` | — | The user updates the device's name. Use it to sync the name to the device or bridge. `name` is the new name. |
| `onSettings({ oldSettings, newSettings, changedKeys })` | yes | The user updates the device's settings. Returns `Promise<string \| void>`. |
| `onDeleted()` | — | The user deleted the device. |
| `onUninit()` | yes | The device is destroyed (app stop/uninstall/update). |
| `ready()` | yes | Not an override — returns a `Promise` resolved when the Device is ready (`onInit()` has run). |

Order in practice: pairing → `onAdded()` → `onInit()` on every app start → `onUninit()` on app teardown;
`onDeleted()` when the user removes the device. Always clear timers created with `this.homey.setInterval()` /
`this.homey.setTimeout()` in both `onDeleted()` and `onUninit()`.

### Device getters & setters

| Method | Returns | Notes |
| --- | --- | --- |
| `getName()` | `string` | The device's name. |
| `getData()` | `any` | The device's immutable `data` object, as provided during pairing. |
| `getState()` | `any` | The device's state object — all capability values. |
| `getClass()` | `string` | The device's class. |
| `setClass(deviceClass)` | `Promise<void>` | Set the device's class. **Any Flow that depends on this class will become broken.** |
| `getAvailable()` | `boolean` | Whether the device is marked available. |
| `getEnergy()` | `any` | The device's energy info object. Returns **only** an override previously set with `setEnergy()`, *not* the `energy` object from `driver.compose.json`. |
| `setEnergy(energy)` | async | Set the device's energy object. Must be the **complete** configuration — it overwrites all existing properties, and from then on the device permanently ignores `energy` in `driver.compose.json`. See `references/energy.md`. |
| `getSettings()` | `any` | The full settings object. |
| `getSetting(key)` | `any` | A single setting value, or `null` when unknown. |
| `setSettings(settings)` | `Promise<void>` | Set settings; the object may be a **subset**. Does **not** fire `onSettings()`. |
| `getStore()` | `any` | The entire store object. |
| `getStoreKeys()` | `Array<string>` | All store keys. |
| `getStoreValue(key)` | `any` | A single store value. |
| `setStoreValue(key, value)` | `Promise<void>` | Set a store value. |
| `unsetStoreValue(key)` | `Promise<void>` | Unset a store value. |
| `setLastSeenAt()` | async | Set the device's `lastSeenAt`. Call it when the device is known to be alive and responding. **Available since Homey v12.6.1.** |

### Device capability methods

| Method | Returns | Notes |
| --- | --- | --- |
| `getCapabilities()` | `Array<string>` | The device's capabilities array. |
| `hasCapability(capabilityId)` | `boolean` | |
| `addCapability(capabilityId)` | async | **Expensive — use only when needed.** |
| `removeCapability(capabilityId)` | async | **Expensive.** Any Flow depending on the capability becomes broken. |
| `getCapabilityValue(capabilityId)` | `any` | The value, or `null` when unknown. |
| `setCapabilityValue(capabilityId, value)` | `Promise<void>` | Push a value from the device into Homey. |
| `getCapabilityOptions(capabilityId)` | `any` | |
| `setCapabilityOptions(capabilityId, options)` | async | **Expensive — use only when needed.** |
| `registerCapabilityListener(capabilityId, listener)` | — | Invoked when a state change is *requested* (Homey → device). |
| `registerMultipleCapabilityListener(capabilityIds, listener, timeout)` | — | Debounced multi-capability listener; `timeout` defaults to `250` ms. |
| `triggerCapabilityListener(capabilityId, value, opts)` | `Promise<any>` | Trigger a capability listener programmatically. |

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

Capability options, sub-capabilities and the full system-capability table: `references/capabilities.md`.

### Device availability & warnings

| Method | Returns | Notes |
| --- | --- | --- |
| `setAvailable()` | `Promise<any>` | Set availability to `true`. |
| `setUnavailable(message)` | `Promise<any>` | Set availability to `false`. `message` is optional — a custom unavailable message, or `null` for the default. |
| `getAvailable()` | `boolean` | |
| `setWarning(message)` | `Promise<any>` | Show a warning to the user. **Persistent** — unset it when it no longer applies. Pass `null` to unset. |
| `unsetWarning()` | `Promise<any>` | Clear the warning. |

While a device is unavailable **all capabilities and Flow actions are prevented**.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDevice extends Homey.Device {

  async onInit() {
    await this.setUnavailable();

    DeviceApi.on('connected', () => {
      this.setAvailable().catch(this.error);
    });

    DeviceApi.on('disconnected', () => {
      this.setUnavailable('Device is offline').catch(this.error);
    });
  }

}

module.exports = MyDevice;
```

Availability vs warning: `setUnavailable()` blocks interaction (device offline, unreachable, unauthenticated);
`setWarning()` leaves the device usable but surfaces a message (e.g. a degraded condition). When a driver uses a
discovery strategy, Homey manages availability automatically.

### Device media methods

| Method | Signature | Description |
| --- | --- | --- |
| `setCameraImage(id, title, image)` | `Promise<any>` | Set a device's camera image. `id`: unique image id (e.g. `front`). `title`: display title (e.g. `Front`). `image`: an `Image` instance. |
| `setAlbumArtImage(image)` | `Promise<any>` | Set this device's album art. |
| `setCameraVideo(id, title, video)` | `Promise<any>` | Set a device's camera stream. `id`: unique video id (e.g. `front_door`). `title`: title (e.g. `Front Door`). `video`: a `Video` instance. |

Images come from `this.homey.images.createImage()` (then `setPath()`, `setStream()` or `setUrl()` — note the
lowercase `rl`; there is no `setURL()`); videos from
`this.homey.videos.createVideoWebRTC() / createVideoRTSP() / createVideoRTMP() / createVideoHLS() /
createVideoDASH() / createVideoOther()`. When a device has an image and a video with the **same `id`**, the image is
used as the background while the video loads. Details: `references/advanced-features.md`.

```javascript
async onInit() {
  const image = await this.homey.images.createImage();
  image.setStream(async (stream) => {
    const res = await fetch(`http://${this.getStoreValue('address')}/snapshot.jpg`);
    return res.body.pipe(stream);
  });

  await this.setCameraImage('front', 'Front', image);
}
```

### Device discovery methods

Overridden on the `Device` when the driver manifest sets `"discovery": "<strategy_id>"`.

| Method | Description |
| --- | --- |
| `onDiscoveryResult(discoveryResult)` | Called when a device has been discovered. Return a **truthy** value when the result belongs to this device, falsy when it doesn't. By default the method matches on the device's `data.id` property. |
| `onDiscoveryAvailable(discoveryResult)` | Called when the device is found for the first time. Overload to create a connection. **Throwing here makes the device unavailable with the thrown error message.** |
| `onDiscoveryAddressChanged(discoveryResult)` | Called when the device's address has changed. |
| `onDiscoveryLastSeenChanged(discoveryResult)` | Called when the device has been found again. |

`DiscoveryResult` exposes `id` (string), `address` (string) and `lastSeen` (Date).

```javascript
'use strict';

const Homey = require('homey');
const MyDeviceAPI = require('./lib/MyDeviceAPI');

class MyDevice extends Homey.Device {

  onDiscoveryResult(discoveryResult) {
    // Return a truthy value here if the discovery result matches your device.
    return discoveryResult.id === this.getData().id;
  }

  async onDiscoveryAvailable(discoveryResult) {
    // Executed once when the device has been found (onDiscoveryResult returned true)
    this.api = new MyDeviceAPI(discoveryResult.address);
    await this.api.connect(); // when this throws, the device becomes unavailable
  }

  onDiscoveryAddressChanged(discoveryResult) {
    this.api.address = discoveryResult.address;
    this.api.reconnect().catch(this.error);
  }

  onDiscoveryLastSeenChanged(discoveryResult) {
    this.api.reconnect().catch(this.error);
  }

}

module.exports = MyDevice;
```

Strategy definitions (`mdns-sd`, `ssdp`, `mac`) live in `/.homeycompose/discovery/<id>.json` — see
`references/wireless-lan-discovery.md`.

---

## Device identifier: `data`

During pairing you must provide a `data` property: a unique identifier object for the device, **immutable after
pairing**. It may contain properties of type String, Number or Object. Homey identifies your device by this object
together with the driver's ID.

> **Only put the essential properties needed to identify a device in `data`.** A MAC address is a good property; an
> IP address is not, because it can change over time.

Anything that can change over time belongs in memory or in the device **store**.

```javascript
async onPairListDevices() {
  const found = await this.discoverDevices();
  return found.map((d) => ({
    name: d.name,
    data: { id: d.macAddress },       // unique + immutable
    store: { address: d.ipAddress },  // mutable
    settings: { poll_interval: 30 },
  }));
}
```

Complete shape of a device object returned from `Driver#onPairListDevices()` or a `list_devices` handler:

```javascript
{
  // The name of the device that will be displayed
  name: 'My Device',

  // Required and unique. A MAC address is good, an IP address is not.
  data: {
    id: 'abcd',
  },

  // Optional: dynamic and persistent storage for your device
  store: {
    address: '127.0.0.1',
  },

  // Optional: initial settings, editable afterwards in the device settings screen
  settings: {
    pincode: '1234',
  },

  // Optional: these overwrite the defaults from the driver manifest
  icon: '/my_icon.svg',                          // relative to /drivers/<driver_id>/assets/
  capabilities: ['onoff', 'target_temperature'],
  capabilitiesOptions: {
    target_temperature: { min: 5, max: 35 },
  },
}
```

Icons may also be referenced from the `/userdata` folder (e.g. `/userdata/my_icon.svg`) — the only exception to the
"relative to `/drivers/<driver_id>/assets/`" rule, so apps can upload an icon and reference it during pairing.
Supported since Homey `v12.3.0`. Full pairing flow: `references/pairing.md`.

## Device store

Persistent storage for device properties that must survive reboots but are not user-configurable. Can be seeded
during pairing (the `store` property of a paired device object) and read/written afterwards.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDevice extends Homey.Device {

  async onInit() {
    this.currentAddress = this.getStoreValue('address');

    DeviceApi.on('address-changed', (address) => {
      this.currentAddress = address;
      this.setStoreValue('address', address).catch(this.error);
    });
  }

}

module.exports = MyDevice;
```

> Using the store is rare — usually there are better solutions. If users should be able to change a value, use
> **device settings**. Instead of storing an IP address, use Homey's built-in **LAN discovery**.

---

## driver.compose.json reference

Every `driver.compose.json` is bundled into `app.json` as an entry of the `drivers` array when the app is built.
The `id` is set automatically from the folder name under `/drivers/`.

```json
{
  "name": { "en": "My Driver" },
  "class": "socket",
  "capabilities": ["onoff", "dim"],
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png",
    "xlarge": "/drivers/my_driver/assets/images/xlarge.png"
  },
  "platforms": ["local", "cloud"],
  "connectivity": ["lan"],
  "pair": [
    {
      "id": "list_devices",
      "template": "list_devices",
      "navigation": { "next": "add_devices" }
    },
    {
      "id": "add_devices",
      "template": "add_devices"
    }
  ]
}
```

### Field table

| Key | Type | Req. | Description |
| --- | --- | --- | --- |
| `id` | string | auto | Driver ID. Set by Homey Compose from the folder name — do not write it yourself. |
| `name` | i18n object | **yes** | Driver name, e.g. `{ "en": "My Driver" }`. |
| `class` | string | **yes** | Device class — see the full table below. |
| `capabilities` | string[] (unique) | **yes** | Capability IDs, e.g. `["onoff", "dim"]`. |
| `capabilitiesOptions` | object | no | Per-capability overrides, keyed by capability ID. See `references/capabilities.md`. |
| `images` | object | publish | `{ small, large, xlarge? }`; `small` and `large` are required inside the object. Required to publish an app. |
| `icon` | string | no | Path to the driver icon SVG. |
| `platforms` | string[] (unique) | verified | `"local"` and/or `"cloud"`. Default `["local"]`. |
| `connectivity` | string[] (unique) | verified | How the driver talks to the device — see the allowed-value table. |
| `energy` | object | no | Power usage/generation metadata. See `references/energy.md`. |
| `settings` | array | no | Device settings. Normally written to `driver.settings.compose.json` instead. |
| `pair` | array | no | Pairing views. Normally `driver.pair.compose.json`. See `references/pairing.md`. |
| `repair` | array | no | Repair views. Normally `driver.repair.compose.json`. |
| `discovery` | string | no | ID of a discovery strategy defined in the app manifest's `discovery` object. |
| `deprecated` | `true` | no | Driver keeps working for existing users but disappears from the 'Add Device' list. |
| `gtin` | string \| string[] (unique) | no | Global Trade Item Number(s) of the supported product. |
| `firmwareUpdates` | object | no | Zigbee or Z-Wave firmware update definitions. Normally `driver.firmware.compose.json`. |
| `zwave` | object | no | Z-Wave device definition. See `references/wireless-zwave.md`. |
| `zigbee` | object | no | Zigbee device definition. See `references/wireless-zigbee.md`. |
| `matter` | object | no | Matter device definition. See `references/wireless-ble-matter.md`. |
| `rf433` | object | no | `{ "satelliteMode": boolean }`. See `references/wireless-rf-infrared.md`. |
| `infrared` | object | no | `{ "satelliteMode": boolean }`. |
| `$extends` | string \| string[] | no | Compose-only: driver template(s) from `/.homeycompose/drivers/templates/<id>.json`. |
| `$pairOptions` | object | no | Compose-only: `{ "<viewId>": { …options } }` merged into the matching `pair` view's `options`. |
| `$repairOptions` | object | no | Compose-only: same, for `repair` views. |
| `$flow` | object | no | Compose-only: driver-scoped Flow cards. Normally written to `driver.flow.compose.json`; the `device` argument is added automatically. See `references/flow-cards.md`. |

### `class`

`"class": "light"` tells Homey what type of device the driver adds. Classes drive Zone Flow cards ("turn off all
lights in this zone" picks up any device with class `light` + capability `onoff`) and third-party integrations such
as Google Assistant ("turn off all lights"). When nothing fits, use `other`. The CLI rejects an unknown class, and
rejects a class whose `minCompatibility` exceeds the app manifest's `compatibility` range.

### `capabilities`

Capabilities describe the states and actions a device supports. Each capability has a data type — `onoff` is
`boolean`, `dim` is a `number` between `0` and `1`. Homey ships many system capabilities and generates built-in Flow
cards for every one of them; app-specific capabilities are declared in the app manifest
(`/.homeycompose/capabilities/<id>.json`). Full reference: `references/capabilities.md`.

### `images` and `icon`

| Size | Required dimensions (driver) |
| --- | --- |
| `small` | 75 × 75 |
| `large` | 500 × 500 |
| `xlarge` | 1000 × 1000 |

`small` and `large` are validated (extension, magic bytes, exact pixel size) and both are required once `images` is
present; `images` itself is required to publish. These are clean marketing pictures of the device shown in the Homey
App Store — see `references/publishing.md`.

The driver **icon** is always expected at `/drivers/<driver_id>/assets/icon.svg`; the docs state its location cannot
be specified in the driver manifest. The default Homey Compose driver template nevertheless writes
`"icon": "{{driverAssetsPath}}/icon.svg"`, which resolves to that same path — so keep the file there regardless of
whether you set the key.

### `platforms`

`"platforms": ["local", "cloud"]` — the platforms this driver supports.

| Value | Meaning |
| --- | --- |
| `local` | Homey Pro (runs locally) |
| `cloud` | Homey Cloud |

Rules enforced by the CLI:

- Default is `["local"]`; the CLI warns when a driver has no `platforms` while the app manifest includes `cloud`.
- A driver may not list a platform the app manifest does not list.
- `platforms` is **required to publish a verified app**.

See `references/homey-cloud.md`.

### `connectivity`

`"connectivity": [ ... ]` — how the driver reaches the device in the real world. Multiple values are allowed, e.g.
`["infrared", "lan"]` for a TV turned on by infrared and then controlled over Wi-Fi.

| Value | Description |
| --- | --- |
| `lan` | Local (Wi-Fi/Ethernet) |
| `cloud` | Cloud-connected (Wi-Fi/Ethernet) |
| `ble` | Bluetooth Low Energy |
| `zwave` | Z-Wave |
| `zigbee` | Zigbee |
| `infrared` | Infrared |
| `rf433` | 433 MHz |
| `rf868` | 868 MHz |
| `matter` | Matter (only available on Homey Pro (Early 2023)) |

Rules enforced by the CLI:

- `connectivity` is **required to publish a verified app**.
- A driver with `platforms` including `cloud` may not use `lan`, `matter` or `rf868`.

### `discovery`

`"discovery": "my_discovery"` must reference a key of the app manifest's `discovery` object (i.e. a file
`/.homeycompose/discovery/my_discovery.json`); the CLI throws on an unknown id. Linking a strategy makes Homey manage
device availability automatically and enables the `Device#onDiscovery*` methods and `Driver#getDiscoveryStrategy()`.

### `deprecated`

`"deprecated": true` keeps an old driver working for users who already paired it, while hiding it from the 'Add
Device' list. The schema's enum allows **only** `true` — writing `"deprecated": false` fails validation; remove the
key instead.

### `matter`, `zwave`, `zigbee`, `firmwareUpdates`

Extra validation the CLI enforces on wireless drivers:

- A driver with a `matter` object **must** include `matter` in `connectivity`.
- Matter drivers **cannot** have `driver.js` / `driver.mjs` / `device.js` / `device.mjs` — apps cannot add
  functionality to Matter devices — and **cannot** define custom `pair` views.
- `matter.deviceVendorId` and `matter.deviceProductName` must be defined together or not at all.
- `firmwareUpdates` is only supported on Zigbee or Z-Wave drivers (i.e. the driver also has a `zigbee` or `zwave`
  object), and every entry in `firmwareUpdates.updates` needs a `changelog` string (or `changelog.en`).

### Compose templating

Shared driver properties go in `/.homeycompose/drivers/templates/<template_id>.json` and are pulled in with
`$extends`. Templates are merged in array order, then the driver's own keys override them; `capabilitiesOptions` is
merged per capability rather than replaced.

```json
// /.homeycompose/drivers/templates/defaults.json
{
  "images": {
    "large": "{{driverAssetsPath}}/images/large.png",
    "small": "{{driverAssetsPath}}/images/small.png"
  },
  "icon": "{{driverAssetsPath}}/icon.svg",
  "capabilities": [],
  "class": "other"
}
```

```json
// /drivers/my_driver/driver.compose.json
{
  "name": { "en": "My Driver", "nl": "Mijn Driver" },
  "$extends": ["defaults"]
}
```

String placeholders replaced by Homey Compose inside driver JSON:

| Placeholder | Replaced with |
| --- | --- |
| `{{driverId}}` | `<driver_id>` |
| `{{driverPath}}` | `/drivers/<driver_id>` |
| `{{driverAssetsPath}}` | `/drivers/<driver_id>/assets` |
| `{{driverName}}` | `name.en` of the driver |
| `{{driverName<Xx>}}` | `name.<locale>` (falling back to `name.en`), e.g. `{{driverNameNl}}` |
| `{{zwaveParameterIndex}}` | The nearest enclosing `zwave.index` value |

A driver without a `name` property makes the placeholder pass throw `Missing property name in driver <driver_id>`.

---

## Device classes

The complete list Homey provides. "Min. Homey" is the class's `minCompatibility`: the app manifest's `compatibility`
range must allow at least that version, otherwise `homey app validate` fails.

| `class` | Title | Min. Homey | Use for |
| --- | --- | --- | --- |
| `airconditioning` | Air Conditioner | 12.0.0 | Use this device class for airconditioners, either portable or split type units. |
| `airfryer` | Air Fryer | 12.0.0 | Use this device class for air fryers. |
| `airpurifier` | Air Purifier | 12.0.0 | Use this device class for air purifiers. |
| `airtreatment` | Air Treatment | 12.0.0 | Use this device class for any type of air treatment appliance, when the `dehumidifier`, `humidifier`, `diffuser` or `airpurifier` device class doesn't apply. Could be for combi units. |
| `amplifier` | Amplifier | — | Use this device class for audio amplifier devices. |
| `battery` | Battery | 12.0.0 | Use this device for batteries, e.g. home battery storage. |
| `bicycle` | Bicycle | 12.0.0 | Use this device class for bicycles. |
| `blinds` | Blinds | — | Use this device class for blinds, both horizontal and vertical. |
| `boiler` | Boiler | 12.0.0 | Use this device class for any kind of boiler, e.g. heatpump boiler, gas boiler, hot water boiler, central heating boiler. |
| `bridge` | Bridge | 12.5.0 | Use this device class for bridges or hubs that connect to other devices or ecosystems. |
| `button` | Button | — | Use this device class for buttons, such as a remote. |
| `camera` | Camera | — | Security camera |
| `car` | Car | 12.0.0 | Use this device class for any kind of car. |
| `coffeemachine` | Coffee Machine | — | Use this device class for coffee machines. |
| `cooktop` | Cooktop | 12.0.0 | Use this device class for cooktops. |
| `curtain` | Curtains | — | Use this device class for curtains. |
| `dehumidifier` | Dehumidifier | 12.0.0 | Use this device class for dehumidifiers. |
| `diffuser` | Diffuser | 12.0.0 | User this device class for diffusers. |
| `dishwasher` | Dishwasher | 12.0.0 | Use this device class for dishwashers. |
| `doorbell` | Doorbell | — | Use this device class for doorbells, usually together with the `button` capability. |
| `dryer` | Dryer | 12.0.0 | Use this device class for dryers, if it is a combination washer/dryer use 'washer_and_dryer'. |
| `evcharger` | EV Charger | 12.0.0 | Use this device class for EV chargers. |
| `fan` | Fan | — | Use this device class for fans that cool your home. |
| `faucet` | Faucet | 12.0.0 | Use this device class for faucets. |
| `fireplace` | Fireplace | 12.0.0 | Use this device class for fireplaces. |
| `freezer` | Freezer | 12.0.0 | Use this device class for any kind of freezer, if it is a frigde/freezer use 'fridge_and_freezer'. |
| `fridge` | Fridge | 12.0.0 | Use this device class for any kind of fridge, if it is a fridge/freezer use 'fridge_and_freezer'. |
| `fridge_and_freezer` | Fridge & Freezer | 12.0.0 | Use this device class for any kind of refrigerator that also has a freezer. |
| `fryer` | Fryer | 12.0.0 | Use this device class for fryers. |
| `gameconsole` | Game Console | 12.0.0 | Use this device class for any type of game console. |
| `garagedoor` | Garage Door | — | Use this device class for garage doors, usually together with the `garagedoor_closed` capability. |
| `grill` | Grill | 12.0.0 | Use this device class for grills. |
| `heater` | Heater | — | Use this device class for heaters, that warm your home. |
| `heatpump` | Heat Pump | 12.0.0 | Use this device class for heat pumps. |
| `homealarm` | Home Security | — | Use this device class for home alarm systems. |
| `hood` | Hood | 12.0.0 | User this device class for any kind of extractor hood. |
| `humidifier` | Humidifier | 12.0.0 | Use this device class for humidifiers. |
| `kettle` | Kettle | — | Use this device class for kettle devices, that can heat water. |
| `lawnmower` | Lawn Mower | 12.0.0 | Use this device class for lawn mowers. |
| `light` | Light | — | Use this device class for lights, usually together with the `onoff`, `dim` and `light_*` capabilities. |
| `lock` | Lock | — | Use this device class for lock devices, usually together with the `locked` and `lock_mode` capabilities. |
| `mediaplayer` | Media Player | 12.0.0 | Use this device class for media players, when the `Set-top box` device class doesn't apply. |
| `microwave` | Microwave | 12.0.0 | Use this device class for any kind of microwave, if it is a combi unit use 'oven_and_microwave'. |
| `mop` | Mop | 12.0.0 | Use this device class for mops, e.g. a robot mop. |
| `multicooker` | Multicooker | 12.0.0 | Use this device class for multicookers. |
| `networkrouter` | Network Router | 12.0.0 | Use this device class for routers or modems. |
| `other` | Other | — | Use this device class for devices that do not fit any other device class. |
| `oven` | Oven | 12.0.0 | Use this device class for ovens. |
| `oven_and_microwave` | Combi Microwave Oven | 12.0.0 | Use this device class for combination microwave ovens. |
| `petfeeder` | Pet Feeder | 12.0.0 | Use this device class for pet feeders. |
| `pump` | Pump | 12.11.0 | Use this device class for pumps. |
| `radiator` | Radiator | 12.0.0 | Use this device class for radiators. |
| `relay` | Relay | — | Use this device class for relays, which are connected to another device. |
| `remote` | Remote | — | Use this device class for (TV/Sunblind/Keyfob etc.) remotes. |
| `scooter` | Scooter | 12.0.0 | Use this device class for scooters. |
| `sensor` | Sensor | — | Use this device class for sensors, e.g. a contact or motion sensor. |
| `service` | Service | 12.3.0 | Use this device class for devices that are not really physical devices, but (cloud) services. |
| `settopbox` | Set-top Box | 12.0.0 | Use this device class for set-top boxes. |
| `shutterblinds` | Shutter Blinds | 12.0.0 | Use this device class for shutter blinds. |
| `siren` | Siren | 12.0.0 | Use this device class for sirens. |
| `smokealarm` | Smoke Alarm | 12.0.0 | Use this device class for any smoke- or CO-alarm, could also be used for combo units. |
| `socket` | Wall Plug | — | Use this device class for sockets (built-in or plug-in socket switches). When adding the `choose_slave` pair template, the user is presented a `What's plugged in?` question. |
| `solarpanel` | Solar Panel | — | Use this device class for solar panels. |
| `speaker` | Speaker | — | Use this device class for devices that can play music, usually together with the `speaker_*` capabilities. |
| `sprinkler` | Sprinkler | 12.0.0 | Use this device class for sprinkler systems. |
| `sunshade` | Sunshade | — | Use this device class for sunshades (window coverings against the sun). |
| `thermostat` | Thermostat | — | Use this device class for thermostats, either for the entire home or radiator-mounted, usually together with the `measure_temperature`, `target_temperature` and `thermostat_mode` capabilities. |
| `tv` | TV | — | Use this device class for TVs. |
| `vacuumcleaner` | Vacuum Cleaner | — | Use this device class for vacuum cleaners, usually together with the `vacuumcleaner_state` capability. |
| `vehicle` | Vehicle | 12.0.0 | Use this device class for any type of vehicle, when the `car`, `bicycle` or `scooter` device class doesn't apply. |
| `washer` | Washing Machine | 12.0.0 | Use this device class for washing machines, if it is a combination washer/dryer use 'washer_and_dryer'. |
| `washer_and_dryer` | Washer & Dryer | 12.0.0 | Use this device class for any kind of washer and dryer combination. |
| `waterheater` | Water Heater | 12.0.0 | Use this device class for water heaters. |
| `waterpurifier` | Water Purifier | 12.0.0 | Use this device class for water purifiers. |
| `watervalve` | Water Valve | 12.0.0 | Use this device class for mechanical water valves. |
| `windowcoverings` | Window Coverings | — | Use this device class for window coverings, when the `curtains`, `blinds` or `sunshade` device class doesn't apply. |

### Virtual classes

A device can end up presenting itself as a class other than the driver's declared `class`. Homey exposes this on the
device object as `virtualClass` (visible in the Homey Web API / `homey list devices` output, where the effective
class is `device.class || device.virtualClass`). The documented way an app opts into this is the `choose_slave` pair
template on a `socket` driver: *"When adding the `choose_slave` pair template, the user is presented a `What's
plugged in?` question."* — the user's answer becomes the device's virtual class.

Do not guess which base classes accept which virtual classes; the Apps SDK does not document a mapping, and there is
no `virtualClass` key in the driver manifest schema. From an app you only ever set `class` (manifest) or
`Device#setClass()`.

---

## Device settings

Device settings are presented to the user as *Advanced settings* and are defined in
`/drivers/<driver_id>/driver.settings.compose.json` — a **JSON array** that Homey Compose merges into
`drivers[].settings`.

```json
[
  {
    "id": "username",
    "type": "text",
    "label": { "en": "Username" },
    "value": "John Doe",
    "hint": { "en": "The name of the user." }
  },
  {
    "id": "password",
    "type": "password",
    "label": { "en": "Password" },
    "value": "Secret",
    "hint": { "en": "The password of the user." }
  }
]
```

### Setting types

| `type` | `value` type | Extra keys | Description |
| --- | --- | --- | --- |
| `text` | string | `pattern` | Single-line text input. |
| `password` | string | `pattern` | Same as `text`, but the input is visually hidden. |
| `textarea` | string | `pattern` | Same as `text`, but allows multi-line input. |
| `label` | string | — | Read-only text field, for extra explanation or headings. Can only be updated by your app. |
| `number` | number | `units`, `min`, `max`, `step`, `attr` | Numeric input. |
| `slider` | number | `units`, `min`, `max`, `step`, `attr` | Numeric input rendered as a slider. |
| `checkbox` | boolean | — | `true` or `false`. |
| `dropdown` | string | `values` (**required**) | Pick one of a predefined set of choices. |
| `radio` | string | `values` (**required**) | Same shape as `dropdown`, rendered as radio buttons. |
| `group` | — | `label`, `children` (**required**) | Groups multiple settings under a label. Has **no `id`**. |

### Common attributes

| Key | Type | Required | Applies to | Description |
| --- | --- | --- | --- | --- |
| `id` | string | yes (except `group`) | all | Setting key used by `getSetting()` / `setSettings()`. Must be a string — the CLI throws for any other type. |
| `type` | string | yes | all | One of the types above. |
| `label` | i18n object | yes | all | Label shown to the user, e.g. `{ "en": "Username" }`. |
| `hint` | i18n object | no | all except `group` | Explanatory text under the setting. |
| `value` | per type | yes (per docs) | all except `group` | Initial value of the setting. |
| `pattern` | string | no | `text`, `password`, `textarea` | Regex the input must satisfy, e.g. `"[a-zA-Z]"` to allow only letters. |
| `units` | i18n object | no | `number`, `slider` | Unit shown next to the value, e.g. `{ "en": "minutes" }`. |
| `min` / `max` | number | no | `number`, `slider` | Bounds. |
| `step` | number (≥ 0) | no | `number`, `slider` | Increment. |
| `attr` | object | no | `number`, `slider` | Alternative nesting for `{ min, max, step }`. |
| `values` | array | yes | `dropdown`, `radio` | `[{ "id": "heating", "label": { "en": "Heating" } }]` — `id` is a string, `label` is an i18n object. |
| `children` | array | yes | `group` | Nested settings array (recursive, same schema). |
| `highlight` | `true` | no | all | Show this setting in the short "Highlighted Settings" list during pairing. |
| `zwave` | object | no | all | Maps the setting to a Z-Wave configuration parameter: `{ "index": number, "size": 1\|2\|4, "signed"?: boolean }`. See `references/wireless-zwave.md`. |
| `$extends` | string \| string[] | no | all | Compose-only: extend a settings template from `/.homeycompose/drivers/settings/<id>.json`. |
| `$id` | string | no | all | Compose-only: the resulting `id` when using `$extends` (defaults to the last template id). |

### Examples per type

```json
{ "id": "username",  "type": "text",     "label": { "en": "Username" },    "value": "John Doe", "hint": { "en": "The name of the user." } }
```
```json
{ "id": "password",  "type": "password", "label": { "en": "Password" },    "value": "Secret",   "hint": { "en": "The password of the user." } }
```
```json
{ "id": "description", "type": "textarea", "label": { "en": "Description" }, "value": "Initial description", "hint": { "en": "A custom device description." } }
```
```json
{ "id": "duration", "type": "number", "label": { "en": "Duration" }, "value": 3, "min": 0, "max": 5, "units": { "en": "minutes" } }
```
```json
{ "id": "allow_override", "type": "checkbox", "value": true, "label": { "en": "Allow override" } }
```
```json
{
  "id": "mode",
  "type": "dropdown",
  "value": "heating",
  "label": { "en": "Default mode" },
  "values": [
    { "id": "heating", "label": { "en": "Heating" } },
    { "id": "cooling", "label": { "en": "Cooling" } }
  ]
}
```
```json
{ "id": "label", "type": "label", "label": { "en": "IP address" }, "value": "192.168.0.10", "hint": { "en": "The IP address of the device." } }
```
```json
{
  "type": "group",
  "label": { "en": "Login details" },
  "children": [
    { "id": "username", "type": "text",     "label": { "en": "Username" }, "value": "John Doe" },
    { "id": "password", "type": "password", "label": { "en": "Password" }, "value": "Secret" }
  ]
}
```

### Highlighted settings

`"highlight": true` promotes a setting into a short list shown while pairing a new device, so users find the key
options quickly. Be selective — highlighting too many settings makes the highlighted list as hard to navigate as the
full one.

### Reserved setting-id prefixes

The following prefixes are **reserved by Homey** and **must not** be used at the start of a setting `id`
(the CLI warns for every violation, including inside `group` children):

```
homey:   zw_   zb_   mtr_   thread_   zone_   energy_   satellite_mode_   homekit_
```

### Reading and writing settings

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    const settings = this.getSettings();
    this.log(settings.username, this.getSetting('poll_interval'));

    await this.setSettings({
      // only provide the settings you want to change
      username: 'Jane Doe',
    });
  }

}

module.exports = MyDevice;
```

### The `onSettings` contract

```javascript
async onSettings({ oldSettings, newSettings, changedKeys }) {
  // runs when the USER has changed the device's settings in Homey.
  // changedKeys: Array<string> of keys changed since the previous version.

  if (newSettings.poll_interval < 5) {
    // throw to reject: the change is not saved and the message is shown to the user
    throw new Error('Poll interval must be at least 5 seconds');
  }

  this.restartPolling(newSettings.poll_interval);

  // optionally return a string: it is saved AND a custom message is displayed
  return this.homey.__('settings.applied');
}
```

| Aspect | Behaviour |
| --- | --- |
| Signature | `async onSettings(event) => Promise<string \| void>` where `event = { oldSettings, newSettings, changedKeys }` |
| `oldSettings` | object — the old settings object |
| `newSettings` | object — the new settings object |
| `changedKeys` | `Array<string>` — keys changed since the previous version |
| Throwing | The error message is shown to the user and they are asked to change their settings in order to store them; the change is not saved. |
| Returning a string | Resolves successfully and the returned string is displayed to the user as a custom message. |
| Triggered by | The **user** changing settings in the Homey app. |
| **Not** triggered by | `Device#setSettings()` — programmatic changes never fire `onSettings()`. |

---

## Gotchas

- **`getSetting()` / `getSettings()` return the OLD value inside `onSettings()`.** Settings are persisted only
  *after* the handler resolves, so during the handler the getters still reflect the pre-change state. Always read
  new values from the `newSettings` argument — restart a poll timer from `newSettings.poll_interval`, never from
  `this.getSetting('poll_interval')`.
- **`setSettings()` does NOT call `onSettings()`.** If a programmatic change must also run your side effects, call
  them explicitly after `await this.setSettings(...)`. Conversely, do not call `setSettings()` from inside
  `onSettings()` for a key the user just changed — you will fight the pending write.
- **Reserved setting-id prefixes** (`homey:`, `zw_`, `zb_`, `mtr_`, `thread_`, `zone_`, `energy_`,
  `satellite_mode_`, `homekit_`) trigger CLI warnings and can collide with Homey's own settings. Namespace your own
  ids differently.
- **Setting ids must be strings.** The JSON schema technically accepts a number, but the CLI's prefix check throws
  `invalid setting id: <x>, must be a string`.
- **There is no `Device#setSetting()` (singular).** Prose in the official docs links the words "`Device#setSetting()`"
  to the `setSettings` anchor, but the only method that exists is `setSettings(obj)`, which accepts a subset of
  settings. Writing `this.setSetting('x', 1)` throws `this.setSetting is not a function` at runtime.
- **There is no `color` device-setting type.** `color` is a *Flow argument* type (a HEX colour picker) — see
  `references/flow-cards.md`. Device settings only support the types in the table above.
- **`Driver#getDevice(deviceData)` needs the exact `data` object**, not an id string, and there is no
  `getDeviceById()`. Use `getDevices().find(...)` for anything else.
- **`data` is immutable after pairing.** Never put an IP address, hostname, token or firmware version in it — use
  the store, settings, or LAN discovery. Changing the shape of `data` in a later app version orphans every already
  paired device.
- **`addCapability()`, `removeCapability()` and `setCapabilityOptions()` are expensive** — call them only when
  something actually changed, guarded by `hasCapability()`, and never on every `onInit()`. Adding a capability to
  already-paired devices is a **migration**: gate it behind a store flag so it runs exactly once per device.

  ```javascript
  async onInit() {
    if (!this.getStoreValue('migrated_v2')) {
      if (!this.hasCapability('measure_power')) {
        await this.addCapability('measure_power');
      }
      await this.setStoreValue('migrated_v2', true);
    }
  }
  ```

- **Never overwrite the constructor** of `Homey.Driver` or `Homey.Device` — the SDK explicitly forbids it. Do all
  setup in `onInit()` and keep instance state as plain properties assigned there.
- **Register Flow cards once, in `App#onInit()` or `Driver#onInit()`** — never in `Device#onInit()`, which would
  attach one duplicate run listener per paired device. See `references/flow-cards.md`.
- **Fire-and-forget promises need `.catch(this.error)`.** An unhandled rejection can take the whole app down (fatal
  on Homey Cloud), so every un-awaited `setCapabilityValue()` / `setStoreValue()` / `setAvailable()` gets a catch.
- **`setClass()` and `removeCapability()` break existing Flows** that depend on the old class/capability. Treat both
  as migrations, not routine calls.
- **Throwing inside `onDiscoveryAvailable()` makes the device unavailable** with the thrown message — that is the
  intended way to report a failed initial connection, not a bug.
- **Unavailable devices block all capabilities and Flow actions.** Do not use `setUnavailable()` for transient
  conditions the user can still act on; use `setWarning()` there.
- **`setWarning()` is persistent** — it survives restarts until `unsetWarning()` (or `setWarning(null)`) is called.
- **`setLastSeenAt()` requires Homey v12.6.1+**; guard it if the app manifest's `compatibility` allows older
  versions.
- **A `cloud` driver cannot declare `lan`, `matter` or `rf868` connectivity** — `homey app validate` fails.
- **`platforms` defaults to `["local"]`**, and the CLI only warns (does not fail) when a driver omits it in an app
  that supports `cloud`. A missing `platforms` silently keeps the driver off Homey Cloud.
- **`platforms` and `connectivity` are both required to publish a *verified* app**, and `images` is required to
  publish at all.
- **Driver id = folder name.** Renaming `/drivers/<id>/` changes the driver id and orphans paired devices. Never
  hand-write `"id"` in `driver.compose.json`.
- **Timers must use `this.homey.setTimeout` / `setInterval` / `clearTimeout` / `clearInterval`**, which are disposed
  correctly on app teardown; plain globals leak on Homey Cloud. Clear them in both `onDeleted()` and `onUninit()`.
- **The device store is also the practical place for a capped rolling history buffer**, because capability Insights
  are write-only from inside the App SDK (see `references/capabilities.md`).
- **Every driver is instantiated even with zero paired devices.** `Driver#onInit()` always runs, which is why
  driver-level Flow card registration and pairing work before any device exists. Conversely, never assume
  `getDevices()` is non-empty — guard array access and `find()` results.
- **`getCapabilityValue()` returns `null` when the value is unknown**, not `undefined` and not a type-appropriate
  default. Guard before arithmetic or `.toFixed()`.
- **`getEnergy()` does not return the manifest's `energy` object** — only an override set with `setEnergy()`. And
  once `setEnergy()` has been called for a device, later edits to `energy` in `driver.compose.json` stop being
  applied to it automatically.
- **`"deprecated": false` is invalid.** The schema enum allows only `true`; delete the key to un-deprecate.
- **Matter drivers must not ship `driver.js`/`device.js`** and must not define `pair` views — validation fails
  outright. They also require `connectivity` to include `matter`.
- **Driver ids allow only letters, numbers, `-` and `_`.** The CLI refuses anything else, and refuses to create a
  driver whose directory already exists.
- **Only `images.small` and `images.large` are pixel-validated** (`.png` / `.jpg` / `.jpeg`, checked by extension,
  magic bytes and exact dimensions). `xlarge` is optional and not size-checked — but ship it correct anyway.

---

## Sources

- <https://apps.developer.homey.app/the-basics/devices>
- <https://apps.developer.homey.app/the-basics/devices/settings>
- <https://apps.developer.homey.app/the-basics/devices/best-practices>
- <https://apps.developer.homey.app/the-basics/devices/pairing>
- <https://apps.developer.homey.app/advanced/homey-compose>
- <https://apps.developer.homey.app/guides/how-to-breaking-changes>
- <https://apps.developer.homey.app/wireless/wi-fi/discovery>
- <https://apps-sdk-v3.developer.homey.app/Driver.html>
- <https://apps-sdk-v3.developer.homey.app/Device.html>
- <https://apps-sdk-v3.developer.homey.app/ManagerDrivers.html>
- <https://apps-sdk-v3.developer.homey.app/tutorial-device-classes.html>
