# Bluetooth LE, Matter & Thread

Reference for the Homey Apps SDK v3 Bluetooth Low Energy API (`ManagerBLE`, `BleAdvertisement`, `BlePeripheral`, `BleService`, `BleCharacteristic`, `BleDescriptor`), the BLE Developer Tool, and Matter/Thread driver manifests.
Siblings: `references/wireless-zigbee.md`, `references/wireless-zwave.md`, `references/wireless-lan-discovery.md`, `references/drivers-and-devices.md`, `references/app-and-manifest.md`, `references/pairing.md`, `references/python-apps.md`.

---

## 1. Decision table — which technology

| Situation | Use | App code required? |
| --- | --- | --- |
| Device speaks BLE GATT (connect, read/write characteristics) | Bluetooth LE (`ManagerBLE`) | Yes — full Driver + Device |
| Device beacons its state in advertisement service data | BLE advertisement subscription / `find()` polling | Yes — Device only, no GATT connection |
| Device is Matter-certified (Wi-Fi, Ethernet or Thread transport) | Matter driver manifest | **No** — manifest only, no `Driver`/`Device` classes allowed |
| Device is behind a Matter bridge | Matter bridge driver + bridged-device drivers | **No** — manifests only |
| Device is Thread-only, non-Matter | Not supported — there is no Thread API in the SDK | n/a |

---

## 2. Bluetooth LE

### 2.1 Prerequisites

| Item | Value |
| --- | --- |
| App permission | `homey:wireless:ble` in `/.homeycompose/app.json` → `permissions` |
| Driver manifest | `"connectivity": ["ble"]` |
| Manager accessor | `this.homey.ble` (on App, Driver, Device and API handlers) |
| Platforms | `local` **and** `cloud` — `ble` is *not* in the list of connectivity values restricted on Homey Bridge (only `lan` and `rf868` are) |
| Working example app | <https://github.com/athombv/com.mipow-example> |

```json
{
  "id": "com.example.myble",
  "sdk": 3,
  "permissions": ["homey:wireless:ble"]
}
```

```json
{
  "name": { "en": "My BLE Sensor" },
  "class": "sensor",
  "capabilities": ["measure_temperature", "measure_battery"],
  "platforms": ["local"],
  "connectivity": ["ble"],
  "energy": { "batteries": ["CR2032"] }
}
```

### 2.2 The GATT object model

Bluetooth devices define a table of data called the Generic Attribute profile (GATT). The hierarchy is:

```
Advertisement  →  Peripheral  →  Service  →  Characteristic  →  Descriptor
```

- **Advertisements** let devices discover each other by broadcasting; they are received without pairing. One-to-one relation with a Peripheral.
- **Peripheral** — the connectable device. After connecting, the paired devices expose their Services.
- **Service** — contains one or more Characteristics.
- **Characteristic** — usually represents a specific state (e.g. a BLE thermostat exposes temperature and humidity characteristics). Contains zero or more Descriptors.
- **Descriptor** — metadata for the Characteristic. The "Characteristic User Description" descriptor commonly explains the meaning/unit of the values.

How a BLE device exposes itself to Homey is entirely up to the manufacturer, so devices expose themselves in different ways.

### 2.3 `ManagerBLE` — `this.homey.ble`

| Member | Signature | Notes |
| --- | --- | --- |
| `discover` | `async discover(serviceFilter?: string[]): Promise<BleAdvertisement[]>` | Discovers BLE peripherals for a certain time. `serviceFilter` = list of required `serviceUuids` the peripheral must expose. Requires `homey:wireless:ble`. |
| `find` | `async find(peripheralUuid: string): Promise<BleAdvertisement>` | Finds a BLE peripheral with the given `peripheralUuid`. Requires `homey:wireless:ble`. Rejects (`NotFound`) when no peripheral with that uuid can be found — treat a rejection as "device out of range". |
| `subscribeToAdvertisements` | `async subscribeToAdvertisements(peripheralUuid: string, { rateLimitMs?: number }, callback: (advertisement: BleAdvertisement) => void): Promise<void>` | Near-realtime advertisement stream without a GATT connection (passive BLE scanning). `rateLimitMs` = minimum interval between delivered advertisements, **default 1000**. Only on Homeys with the `ble-advertisements` feature. Requires `homey:wireless:ble`. |
| `unsubscribeFromAdvertisements` | `async unsubscribeFromAdvertisements(peripheralUuid: string): Promise<void>` | Stops the subscription. Call from `onUninit()`. |
| `__registerPeripheral` | `__registerPeripheral(peripheral: BlePeripheral)` | Internal. Registers a peripheral connection, needed for notify and disconnect. Do not call. |
| `__unregisterPeripheral` | `__unregisterPeripheral(peripheral: BlePeripheral)` | Internal. Unregisters a peripheral connection when disconnected. Do not call. |

`discover`, `find`, `__registerPeripheral` and `__unregisterPeripheral` are the four members in the `ManagerBLE` apidoc; `subscribeToAdvertisements` / `unsubscribeFromAdvertisements` are documented in the Bluetooth LE guide and the Python API reference.

**The `ManagerBLE` API reference documents no events.** There is no `advertisementReceived` event in the SDK v3 API — the documented push mechanism is `subscribeToAdvertisements()`. The only documented BLE event is `'disconnect'` on `BlePeripheral` (§2.6).

```javascript
// Discover everything nearby
const advertisements = await this.homey.ble.discover();

// Discover only peripherals advertising a specific service
const advertisements = await this.homey.ble.discover([
  '0000180000001000800000805F9B34FB',
]);

// Fetch a known peripheral by uuid
const advertisement = await this.homey.ble.find('my_device_id');
```

`find()` returns the most recent cached advertisement instantaneously if Homey already knows the device; otherwise Homey performs a discovery first.

### 2.4 `BleAdvertisement`

Retrieved from `ManagerBLE#discover()` or `ManagerBLE#find()`. Never construct it yourself.

| Property | Type | Description | Always present? |
| --- | --- | --- | --- |
| `uuid` | `string` | Uuid of the peripheral | Yes |
| `id` | `string` | Id of the peripheral assigned by Homey | — |
| `rssi` | `number` | The rssi signal strength value for the peripheral | Yes |
| `localName` | `string` | The local name of the peripheral | No |
| `connectable` | `boolean` | Indicates if Homey can connect to the peripheral | Yes |
| `serviceUuids` | `string[]` | Array of service uuids. Some peripherals show one or more services in their advertisement; this list does **not** necessarily contain *all* services of the peripheral | No |
| `serviceData` | `Array<{ uuid: string, data: Buffer }>` | Array of service data entries a peripheral may expose during advertisement | No |
| `manufacturerData` | `Buffer` | Manufacturer-specific data for the peripheral | — |
| `address` | `string` | The mac address of the peripheral | Yes |
| `addressType` | `string` | The address type of the peripheral (`"random"` \| `"public"`) | Yes |
| `timestamp` | `number` | Timestamp of the last time it was discovered (Unix epoch, ms) | — |
| `state` | `string` | The state of the peripheral (`"(dis)connected"`, `"(dis)connecting"`, `"error"`) | Yes |

