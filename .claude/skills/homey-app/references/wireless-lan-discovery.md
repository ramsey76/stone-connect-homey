# Wi-Fi / LAN Devices & Discovery

How a Homey app finds and talks to devices on the user's local network: the three discovery
strategies (`mdns-sd`, `ssdp`, `mac`), their JSON manifests, the `Device` discovery lifecycle,
`ManagerDiscovery`, ARP lookups and the rules about what may be stored as device identity.

Siblings: `references/drivers-and-devices.md` (Driver/Device lifecycle, store, settings),
`references/pairing.md` (pair views, `onPairListDevices`), `references/homey-cloud.md`
(Bridge restrictions), `references/cloud-oauth-webhooks.md` (OAuth2, webhooks, internet APIs),
`references/cli-and-tooling.md` (CLI flags), `references/publishing.md` (store guidelines).

---

## 1. LAN access basics

| Fact | Detail |
| --- | --- |
| Permissions | **None.** Homey can reach devices on the LAN (e.g. `192.168.1.100`) without any manifest permission. There is no `homey:wireless:lan`. |
| Internet | Also permission-free. Many Web APIs can be accessed directly. |
| Availability | The Wi-Fi connection might not always be available. Homey still functions normally without Wi-Fi or internet — your app must handle these cases. |
| Driver manifest | `"connectivity": ["lan"]` for LAN devices, `"platforms": ["local"]`. |
| Homey Cloud (Bridge) | **Does not support local Wi-Fi connections.** mDNS, SSDP and MAC discovery are unavailable, `connectivity: "lan"` is not possible, and `ManagerCloud#getLocalAddress()` is not supported. |
| App Store rule | **App Store submissions where users must enter an IP address, where discovery could have been used instead, will be rejected.** |

```json
// /drivers/<driver_id>/driver.compose.json
{
  "name": { "en": "My LAN Device" },
  "class": "light",
  "capabilities": ["onoff", "dim"],
  "platforms": ["local"],
  "connectivity": ["lan"],
  "discovery": "my_discovery"
}
```

`connectivity` specifies how the driver connects to the device in the real world. You may specify
**multiple** values — e.g. `[ "infrared", "lan" ]` for a TV that is turned on by infrared and then
controlled over Wi-Fi LAN.

`connectivity` enum (complete allowed values, from the Devices reference; the Homey Cloud guide adds
the Bridge caveats):

| Value | Meaning | Homey Bridge / Cloud |
| --- | --- | --- |
| `lan` | Local (Wi-Fi/Ethernet). | **Not possible with Homey Bridge.** |
| `cloud` | Cloud-connected (Wi-Fi/Ethernet) — driver uses OAuth or Webhooks to connect to a cloud service. | Supported. |
| `ble` | Bluetooth Low Energy. | Supported. |
| `zwave` | Z-Wave. | Supported. |
| `zigbee` | Zigbee. | Supported. |
| `infrared` | Infrared. | Supported. |
| `rf433` | 433 MHz. | Supported. |
| `rf868` | 868 MHz. | **Not possible with Homey Bridge.** |
| `matter` | Matter. | Only available on Homey Pro (Early 2023). |

### HTTP requests to LAN devices

As of Homey v12.9.0 all platforms run apps on **Node.js v22** (previously v16 / v18), so the global
`fetch` is built in; `axios` / `node-fetch` also work. Prefer the built-in `fetch` for new code —
`node-fetch` on Node 22 can throw `ECONNRESET` / "socket hang up" on keep-alive sockets unless you
pass a custom `http.Agent`.

