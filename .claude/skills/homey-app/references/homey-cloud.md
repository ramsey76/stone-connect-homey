# Homey Cloud

Everything that differs when an app runs on **Homey Cloud** (Homey Bridge) instead of **Homey Pro** /
**Homey Self-Hosted Server**: the `platforms` manifest key, the multi-tenancy rules, the list of
unavailable managers and permissions, the Docker-based local test loop, and the Verified Developer
requirement for publishing. Sibling files: `references/app-and-manifest.md` (manifest, lifecycle),
`references/drivers-and-devices.md` (driver manifest), `references/cloud-oauth-webhooks.md`,
`references/publishing.md`.

---

## Architecture

The Homey Apps SDK is engineered to support both Homey Pro and Homey Cloud. An app written for one
usually already works on the other — the differences below are the exceptions.

| | Homey Pro / Self-Hosted Server | Homey Cloud |
| --- | --- | --- |
| Where the app process runs | On the Homey itself, sandboxed and **chroot'ed** | In Athom's cloud, in a **Docker container** |
| Instances per process | One app instance per process | **Several app instances (several users) share one Node.js process** — multi-tenancy |
| Horizontal scaling | n/a | A popular app is started on **several servers** to spread the load |
| Filesystem root `/` | Your app's directory | The **Linux root** |
| Radios | Built into Homey Pro | Provided by the user's **Homey Bridge** |
| SDK levels | SDK v2 and v3 | **SDK v3 only** |

Consequences that drive almost every rule on this page:

1. Because instances share a process, **module-level (global) mutable state is shared between users**.
2. Because an app instance can be destroyed without the process dying, **cleanup must be explicit**.
3. Because `/` differs, **absolute paths break**; always use relative paths / `__dirname`.

### Runtime platform detection

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    if (this.homey.platform === 'cloud') {
      this.log('running on Homey Cloud — no LAN, no Web API, no app-to-app');
    }
  }

}

