# Homey Ecosystem & CI/CD

Everything outside the core SDK: the official Athom npm packages, the ESLint plugin, Sentry crash
reporting via `homey-log`, the four official GitHub Actions and copy-paste workflows, the official
example apps, and where to file bugs or request assets.

Related: `references/cli-and-tooling.md` (every CLI command), `references/publishing.md` (App Store
guidelines and certification), `references/web-api-and-realtime.md` (`homey-api` in depth),
`references/wireless-zwave.md` / `references/wireless-zigbee.md` / `references/wireless-rf-infrared.md`
(driver library usage), `references/cloud-oauth-webhooks.md` (`homey-oauth2app` in depth).

---

## 1. Official npm packages

All packages are published by Athom B.V. under the `athombv` GitHub organisation.

| Package | Install | What it is | Docs |
| --- | --- | --- | --- |
| `homey` | `npm install --global homey` | The Homey CLI ("Command-line interface and type declarations for Homey Apps"). Repo: `athombv/node-homey`. Requires Node `>=22`. Exposes the `homey` binary. | <https://apps.developer.homey.app/the-basics/getting-started/homey-cli> |
| `homey-zwavedriver` | `npm install homey-zwavedriver` | Maps Homey capabilities to Z-Wave Command Classes. Extend `ZwaveDevice` (or `ZwaveLightDevice` for lights). Repo: `athombv/node-homey-zwavedriver`. Requires SDK v3. | <https://athombv.github.io/node-homey-zwavedriver> |
| `homey-zigbeedriver` | `npm install --save homey-zigbeedriver zigbee-clusters` | Maps Homey capabilities to Zigbee endpoints/clusters. Extend `ZigBeeDevice` (or `ZigBeeLightDevice`). Repo: `athombv/node-homey-zigbeedriver`. Requires SDK v3. | <https://athombv.github.io/node-homey-zigbeedriver> |
| `zigbee-clusters` | `npm install zigbee-clusters` | The ZCL (Zigbee Cluster Library) implementation `homey-zigbeedriver` is built on. Exports `CLUSTER`, `BoundCluster`, `debug`, `ZCLNode`. Repo: `athombv/node-zigbee-clusters`. **A `peerDependency` of `homey-zigbeedriver`** — install a compatible version alongside it. | <https://athombv.github.io/node-zigbee-clusters/> |
| `homey-rfdriver` | `npm install homey-rfdriver` | RF drivers: 433 MHz, 868 MHz and Infrared. Exports `RFSignal`, `RFDriver`, `RFDevice`, `RFError`, `RFUtil`. Repo: `athombv/node-homey-rfdriver`. Requires SDK v3. | <https://athombv.github.io/node-homey-rfdriver> |
| `homey-oauth2app` | `npm install homey-oauth2app` | Does the heavy lifting for apps that talk to an OAuth2 Web API. Exports `OAuth2App`, `OAuth2Client`, `OAuth2Driver`, `OAuth2Device`, `OAuth2Token`, `OAuth2Error`. Repo: `athombv/node-homey-oauth2app`. Requires SDK v3. | <https://athombv.github.io/node-homey-oauth2app/> |
| `homey-log` | `npm install --save homey-log` | Sends events (including crashes) to [Sentry](http://sentry.io/). Exports `{ Log }`. Repo: `athombv/node-homey-log`. v2.0.0+ is SDK v3 only. | <https://athombv.github.io/node-homey-log/> |
| `homey-api` | `npm install homey-api` | The Homey Web API client (`HomeyAPI`). Used from inside an app (`createAppAPI`) or from Node/browser (`createLocalAPI`). Repo: `athombv/node-homey-api`. The Homey CLI itself depends on it. | <https://athombv.github.io/node-homey-api/> |
| `homey-lib` | `npm install homey-lib` | "Shared Library for Homey" — the source of truth for capabilities, device classes, categories, permissions, media codecs, energy data and app/capability/signal validation. Used by the CLI validator and Developer Tools. Repo: `athombv/node-homey-lib`. | <https://github.com/athombv/node-homey-lib> |
| `eslint-plugin-homey-app` | `npm install --save-dev eslint-plugin-homey-app` | ESLint rules that enforce Homey App best practices (`global-timers`, `homey-log`). Requires ESLint v10 + flat config; use `@1` for legacy config. | see §3 |
| `homey-apps-sdk-v3-types` | `npm install @types/homey@npm:homey-apps-sdk-v3-types` | TypeScript declarations for the Apps SDK v3, aliased into `@types/homey`. Repo: `athombv/node-homey-apps-sdk-v3-types`. Installed automatically by `homey app add-types`. | <https://github.com/athombv/node-homey-apps-sdk-v3-types> |

### Archived / do not use

| Package | Status |
| --- | --- |
| `homey-meshdriver` (repo `athombv/node-homey-meshdriver`) | **ARCHIVED. SDK v2 only.** It is the predecessor of `homey-zwavedriver` and `homey-zigbeedriver`. Do not use it in new apps. Both replacements publish a *non-exhaustive* list of deprecations and breaking changes relative to it — see §1.2. |

### 1.1 `require('homey')` is not an npm dependency

`homey app create` scaffolds a `package.json` that looks like this — note there is no `homey` entry
in `dependencies`:

```json
{
  "name": "com.example.myapp",
  "version": "1.0.0",
  "main": "app.js",
  "scripts": {
    "lint": "eslint --ext .js,.ts --ignore-path .gitignore ."
  }
}
```

The `lint` script is only written when you accept the CLI's "Use ESLint?" prompt (it defaults to
**yes**); decline it and `scripts` is left empty. For a **TypeScript** app the CLI drops `main`
entirely and writes `"build": "tsc"` instead. Everything else — including the absence of a `homey`
entry — is the same.