```javascript
const res = await fetch(`http://${this.address}/api/status`);
if (!res.ok) throw new Error(`HTTP ${res.status}`);
const data = await res.json();
```

---

## 2. Choosing a discovery strategy

Homey can automatically find devices using **mDNS-SD**, **SSDP** and **MAC**. Discovery is preferred
over asking the user for an IP address, because an IP can change over time.

| Type | Protocol | Match data exposed | ID source | Scouting tool |
| --- | --- | --- | --- | --- |
| `mdns-sd` | Multicast-DNS Service Discovery (Avahi / Bonjour) | `txt` (lowercased TXT records), `name`, `fullname`, `host`, `port` | **you must define `id`** | [Discovery](https://apps.apple.com/us/app/discovery-dns-sd-browser/id305441017) (macOS), [Bonjour Browser](https://hobbyistsoftware.com/bonjourbrowser) (Windows) |
| `ssdp` | Simple Service Discovery Protocol (UPnP) | `headers` (lowercased response headers), `port` | **you must define `id`** | device documentation / UPnP scanner |
| `mac` | ARP on the manufacturer OUI | `address`, `mac` only | the MAC address is used automatically | device documentation / router ARP table |

Most devices use **mDNS-SD**. If a device is not discoverable with mDNS-SD, refer to the device's
documentation to learn what strategy you can use.

A working example app that uses Discovery: <https://github.com/athombv/com.plugwise.adam-example>

---

## 3. Strategy files

### Location

Homey Compose reads one JSON file per strategy:

```
/.homeycompose/discovery/<strategy_id>.json
```

The file name (without `.json`) is the **strategy id** you reference from a driver or from
`ManagerDiscovery#getStrategy()`.

Compose merges these into a top-level `discovery` object in the generated `/app.json`, keyed by
strategy id (never hand-edit `app.json`):

```json
{
  "discovery": {
    "plugwise": {
      "type": "mdns-sd",
      "mdns-sd": { "name": "plugwise", "protocol": "tcp" },
      "id": "{{name}}"
    }
  }
}
```

### Scaffolding via the CLI

```bash
homey app discovery create
```

Interactive wizard that adds a discovery strategy (mDNS-SD, SSDP, or MAC) to
`.homeycompose/discovery/`. Prefer it over hand-writing the file — it emits the current schema.

### Field reference (all types)

| Field | Type | Applies to | Required | Description |
| --- | --- | --- | --- | --- |
| `type` | `"mdns-sd"` \| `"ssdp"` \| `"mac"` | all | yes | The discovery strategy type. |
| `id` | string (template) | `mdns-sd`, `ssdp` | yes | Template that produces a stable identifier for a result, using `{{…}}` interpolation. For `mac`, the MAC address is used as the ID and `id` is not needed. |
| `conditions` | Array of Arrays of rule objects | all | no (highly recommended) | Pre-filter, so your app only receives results for devices it can actually pair. |
| `mdns-sd` | object | `mdns-sd` | yes | `{ "name": <service name>, "protocol": "tcp" \| "udp" }` |
| `mdns-sd.name` | string | `mdns-sd` | yes | The service name as specified by the manufacturer. For `_homey._tcp` the name is `homey`. |
| `mdns-sd.protocol` | `"tcp"` \| `"udp"` | `mdns-sd` | yes | The service protocol. |
| `ssdp` | object | `ssdp` | yes | `{ "search": <search target> }` |
| `ssdp.search` | string | `ssdp` | yes | The SSDP search target (`ST`), e.g. `urn:schemas-denon-com:device:ACT-Denon:1`. |
| `mac` | object | `mac` | yes | `{ "manufacturer": [[b0, b1, b2], …] }` |
| `mac.manufacturer` | Array of 3-number Arrays | `mac` | yes | One or more OUIs — the first 3 bytes of the MAC address, **in decimal**. |

**On `id` being "required":** the docs say that for `mdns-sd` and `ssdp` "the app **must** define how a
discovery result can be identified". Athom's own minimal driver example (see §6) nevertheless omits
`id`, and `Device#onDiscoveryResult` falls back to matching on the device's `data.id` property.
Always define `id` explicitly anyway — without it you have no guarantee which property Homey keys the
result on, and re-discovery after a DHCP change is exactly what `id` exists to make reliable.

Condition rule object:

| Field | Type | Description |
| --- | --- | --- |
| `field` | string | Dotted path into the discovery result, e.g. `txt.md`, `headers.st`, `name`. |
| `match.type` | `"string"` \| `"regex"` | Match kind. |
| `match.value` | string | Literal value, or a regular expression when `type` is `regex`. |