module.exports = MyApp;
```

| Property | Type | Notes |
| --- | --- | --- |
| `this.homey.platform` | `'local'` \| `'cloud'` | May be `undefined` on older Homey Pro software — treat `undefined` as `'local'`. |
| `this.homey.platformVersion` | `1` \| `2` | Homey Cloud is `1`. May be `undefined` on older software. |
| `this.homey.platformFeatures` | `string[]` | Feature strings supported by this Homey. |
| `this.homey.hasFeature(feature)` | `boolean` | Homey v12.7.1+. Guard with `typeof this.homey.hasFeature === 'function'` on wider `compatibility` ranges. |

| Product | `platform` | `platformVersion` |
| --- | --- | --- |
| Homey Cloud | `cloud` | `1` |
| Homey (Early 2016 / 2018 / 2019) | `local` | `1` |
| Homey Pro (Early 2019) | `local` | `1` |
| Homey Pro (Early 2023) | `local` | `2` |
| Homey Pro mini (2025) | `local` | `2` |
| Homey Pro (2026) | `local` | `2` |
| Homey Self-Hosted Server | `local` | `2` |

---

## Eligibility — publishing for Homey Cloud

Homey Cloud is offered to a mainstream audience, so Athom gates it:

- A **[Homey Verified Developer](https://homey.app/homey-verified-developer/) subscription is required**
  to publish an app to the App Store when the manifest targets `"platforms": ["cloud"]` or
  `"platforms": ["local", "cloud"]`. Publishing for Homey Pro **does not** require a subscription and
  will always remain free.
- The subscription is **solely intended for companies, brands, or a third-party developer commissioned
  by said brand/company**. Only **official app integrations** are approved. Apps published by community
  developers holding a verified subscription are **not approved without proof of a partnership** with
  the brand.
- Verified developers get the blue **"Official"** badge behind the developer name in the App Store,
  plus code-level support and in-depth app reviews.
- To obtain it, contact Athom's partnerships team at `partners@athom.com`.
- A verified developer account name **should be the name of the company publishing the app**
  (e.g. *Home Connect GmbH*, *frient A/S*, *Yale Access*, *Plugwise B.V.*).
- Verified developers do **not** get the "Donate" button on their app pages.

> **Gotcha — default to `"platforms": ["local"]`.** Unless the user actually holds a Verified Developer
> subscription, targeting `["cloud"]` or `["local", "cloud"]` gets `homey app publish` rejected with
> *"Your account is not eligible to publish apps for Homey Cloud."* Adding `"cloud"` speculatively costs
> nothing at `homey app run` time but blocks the publish.

> **Gotcha — `platforms` ≠ `connectivity`.** `platforms` says *where the app can run*; a driver's
> `connectivity` says *how the device talks*. A perfectly normal `"platforms": ["local"]` app can still
> integrate a cloud API with `"connectivity": ["cloud"]`. Wanting to talk to a vendor cloud is **not** a
> reason to add `"cloud"` to `platforms`.

### Validation levels

```bash
homey app validate --level verified
```

| Level | When it applies |
| --- | --- |
| `debug` | During development. Optional fields such as `images`, `brandColor` and `category` are not required. |
| `publish` | Required to publish to the Homey App Store for Homey Pro. |
| `verified` | Required for verified developers and **required for Homey Cloud**. Adds requirements such as `platforms`, `connectivity` and `support` in the manifest. Applied by default when your account is a verified developer. |

What the `verified` level actually adds on top of `publish` (from `homey-lib`'s validator):

| Check | Error |
| --- | --- |
| App manifest `platforms` | ``The property `platforms` is required in order to publish a verified app.`` |
| App manifest `support` | ``The property `support` is required in order to publish a verified app.`` |
| Every driver's `platforms` | ``drivers.<id>: property `platforms` is required in order to publish a verified app.`` |
| Every driver's `connectivity` | ``drivers.<id>: property `connectivity` is required in order to publish a verified app.`` |
| Every Flow-card argument's `title` | ``…args['<name>'].title is required for arguments in order to publish a verified app.`` |
| Every Flow card's `titleFormatted` | ``…titleFormatted is required in order to publish a verified app.`` |
| `homey:manager:speech-input` permission | Hard error at `verified` (`Unsupported permission: …, please remove any speech input related functionality.`); only a warning at lower levels. |

Two permission rules apply at every level and matter when targeting Cloud:

- `homey:app:com.athom.homeyscript` is **always forbidden** (`Forbidden permission: …`).
- `homey:manager:api` only produces a warning at `publish`/`verified`
  (*"using the homey:manager:api permission will require a more thorough review"*) — the block on Homey
  Cloud is a **store/runtime restriction**, not a `homey app validate` failure. Do not expect the CLI to
  catch it for you.

### App review — what gets rejected for Cloud

- Apps that **add Drivers for a brand of smart home devices** are very welcome on Homey Cloud.
- Apps that add **advanced functionality only usable in combination with other apps** are rejected.
  These are typically the "Tools" category apps (DIY alarm systems, HomeyScript, Device Groups…), which
  cannot work on Cloud anyway because `homey:manager:api` is forbidden.
- Verified-developer reviews are thorough: provide **sample devices** before submission (for cloud apps
  a **demo account** can be an option). Review of a new verified app takes longer than a normal review.
- If you are a verified developer and unsure whether an app idea will be allowed on Homey Cloud,
  contact developer support before building it.

---

## The `platforms` manifest key

`platforms` must be added to the **App**, **Driver** and **Flow** manifests. Only SDK v3 is supported on
Homey Cloud — make sure `"sdk": 3` before doing anything else.

### App manifest

```jsonc
// /.homeycompose/app.json
{
  "id": "my.company.example",
  "version": "1.0.0",
  "compatibility": ">=5.0.0",
  "platforms": ["local", "cloud"],
  "sdk": 3
  // ...
}
```

### Flow manifest

```jsonc
// /.homeycompose/flow/triggers/rain_start.json
{
  "title": { "en": "It starts raining" },
  "hint": { "en": "When it starts raining more than 0.1 mm/h." },
  "platforms": ["local", "cloud"]
}
```

### Driver manifest

```jsonc
// /drivers/<driver_id>/driver.compose.json
{
  "name": { "en": "My Driver" },
  "platforms": ["local", "cloud"],
  "connectivity": ["ble"],
  "class": "light",
  "capabilities": ["onoff", "dim"]
}
```

### `platforms` values and CLI rules

| Value | Meaning |
| --- | --- |
| `local` | Homey Pro / Homey Self-Hosted Server (runs locally) |
| `cloud` | Homey Cloud |

- Default is `["local"]`.
- A **driver may not list a platform the app manifest does not list** — hard error:
  ``drivers.<id> invalid 'platforms': App manifest does not list 'cloud' as a supported platform.``
  (and the same message for `'local'`).
- **The same rule applies to Flow cards.** A Flow card whose `platforms` includes a value the app
  manifest omits fails validation with
  ``<card path> invalid 'platforms': App manifest does not list 'cloud' as a supported platform.``
- The CLI **warns** when a driver has no `platforms` while the app manifest includes `cloud` —
  ``Warning: drivers.<id> doesn't have a 'platforms' property. The default is ["local"].`` — so a missing
  `platforms` on a driver silently keeps that driver off Homey Cloud.
- `platforms` is **required to publish a verified app**.

### `platformLocalRequiredFeatures` / `platformLocalOptionalFeatures`

Two sibling app-manifest keys gate the app on local-only hardware. Both take the same enum.

| Key | Effect |
| --- | --- |
| `platformLocalRequiredFeatures` | The app becomes **uninstallable** on a Homey Pro that lacks any listed feature. Use only when the app cannot function without it. |
| `platformLocalOptionalFeatures` | Present in the app-manifest schema and the validator (same enum), but not described on the Manifest docs page. It carries **no** installability restriction and **no** cloud hard error — only the `platforms: [local]` warning below. |

- Documented values: `nfc`, `ledring`, `speaker`, `matter`. The app-manifest schema additionally accepts
  **`camera-streaming`**.
- `platformLocalRequiredFeatures` **cannot be combined with `"cloud"`** in `platforms` — hard error:
  ``The property `platformLocalRequiredFeatures` can not be used in combination with platform: `cloud`.``
  All of these are local-only hardware, which is exactly why the combination is illegal.
  `platformLocalOptionalFeatures` has **no** such hard error.
- Both only **warn** when `platforms` lacks `"local"`
  (``Warning: using `platformLocalRequiredFeatures` requires `platforms: [local]`.``).
- Matter cross-check (warnings only): if every driver has `connectivity: ["matter"]` but `matter` is not
  in `platformLocalRequiredFeatures`, the CLI warns — and vice versa.

---

## `connectivity` (driver manifest)

Each driver declares how it reaches the device. Multiple values are allowed (e.g.
`["infrared", "lan"]` for a TV turned on by infrared and then controlled over Wi-Fi).

Values, verbatim from the Homey Cloud guide:

| Value | Description |
| --- | --- |
| `lan` | **Not possible with Homey Bridge** — see [Local Wi-Fi & Device Discovery](#unavailable-lan). |
| `cloud` | Your Driver uses OAuth or Webhooks to connect to a cloud service. |
| `ble` | Your Driver connects to Bluetooth Low Energy devices. |
| `zwave` | Your Driver implements a Z-Wave device. |
| `zigbee` | Your Driver implements a Zigbee device. |
| `infrared` | Your Driver sends infrared signals. |
| `rf433` | Your Driver sends 433 MHz signals. |
| `rf868` | **Not possible with Homey Bridge.** |

The driver-manifest schema accepts a **9th** value the guide's table omits: `matter` (Matter apps are
supported since Homey Pro (Early 2023) v11.1.0), which is likewise not available on Homey Cloud. Full
schema enum: `lan`, `cloud`, `ble`, `zwave`, `zigbee`, `infrared`, `rf433`, `rf868`, `matter`.

Rules enforced by the CLI:

- `connectivity` is **required to publish a verified app**.
- **A driver whose `platforms` includes `cloud` may not use `lan`, `matter` or `rf868`** — hard error:
  ``drivers.<id> invalid 'connectivity': Platform 'cloud' does not support 'lan', 'matter' or 'rf868'.``
- `connectivity: ["matter"]` requires a `matter` object on the driver, and a driver with a `matter`
  object must include `matter` in `connectivity` — both are hard errors. See
  `references/wireless-ble-matter.md`.

So a Homey Cloud driver is limited to: `cloud`, `ble`, `zwave`, `zigbee`, `infrared`, `rf433`.

---

## Multi-tenancy rules

These are mandatory on Homey Cloud and good practice everywhere.

### 1. Never mutate global variables

The global scope is shared between app instances, so values become unpredictable.

```javascript
// BAD — /app.js
'use strict';