The `homey` module that apps `require('homey')` is supplied by the Homey runtime. The npm package
named `homey` is the **CLI**, installed globally. Only add real runtime libraries
(`homey-zwavedriver`, `homey-oauth2app`, …) to `dependencies`.

`homey app create` also writes a `/.gitignore` containing exactly:

```
/env.json
/node_modules/
/.homeybuild/
```

### 1.2 MeshDriver → ZwaveDriver / ZigBeeDriver migration notes

Non-exhaustive lists of breaking changes relative to `homey-meshdriver`, straight from the library
READMEs.

**`homey-zwavedriver`:**

| Old (meshdriver) | New |
| --- | --- |
| `MeshDevice` | `ZwaveDevice` |
| `onMeshInit()` | `onNodeInit()` (old name deprecated) |
| `calculateZwaveDimDuration` | `calculateDimDuration` (old name deprecated) |
| `ZwaveMeteringDevice`, `ZwaveLockDevice` | removed |

**`homey-zigbeedriver`:**

| Old (meshdriver) | New |
| --- | --- |
| `MeshDevice` | `ZigBeeDevice` |
| `onMeshInit()` | `onNodeInit()` (old name deprecated) |
| `this.node.on('online')` | `this.onEndDeviceAnnounce()` |
| `getClusterEndpoint` threw / other | returns `null` if not found |
| `cluster: 'genOnOff'` (string) | `CLUSTER.ON_OFF` object from `const { CLUSTER } = require('zigbee-clusters');` |
| `registerReportListener` | `BoundCluster` implementation (old name deprecated) |
| `registerAttrReportListener` | `configureAttributeReporting` (old name deprecated) |
| `calculateZigbeeDimDuration` | `calculateLevelControlTransitionTime` |
| — | `calculateColorControlTransitionTime` added for the `colorControl` cluster |
| `ZigBeeXYLightDevice` | removed — `ZigBeeLightDevice` detects hue/saturation vs XY-only |

`homey-zigbeedriver` 2.0.0 breaking change: **`windowcoverings_set` values are no longer inverted.**

---

## 2. Which library for which integration

| The device / service talks over… | Reach for | Also read |
| --- | --- | --- |
| Z-Wave | `homey-zwavedriver` | `references/wireless-zwave.md` |
| Zigbee | `homey-zigbeedriver` (+ `zigbee-clusters` for advanced clusters, bound clusters, custom clusters) | `references/wireless-zigbee.md` |
| 433 MHz / 868 MHz RF | `homey-rfdriver` — needs the `homey:wireless:433` permission | `references/wireless-rf-infrared.md` |
| Infrared | `homey-rfdriver` — needs the `homey:wireless:ir` permission | `references/wireless-rf-infrared.md` |
| A cloud API with OAuth2 | `homey-oauth2app` | `references/cloud-oauth-webhooks.md` |
| A cloud API with an API key / no OAuth2 | plain `fetch`/HTTP in `device.js`; no Athom library needed | `references/drivers-and-devices.md` |
| Homey itself (reading devices, flows, zones from inside your app or a widget) | `homey-api` | `references/web-api-and-realtime.md` |
| LAN device found via mDNS-SD / SSDP / MAC | SDK discovery strategies; no extra package | `references/wireless-lan-discovery.md` |
| Nothing — you need capability/device-class metadata at build time | `homey-lib` | §5 |

---

## 3. `eslint-plugin-homey-app`

ESLint rules that enforce best practices for Homey Apps.

### Install

```bash
npm install --save-dev eslint-plugin-homey-app
```

### Flat config (ESLint v10)

```js
// eslint.config.js
const homeyApp = require('eslint-plugin-homey-app');

module.exports = [
  homeyApp.configs.recommended,
];
```

### Legacy config

The plugin requires **ESLint v10 and flat config**. For legacy (`.eslintrc*`) config support, install
the v1 line:

```bash
npm install --save-dev eslint-plugin-homey-app@1
```

### Rules

