---
name: homey-app
description: >
  Build, scaffold, debug, test, and publish apps for the Homey smart home platform with the Homey
  Apps SDK v3 (Node.js or Python runtime). Use this skill whenever the user mentions Homey, Homey
  Pro, Homey Cloud, Homey Bridge, Homey Self-Hosted Server, Homey app development, the Homey CLI
  (`homey app …`), Homey Compose, Flow cards, drivers, devices, capabilities, Homey Energy, dashboard
  widgets, pairing/repair views, app settings pages, the Homey App Store or its guidelines, or app
  certification. Also trigger for Homey wireless integrations — Wi-Fi/LAN, mDNS/SSDP discovery,
  Z-Wave, Zigbee, 433/868 MHz RF, Infrared, Bluetooth LE, Matter/Thread — and for cloud
  integrations via OAuth2 or webhooks. Even if the user just says "I want to make a Homey app" or
  names a device or service they want to control with Homey, use this skill.
---

# Homey Apps SDK — Skill Guide

A Homey app is a **Node.js or Python bundle** that runs on Homey — locally on Homey Pro / Homey
Self-Hosted Server, or in a container on Homey Cloud. Apps add **Devices**, **Flow cards**,
**Widgets**, **Energy** data and more. Distribution is through the Homey App Store.

Official docs: <https://apps.developer.homey.app> · JS API: <https://apps-sdk-v3.developer.homey.app>
· Python API: <https://python-apps-sdk-v3.developer.homey.app> · Developer Tools:
<https://tools.developer.homey.app>

## Step 1 — Route to the right reference

`references/` holds the deep material. **Read the files relevant to the task before writing code**;
they contain the complete tables (capabilities, guidelines, CLI flags, CSS variables) that you must
not reconstruct from memory.

| If the task involves… | Read |
| --- | --- |
| Manifest fields, app lifecycle, Homey Compose, i18n, permissions, storage | `references/app-and-manifest.md` |
| Driver/Device classes, lifecycle hooks, device settings, device classes | `references/drivers-and-devices.md` |
| Which capability to use, capability options, sub-capabilities, custom capabilities | `references/capabilities.md` |
| Power/energy, Homey Energy, batteries, solar, EV chargers, meters | `references/energy.md` |
| Pairing, repair, list_devices, login views, custom pair HTML | `references/pairing.md` |
| App settings page, custom HTML views, Homey CSS styleguide | `references/custom-views-and-settings.md` |
| Flow triggers/conditions/actions, arguments, autocomplete, tokens | `references/flow-cards.md` |
| Dashboard widgets, widget settings, widget styling, previews | `references/widgets.md` |
| Wi-Fi/LAN devices, mDNS-SD / SSDP / MAC discovery | `references/wireless-lan-discovery.md` |
| Z-Wave drivers, command classes, OTA firmware | `references/wireless-zwave.md` |
| Zigbee drivers, clusters, OTA firmware | `references/wireless-zigbee.md` |
| 433/868 MHz RF signals, Infrared remotes | `references/wireless-rf-infrared.md` |
| Bluetooth LE, Matter, Thread | `references/wireless-ble-matter.md` |
| OAuth2 login, cloud APIs, webhooks | `references/cloud-oauth-webhooks.md` |
| `api.js`, app-to-app calls, realtime events | `references/web-api-and-realtime.md` |
| Images, cameras, videos, LED ring, Insights, notifications, misc managers | `references/advanced-features.md` |
| Homey CLI commands, validation, debugging, TypeScript, ESM | `references/cli-and-tooling.md` |
| Writing the app in Python | `references/python-apps.md` |
| Official Athom libraries, example apps, GitHub Actions CI/CD, ESLint, Sentry | `references/ecosystem-and-ci.md` |
| App Store guidelines, assets, certification, publishing, updates | `references/publishing.md` |
| SDK v2→v3, Node 22, compatibility ranges, deprecating things safely | `references/migration-and-breaking-changes.md` |
| Homey Cloud restrictions and multi-tenancy | `references/homey-cloud.md` |
| "Does method X exist? What is its exact signature?" | `references/sdk-api-index.md` |

