# Pairing, Repair & Unpair

Pairing is the wizard the user walks through when adding a device: a list of **views** declared in the driver
manifest (`pair`), driven from `Driver#onPair(session)` in the app. `repair` is the same machinery for an
already-paired device (`Driver#onRepair(session, device)`). Driver/Device classes live in
`references/drivers-and-devices.md`, OAuth2 specifics in `references/cloud-oauth-webhooks.md`, the Homey CSS
styleguide for custom HTML in `references/custom-views-and-settings.md`.

## Mental model

```
user selects the device to add, in the Homey app  →  your driver
        │
        ▼
Homey opens a PairSession  ───────────►  Driver#onPair(session)      (app side)
        │                                    session.setHandler(...)
        ▼
first entry of driver.pair[] is shown
        │  navigation.next / navigation.prev  ·  session.showView() / nextView() / prevView()
        │  Homey.emit(...)  ⇄  session.setHandler(...)      (view ⇄ app)
        │  session.emit(...) ⇄  Homey.on(...)
        ▼
add_devices (or Homey.createDevice()) creates the Device  →  Device#onAdded() → Device#onInit()
        │
        ▼
session closes → the `disconnect` handler fires
```

- A **view** is either a **system template** (`"template": "list_devices"`, HTML shipped by Homey) or a **custom
  view** (`/drivers/<driver_id>/pair/<view_id>.html`, no `template` key).
- Handler event names (`list_devices`, `login`, `pincode`, …) belong to the **template**, not to the view `id`.
  The docs' own example uses `"id": "list_my_devices"` with `"template": "list_devices"` and still implements
  `onPairListDevices()` / `session.setHandler("list_devices")`.
- **Homey already knows how to pair Zigbee and Z-Wave devices, so you cannot implement your own pairing for
  those.** See `references/wireless-zigbee.md` / `references/wireless-zwave.md`.

---

## 1. The `pair` and `repair` arrays

Both are arrays of view objects on the driver manifest (`/drivers/<driver_id>/driver.compose.json` → bundled into
`app.json` `drivers[]`).

```json
{
  "name": { "en": "My Driver" },
  "class": "socket",
  "capabilities": ["onoff"],
  "platforms": ["local", "cloud"],
  "connectivity": "cloud",
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "pair": [
    {
      "id": "list_my_devices",
      "template": "list_devices",
      "navigation": { "next": "add_my_devices" }
    },
    {
      "id": "add_my_devices",
      "template": "add_devices"
    }
  ],
  "repair": [
    {
      "id": "login_oauth2",
      "template": "login_oauth2"
    }
  ]
}
```

### View object schema

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | **yes** | Unique id of the view inside this array. Without `template` it must match `/drivers/<driver_id>/pair/<id>.html`. |
| `template` | string | no | A system template id (`list_devices`, `add_devices`, `login_oauth2`, `login_credentials`, `pincode`, `loading`, `done`, `choose_slave`). Omit for a custom HTML view. |
| `options` | object | no | Per-template option object, readable from the front-end with `Homey.getOptions()`. |
| `navigation` | object | no | `{ "next": "<view_id>", "prev": "<view_id>" }` — which view the *Next* / *Back* button goes to. |

The `app.json` JSON schema used by `homey app validate` (homey-lib) for `drivers[].pair`:

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id"],
    "properties": {
      "id": { "type": "string" },
      "template": { "type": "string" },
      "options": { "type": "object" },
      "navigation": {
        "type": "object",
        "properties": { "prev": { "type": "string" }, "next": { "type": "string" } }
      }
    }
  }
}
```

### Navigation

- `navigation.next` is where the *Next* button goes; `navigation.prev` adds a *Back* button. `prev` is useful with
  `login_credentials` so users can retry a failed login.
- Both ids must exist **in the same array**. `homey app validate` throws
  `drivers.<driver_id> invalid navigation.next: <id>` / `… invalid navigation.prev: <id>` otherwise.
- Navigation can also be driven from the app (`session.showView() / nextView() / prevView()`) and from the view
  (`Homey.showView() / nextView() / prevView()`).

### CLI validation rules (what `homey app validate` actually checks)

| Rule | Failure |
| --- | --- |
| `navigation.prev` / `navigation.next` point to an existing view in the same `pair` array | `drivers.<id> invalid navigation.next: <viewId>` |
| A `pair` view **without** `template` has a matching HTML file | `Filepath does not exist: drivers/<id>/pair/<viewId>.html` (case-sensitive) |
| A driver with `connectivity: ["matter"]` has no `pair` at all | `drivers.<id> invalid 'pair' configuration, Matter drivers do not support custom pairing views.` |

**Gotcha:** the schema and the validator know **only `pair`** — the word `repair` does not appear anywhere in
homey-lib. `repair` still works at runtime (it is documented on the docs site and the manifest schema does not set
`additionalProperties: false`), but **nothing validates it**: a broken `navigation` target or a missing
`/drivers/<id>/repair/<view_id>.html` passes `homey app validate` and only fails in the user's face.

**Gotcha:** `template` values are **not** validated either. A typo (`"list_device"`) validates fine and produces a
blank/broken step at runtime.

### Where the arrays live (Homey Compose)

| File | Contents |
| --- | --- |
| `/drivers/<id>/driver.compose.json` → `pair` / `repair` | Inline arrays. |
| `/drivers/<id>/driver.pair.compose.json` | The whole `pair` array, as a JSON array. |
| `/drivers/<id>/driver.repair.compose.json` | The whole `repair` array. |
| `/drivers/<id>/pair/<view_id>.html` | Custom pair view. |
| `/drivers/<id>/repair/<view_id>.html` | Custom repair view. |
| `/.homeycompose/drivers/pair/<template_id>/index.html` (+ `assets/`) | Shared custom-view template, pulled in with `"$template": "<template_id>"`. |
| `/.homeycompose/drivers/repair/<template_id>/index.html` (+ `assets/`) | Same, for repair views. |

```
com.athom.example/
├─ .homeycompose/
│  ├─ drivers/
│  │  ├─ pair/
│  │  │  └─ my_shared_view/
│  │  │     ├─ index.html          # {{assets}} is replaced with "<view_id>.assets"
│  │  │     └─ assets/             # copied to /drivers/<id>/pair/<view_id>.assets/
│  │  └─ repair/
│  │     └─ my_shared_repair_view/
│  │        └─ index.html
│  └─ locales/
│     └─ en.json
└─ drivers/
   └─ my_driver/
      ├─ driver.compose.json
      ├─ driver.pair.compose.json
      ├─ driver.repair.compose.json
      ├─ pair/
      │  └─ start.html
      └─ repair/
         └─ start.html