### mDNS-SD

A `DiscoveryResultMDNSSD` has a `txt` property that contains the (lowercased) TXT values of the
broadcast.

```json
// /.homeycompose/discovery/nanoleaf-aurora.json
{
  "type": "mdns-sd",
  "mdns-sd": {
    "name": "nanoleafapi",
    "protocol": "tcp"
  },
  "id": "{{txt.id}}",
  "conditions": [
    [
      {
        "field": "txt.md",
        "match": {
          "type": "string",
          "value": "NL22"
        }
      }
    ]
  ]
}
```

### SSDP

A `DiscoveryResultSSDP` has a `headers` property that contains the (lowercased) headers of the
response.

```json
// /.homeycompose/discovery/denon-heos.json
{
  "type": "ssdp",
  "ssdp": {
    "search": "urn:schemas-denon-com:device:ACT-Denon:1"
  },
  "id": "{{headers.usn}}",
  "conditions": [
    [
      {
        "field": "headers.st",
        "match": {
          "type": "string",
          "value": "urn:schemas-denon-com:device:ACT-Denon:1"
        }
      }
    ]
  ]
}
```

### MAC

MAC discovery specifies the first 3 bytes of a network device's MAC address. These first three bytes
are reserved for the manufacturer and can be used to find a device on the network using ARP.

A `DiscoveryResultMAC` only has an `address` property containing the IP address of the device (plus
the inherited `id` / `lastSeen`, and `mac`).

To find a device whose MAC starts with `00:24:6d` or `00:24:6e`, convert from hexadecimal to decimal
(`0x00 → 0`, `0x24 → 36`, `0x6d → 109`, `0x6e → 110`):

```json
// /.homeycompose/discovery/weinzierl.json
{
  "type": "mac",
  "mac": {
    "manufacturer": [
      [ 0, 36, 109 ],
      [ 0, 36, 110 ]
    ]
  }
}
```

**Gotcha:** the MAC address must be specified in **decimal numbers**, because JSON does not support
hexadecimal notation. Writing `[0x00, 0x24, 0x6d]` is invalid JSON.

---

## 4. The Discovery Result ID

For `mdns-sd` and `ssdp`, the app must define how a discovery result is identified when it is found
multiple times, **regardless of whether the IP address has changed**. For `mac`, the MAC address is
used as the ID.

Find a unique and consistent property in the result and define it as `id`. Homey then matches the
result to previous results and notifies your app that the device has been found *again*, instead of
treating it as a new discovery result.

All properties available in the DiscoveryResult are available between double curly braces
(`{{` and `}}`):

```json
"id": "{{txt.id}}"
```
```json
"id": "{{headers.uuid}}"
```
```json
"id": "{{name}}"
```

**Gotcha:** never template the `id` off `{{address}}`. The IP changes on DHCP renewal and Homey would
see the device as brand new, orphaning the paired device.

---

## 5. Conditions

A discovery strategy can have a set of conditions that must be true before the result is sent to the
app. `conditions` is an `Array` containing one or more `Array`s of rule `Object`s:

- All rules **within** one inner array must be true → **AND**.
- Multiple inner arrays behave as `rulesArray1 OR rulesArray2 OR …` → **OR**.
- Two match types exist: `string` and `regex`.
- **Conditions are matched case-insensitively.**

```json
"conditions": [
  [
    {
      "field": "txt.md",
      "match": { "type": "string", "value": "NL29" }
    },
    {
      "field": "txt.version",
      "match": { "type": "string", "value": "1" }
    }
  ],
  [
    {
      "field": "txt.md",
      "match": { "type": "regex", "value": "NL\\d\\d" }
    }
  ]
]
```

The first inner array means `txt.md == "NL29" AND txt.version == "1"`; the second means
`txt.md` matches `/NL\d\d/`. A result matches if **either** inner array matches.

**Gotcha:** regex backslashes must be **double-escaped** in JSON — `"NL\\d\\d"` in the file is the
regex `NL\d\d`.