| Method | Signature | Description |
| --- | --- | --- |
| `connect` | `async connect(): Promise<BlePeripheral>` | Connect to the BLE peripheral this advertisement references |

`state` is documented on the advertisement object returned by `discover()`; `BlePeripheral#state` carries the same semantics after connecting.

### 2.5 `BlePeripheral`

Retrieved from `BleAdvertisement#connect()`. Never construct it yourself.

| Property | Type | Description |
| --- | --- | --- |
| `uuid` | `string` | Uuid of the peripheral |
| `id` | `string` | Id of the peripheral assigned by Homey |
| `address` | `string \| undefined` | The mac address of the peripheral |
| `addressType` | `string \| undefined` | The address type of the peripheral (`"random"` \| `"public"` \| `"unknown"`) |
| `connectable` | `boolean \| undefined` | Indicates if Homey can connect to the peripheral |
| `isConnected` | — | If the peripheral is currently connected to Homey |
| `rssi` | `number \| undefined` | The rssi signal strength value for the peripheral |
| `services` | `BleService[]` | Array of services of the peripheral. **Only filled after** the services are discovered via `discoverServices` / `getService` |
| `state` | `string` | The state of the peripheral: `"error"`, `"connecting"`, `"connected"`, `"disconnecting"`, `"disconnected"` |

| Method | Signature | Throws | Description |
| --- | --- | --- | --- |
| `connect` | `async connect(): Promise<this>` | — | Connects to the peripheral if Homey disconnected from it |
| `disconnect` | `async disconnect(): Promise<void>` | — | Disconnect Homey from the peripheral |
| `discoverAllServicesAndCharacteristics` | `async discoverAllServicesAndCharacteristics(): Promise<BleService[]>` | not connected | Discovers all services **and** characteristics in one go |
| `discoverServices` | `async discoverServices(servicesFilter?: string[]): Promise<BleService[]>` | not connected | Discovers the services; omit the filter to discover all |
| `getService` | `async getService(uuid: string): Promise<BleService>` | not connected | Get a service with the given uuid |
| `read` | `async read(serviceUuid, characteristicUuid): Promise<Buffer>` | not connected | Shorthand read — performs service/characteristic discovery for you |
| `write` | `async write(serviceUuid, characteristicUuid, data: Buffer): Promise<Buffer>` | not connected | Shorthand write — performs service/characteristic discovery for you |
| `updateRssi` | `async updateRssi(): Promise<string>` | — | Updates the RSSI signal strength value (returns `rssi`) |
| `assertConnected` | `async assertConnected()` | — | Kept for backwards compatibility |

**Type definition `BlePeripheral.Advertisement`** (`object`):

| Name | Type | Description |
| --- | --- | --- |
| `localName` | `string` | The local name of the peripheral |
| `manufacturerData` | `string` | Manufacturer specific data for peripheral |
| `serviceData` | `string[]` | Array of service data entries |
| `serviceUuids` | `string[]` | Array of service uuids |

### 2.6 The `disconnect` event

Reintroduced in Homey v6.0.0. Useful together with BLE notifications.

```javascript
peripheral.on('disconnect', () => {
  this.log('Disconnected from peripheral: ', peripheral.uuid);
});
```

A connected BLE device is allowed to turn off its radio while keeping the connection — this is a BLE power-saving feature. If the device is powered off or moved out of range during that period, Homey still registers it as connected (correct BLE behaviour: the connection may be restored when it returns). Homey emits `disconnect` only at the moment it *knows* the peripheral is gone.

> The `disconnect` event is **not guaranteed to trigger** on each disconnect. But if it *does* trigger, the peripheral is guaranteed to be disconnected.

### 2.7 `BleService`

Retrieved from `BlePeripheral#discoverServices()` or `BlePeripheral#getService()`.

| Property | Type | Description |
| --- | --- | --- |
| `uuid` | `string` | Uuid of the service |
| `id` | `string` | Id of the service assigned by Homey |
| `name` | `string` | The name of the service |
| `type` | `string` | The type of the service |
| `characteristics` | `BleCharacteristic[]` | Discovered characteristics |

| Method | Signature | Throws | Description |
| --- | --- | --- | --- |
| `discoverCharacteristics` | `async discoverCharacteristics(characteristicsFilter?: string[]): Promise<BleCharacteristic[]>` | not connected | Discover characteristics of this service |
| `getCharacteristic` | `async getCharacteristic(uuid: string): Promise<BleCharacteristic>` | not connected | Gets a characteristic for the given `characteristicUuid` |
| `read` | `async read(characteristicUuid: string): Promise<Buffer>` | not connected | Shorthand read on this service |
| `write` | `async write(characteristicUuid: string, data: Buffer): Promise<Buffer>` | not connected | Shorthand write on this service |

### 2.8 `BleCharacteristic`

Retrieved from `BleService#discoverCharacteristics()` or `BleService#getCharacteristic()`.

| Property | Type | Description |
| --- | --- | --- |
| `uuid` | `string` | Uuid of the characteristic |
| `id` | `string` | Id of the characteristic assigned by Homey |
| `name` | `string` | The name of the characteristic |
| `type` | `string` | The type of the characteristic |
| `properties` | `string[]` | The properties of the characteristic. Values: `broadcast`, `read`, `writeWithoutResponse`, `write`, `notify`, `indicate`, `authenticatedSignedWrites`, `extendedProperties` |
| `value` | `Buffer \| null` | The value of the characteristic. Set to the last result of `BleCharacteristic#read`; **initially `null`** |
| `descriptors` | `BleDescriptor[]` | Discovered descriptors |

| Method | Signature | Throws | Description |
| --- | --- | --- | --- |
| `read` | `async read(): Promise<Buffer>` | not connected | Read the value for this characteristic |
| `write` | `async write(data: Buffer): Promise<Buffer>` | not connected | Write a value to this characteristic |
| `discoverDescriptors` | `async discoverDescriptors(descriptorsFilter?: string[]): Promise<BleDescriptor[]>` | not connected | Discovers descriptors for this characteristic |
| `subscribeToNotifications` | `async subscribeToNotifications(callback: BleCharacteristic.NotificationCallback): Promise<void>` | not connected | Subscribe to BLE notifications; the callback is called with the data as a Buffer. Resolves when the subscription is successful. **Only one callback can be active at a time** per characteristic |
| `unsubscribeFromNotifications` | `async unsubscribeFromNotifications(): Promise<void>` | not connected | Resolves when unsubscribe succeeded and the callback has been removed |