```

Compose behaviour, verified against the CLI's `HomeyCompose`:

- `driver.pair.compose.json` / `driver.repair.compose.json` **replace** the array wholesale — they are assigned,
  not merged. A `pair` array inherited through `$extends` is discarded when the file exists.
- `$template` on a view copies `/.homeycompose/drivers/pair/<template_id>/index.html` to
  `/drivers/<id>/pair/<view_id>.html`, replacing every `{{assets}}` with `<view_id>.assets`, and copies the
  template's `assets/` folder to `/drivers/<id>/pair/<view_id>.assets`. Unknown template id →
  `Invalid pair template for driver <id>: <templateId>`; missing/non-string `id` →
  `Invalid pair template "id" property for driver <id>: <templateId>`.
- `$pairOptions` / `$repairOptions` merge extra options into an existing view by id:

```json
{
  "$extends": ["my_template"],
  "$pairOptions": {
    "list_devices": { "singular": true },
    "pincode": { "length": 6 }
  }
}
```

  They are applied with `Object.assign` onto `view.options`, and **only when the corresponding `pair` / `repair`
  array is a non-empty array** — `$pairOptions` on a driver with no `pair` views is silently ignored.
- Every `$`-prefixed key (`$template`, `$pairOptions`, `$repairOptions`, `$extends`) is stripped recursively from
  the generated `app.json`.

### Translating view options from `/.homeycompose/locales/`

Instead of inlining translation objects in `options`, a locale file can fill them in per language. Compose writes
`options.<key>[<locale>]`:

```json
// /.homeycompose/locales/nl.json
{
  "$drivers": {
    "my_driver": {
      "pair": {
        "pincode": {
          "options": {
            "title": "Voer de pincode in",
            "hint": "De pincode staat op de achterkant van het apparaat."
          }
        }
      },
      "repair": {
        "login_credentials": {
          "options": { "title": "Log opnieuw in" }
        }
      }
    }
  }
}
```

Any option value that the docs type as a *translation object* is `{ "en": "…", "nl": "…" }` (a plain string is also
accepted when no translation is needed). See `references/app-and-manifest.md`.

---

## 2. System views

| `template` | Purpose | Options | App-side handler(s) |
| --- | --- | --- | --- |
| `list_devices` | Let the user pick from a list of found devices | `singular` | `list_devices` (or `Driver#onPairListDevices()`); may stream with `session.emit('list_devices', …)` |
| `add_devices` | Adds the selected devices to Homey | — | — (reads the previous `list_devices` selection; a custom view can fill it with `Homey.setViewStoreValue('add_devices', 'devices', […])`) |
| `login_oauth2` | OAuth2 login popup | `title`, `subtitle`, `hint`, `button` | emit `url`, then `authorized` |
| `login_credentials` | Username + password form | `title`, `logo`, `usernameLabel`, `usernamePlaceholder`, `passwordLabel`, `passwordPlaceholder` | `login` |
| `pincode` | Pincode/passcode entry | `type`, `length`, `title`, `hint` | `pincode` |
| `loading` | Spinner while the app works | — | `showView` → do work → `session.nextView()` |
| `done` | Final view | — | — |
| `choose_slave` | On a `socket` driver: asks the user *"What's plugged in?"* (sets the device's virtual class) | — | — |

### 2.1 `list_devices`

```json
{
  "pair": [
    {
      "id": "list_devices",
      "template": "list_devices",
      "navigation": { "next": "add_devices" },
      "options": { "singular": true }
    },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `singular` | `boolean` | `false` | Only allow a single device to be selected |

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    session.setHandler('list_devices', async () => {
      const devices = await DeviceApi.discoverDevices();

      // Optional: push partial results while still searching
      // await session.emit('list_devices', devices);

      // Return the devices when searching is done
      return devices;

      // No devices found → return an empty array
      // return [];

      // Or throw an Error to show that message to the user
      // throw new Error('Something bad has occured!');
    });
  }

}

module.exports = MyDriver;
```

Because `list_devices` is so common, implement **`Driver#onPairListDevices()`** instead of `onPair()` when the flow
is just list + add:

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDriver extends Homey.Driver {

  async onPairListDevices() {
    const devices = await DeviceApi.discoverDevices();
    return devices;
  }

}

module.exports = MyDriver;
```

`onPairListDevices()` is called only when **no custom `onPair()` is defined** and the default is used — defining
`onPair()` disables it, and you must register the `list_devices` handler yourself.

### 2.2 `add_devices`

`"template": "add_devices"` — no options, no handlers. It adds the devices selected in the preceding
`list_devices` view. A custom view can seed it:

```javascript
Homey.setViewStoreValue('add_devices', 'devices', [
  { name: 'My Device', data: { id: 'abcd' } },
]);
```

### 2.3 `login_oauth2`

```json
{
  "pair": [
    {
      "id": "login_oauth2",
      "template": "login_oauth2",
      "options": {
        "hint": "Login with your credentials",
        "button": "Log-in"
      }
    },
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "add_devices" } },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `title` | translation object | | |
| `subtitle` | translation object | | |
| `hint` | translation object | `""` | |
| `button` | translation object | `""` | |

When either `hint` or `button` is set, a button appears and the popup only opens after the user clicks it.

```javascript
'use strict';

const Homey = require('homey');

const API_URL = 'https://api.myservice.com/oauth2/authorise?response_type=code';
const CALLBACK_URL = 'https://callback.athom.com/oauth2/callback/';
const CLIENT_ID = Homey.env.CLIENT_ID;
const OAUTH_URL = `${API_URL}&client_id=${CLIENT_ID}&redirect_uri=${CALLBACK_URL}`;

class MyDriver extends Homey.Driver {

  async onPair(session) {
    const myOAuth2Callback = await this.homey.cloud.createOAuth2Callback(OAUTH_URL);

    myOAuth2Callback
      .on('url', (url) => {
        // Send the URL to the front-end to open a popup
        session.emit('url', url).catch(this.error);
      })
      .on('code', (code) => {
        // ... swap your code here for an access token

        // Tell the front-end we're done
        session.emit('authorized').catch(this.error);
      });
  }

}

module.exports = MyDriver;
```

Prefer the `homey-oauth2app` library over hand-rolling this; the redirect-URI and token rules are in
`references/cloud-oauth-webhooks.md`.

**Gotcha (field-tested):** the `login_oauth2` view speaks a three-step protocol — driver emits **`url`** (view opens
the popup) → Athom relays the **`code`** → driver emits **`authorized`** (advance) or **`error`** (show the
message). If you guard the code exchange with a "started" latch, **reset it in the catch branch**, otherwise a
failed exchange can never be retried inside the same pair session and the user has to cancel and start over.

**Gotcha (field-tested):** always `await session.emit('authorized')` **before** any `session.done()`. `done()`
destroys the session; emitting afterwards fails with `404 Not Found: PairSession with ID … not found`. In the
standard `login_oauth2` flow you normally never call `done()` yourself.

### 2.4 `login_credentials`

```json
{
  "pair": [
    {
      "id": "login_credentials",
      "template": "login_credentials",
      "options": {
        "logo": "logo.png",
        "title": { "en": "Your custom title" },
        "usernameLabel": { "en": "E-mail address" },
        "usernamePlaceholder": { "en": "john@doe.com" },
        "passwordLabel": { "en": "Password" },
        "passwordPlaceholder": { "en": "Password" }
      }
    },
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "add_devices" } },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `title` | translation object | | |
| `logo` | `string` | `null` | A path to an image for a logo |
| `usernameLabel` | translation object | `"E-mail address"` | |
| `usernamePlaceholder` | translation object | `"john@doe.com"` | |
| `passwordLabel` | translation object | `"Password"` | |
| `passwordPlaceholder` | translation object | `"Password"` | |

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    let username = '';
    let password = '';

    session.setHandler('login', async (data) => {
      username = data.username;
      password = data.password;

      const credentialsAreValid = await DeviceApi.testCredentials({ username, password });

      // true  → continue to the next view
      // false → tell the user the login attempt failed
      // throwing shows the error message to the user
      return credentialsAreValid;
    });

    session.setHandler('list_devices', async () => {
      const api = await DeviceApi.login({ username, password });
      const myDevices = await api.getDevices();

      return myDevices.map((myDevice) => ({
        name: myDevice.name,
        data: { id: myDevice.id },
        settings: {
          // Store username & password in settings so the user can change them later
          username,
          password,
        },
      }));
    });
  }

}

module.exports = MyDriver;
```

### 2.5 `pincode`

```json
{
  "pair": [
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "pincode" } },
    {
      "id": "pincode",
      "template": "pincode",
      "options": {
        "title": "Login with your account",
        "hint": "Enter the device's pincode",
        "type": "number",
        "length": 4
      }
    },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | `string` | `"number"` | Either `number` or `text`. Changes the mobile keyboard shown for the pincode field. |
| `length` | `number` | `4` | The number of characters |
| `hint` | translation object | `""` | |
| `title` | translation object | `"Enter pincode:"` | |

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    session.setHandler('pincode', async (pincode) => {
      // The pincode is given as an array of the filled in values
      return pincode[0] === '1'
        && pincode[1] === '2'
        && pincode[2] === '3'
        && pincode[3] === '4';
    });
  }

}

module.exports = MyDriver;
```

**Gotcha:** the handler receives an **array of strings**, one entry per character (`['1','2','3','4']`), even when
`type` is `number`. Join it (`pincode.join('')`) before comparing to a stored string, and never compare with `===`
against a number.

### 2.6 `loading`

```json
{
  "pair": [
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "loading" } },
    { "id": "loading", "template": "loading" },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

No options. The pattern is: catch the view change, do the async work, then advance.

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    session.setHandler('list_devices', async () => {
      return [
        { name: 'My Device', data: { id: 'abcd' } },
      ];
    });

    session.setHandler('showView', async (view) => {
      if (view === 'loading') {
        await DeviceApi.connect();
        await session.nextView();
      }
    });
  }

}

module.exports = MyDriver;
```

**Gotcha:** a `loading` view has no exit of its own — if your `showView` handler throws or never calls
`nextView()`, the wizard spins forever. Wrap the work in `try/catch` and navigate somewhere (or `session.showView()`
back to a login step) on failure.

### 2.7 `done`

`"template": "done"` — final view. The documentation lists no options and no handlers for it.

### 2.8 `choose_slave` (class `socket` only)

Documented with the `socket` device class: *"When adding the `choose_slave` pair template, the user is presented a
`What's plugged in?` question."* The answer becomes the device's virtual class. See
`references/drivers-and-devices.md` § Virtual classes.

### 2.9 RF / Infrared: `rf_ir_remote_learn` + `rf_ir_remote_add`

These are **not** system templates — they are HTML views shipped by `homey-rfdriver`, copied into
`/drivers/<driver_id>/pair/`, so they are declared **without** a `template` key:

```json
{
  "infrared": { "satelliteMode": true },
  "pair": [
    {
      "id": "rf_ir_remote_learn",
      "navigation": { "next": "rf_ir_remote_add" },
      "options": {
        "title": { "en": "Pair your IR remote" },
        "instruction": { "en": "Press next to pair your remote." }
      }
    },
    { "id": "rf_ir_remote_add" }
  ]
}
```

Full flow: `references/wireless-rf-infrared.md`.

### 2.10 Zigbee, Z-Wave and Matter: no custom pairing

| Technology | What you can do |
| --- | --- |
| Zigbee | No pair views — *"Pairing is completely handled by Homey … you don't have to implement your own pairing views."* You can still customise the built-in wizard with `zigbee.learnmode` (`image`, `instruction`). |
| Z-Wave | Devices pair through the built-in Z-Wave wizard. Customise it with `zwave.learnmode` (`image`, `instruction`) and the unpair wizard with `zwave.unlearnmode` (same properties). |
| Matter | Only pair instructions: `matter.learnmode.instruction` (translation object) and `matter.learnmode.image` (image or animated SVG). A `pair` array is a **validation error**. |

In all three cases `learnmode.instruction` is required and `learnmode.image` is optional (the JSON schema requires
only `instruction`), and `learnmode.instruction` can be filled per language from `/.homeycompose/locales/<lang>.json`
→ `$drivers.<id>.{zwave,zigbee,matter}.learnmode.instruction`. `zwave.unlearnmode` is documented on the docs site but,
like `repair`, is absent from the `app.json` schema and from Compose's locale merge — write it as a plain translation
object inline.

---

## 3. The device object

Return an array of these from `Driver#onPairListDevices()` or a `list_devices` handler; the same shape is accepted
by `Homey.createDevice()` in a custom view.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | **yes** | The name of the device that will be displayed. |
| `data` | object | **yes** | Unique identifier object for the device. Properties may be String, Number or Object. **Immutable after pairing.** |
| `store` | object | no | Dynamic, persistent storage for your device (e.g. the IP address). |
| `settings` | object | no | Initial device settings; the user can change them afterwards in the device settings screen. |
| `icon` | string | no | Overrides the driver icon. Relative to `/drivers/<driver_id>/assets/`, e.g. `/my_icon.svg`. |
| `capabilities` | string[] | no | Overrides the driver manifest's `capabilities`. |
| `capabilitiesOptions` | object | no | Overrides the driver manifest's `capabilitiesOptions`, keyed by capability id. |
| `class` | string | no | Device class; accepted by `Homey.createDevice()` (`data` and `name` are required, `icon`, `class`, `capabilities`, `capabilitiesOptions`, `store` and `settings` are optional). |

```javascript
{
  // The name of the device that will be displayed
  name: 'My Device',

  // The data object is required and should be unique for the device.
  // A device's MAC address is good; an IP address is bad since it can change over time.
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
  icon: '/my_icon.svg',                         // relative to /drivers/<driver_id>/assets/
  capabilities: ['onoff', 'target_temperature'],
  capabilitiesOptions: {
    target_temperature: { min: 5, max: 35 },
  },
}
```

Icons may also be referenced from `/userdata` (e.g. `/userdata/my_icon.svg`) — the only exception to the
"relative to `/drivers/<driver_id>/assets/`" rule, so an app can upload an icon during pairing and reference it.
Supported since Homey **v12.3.0**.

### `data` uniqueness

- Homey identifies a device by the **`data` object together with the driver's ID**. Two devices of the same driver
  must never produce the same `data`.
- Put **only** the properties needed to identify the device in `data`. A MAC address or a vendor's device UUID is
  good; an IP address, hostname, token or firmware version is not.
- `data` cannot be changed after pairing. Changing its shape in a later app version orphans every already-paired
  device — see `references/migration-and-breaking-changes.md`.
- Everything mutable goes in the **store** (`store` at pair time, `getStoreValue()/setStoreValue()` later) or in
  **settings** when the user should be able to edit it.
- `Driver#getDevice(deviceData)` looks a device up by exactly this object.

**Gotcha:** the SDK documentation makes **no promise that already-paired devices are filtered out** of a
`list_devices` result. Filter them yourself so users cannot pair the same device twice:

```javascript
async onPairListDevices() {
  const paired = new Set(this.getDevices().map((device) => device.getData().id));
  const found = await this.discoverDevices();

  return found
    .filter((device) => !paired.has(device.macAddress))
    .map((device) => ({
      name: device.name,
      data: { id: device.macAddress },   // unique + immutable
      store: { address: device.ipAddress },
      settings: { poll_interval: 30 },
    }));
}
```

---

## 4. `Driver#onPair(session)` and the `PairSession` API

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    // session is a PairSession: a bi-directional socket to the front-end

    // Show a specific view by ID
    await session.showView('my_view');

    // Show the next view
    await session.nextView();

    // Show the previous view
    await session.prevView();

    // Close the pair session
    await session.done();

    // Received when a view has changed
    session.setHandler('showView', async (viewId) => {
      this.log('View:', viewId);
    });
  }

}