Conditions are optional but **highly recommended**: they pre-filter results so your app only receives
discovery results of devices that can actually be paired using your app.

---

## 6. Using discovery with a Driver (recommended)

Link the strategy to the driver and **Homey manages the Device's availability state automatically**.

```json
// /drivers/<driver_id>/driver.compose.json
{
  "discovery": "my_discovery"
}
```

```json
// /.homeycompose/discovery/my_discovery.json
{
  "type": "mdns-sd",
  "mdns-sd": {
    "protocol": "tcp",
    "name": "my_service"
  }
}
```

### Device discovery lifecycle

| Method | Async? | When it is called | What to do |
| --- | --- | --- | --- |
| `onDiscoveryResult(discoveryResult)` | sync | A device has been discovered. | Return a **truthy** value when the result belongs to this device, **falsy** when it doesn't. **By default (not overloaded), the method matches on the device's `data.id` property.** |
| `onDiscoveryAvailable(discoveryResult)` | async | The device is found for the **first time** (i.e. `onDiscoveryResult` returned truthy). | Create the connection to the device. **Throwing here makes the device unavailable with the error message.** |
| `onDiscoveryAddressChanged(discoveryResult)` | sync | The device's address has changed. | Update your connection details; reconnect if the device was offline. |
| `onDiscoveryLastSeenChanged(discoveryResult)` | sync | The device has been found again (heartbeat). | Reconnect if the device was offline. |

Order of events for a typical device: `onDiscoveryResult` → (truthy) → `onDiscoveryAvailable` →
then repeated `onDiscoveryLastSeenChanged`, plus `onDiscoveryAddressChanged` whenever the IP moves.

### Complete worked example

```json
// /.homeycompose/discovery/my_service.json
{
  "type": "mdns-sd",
  "mdns-sd": {
    "name": "my_service",
    "protocol": "tcp"
  },
  "id": "{{txt.serial}}",
  "conditions": [
    [
      { "field": "txt.vendor", "match": { "type": "string", "value": "acme" } }
    ]
  ]
}
```

```json
// /drivers/lamp/driver.compose.json
{
  "name": { "en": "ACME Lamp" },
  "class": "light",
  "capabilities": ["onoff", "dim"],
  "platforms": ["local"],
  "connectivity": ["lan"],
  "discovery": "my_service",
  "pair": [
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "add_devices" } },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

```javascript
// /drivers/lamp/driver.js
'use strict';

const Homey = require('homey');

module.exports = class LampDriver extends Homey.Driver {

  async onInit() {
    this.log('LampDriver has been initialized');
  }

  async onPairListDevices() {
    const discoveryStrategy = this.getDiscoveryStrategy();
    const discoveryResults = discoveryStrategy.getDiscoveryResults();

    return Object.values(discoveryResults).map((discoveryResult) => ({
      // Human-readable name shown in the pair view.
      name: discoveryResult.name || discoveryResult.txt.name || discoveryResult.address,
      // data must be stable forever — NEVER put the IP address in here.
      data: {
        id: discoveryResult.id,
      },
    }));
  }

};
```

```javascript
// /drivers/lamp/device.js
'use strict';

const Homey = require('homey');
const LampApi = require('../../lib/LampApi');