**Type definition `BleCharacteristic.NotificationCallback`**: `NotificationCallback(data: Buffer)` — `data` is the received notification data.

### 2.9 `BleDescriptor`

Retrieved from `BleCharacteristic#discoverDescriptors()`.

| Property | Type | Description |
| --- | --- | --- |
| `uuid` | `string` | Uuid of the characteristic |
| `id` | `string` | Id of the characteristic assigned by Homey |
| `name` | `string` | The name of the descriptor |
| `type` | `string` | The type of the descriptor |
| `value` | `Buffer \| null` | The value of the descriptor. Set to the last result of `BleDescriptor#read`; **initially `null`** |

| Method | Signature | Throws | Description |
| --- | --- | --- | --- |
| `readValue` | `async readValue(): Promise<Buffer>` | not connected | Read the value for this descriptor |
| `writeValue` | `async writeValue(data: Buffer): Promise<Buffer>` | not connected | Write a value to this descriptor |

**Note the naming asymmetry:** in the JavaScript SDK characteristics use `read()` / `write()` while descriptors use `readValue()` / `writeValue()`. (The Python SDK has no such asymmetry — descriptors there use `read()` / `write()` too.)

### 2.10 UUID conventions

A BLE UUID has 128 bits. If it matches the base UUID it can be shortened to 16 bits by using only the 4th–8th hexadecimal characters:

```
// 128bit UUID
'0000ABCD-0000-1000-8000-00805F9B34FB'

// 16bit UUID (Deprecated)
'ABCD'
```

From Homey v6.0.0 Homey uses **long UUIDs for all BLE devices by default**, to prevent confusion and to give consistent results across Homey models. Short UUIDs are still supported and existing apps keep working. Write new code against long UUIDs.

### 2.11 Reading and writing

Three levels, from most to least convenient:

```javascript
// 1. Peripheral shorthand — service & characteristic discovery is done for you
const data = await peripheral.read(serviceUuid, characteristicUuid);
await peripheral.write(serviceUuid, characteristicUuid, data);

// 2. Service shorthand
const data = await service.read(characteristicUuid);
await service.write(characteristicUuid, data);

// 3. Characteristic — requires discovering services & characteristics first
const data = await characteristic.read();
await characteristic.write(data);
```

**Reading and writing data using a Handle is not supported.** **Included Services are not (yet) supported.**

### 2.12 Service & characteristic discovery

```javascript
// All services of a peripheral
const services = await peripheral.discoverServices();

// A single service
const service = await peripheral.getService(serviceUuid);

// Everything in one call
const services = await peripheral.discoverAllServicesAndCharacteristics();

// Characteristics of a service
const characteristics = await service.discoverCharacteristics();
```

Locating a specific service + characteristic explicitly:

```javascript
// Find the service
const services = await this._connection.discoverServices();
const dataService = services.find(service => service.uuid === 'my_service_uuid');
if (!dataService) throw new Error('Could not find service');

// Find the characteristic
const dataCharacteristics = await dataService.discoverCharacteristics(['my_characteristic_uuid']);
if (!dataCharacteristics || !dataCharacteristics.length) throw new Error('Could not find Characteristic');
this._dataCharacteristic = dataCharacteristics[0];
```

### 2.13 Connect → discover → read/write → disconnect

The canonical short-lived-connection pattern with error handling. `connect()` may reject — for example when another app is connected to the peripheral, or when the peripheral is no longer available. If the peripheral is already connected you receive the **existing** connection.

```javascript
'use strict';

const Homey = require('homey');

const SERVICE_UUID = '0000180f00001000800000805f9b34fb';
const CHARACTERISTIC_UUID = '00002a1900001000800000805f9b34fb';

class MyDevice extends Homey.Device {

  async onInit() {
    this.peripheralUuid = this.getStore().peripheralUuid;
    await this.readOnce().catch(this.error);
  }

  async readOnce() {
    const advertisement = await this.homey.ble.find(this.peripheralUuid);

    let peripheral;
    try {
      peripheral = await advertisement.connect();

      const service = await peripheral.getService(SERVICE_UUID);
      const characteristic = await service.getCharacteristic(CHARACTERISTIC_UUID);
      const data = await characteristic.read();

      await this.setCapabilityValue('measure_battery', data.readUInt8(0));
      await this.setAvailable();
    } catch (err) {
      this.error('BLE read failed:', err);
      await this.setUnavailable(this.homey.__('errors.ble_unreachable')).catch(this.error);
      throw err;
    } finally {
      // Always release the radio — some devices allow only one connection.
      if (peripheral) await peripheral.disconnect().catch(this.error);
    }
  }

}

module.exports = MyDevice;
```

Writing from a capability listener, connecting only for the duration of the write:

```javascript
this.registerCapabilityListener('onoff', async (value) => {
  const advertisement = await this.homey.ble.find(this.peripheralUuid);
  const peripheral = await advertisement.connect();
  try {
    await peripheral.write(SERVICE_UUID, CHARACTERISTIC_UUID, Buffer.from([value ? 0x01 : 0x00]));
  } finally {
    await peripheral.disconnect().catch(this.error);
  }
});
```

Or, with a permanent connection held on `this.peripheral`:

```javascript
this.registerCapabilityListener('onoff', async (value) => {
  await this.peripheral.write(SERVICE_UUID, CHARACTERISTIC_UUID, Buffer.from([value ? 0x01 : 0x00]));
});
```

### 2.14 Connection-count constraints

