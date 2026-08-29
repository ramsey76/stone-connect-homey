# Homey Apps SDK v3 — JavaScript API Index

Complete signature index of every class documented on <https://apps-sdk-v3.developer.homey.app>
(70 class pages). Use it to verify that a method exists and what its exact arguments, optionality
and return type are, without a web lookup. Everything below is transcribed from the reference site;
nothing is inferred.

The reference site hosts 73 pages in total: the 70 class pages indexed here, `index.html`, and two
non-API tutorial pages (`tutorial-device-capabilities.html`, `tutorial-device-classes.html`) whose
content is covered by `references/capabilities.md`.

**Two runtime APIs have no page on this reference site:**

| Missing from the JS reference | Where it is documented |
| --- | --- |
| `ManagerDashboards` — `this.homey.dashboards`, entry point for dashboard widgets (`getWidget(id)`) | `references/widgets.md`, `references/python-apps.md` |
| `ManagerSpeechInput` — exposed as the `Homey#speechInput` property, but `ManagerSpeechInput.html` does not exist (HTTP 403) | not documented on the JS reference site |

Both exist at runtime; `Homey#speechInput` is listed as an instance property on `Homey.html`, and
`ManagerDashboards` is reachable as `this.homey.dashboards`.

---

## 1. Notation used in this file

| Marker | Meaning |
| --- | --- |
| `async` prefix | The reference marks the method `(async)`; it returns a Promise. |
| `argopt` / `arg?` | Argument is `<optional>` on the reference page. Written `arg?` here. |
| `…args` | Repeatable argument (`<repeatable>`). |
| `→ Type` | Documented return type. Absent `→` means the page documents no return value. |
| `Array.<T>` / `Object.<K, V>` | JSDoc types, reproduced verbatim from the site. |

Every class heading carries its doc URL: `https://apps-sdk-v3.developer.homey.app/<Class>.html`.

## 2. Manager map — `this.homey.<id>`

Access every manager through the `Homey` instance. `this.homey` is available on `App`, `Driver` and
`Device`, and is passed into API handlers.