## Step 2 — Consult the live docs when unsure

Do not guess API names. Two zero-setup ways to check the current official docs:

1. **Any docs page is available as Markdown** by appending `.md` to its URL, e.g.
   `https://apps.developer.homey.app/the-basics/devices/capabilities.md`. The full page index is at
   `https://apps.developer.homey.app/llms.txt`.
2. **A documentation MCP server** at `https://apps.developer.homey.app/~gitbook/mcp` exposes
   `searchDocumentation`, `getPage` and `sendFeedback`. If it is not wired into the session, call it
   over plain HTTP:

```bash
curl -s -X POST https://apps.developer.homey.app/~gitbook/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchDocumentation","arguments":{"query":"energy cumulative"}}}'
```

## Platforms & runtimes

| | Homey Pro / Homey Self-Hosted Server | Homey Cloud (Bridge) |
| --- | --- | --- |
| `platforms` value | `"local"` | `"cloud"` |
| Local wireless (Wi-Fi/LAN, Z-Wave, Zigbee, 433 MHz, IR, BLE) | yes | **no** — cloud-connected devices only |
| App Web API (`api.js`), app-to-app, `homey:manager:api` | yes | **no** |
| Publishing requirement | normal developer account | **Homey Verified Developer subscription** |

- `"sdk": 3` always. `"runtime": "nodejs"` (default) or `"python"`.
- Node.js apps run **Node 22** (Homey v12.9.0+). Python apps run **Python 3.14** and need
  `"pythonVersion"` + `"pythonDependencies"` in the manifest and `"compatibility": ">=13.0.0"`.
- The **Homey CLI itself needs Node.js v24+**, and **Docker** for Homey Cloud, Homey Pro (Early 2023+)
  and Homey Self-Hosted Server targets. Homey Pro (2016–2019) has no Docker path — the CLI runs the
  app remotely (`--remote`) instead.
- Default to `"platforms": ["local"]` unless the user has a Verified Developer subscription.

## Project structure (Homey Compose)

```
com.example.myapp/
├─ .homeycompose/
│  ├─ app.json                          # Core manifest properties
│  ├─ capabilities/<id>.json            # Custom capabilities
│  ├─ screensavers/<id>.json            # LED ring screensavers
│  ├─ signals/{433,868,ir}/<id>.json    # RF / IR signal definitions
│  ├─ flow/{triggers,conditions,actions}/<id>.json   # App-level Flow cards
│  ├─ discovery/<id>.json               # mDNS-SD / SSDP / MAC strategies
│  ├─ drivers/
│  │  ├─ templates/<template_id>.json   # Shared driver props ($extends)
│  │  ├─ settings/<setting_id>.json     # Shared device settings
│  │  └─ flow/{triggers,conditions,actions}/<id>.json  # Shared driver Flow cards
│  └─ locales/<locale>.json             # App-level translations
├─ assets/
│  ├─ icon.svg
│  └─ images/{small.png,large.png,xlarge.png}     # 250x175 / 500x350 / 1000x700
├─ drivers/<driver_id>/
│  ├─ assets/icon.svg + assets/images/{small,large,xlarge}.png   # 75x75 / 500x500 / 1000x1000
│  ├─ driver.js  device.js              # (driver.py / device.py for Python)
│  ├─ driver.compose.json               # Driver manifest
│  ├─ driver.flow.compose.json          # Driver-scoped Flow cards (optional)
│  ├─ driver.settings.compose.json      # Device settings (optional)
│  └─ pair/*.html  repair/*.html        # Custom pairing/repair views (optional)
├─ widgets/<widget_id>/
│  ├─ public/index.html                 # Widget frontend
│  ├─ api.js                            # Widget API handlers
│  ├─ widget.compose.json
│  └─ preview-light.png  preview-dark.png
├─ locales/{en,nl,…}.json
├─ settings/index.html                  # App settings page (optional)
├─ api.js                               # App Web API (optional, not on Homey Cloud)
├─ app.js                               # (app.py for Python)
├─ env.json                             # Secrets — gitignore this
├─ .homeychangelog.json                 # Per-version changelog
├─ .homeyreview.md                      # Extra instructions for `homey app review` (optional)
├─ README.txt                           # App Store long description (plain text)
└─ .homeyignore                         # Files excluded from the build
```