const Homey = require('homey');

let count = 0; // shared by several app instances

class App extends Homey.App {
  onInit() {
    count += 1;
  }
}

module.exports = App;
```

```javascript
// GOOD — /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  onInit() {
    // only used by a single app instance
    this.count = (this.count ?? 0) + 1;
  }
}

module.exports = App;
```

Keep every piece of mutable state as a property on the `App`, `Driver` or `Device` instance. Module-level
`const` values that are never mutated (URLs, lookup tables, class definitions) are fine.

### 2. Clean up in `onUninit()`

On Homey Pro, removing an app kills the entire process. On Homey Cloud the process keeps running for
other tenants, so **resources must be released explicitly**. The SDK provides `App#onUninit()`,
`Driver#onUninit()` and `Device#onUninit()`.

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {

  async onInit() {
    this.api = new DeviceApi();
  }

  async onUninit() {
    this.api.destroy();
  }

}

module.exports = App;
```

Release in `onUninit()`: sockets and HTTP agents, WebSocket/MQTT connections, event listeners on shared
objects, vendor-SDK clients, and any timer you did not create through `this.homey`.

### 3. Use `this.homey` timers, never the globals

`this.homey.setTimeout()` / `this.homey.setInterval()` behave exactly like their global counterparts but
are **automatically cleared when the app instance is destroyed**. Matching
`this.homey.clearTimeout()` / `this.homey.clearInterval()` exist.

```javascript
// BAD — /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  onInit() {
    // the interval is not cleaned up after the app instance is destroyed
    setInterval(() => {
      // do something
    }, 10000);
  }
}