| Rule | What it catches |
| --- | --- |
| `homey-app/global-timers` | Warns when using global `setTimeout` or `setInterval` instead of `this.homey.setTimeout` / `this.homey.setInterval`. Global timers are **not** automatically cleared when the app is destroyed. |
| `homey-app/homey-log` | Warns when using `console.log` or `console.error` instead of `this.log` / `this.error`. |

Both rules encode hard SDK v3 requirements, so treat them as errors in review even when they only
warn:

```js
'use strict';

const Homey = require('homey');

module.exports = class MyApp extends Homey.App {

  async onInit() {
    // BAD — flagged by homey-app/global-timers, survives app destruction
    // setInterval(() => this.poll(), 60000);

    // GOOD — cleared automatically when the app is destroyed
    this.pollInterval = this.homey.setInterval(() => {
      this.poll().catch(this.error);
    }, 60000);

    // BAD — flagged by homey-app/homey-log
    // console.log('MyApp has been initialized');

    // GOOD
    this.log('MyApp has been initialized');
  }

  async poll() {
    // ...
  }

  async onUninit() {
    this.homey.clearInterval(this.pollInterval);
  }

};
```

### The older `eslint-config-athom` path

`homey app create` offers to set up ESLint. When accepted, the CLI installs `eslint@^7.32.0` and
`eslint-config-athom` (dev dependencies), adds a `lint` script, and writes:

```json
// .eslintrc.json
{
  "extends": "athom/homey-app"
}
```

```json
// package.json (excerpt)
{
  "scripts": {
    "lint": "eslint --ext .js,.ts --ignore-path .gitignore ."
  }
}
```

This is the **legacy** ESLint 7 setup, a style/config preset — it is a different thing from
`eslint-plugin-homey-app`, which is a rules plugin on ESLint v10 flat config. New apps that are on
ESLint v10 should use `eslint-plugin-homey-app`; the two can coexist only if the ESLint major version
matches what each requires.

---

## 4. `homey-log` — crash reporting to Sentry