module.exports = MyDriver;
```

### PairSession methods

| Method | Returns | Description |
| --- | --- | --- |
| `setHandler(event, handler)` | `this` | Register a handler for an event. Accepts async functions that receive and respond to messages from the pair view. Chainable. |
| `emit(event, data)` | `Promise<any>` | Send an event to the view; resolves with whatever the view's `Homey.on()` callback returns. |
| `showView(viewId)` | `Promise<void>` | Show a specific pairing step by its id. |
| `nextView()` | `Promise<void>` | Go to the next pairing step. |
| `prevView()` | `Promise<void>` | Go back to the previous pairing step. |
| `done()` | `Promise<void>` | Close the pairing session. |

`PairSession.Handler` typedef: `async (data) => Promise<any>`.

### Handler names (view → app)

| Event | Sent by | Payload | Return value |
| --- | --- | --- | --- |
| `list_devices` | `list_devices` template | — | `Array<device object>`; `[]` for "nothing found"; throwing shows the error |
| `login` | `login_credentials` template | `{ username, password }` | `boolean` (`false` = failed login); throwing shows the error |
| `pincode` | `pincode` template | `string[]` — one entry per character | `boolean` |
| `showView` | every view change | `viewId` (string) | — |
| `disconnect` | session teardown | — | — (documented in the repair example; use it to clean up) |
| *any other name* | your custom view's `Homey.emit(event, data)` | whatever you send | resolved back into the `Homey.emit()` promise |

### Events (app → view)

| Event | Consumed by | Payload |
| --- | --- | --- |
| `list_devices` | `list_devices` template | array of device objects, to stream results while still searching |
| `url` | `login_oauth2` template | the authorization URL to open in a popup |
| `authorized` | `login_oauth2` template | — (advance) |
| `error` | `login_oauth2` template | error message string (field-tested) |
| *any other name* | your custom view's `Homey.on(event, cb)` | whatever you send; the callback's return value resolves `session.emit()` |

### Round trip in both directions

```javascript
// /drivers/<driver_id>/driver.js
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    session.setHandler('my_event', async (data) => {
      this.log('data from the view:', data); // { foo: 'bar' }
      return 'Hello!';
    });

    session.setHandler('showView', async (viewId) => {
      if (viewId === 'start') {
        const reply = await session.emit('hello', 'Hello to you!');
        this.log(reply); // Hi!
      }
    });

    session.setHandler('disconnect', async () => {
      // Cleanup: close sockets, clear timers, drop temporary credentials
    });
  }

}