module.exports = App;
```

```javascript
// GOOD — /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  onInit() {
    // automatically cleared when the app is destroyed
    this.homey.setInterval(() => {
      // do something
    }, 10000);
  }
}

module.exports = App;
```

### 4. Unhandled promise rejections crash the app

On Homey Cloud an **unhandled promise rejection crashes the app**. Unhandled rejections can cause memory
leaks and usually indicate that errors are not being handled. This behaviour is about to become standard
in Node.js and is therefore also coming to Homey Pro in the near future — write for it now.

If the error genuinely does not matter, log it: `.catch(this.error)`.

```javascript
// BAD — /drivers/<driver_id>/device.js
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {
  async onInit() {
    // returns a promise, which may cause an unhandled promise rejection
    this.setCapabilityValue('onoff', false);
  }
}

module.exports = Device;
```

```javascript
// GOOD — /drivers/<driver_id>/device.js
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {
  async onInit() {
    // catching the promise prevents unhandled promise rejections
    this.setCapabilityValue('onoff', false).catch(this.error);
  }
}

module.exports = Device;
```

Every fire-and-forget SDK call returns a promise: `setCapabilityValue()`, `setSettings()`,
`setStoreValue()`, `setAvailable()`, `setUnavailable()`, `setWarning()`, Flow `trigger()`. Either
`await` them inside an `async` function that itself is awaited, or append `.catch(this.error)`.

### 5. Relative paths only

On Homey Pro apps are sandboxed and chroot'ed, so `/` is your app's directory. On Homey Cloud apps run
in a Docker container, so `/` is the **Linux root**. An absolute path that works on Pro reads the wrong
file (or nothing) on Cloud.

```javascript
'use strict';

const path = require('path');

// GOOD
const foo = require('./assets/foo.js');
const svgPath = path.join(__dirname, 'myfile.svg');

// BAD — resolves differently on Homey Pro and Homey Cloud
// const svgPath = '/assets/myfile.svg';
```

### 6. No app-writable filesystem

The `/userdata/` folder is documented as writable **on Homey Pro** only. Do not design a Homey Cloud app
around writing files. Use, in order of preference:

| Need | Use |
| --- | --- |
| Per-device user-visible values | Device Settings (`this.getSettings()` / `setSettings()`) |
| Per-device back-end values | Device Store (`getStoreValue()` / `setStoreValue()`) |
| App-wide JSON-serializable values | `this.homey.settings` (`ManagerSettings`) |
| Ephemeral values | Properties on the instance (`this.…`) |

Note that on Homey Pro `/userdata/` is publicly reachable at
`https://<homey>/app/your.app.id/userdata/` — use unguessable filenames (a UUID, not `image1.jpg`).

### 7. Resource limits

The SDK emits system events when an app is consuming too much of the machine. Handle or at least log
them; an app that does not behave within a reasonable time is **killed**.

```javascript
this.homey.on('memwarn', ({ count, limit }) => this.log(`memwarn ${count}/${limit}`));
this.homey.on('cpuwarn', ({ count, limit }) => this.log(`cpuwarn ${count}/${limit}`));
this.homey.on('unload', () => this.log('app is being stopped'));
```

| Event | Payload | Fired when |
| --- | --- | --- |
| `memwarn` | `{ count, limit }` | The app uses too much memory. `count` = warnings sent so far, `limit` = max warnings before the kill. |
| `cpuwarn` | `{ count, limit }` | The app uses too much CPU. Same kill semantics. |
| `unload` | — | The app is being stopped. |

On Cloud these matter more than on Pro: the process is shared, so a leaking instance degrades other
tenants. Poll conservatively, close connections, and prefer webhooks/push over tight intervals.

---

## Unavailable on Homey Cloud