module.exports = class LampDevice extends Homey.Device {

  async onInit() {
    this.registerCapabilityListener('onoff', async (value) => {
      if (!this.api) throw new Error('Not connected');
      await this.api.setPower(value);
    });

    this.registerCapabilityListener('dim', async (value) => {
      if (!this.api) throw new Error('Not connected');
      await this.api.setBrightness(Math.round(value * 100));
    });
  }

  onDiscoveryResult(discoveryResult) {
    // Return a truthy value here if the discovery result matches this device.
    return discoveryResult.id === this.getData().id;
  }

  async onDiscoveryAvailable(discoveryResult) {
    // Called once, when the device has been found (onDiscoveryResult returned true).
    this.api = new LampApi({
      address: discoveryResult.address,
      port: discoveryResult.port,
    });

    // Throwing here marks the device unavailable with this error's message.
    await this.api.connect();

    this.api.on('state', (state) => {
      this.setCapabilityValue('onoff', state.on).catch(this.error);
      this.setCapabilityValue('dim', state.brightness / 100).catch(this.error);
    });
  }

  onDiscoveryAddressChanged(discoveryResult) {
    // The device moved to a different IP — update and reconnect.
    if (!this.api) return;
    this.api.address = discoveryResult.address;
    this.api.reconnect().catch(this.error);
  }

  onDiscoveryLastSeenChanged(discoveryResult) {
    // The device was seen again — reconnect in case it was offline.
    if (!this.api) return;
    this.api.reconnect().catch(this.error);
  }

  async onUninit() {
    if (this.api) {
      await this.api.disconnect().catch(this.error);
    }
  }

};
```

`Driver#getDiscoveryStrategy()` returns the driver's discovery strategy **when defined in the
manifest** — if the driver has no `discovery` key there is no strategy to get.

---

## 7. Using discovery standalone

Call `ManagerDiscovery#getStrategy()` with the strategy id from the App Manifest, read the results
that were already found, and subscribe to `result` for new ones.

```javascript
// /app.js
'use strict';

const Homey = require('homey');

module.exports = class MyApp extends Homey.App {

  async onInit() {
    const discoveryStrategy = this.homey.discovery.getStrategy('my_strategy');

    // Use the discovery results that were already found
    const initialDiscoveryResults = discoveryStrategy.getDiscoveryResults();
    for (const discoveryResult of Object.values(initialDiscoveryResults)) {
      this.handleDiscoveryResult(discoveryResult);
    }

    // And listen to new results while the app is running
    discoveryStrategy.on('result', (discoveryResult) => {
      this.handleDiscoveryResult(discoveryResult);
    });
  }

  handleDiscoveryResult(discoveryResult) {
    this.log('Got result:', discoveryResult.id, discoveryResult.address);

    discoveryResult.on('addressChanged', (result) => {
      this.log('Address changed:', result.id, result.address);
    });

    discoveryResult.on('lastSeenChanged', (result) => {
      this.log('Seen again:', result.id, result.lastSeen);
    });
  }

};
```

**Gotcha:** the accessor on `ManagerDiscovery` is `getStrategy(strategyId)` — there is **no**
`ManagerDiscovery#getDiscoveryStrategy()`. `getDiscoveryStrategy()` exists only on `Driver`.

---

## 8. API reference

### `ManagerDiscovery` — `this.homey.discovery`

| Member | Signature | Notes |
| --- | --- | --- |
| `getStrategy` | `getStrategy(strategyId: string): DiscoveryStrategy` | `strategyId` is the ID as defined in your `app.json` (i.e. the `.homeycompose/discovery/<id>.json` filename). |

### `DiscoveryStrategy`

Not instantiable manually — created by calling `ManagerDiscovery#getStrategy()` (or obtained via
`Driver#getDiscoveryStrategy()`).

| Member | Signature | Notes |
| --- | --- | --- |
| `getDiscoveryResult` | `getDiscoveryResult(id: string): DiscoveryResultMDNSSD \| DiscoveryResultSSDP \| DiscoveryResultMAC` | Get a specific discovery result. |
| `getDiscoveryResults` | `getDiscoveryResults(): Object.<string, (DiscoveryResultMDNSSD\|DiscoveryResultSSDP\|DiscoveryResultMAC)>` | Get all discovery results as an object keyed by result id. |
| `.on('result')` | `(discoveryResult) => void` | Fired when a **new** result has been found. |

### `DiscoveryResult` (base class)

Base class for `DiscoveryResultMAC`, `DiscoveryResultMDNSSD` and `DiscoveryResultSSDP`. Not
instantiable manually.

| Property | Type | Description |
| --- | --- | --- |
| `address` | `string` | The (IP) address of the device. |
| `id` | `string` | The identifier of the result. |
| `lastSeen` | `Date` | When the device has been last discovered. |