module.exports = MyDriver;
```

```html
<!-- /drivers/<driver_id>/pair/start.html -->
<script type="application/javascript">
  Homey.emit('my_event', { foo: 'bar' }).then(function (result) {
    console.log(result); // result is: Hello!
  });

  Homey.on('hello', function (message) {
    Homey.alert(message);   // Hello to you!
    return 'Hi!';           // send a reply back to the pairing session
    // you can also return a promise if you need to do async work before replying
  });
</script>
```

---

## 5. Repair

Devices should stay available without user interaction, but when a device explicitly needs the user (e.g. an OAuth2
token has been revoked and the user must authenticate again) the user can initiate a **repair** process. On Homey
Cloud, repair views are the sanctioned way to update credentials because custom app-settings pages are not
supported there — and repairing keeps the user's Flows intact instead of breaking them by re-pairing.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "repair": [
    { "id": "login_oauth2", "template": "login_oauth2" }
  ]
}
```

```javascript
'use strict';

const Homey = require('homey');

class MyDriver extends Homey.Driver {

  async onRepair(session, device) {
    // session is a PairSession, exactly like Driver#onPair
    // device is the Homey.Device instance being repaired

    session.setHandler('my_event', async (data) => {
      // Your code
    });

    session.setHandler('disconnect', async () => {
      // Cleanup
    });
  }

}

module.exports = MyDriver;
```