| Feature | Status on Homey Cloud | Alternative |
| --- | --- | --- |
| **App Web API** (`/api.js`, `api` manifest key, REST + Realtime) | **Not supported.** Apps on Homey Cloud are not allowed to expose a Web API. | Webhooks (`this.homey.cloud.createWebhook()`) still work. |
| **App-to-app communication** (`homey:app:<appId>` permission) | **Not supported.** | Embed the functionality in your own app. |
| **`homey:manager:api` permission / `ManagerApi` / Homey Web API** | **Not allowed.** | — (this is what blocks most "Tools" apps) |
| **Custom App Settings views** (`/settings/index.html`) | **Not supported.** | Ask for the information during **pairing**; use **repair** views to update it later so Flows do not break. |
| <a id="unavailable-lan"></a>**Local Wi-Fi / LAN** | **Not supported** — Homey Bridge has no local Wi-Fi connection. | Use the vendor's cloud API (`connectivity: ["cloud"]`). |
| **mDNS-SD, SSDP and MAC (ARP) discovery** | **Not supported.** | — |
| **`ManagerCloud#getLocalAddress()`** | **Not supported.** | Guard with `this.homey.platform === 'cloud'`. |
| **`connectivity: "lan"`** | **Not possible with Homey Bridge**; validation fails on a cloud driver. | `cloud` |
| **`connectivity: "rf868"`** (868 MHz) | **Not possible with Homey Bridge.** | — |
| **`connectivity: "matter"` / Matter drivers** | **Not available on Homey Cloud.** Matter drivers must be `"platforms": ["local"]`. | — |
| **Widgets** (`/widgets/<id>/`) | **Do not work on Homey Cloud** (and require `"compatibility": ">=12.3.0"`). | — |
| **LED ring** (`ManagerLedring`) | Controllable only on Homey Pro (Early 2019) and older. | — |
| **`platformLocalRequiredFeatures`** (`nfc`, `ledring`, `speaker`, `matter`; schema also allows `camera-streaming`) | Cannot be combined with `"cloud"` in `platforms` — hard validation error. `platformLocalOptionalFeatures` takes the same enum but has no such error. | — |
| **`homey:manager:speech-input` permission** | Hard error at `--level verified` (so effectively unusable for Cloud); warning at lower levels. | Remove all speech-input functionality. |
| **`homey:app:com.athom.homeyscript` permission** | **Always forbidden**, on every platform and level. | — |
| **BLE advertisement subscriptions** (`ble-advertisements` feature, `ManagerBLE#subscribeToAdvertisements()`) | Feature is listed only for Homey Pro (Early 2023), Homey Pro mini, Homey Pro 2026 and Homey SHS. | Check `this.homey.hasFeature('ble-advertisements')` and fall back to `ManagerBLE#find()` polling. |
| **Writable `/userdata/`** | Documented as writable on Homey Pro only. | Device Store / `ManagerSettings`. |
| **SDK v2** | Only SDK v3 is supported. | `"sdk": 3` |

Guard pattern for anything in this table that you still want to use on Pro:

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    if (this.homey.platform === 'cloud') return; // getLocalAddress() is Pro-only

    const localAddress = await this.homey.cloud.getLocalAddress();
    this.log('local address', localAddress);
  }

}

module.exports = MyApp;
```

---

## Available on Homey Cloud

Things that do work, and that are easy to assume otherwise:

| Feature | Notes |
| --- | --- |
| **Webhooks** — `this.homey.cloud.createWebhook(id, secret, data)` | The documented replacement for the App Web API. See `references/cloud-oauth-webhooks.md`. |
| **OAuth2 callbacks** — `this.homey.cloud.createOAuth2Callback(url)` | The whole `connectivity: "cloud"` pairing story. |
| **`this.homey.cloud.getHomeyId()`** | Used for query-parameter webhook URLs. |
| **Z-Wave drivers** | The Homey Pro Z-Wave User Manual applies to Homey Pro (Early 2023) and newer, Homey Pro mini, Homey Self-Hosted Server **and Homey Cloud**. |
| **Zigbee drivers** | `connectivity: ["zigbee"]` is allowed on Cloud. |
| **433 MHz RF and Infrared** | `connectivity: ["rf433"]`, `["infrared"]`. |
| **Bluetooth LE** | `connectivity: ["ble"]` is an allowed Cloud value; only *advertisement subscriptions* are gated behind the `ble-advertisements` feature. |
| **Z-Wave & Zigbee OTA firmware updates** | Homey firmware v13.2.0+; available for Homey Pro (Early 2023, 2026, mini), Homey Self-Hosted Server **and Homey Cloud**. Mobile App v9.10.0+ required to start updates. |
| **Videos** | Available on Homey Pro (2023–2026), Homey Pro mini since v12.7.0, **and Homey Cloud**. |
| **Custom pairing & repair views** | The documented substitute for app settings pages. |
| **The Homey CSS classes for custom views** | Available on Homey Cloud, and on Homey Pro since v8.1.0. |
| **Energy** | `cumulativeImportedCapability` / `cumulativeExportedCapability` (Homey v12.3.0+) and `meterPowerImportedCapability` / `meterPowerExportedCapability` (v12.4.5+) are used on Homey Pro (Early 2023), Homey Pro mini **and Homey Cloud**. |
| **Node.js 22** | Homey Cloud runs Node.js v22 from Homey v12.9.0. **Cloud apps only migrate to Node 22 after you publish a new version after December 2nd, 2025** — earlier published versions keep running on the previous Node.js version. |

---

## Local testing (Docker)

Despite running in the cloud in production, a Homey Cloud app is developed locally.

**Prerequisites**

- **Node.js v24 or higher** for the Homey CLI itself (`npm install --global homey`).
- **Docker**, required for Homey Cloud, Homey Pro and Homey Self-Hosted Server targets (and for Python
  apps).

**The loop**

```bash
homey login
homey select                # pick the Cloud Homey
homey app run               # runs locally in Docker, connected to Homey Cloud
```

If you run `homey app run` while a Cloud Homey is selected, the CLI **automatically guides you to
install all the required tools**, then runs the app on your computer and connects it to Homey Cloud.
Console output streams to your terminal; `Ctrl+C` uninstalls the app from the Homey again.

`homey app run` options relevant here:

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--clean`, `-c` | boolean | `false` | Delete all userdata, paired devices and settings before running. Useful when testing pairing flows. |
| `--remote`, `-r` | boolean | `false` | Force the app to run on the Homey instead of locally in Docker. Automatically enabled on Homey Pro (2016–2019). |
| `--skip-build`, `-s` | boolean | `false` | Skip the build step. |
| `--link-modules`, `-l` | string | `""` | Comma-separated list of local Node.js modules to link into the runner. **Docker mode only.** |
| `--network`, `-n` | string | `bridge` | Docker network mode; must match a name from `docker network ls`. Use `host` if your app needs LAN discovery from the host. **Docker mode only.** |
| `--docker-socket-path` | string | — | Path to the Docker socket (Colima, Rancher Desktop, …). |
| `--find-links` | string | — | Additional location to search for Python package distributions. |