| Event | Payload | Description |
| --- | --- | --- |
| `addressChanged` | `discoveryResult: DiscoveryResult` | Fired when the address has changed. |
| `lastSeenChanged` | `discoveryResult: DiscoveryResult` | Fired when the device has been seen again. |

### `DiscoveryResultMDNSSD extends DiscoveryResult`

| Property | Type | Description |
| --- | --- | --- |
| `address` | `string` | The (IP) address of the device. |
| `fullname` | `string \| undefined` | The full name of the device. |
| `host` | `string \| undefined` | The hostname of the device. |
| `id` | `string` | The identifier of the result. |
| `lastSeen` | `Date` | When the device has been last discovered. |
| `name` | `string \| undefined` | The name of the device. |
| `port` | `number \| undefined` | The port of the device. |
| `txt` | `Object.<string, string>` | The TXT records of the device, key-value (lowercased). |

Events: `addressChanged`, `lastSeenChanged` (inherited).

### `DiscoveryResultSSDP extends DiscoveryResult`

| Property | Type | Description |
| --- | --- | --- |
| `address` | `string` | The (IP) address of the device. |
| `headers` | `Object.<string, string>` | The headers (lowercase) in the SSDP response. |
| `id` | `string` | The identifier of the result. |
| `lastSeen` | `Date` | When the device has been last discovered. |
| `port` | `number` | The port of the device. |

Events: `addressChanged`, `lastSeenChanged` (inherited).

**Note:** SSDP results have **no** `name`, `host`, `fullname` or `txt` — match on `headers.*`.

### `DiscoveryResultMAC extends DiscoveryResult`

| Property | Type | Description |
| --- | --- | --- |
| `address` | `string` | The (IP) address of the device. |
| `id` | `string` | The identifier of the result (the MAC address). |
| `lastSeen` | `Date` | When the device has been last discovered. |
| `mac` | `string` | The MAC address of the device. |

Events: `addressChanged`, `lastSeenChanged` (inherited).

**Note:** MAC results have **no** `port` — hardcode or configure the port yourself.

### `Driver`

| Member | Signature | Notes |
| --- | --- | --- |
| `getDiscoveryStrategy` | `getDiscoveryStrategy(): DiscoveryStrategy` | Get the driver's discovery strategy when defined in the manifest. |

### `Device`

| Member | Signature | Notes |
| --- | --- | --- |
| `onDiscoveryResult` | `onDiscoveryResult(discoveryResult)` | Called when a device has been discovered. Overload it and return truthy when the result belongs to the current device, falsy when it doesn't. **By default, the method will match on a device's `data.id` property.** |
| `onDiscoveryAvailable` | `onDiscoveryAvailable(discoveryResult)` | Called when the device is found for the first time. Overload to create a connection. Throwing makes the device unavailable with the error message. |
| `onDiscoveryAddressChanged` | `onDiscoveryAddressChanged(discoveryResult)` | Called when the device's address has changed. |
| `onDiscoveryLastSeenChanged` | `onDiscoveryLastSeenChanged(discoveryResult)` | Called when the device has been found again. |

### `ManagerArp` — `this.homey.arp`

| Member | Signature | Notes |
| --- | --- | --- |
| `getMAC` | `async getMAC(ip: string): Promise<string>` | Get an IP's MAC address. |

```javascript
'use strict';

const Homey = require('homey');

module.exports = class MyDevice extends Homey.Device {

  async onDiscoveryAvailable(discoveryResult) {
    // Resolve a stable hardware identity for an IP found via mDNS-SD/SSDP.
    const mac = await this.homey.arp.getMAC(discoveryResult.address);
    this.log('Device MAC:', mac);

    if (mac !== this.getStoreValue('mac')) {
      await this.setStoreValue('mac', mac);
    }
  }

};
```

Use `getMAC()` when you need a hardware-stable identifier but the discovery protocol only gives you
an IP, or to sanity-check that the address you are about to talk to is still the same physical box.

### `ManagerCloud#getLocalAddress()` — `this.homey.cloud`