`app.json` in the project root is **generated** — never hand-edit it.

## Standard workflow

1. **Classify the integration**: LAN device (Wi-Fi + mDNS/SSDP/MAC) · cloud API (OAuth2 / webhooks /
   polling) · wireless protocol (Z-Wave, Zigbee, 433 MHz, IR, BLE, Matter) · virtual/no device.
2. **Read the matching reference file(s)** from the table above.
3. **Scaffold**: `homey app create`, then `homey app driver create` / `homey app flow create` /
   `homey app widget create` / `homey app discovery create`. Prefer the CLI generators over
   hand-writing compose files — they produce the exact current schema.
4. **Implement** with SDK v3 patterns (async/await, `this.homey.*`).
5. **Validate**: `homey app validate --level debug` while developing,
   `--level publish` before shipping, `--level verified` for Homey Cloud / Verified Developers.
6. **Run**: `homey app run` (uninstalls on Ctrl+C), `homey app run --clean` to wipe paired devices,
   `homey app install` to leave it installed.
7. **Pre-flight the store review**: `homey app review` runs an AI check against the App Store
   Guidelines and returns `approve` / `request_changes` / `reject` with blockers. Run it before
   `homey app publish`.
8. **Ship**: `homey app version <patch|minor|major> --changelog.en "…"` then `homey app publish`,
   then submit for certification in Developer Tools.

## Minimal scaffolds

### `/.homeycompose/app.json`

```json
{
  "id": "com.example.myapp",
  "version": "1.0.0",
  "compatibility": ">=12.0.0",
  "sdk": 3,
  "platforms": ["local"],
  "name": { "en": "My App" },
  "description": { "en": "Adds support for Example devices." },
  "category": "tools",
  "brandColor": "#1F6FEB",
  "images": {
    "small": "/assets/images/small.png",
    "large": "/assets/images/large.png",
    "xlarge": "/assets/images/xlarge.png"
  },
  "author": { "name": "Jane Doe", "email": "jane@example.com" }
}
```

Categories: `lights`, `video`, `music`, `appliances`, `security`, `climate`, `tools`, `internet`,
`localization`, `energy`.

### `/app.js`

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

### `/drivers/<id>/driver.js`

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {
  async onInit() {
    this.log('MyDriver has been initialized');
  }

  async onPairListDevices() {
    return [
      {
        name: 'Example Device',
        data: { id: 'aa:bb:cc:dd:ee:ff' }, // immutable & unique
        store: { address: '192.168.1.42' }, // changing properties go here
      },
    ];
  }
}

module.exports = MyDriver;
```

### `/drivers/<id>/device.js`

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {
  async onInit() {
    this.registerCapabilityListener('onoff', async (value) => {
      await this.setDeviceState(value);
    });
  }

  async onAdded() {}

  async onSettings({ oldSettings, newSettings, changedKeys }) {
    // read new values from newSettings — getSetting() still returns the OLD value here
  }

  async onRenamed(name) {}

  async onDeleted() {}

  async onUninit() {}
}

module.exports = MyDevice;
```

### `/drivers/<id>/driver.compose.json`