- **Some devices do not support multiple BLE connections.** A permanent connection with Homey would block other devices (e.g. the manufacturer's phone app) from connecting. **Do not keep a connection with a device occupied if there is no reason to do so.**
- If the peripheral is already connected, `connect()` resolves with the **existing** connection instead of opening a second one.
- If your app opened multiple connections to one device, Homey only closes the actual BLE connection when **all** of them are closed.
- `disconnect()` on an already-disconnected peripheral simply resolves — it is safe to call unconditionally.
- Since Homey 6.0 a peripheral **no longer auto-disconnects after 60 seconds**. It stays connected until the app using it closes, until the corresponding device is removed by the user, or until `peripheral.disconnect()` is explicitly called. Some devices work better when an active connection is maintained.
- Discovery results are kept in cache for **at least 30 seconds**.
- `peripheral.state` may incorrectly read `connected` after a silent disconnect: the connection status is assumed unchanged until the SDK receives an indication otherwise.

### 2.15 BLE notifications

Available since Homey 6.0. Requires a connected peripheral and a discovered characteristic.

```javascript
'use strict';

const Homey = require('homey');

class MyNotifyDevice extends Homey.Device {

  async onInit() {
    await this.connectAndSubscribe().catch(this.error);
  }

  async connectAndSubscribe() {
    const advertisement = await this.homey.ble.find(this.getStore().peripheralUuid);
    this.peripheral = await advertisement.connect();

    this.peripheral.on('disconnect', () => {
      this.log('Peripheral disconnected:', this.peripheral.uuid);
      this.setUnavailable().catch(this.error);
      // Reconnect after a back-off; setTimeout is auto-cleared on uninit.
      this.homey.setTimeout(() => this.connectAndSubscribe().catch(this.error), 30 * 1000);
    });

    const service = await this.peripheral.getService('my_service_uuid');
    this.characteristic = await service.getCharacteristic('my_characteristic_uuid');

    await this.characteristic.subscribeToNotifications((data) => {
      this.log('Received notification:', data);
      this.setCapabilityValue('measure_temperature', data.readInt16LE(0) / 100).catch(this.error);
    });

    await this.setAvailable();
  }

  async onUninit() {
    if (this.characteristic) {
      await this.characteristic.unsubscribeFromNotifications().catch(this.error);
    }
    if (this.peripheral) {
      await this.peripheral.disconnect().catch(this.error);
    }
  }

}

module.exports = MyNotifyDevice;
```

### 2.16 Advertisement subscriptions and the `ble-advertisements` feature

If the device broadcasts its state in the advertisement itself — for example a sensor exposing temperature in its service data — subscribe to advertisements instead of polling. This delivers near-realtime updates **without opening a GATT connection**.

Advertisement subscriptions are only available on Homeys that support the `ble-advertisements` feature. Check with `this.homey.hasFeature('ble-advertisements')` and provide a `find()`-based fallback for unsupported Homeys.

`ble-advertisements` is supported on:

| Model |
| --- |
| Homey Pro (Early 2023) |
| Homey Pro Mini |
| Homey Pro 2026 |
| Homey SHS |

```javascript
'use strict';

const Homey = require('homey');

const POLL_INTERVAL = 10 * 60 * 1000; // 10 minutes

class Device extends Homey.Device {

  async onInit() {
    if (this.homey.hasFeature('ble-advertisements')) {
      try {
        await this.homey.ble.subscribeToAdvertisements(
          this.getStore().peripheralUuid,
          { rateLimitMs: 5000 },
          advertisement => {
            this.onAdvertisement({
              address: advertisement.address,
              rssi: advertisement.rssi,
              manufacturerData: advertisement.manufacturerData,
              serviceData: advertisement.serviceData,
              localName: advertisement.localName,
              ts: Date.now(),
            });
          },
        );
        this.isSubscribed = true;
      } catch (err) {
        this.log('Could not subscribe to advertisements, falling back to polling:', err.message);
      }
    }

    if (!this.isSubscribed) {
      this.pollInterval = this.homey.setInterval(() => {
        this.poll().catch(this.error);
      }, POLL_INTERVAL);
    }
  }

  async poll() {
    const advertisement = await this.homey.ble.find(this.getStore().peripheralUuid);
    this.onAdvertisement({
      address: advertisement.address,
      rssi: advertisement.rssi,
      manufacturerData: advertisement.manufacturerData,
      serviceData: advertisement.serviceData,
      localName: advertisement.localName,
      ts: Date.now(),
    });
  }

  onAdvertisement(advertisement) {
    // parse and update capabilities
  }

  async onUninit() {
    if (this.isSubscribed) {
      await this.homey.ble.unsubscribeFromAdvertisements(this.getStore().peripheralUuid);
    }
    if (this.pollInterval) this.homey.clearInterval(this.pollInterval);
  }

}

module.exports = Device;
```

Only one option is documented for `subscribeToAdvertisements`: `rateLimitMs` (minimum milliseconds between delivered advertisements, **default 1000**). The polling fallback stays correct, but for sensors that beacon every few seconds it is functionally slower than a live subscription.

Documented subscription semantics:

- The subscription uses **passive BLE scanning** — no GATT connection is opened, so it does not block the manufacturer's own app and costs the peripheral nothing extra.
- **Only one callback can be active per peripheral.** Subscribing again for the same `peripheralUuid` *replaces* the previous callback rather than adding a second one.
- The callback receives a `BleAdvertisement`. **The same instance is reused and updated in place** across broadcasts — never store the advertisement object itself expecting a snapshot; copy the fields you need (as the example above does) or read them immediately.
- Requires the `homey:wireless:ble` permission, like `discover()` and `find()`.

### 2.17 Polling patterns for battery devices

BLE sensors are almost always battery powered. Every GATT connection costs the peripheral far more energy than passively beaconing, so pick the cheapest mechanism that works:

| Preference | Mechanism | Radio cost | Requirement |
| --- | --- | --- | --- |
| 1 | `subscribeToAdvertisements()` | none (passive listen) | `ble-advertisements` feature; device beacons its state |
| 2 | Long-lived connection + `subscribeToNotifications()` | one connection held open | Device supports notifications and multiple/permanent connections |
| 3 | `find()` polling on an interval | none (reads the advertisement cache) | Device beacons its state |
| 4 | `connect()` → `read()` → `disconnect()` on an interval | one connection per poll | Device only exposes state through GATT |

Rules for the polling loop:

- Use `this.homey.setInterval` / `this.homey.clearInterval` (and `this.homey.setTimeout`) so timers are tied to the Device lifecycle and cleared automatically.
- Always `.catch(this.error)` inside the interval callback — an unhandled rejection crashes the app.
- Clear the interval and disconnect in `onUninit()`.
- Expose the interval as a device setting (e.g. `poll_interval`) rather than hard-coding it, and re-create the interval in `onSettings()`.
- Never poll faster than the device's own beacon rate — you only burn battery.
- Report battery with **either** `measure_battery` **or** `alarm_battery`, never both, and declare `"energy": { "batteries": [...] }` in the driver manifest.

```javascript
'use strict';

const Homey = require('homey');

class MyPolledDevice extends Homey.Device {

  async onInit() {
    this.startPolling(this.getSetting('poll_interval') || 600);
  }

  startPolling(seconds) {
    if (this.pollInterval) this.homey.clearInterval(this.pollInterval);
    this.pollInterval = this.homey.setInterval(() => {
      this.poll().catch(this.error);
    }, seconds * 1000);
  }

  async poll() {
    const advertisement = await this.homey.ble.find(this.getStore().peripheralUuid);
    const entry = (advertisement.serviceData || [])
      .find(({ uuid }) => uuid === 'my_service_uuid');
    if (!entry) return;

    await this.setCapabilityValue('measure_temperature', entry.data.readInt16LE(0) / 100);
    await this.setCapabilityValue('measure_battery', entry.data.readUInt8(2));
    await this.setAvailable();
  }

  async onSettings({ newSettings, changedKeys }) {
    if (changedKeys.includes('poll_interval')) {
      this.startPolling(newSettings.poll_interval);
    }
  }

  async onUninit() {
    if (this.pollInterval) this.homey.clearInterval(this.pollInterval);
  }

}

module.exports = MyPolledDevice;
```

### 2.18 Building a BLE app end-to-end

**Step 1 — explore the device with the BLE Developer Tool** (§3) and write down:

| Key | Value |
| --- | --- |
| Device Name | `my_device_name` |
| Service UUID | `my_service_uuid` |
| Characteristic UUID | `my_characteristic_uuid` |
| Format of received data | `[temp1, temp2]` |

**Step 2 — scaffold**: `homey app create`, then `homey app driver create`. The App class can stay as-is; the driver does the pairing work.

**Step 3 — the driver** scans for BLE devices, filters for a property in the advertisement (an exposed service or the device name), and formats the result for Homey:

```javascript
'use strict';

const Homey = require('homey');

class Driver extends Homey.Driver {

  async onPairListDevices() {
    const advertisements = await this.homey.ble.discover();

    return advertisements
      .filter(advertisement => advertisement.localName === 'my_device_name')
      .map(advertisement => {
        return {
          name: advertisement.localName,
          data: {
            id: advertisement.uuid,
          },
          store: {
            peripheralUuid: advertisement.uuid,
          },
        };
      });
  }

}

module.exports = Driver;
```

The `store.peripheralUuid` is what the Device later feeds to `ManagerBLE#find()`. Keep `data` minimal and immutable — it identifies the device forever.

**Step 4 — the device**: use §2.13 (connect/read/write), §2.15 (notifications) or §2.16 (advertisement subscription), whichever matches the hardware.

### 2.19 BLE gotchas

- **Gotcha:** the app will not get any BLE access without the `homey:wireless:ble` permission in the app manifest — `this.homey.ble.discover()` and `find()` both require it.
- **Gotcha:** advertisement subscriptions require the `ble-advertisements` feature. Always gate on `this.homey.hasFeature('ble-advertisements')` and ship a `find()` polling fallback; otherwise the app breaks on older Homeys.
- **Gotcha:** since Homey 6.0 peripherals **no longer auto-disconnect after 60 s**. Code written for Homey 5 that relied on the implicit disconnect now leaks a held connection — disconnect explicitly.
- **Gotcha:** handle-based read/write is **not supported**, and Included Services are **not (yet) supported**. Do not try to address a characteristic by handle.
- **Gotcha:** some devices reject multiple simultaneous connections. Holding a permanent connection can lock the user out of the manufacturer's own app. Prefer short connections, or advertisement subscriptions.
- **Gotcha:** `connect()` rejects when another app already holds the peripheral or the peripheral vanished — wrap it and call `setUnavailable()`, never let it reject unhandled.
- **Gotcha:** `peripheral.state` can lie (`connected` after a silent disconnect). Do not use it as a health check; rely on the `disconnect` event plus failing reads.
- **Gotcha:** `BleCharacteristic#value` and `BleDescriptor#value` are `null` until you have called `read()` / `readValue()` at least once — they are caches, not live values.
- **Gotcha:** `BlePeripheral#services` is empty until `discoverServices()` / `getService()` / `discoverAllServicesAndCharacteristics()` has run.
- **Gotcha:** discovery results are cached for at least 30 s, so `find()` can return a stale advertisement. Use `timestamp` if freshness matters.
- **Gotcha:** write long (128-bit) UUIDs. Short 16-bit UUIDs are deprecated since Homey v6.0.0, even though they still work.
- **Gotcha:** descriptors use `readValue()`/`writeValue()`, not `read()`/`write()`. Mixing them up throws.
- **Gotcha:** the driver manifest needs `"connectivity": ["ble"]`; forgetting it does not break runtime but is flagged in App Store review and mis-categorises the driver.
- **Gotcha:** manufacturers implement BLE inconsistently — never assume `localName`, `serviceUuids` or `serviceData` are present. Only `uuid`, `rssi`, `connectable`, `state`, `address` and `addressType` are always there.
- **Gotcha:** the `BleAdvertisement` handed to a `subscribeToAdvertisements` callback is **the same object every time, mutated in place**. Storing it and reading it later gives you the *latest* values, not the ones from that callback — copy the fields you care about inside the callback.
- **Gotcha:** only **one** advertisement callback can be active per peripheral, and only **one** notification callback per characteristic. Subscribing a second time silently replaces the first — it does not fan out.
- **Gotcha:** `find()` rejects when the peripheral cannot be found at all (`NotFound`), so an out-of-range device makes it throw rather than resolve with `undefined`. Always `.catch()` it and `setUnavailable()`.

### 2.20 Python equivalents

The Python runtime exposes the same BLE API, mostly as a snake_case rename of the JavaScript names — but **several members are not a straight rename**, so do not machine-translate. Verified mapping:

| JavaScript | Python |
| --- | --- |
| `this.homey.ble.discover(serviceFilter?)` | `await self.homey.ble.discover(service_filter=None)` → tuple |
| `this.homey.ble.find(uuid)` | `await self.homey.ble.find(peripheral_uuid)` (raises `NotFound`) |
| `ble.subscribeToAdvertisements(uuid, { rateLimitMs }, cb)` | `await self.homey.ble.subscribe_to_advertisements(peripheral_uuid, callback, rate_limit_ms=1000)` — **callback is the 2nd positional arg, the rate limit is a keyword** |
| `ble.unsubscribeFromAdvertisements(uuid)` | `await self.homey.ble.unsubscribe_from_advertisements(peripheral_uuid)` |
| `advertisement.connect()` | `await advertisement.connect()` |
| `peripheral.isConnected` | `peripheral.connected` (**not** `is_connected`) |
| `peripheral.discoverAllServicesAndCharacteristics()` | `await peripheral.discover_all()` (**not** a literal rename) |
| `peripheral.discoverServices(filter?)` | `await peripheral.discover_services(uuid_filter=None)` |
| `peripheral.getService(uuid)` | `await peripheral.get_service(uuid)` |
| `peripheral.updateRssi()` | `await peripheral.update_rssi()` → `int` |
| `peripheral.on('disconnect', cb)` | `peripheral.on_disconnect(callback)` |
| `service.discoverCharacteristics(filter?)` | `await service.discover_characteristics(uuid_filter=None)` |
| `characteristic.subscribeToNotifications(cb)` | `await characteristic.subscribe_to_notifications(callback)` |
| `characteristic.unsubscribeFromNotifications()` | `await characteristic.unsubscribe_from_notification()` (**singular** "notification") |
| `descriptor.readValue()` / `writeValue(data)` | `await descriptor.read()` / `await descriptor.write(data)` (**no** `read_value`/`write_value`) |
| `this.homey.hasFeature(f)` | `self.homey.has_feature(f)` |
| `this.homey.setInterval` / `clearInterval` | `self.homey.set_interval` / `clear_interval` |

Advertisement properties become `local_name`, `address_type`, `manufacturer_data`, `service_data`, `service_uuids`. Buffers become `bytes`. Arrays returned by discovery are `tuple`s, not `list`s. There is no `assert_connected`. See `references/python-apps.md`.

---

## 3. BLE Developer Tool

<https://tools.developer.homey.app/tools/ble> (from the Homey Developer Portal at <https://tools.developer.homey.app/>).

The tool follows the BLE hierarchy, one column per level: **All Advertisements → Peripheral → Service → Characteristic → Descriptor**.

| Column | What it does |
| --- | --- |
| **Advertisements** | Shows all devices detected by Homey, sorted on signal strength (`RSSI`). "Discover devices" button at the top of the column triggers a discovery. Clicking an advertisement opens the peripheral. |
| **Peripheral** | Details for the selected device. For most BLE devices you can connect and disconnect. A connection must be made **first**; only after a successful connection do the other options appear — "Discover Services", "Discover Services & Characteristics", update RSSI, and disconnect. Some devices cannot be connected to at all — e.g. when all their data is already in the advertisement and a connection is unnecessary. |
| **Services** | Each service is a collection of one or more characteristics; they must be discovered before more information is displayed. |
| **Characteristics** | The most complex section — each characteristic is a specific functionality (from reading a device identifier to telling a BLE bulb to change colour). Read/write plus descriptor discovery and BLE notification subscribe/unsubscribe. |
| **Descriptors** | Not always present. Provide extra information about the characteristic they belong to (user description, subscription status). Their read/write buttons behave like the characteristic's. |

Practical notes from the tool page:

- *"Discover Services"* and *"Discover Services & Characteristics"* initially perform the same operation; the latter saves time in the services column.
- Data read from a device is shown in **multiple formats**, to help decode it quickly.
- **Write data as a buffer in decimal format**, e.g. `[255, 0, 0]`.
- A writable characteristic is often also readable. Reading an RGBW lamp that is currently green and getting `[0, 255, 0, 0]` tells you the layout is `[R, G, B, W]`; getting it while red suggests `[W, R, G, B]`. Then try writing `[255, 0, 0, 0]` to confirm.
- Raw characteristic reads usually come without explanation — read the **"Characteristic User Description"** descriptor, it often documents the meaning and unit.
- If a device does not support BLE notifications, the notification buttons are disabled. After subscribing, the tool shows a live feed of incoming notifications.

---

## 4. Matter

> Matter apps are supported since Homey Pro (Early 2023) **v11.1.0**.

Matter is a smart-home protocol released by the Connectivity Standards Alliance in 2022. The standard describes how the protocol functions and how devices should react to certain commands. **Because of this, Homey Pro can control all Matter devices without the need of a Homey App.** A Homey app can only *enhance* the experience of a Matter device by adding pairing instructions and device icons.

### 4.1 Homey vs. the app — division of labour

| Concern | Handled by |
| --- | --- |
| Commissioning / pairing over Matter | Homey Pro |
| Determining device class and capabilities | Homey Pro (at pairing time) |
| Capability handling and device updates | Homey Pro |
| Firmware updates via the DCL | Homey Pro |
| Thread transport / border router | Homey Pro |
| Pairing instructions (`learnmode`) | **Your app** |
| Device icon and App Store presentation | **Your app** |
| Bridged-device recognition (icons per bridged product) | **Your app** |
| Custom `Driver` / `Device` classes | **Not possible** |

### 4.2 Matter driver manifest

Add `/drivers/<driver_id>/driver.compose.json` with at least the following, plus the required driver fields from `references/drivers-and-devices.md`:

| Field | Value / type | Notes |
| --- | --- | --- |
| `platforms` | `["local"]` | Always. Matter is **not** available on Homey Cloud. |
| `connectivity` | `["matter"]` | This is what makes the driver a Matter driver. Only available on Homey Pro (Early 2023). |
| `class` | device class string | Use the class that best fits your device. **Ignored at runtime** — display only. |
| `capabilities` | array | Set the capabilities your device has (find them in the developer tools after adding the device to Homey Pro). **Ignored at runtime** — display only. |
| `matter` | object | Matter-specific properties, below. |

`matter` object fields:

These five keys — `vendorId`, `productId`, `deviceVendorId`, `deviceProductName`, `learnmode` — are the **complete** set defined by the `matterDevice` definition in the validator schema. There is nothing else; any other key inside `matter` is not read by Homey.

| Field | Type | Required | Constraints (from the validator schema) | Description |
| --- | --- | --- | --- | --- |
| `vendorId` | `number` \| `number[]` | **Yes** | integer, `1` – `65520` (`0x0001`–`0xFFF0`) | The vendor id the Matter device uses. Array to support multiple devices with a single driver. |
| `productId` | `number` \| `number[]` | **Yes** | integer, `1` – `65535` (`0x0001`–`0xFFFF`) | The product id the Matter device uses. Array to support multiple devices with a single driver. |
| `deviceVendorId` | `number` \| `number[]` | No (bridged devices only) | integer, `1` – `65520` | The `VendorID` attribute reported by the bridged Matter device. If no `VendorID` attribute is present, use the `VendorID` property of the `Basic Information` cluster of the root endpoint. |
| `deviceProductName` | `string` \| `string[]` | No (bridged devices only) | 1 – 32 characters | The `ProductName` attribute reported by the bridged Matter device. |
| `learnmode` | object | No | — | Pairing instructions. |
| `learnmode.instruction` | translation object (`{ "en": "…" }`, `en` required) | **Yes, when `learnmode` is present** | — | Tells the user how to enable pairing mode on the device. |
| `learnmode.image` | path string | No | — | An image (or animated SVG) showing how to enable pairing mode. |

Schema notes worth knowing before `homey app validate` tells you:

- `deviceVendorId` and `deviceProductName` are **not** required by the schema even for bridged-device drivers — the "bridged devices only" rule is a documentation convention, not something the validator enforces. Omitting them on a bridged driver validates fine and then simply never matches a device.
- `learnmode` is optional, but if you include it, `instruction` is **required** inside it. A `learnmode` containing only `image` fails validation.
- All four id fields accept either a single number or an array of numbers; the range applies to each array element.
- The driver object itself requires `id`, `name`, `class` and `capabilities`, so a Matter driver must still carry `class` and `capabilities` (`[]` is a valid value) even though Homey ignores them at runtime.

Icons follow the normal driver icon mechanism (see `references/drivers-and-devices.md`).

**Example — a regular Matter device:**

```json
{
  "name": { "en": "My Driver" },
  "platforms": ["local"],
  "connectivity": ["matter"],
  "class": "socket",
  "capabilities": ["onoff", "dim"],
  "matter": {
    "vendorId": 1234,
    "productId": 4567,
    "learnmode": {
      "instruction": { "en": "Press the button on your device three times" },
      "image": "/drivers/<driver_id>/assets/learnmode.svg"
    }
  }
}
```

### 4.3 Finding vendorId / productId

Add the device to Homey, then check the device's **advanced settings**. The advanced settings show vendor and product id in **hexadecimal** (e.g. `0x1234`), but `driver.compose.json` accepts only **base-10** numbers (e.g. `4660`).

The validator caps `vendorId` (and `deviceVendorId`) at **65520** = `0xFFF0`, while `productId` goes up to **65535** = `0xFFFF`. That ceiling is deliberate: the Matter specification reserves `0xFFF1`–`0xFFF4` as *test* vendor ids, so a device still running a development/test vendor id (65521–65524) cannot be shipped in a Homey app — `homey app validate` rejects it. `0` is rejected too; the minimum for every id field is `1`.

### 4.4 Matter bridges

The Matter specification defines a **Matter bridge** — a device that exposes other, non-Matter devices through the Matter protocol (e.g. a Zigbee hub that adds Matter support and converts Matter commands into Zigbee commands).

Supporting a bridge needs **at least two drivers**:

1. **A driver for the bridge itself.** This is the driver the user selects; it provides the instructions for putting the bridge into pairing mode. The bridge itself is **never added as a device** to Homey. It must have `"class": "bridge"` and **no capabilities**. It is the only device that can be selected by the user when adding a Matter device.
2. **Drivers for the bridged devices**, one per bridged product. Each provides the icon for that bridged device.

**Bridge manifest:**

```json
{
  "name": { "en": "My Bridge Driver" },
  "platforms": ["local"],
  "connectivity": ["matter"],
  "class": "bridge",
  "capabilities": [],
  "matter": {
    "vendorId": 1234,
    "productId": 4567,
    "learnmode": {
      "instruction": { "en": "Press the button on your device three times" },
      "image": "/drivers/<bridge_driver_id>/assets/learnmode.svg"
    }
  }
}
```

**Bridged-device manifest** — keeps the bridge's `vendorId`/`productId` (this tells Homey which bridge the device belongs to) and adds `deviceVendorId` / `deviceProductName` from the `Bridged Device Basic Information` cluster:

```json
{
  "name": { "en": "My Bridged Device Driver" },
  "platforms": ["local"],
  "connectivity": ["matter"],
  "class": "other",
  "capabilities": [],
  "matter": {
    "vendorId": 1234,
    "productId": 4567,
    "deviceVendorId": 1234,
    "deviceProductName": "XYZ-123"
  }
}
```

> `ProductName` is an **optional** attribute of the `Bridged Device Basic Information` cluster. If it is not present, it is **not possible** to create a Homey driver for that bridged device.

Find the cluster attributes by adding the Matter Bridge to Homey, then opening the **Matter Developer Tools** at <https://tools.developer.homey.app/tools/matter> and performing an **interview** of the bridge. This shows all attributes for all endpoints the bridge has.

### 4.5 `platformLocalRequiredFeatures` and `platformFeatures`

Three related mechanisms, do not confuse them:

| Mechanism | Where | Type | Purpose |
| --- | --- | --- | --- |
| `platformLocalRequiredFeatures` | app manifest (`/.homeycompose/app.json`) | `string[]` | Makes the app **uninstallable** on Homey Pros lacking any listed feature. Allowed values per the validator schema: `nfc`, `speaker`, `ledring`, `matter`, `camera-streaming`. |

> **Schema vs. prose:** the prose documentation lists only `nfc`, `ledring`, `speaker` and `matter` for `platformLocalRequiredFeatures`. The app-manifest schema used by `homey app validate` also accepts **`camera-streaming`**. The schema wins — `camera-streaming` validates. `ble-advertisements` is *not* in the enum and will fail validation.
| `Homey#platformFeatures` | runtime, `this.homey.platformFeatures` | `string[]` | The features supported by the Homey that is running this app. |
| `Homey#hasFeature(feature)` | runtime, `this.homey.hasFeature('…')` | `boolean` | Check whether the Homey supports a specific feature. **Available since Homey v12.7.1.** Documented values: `speaker`, `ledring`, `nfc`, `camera-streaming`, `matter`. The BLE guide additionally documents `ble-advertisements`. |

```json
{
  "id": "com.athom.example",
  "platformLocalRequiredFeatures": ["matter"]
}
```

Adding `matter` to `platformLocalRequiredFeatures` is **recommended when your app only contains drivers for Matter devices**. If the app has drivers for other technologies or other features, Matter should **not** be added to the required-features list — use a runtime `hasFeature('matter')` check instead.

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.log('platform:', this.homey.platform, 'version:', this.homey.platformVersion);
    this.log('features:', this.homey.platformFeatures.join(', '));

    if (!this.homey.hasFeature('matter')) {
      this.log('This Homey has no Matter support; Matter drivers will not be usable.');
    }
  }

}