`--docker-socket-path` and `--find-links` are also accepted by `homey app build`, `homey app validate`
and `homey app publish`.

**Troubleshooting**

| Symptom | Fix |
| --- | --- |
| *"Cannot connect to the Docker daemon."* | `run`, `build`, `validate` and `publish` require Docker on Homey Pro (Early 2023) and later, and on Cloud. Start Docker Desktop / Colima / Rancher Desktop, or pass `--docker-socket-path <path>`. |
| Cannot reach the Homey from Docker | `homey api diagnose` shows which discovery strategies work; `homey app run --network host` (macOS/Linux) often helps when local mDNS discovery is required. |
| *"No Homey is currently selected."* | `homey select` (interactive) or `homey select --name "<homey>"`; check with `homey select current`. |
| Homey Pro (2016–2019) cannot use Docker | Pass `--remote` (the CLI does it automatically); rebuilds are slower than Docker mode. |
| Publish rejected on validation | Run `homey app validate --level verified` locally and fix every error first. |
| Reset the CLI | Remove `~/.homey/`. |

> **Gotcha — a fresh Compose-only repo has no `/app.json`.** `/app.json` is *generated* from
> `.homeycompose/` and the `*.compose.json` files at run/build/publish time. Tools (and your own
> scripts) that read `app.json` before the first `homey app run` / `homey app build` fail with `ENOENT`.
> Never hand-edit `/app.json`; edit the compose sources. Details in `references/app-and-manifest.md`.

---

## Porting an existing Homey Pro app to Homey Cloud

1. Confirm `"sdk": 3`.
2. Add `"platforms": ["local", "cloud"]` to `/.homeycompose/app.json`.
3. Add `"platforms"` to **every** Flow card manifest that should be available on Cloud
   (`/.homeycompose/flow/{triggers,conditions,actions}/<id>.json`, and driver-scoped cards).
4. Add `"platforms"` and `"connectivity"` to every `driver.compose.json`. Drop `lan`, `matter` and
   `rf868` drivers back to `"platforms": ["local"]`.
5. Remove `homey:manager:api` and every `homey:app:<appId>` permission (or keep the app local-only).
6. Delete `/api.js` and the `api` manifest key, or accept that it is Pro-only — Cloud apps may not
   expose a Web API. Move external triggers to webhooks.
7. Delete `/settings/index.html`; move whatever it asked for into pairing views and add a `repair` view
   so users can update credentials.
8. Delete/gate widgets (`/widgets/`) — they do not work on Cloud.
9. Replace discovery-based drivers (mDNS/SSDP/MAC) with cloud-API drivers, or keep them local-only.
10. Replace every module-level `let`/`var` with instance properties.
11. Replace every `setTimeout`/`setInterval` with `this.homey.setTimeout`/`this.homey.setInterval`.
12. Implement `onUninit()` on App/Driver/Device and release connections there.
13. Add `.catch(this.error)` to every un-awaited promise.
14. Replace absolute paths with `./…` / `path.join(__dirname, …)`.
15. Add `support` to the manifest (required at the `verified` level).
16. Give every Flow card a `titleFormatted` and every Flow-card argument a `title` — both are hard
    requirements at the `verified` level.
17. Remove the `homey:manager:speech-input` permission if present (hard error at `verified`).
18. `homey app validate --level verified`.

---