| Property | Class | Doc URL |
| --- | --- | --- |
| `this.homey.api` | `ManagerApi` | [ManagerApi.html](https://apps-sdk-v3.developer.homey.app/ManagerApi.html) |
| `this.homey.apps` | `ManagerApps` | [ManagerApps.html](https://apps-sdk-v3.developer.homey.app/ManagerApps.html) |
| `this.homey.arp` | `ManagerArp` | [ManagerArp.html](https://apps-sdk-v3.developer.homey.app/ManagerArp.html) |
| `this.homey.audio` | `ManagerAudio` | [ManagerAudio.html](https://apps-sdk-v3.developer.homey.app/ManagerAudio.html) |
| `this.homey.ble` | `ManagerBLE` | [ManagerBLE.html](https://apps-sdk-v3.developer.homey.app/ManagerBLE.html) |
| `this.homey.clock` | `ManagerClock` | [ManagerClock.html](https://apps-sdk-v3.developer.homey.app/ManagerClock.html) |
| `this.homey.cloud` | `ManagerCloud` | [ManagerCloud.html](https://apps-sdk-v3.developer.homey.app/ManagerCloud.html) |
| `this.homey.discovery` | `ManagerDiscovery` | [ManagerDiscovery.html](https://apps-sdk-v3.developer.homey.app/ManagerDiscovery.html) |
| `this.homey.drivers` | `ManagerDrivers` | [ManagerDrivers.html](https://apps-sdk-v3.developer.homey.app/ManagerDrivers.html) |
| `this.homey.flow` | `ManagerFlow` | [ManagerFlow.html](https://apps-sdk-v3.developer.homey.app/ManagerFlow.html) |
| `this.homey.geolocation` | `ManagerGeolocation` | [ManagerGeolocation.html](https://apps-sdk-v3.developer.homey.app/ManagerGeolocation.html) |
| `this.homey.i18n` | `ManagerI18n` | [ManagerI18n.html](https://apps-sdk-v3.developer.homey.app/ManagerI18n.html) |
| `this.homey.images` | `ManagerImages` | [ManagerImages.html](https://apps-sdk-v3.developer.homey.app/ManagerImages.html) |
| `this.homey.insights` | `ManagerInsights` | [ManagerInsights.html](https://apps-sdk-v3.developer.homey.app/ManagerInsights.html) |
| `this.homey.ledring` | `ManagerLedring` | [ManagerLedring.html](https://apps-sdk-v3.developer.homey.app/ManagerLedring.html) |
| `this.homey.nfc` | `ManagerNFC` | [ManagerNFC.html](https://apps-sdk-v3.developer.homey.app/ManagerNFC.html) |
| `this.homey.notifications` | `ManagerNotifications` | [ManagerNotifications.html](https://apps-sdk-v3.developer.homey.app/ManagerNotifications.html) |
| `this.homey.rf` | `ManagerRF` | [ManagerRF.html](https://apps-sdk-v3.developer.homey.app/ManagerRF.html) |
| `this.homey.settings` | `ManagerSettings` | [ManagerSettings.html](https://apps-sdk-v3.developer.homey.app/ManagerSettings.html) |
| `this.homey.speechInput` | `ManagerSpeechInput` | *(no page on the reference site)* |
| `this.homey.speechOutput` | `ManagerSpeechOutput` | [ManagerSpeechOutput.html](https://apps-sdk-v3.developer.homey.app/ManagerSpeechOutput.html) |
| `this.homey.videos` | `ManagerVideos` | [ManagerVideos.html](https://apps-sdk-v3.developer.homey.app/ManagerVideos.html) |
| `this.homey.zigbee` | `ManagerZigBee` | [ManagerZigBee.html](https://apps-sdk-v3.developer.homey.app/ManagerZigBee.html) |
| `this.homey.zwave` | `ManagerZwave` | [ManagerZwave.html](https://apps-sdk-v3.developer.homey.app/ManagerZwave.html) |
| `this.homey.dashboards` | `ManagerDashboards` | *(no page — see `references/widgets.md`)* |

`ManagerVideos` is listed under `this.homey.videos` on its own page but is **not** listed among the
`Homey` instance properties on `Homey.html`.

---

## 3. Core

### 3.1 `SimpleClass` — [SimpleClass.html](https://apps-sdk-v3.developer.homey.app/SimpleClass.html)

Base class with log functions. `Homey` and `App` extend it.

| Signature | Notes |
| --- | --- |
| `new SimpleClass()` | Constructor. |
| `log(…args: *)` | Emits the `__log` event with `args` as parameters. |
| `error(…args: *)` | Emits the `__error` event with `args` as parameters. |

### 3.2 `App` — [App.html](https://apps-sdk-v3.developer.homey.app/App.html)

Extends `SimpleClass`. Extend and export from `/app.js`. Methods prefixed with `on` are meant to be
overridden. **It is not allowed to overwrite the constructor.**

**Instance properties**

| Property | Type | Description |
| --- | --- | --- |
| `homey` | `Homey` | The Homey instance of this app |
| `id` | `string` | The app id |
| `manifest` | `any` | The `app.json` manifest |
| `sdk` | `number` | The app sdk version |

**Instance methods**

| Signature | Notes |
| --- | --- |
| `async onInit()` | Called upon initialization of your app. |
| `async onUninit()` | Called when your app is destroyed. |
| `log(…args: *)` | Emits `__log`. |
| `error(…args: *)` | Emits `__error`. |

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.log('MyApp has been initialized');
  }

}

module.exports = MyApp;
```

### 3.3 `Driver` — [Driver.html](https://apps-sdk-v3.developer.homey.app/Driver.html)

Manages all `Device` instances, which represent all paired devices. Extend and export from
`/drivers/<id>/driver.js`. Methods prefixed with `on` are meant to be overridden. **It is not
allowed to overwrite the constructor.**

**Instance properties**

| Property | Type | Description |
| --- | --- | --- |
| `homey` | `Homey` | The Homey instance of this driver |
| `manifest` | `any` | The driver's manifest (`app.json` entry) |

**Instance methods**

| Signature | Notes |
| --- | --- |
| `getDevice(deviceData: object) → Device` | `deviceData` = unique Device object as provided during pairing. |
| `getDevices() → Array.<Device>` | All `Device` instances. |
| `getDiscoveryStrategy() → DiscoveryStrategy` | The driver's discovery strategy when defined in the manifest. |
| `async onInit()` | Called when the driver is inited. |
| `async onUninit()` | Called when the driver is destroyed. |
| `onMapDeviceClass(device: Device)` | When this method exists it is called prior to initing the device instance. Return a class that extends `Device`. The passed `device` exists for a single tick and **does not support async methods**. |
| `onPair(session: PairSession)` | Called when a pair session starts. `session` is a bi-directional socket for communication with the front-end. |
| `async onPairListDevices() → Promise.<Array.<any>>` | Called when no custom `onPair()` has been defined and the default is used. Simple drivers should override this to provide a list of devices ready to be paired. |
| `async ready() → Promise.<void>` | Resolves when the Driver is ready (`Driver#onInit` has been run). |

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  async onInit() {
    this.log('MyDriver has been initialized');
  }

  onMapDeviceClass(device) {
    if (device.hasCapability('dim')) {
      return MyDeviceDim;
    }
    return MyDevice;
  }

}

module.exports = MyDriver;
```

### 3.4 `Device` — [Device.html](https://apps-sdk-v3.developer.homey.app/Device.html)

A representation of a device paired in Homey. Extend and export from `/drivers/<id>/device.js`, or
any custom class returned by `Driver#onMapDeviceClass`. Methods prefixed with `on` are meant to be
overridden. **It is not allowed to overwrite the constructor.**
The reference page documents **no events** on `Device`.

**Instance properties**

| Property | Type | Description |
| --- | --- | --- |
| `driver` | `Driver` | The device's driver instance |
| `homey` | `Homey` | The Homey instance of this app |

**Getters**

| Signature | Returns |
| --- | --- |
| `getAvailable() → boolean` | If the device is marked as available |
| `getCapabilities() → Array.<string>` | The device's capabilities array |
| `getCapabilityOptions(capabilityId: string) → any` | A device's capability options |
| `getCapabilityValue(capabilityId: string) → any` | The value, or `null` when unknown |
| `getClass() → string` | The device's class |
| `getData() → any` | The device's data object |
| `getEnergy() → any` | The device's energy info object |
| `getName() → string` | The device's name |
| `getSetting(key: string) → any` | The value, or `null` when unknown |
| `getSettings() → any` | The device's settings object |
| `getState() → any` | The device's state object (capability values) |
| `getStore() → any` | The entire store |
| `getStoreKeys() → Array.<string>` | All store keys |
| `getStoreValue(key: string) → any` | value |
| `hasCapability(capabilityId: string) → boolean` | `true` if the device has that capability |

**Setters / mutators**

| Signature | Notes |
| --- | --- |
| `async addCapability(capabilityId: string)` | **Expensive method** — use only when needed. |
| `async removeCapability(capabilityId: string)` | Any Flow depending on this capability becomes broken. **Expensive method.** |
| `async setCapabilityOptions(capabilityId: string, options: object)` | **Expensive method.** |
| `async setCapabilityValue(capabilityId: string, value: any) → Promise.<void>` | |
| `async setClass(deviceClass: string) → Promise.<void>` | Any Flow depending on this class becomes broken. |
| `async setEnergy(energy: object)` | Set the device's energy object. |
| `async setSettings(settings: any) → Promise.<void>` | May contain a subset of all settings. **`Device#onSettings` is NOT called** when settings are changed programmatically. |
| `async setStoreValue(key: string, value: any) → Promise.<void>` | |
| `async unsetStoreValue(key: string) → Promise.<void>` | |
| `async setAvailable() → Promise.<any>` | Availability → `true`. |
| `async setUnavailable(message?: string\|null) → Promise.<any>` | Custom unavailable message, or `null` for default. |
| `async setWarning(message?: string\|null) → Promise.<any>` | Custom warning message shown to the user, or `null` to unset the warning. Persistent — unset it when necessary. |
| `async unsetWarning() → Promise.<any>` | |
| `async setLastSeenAt()` | Call when the device is known to be alive and responding. **Available since Homey v12.6.1.** |
| `async setAlbumArtImage(image: Image) → Promise.<any>` | |
| `async setCameraImage(id: string, title: string, image: Image) → Promise.<any>` | `id` e.g. `front`, `title` e.g. `Front`. |
| `async setCameraVideo(id: string, title: string, video: Video) → Promise.<any>` | `id` e.g. `front_door`, `title` e.g. `Front Door`. |

**Capability listeners**

| Signature | Notes |
| --- | --- |
| `registerCapabilityListener(capabilityId: string, listener: Device.CapabilityCallback)` | Invoked when a device's state change is requested. |
| `registerMultipleCapabilityListener(capabilityIds: Array.<string>, listener: Device.MultipleCapabilityCallback, timeout: number = 250)` | Debounced with `timeout` ms. |
| `async triggerCapabilityListener(capabilityId: string, value: any, opts: object) → Promise.<any>` | Trigger a capability listener programmatically. |

**Lifecycle / overridable methods**

| Signature | Notes |
| --- | --- |
| `async onInit()` | Called when the device is loaded and name, capabilities and state are available. |
| `async onUninit()` | Called when the device is destroyed. |
| `onAdded()` | Called when the user adds the device, just after pairing. |
| `onDeleted()` | Called when the user deleted the device. |
| `onRenamed(name: string)` | Called when the user updates the device's name. |
| `async onSettings(event: object) → Promise.<(string\|void)>` | `event = { oldSettings: object, newSettings: object, changedKeys: Array.<string> }`. Return a custom message that will be displayed. |
| `async ready() → Promise.<void>` | Resolves when the Device is ready (`Device#onInit` has been run). |
| `onDiscoveryResult(discoveryResult: DiscoveryResult)` | Return truthy when the result belongs to this device. **Defaults to matching on the device's `data.id` property.** |
| `onDiscoveryAvailable(discoveryResult: DiscoveryResult)` | Called when the device is found for the first time. Overload to create a connection. **Throwing here makes the device unavailable with the error message.** |
| `onDiscoveryAddressChanged(discoveryResult: DiscoveryResult)` | Called when the device's address has changed. |
| `onDiscoveryLastSeenChanged(discoveryResult: DiscoveryResult)` | Called when the device has been found again. |

**Type definitions**

| Type | Signature |
| --- | --- |
| `Device.CapabilityCallback` | `(value: any, opts: any) → Promise.<void>\|void` — `opts` is an object with optional properties, e.g. `{ duration: 300 }` |
| `Device.MultipleCapabilityCallback` | `(capabilityValues: Object.<string, any>, capabilityOptions: Object.<string, any>) → Promise.<void>\|void` — e.g. `{ dim: 0.5 }` and `{ dim: { duration: 300 } }` |

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
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

    this.homey.setInterval(() => {
      this.setCapabilityValue('measure_temperature', 21.5).catch(this.error);
    }, 60000);
  }

  async onSettings({ oldSettings, newSettings, changedKeys }) {
    this.log('changed', changedKeys);
  }

}

module.exports = MyDevice;
```

### 3.5 `Homey` — [Homey.html](https://apps-sdk-v3.developer.homey.app/Homey.html)

Extends `SimpleClass`. Holds all Managers, System Events and generic properties. Accessible as
`this.homey` on `App`, `Driver` and `Device`, and passed into API handlers.

**Non-manager instance properties**

| Property | Type | Description |
| --- | --- | --- |
| `app` | `App` | A pointer to the App's instance |
| `env` | `any` | The `env.json` environment variables |
| `manifest` | `any` | The `app.json` manifest |
| `platform` | `'local'\|'cloud'` | May be `undefined` on older Homey Pro versions |
| `platformVersion` | `1\|2` | May be `undefined` on older Homey Pro versions |
| `platformFeatures` | `Array.<string>` | Features supported by the Homey running this app |
| `version` | `string` | The software version of the Homey running this app |

Manager properties: `api`, `apps`, `arp`, `audio`, `ble`, `clock`, `cloud`, `discovery`, `drivers`,
`flow`, `geolocation`, `i18n`, `images`, `insights`, `ledring`, `nfc`, `notifications`, `rf`,
`settings`, `speechInput`, `speechOutput`, `zigbee`, `zwave` (see §2).

**Platform matrix** (from `Homey.html`)

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

> On older software versions either `platform` or `platformVersion` might be `undefined`. In such
> case, assume `platform === 'local'` and `platformVersion === 1`.

**Instance methods**

| Signature | Notes |
| --- | --- |
| `__(key: string\|Object, tags?: Object) → string` | Shortcut to `ManagerI18n#__`. |
| `hasFeature(feature: string) → boolean` | **Available since Homey v12.7.1.** `feature` is one of: `speaker`, `ledring`, `nfc`, `camera-streaming`, `matter`. |
| `hasPermission(permission: string) → boolean` | |
| `setTimeout(callback: function, ms: number, …args: any) → NodeJS.Timer` | Alias to `setTimeout` that ensures the timeout is correctly disposed of when the Homey instance gets destroyed. |
| `setInterval(callback: function, ms: number, …args: any) → NodeJS.Timer` | Alias to `setInterval` with the same disposal guarantee. |
| `clearTimeout(timeoutId: any)` | Alias to `clearTimeout`. |
| `clearInterval(timeoutId: any)` | Alias to `clearInterval`. |
| `log(…args: *)` | Emits `__log`. |
| `error(…args: *)` | Emits `__error`. |

**Events**

| Event | Payload | Description |
| --- | --- | --- |
| `cpuwarn` | `data: { count: number, limit: number }` | The app is using too much CPU. `count` = warnings already sent, `limit` = max warnings until the app is killed. When the app does not behave within a reasonable amount of time, the app is killed. |
| `memwarn` | `data: { count: number, limit: number }` | The app is using too much memory. Same semantics, same kill behaviour. |
| `unload` | — | The app is being stopped. |

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.homey.on('memwarn', ({ count, limit }) => {
      this.log(`memwarn ${count}/${limit}`);
    });

    this.homey.on('unload', () => this.log('unloading'));

    const latitude = this.homey.geolocation.getLatitude();
    this.log('Latitude:', latitude);

    if (typeof this.homey.hasFeature === 'function' && this.homey.hasFeature('ledring')) {
      this.log('this Homey has a LED ring');
    }
  }

}

module.exports = MyApp;
```

---

## 4. Managers

### 4.1 `ManagerApps` — [ManagerApps.html](https://apps-sdk-v3.developer.homey.app/ManagerApps.html)

| Signature | Notes |
| --- | --- |
| `async getInstalled(appInstance: ApiApp) → Promise.<boolean>` | Whether an app is installed, enabled and running. |
| `async getVersion(appInstance: ApiApp) → Promise.<string>` | An installed app's version. |

### 4.2 `ManagerArp` — [ManagerArp.html](https://apps-sdk-v3.developer.homey.app/ManagerArp.html)

| Signature | Notes |
| --- | --- |
| `async getMAC(ip: string) → Promise.<string>` | Get an IP's MAC address. |

### 4.3 `ManagerClock` — [ManagerClock.html](https://apps-sdk-v3.developer.homey.app/ManagerClock.html)

| Signature | Notes |
| --- | --- |
| `getTimezone() → string` | Current TimeZone. |

| Event | Payload |
| --- | --- |
| `timezoneChange` | `timezone: string` — the new timezone |

### 4.4 `ManagerDrivers` — [ManagerDrivers.html](https://apps-sdk-v3.developer.homey.app/ManagerDrivers.html)

| Signature | Notes |
| --- | --- |
| `getDriver(driverId: string) → Driver` | `driverId` as defined in `app.json`. |
| `getDrivers() → Object.<string, Driver>` | All `Driver` instances keyed by ID. |

### 4.5 `ManagerGeolocation` — [ManagerGeolocation.html](https://apps-sdk-v3.developer.homey.app/ManagerGeolocation.html)

All methods and the `location` event require the **`homey:manager:geolocation`** permission.

| Signature | Returns |
| --- | --- |
| `getLatitude() → number` | latitude |
| `getLongitude() → number` | longitude |
| `getAccuracy() → number` | accuracy (in meter) |
| `getMode() → string` | `auto` or `manual` |

| Event | Payload |
| --- | --- |
| `location` | — (fired when the location is updated) |

### 4.6 `ManagerI18n` — [ManagerI18n.html](https://apps-sdk-v3.developer.homey.app/ManagerI18n.html)

| Signature | Notes |
| --- | --- |
| `__(key: string, tags: object) → string\|null` | Translate a string from `/locales/<language>.json`. Returns `null` when the key was not found. `tags` replaces `__name__`-style placeholders. Also available as `Homey#__`. |
| `getLanguage() → string` | Homey's current language, a 2-character string (e.g. `en`). |
| `getUnits() → string` | `metric` or `imperial`. |

```javascript
// /locales/en.json → { "welcome": "Welcome, __name__!" }
const welcomeMessage = this.homey.__('welcome', { name: 'Dave' });
// "Welcome, Dave!"

// Inline object form (Homey#__ only):
this.homey.__({ en: 'My String', nl: 'Mijn tekst' });
```

### 4.7 `ManagerSettings` — [ManagerSettings.html](https://apps-sdk-v3.developer.homey.app/ManagerSettings.html)

Synchronous — none of these are async.

| Signature | Notes |
| --- | --- |
| `get(key: string) → any` | value |
| `set(key: string, value: any)` | |
| `unset(key: string)` | Unset (delete) a setting. |
| `getKeys() → Array.<string>` | All settings keys. |

| Event | Payload |
| --- | --- |
| `set` | `key: string` — a setting has been set |
| `unset` | `key: string` — a setting has been unset |

### 4.8 `ManagerInsights` — [ManagerInsights.html](https://apps-sdk-v3.developer.homey.app/ManagerInsights.html)

| Signature | Notes |
| --- | --- |
| `async createLog(id: string, options: object) → Promise.<InsightsLog>` | `id` must be lowercase, alphanumeric. |
| `async getLog(id: string) → Promise.<InsightsLog>` | |
| `async getLogs() → Promise.<Array.<InsightsLog>>` | All logs belonging to this app. |
| `async deleteLog(log: InsightsLog) → Promise.<any>` | |

`createLog` `options`:

| Key | Type | Optional | Description |
| --- | --- | --- | --- |
| `title` | `string` | no | Log's title |
| `type` | `string` | no | Value type: `number` or `boolean` |
| `units` | `string` | yes | Units of the values, e.g. `°C` |
| `decimals` | `number` | yes | Number of decimals visible |

#### `InsightsLog` — [InsightsLog.html](https://apps-sdk-v3.developer.homey.app/InsightsLog.html)

Never instanced manually; retrieve via `ManagerInsights`.

| Signature | Notes |
| --- | --- |
| `async createEntry(value: number\|boolean) → Promise.<any>` | Create a new log entry. |

### 4.9 `ManagerNotifications` — [ManagerNotifications.html](https://apps-sdk-v3.developer.homey.app/ManagerNotifications.html)

| Signature | Notes |
| --- | --- |
| `async createNotification(options: object)` | `options = { excerpt: string }` — a short message. Use `**double astrisks**` to highlight variable words. |

---

## 5. Flow

### 5.1 `ManagerFlow` — [ManagerFlow.html](https://apps-sdk-v3.developer.homey.app/ManagerFlow.html)

| Signature | Notes |
| --- | --- |
| `getTriggerCard(id: string) → FlowCardTrigger` | `id` as defined in `app.json`. |
| `getDeviceTriggerCard(id: string) → FlowCardTriggerDevice` | |
| `getConditionCard(id: string) → FlowCardCondition` | |
| `getActionCard(id: string) → FlowCardAction` | |
| `async createToken(id: string, opts: object) → Promise.<FlowToken>` | `id` should be alphanumeric. |
| `getToken(id: string) → FlowToken` | `id` as provided in `createToken`. |
| `async unregisterToken(tokenInstance: FlowToken) → Promise.<any>` | |

`createToken` `opts`:

| Key | Type | Description |
| --- | --- | --- |
| `type` | `string` | `string`, `number`, `boolean` or `image` |
| `title` | `string` | Title of the token |
| `value` | `*` | Initial value of the token |

### 5.2 `FlowCard` — [FlowCard.html](https://apps-sdk-v3.developer.homey.app/FlowCard.html)

Base class for all Flow cards; programmatic representation of a card defined in `/app.json`.

| Signature | Notes |
| --- | --- |
| `getArgument(name: string) → FlowArgument` | |
| `registerRunListener(listener: FlowCard.RunCallback) → FlowCard` | Chainable. |
| `registerArgumentAutocompleteListener(name: string, listener: FlowCard.ArgumentAutocompleteCallback) → FlowCard` | Fired when the argument is of type `autocomplete` and the user typed a query. |

| Event | Description |
| --- | --- |
| `update` | Fired when the card is updated by the user (e.g. a Flow has been saved). |

**Type definitions**

| Type | Signature / shape |
| --- | --- |
| `FlowCard.RunCallback` | `(args: any, state: any) → Promise.<any>\|any` — `args` keys are defined in `/app.json`; `state` is the state of the Flow |
| `FlowCard.ArgumentAutocompleteCallback` | `(query: string, args: any) → Promise.<FlowCard.ArgumentAutocompleteResults>\|FlowCard.ArgumentAutocompleteResults` — `args` is the current state of the arguments as selected in the front-end |
| `FlowCard.ArgumentAutocompleteResults` | `object` with `name: string`, `description?: string`, `icon?: string`, `image?: string` |

### 5.3 Subclass matrix

| Class | Extends | Extra members | Doc URL |
| --- | --- | --- | --- |
| `FlowCardAction` | `FlowCard` | `async getArgumentValues() → Promise.<Array.<any>>` | [FlowCardAction.html](https://apps-sdk-v3.developer.homey.app/FlowCardAction.html) |
| `FlowCardCondition` | `FlowCard` | `async getArgumentValues() → Promise.<Array.<any>>` | [FlowCardCondition.html](https://apps-sdk-v3.developer.homey.app/FlowCardCondition.html) |
| `FlowCardTrigger` | `FlowCard` | `async getArgumentValues() → Promise.<Array.<any>>`, `async trigger(tokens?: object, state?: object) → Promise.<any>` | [FlowCardTrigger.html](https://apps-sdk-v3.developer.homey.app/FlowCardTrigger.html) |
| `FlowCardTriggerDevice` | `FlowCard` | `async getArgumentValues(device: Device) → Promise.<Array.<any>>`, `async trigger(device: Device, tokens?: object, state?: object) → Promise.<any>` | [FlowCardTriggerDevice.html](https://apps-sdk-v3.developer.homey.app/FlowCardTriggerDevice.html) |

`getArgumentValues()` resolves to an array of key-value objects with the argument's name as key;
every array entry represents one Flow card. `FlowCardTriggerDevice` is the class for a card with
type `trigger` and an argument with type `device` and a filter with `driver_id`.

All four subclasses also expose `getArgument`, `registerRunListener`,
`registerArgumentAutocompleteListener` and the `update` event, inherited from `FlowCard`.

### 5.4 `FlowArgument` — [FlowArgument.html](https://apps-sdk-v3.developer.homey.app/FlowArgument.html)

Must not be initiated by the developer; retrieve via `FlowCard#getArgument`.

| Signature | Notes |
| --- | --- |
| `registerAutocompleteListener(listener: FlowCard.ArgumentAutocompleteCallback) → FlowArgument` | Chainable. |

### 5.5 `FlowToken` — [FlowToken.html](https://apps-sdk-v3.developer.homey.app/FlowToken.html)

Creates a Tag in the Flow Editor.

| Signature | Notes |
| --- | --- |
| `async setValue(value: string\|number\|boolean\|Image) → Promise.<any>` | Must be of the same type as defined in the Token instance. |
| `async unregister() → Promise.<any>` | Shorthand for `ManagerFlow#unregisterToken`. |

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const actionCard = this.homey.flow.getActionCard('my_action');

    actionCard.registerRunListener(async (args, state) => {
      this.log('running with', args, state);
      return true;
    });

    actionCard.registerArgumentAutocompleteListener('my_arg', async (query, args) => {
      const results = [
        {
          name: 'Value name',
          description: 'Optional description',
          icon: 'https://path.to/icon.svg',
          id: '...',
        },
      ];
      return results.filter((result) => result.name.toLowerCase().includes(query.toLowerCase()));
    });

    const triggerCard = this.homey.flow.getTriggerCard('my_trigger');
    await triggerCard.trigger({ my_token: 42 }, { my_state: 'x' });

    const token = await this.homey.flow.createToken('my_token', {
      type: 'number',
      title: 'My Token',
      value: 0,
    });
    await token.setValue(1);
  }

}

module.exports = MyApp;
```

---

## 6. Pairing

### `PairSession` — [PairSession.html](https://apps-sdk-v3.developer.homey.app/PairSession.html)

Returned by `Driver#onPair`.

| Signature | Notes |
| --- | --- |
| `setHandler(event: string, handler: PairSession.Handler) → this` | Accepts async functions that can receive and respond to messages from the pair view. Chainable. |
| `async emit(event: string, data: any) → Promise.<any>` | |
| `async showView(viewId: string) → Promise.<void>` | Show a specific pairing step by its id. |
| `async nextView() → Promise.<void>` | |
| `async prevView() → Promise.<void>` | |
| `async done() → Promise.<void>` | Close the pairing session. |

**Type definitions**

| Type | Signature |
| --- | --- |
| `PairSession.Handler` | `async (data: any) → Promise.<any>` |

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  onPair(session) {
    let username = null;

    session.setHandler('login', async (data) => {
      username = data.username;
      return true;
    });

    session.setHandler('list_devices', async () => {
      return [{ name: 'Device', data: { id: 'abcd' }, store: { username } }];
    });
  }

}

module.exports = MyDriver;
```

---

## 7. Discovery

### 7.1 `ManagerDiscovery` — [ManagerDiscovery.html](https://apps-sdk-v3.developer.homey.app/ManagerDiscovery.html)

| Signature | Notes |
| --- | --- |
| `getStrategy(strategyId: string) → DiscoveryStrategy` | `strategyId` as defined in your `app.json`. |

### 7.2 `DiscoveryStrategy` — [DiscoveryStrategy.html](https://apps-sdk-v3.developer.homey.app/DiscoveryStrategy.html)

Not instanced manually; created by `ManagerDiscovery#getStrategy`.

| Signature | Notes |
| --- | --- |
| `getDiscoveryResult(id: string) → DiscoveryResultMDNSSD\|DiscoveryResultSSDP\|DiscoveryResultMAC` | |
| `getDiscoveryResults() → Object.<string, (DiscoveryResultMDNSSD\|DiscoveryResultSSDP\|DiscoveryResultMAC)>` | All results as an object. |

| Event | Payload |
| --- | --- |
| `result` | `discoveryResult: DiscoveryResultMDNSSD\|DiscoveryResultSSDP\|DiscoveryResultMAC` |

### 7.3 `DiscoveryResult` and subclasses

`DiscoveryResult` is the base class for `DiscoveryResultMAC`, `DiscoveryResultMDNSSD` and
`DiscoveryResultSSDP`. None may be instanced manually. All four expose the same two events.

| Class | Doc URL |
| --- | --- |
| `DiscoveryResult` | [DiscoveryResult.html](https://apps-sdk-v3.developer.homey.app/DiscoveryResult.html) |
| `DiscoveryResultMAC` | [DiscoveryResultMAC.html](https://apps-sdk-v3.developer.homey.app/DiscoveryResultMAC.html) |
| `DiscoveryResultMDNSSD` | [DiscoveryResultMDNSSD.html](https://apps-sdk-v3.developer.homey.app/DiscoveryResultMDNSSD.html) |
| `DiscoveryResultSSDP` | [DiscoveryResultSSDP.html](https://apps-sdk-v3.developer.homey.app/DiscoveryResultSSDP.html) |

**Properties**

| Property | Type | Present on | Description |
| --- | --- | --- | --- |
| `id` | `string` | all | The identifier of the result |
| `address` | `string` | all | The (IP) address of the device |
| `lastSeen` | `Date` | all | When the device has been last discovered |
| `mac` | `string` | `DiscoveryResultMAC` | The MAC address of the device |
| `host` | `string\|undefined` | `DiscoveryResultMDNSSD` | The hostname of the device |
| `name` | `string\|undefined` | `DiscoveryResultMDNSSD` | The name of the device |
| `fullname` | `string\|undefined` | `DiscoveryResultMDNSSD` | The full name of the device |
| `port` | `number\|undefined` | `DiscoveryResultMDNSSD` | The port of the device |
| `txt` | `Object.<string, string>` | `DiscoveryResultMDNSSD` | The TXT records of the device, key-value |
| `headers` | `Object.<string, string>` | `DiscoveryResultSSDP` | The headers (lowercase) in the SSDP response |
| `port` | `number` | `DiscoveryResultSSDP` | The port of the device |

`DiscoveryResultMDNSSD` documents a constructor: `new DiscoveryResultMDNSSD(props: any)`.

**Events (all discovery result classes)**

| Event | Payload | Description |
| --- | --- | --- |
| `addressChanged` | `discoveryResult: DiscoveryResult` | The address has changed |
| `lastSeenChanged` | `discoveryResult: DiscoveryResult` | The device has been seen again |

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    this.log('MyDevice initialized');
  }

  onDiscoveryResult(discoveryResult) {
    return discoveryResult.id === this.getData().id;
  }

  async onDiscoveryAvailable(discoveryResult) {
    this.address = discoveryResult.address;
    await this.setAvailable();
  }

  onDiscoveryAddressChanged(discoveryResult) {
    this.address = discoveryResult.address;
  }

  onDiscoveryLastSeenChanged(discoveryResult) {
    this.setAvailable().catch(this.error);
  }

}

module.exports = MyDevice;
```

---

## 8. Wireless

### 8.1 `ManagerBLE` — [ManagerBLE.html](https://apps-sdk-v3.developer.homey.app/ManagerBLE.html)

`discover` and `find` require the **`homey:wireless:ble`** permission.
The reference page documents **no events** on `ManagerBLE`.

| Signature | Notes |
| --- | --- |
| `async discover(serviceFilter?: Array.<string>) → Promise.<Array.<BleAdvertisement>>` | Discovers BLE peripherals for a certain time. `serviceFilter` = list of required serviceUuids. |
| `async find(peripheralUuid: string) → Promise.<BleAdvertisement>` | Finds a BLE peripheral with a given uuid. |
| `__registerPeripheral(peripheral: BlePeripheral)` | Internal — register a peripheral connection, needed for notify and disconnect. |
| `__unregisterPeripheral(peripheral: BlePeripheral)` | Internal — unregister when disconnected. |

### 8.2 `BleAdvertisement` — [BleAdvertisement.html](https://apps-sdk-v3.developer.homey.app/BleAdvertisement.html)

Retrieved via `ManagerBLE#discover` or `ManagerBLE#find`.

| Property | Type | Description |
| --- | --- | --- |
| `id` | `string` | Id of the peripheral assigned by Homey |
| `uuid` | `string` | Uuid of the peripheral |
| `address` | `string` | The mac address of the peripheral |
| `addressType` | `string` | The address type of the peripheral |
| `connectable` | `boolean` | Indicates if Homey can connect to the peripheral |
| `localName` | `string` | The local name of the peripheral |
| `manufacturerData` | `Buffer` | Manufacturer specific data |
| `serviceData` | `Array.<{uuid: string, data: Buffer}>` | Array of service data entries |
| `serviceUuids` | `Array.<string>` | Array of service uuids |
| `rssi` | `number` | The rssi signal strength value |
| `timestamp` | *(type not documented)* | Timestamp of the last time it was discovered |

| Signature | Notes |
| --- | --- |
| `async connect() → Promise.<BlePeripheral>` | Connect to the peripheral this advertisement references. |

### 8.3 `BlePeripheral` — [BlePeripheral.html](https://apps-sdk-v3.developer.homey.app/BlePeripheral.html)

Retrieved via `BleAdvertisement#connect`. All discovery/read/write methods **throw if the peripheral
is not connected**. The reference page documents **no events** on `BlePeripheral` — `disconnect` is a
method, not an event.

| Property | Type | Description |
| --- | --- | --- |
| `id` | `string` | Id of the peripheral assigned by Homey |
| `uuid` | `string` | Uuid of the peripheral |
| `address` | `string\|undefined` | The mac address |
| `addressType` | `string\|undefined` | The address type |
| `connectable` | `boolean\|undefined` | If Homey can connect |
| `isConnected` | *(type not documented)* | If the peripheral is currently connected to Homey |
| `rssi` | `number\|undefined` | rssi signal strength |
| `state` | `string` | The state of the peripheral |
| `services` | `Array.<BleService>` | Only filled after services are discovered |

| Signature | Notes |
| --- | --- |
| `async connect() → Promise.<this>` | Reconnects if Homey disconnected. |
| `async disconnect() → Promise.<void>` | |
| `async assertConnected()` | Kept for backwards compatibility. |
| `async discoverAllServicesAndCharacteristics() → Promise.<Array.<BleService>>` | Throws if not connected. |
| `async discoverServices(servicesFilter?: Array.<string>) → Promise.<Array.<BleService>>` | Discovers all services if no filter given. Throws if not connected. |
| `async getService(uuid: string) → Promise.<BleService>` | Throws if not connected. |
| `async read(serviceUuid: string, characteristicUuid: string) → Promise.<Buffer>` | Shorthand read. Throws if not connected. |
| `async write(serviceUuid: string, characteristicUuid: string, data: Buffer) → Promise.<Buffer>` | Shorthand write. Throws if not connected. |
| `async updateRssi() → Promise.<string>` | Updates and returns the RSSI value. |

**Type definitions**

| Type | Shape |
| --- | --- |
| `BlePeripheral.Advertisement` | `object` with `localName: string`, `manufacturerData: string`, `serviceData: Array.<string>`, `serviceUuids: Array.<string>` |

### 8.4 `BleService` — [BleService.html](https://apps-sdk-v3.developer.homey.app/BleService.html)

Retrieved via `BlePeripheral#discoverServices` or `BlePeripheral#getService`.

| Property | Type |
| --- | --- |
| `id` | `string` — Id of the service assigned by Homey |
| `uuid` | `string` |
| `name` | `string` |
| `type` | `string` |
| `characteristics` | `Array.<BleCharacteristic>` |

| Signature | Notes |
| --- | --- |
| `async discoverCharacteristics(characteristicsFilter?: Array.<string>) → Promise.<Array.<BleCharacteristic>>` | Throws if not connected. |
| `async getCharacteristic(uuid: string) → Promise.<BleCharacteristic>` | Throws if not connected. |
| `async read(characteristicUuid: string) → Promise.<Buffer>` | Throws if not connected. |
| `async write(characteristicUuid: string, data: Buffer) → Promise.<Buffer>` | Throws if not connected. |

### 8.5 `BleCharacteristic` — [BleCharacteristic.html](https://apps-sdk-v3.developer.homey.app/BleCharacteristic.html)

Retrieved via `BleService#discoverCharacteristics` or `BleService#getCharacteristic`.

| Property | Type | Description |
| --- | --- | --- |
| `id` | `string` | Id of the characteristic assigned by Homey |
| `uuid` | `string` | |
| `name` | `string` | |
| `type` | `string` | |
| `properties` | `Array.<string>` | The properties of the characteristic |
| `descriptors` | `Array.<BleDescriptor>` | |
| `value` | `Buffer\|null` | Last result of `read()`; initially `null` |

| Signature | Notes |
| --- | --- |
| `async read() → Promise.<Buffer>` | Throws if not connected. |
| `async write(data: Buffer) → Promise.<Buffer>` | Throws if not connected. |
| `async discoverDescriptors(descriptorsFilter?: Array.<string>) → Promise.<Array.<BleDescriptor>>` | Throws if not connected. |
| `async subscribeToNotifications(callback: BleCharacteristic.NotificationCallback) → Promise.<void>` | Resolves when the subscription is successful. Throws if not connected. |
| `async unsubscribeFromNotifications() → Promise.<void>` | Resolves when unsubscribe succeeded and the callback has been removed. Throws if not connected. |

**Type definitions**

| Type | Signature |
| --- | --- |
| `BleCharacteristic.NotificationCallback` | `(data: Buffer)` — the received notification data |

### 8.6 `BleDescriptor` — [BleDescriptor.html](https://apps-sdk-v3.developer.homey.app/BleDescriptor.html)

Retrieved via `BleCharacteristic#discoverDescriptors`.

| Property | Type |
| --- | --- |
| `id`, `uuid`, `name`, `type` | `string` |
| `value` | `Buffer\|null` — last result of `readValue()`; initially `null` |

| Signature | Notes |
| --- | --- |
| `async readValue() → Promise.<Buffer>` | Throws if not connected. |
| `async writeValue(data: Buffer) → Promise.<Buffer>` | Throws if not connected. |

### 8.7 `ManagerNFC` — [ManagerNFC.html](https://apps-sdk-v3.developer.homey.app/ManagerNFC.html)

The page documents **no instance methods** — only one event. Requires the **`homey:wireless:nfc`**
permission.

| Event | Payload |
| --- | --- |
| `tag` | `tag: { uid: object }` |

### 8.8 `ManagerRF` — [ManagerRF.html](https://apps-sdk-v3.developer.homey.app/ManagerRF.html)

All transmit/receive methods require the **`homey:wireless:433`**, **`homey:wireless:868`** and/or
**`homey:wireless:ir`** permissions.

| Signature | Notes |
| --- | --- |
| `getSignal433(id: string) → Signal433` | `id` as defined in the app's `app.json`. |
| `getSignal868(id: string) → Signal868` | |
| `getSignalInfrared(id: string) → SignalInfrared` | |
| `async tx(signal: Signal, frame: Array.<number>\|Buffer, opts?: Object)` | Transmit a raw frame using the specified signal. |
| `async cmd(signal: Signal, commandId: string, opts?: Object)` | Send a predefined command (name as specified in the app manifest). |
| `async enableSignalRX(signal: T) → Promise.<T>` | Enables a signal to start receiving events. (Argument type is documented as `T`.) |
| `async disableSignalRX(signal: Signal) → Promise.<void>` | Disables a signal from receiving events. |

### 8.9 `Signal` / `Signal433` / `Signal868` / `SignalInfrared`

`Signal433`, `Signal868` and `SignalInfrared` all extend `Signal` and expose an **identical** API.

| Class | Represents | Doc URL |
| --- | --- | --- |
| `Signal` | A Signal as defined in the app's `app.json` | [Signal.html](https://apps-sdk-v3.developer.homey.app/Signal.html) |
| `Signal433` | An 433 MHz Signal | [Signal433.html](https://apps-sdk-v3.developer.homey.app/Signal433.html) |
| `Signal868` | An 868 MHz Signal | [Signal868.html](https://apps-sdk-v3.developer.homey.app/Signal868.html) |
| `SignalInfrared` | An Infrared Signal | [SignalInfrared.html](https://apps-sdk-v3.developer.homey.app/SignalInfrared.html) |

| Signature | Notes |
| --- | --- |
| `async tx(frame: Array.<number>, opts?: object) → Promise.<any>` | `frame` = an array of word indexes. |
| `async cmd(commandId: string, opts?: object) → Promise.<any>` | `commandId` as specified in `/app.json`. |
| `async enableRX() → Promise.<void>` | Shorthand for `ManagerRF#enableSignalRX`. |
| `async disableRX() → Promise.<void>` | Shorthand for `ManagerRF#disableSignalRX`. |

`opts` for both `tx` and `cmd`:

| Key | Type | Optional | Description |
| --- | --- | --- | --- |
| `repetitions` | `object` | yes | A custom amount of repetitions. 1 means 1 transmit in total, 2 means 2 transmits in total, etc. |
| `device` | `Device` | yes | The device being transmitted to |

| Event | Payload |
| --- | --- |
| `cmd` | `commandId: string` — the ID of the command, as specified in `/app.json` |
| `payload` | `payload: Array.<number>` (array of word indexes), `first: boolean` (if this is the first detected repetition) |

### 8.10 `ManagerZigBee` — [ManagerZigBee.html](https://apps-sdk-v3.developer.homey.app/ManagerZigBee.html)

| Signature | Notes |
| --- | --- |
| `async getNode(device: Device) → Promise.<ZigBeeNode>` | |

#### `ZigBeeNode` — [ZigBeeNode.html](https://apps-sdk-v3.developer.homey.app/ZigBeeNode.html)

Never instanced directly; retrieve via `ManagerZigBee#getNode`.

| Property | Type | Description |
| --- | --- | --- |
| `ieeeAddress` *(readonly)* | `string` | The node's IEEE address. **Available since Homey v12.3.0.** |
| `manufacturerName` *(readonly)* | `string` | The node's manufacturer name |
| `productId` *(readonly)* | `string` | The node's product id |

| Signature | Notes |
| --- | --- |
| `async sendFrame(endpointId: number, clusterId: number, frame: Buffer) → Promise.<void>` | Send a frame to this node. |
| `async handleFrame(endpointId: number, clusterId: number, frame: Buffer, meta: object) → Promise.<void>` | Called when a frame has been received. **This method must be overridden.** |

```javascript
// device.js
const zigBeeNode = await this.homey.zigbee.getNode(this);
```

### 8.11 `ManagerZwave` — [ManagerZwave.html](https://apps-sdk-v3.developer.homey.app/ManagerZwave.html)

| Signature | Notes |
| --- | --- |
| `async getNode(device: Device) → Promise.<ZwaveNode>` | |

#### `ZwaveNode` — [ZwaveNode.html](https://apps-sdk-v3.developer.homey.app/ZwaveNode.html)

| Property | Type | Description |
| --- | --- | --- |
| `nodeId` | `number` | The id of the node within the Z-Wave network |
| `battery` | `boolean` | Whether the node is battery operated |
| `online` | `boolean` | Whether the node is online |
| `firmwareId` | `number` | Firmware identifier |
| `manufacturerId` | `Object` | The manufacturer id, in the `value` property of the object |
| `productId` | `Object` | The product id, in the `value` property of the object |
| `productTypeId` | `Object` | The product type id, in the `value` property of the object |
| `deviceClassBasic` | `string` | Basic device class |
| `deviceClassGeneric` | `string` | Generic device class |
| `deviceClassSpecific` | `string` | Specific device class |
| `isMultiChannelNode` | `boolean` | Whether this node is a multichannel node |
| `multiChannelNodeId` | `number` | If this is a multichannel node, the id |
| `MultiChannelNodes` | `Object.<string, ZwaveNode>` | An object with `ZwaveNode` instances |
| `CommandClass` | `Object.<string, ZwaveCommandClass>` | An object with `ZwaveCommandClass` instances |

| Signature | Notes |
| --- | --- |
| `async sendCommand(command: object) → Promise.<void>` | `command = { commandClassId: number, commandId: number, params?: Buffer }`. Send a raw command to a node. |

| Event | Payload | Description |
| --- | --- | --- |
| `nif` | `nif: Buffer` | A Node Information Frame (NIF) has been sent |
| `online` | `online: boolean` | A battery node changed its online/offline status |
| `unknownReport` | `data: Buffer` | A node has received an unknown command |

#### `ZwaveCommandClass` — [ZwaveCommandClass.html](https://apps-sdk-v3.developer.homey.app/ZwaveCommandClass.html)

The class has properties of type `Function` that are the commands, dependent on the Command Class.

| Event | Payload |
| --- | --- |
| `report` | `command: { value: number, name: string }`, `report: object` (contents depend on the Command Class) |

```javascript
'use strict';

const Homey = require('homey');

class MyZwaveDevice extends Homey.Device {

  async onInit() {
    const node = await this.homey.zwave.getNode(this);

    node.CommandClass.COMMAND_CLASS_BASIC.on('report', (command, report) => {
      this.log('onReport', command, report);
    });

    node.CommandClass.COMMAND_CLASS_BASIC.BASIC_SET({ Value: 0xFF })
      .then(this.log)
      .catch(this.error);
  }

}

module.exports = MyZwaveDevice;
```

---

## 9. Media

### 9.1 `ManagerImages` — [ManagerImages.html](https://apps-sdk-v3.developer.homey.app/ManagerImages.html)

| Signature | Notes |
| --- | --- |
| `async createImage() → Promise.<Image>` | |
| `getImage(id: string) → Image` | Get a registered Image. |
| `async unregisterImage(imageInstance: Image) → Promise.<void>` | |

### 9.2 `Image` — [Image.html](https://apps-sdk-v3.developer.homey.app/Image.html)

An image must be registered; the contents are retrieved when needed. The page documents exactly
these methods — there is no buffer setter.

| Signature | Notes |
| --- | --- |
| `setPath(path: string)` | Relative path to your image, e.g. `/userdata/kitten.jpg`. |
| `setUrl(url: string)` | Absolute url, `https://`. Must be accessible from any network. |
| `setStream(source: function)` | `source` is called with `(stream)` when someone pipes this image; pipe the image content to the stream. Mostly for external image sources. |
| `async getStream() → Promise.<NodeJS.ReadableStream>` | The readable stream carries metadata properties (`Image.ImageStreamMetadata`). |
| `async pipe(stream: NodeJS.WritableStream) → Promise.<Image.ImageStreamMetadata>` | Pipe the image into the target stream and return metadata. |
| `async update() → Promise.<any>` | Notify that the image's contents have changed. |
| `async unregister()` | Shorthand for `ManagerImages#unregisterImage`. |

**Type definitions**

| Type | Shape |
| --- | --- |
| `Image.ImageStreamMetadata` | `filename: string`, `contentType: string` (mime type), `contentLength?: number` (size in bytes, if available) |

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onInit() {
    const image = await this.homey.images.createImage();
    image.setUrl(`https://${this.getSetting('ip')}/snapshot.jpg`);
    await this.setCameraImage('front', 'Front', image);

    this.homey.setInterval(() => {
      image.update().catch(this.error);
    }, 10000);
  }

}

module.exports = MyDevice;
```

### 9.3 `ManagerVideos` — [ManagerVideos.html](https://apps-sdk-v3.developer.homey.app/ManagerVideos.html)

Every created video **must be associated with a device using `Device#setCameraVideo`** to enable
streaming functionality.

| Signature | Returns |
| --- | --- |
| `async createVideoHLS(options?: object = {}) → Promise.<VideoHLS>` | A configured HLS video instance |
| `async createVideoDASH(options?: object = {}) → Promise.<VideoDASH>` | A configured DASH video instance |
| `async createVideoRTSP(options?: object = {}) → Promise.<VideoRTSP>` | A configured RTSP video instance |
| `async createVideoRTMP(options?: object = {}) → Promise.<VideoRTMP>` | A configured RTMP video instance |
| `async createVideoOther(options?: object = {}) → Promise.<VideoOther>` | A configured 'other' video instance — any VLC-supported URL |
| `async createVideoWebRTC(options?: object = {}) → Promise.<VideoWebRTC>` | A configured WebRTC video stream instance |
| `getVideo(id: string) → VideoWebRTC\|VideoRTSP\|VideoHLS\|VideoDASH\|VideoRTMP\|VideoOther` | Get a registered Video |
| `async unregisterVideo(videoInstance: Video) → Promise.<void>` | |

`options` for `createVideoHLS`, `createVideoDASH`, `createVideoRTSP`, `createVideoRTMP` and
`createVideoOther` (all optional):

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `acceptInvalidCertificates` | `boolean` | `false` | Whether the frontend should accept invalid certificates |
| `demuxer` | `string` | — | The demuxer to use for the stream. If `null`, the default demuxer is used. Only used for raw streams. One of `'h264'`, `'h265'`, `'mpegts'` or `'ts'` |
| `disableWebRTCProxy` | `boolean` | `false` | Frontends default to using the WebRTC streaming proxy when supported. Set to `true` to disable the proxy and use direct URL playback. **When disabled, videos cannot be played on web platforms or outside the local network.** |

`options` for `createVideoWebRTC`:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `dataChannel` | `boolean` | `true` | Whether the frontend should set up a WebRTC data channel for bidirectional communication. Some video streams don't work with a data channel and some don't work without it. |

### 9.4 Video class hierarchy

| Class | Extends | Doc URL |
| --- | --- | --- |
| `Video` | — (base class for video streams) | [Video.html](https://apps-sdk-v3.developer.homey.app/Video.html) |
| `VideoWithURL` | `Video` — **do not use directly** | [VideoWithURL.html](https://apps-sdk-v3.developer.homey.app/VideoWithURL.html) |
| `VideoHLS` | `VideoWithURL` | [VideoHLS.html](https://apps-sdk-v3.developer.homey.app/VideoHLS.html) |
| `VideoDASH` | `VideoWithURL` | [VideoDASH.html](https://apps-sdk-v3.developer.homey.app/VideoDASH.html) |
| `VideoRTSP` | `VideoWithURL` | [VideoRTSP.html](https://apps-sdk-v3.developer.homey.app/VideoRTSP.html) |
| `VideoRTMP` | `VideoWithURL` | [VideoRTMP.html](https://apps-sdk-v3.developer.homey.app/VideoRTMP.html) |
| `VideoOther` | `VideoWithURL` | [VideoOther.html](https://apps-sdk-v3.developer.homey.app/VideoOther.html) |
| `VideoWebRTC` | `Video` | [VideoWebRTC.html](https://apps-sdk-v3.developer.homey.app/VideoWebRTC.html) |

| Signature | Present on | Notes |
| --- | --- | --- |
| `async unregister()` | all video classes | Shorthand for `ManagerVideos#unregisterVideo`. |
| `registerVideoUrlListener(listener: function) → VideoWithURL` | `VideoWithURL` + HLS/DASH/RTSP/RTMP/Other | Invoked when Homey requests the video stream URL. Listener returns the video stream URL object, e.g. `{ url: 'rtsp://...' }`. |
| `registerOfferListener(listener: function) → VideoWebRTC` | `VideoWebRTC` | Invoked when Homey requests an SDP answer for a WebRTC offer. Receives the offer SDP, returns a promise resolving with the answer SDP. |
| `registerKeepAliveListener(listener: function) → VideoWebRTC` | `VideoWebRTC` | Invoked when Homey sends keep alive signals for active WebRTC streams. Receives the stream ID. |

`VideoHLS`, `VideoDASH`, `VideoRTSP`, `VideoRTMP` and `VideoOther` each document a no-argument
constructor (`new VideoHLS()` etc.), but instances are created through `ManagerVideos`.

```javascript
'use strict';

const Homey = require('homey');

class MyCamera extends Homey.Device {

  async onInit() {
    const video = await this.homey.videos.createVideoRTSP();

    video.registerVideoUrlListener(async () => {
      return { url: `rtsp://${this.getSetting('ip')}:554/stream` };
    });

    await this.setCameraVideo('front_door', 'Front Door', video);
  }

}

module.exports = MyCamera;
```

```javascript
// WebRTC variant
const video = await this.homey.videos.createVideoWebRTC({ options: {} });

video.registerOfferListener(async (offerSdp) => {
  return this.handleWebRTCOffer(offerSdp);
});

video.registerKeepAliveListener(async (streamId) => {
  await this.refreshStream(streamId);
});

await this.setCameraVideo('front_door', 'Front Door', video);
```

### 9.5 `ManagerAudio` — [ManagerAudio.html](https://apps-sdk-v3.developer.homey.app/ManagerAudio.html)

For both play methods: the sample is cached in Homey and can be played again by calling the function
with the same `sampleId` **without** the `sample` argument, which loads faster.

| Signature | Notes |
| --- | --- |
| `async playMp3(sampleId: string, sample?: Buffer\|string) → Promise.<any>` | `sample` = Buffer with MP3 data, or path to a file. |
| `async playWav(sampleId: string, sample?: Buffer\|string) → Promise.<any>` | `sample` = Buffer with WAV data, or path to a file. |
| `async removeMp3(sampleId: string) → Promise.<any>` | Remove MP3 sample from cache. |
| `async removeWav(sampleId: string) → Promise.<any>` | Remove WAV sample from cache. |

### 9.6 `ManagerSpeechOutput` — [ManagerSpeechOutput.html](https://apps-sdk-v3.developer.homey.app/ManagerSpeechOutput.html)

Requires the **`homey:manager:speech-output`** permission.

| Signature | Notes |
| --- | --- |
| `async say(text: string, opts: object) → Promise.<any>` | **Limit of 255 characters.** `opts = { session: object }` — the session of the speech; leave empty to use Homey's built-in speaker. |

```javascript
this.homey.speechOutput.say('Hello world!')
  .then(this.log)
  .catch(this.error);
```

### 9.7 `ManagerLedring` — [ManagerLedring.html](https://apps-sdk-v3.developer.homey.app/ManagerLedring.html)

Every method requires the **`homey:manager:ledring`** permission.

| Signature | Notes |
| --- | --- |
| `async createAnimation(opts: object) → Promise.<LedringAnimation>` | See options table. |
| `async createSystemAnimation(systemId: string, opts: object) → Promise.<LedringAnimation>` | `systemId` is one of `colorwipe`, `loading`, `off`, `progress`, `pulse`, `rainbow`, `rgb`, `solid`. `opts = { priority: string, duration: number\|boolean }`. |
| `async createProgressAnimation(opts: object)` | `opts = { priority: string, options: { color: string } }`, `color` is a HEX string, default `#0092ff`. *(No return type documented; `LedringAnimationSystemProgress` documents `setProgress()`.)* |
| `async registerAnimation(animation: LedringAnimation) → Promise.<LedringAnimation>` | |
| `async unregisterAnimation(animation: LedringAnimation) → Promise.<LedringAnimation>` | |
| `async registerScreensaver(name: string, animation: LedringAnimation) → Promise.<any>` | `name` as defined in your app's `app.json`. |
| `async unregisterScreensaver(name: string, animation: LedringAnimation) → Promise.<any>` | |

`createAnimation` `opts`:

| Key | Type | Description |
| --- | --- | --- |
| `frames` | `Array.<LedringAnimation.Frame>` | An array of frames. A frame is an Array of 24 objects with `r`, `g` and `b` properties, numbers between 0 and 255. |
| `priority` | `string` | Priority-stack level: `INFORMATIVE`, `FEEDBACK` or `CRITICAL`. |
| `transition` | `number` | Transition time (ms) how fast to fade the information in. Defaults to `300`. |
| `duration` | `number\|Boolean` | Duration (ms) how long the animation should be shown. Defaults to `false`. **`false` is required for screensavers.** |
| `options.fps` | `number` | Frames per second |
| `options.tfps` | `number` | Target frames per second (must be divisible by `fps`) |
| `options.rpm` | `number` | Rotations per minute |

### 9.8 Ledring animation classes

| Class | Extends | Doc URL |
| --- | --- | --- |
| `LedringAnimation` | — | [LedringAnimation.html](https://apps-sdk-v3.developer.homey.app/LedringAnimation.html) |
| `LedringAnimationSystem` | `LedringAnimation` | [LedringAnimationSystem.html](https://apps-sdk-v3.developer.homey.app/LedringAnimationSystem.html) |
| `LedringAnimationSystemProgress` | `LedringAnimationSystem` | [LedringAnimationSystemProgress.html](https://apps-sdk-v3.developer.homey.app/LedringAnimationSystemProgress.html) |

| Signature | Present on | Notes |
| --- | --- | --- |
| `async start() → Promise.<any>` | all three | Start the animation. |
| `async stop() → Promise.<any>` | all three | Stop the animation. |
| `async updateFrames(frames: Array.<LedringAnimation.Frame>) → Promise.<any>` | all three | Update the animation frames. |
| `async unregister() → Promise.<LedringAnimation>` | all three | Shorthand for `ManagerLedring#unregisterAnimation`. |
| `async registerScreensaver(screensaverName: string) → Promise.<any>` | all three | Shorthand for `ManagerLedring#registerScreensaver`. |
| `async unregisterScreensaver(screensaverName: string) → Promise.<any>` | all three | Shorthand for `ManagerLedring#unregisterScreensaver`. |
| `async setProgress(progress: number) → Promise.<any>` | `LedringAnimationSystemProgress` only | `progress` is a number between 0 – 1. |

**Type definitions**

| Type | Shape |
| --- | --- |
| `LedringAnimation.Frame` | `r: number`, `g: number`, `b: number` — each between 0 and 255 |

**Events (all three animation classes)**

| Event | Description |
| --- | --- |
| `start` | The animation has started |
| `stop` | The animation has stopped |
| `finish` | The animation has finished (duration has been reached) |

---

## 10. Cloud, Web API and inter-app communication

### 10.1 `ManagerCloud` — [ManagerCloud.html](https://apps-sdk-v3.developer.homey.app/ManagerCloud.html)

| Signature | Notes |
| --- | --- |
| `async getHomeyId() → Promise.<string>` | Homey's Cloud ID. |
| `async getLocalAddress() → Promise.<string>` | Homey's local address & port. |
| `async createWebhook(id: string, secret: string, data: object) → Promise.<CloudWebhook>` | Webhook ID / Secret / Data. |
| `async unregisterWebhook(webhook: CloudWebhook) → Promise.<any>` | |
| `async createOAuth2Callback(apiUrl: string) → Promise.<CloudOAuth2Callback>` | Generate an OAuth2 Callback. |

### 10.2 `CloudWebhook` — [CloudWebhook.html](https://apps-sdk-v3.developer.homey.app/CloudWebhook.html)

| Signature | Notes |
| --- | --- |
| `async unregister() → Promise.<any>` | Shortcut for `ManagerCloud#unregisterWebhook`. |

| Event | Payload |
| --- | --- |
| `message` | `args: { headers: object, query: object, body: object }` — received HTTP headers, query string and body |

### 10.3 `CloudOAuth2Callback` — [CloudOAuth2Callback.html](https://apps-sdk-v3.developer.homey.app/CloudOAuth2Callback.html)

The page documents **no instance methods** — only two events.

| Event | Payload | Description |
| --- | --- | --- |
| `url` | `url: string` | The absolute URL to the sign-in page. The user must be redirected here to complete sign-in. |
| `code` | `code: string\|Error` | The OAuth2 code (usually swapped for an access token), or an `Error` when something went wrong. |

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  onPair(session) {
    session.setHandler('showView', async (viewId) => {
      if (viewId !== 'login_oauth2') return;

      const apiUrl = 'https://example.com/oauth2/authorise?client_id=...';
      const myOAuth2Callback = await this.homey.cloud.createOAuth2Callback(apiUrl);

      myOAuth2Callback
        .on('url', (url) => {
          session.emit('url', url).catch(this.error);
        })
        .on('code', (code) => {
          // swap the code for an access token here
          session.nextView().catch(this.error);
        });
    });
  }

}

module.exports = MyDriver;
```

### 10.4 `ManagerApi` — [ManagerApi.html](https://apps-sdk-v3.developer.homey.app/ManagerApi.html)

| Signature | Notes |
| --- | --- |
| `async get(uri: string) → Promise.<any>` | Path relative to `/api`. |
| `async post(uri: string, body: any) → Promise.<any>` | |
| `async put(uri: string, body: any) → Promise.<any>` | |
| `async delete(uri: string) → Promise.<any>` | |
| `async realtime(event: string, data: any)` | Emit a realtime event. |
| `getApi(uri: string) → Api` | Create an `Api` instance to receive realtime events. `uri` is the URI of the endpoint, e.g. `homey:manager:webserver`. |
| `getApiApp(appId: string) → Api` | Create an `ApiApp` instance to receive realtime events. `appId` e.g. `com.athom.foo`. *(The reference lists the return type as `Api`.)* |
| `unregisterApi(api: Api)` | Unregister an `Api` instance. |
| `async getOwnerApiToken() → Promise.<string>` | Starts a new API session on behalf of the Homey owner and returns the API token. **The token expires after not being used for two weeks.** Requires the **`homey:manager:api`** permission. |
| `async getLocalUrl() → Promise.<string>` | Returns the url for local access. |

### 10.5 `Api` — [Api.html](https://apps-sdk-v3.developer.homey.app/Api.html)

An API endpoint on Homey. When registered, realtime events fire on the instance.

| Signature | Notes |
| --- | --- |
| `async get(uri: string) → Promise.<any>` | Path relative to the endpoint. |
| `async post(uri: string, body: any) → Promise.<any>` | |
| `async put(uri: string, body: any) → Promise.<any>` | |
| `async delete(uri: string) → Promise.<any>` | |
| `unregister()` | Shorthand for `ManagerApi#unregisterApi`. |

| Event | Payload |
| --- | --- |
| `realtime` | `event: string` (name of the realtime event), `data?: any` |

### 10.6 `ApiApp` — [ApiApp.html](https://apps-sdk-v3.developer.homey.app/ApiApp.html)

Extends `Api`. Represents another App on Homey.

| Signature | Notes |
| --- | --- |
| `async get(uri: string) → Promise.<any>` | |
| `async post(uri: string, body: any) → Promise.<any>` | |
| `async put(uri: string, body: any) → Promise.<any>` | |
| `async delete(uri: string) → Promise.<any>` | |
| `async getInstalled() → Promise.<boolean>` | Short-hand for `ManagerApps#getInstalled`. |
| `async getVersion() → Promise.<string>` | Short-hand for `ManagerApps#getVersion`. |
| `unregister()` | Shorthand for `ManagerApi#unregisterApi`. |

| Event | Description |
| --- | --- |
| `realtime` | A realtime event was received on this URI. Payload: `event: string`, `data?: any`. |
| `install` | The app is installed, enabled and running (accessible). |
| `uninstall` | The app is uninstalled, disabled or crashed (inaccessible). |

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const otherApp = this.homey.api.getApiApp('com.athom.otherApp');

    otherApp
      .on('realtime', (result) => this.log('otherApp.onRealtime', result))
      .on('install', (result) => this.log('otherApp.onInstall', result))
      .on('uninstall', (result) => this.log('otherApp.onUninstall', result));

    otherApp.get('/')
      .then((result) => this.log('otherApp.get', result))
      .catch((error) => this.error('otherApp.get', error));

    const installed = await otherApp.getInstalled();
    const version = await otherApp.getVersion();
    this.log({ installed, version });
  }

}

module.exports = MyApp;
```

---

## 11. Cross-cutting indexes

### 11.1 Every documented event, by class

| Class | Events |
| --- | --- |
| `Homey` | `cpuwarn`, `memwarn`, `unload` |
| `Api` | `realtime` |
| `ApiApp` | `realtime`, `install`, `uninstall` |
| `ManagerClock` | `timezoneChange` |
| `ManagerGeolocation` | `location` |
| `ManagerSettings` | `set`, `unset` |
| `ManagerNFC` | `tag` |
| `FlowCard`, `FlowCardAction`, `FlowCardCondition`, `FlowCardTrigger`, `FlowCardTriggerDevice` | `update` |
| `DiscoveryStrategy` | `result` |
| `DiscoveryResult`, `DiscoveryResultMAC`, `DiscoveryResultMDNSSD`, `DiscoveryResultSSDP` | `addressChanged`, `lastSeenChanged` |
| `CloudWebhook` | `message` |
| `CloudOAuth2Callback` | `url`, `code` |
| `Signal`, `Signal433`, `Signal868`, `SignalInfrared` | `cmd`, `payload` |
| `ZwaveNode` | `nif`, `online`, `unknownReport` |
| `ZwaveCommandClass` | `report` |
| `LedringAnimation`, `LedringAnimationSystem`, `LedringAnimationSystemProgress` | `start`, `stop`, `finish` |

Classes with **no documented events**: `SimpleClass`, `App`, `Driver`, `Device`, `PairSession`,
`ManagerApi`, `ManagerApps`, `ManagerArp`, `ManagerAudio`, `ManagerBLE`, `ManagerCloud`,
`ManagerDiscovery`, `ManagerDrivers`, `ManagerFlow`, `ManagerI18n`, `ManagerImages`,
`ManagerInsights`, `ManagerLedring`, `ManagerNotifications`, `ManagerRF`, `ManagerSpeechOutput`,
`ManagerVideos`, `ManagerZigBee`, `ManagerZwave`, `FlowArgument`, `FlowToken`, `Image`,
`InsightsLog`, `BleAdvertisement`, `BlePeripheral`, `BleService`, `BleCharacteristic`,
`BleDescriptor`, `ZigBeeNode`, `Video` and all `Video*` subclasses.

### 11.2 Every documented type definition

| Type | Owner | Shape |
| --- | --- | --- |
| `Device.CapabilityCallback` | `Device` | `(value: any, opts: any) → Promise.<void>\|void` |
| `Device.MultipleCapabilityCallback` | `Device` | `(capabilityValues: Object.<string, any>, capabilityOptions: Object.<string, any>) → Promise.<void>\|void` |
| `FlowCard.RunCallback` | `FlowCard` | `(args: any, state: any) → Promise.<any>\|any` |
| `FlowCard.ArgumentAutocompleteCallback` | `FlowCard` | `(query: string, args: any) → Promise.<ArgumentAutocompleteResults>\|ArgumentAutocompleteResults` |
| `FlowCard.ArgumentAutocompleteResults` | `FlowCard` | `{ name: string, description?: string, icon?: string, image?: string }` |
| `PairSession.Handler` | `PairSession` | `async (data: any) → Promise.<any>` |
| `Image.ImageStreamMetadata` | `Image` | `{ filename: string, contentType: string, contentLength?: number }` |
| `BleCharacteristic.NotificationCallback` | `BleCharacteristic` | `(data: Buffer)` |
| `BlePeripheral.Advertisement` | `BlePeripheral` | `{ localName: string, manufacturerData: string, serviceData: Array.<string>, serviceUuids: Array.<string> }` |
| `LedringAnimation.Frame` | `LedringAnimation` | `{ r: number, g: number, b: number }` (0–255) |

### 11.3 Permissions named in the reference

| Permission | Required by |
| --- | --- |
| `homey:manager:api` | `ManagerApi#getOwnerApiToken` |
| `homey:manager:geolocation` | all `ManagerGeolocation` methods and the `location` event |
| `homey:manager:ledring` | all `ManagerLedring` methods |
| `homey:manager:speech-output` | `ManagerSpeechOutput#say` |
| `homey:wireless:ble` | `ManagerBLE#discover`, `ManagerBLE#find` |
| `homey:wireless:nfc` | `ManagerNFC` `tag` event |
| `homey:wireless:433` | `ManagerRF` transmit/receive methods |
| `homey:wireless:868` | `ManagerRF` transmit/receive methods |
| `homey:wireless:ir` | `ManagerRF` transmit/receive methods |

### 11.4 Version-gated API members

| Member | Available since |
| --- | --- |
| `Homey#hasFeature(feature)` | Homey v12.7.1 |
| `Device#setLastSeenAt()` | Homey v12.6.1 |
| `ZigBeeNode#ieeeAddress` | Homey v12.3.0 |

### 11.5 Methods flagged as expensive or destructive

| Method | Flag |
| --- | --- |
| `Device#addCapability` | "this is an expensive method so use it only when needed" |
| `Device#removeCapability` | expensive; "Any Flow that depends on this capability will become broken" |
| `Device#setCapabilityOptions` | "this is an expensive method so use it only when needed" |
| `Device#setClass` | "Any Flow that depends on this class will become broken" |
| `Device#setSettings` | `Device#onSettings` is **not** called |

### 11.6 Shorthand methods (instance → manager)

| Shorthand | Delegates to |
| --- | --- |
| `Api#unregister()` / `ApiApp#unregister()` | `ManagerApi#unregisterApi` |
| `ApiApp#getInstalled()` | `ManagerApps#getInstalled` |
| `ApiApp#getVersion()` | `ManagerApps#getVersion` |
| `CloudWebhook#unregister()` | `ManagerCloud#unregisterWebhook` |
| `FlowToken#unregister()` | `ManagerFlow#unregisterToken` |
| `Image#unregister()` | `ManagerImages#unregisterImage` |
| `Video#unregister()` (and all subclasses) | `ManagerVideos#unregisterVideo` |
| `Signal#enableRX()` / `#disableRX()` | `ManagerRF#enableSignalRX` / `#disableSignalRX` |
| `LedringAnimation#unregister()` | `ManagerLedring#unregisterAnimation` |
| `LedringAnimation#registerScreensaver()` / `#unregisterScreensaver()` | `ManagerLedring#registerScreensaver` / `#unregisterScreensaver` |
| `Homey#__()` | `ManagerI18n#__` |

### 11.7 The three classes you extend

Per the reference index: **`App`** (export from `app.js`), **`Driver`** (export from `driver.js`),
**`Device`** (export from `device.js`). Everything else is retrieved through a manager. Related
official projects listed on the index page: Homey Z-Wave Driver, Homey Zigbee Driver, Homey RF
Driver, Homey OAuth2 App, Homey Log.

---

## Sources

- SDK v3 reference index — <https://apps-sdk-v3.developer.homey.app/index.html>
- Core: <https://apps-sdk-v3.developer.homey.app/Homey.html>, [App](https://apps-sdk-v3.developer.homey.app/App.html), [Driver](https://apps-sdk-v3.developer.homey.app/Driver.html), [Device](https://apps-sdk-v3.developer.homey.app/Device.html), [SimpleClass](https://apps-sdk-v3.developer.homey.app/SimpleClass.html)
- Managers: [ManagerApi](https://apps-sdk-v3.developer.homey.app/ManagerApi.html), [ManagerApps](https://apps-sdk-v3.developer.homey.app/ManagerApps.html), [ManagerArp](https://apps-sdk-v3.developer.homey.app/ManagerArp.html), [ManagerAudio](https://apps-sdk-v3.developer.homey.app/ManagerAudio.html), [ManagerBLE](https://apps-sdk-v3.developer.homey.app/ManagerBLE.html), [ManagerClock](https://apps-sdk-v3.developer.homey.app/ManagerClock.html), [ManagerCloud](https://apps-sdk-v3.developer.homey.app/ManagerCloud.html), [ManagerDiscovery](https://apps-sdk-v3.developer.homey.app/ManagerDiscovery.html), [ManagerDrivers](https://apps-sdk-v3.developer.homey.app/ManagerDrivers.html), [ManagerFlow](https://apps-sdk-v3.developer.homey.app/ManagerFlow.html), [ManagerGeolocation](https://apps-sdk-v3.developer.homey.app/ManagerGeolocation.html), [ManagerI18n](https://apps-sdk-v3.developer.homey.app/ManagerI18n.html), [ManagerImages](https://apps-sdk-v3.developer.homey.app/ManagerImages.html), [ManagerInsights](https://apps-sdk-v3.developer.homey.app/ManagerInsights.html), [ManagerLedring](https://apps-sdk-v3.developer.homey.app/ManagerLedring.html), [ManagerNFC](https://apps-sdk-v3.developer.homey.app/ManagerNFC.html), [ManagerNotifications](https://apps-sdk-v3.developer.homey.app/ManagerNotifications.html), [ManagerRF](https://apps-sdk-v3.developer.homey.app/ManagerRF.html), [ManagerSettings](https://apps-sdk-v3.developer.homey.app/ManagerSettings.html), [ManagerSpeechOutput](https://apps-sdk-v3.developer.homey.app/ManagerSpeechOutput.html), [ManagerVideos](https://apps-sdk-v3.developer.homey.app/ManagerVideos.html), [ManagerZigBee](https://apps-sdk-v3.developer.homey.app/ManagerZigBee.html), [ManagerZwave](https://apps-sdk-v3.developer.homey.app/ManagerZwave.html)
- Classes: [Api](https://apps-sdk-v3.developer.homey.app/Api.html), [ApiApp](https://apps-sdk-v3.developer.homey.app/ApiApp.html), [BleAdvertisement](https://apps-sdk-v3.developer.homey.app/BleAdvertisement.html), [BleCharacteristic](https://apps-sdk-v3.developer.homey.app/BleCharacteristic.html), [BleDescriptor](https://apps-sdk-v3.developer.homey.app/BleDescriptor.html), [BlePeripheral](https://apps-sdk-v3.developer.homey.app/BlePeripheral.html), [BleService](https://apps-sdk-v3.developer.homey.app/BleService.html), [CloudOAuth2Callback](https://apps-sdk-v3.developer.homey.app/CloudOAuth2Callback.html), [CloudWebhook](https://apps-sdk-v3.developer.homey.app/CloudWebhook.html), [DiscoveryResult](https://apps-sdk-v3.developer.homey.app/DiscoveryResult.html), [DiscoveryResultMAC](https://apps-sdk-v3.developer.homey.app/DiscoveryResultMAC.html), [DiscoveryResultMDNSSD](https://apps-sdk-v3.developer.homey.app/DiscoveryResultMDNSSD.html), [DiscoveryResultSSDP](https://apps-sdk-v3.developer.homey.app/DiscoveryResultSSDP.html), [DiscoveryStrategy](https://apps-sdk-v3.developer.homey.app/DiscoveryStrategy.html), [FlowArgument](https://apps-sdk-v3.developer.homey.app/FlowArgument.html), [FlowCard](https://apps-sdk-v3.developer.homey.app/FlowCard.html), [FlowCardAction](https://apps-sdk-v3.developer.homey.app/FlowCardAction.html), [FlowCardCondition](https://apps-sdk-v3.developer.homey.app/FlowCardCondition.html), [FlowCardTrigger](https://apps-sdk-v3.developer.homey.app/FlowCardTrigger.html), [FlowCardTriggerDevice](https://apps-sdk-v3.developer.homey.app/FlowCardTriggerDevice.html), [FlowToken](https://apps-sdk-v3.developer.homey.app/FlowToken.html), [Image](https://apps-sdk-v3.developer.homey.app/Image.html), [InsightsLog](https://apps-sdk-v3.developer.homey.app/InsightsLog.html), [LedringAnimation](https://apps-sdk-v3.developer.homey.app/LedringAnimation.html), [LedringAnimationSystem](https://apps-sdk-v3.developer.homey.app/LedringAnimationSystem.html), [LedringAnimationSystemProgress](https://apps-sdk-v3.developer.homey.app/LedringAnimationSystemProgress.html), [PairSession](https://apps-sdk-v3.developer.homey.app/PairSession.html), [Signal](https://apps-sdk-v3.developer.homey.app/Signal.html), [Signal433](https://apps-sdk-v3.developer.homey.app/Signal433.html), [Signal868](https://apps-sdk-v3.developer.homey.app/Signal868.html), [SignalInfrared](https://apps-sdk-v3.developer.homey.app/SignalInfrared.html), [Video](https://apps-sdk-v3.developer.homey.app/Video.html), [VideoDASH](https://apps-sdk-v3.developer.homey.app/VideoDASH.html), [VideoHLS](https://apps-sdk-v3.developer.homey.app/VideoHLS.html), [VideoOther](https://apps-sdk-v3.developer.homey.app/VideoOther.html), [VideoRTMP](https://apps-sdk-v3.developer.homey.app/VideoRTMP.html), [VideoRTSP](https://apps-sdk-v3.developer.homey.app/VideoRTSP.html), [VideoWebRTC](https://apps-sdk-v3.developer.homey.app/VideoWebRTC.html), [VideoWithURL](https://apps-sdk-v3.developer.homey.app/VideoWithURL.html), [ZigBeeNode](https://apps-sdk-v3.developer.homey.app/ZigBeeNode.html), [ZwaveCommandClass](https://apps-sdk-v3.developer.homey.app/ZwaveCommandClass.html), [ZwaveNode](https://apps-sdk-v3.developer.homey.app/ZwaveNode.html)
- Widgets / `ManagerDashboards` — see `references/widgets.md` and `references/python-apps.md`