| Member | Signature | Notes |
| --- | --- | --- |
| `getLocalAddress` | `async getLocalAddress(): Promise<string>` | Get Homey's local address & port. Resolves to the local address, e.g. `192.168.1.20:80`. **Not supported on Homey Cloud** (Homey Bridge has no local Wi-Fi connection). |

```javascript
'use strict';

const Homey = require('homey');

module.exports = class MyApp extends Homey.App {

  async onInit() {
    if (this.homey.platform === 'cloud') return; // getLocalAddress() is Pro-only

    // Resolves to '<ip>:<port>', e.g. '192.168.1.20:80' — note it already includes the port.
    const localAddress = await this.homey.cloud.getLocalAddress();
    this.log('Homey is reachable at', localAddress);

    // Typical use: tell a LAN device where to push events/streams back to.
    this.callbackUrl = `http://${localAddress}/api/app/${Homey.manifest.id}/events`;
  }

};
```

`this.homey.platform` is `'local' | 'cloud'` (may be `undefined` on older Homey Pro versions), so
guard rather than assume. See `references/homey-cloud.md`.

---

## 9. Device identity: `data` vs `store` vs `settings`

**Hard rule: an IP address must never go in `device.data`.**

| Where | Mutable? | Use for |
| --- | --- | --- |
| `data` | **No** — cannot be changed after pairing; Homey identifies the device by `data` + driver id | Only the essential, permanently stable identity: a MAC address, a serial number, the discovery result `id`. |
| `store` | Yes, at runtime (`getStoreValue` / `setStoreValue`) | Persistent-but-changeable properties. An IP address *can* live here, but prefer discovery. |
| `settings` | Yes, user-editable | Values the user should be able to change. |
| in-memory (`this.…`) | Yes | The current address from the discovery result — the normal place for it. |

> Only put the essential properties needed to identify a device in the data object. For example, a
> MAC address is a good property, an IP address is not, because it can change over time.

> Instead of storing the device's IP address in the device store you could use the local network
> device discovery functionality that is built into Homey.

In practice, with discovery wired to the driver: `data: { id: discoveryResult.id }`, and the address
comes from `discoveryResult.address` inside `onDiscoveryAvailable` / `onDiscoveryAddressChanged`.

---

## 10. Non-JavaScript runtimes

| JavaScript | Python |
| --- | --- |
| `this.homey.discovery.getStrategy(id)` | `self.homey.discovery.get_strategy(id)` |
| `strategy.getDiscoveryResults()` | `strategy.get_discovery_results()` |
| `Driver#getDiscoveryStrategy()` | `Driver#get_discovery_strategy()` |
| `onDiscoveryResult` | `on_discovery_result` (async) |
| `onDiscoveryAvailable` | `on_discovery_available` (async) |
| `onDiscoveryAddressChanged` | `on_discovery_address_changed` (async) |
| `onDiscoveryLastSeenChanged` | `on_discovery_last_seen_changed` (async) |

TypeScript apps import the result types from `homey`:
`import Homey, { type DiscoveryResultMDNSSD } from "homey";` — `getDiscoveryResults()` returns
`{ [id: string]: DiscoveryResult… }` and usually needs a cast to the concrete subclass. See
`references/python-apps.md` and `references/cli-and-tooling.md`.

---

## 11. Gotchas

- **Manual IP entry is a store rejection.** App Store submissions where users must enter an IP
  address, where discovery could have been used instead, will be rejected. Only fall back to a
  manual-IP pair view when the device genuinely broadcasts nothing.
- **Homey Cloud / Bridge has no LAN at all.** mDNS, SSDP and MAC discovery are not supported, and
  neither is `ManagerCloud#getLocalAddress()`. A LAN driver must be `"platforms": ["local"]` with
  `"connectivity": ["lan"]`.
- **Never put an IP address in `device.data`.** `data` is immutable after pairing and identifies the
  device forever; DHCP will break it. Use the discovery result `id`, a MAC, or a serial.
- **Never template the strategy `id` off `{{address}}`.** The whole point of `id` is that it survives
  an IP change.