## Homey Pro vs Homey Cloud — comparison

| | Homey Pro / Homey Self-Hosted Server | Homey Cloud (Homey Bridge) |
| --- | --- | --- |
| `platforms` value | `"local"` | `"cloud"` |
| `this.homey.platform` | `'local'` | `'cloud'` |
| `this.homey.platformVersion` | `1` (2016–2019) / `2` (Early 2023, mini, 2026, SHS) | `1` |
| SDK levels | v2 and v3 | **v3 only** |
| Runtime | Node.js v22 (Homey v12.9.0+) | Node.js v22 (Homey v12.9.0+), after re-publishing post 2025-12-02 |
| Process model | One instance per process, sandboxed + chroot'ed | **Multi-tenant**: many instances per Node.js process, spread over several servers |
| Filesystem root `/` | The app's directory | The Linux root (Docker container) |
| Writable `/userdata/` | Yes (publicly served at `https://<homey>/app/<id>/userdata/`) | Not documented — do not rely on it |
| Global mutable state | Works (still bad practice) | **Forbidden** — shared between tenants |
| Timers | `this.homey.setTimeout/​setInterval` recommended | **Required** — plain timers leak |
| Unhandled promise rejection | Tolerated today, changing soon | **Crashes the app** |
| App Web API (`api.js`, REST + Realtime) | Yes | **No** |
| Webhooks (`ManagerCloud#createWebhook`) | Yes | **Yes** |
| OAuth2 callback (`ManagerCloud#createOAuth2Callback`) | Yes | Yes |
| App-to-app (`homey:app:<appId>`) | Yes | **No** |
| `homey:manager:api` / `ManagerApi` | Yes | **No** |
| Custom App Settings views | Yes (`/settings/index.html`) | **No** — use pairing + repair views |
| Custom pairing / repair views | Yes | Yes |
| Homey CSS classes for custom views | Yes, since Homey v8.1.0 | Yes |
| Widgets | Yes (`compatibility >= 12.3.0`) | **No** |
| LAN / Wi-Fi devices (`connectivity: "lan"`) | Yes | **No** |
| mDNS-SD / SSDP / MAC discovery | Yes | **No** |
| `ManagerCloud#getLocalAddress()` | Yes | **No** |
| Z-Wave | Yes | Yes |
| Zigbee | Yes | Yes |
| 433 MHz (`rf433`) | Yes | Yes |
| 868 MHz (`rf868`) | Homey Pro 2016–2019 only | **No** |
| Infrared | Yes | Yes |
| Bluetooth LE (`connectivity: "ble"`) | Yes | Yes |
| BLE advertisement subscriptions (`ble-advertisements`) | Homey Pro (Early 2023), Pro mini, Pro 2026, SHS | **No** |
| Matter (`connectivity: "matter"`) | Homey Pro (Early 2023) v11.1.0+ | **No** — Matter drivers must be `"platforms": ["local"]` |
| Z-Wave & Zigbee OTA firmware updates | Homey Pro (Early 2023, 2026, mini), SHS — v13.2.0+ | **Yes** — v13.2.0+ |
| Videos | Homey Pro (2023–2026), Pro mini v12.7.0+, SHS | **Yes** |
| LED ring | Homey Pro (Early 2019) and older | **No** |
| `platformLocalRequiredFeatures` | Allowed | **Illegal** together with `"cloud"` |
| Publishing requirement | Free, any developer account | **Homey Verified Developer subscription**, official integrations only |
| Required validation level | `publish` | `verified` (adds `platforms`, `connectivity`, `support`) |
| Local development | `homey app run` (Docker; `--remote` on Pro 2016–2019) | `homey app run` in Docker, connected to Homey Cloud |

---

## Homey Self-Hosted Server

Homey Self-Hosted Server (Homey SHS) is a **`local` platform**, not a cloud platform: it reports
`this.homey.platform === 'local'` and `platformVersion === 2`, and an app targets it with
`"platforms": ["local"]` — the same value as Homey Pro. Documented specifics:

- The Homey CLI needs **Docker** for Homey Cloud, Homey Pro **and Homey Self-Hosted Server**.
- Supports the **`ble-advertisements`** feature (alongside Homey Pro Early 2023, Pro mini and Pro 2026).
- Supports **Z-Wave and Zigbee OTA firmware updates** (Homey firmware v13.2.0+, Mobile App v9.10.0+).
- The Homey Pro **Z-Wave User Manual** applies to Homey Pro (Early 2023) and newer, Homey Pro mini,
  Homey Self-Hosted Server and Homey Cloud.
- **Videos** are served as WebRTC to the frontend as of Homey Pro (2023–2026), Homey Pro mini and Homey
  Self-Hosted Server v12.12.0; opt out with `disableWebRTCProxy: true` when creating the video.