module.exports = MyApp;
```

Platform / platformVersion matrix (from `Homey`):

| Product | `platform` | `platformVersion` |
| --- | --- | --- |
| Homey Cloud | `cloud` | 1 |
| Homey (Early 2016) | `local` | 1 |
| Homey (Early 2018) | `local` | 1 |
| Homey (Early 2019) | `local` | 1 |
| Homey Pro (Early 2019) | `local` | 1 |
| Homey Pro (Early 2023) | `local` | 2 |
| Homey Pro mini (2025) | `local` | 2 |
| Homey Pro (2026) | `local` | 2 |
| Homey Self-Hosted Server | `local` | 2 |

On older software versions `platform` or `platformVersion` may be `undefined`; assume `local` / `1` in that case.

### 4.6 Matter firmware updates

Homey periodically checks the **Matter Distributed Compliance Ledger** (DCL) at <https://webui.dcl.csa-iot.org/models> for updates of Matter devices. To make an update available for a Matter device, ensure the update is added to the DCL. No app code is involved. (This is unrelated to the Z-Wave/Zigbee `driver.firmware.compose.json` OTA mechanism — see `references/wireless-zwave.md` and `references/wireless-zigbee.md`.)

### 4.7 Matter gotchas

- **Gotcha:** you **cannot** provide a custom `Driver` or `Device` class for a Matter device. Homey Pro handles all capabilities and device updates. Shipping `driver.js`/`device.js` for a Matter driver is wrong.
- **Gotcha:** `class` and `capabilities` in a Matter `driver.compose.json` are **only used for the Homey App Store listing**. At pairing Homey determines the real class and capabilities itself and ignores the manifest values. Do not debug "my capabilities aren't applied" — they never will be.
- **Gotcha:** the advanced settings show vendor/product ids in **hex** (`0x1234`); the manifest requires **base-10** (`4660`). Pasting the hex value silently produces a driver that never matches.
- **Gotcha:** `vendorId`/`deviceVendorId` are capped at **65520** (`0xFFF0`) by the validator, so the Matter *test* vendor ids `0xFFF1`–`0xFFF4` (65521–65524) fail `homey app validate`. Prototype hardware still on a test vendor id cannot be shipped — get a real CSA vendor id first.
- **Gotcha:** `deviceProductName` is limited to **32 characters** by the schema, matching the Matter `ProductName` attribute's own length limit. A longer string fails validation.
- **Gotcha:** if you add a `learnmode` object, `instruction` is **required** inside it. `learnmode` with only an `image` fails validation — the error points at `learnmode`, not at the missing key.
- **Gotcha:** `matter` has exactly five keys (`vendorId`, `productId`, `deviceVendorId`, `deviceProductName`, `learnmode`). There is no `endpoint`, no `clusters`, no `deviceType`, no `productId`-style filter beyond these — Matter drivers are matched on ids alone.
- **Gotcha:** Matter is `platforms: ["local"]` only. It is not available on Homey Cloud, and `matter` is documented as only available on Homey Pro (Early 2023) in the connectivity table.
- **Gotcha:** the Matter **bridge** driver is never added as a device — only the bridged devices appear. It exists solely to be selectable during pairing and to carry `learnmode`. Give it `"class": "bridge"` and `"capabilities": []`.
- **Gotcha:** a bridged device whose `Bridged Device Basic Information` cluster lacks the optional `ProductName` attribute **cannot** get a Homey driver at all.
- **Gotcha:** keep the bridge's own `vendorId`/`productId` in every bridged-device manifest; without them Homey cannot associate the bridged driver with its bridge.
- **Gotcha:** only add `matter` to `platformLocalRequiredFeatures` when the app is Matter-only — otherwise you lock the app out of Homeys that could still use its other drivers.
- **Gotcha:** the device-setting id prefixes `mtr_` and `thread_` are **reserved by Homey** (alongside `homey:`, `zw_`, `zb_`, `zone_`, `energy_`, `satellite_mode_`, `homekit_`). Never start your own setting ids with them. See `references/custom-views-and-settings.md`.

---

## 5. Thread

- **There is no Thread API in the Homey Apps SDK.** No manager, no class, no manifest object. Searching the SDK v3 reference for "Thread" returns nothing.
- Thread is a **transport** for Matter. A Thread-based Matter device is supported exactly like any other Matter device: `"connectivity": ["matter"]` plus the `matter` object in `driver.compose.json` (§4.2). Nothing in the manifest distinguishes Wi-Fi, Ethernet and Thread Matter devices.
- **Field-tested:** Homey Pro models with Matter support act as a **Thread Border Router** themselves; there is no configuration exposed to apps and no border-router API to call. From the app's point of view, Thread commissioning and routing are entirely Homey's responsibility.
- Homey reserves the `thread_` device-setting id prefix, which is the only place Thread surfaces in the app-facing API surface.
- A Thread device that does **not** speak Matter cannot be integrated by a Homey app.

---

## 6. Quick feature-detection reference

| Feature string | Checked with | Documented in |
| --- | --- | --- |
| `speaker` | `this.homey.hasFeature('speaker')` | `Homey#hasFeature` |
| `ledring` | `this.homey.hasFeature('ledring')` | `Homey#hasFeature` |
| `nfc` | `this.homey.hasFeature('nfc')` | `Homey#hasFeature` |
| `camera-streaming` | `this.homey.hasFeature('camera-streaming')` | `Homey#hasFeature`; also valid in `platformLocalRequiredFeatures` (schema only — the prose docs omit it) |
| `matter` | `this.homey.hasFeature('matter')` | `Homey#hasFeature`; also valid in `platformLocalRequiredFeatures` |
| `ble-advertisements` | `this.homey.hasFeature('ble-advertisements')` | Bluetooth LE guide (not listed in the `hasFeature` apidoc enumeration, and **not** valid in `platformLocalRequiredFeatures`) |