- **MAC OUIs are decimal, not hex.** JSON has no hexadecimal notation:
  `00:24:6d` → `[0, 36, 109]`.
- **`mdns-sd.name` excludes the underscore and the protocol.** The service `_homey._tcp` is
  `{ "name": "homey", "protocol": "tcp" }`.
- **Regex values are double-escaped in JSON.** `"NL\\d\\d"` in the file means the regex `NL\d\d`.
- **Conditions are case-insensitive** and structured `AND` inside an inner array, `OR` between inner
  arrays. Forgetting the outer array (writing `"conditions": [ {…} ]`) silently does not do what you
  expect — it must be an array *of arrays*.
- **`txt` keys and `headers` keys are lowercased** by Homey. Match on `txt.md`, not `txt.MD`;
  `headers.usn`, not `headers.USN`.
- **SSDP results have no `txt`/`name`; MAC results have no `port`.** Pick the strategy that actually
  exposes the fields you need to identify and reach the device.
- **`onDiscoveryResult` has a default implementation.** If you do not overload it, Homey matches on
  the device's `data.id` property. That is exactly right when you paired with
  `data: { id: discoveryResult.id }`, and silently wrong when your `data` key is named anything else —
  in which case you must overload it.
- **Throwing in `onDiscoveryAvailable` marks the device unavailable** with the thrown message — this
  is the intended way to surface "cannot connect". Do not swallow the error.
- **`onDiscoveryAddressChanged` / `onDiscoveryLastSeenChanged` are not async-awaited.** Fire-and-forget
  reconnects there, always with `.catch(this.error)`; an unhandled rejection can crash the app.
- **Guard against `this.api` being undefined** in `onDiscoveryAddressChanged` /
  `onDiscoveryLastSeenChanged` — they can fire before `onDiscoveryAvailable` has finished connecting.
- **Availability is managed for you** only when the strategy is linked to the driver via the
  `discovery` key. Standalone `ManagerDiscovery` usage does not touch device availability.
- **`homey app run` uses Docker `bridge` networking by default**, which is not the host LAN. Pass
  `homey app run --network host` (macOS/Linux) when your app needs LAN discovery from the host, or use
  `homey app install` to test on the real Homey. `homey api diagnose` reports which discovery
  strategies work.
- **`app.json` is generated.** Add strategies to `/.homeycompose/discovery/<id>.json`, never to
  `/app.json`.
- **The Wi-Fi connection might not always be available.** Homey still functions normally without
  Wi-Fi or internet, so the app must tolerate a device never appearing and reconnect when it does.

---

## Sources

- <https://apps.developer.homey.app/wireless/wi-fi>
- <https://apps.developer.homey.app/wireless/wi-fi/discovery>
- <https://apps.developer.homey.app/the-basics/devices>
- <https://apps.developer.homey.app/the-basics/devices/pairing>
- <https://apps.developer.homey.app/the-basics/getting-started/homey-cli>
- <https://apps.developer.homey.app/advanced/homey-compose>
- <https://apps.developer.homey.app/guides/homey-cloud>
- <https://apps-sdk-v3.developer.homey.app/ManagerDiscovery.html>
- <https://apps-sdk-v3.developer.homey.app/DiscoveryStrategy.html>
- <https://apps-sdk-v3.developer.homey.app/DiscoveryResult.html>
- <https://apps-sdk-v3.developer.homey.app/DiscoveryResultMDNSSD.html>
- <https://apps-sdk-v3.developer.homey.app/DiscoveryResultSSDP.html>
- <https://apps-sdk-v3.developer.homey.app/DiscoveryResultMAC.html>
- <https://apps-sdk-v3.developer.homey.app/ManagerArp.html>
- <https://apps-sdk-v3.developer.homey.app/ManagerCloud.html#getLocalAddress>
- <https://apps-sdk-v3.developer.homey.app/Driver.html#getDiscoveryStrategy>
- <https://apps-sdk-v3.developer.homey.app/Device.html>
- Example app: <https://github.com/athombv/com.plugwise.adam-example>