Nothing on this page's *restriction* lists applies to Homey SHS — treat it as Homey Pro.

---

## Gotchas

- **Publishing for Cloud needs an Athom-approved (Verified Developer) account.** Without it,
  `homey app publish` is rejected with *"Your account is not eligible to publish apps for Homey Cloud."*
  Keep `"platforms": ["local"]` as the default and only add `"cloud"` when the user actually holds the
  subscription and is the brand (or commissioned by it).
- **`platforms` is independent of `connectivity`.** Integrating a vendor's cloud API does *not* require
  `"platforms": ["cloud"]`. This is the single most common mix-up.
- **Adding `"cloud"` to the app manifest is not enough.** Flow cards and drivers each need their own
  `platforms`; a driver without `platforms` is silently local-only, and the CLI only *warns*.
- **A `cloud` driver may not declare `lan`, `matter` or `rf868` connectivity** — `homey app validate`
  fails outright.
- **`platformLocalRequiredFeatures` + `"cloud"` is a hard error**, not a warning.
- **An unhandled promise rejection is a crash on Cloud.** Treat `.catch(this.error)` on every
  fire-and-forget SDK call as mandatory, not as style.
- **Plain `setInterval` leaks per tenant.** On Pro the process dies and hides the bug; on Cloud the
  timer keeps firing against a destroyed instance. Same for listeners you attached to shared objects —
  detach them in `onUninit()`.
- **Absolute paths silently read the wrong file on Cloud** because `/` is the Linux root there and the
  app directory on Pro. Always `./…` or `path.join(__dirname, …)`.
- **Custom App Settings pages are not an option on Cloud**, so credential updates must go through a
  `repair` view — otherwise the user's only recovery is deleting and re-adding the device, which breaks
  every Flow that referenced it.
- **`homey app validate` defaults to `--level publish`.** If your account is a verified developer the
  CLI applies `verified` by default; if it is not, run `--level verified` explicitly before shipping a
  Cloud-targeted app so `platforms`, `connectivity` and `support` are actually checked.
- **A fresh Compose-only repo has no `/app.json`** until the first `homey app run` / `build` / `validate`
  generates it — expect `ENOENT` from anything that reads it too early.
- **"Tools"-style apps are a dead end on Cloud.** Without `homey:manager:api` and app-to-app permissions
  they cannot work, and the review guidelines reject apps that only add value in combination with other
  apps.
- **Widgets silently do nothing on Cloud.** If the app is `["local", "cloud"]` and ships widgets, Cloud
  users just do not get them — document it rather than assuming parity.
- **Node 22 on Cloud requires a re-publish.** Cloud apps migrate to Node.js 22 only after you publish a
  new version after December 2nd, 2025; previously published versions keep the old Node.js version.

---

## Sources

- <https://apps.developer.homey.app/guides/homey-cloud>
- <https://apps.developer.homey.app/app-store/verified-developer>
- <https://apps.developer.homey.app/app-store/publishing>
- <https://apps.developer.homey.app/app-store/guidelines>
- <https://apps.developer.homey.app/the-basics/app>
- <https://apps.developer.homey.app/the-basics/app/manifest>
- <https://apps.developer.homey.app/the-basics/app/permissions>
- <https://apps.developer.homey.app/the-basics/app/persistent-storage>
- <https://apps.developer.homey.app/the-basics/devices>
- <https://apps.developer.homey.app/the-basics/devices/energy>
- <https://apps.developer.homey.app/the-basics/widgets>
- <https://apps.developer.homey.app/the-basics/getting-started>
- <https://apps.developer.homey.app/the-basics/getting-started/homey-cli>
- <https://apps.developer.homey.app/advanced/web-api>
- <https://apps.developer.homey.app/advanced/custom-views/app-settings>
- <https://apps.developer.homey.app/advanced/custom-views/html-and-css-styling>
- <https://apps.developer.homey.app/advanced/videos>
- <https://apps.developer.homey.app/advanced/ledring>
- <https://apps.developer.homey.app/wireless/wi-fi>
- <https://apps.developer.homey.app/wireless/wi-fi/discovery>
- <https://apps.developer.homey.app/wireless/bluetooth>
- <https://apps.developer.homey.app/wireless/matter>
- <https://apps.developer.homey.app/wireless/z-wave>
- <https://apps.developer.homey.app/wireless/z-wave/z-wave-firmware-updates>
- <https://apps.developer.homey.app/wireless/zigbee/zigbee-firmware-updates>
- <https://apps-sdk-v3.developer.homey.app/Homey.html>
- <https://apps-sdk-v3.developer.homey.app/ManagerCloud.html>
- <https://apps-sdk-v3.developer.homey.app/ManagerBLE.html>
- `homey-lib` `lib/App/index.js` (validator) and the app-manifest JSON schema