### Repair vs pair

| | `onPair(session)` | `onRepair(session, device)` |
| --- | --- | --- |
| Manifest array | `pair` | `repair` |
| Custom views folder | `/drivers/<id>/pair/*.html` | `/drivers/<id>/repair/*.html` |
| Compose file | `driver.pair.compose.json` | `driver.repair.compose.json` |
| Compose options key | `$pairOptions` | `$repairOptions` |
| System templates | all | all |
| `session.*` API | full | full |
| `Homey.createDevice()` | available | **not available** — the device already exists; write to it via the `device` argument |
| Started by | the user adds a device | the user initiates a repair on an existing device |
| CLI validation | navigation + HTML existence + Matter check | **none** |
| SDK v3 API reference | `Driver#onPair(session)` is documented | **absent** — `onRepair` exists only on the docs site, not in the JSDoc reference |

Typical repair implementation — re-authenticate, then write the fresh credentials to the existing device:

```javascript
'use strict';

const Homey = require('homey');
const DeviceApi = require('device-api');

class MyDriver extends Homey.Driver {

  async onRepair(session, device) {
    session.setHandler('login', async ({ username, password }) => {
      const valid = await DeviceApi.testCredentials({ username, password });
      if (!valid) return false;

      await device.setSettings({ username, password });
      await device.setAvailable();

      return true;
    });

    session.setHandler('disconnect', async () => {
      this.log('repair session for', device.getName(), 'closed');
    });
  }

}

module.exports = MyDriver;
```