`platformLocalRequiredFeatures` accepts exactly `nfc`, `speaker`, `ledring`, `matter` and `camera-streaming` — that is the full enum in the app-manifest schema. Anything else, including `ble-advertisements`, fails `homey app validate`.

---

## Sources

- <https://apps.developer.homey.app/wireless/bluetooth>
- <https://apps.developer.homey.app/wireless/matter>
- <https://apps.developer.homey.app/guides/tools/bluetooth>
- <https://apps.developer.homey.app/guides/tools>
- <https://apps.developer.homey.app/upgrade-guides/changelog-homey-6>
- <https://apps.developer.homey.app/the-basics/app/manifest>
- <https://apps.developer.homey.app/the-basics/app/permissions>
- <https://apps.developer.homey.app/the-basics/devices>
- <https://apps.developer.homey.app/the-basics/devices/settings>
- <https://apps.developer.homey.app/the-basics/devices/best-practices/battery-status>
- <https://apps.developer.homey.app/guides/homey-cloud>
- <https://apps-sdk-v3.developer.homey.app/ManagerBLE.html>
- <https://apps-sdk-v3.developer.homey.app/BleAdvertisement.html>
- <https://apps-sdk-v3.developer.homey.app/BlePeripheral.html>
- <https://apps-sdk-v3.developer.homey.app/BleService.html>
- <https://apps-sdk-v3.developer.homey.app/BleCharacteristic.html>
- <https://apps-sdk-v3.developer.homey.app/BleDescriptor.html>
- <https://apps-sdk-v3.developer.homey.app/Homey.html>
- <https://python-apps-sdk-v3.developer.homey.app/manager/ble.html>
- <https://python-apps-sdk-v3.developer.homey.app/ble_advertisement.html>
- <https://python-apps-sdk-v3.developer.homey.app/ble_peripheral.html>
- <https://python-apps-sdk-v3.developer.homey.app/ble_characteristic.html>
- <https://python-apps-sdk-v3.developer.homey.app/ble_service.html>
- <https://python-apps-sdk-v3.developer.homey.app/ble_descriptor.html>
- <https://tools.developer.homey.app/tools/ble>
- <https://tools.developer.homey.app/tools/matter>
- <https://github.com/athombv/com.mipow-example>