```json
{
  "name": { "en": "My Device" },
  "class": "socket",
  "capabilities": ["onoff", "measure_power"],
  "platforms": ["local"],
  "connectivity": ["lan"],
  "images": {
    "small": "/drivers/my_device/assets/images/small.png",
    "large": "/drivers/my_device/assets/images/large.png",
    "xlarge": "/drivers/my_device/assets/images/xlarge.png"
  },
  "pair": [
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "add_devices" } },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

## Critical rules

1. **Never edit `/app.json`** — Homey Compose generates it from `.homeycompose/` + `*.compose.json`.
   A fresh Compose-only repo still needs the file to exist: run `homey app build` (or
   `run`/`validate`) once to generate it. `ENOENT: no such file or directory, open 'app.json'` means
   you skipped that step.
2. **Choose the app `id` before the first publish — it is effectively permanent.** Changing it later
   creates a *new* App Store listing and loses all installs and reviews. Reverse-domain notation.
   Do not pass your app off as Athom's (no `com.athom.*`, no Homey/Athom branding as the app's
   identity).
3. **In `onSettings({ oldSettings, newSettings, changedKeys })`, `this.getSetting()` still returns
   the OLD value** — settings persist only after the handler resolves. Read from `newSettings`.
4. **`device.data` must be immutable and globally unique** — MAC address, serial number, Z-Wave/Zigbee
   node id. **Never an IP address.** Changing values belong in the device store or settings.
5. **Use `this.homey.setTimeout` / `setInterval` / `clearInterval`**, not the globals — Homey clears
   them on app destroy. Leaked timers break Homey Cloud multi-tenancy.
6. **Never override the constructor** of `Homey.App` / `Driver` / `Device` — use `onInit()`.
7. **Always handle promise rejections.** Unhandled rejections crash the app (fatal on Homey Cloud).
   Use `.catch(this.error)` for fire-and-forget.
8. **Log with `this.log()` / `this.error()`**, never `console.log`.
9. **Access managers through `this.homey.*`** (`this.homey.flow`, `.settings`, `.drivers`,
   `.images`, `.cloud`, `.insights`, `.dashboards`, …). From a Device/Driver, `this.homey.app` is the
   App instance and `this.driver` is its Driver.
10. **Insights is write-only at runtime** — an app can create logs and entries but cannot read a
    capability's history back. Keep your own capped buffer if you need history.
11. **`env.json` holds secrets** (uppercase keys, string values), read via `Homey.env.NAME`. Keep it
    out of version control; it ships inside the app bundle, so it is not a security boundary.
12. **Adding a capability to already-paired devices requires a migration** — guard `addCapability()`
    behind a store flag; never call it unconditionally on every `onInit`.
13. **Register Flow cards once**, in `App.onInit()` or `Driver.onInit()` — not per device.
14. **Widgets need `compatibility >=12.3.0`** and Homey 2023+ hardware.
15. **`homey app validate --level publish` is not certification.** Athom's human review rejects
    things the validator never checks (icons, images, naming, Flow card titles). Read
    `references/publishing.md` before submitting, and run `homey app review`.

## Common patterns

### Polling a cloud API

```javascript
async onInit() {
  this.pollInterval = this.homey.setInterval(() => {
    this.poll().catch(this.error);
  }, 30_000);
}

async onUninit() {
  this.homey.clearInterval(this.pollInterval);
}
```

### Device → Homey (report state)

```javascript
await this.setCapabilityValue('measure_temperature', 22.5).catch(this.error);
```

### Homey → device (accept a command)

```javascript
this.registerCapabilityListener('target_temperature', async (value, opts) => {
  await this.api.setTemperature(value);
});
```

### Firing a device Flow trigger

```javascript
// Driver.onInit()
this.myTrigger = this.homey.flow.getDeviceTriggerCard('my_event');

// Device
await this.driver.myTrigger.trigger(this, { token_key: 'value' }, {});
```

### Availability & warnings

```javascript
await this.setUnavailable(this.homey.__('errors.unreachable'));
await this.setAvailable();
await this.setWarning('Battery low');
await this.unsetWarning();
```

---

Everything above is a summary. For complete tables, schemas and edge cases, open the reference file
listed in the routing table — and when the docs may have changed, fetch the page as Markdown or ask
the documentation MCP server.