For an OAuth2 repair, run the same `createOAuth2Callback()` flow as in pairing, then
`await device.setStoreValue('tokens', tokens)` and `await session.emit('authorized')` — full example in
`references/cloud-oauth-webhooks.md`.

---

## 6. Unpair / deletion

- The SDK v3 API reference documents **no `Driver#onUnpair()`**. There is no unpair session and no unpair view
  array in the manifest schema. Do not write `onUnpair` — it will simply never be called.
- The hook that runs when the user removes a device is **`Device#onDeleted()`** (see
  `references/drivers-and-devices.md`). Use it to unsubscribe from the vendor cloud, close sockets and clear timers
  created with `this.homey.setInterval()` / `setTimeout()`.

```javascript
'use strict';

const Homey = require('homey');

class MyDevice extends Homey.Device {

  async onDeleted() {
    this.homey.clearInterval(this.pollInterval);
    await this.api.unsubscribe().catch(this.error);
    this.log('device removed');
  }

}

module.exports = MyDevice;
```

- Z-Wave has an **unpair wizard** you can customise with `zwave.unlearnmode`, which accepts the same properties as
  `learnmode` (`image`, `instruction`). See `references/wireless-zwave.md`.

---

## 7. Custom views

A custom view is an `.html` file in `/drivers/<driver_id>/pair/` (or `/repair/`); **the file name is the view id**
declared in the manifest. Declare it without a `template`:

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
  "pair": [
    { "id": "my_view" }
  ]
}
```

The global `Homey` object is available inside the view.

### Front-end API

| Call | Returns | Description |
| --- | --- | --- |
| `Homey.emit(event, data)` | `Promise<any>` | Emit an event to your app; the handler registered with `session.setHandler(event, cb)` runs and its return value resolves the promise. |
| `Homey.on(event, callback)` | — | Listen for `session.emit()` from your app. The callback may return a value or a promise, which is sent back as the reply. |
| `Homey.setTitle(title)` | — | Set the window's title. |
| `Homey.setSubtitle(subtitle)` | — | Set the window's subtitle. |
| `Homey.showView(viewId)` | — | Navigate to another view, by an `id` from the App Manifest. |
| `Homey.prevView()` | — | Show the previous view. |
| `Homey.nextView()` | — | Show the next view. |
| `Homey.getCurrentView()` | view id | Returns the current view ID. |
| `Homey.createDevice(device)` | `Promise<Object>` | Create a device. Requires `data` and `name`; may contain `icon`, `class`, `capabilities`, `capabilitiesOptions`, `store`, `settings`. **Not available while repairing.** |
| `Homey.getZone()` | `Promise<string>` | Zone ID of the active Zone. |
| `Homey.getOptions([viewId])` | `Promise<Object>` | The `options` object of a view (the current view when `viewId` is omitted). |
| `Homey.setNavigationClose()` | — | Remove all navigation buttons and show a single *Close* button. |
| `Homey.done()` | — | Close the pairing window. |
| `Homey.alert(message[, icon])` | `Promise<void>` | Alert dialog. `icon` may be `null`, `error`, `warning` or `info`. |
| `Homey.confirm(message[, icon])` | `Promise<boolean>` | Confirm dialog; resolves `true` when the user pressed *OK*. Same `icon` values. |
| `Homey.popup(url)` | — | Show a popup with a remote website. |
| `Homey.__(key[, tokens])` | string | Translate programmatically; `key` uses dots for sub-properties (`pair.title`). |
| `Homey.showLoadingOverlay()` | — | Show the loading overlay. |
| `Homey.hideLoadingOverlay()` | — | Hide the loading overlay. |
| `Homey.getViewStoreValue(viewId, key)` | `Promise<any>` | Read a view's store value. |
| `Homey.setViewStoreValue(viewId, key, value)` | `Promise<void>` | Write a view's store value. |

Translations also work declaratively with `data-i18n`, resolved against `/locales/<language>.json`:

```html
<span data-i18n="pair.title"></span>
<p data-i18n="pair.intro"></p>
```

```html
<script type="application/javascript">
  Homey.setTitle(Homey.__('pair.title'));
  Homey.setSubtitle(Homey.__('pair.subtitle'));
</script>
```

### Creating a device from a custom view

```html
<!-- /drivers/<driver_id>/pair/start.html -->
<script type="application/javascript">
  Homey.createDevice({
    // The name of the device that will be shown to the user
    name: 'My Device',

    // The data object is required and should contain only unique properties for the device.
    // So a MAC address is good, but an IP address is bad (can change over time)
    data: {
      id: 'abcd',
    },

    // Optional: The store is dynamic and persistent storage for your device
    store: {
      address: '127.0.0.1',
    },

    // Optional: Initial device settings that can be changed by the user afterwards
    settings: {
      pincode: '1234',
    },
  })
    .then(function () {
      Homey.done();
    })
    .catch(function (error) {
      Homey.alert(error);
    });