`homey-log` sends events from a Homey App to [Sentry](http://sentry.io/). Version 2.0.0+ is SDK v3
only and requires the `{ homey }` constructor form shown below.

### Install

```bash
npm install --save homey-log
```

### `env.json`

Put the Sentry DSN in the app's `/env.json`. Setting `HOMEY_LOG_FORCE` to `"1"` also sends logs
during development.

```json
{
  "HOMEY_LOG_FORCE": "0",
  "HOMEY_LOG_URL": "https://foo:bar@sentry.io/123456"
}
```

| Key | Type | Meaning |
| --- | --- | --- |
| `HOMEY_LOG_URL` | string | The Sentry DSN to send events to. |
| `HOMEY_LOG_FORCE` | string (`"0"` / `"1"`) | `"1"` sends logs to Sentry *also* during development. |

`/env.json` values must be uppercase keys with string values, and are readable anywhere in the app as
`Homey.env.HOMEY_LOG_URL` etc. The docs state `/env.json` is typically used for secrets and should be
added to `/.gitignore`. Keep that in mind for CI: anything the build genuinely needs at publish time
must be present in the checked-out tree — verify with `homey app build` before wiring up the publish
workflow. See `references/app-and-manifest.md` for the full `/env.json` behaviour.

### `app.js`

```js
'use strict';

const Homey = require('homey');
const { Log } = require('homey-log');

module.exports = class MyApp extends Homey.App {

  async onInit() {
    this.homeyLog = new Log({ homey: this.homey });
    this.log('MyApp has been initialized');
  }

};
```

### Behaviour

* When the app crashes due to an **`uncaughtException`** or **`unhandledRejection`**, the event is
  sent to Sentry automatically — no extra wiring needed.
* When running the app with **`homey app run`, events are not sent to Sentry** (unless
  `HOMEY_LOG_FORCE` is `"1"`).

---

## 5. `homey-lib` — capability / device-class / validation metadata

`homey-lib` contains shared code between Homey, Homey Apps, the Homey CLI, Homey Developer Tools and
others. It can, among other things:

* Validate a Homey App
* Validate a Capability
* Validate a Signal
* Return supported device classes
* Return supported device capabilities
* Return supported media codecs
* Return supported app permissions
* Return supported app store categories

Useful in scripts and codegen (for example: "list every valid capability id" or "check this device
class exists") rather than inside a shipped app.

```js
'use strict';

const HomeyLib = require('homey-lib');
const { App, Energy, Media } = require('homey-lib');

// Capabilities and device classes
console.log('Device Classes:', Object.keys(HomeyLib.getDeviceClasses()));
console.log('Capabilities:', Object.keys(HomeyLib.getCapabilities()));
console.log('Has Capability onoff:', HomeyLib.hasCapability('onoff'));

// App metadata
console.log('Permissions:', App.getPermissions());
console.log('Categories:', App.getCategories());
console.log('Locales:', App.getLocales());

// Energy + media
console.log('Batteries:', Energy.getBatteries());
console.log('Currencies:', Energy.getCurrencies());
console.log('Codecs:', Object.keys(Media.getCodecs()));
```

### Exports

Class exports: `App`, `Capability`, `Device`, `Energy`, `Media`, `Signal`, `Util` — plus
`AIReviewer` / `AIReviewerEnums`, which are Node-only (they pull in `fs`, `child_process` and the
OpenAI/Anthropic SDKs) and back `homey app review`. In the webpack / React Native bundle they are
stripped and resolve to `undefined`, so guard before using them.

`index.js` additionally binds a flat set of convenience functions on the module root — these are the
ones to reach for in a script:

| Top-level function | Delegates to |
| --- | --- |
| `getDeviceClasses()` | `Device.getClasses()` |
| `getDeviceClass(id)` | `Device.getClass(id)` |
| `getCapabilities()` | `Capability.getCapabilities()` |
| `getCapability(id)` | `Capability.getCapability(id)` |
| `hasCapability(id)` | `Capability.hasCapability(id)` |
| `getAppLocales()` | `App.getLocales()` |
| `getAppCategories()` | `App.getCategories()` |
| `getAppPermissions()` | `App.getPermissions()` |
| `getAppBrandColor(appId)` | `App.getBrandColor(appId)` |
| `getMediaCodecs()` | `Media.getCodecs()` |
| `getCurrencies()` | `Energy.getCurrencies()` |
| `getBatteries()` | `Energy.getBatteries()` |

`App` also exposes `App.isValidBrandColor('#FFFFFF')`, used by the browser build
(`window.HomeyLib`) and by `homey-lib/react-native`.

### Validation

The three validators listed above are constructor + `async validate()` pairs. All three resolve to
`undefined` on success and **reject** with the validation error on failure — none of them return a
boolean, so wrap them in `try`/`catch`.

```js
'use strict';

const { App, Capability, Signal, getCapability } = require('homey-lib');

// new App(path) — validate({ level, debug }); level defaults to 'debug'
const app = new App('/path/to/my/app');
await app.validate({ level: 'publish', debug: true });

// new Capability(capabilityDefinition) — validate({ debug })
const capability = new Capability(getCapability('onoff'));
await capability.validate({ debug: true });

// new Signal(signalDefinition, { frequency }) — validate({ debug })
const signal = new Signal(signalDefinition, { frequency: '433' });
await signal.validate({ debug: true });
```

More runnable snippets ship in the package's own `/examples/` folder (`app.js`, `capability.js`,
`device.js`, `energy.js`, `media.js`, `browser.html`, `react-native.js`, `validate-app.js`,
`validate-capability.js`, `validate-capabilities.js`, `validate-classes.js`, `validate-signal.js`,
`validate-signal-prontohex.js`).

Translations live in `./assets/app/permissions.json`,
`./assets/capability/capabilities/<capability_id>.json` and
`./assets/device/classes/<device_class_id>.json`; the files under `./generated_locales` are generated
and must never be edited by hand.

---

## 6. TypeScript types — `homey-apps-sdk-v3-types`

Install directly:

```bash
npm install @types/homey@npm:homey-apps-sdk-v3-types
```

Or let the CLI do it:

```bash
homey app add-types
```

The CLI has **one** `addTypes` routine but two entry points, and they do different things — do not
assume the standalone command sets up TypeScript:

| Entry point | Packages installed (all as **dev** dependencies) | Files written |
| --- | --- | --- |
| `homey app add-types` (standalone command) | `@types/homey@npm:homey-apps-sdk-v3-types` only | — |
| `homey app create` answering **TypeScript** | `@types/homey@npm:homey-apps-sdk-v3-types`, `@types/node`, `@tsconfig/node16` | `tsconfig.json` |
| `homey app create` answering **JavaScript** | `@types/homey@npm:homey-apps-sdk-v3-types` only | — |

The standalone command never asks which language you use and never passes the TypeScript flag
through, so on an existing TypeScript app it installs the types and stops. `tsconfig.json`,
`@types/node` and `@tsconfig/node16` are your job in that case.

The `tsconfig.json` written by `homey app create` for a TypeScript app:

```json
{
  "extends": "@tsconfig/node16/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "outDir": ".homeybuild/"
  }
}
```

Full TypeScript/ESM setup: `references/cli-and-tooling.md`.

---

## 7. `homey-oauth2app` in one screen

Deep coverage lives in `references/cloud-oauth-webhooks.md`; this is the shape to recognise.

`/app.js`:

```javascript
const { OAuth2App } = require('homey-oauth2app');
const MyBrandOAuth2Client = require('./lib/MyBrandOAuth2Client');

module.exports = class MyBrandApp extends OAuth2App {

  static OAUTH2_CLIENT = MyBrandOAuth2Client; // Default: OAuth2Client
  static OAUTH2_DEBUG = true; // Default: false
  static OAUTH2_MULTI_SESSION = false; // Default: false
  static OAUTH2_DRIVERS = [ 'my_driver' ]; // Default: all drivers

  async onOAuth2Init() {
    // Do App logic here
  }

}
```

`/lib/MyBrandOAuth2Client.js`:

```javascript
const { OAuth2Client, OAuth2Error } = require('homey-oauth2app');
const MyBrandOAuth2Token = require('./MyBrandOAuth2Token');

module.exports = class MyBrandOAuth2Client extends OAuth2Client {

  // Required:
  static API_URL = 'https://api.mybrand.com/v1';
  static TOKEN_URL = 'https://api.mybrand.com/oauth2/token';
  static AUTHORIZATION_URL = 'https://auth.mybrand.com';
  static SCOPES = [ 'my_scope' ];

  // Optional:
  static TOKEN = MyBrandOAuth2Token; // Default: OAuth2Token
  static REDIRECT_URL = 'https://callback.athom.com/oauth2/callback'; // Default: 'https://callback.athom.com/oauth2/callback'

  async onHandleNotOK({ body }) {
      throw new OAuth2Error(body.error);
  }

  async getThings({ color }) {
    return this.get({
      path: '/things',
      query: { color },
    });
  }

}
```

`/drivers/<driver_id>/driver.js` extends `OAuth2Driver` and implements
`async onPairListDevices({ oAuth2Client })`; `/drivers/<driver_id>/device.js` extends `OAuth2Device`
and implements `async onOAuth2Init()` / `async onOAuth2Deleted()`. `driver.compose.json` uses the
`login_oauth2` pair template (and the same template in `repair`).

`OAuth2Client` works with any API following [RFC 6749](https://tools.ietf.org/html/rfc6749). **Only
overload methods starting with `on`** (e.g. `onRequestError`); overloading anything else may break in
a future release.

---

## 8. `homey-rfdriver` file layout

The library expects this shape (copy the pair views out of the module's own `/pair` folder):

```
/.homeycompose/signals/433/my_signal.json
/lib/MySignal.js                            (extends RFSignal)
/drivers/my_driver/driver.js                (extends RFDriver, static SIGNAL = MySignal)
/drivers/my_driver/device.js                (extends RFDevice, static CAPABILITIES = { ... })
/drivers/my_driver/pair/rf_receiver_learn.html
/drivers/my_driver/pair/rf_receiver_add.html
/drivers/my_driver/pair/image.svg
```

| Driver kind | Pair views to copy from the module's `/pair` | Pair step ids |
| --- | --- | --- |
| Transmitter (e.g. a remote) | `rf_transmitter_learn.html` | `rf_transmitter_learn` |
| Receiver (e.g. a socket switch) | `rf_receiver_learn.html`, `rf_receiver_add.html` | `rf_receiver_learn` → `rf_receiver_add` |
| Receiver + copy-from-remote | the receiver pair plus `rf_transmitter_learn.html` | `rf_receiver_learn` (with `copyFromRemote` option) → `rf_transmitter_learn` → `rf_receiver_add` |
| IR remote | `rf_ir_remote_learn.html`, `rf_ir_remote_add` | `rf_ir_remote_learn` → `rf_ir_remote_add` |

Transmitter drivers additionally set `"rf433": { "satelliteMode": true }` (or `"infrared"`) in
`driver.compose.json`, and `RFDevice` subclasses set `static RX_ENABLED = true`.

Full details: `references/wireless-rf-infrared.md`.

---

## 9. CI/CD with the official GitHub Actions

Four Actions are published by Athom. Each is a Docker action; pin with `@master` as Athom's own
templates do.

| Action | Marketplace name | Inputs | Outputs |
| --- | --- | --- | --- |
| `athombv/github-action-homey-app-validate` | Homey App — Validate | `level` (optional, default `publish`) — "Validation level. Can be `debug`, `publish` or `verified`." | — |
| `athombv/github-action-homey-app-version` | Homey App — Update Version | `version` (**required**) — "Version. Can be either major, minor, patch, or a semver version."<br>`changelog` (optional) — "Changelog of the new version in English." | `version` — "The new version" |
| `athombv/github-action-homey-app-publish` | Homey App — Publish | `personal_access_token` (**required**) — "The app's owner Personal Access Token. This can be found at <https://tools.developer.homey.app/me>." | `url` — "An URL to the Homey Developer Tools, where the release can be managed." |
| `athombv/github-action-homey-app-translate` | Homey App — Translate | `openai_api_key` (**required**) — "OpenAI API Key" | — |

The publishing docs page ("Automating within GitHub Actions") links only the first three — the
Translate action exists but is undocumented there:

* <https://github.com/marketplace/actions/homey-app-validate>
* <https://github.com/marketplace/actions/homey-app-update-version>
* <https://github.com/marketplace/actions/homey-app-publish>
* (Translate: repo `athombv/github-action-homey-app-translate`, no docs-page link)

### 9.1 The `HOMEY_PAT` secret

The publish Action authenticates with a **Personal Access Token**, not with `homey login`.

1. Go to <https://tools.developer.homey.app/me> and create a Personal Access Token.
2. In the GitHub repository, go to **Settings → Secrets and variables → Actions** and add a
   repository secret named **`HOMEY_PAT`** with that token as the value.
3. Reference it as `${{ secrets.HOMEY_PAT }}` in the publish step.

The token must belong to the **app's owner**. The same variable name is used by the CLI: setting the
`HOMEY_PAT` environment variable bypasses the interactive login flow for every command that talks to
Athom Cloud, which is the recommended CI/CD path (see `references/cli-and-tooling.md`).

### 9.2 CLI shortcut: `homey app add-github-workflows`

```bash
homey app add-github-workflows
```

Copies three ready-made workflows into `.github/workflows/`:

| File | Purpose |
| --- | --- |
| `homey-app-validate.yml` | Validate on `workflow_dispatch`, `push`, `pull_request` — at level `verified` |
| `homey-app-version.yml` | Manual version bump; commits, tags, and creates a GitHub Release with `gh release create --generate-notes` |
| `homey-app-publish.yml` | Publish — `workflow_dispatch` only |

After copying, the CLI prints: *"Make sure to add the HOMEY_PAT secret to your GitHub repository, the
personal access token can be found at https://tools.developer.homey.app/me."*
`homey app create` also offers to add these workflows during scaffolding.

Note the differences vs. the tag-driven pipeline in §9.3: the CLI templates validate at `verified`
level (which fails for non-verified developers whose manifest lacks `platforms`, `connectivity` and
`support`), publish only on manual dispatch, and create a GitHub Release in the version workflow.
Pick whichever fits; do not mix half of each.

### 9.3 Copy-paste pipeline (validate on push → manual bump + tag → publish on tag)

Three files. Together they give: validation on every push/PR, a manual version bump that commits and
tags `v<version>`, and a publish triggered by that tag.

**`.github/workflows/validate.yml`**

```yaml
# Validates the Homey app on every push and pull request.
# Uses the official Athom action. No secrets required.
name: Validate

on:
  push:
  pull_request:
  workflow_dispatch:

jobs:
  validate:
    name: Validate Homey App
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate (publish level)
        uses: athombv/github-action-homey-app-validate@master
        with:
          # debug | publish | verified
          level: publish
```

**`.github/workflows/update-version.yml`**

```yaml
# Bumps the app version in app.json / .homeycompose and writes the changelog,
# then commits and tags the result. Run manually from the Actions tab.
# The pushed tag (v*) triggers the Publish workflow.
name: Update Version

on:
  workflow_dispatch:
    inputs:
      version:
        type: choice
        description: Version bump
        required: true
        default: patch
        options:
          - patch
          - minor
          - major
      changelog:
        type: string
        description: Changelog (English)
        required: true

permissions:
  contents: write

jobs:
  update-version:
    name: Update Homey App Version
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update Homey App Version
        uses: athombv/github-action-homey-app-version@master
        id: update_version
        with:
          version: ${{ inputs.version }}
          changelog: ${{ inputs.changelog }}

      - name: Commit & Push
        run: |
          git config --local user.name "github-actions[bot]"
          git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A
          git commit -m "Update Homey App Version to v${{ steps.update_version.outputs.version }}"
          git tag "v${{ steps.update_version.outputs.version }}"
          git push origin HEAD --tags
```

**`.github/workflows/publish.yml`**

```yaml
# Validates and then publishes the app to the Homey App Store.
# Runs automatically when a version tag (v*) is pushed by the Update Version
# workflow, and can also be started manually.
# Requires the HOMEY_PAT repository secret (Settings > Secrets and variables >
# Actions). Create a Personal Access Token at https://tools.developer.homey.app/me
name: Publish

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  publish:
    name: Publish Homey App
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate (publish level)
        uses: athombv/github-action-homey-app-validate@master
        with:
          level: publish

      - name: Publish
        id: publish
        uses: athombv/github-action-homey-app-publish@master
        with:
          personal_access_token: ${{ secrets.HOMEY_PAT }}

      - name: Summary
        run: echo "Manage your app at ${{ steps.publish.outputs.url }}" >> $GITHUB_STEP_SUMMARY
```

Required bits, so they are not lost when editing:

* `permissions: contents: write` on the version workflow — without it the bot cannot push the commit
  or tag.
* `git push origin HEAD --tags` — pushing only the branch will not trigger the publish workflow.
* `id:` on the version and publish steps — the outputs are read as
  `steps.<id>.outputs.version` / `steps.<id>.outputs.url`.
* Verified developers should change both `level: publish` values to `level: verified`.

### 9.4 Athom's own CLI templates, verbatim

For reference, this is exactly what `homey app add-github-workflows` writes.

**`.github/workflows/homey-app-validate.yml`**

```yaml
name: Validate Homey App
on:
  workflow_dispatch:
  push:
  pull_request:

jobs:
  main:
    name: Validate Homey App
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: athombv/github-action-homey-app-validate@master
        with:
          level: verified
```

**`.github/workflows/homey-app-version.yml`**

```yaml
name: Update Homey App Version
on:
  workflow_dispatch:
    inputs:
      version:
        type: choice
        description: Version
        required: true
        default: patch
        options:
          - major
          - minor
          - patch
      changelog:
        type: string
        description: Changelog
        required: true

# Needed in order to push the commit and create a release
permissions:
  contents: write

jobs:
  main:
    name: Update Homey App Version
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update Homey App Version
        uses: athombv/github-action-homey-app-version@master
        id: update_app_version
        with:
          version: ${{ inputs.version }}
          changelog: ${{ inputs.changelog }}

      - name: Commit & Push
        run: |
          git config --local user.name "github-actions[bot]"
          git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add -A
          git commit -m "Update Homey App Version to v${{ steps.update_app_version.outputs.version }}"
          git tag "v${{ steps.update_app_version.outputs.version }}"

          git push origin HEAD --tags
          gh release create "v${{ steps.update_app_version.outputs.version }}" -t "v${{ steps.update_app_version.outputs.version }}" --notes "" --generate-notes
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GH_TOKEN: ${{ github.token }}
```

**`.github/workflows/homey-app-publish.yml`**

```yaml
name: Publish Homey App
on:
  workflow_dispatch:

jobs:
  main:
    name: Publish Homey App
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Publish Homey App
        uses: athombv/github-action-homey-app-publish@master
        id: publish
        with:
          personal_access_token: ${{ secrets.HOMEY_PAT }}

      - name: URL
        run: |
          echo "Manage your app at ${{ steps.publish.outputs.url }}." >> $GITHUB_STEP_SUMMARY
```

### 9.5 Translation in CI

`athombv/github-action-homey-app-translate` takes a single required input, `openai_api_key`. Store
the key as a repository secret and run it on demand, committing the result:

```yaml
name: Translate

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  translate:
    name: Translate Homey App
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Translate
        uses: athombv/github-action-homey-app-translate@master
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

The local equivalent is `homey app translate` (options `--languages`, `--api-key`, `--model`,
`--file`; reads `OPENAI_API_KEY` from the environment). AI translations vary in quality — always
review the diff before committing.

### 9.6 What the pipeline does and does not do

| Step | Automated by the Actions | Still manual |
| --- | --- | --- |
| Validation at `debug` / `publish` / `verified` | yes | — |
| Version bump + changelog in `app.json` / `.homeychangelog.json` | yes (`-version`) | choosing the bump type and writing the changelog text |
| Upload to the Homey App Store | yes (`-publish`) | — |
| Releasing the uploaded build to **Test** or submitting for **certification** | no | done at <https://tools.developer.homey.app> → *Apps SDK* → *My Apps* |

`homey app publish` (and the Action) submits the app as **Draft**. From the dashboard you promote it
to a *Test* version (reachable only through the Test link) or submit it for certification by Athom.
Apps that have never been released must be certified before becoming publicly available; when you
only want a Test release, **disable the "publish directly after approval" checkbox** when submitting
for certification. Full flow and guidelines: `references/publishing.md`.

### 9.7 Validation levels

| Validation level | Description |
| --- | --- |
| `debug` | Used during development. Various app manifest properties, such as `images`, `brandColor` and `category`, are optional at this validation level. |
| `publish` | Your app needs to pass this validation level to be published to the Homey App Store for Homey Pro. |
| `verified` | If you are a verified app developer your app needs to pass this validation level. This is required for Homey Cloud. Adds requirements such as `platforms`, `connectivity` and `support` in the manifest. Applied by default when logged in with a verified developer account. |

Locally:

```bash
homey app validate --level publish
homey app validate --level verified
```

---

## 10. Official Athom example apps

Real, public reference implementations in the `athombv` GitHub organisation. Point users at the one
matching their integration type instead of inventing a structure.

| Repo | What it demonstrates |
| --- | --- |
| `athombv/com.ikea.tradfri-example` | Zigbee + LAN gateway integration |
| `athombv/com.fibaro-example` | Z-Wave devices |
| `athombv/com.mipow-example` | Bluetooth LE devices |
| `athombv/nl.klikaanklikuit-example` | 433 MHz RF devices |
| `athombv/com.lg.ir-example` | Infrared devices |
| `athombv/nl.thermosmart-example` | Cloud API integration |
| `athombv/nl.eneco.toon-example` | Cloud API / thermostat |
| `athombv/io.nuki-example` | Cloud API / lock |
| `athombv/com.danalock-example` | Lock |
| `athombv/com.plugwise.adam-example` | LAN gateway / climate |
| `athombv/org.knx` | Large production app (KNX) |
| `athombv/com.smartthings` | Large production app (SmartThings cloud) |
| `athombv/com.athom.matter-bridge` | Exposes Homey Pro devices to Matter |
| `athombv/com.athom.homeyscript` | HomeyScript app |
| `athombv/homey.ink` | Dashboard using the Homey Web API |

Library-level examples shipped inside the driver modules:

| Example | Where |
| --- | --- |
| Zigbee bulb driver | `examples/exampleBulb.js` + `examples/exampleBulb.json` in `athombv/node-homey-zigbeedriver` |
| Z-Wave plug driver | `examples/fibaroplug.js` + `examples/fibaroplug.json` in `athombv/node-homey-zwavedriver` |

---

## 11. Other `athombv` repos worth knowing

| Repo | What it is |
| --- | --- |
| `athombv/node-homey` | The Homey CLI source |
| `athombv/node-homey-lib` | Shared definitions of capabilities, device classes, categories and energy — the source of truth the CLI validator and Developer Tools use |
| `athombv/node-homey-api` | The Homey Web API client (`homey-api`) |
| `athombv/node-homey-apps-sdk-v3-types` | TypeScript definitions (installed by `homey app add-types`) |
| `athombv/node-zigbee-clusters` | ZCL cluster definitions; add or extend clusters in `lib/clusters/` |
| `athombv/node-homey-meshdriver` | **ARCHIVED**, the SDK v2 predecessor of `homey-zwavedriver` / `homey-zigbeedriver`. Do not use in new apps. |

---

## 12. Reporting bugs and requesting assets

| I want to… | Where |
| --- | --- |
| Report an **Apps SDK** bug (something in `require('homey')`, drivers, pairing, widgets, the CLI's SDK behaviour) | <https://github.com/athombv/homey-apps-sdk-issues> — the official Apps SDK issue tracker |
| Report a **Web API** bug (`homey-api`, the local/cloud API surface) | <https://github.com/athombv/homey-web-api-issues> |
| Report a bug in a **specific library** | That library's own repo, e.g. `athombv/node-homey-zigbeedriver` |
| **Request a free, custom-made vector icon** for my app | <https://github.com/athombv/homey-vectors-public/issues> — open an issue with your App ID (e.g. `com.athom.myapp`). Use this when designing is not your strong suit. |
| Manage releases, PATs, webhooks, and app certification | <https://tools.developer.homey.app> |

---

## 13. Agent checklist

Before shipping an app, verify:

- [ ] `require('homey')` is **not** in `package.json` dependencies; only real libraries are.
- [ ] For Zigbee apps, `zigbee-clusters` is installed alongside `homey-zigbeedriver` at a compatible
      version (it is a `peerDependency`).
- [ ] No `homey-meshdriver` anywhere.
- [ ] No global `setTimeout` / `setInterval` — use `this.homey.setTimeout` / `this.homey.setInterval`
      (rule `homey-app/global-timers`).
- [ ] No `console.log` / `console.error` — use `this.log` / `this.error`
      (rule `homey-app/homey-log`).
- [ ] Every promise in a non-awaited position ends with `.catch(this.error)`.
- [ ] `/env.json` is in `/.gitignore`.
- [ ] If `homey-log` is used: `HOMEY_LOG_URL` is set, `Log` is constructed with `{ homey: this.homey }`.
- [ ] `.github/workflows/` contains validate + version + publish, and the `HOMEY_PAT` repository
      secret exists.
- [ ] `homey app validate --level publish` (or `verified`) passes locally.
- [ ] `homey app review` has been run against the App Store Guidelines.

---

## Sources

* <https://apps.developer.homey.app/app-store/publishing> — publishing, validation levels, "Automating within GitHub Actions"
* <https://apps.developer.homey.app/the-basics/getting-started/homey-cli> — `homey app add-github-workflows`, `homey app add-types`, `homey app translate`, `HOMEY_PAT`
* <https://apps.developer.homey.app/the-basics/app> — `/env.json`
* <https://github.com/marketplace/actions/homey-app-validate>
* <https://github.com/marketplace/actions/homey-app-update-version>
* <https://github.com/marketplace/actions/homey-app-publish>
* <https://github.com/athombv/github-action-homey-app-translate>
* <https://athombv.github.io/node-homey-zwavedriver>
* <https://athombv.github.io/node-homey-zigbeedriver>
* <https://athombv.github.io/node-zigbee-clusters/>
* <https://athombv.github.io/node-homey-rfdriver>
* <https://athombv.github.io/node-homey-oauth2app/>
* <https://athombv.github.io/node-homey-log/>
* <https://athombv.github.io/node-homey-api/>
* <https://github.com/athombv/node-homey-lib>
* <https://github.com/athombv/node-homey-apps-sdk-v3-types>
* <https://github.com/athombv/homey-apps-sdk-issues>
* <https://github.com/athombv/homey-web-api-issues>
* <https://github.com/athombv/homey-vectors-public>
* <https://tools.developer.homey.app/me> — Personal Access Tokens