</script>
```

### Handing devices to the `add_devices` template

```html
<script type="application/javascript">
  var devicesArray = [
    {
      name: 'My Device',
      data: { id: 'abcd' },
    },
  ];
  Homey.setViewStoreValue('add_devices', 'devices', devicesArray);
</script>
```

### A complete custom view

```html
<!-- /drivers/my_driver/pair/start.html -->
<header class="homey-header">
  <h1 class="homey-title" data-i18n="pair.title"></h1>
  <p class="homey-subtitle" data-i18n="pair.intro"></p>
</header>

<form class="homey-form">
  <div class="homey-form-group">
    <label class="homey-form-label" for="host">Hostname</label>
    <input class="homey-form-input" id="host" type="text" value="" />
  </div>
  <button class="homey-button-primary-full" id="connect" type="button">Connect</button>
</form>

<script type="application/javascript">
  Homey.setTitle(Homey.__('pair.title'));

  document.getElementById('connect').addEventListener('click', function () {
    Homey.showLoadingOverlay();

    Homey.emit('connect', { host: document.getElementById('host').value })
      .then(function () {
        Homey.hideLoadingOverlay();
        Homey.showView('list_devices');
      })
      .catch(function (error) {
        Homey.hideLoadingOverlay();
        Homey.alert(error, 'error');
      });
  });
</script>
```

The `homey-header` / `homey-form` / `homey-button-*` classes come from the Homey Style Library, available on Homey
Cloud and on Homey Pro since v8.1.0 — the full class list is in `references/custom-views-and-settings.md`. Prefer
it over custom CSS.

### Right-to-Left (RTL) languages

All **built-in** pairing views support RTL (Arabic, `ar`) out of the box — you only have to ship the translations.
**Custom** pairing views are your own responsibility: when an RTL language is active you may need to adjust layout
direction, text alignment, margins/padding/positioning and icon placement. Use the CSS `:dir(rtl)` selector:

```css
.my-custom-class { transform: translate(-50%); }
.my-custom-class:dir(rtl) { transform: translateX(50%); }
```

---

## 8. Worked example: login → connect → list → add

`/drivers/my_driver/driver.pair.compose.json`:

```json
[
  {
    "id": "login_credentials",
    "template": "login_credentials",
    "options": {
      "title": { "en": "Sign in" },
      "usernameLabel": { "en": "E-mail address" },
      "passwordLabel": { "en": "Password" }
    },
    "navigation": { "next": "loading" }
  },
  {
    "id": "loading",
    "template": "loading"
  },
  {
    "id": "list_devices",
    "template": "list_devices",
    "navigation": { "prev": "login_credentials", "next": "add_devices" }
  },
  {
    "id": "add_devices",
    "template": "add_devices"
  }
]
```

```javascript
'use strict';

const Homey = require('homey');
const CloudApi = require('cloud-api');

class MyDriver extends Homey.Driver {

  async onPair(session) {
    let username = '';
    let password = '';
    let api = null;

    session.setHandler('login', async (data) => {
      username = data.username;
      password = data.password;

      // false → "login failed"; throwing shows the message to the user
      return CloudApi.testCredentials({ username, password });
    });

    session.setHandler('showView', async (viewId) => {
      if (viewId !== 'loading') return;

      try {
        api = await CloudApi.login({ username, password });
        await session.nextView();
      } catch (err) {
        this.error(err);
        await session.showView('login_credentials');
      }
    });

    session.setHandler('list_devices', async () => {
      const paired = new Set(this.getDevices().map((device) => device.getData().id));
      const devices = await api.getDevices();

      return devices
        .filter((device) => !paired.has(device.id))
        .map((device) => ({
          name: device.name,
          data: { id: device.id },
          store: { region: device.region },
          settings: { username, password, poll_interval: 30 },
          capabilities: device.dimmable ? ['onoff', 'dim'] : ['onoff'],
          capabilitiesOptions: device.dimmable ? { dim: { title: { en: 'Brightness' } } } : {},
        }));
    });

    session.setHandler('disconnect', async () => {
      username = '';
      password = '';
      if (api) await api.close().catch(this.error);
    });
  }

}

module.exports = MyDriver;
```

**Note on view ids:** the view `id` is free-form — real published apps use e.g. `{"id": "list_bridges", "template":
"list_devices", "options": {"singular": true}}` for a hub-selection step followed by a second
`{"id": "list_devices", "template": "list_devices"}` step for the hub's devices. Both fire the **same**
`list_devices` handler, so track the active step in the `showView` handler and branch on it.

---

## 9. Testing pairing

```bash
homey app run              # install & run in development mode, live logs
homey app run --clean      # -c: "Delete all userdata, paired devices etc. before running the app"
homey app validate
```

`--clean` is the fast way to re-test a pair flow from zero. Full CLI reference: `references/cli-and-tooling.md`.

---

## Gotchas

- **`homey app driver create` does not write a `pair` array.** The wizard writes `name`, `class`, `capabilities`,
  `platforms`, `connectivity`, `images` (+ `zwave`/`matter`) only. With no `pair` array the driver has no pairing
  steps at all and the scaffolded `onPairListDevices()` never runs (it belongs to the `list_devices` view) — add
  the `list_devices` + `add_devices` pair right after scaffolding.
- **Defining `onPair()` disables `onPairListDevices()`.** `onPairListDevices()` runs only when *no custom
  `onPair()` method has been defined*. Once you write `onPair()`, register `session.setHandler('list_devices', …)`
  yourself.
- **Handler names come from the template, not from the view id.** A view `{"id": "list_my_devices", "template":
  "list_devices"}` still fires the `list_devices` handler. When two views share a template, disambiguate with the
  `showView` handler.
- **`repair` is completely unvalidated.** It is absent from the `app.json` schema and from every CLI check: broken
  `navigation` ids and missing `/drivers/<id>/repair/<view_id>.html` files ship silently. Test repair manually.
- **`template` names are not validated either** — a typo produces a broken step at runtime, not a validation error.
- **A custom pair view must exist on disk with the exact case.** `homey app validate` throws
  `Filepath does not exist: drivers/<id>/pair/<view_id>.html` (case-sensitive), which also bites on
  case-insensitive macOS/Windows filesystems when the repo is built on Linux CI.
- **`navigation.prev`/`next` must reference views in the same array.** You cannot navigate from a `pair` view to a
  `repair` view or vice versa.
- **`driver.pair.compose.json` replaces the array** — it is assigned over anything inherited via `$extends`, not
  merged. Same for `driver.repair.compose.json`.
- **`$pairOptions` / `$repairOptions` are ignored when the matching array is empty or missing.** Compose only walks
  them while iterating existing views.
- **Matter drivers must not define `pair`** — `homey app validate` fails with *"Matter drivers do not support
  custom pairing views"*. Zigbee and Z-Wave pairing is likewise handled entirely by Homey (not CLI-enforced, but
  your views will never run).
- **`data` is immutable and identifies the device together with the driver id.** Never put an IP address,
  hostname, token or firmware version in it; use `store`/`settings`, or LAN discovery
  (`references/wireless-lan-discovery.md`).
- **Nothing guarantees already-paired devices are hidden from `list_devices`.** Filter with
  `this.getDevices().map((d) => d.getData().id)` yourself.
- **Asking the user to type an IP address is an App Store review failure.** Homey's review feedback is explicit:
  *"users need to manually enter their IP address … This is no longer allowed. Please use the `ManagerDiscovery`
  to make it easy for your users to pair their devices."* Use mDNS-SD / SSDP / MAC discovery in the pair flow.
- **The `pincode` handler receives `string[]`, never a number or a string.** `['1','2','3','4']`.
- **A `loading` view never exits by itself.** Always `await session.nextView()` (or `showView()`) from the
  `showView` handler, inside a `try/catch`.
- **(Field-tested) `emit('authorized')` must come BEFORE `session.done()`.** `done()` destroys the session; any
  later emit or navigation fails with `404 Not Found: PairSession with ID … not found`. Order: exchange code →
  store tokens → `await session.emit('authorized')` → only then, if at all, `session.done()`.
- **(Field-tested) reset your "started" latch in the catch branch** of an OAuth2 code exchange, or a single failure
  bricks the rest of the pair session and the user must cancel and restart.
- **`Homey.createDevice()` does not exist during repair.** Write to the `device` argument of `onRepair()` instead
  (`device.setSettings()`, `device.setStoreValue()`, `device.setAvailable()`).
- **Credentials entered during pairing should be stored in device `settings`**, so the user can change them later
  without re-pairing — and pair a `repair` view for the case where they change externally.
- **Repair, not re-pair.** Re-pairing creates a new device (new `data`/id) and breaks every Flow that referenced
  the old one; on Homey Cloud repair views are the only supported way to update credentials, since custom app
  settings pages are unavailable there.
- **`session.emit()` and `session.showView()` are async** — `await` them, or attach `.catch(this.error)`; an
  unhandled rejection inside an event-emitter callback can take the app down.
- **Everything a view sends is untrusted user input.** Validate payloads from `Homey.emit()` in the handler before
  using them.
- **The App Store guidelines' URL ban applies to the readme, not to pair views.** §1.3 forbids URLs in the readme
  text (including donation links — use `contributing.donate`); §1.8 wants support/source/homepage URLs in the App
  Manifest instead. Nothing forbids a link inside a pair view, and `Homey.popup(url)` exists precisely to open a
  remote website from one. Reviewers do test that *"pairing instructions for all drivers are accurate and clear."*
- **Compose writes generated pair HTML into your source tree.** `$template` materialises
  `/drivers/<id>/pair/<view_id>.html` and `<view_id>.assets/` on every build; keep the originals in
  `/.homeycompose/drivers/pair/<template_id>/` as the source of truth.

---

## Sources

- <https://apps.developer.homey.app/the-basics/devices/pairing>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/devices-list>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/add-devices>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/oauth2-login>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/credentials-login>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/pincode>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/loading>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/done>
- <https://apps.developer.homey.app/the-basics/devices/pairing/custom-views>
- <https://apps.developer.homey.app/advanced/custom-views/custom-pairing-views>
- <https://apps.developer.homey.app/advanced/custom-views/html-and-css-styling>
- <https://apps.developer.homey.app/advanced/homey-compose>
- <https://apps.developer.homey.app/the-basics/devices>
- <https://apps.developer.homey.app/wireless/zigbee>
- <https://apps.developer.homey.app/wireless/z-wave>
- <https://apps.developer.homey.app/wireless/matter>
- <https://apps.developer.homey.app/wireless/infrared>
- <https://apps.developer.homey.app/guides/homey-cloud>
- <https://apps.developer.homey.app/the-basics/app/internationalization> (RTL support for pairing views)
- <https://apps.developer.homey.app/app-store/guidelines>
- <https://apps-sdk-v3.developer.homey.app/PairSession.html>
- <https://apps-sdk-v3.developer.homey.app/Driver.html>
- <https://apps-sdk-v3.developer.homey.app/Device.html>
- <https://apps-sdk-v3.developer.homey.app/tutorial-device-classes.html>
