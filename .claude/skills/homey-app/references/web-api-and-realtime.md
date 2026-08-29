# App Web API, Realtime & App-to-App

How a Homey app exposes REST endpoints (`/api.js` + the `api` manifest block), pushes one-way
realtime events to settings pages and widgets, talks to other apps through `ApiApp`, and uses the
Homey Web API itself with `homey:manager:api`.

**Everything on this page is Homey Pro / Homey Self-Hosted Server only.** Apps on Homey Cloud may
not expose a Web API, may not use `homey:app:<appId>`, and may not use `homey:manager:api`
(see [Homey Cloud restrictions](#cloud)).

## Table of contents
1. [Surface map — which "api.js" is which](#surface-map)
2. [Declaring routes in the App Manifest](#declaring)
3. [Implementing handlers in `/api.js`](#handlers)
4. [Calling the API from a settings page](#from-settings)
5. [Calling the API from a widget](#from-widget)
6. [Calling the API over HTTP and from the CLI](#from-http)
7. [Realtime events](#realtime)
8. [App-to-app communication (`ApiApp`)](#app-to-app)
9. [`ManagerApi` full reference](#managerapi)
10. [Using the Homey Web API from inside an app (`homey:manager:api`)](#homey-web-api)
11. [`homey-api` (HomeyAPI) inside an app](#homey-api-package)
12. [Homey Cloud restrictions](#cloud)
13. [Gotchas](#gotchas)
14. [Sources](#sources)

---

## 1. Surface map — which "api.js" is which {#surface-map}

Three different things are called "the API" in Homey apps. Do not mix them up.

| Surface | Where it is declared | Where it is implemented | Who calls it | Cloud |
| --- | --- | --- | --- | --- |
| **App Web API** | `api` object in the App Manifest (`/.homeycompose/app.json` → `app.json`) | `/api.js` at the app root | Settings pages (`Homey.api`), external HTTP clients, **other apps** (`ApiApp`) | **no** |
| **Widget API** | `api` object in `/widgets/<widgetId>/widget.compose.json` | `/widgets/<widgetId>/api.js` | Only that widget's webview (`Homey.api`) — "scoped to the widget and not global" | no (widgets are Pro-only) |
| **Homey Web API** | Not declared by your app — it is Homey's own REST/realtime API | Implemented by Homey | Your app, *if* it has `homey:manager:api` | **no** |

- Both `api.js` variants use the **same handler signature** `({ homey, params, query, body })` and both
  reach the app instance through `homey.app`.
- The widget API is documented in `references/widgets.md`; this file covers the app-level Web API,
  realtime and app-to-app.

---

## 2. Declaring routes in the App Manifest {#declaring}

In SDK v3 routes live in the **App Manifest**, not in `api.js`. The **key** of each route is the name
of the exported handler function.

```jsonc
// /.homeycompose/app.json   (Homey Compose copies this into the generated /app.json)
{
  "id": "com.athom.example",
  "sdk": 3,
  // ...
  "api": {
    "getSomething":    { "method": "GET",    "path": "/" },
    "addSomething":    { "method": "POST",   "path": "/" },
    "updateSomething": { "method": "PUT",    "path": "/:id" },
    "deleteSomething": { "method": "DELETE", "path": "/:id" }
  }
}
```

### Route options

| Key | Type | Value |
| --- | --- | --- |
| `method` | `String`, `Array` | `"GET"`, `"POST"`, `"PUT"` or `"DELETE"`, or an array of these values. |
| `path` | `String` | For example `"/"`, `"/:foo"`, `"/bar/:foo"`. Named `:params` are exposed as `params.foo`. |
| `public` | `Boolean` | Default `false`. Set to `true` to make the endpoint accessible **without a token**. |

There are **no other documented route options in SDK v3**. `method`/`path`/`public` is the complete
set.

### Endpoint URLs

```
/api/app/<appId>/<path>
```

e.g. route `{ "method": "PUT", "path": "/:id" }` in app `com.athom.example` is
`PUT /api/app/com.athom.example/42`.

- **All endpoints are protected by default.** The requesting user needs permission to your app,
  which is **granted by default after installation**.
- `"public": true` removes the token requirement. Only use public endpoints when no alternative
  exists — the documented good use case is *sending a pin-code from another device to Homey*.

### Multiple methods on one route

```jsonc
"api": {
  "handleWebhookish": { "method": ["GET", "POST"], "path": "/hook" }
}
```

One handler serves both; branch on the presence of `body` if the behaviour differs.

### Casing

The Web API guide documents uppercase (`"GET"`, `"POST"`, `"PUT"`, `"DELETE"`); the SDK v3 upgrade
guide contains an example with lowercase `"method": "get"`. **Always write uppercase** — the widget
`api` JSON schema in `homey-lib` enforces the uppercase enum, so uppercase is the only form that is
valid everywhere.

### The array form is app-level only

`"method": ["GET", "POST"]` comes from the **app-level** Web API guide, and the app-level `api` block
is not schema-validated (see [Gotchas](#gotchas)). The **widget** `api` block *is* validated, and its
schema is stricter:

| Widget `api.<name>` | Rule (from `homey-lib`'s `app.json` schema) |
| --- | --- |
| `method` | **Required.** `"type": "string"` with `enum: ["GET", "POST", "PUT", "DELETE"]` — a single uppercase string. **Arrays are rejected.** |
| `path` | **Required.** `"type": "string"`. |

So a multi-method route can only be expressed in the app-level `api` block; in a widget, declare one
route name per method.

---

## 3. Implementing handlers in `/api.js` {#handlers}

`api.js` sits in the **app root** and exports an object whose keys match the route names in the
manifest. Every handler is an `async` function.

```javascript
// /api.js
'use strict';

module.exports = {
  async getSomething({ homey, query }) {
    // query parameters like "/?foo=bar" arrive as query.foo
    // the App instance is reachable through homey.app
    const result = await homey.app.getSomething(query.foo);

    // perform other logic like mapping result data
    return result;
  },

  async addSomething({ homey, body }) {
    // access the post body and perform some action on it
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

### Handler argument

Handlers receive **one object** with four properties:

| Property | Type | Contents |
| --- | --- | --- |
| `homey` | `Homey` | The Homey instance — the same object as `this.homey` inside `App`/`Driver`/`Device`. Use `homey.app` for the App instance, `homey.drivers`, `homey.settings`, `homey.api.realtime(...)`, … |
| `params` | `Object<string,string>` | The `:named` segments declared in `path`. |
| `query` | `Object<string,string>` | Query-string parameters: `?foo=bar` → `{ "foo": "bar" }`. |
| `body` | `Object` | The request body for `POST`/`PUT`. **JSON is automatically parsed.** `Homey.api` sends an **empty body** for `GET` and `DELETE`. |

The return value is serialised back to the caller. Throwing (or returning a rejected promise) surfaces
as an error to the caller: the settings-page callback receives it as `err`, the widget/`ApiApp`
promise rejects.

### A realistic handler with validation and realtime

```javascript
// /api.js
'use strict';

module.exports = {
  async getStatus({ homey }) {
    return homey.app.getStatus();                       // plain JSON-serialisable object
  },

  async setMode({ homey, body }) {
    if (typeof body?.mode !== 'string') {
      throw new Error('Missing or invalid "mode"');      // -> error at the caller
    }

    await homey.app.setMode(body.mode);

    // push the new state to every subscribed settings page / widget
    await homey.api.realtime('mode_changed', { mode: body.mode });

    return { ok: true };
  },

  async deleteItem({ homey, params }) {
    const removed = await homey.app.removeItem(params.id);
    if (!removed) throw new Error(`Unknown id: ${params.id}`);
    return { ok: true };
  },
};
```

Keep `api.js` **thin**: validate input, delegate to a method on the App/Driver/Device, map the result.
Business logic belongs in `app.js` so Flow cards and the Web API share one implementation.

### Accepted file names

| Runtime | App-level file | Notes |
| --- | --- | --- |
| JavaScript (CommonJS) | `/api.js` | Default. `module.exports = { … }` |
| JavaScript (explicit module type) | `/api.mjs` (ESM) or `/api.cjs` (CommonJS) | Both extensions require `"compatibility": ">=12.0.1"` — `homey-lib` runs the same `checkEsm()` on `api.mjs` *and* `api.cjs` and throws `ESM apps require a compatibility of at least >=12.0.1. (<path>)` otherwise. (`"esm": true` in the manifest is checked separately with the same minimum.) |
| TypeScript | `/api.mts` (compiled) | Uses `export default { … }`; type the argument yourself (see below). |
| Python | `/api.py` | `async def` functions with **keyword-only** arguments, plus `__all__ = [...]` to export them as endpoints. |

TypeScript argument types (from the official example):

```ts
// /api.mts
import type App from "./app.mjs";

type RequestWithBody = {
  homey: App["homey"];
  query: Record<string, string>;
  params: Record<string, string>;
  body: Record<string, unknown>;
};

type RequestWithoutBody = {
  homey: App["homey"];
  query: Record<string, string>;
  params: Record<string, string>;
  body: Record<never, never>; // Homey.API sends an empty body for GET and DELETE requests
};

export default {
  async getSomething({ homey, query }: RequestWithoutBody): Promise<any> {
    return (homey.app as App).getSomething();
  },
  async addSomething({ homey, body }: RequestWithBody): Promise<any> {
    return (homey.app as App).addSomething(body);
  },
};
```

Python shape (`/api.py`) — keyword-only arguments plus an `__all__` export list; see
`references/python-apps.md`. The **manifest route keys are the snake_case function names**
(`"get_something"`, `"add_something"`, `"update_something"`, `"delete_something"`), and every handler
takes all four keyword arguments (`homey`, `query`, `params`, `body`) even when it ignores some:

```python
async def get_something(
    *,
    homey: Homey,
    query: dict[str, str],
    params: dict[str, str],
    body: dict[Never, Never],  # Homey.API sends an empty body for GET requests
) -> Any:
    return cast(App, homey.app).get_something()


# Export all these methods as endpoints
__all__ = ["get_something"]
```

### Legacy SDK v2 array style — recognise, do not write

Before SDK v3, routes were declared **inside `api.js`**, which exported an **array** of route objects
each carrying its own `method`/`path`/`public` (and, in old apps, a `role` restriction) plus a
callback-style `fn`. The SDK v3 upgrade guide states the change plainly:

> API routes now need to be defined in the App Manifest instead of the `api.js`. Additionally since
> you can no longer gain access to the API through require-ing homey it is now passed as an argument
> to your API handler method.

```javascript
// ✗ SDK v2 — shape you will meet in old apps. NOT valid in SDK v3.
const Homey = require('homey');          // v2 gave you the managers via require()

module.exports = [
  {
    method: 'GET',
    path: '/',
    public: true,
    role: 'owner',                        // not part of the SDK v3 route surface
    fn: function (args, callback) {       // callbacks were removed in SDK v3
      callback(null, 'Hello!');
    },
  },
];
```

That shape is shown for **recognition while migrating an old app**; it is not part of the SDK v3
documentation, and neither `fn` nor `role` exist in SDK v3.

Migration table:

| SDK v2 | SDK v3 |
| --- | --- |
| Route array in `api.js` | `api` object in the App Manifest, keyed by handler name |
| `fn: function (args, callback)` | `async handlerName({ homey, params, query, body })` |
| `callback(err, result)` | `return result` / `throw err` |
| `const Homey = require('homey')` for managers | `homey` argument (`homey.app`, `homey.settings`, …) |
| `role: 'owner'` | **No documented equivalent.** SDK v3 route options are only `method`, `path`, `public`. (`owner`/`manager`/`user`/`guest` still exist as Homey *user* roles — `HomeyAPI#hasRole(roleId)` — but they are not a route option.) |

---

## 4. Calling the API from a settings page {#from-settings}

A custom app settings view (`/settings/index.html`, `<script src="/homey.js" data-origin="settings">`)
gets a global `Homey` object inside `onHomeyReady(Homey)`.

### `Homey.api(String method, String path, Mixed body, Function callback)`

`method` is `GET`, `POST`, `PUT` or `DELETE`; `path` is **relative to your app's API endpoint**;
`body` is optional (`null` to ignore it). The callback is `(err, result)`.

```html
<!-- /settings/index.html -->
<script type="text/javascript">
  function onHomeyReady(Homey) {
    // make a PUT call to /api/app/com.your.app/hello
    Homey.api('PUT', '/hello', { foo: 'bar' }, function (err, result) {
      if (err) return Homey.alert(err);
      document.getElementById('status').textContent = String(result);
    });

    // subscribe to realtime events emitted by the app
    Homey.on('mode_changed', function (data) {
      document.getElementById('mode').textContent = data.mode;
    });

    Homey.ready();   // the view stays hidden until this is called
  }
</script>
```

### Full settings-view API (`data-origin="settings"`)

| Method | Purpose |
| --- | --- |
| `Homey.ready()` | Show the view. The view is hidden until called — use the time to prefetch and avoid flicker. |
| `Homey.get([String name,] Function callback)` | One setting's value, or all settings when `name` is omitted. |
| `Homey.set(String name, Mixed value, Function callback)` | Set a setting (value must be JSON-serialisable). |
| `Homey.unset(String name, Function callback)` | Unset a setting. |
| `Homey.on(String event, Function callback)` | Listen to **your app's realtime events**. System events while modifying settings: `settings.set`, `settings.unset`. |
| `Homey.api(String method, String path, Mixed body, Function callback)` | Call your app's Web API. |
| `Homey.alert(String message, Function callback)` | Alert dialog. |
| `Homey.confirm(String message, Function callback)` | Confirm dialog; callback's 2nd argument is `true` on OK. |
| `Homey.popup(String url[, Object opts])` | New window; `opts` may contain `width`/`height` (default `400`). |
| `Homey.openURL(String url)` | Open a new window. |
| `Homey.__(String key[, Object tokens])` | Translate a key from `/locales/<lang>.json` (dots for sub-properties). |

**Gotcha:** the documented settings-view signature is **callback-based**, unlike the widget's
promise-based `Homey.api`. If you prefer `await`, promisify it yourself instead of assuming a promise
is returned:

```javascript
const api = (method, path, body = null) =>
  new Promise((resolve, reject) =>
    Homey.api(method, path, body, (err, result) => (err ? reject(err) : resolve(result))));

const status = await api('GET', '/status');
```

> Custom app settings views are **not allowed on Homey Cloud** — see `references/custom-views-and-settings.md`.

---

## 5. Calling the API from a widget {#from-widget}

Widgets call **their own** API (`widget.compose.json` → `api`, implemented in
`/widgets/<widgetId>/api.js`), not the app-level `/api.js`.

```json
// /widgets/<widgetId>/widget.compose.json
{
  "name": { "en": "My Widget" },
  "height": 100,
  "api": {
    "getSomething":    { "method": "GET",    "path": "/" },
    "addSomething":    { "method": "POST",   "path": "/" },
    "updateSomething": { "method": "PUT",    "path": "/:id" },
    "deleteSomething": { "method": "DELETE", "path": "/:id" }
  }
}
```

```javascript
// /widgets/<widgetId>/api.js
'use strict';

module.exports = {
  async getSomething({ homey, query }) {
    // you can access the App instance through homey.app
    return 'Hello from App';
  },
};
```

Frontend (promise-based here, unlike settings views):

```javascript
function onHomeyReady(Homey) {
  Homey.ready({ height: 200 });

  Homey.api('GET', '/', {})
    .then((result) => { document.getElementById('message').innerText = String(result); })
    .catch(console.error);

  Homey.on('mode_changed', (data) => { /* realtime push from the app */ });
}
```

| Widget view API | Signature |
| --- | --- |
| `Homey.api` | `Homey.api(method: string, path: string, body?: object): Promise<unknown>` — "Access your api as defined under `widget.compose.json` -> `api`." |
| `Homey.on` | `Homey.on(event: string, callback: (...args[]: any) => void): void` — "Listen to events emitted by your app." |

Full widget surface: `references/widgets.md`.

---

## 6. Calling the API over HTTP and from the CLI {#from-http}

### Raw HTTP

```
<base-url>/api/app/<appId>/<path>
Authorization: Bearer <token>          # omit only for "public": true routes
Content-Type: application/json         # for POST/PUT bodies
```

- Get a usable base URL from inside the app with `await this.homey.api.getLocalUrl()` ("Returns the
  url for local access").
- Get a token from inside the app with `await this.homey.api.getOwnerApiToken()` (requires
  `homey:manager:api`), or create a **Personal Access Token** in the Homey Web App for external
  scripts.

```javascript
// app.js — hand a ready-to-use URL to an external device (e.g. a Raspberry Pi reporting status)
const url = await this.homey.api.getLocalUrl();     // the url for local access
this.log(`POST ${url}/api/app/${this.manifest.id}/status`);
```

### From the Homey CLI

`homey api raw` performs an arbitrary request against the selected Homey and accepts any path, so it
is the fastest way to exercise your own endpoints:

```bash
# GET /api/app/com.athom.example/
homey api raw --path /api/app/com.athom.example/

# POST with a JSON body
homey api raw -X POST \
  --path /api/app/com.athom.example/thing \
  --body '{"mode":"eco"}'

# body from a file, with request diagnostics on stderr
homey api raw -X PUT --path /api/app/com.athom.example/42 --body @./payload.json --verbose

# pluck a field out of your own endpoint's JSON response
homey api raw --path /api/app/com.athom.example/status --jq '.mode'

# the CLI guide's own example against one of Homey's managers
homey api raw --path /api/manager/system/ --jq '.value.homeyVersion'
```

`homey api raw` options:

| Option | Notes |
| --- | --- |
| `--path` | **Required** (`demandOption`). Must be absolute — otherwise `Invalid path. Please provide an absolute path starting with "/".` |
| `--method`, `-X` | Default `GET`; case-insensitive (upper-cased for you). |
| `--header`, `-H` | Repeatable, `"name:value"`. |
| `--body` | Inline JSON string or `@file` path. **Only accepted with `POST` and `PUT`** — any other method throws `Invalid option usage: --body is only supported with methods POST, PUT.` |
| `--request-json` | Default `true`; encodes the body as JSON. Set `--no-request-json` to send it raw. |
| `--include` | Print the status line and response headers as well. |
| `--verbose` | Request diagnostics to **stderr** (`method`, `path`, `timeoutMs`, `authMode`, `url`, request headers with `authorization`/`cookie` redacted, `status`, `contentType`, `durationMs`). |
| `--token` | Token mode. Requires `--address` **or** `--homey-id`; all three together are rejected. |
| `--address` | Base URL, e.g. `http://192.168.1.100`. **Only valid together with `--token`.** |
| `--homey-id` | Target a cached Homey by id instead of the selected Homey. |
| `--timeout` | Milliseconds, default `30000`. |
| `--json` | Force JSON output even when the response is a plain string. |
| `--jq` | Filter the JSON output with a jq expression. |

Aliases: `homey api call`, `homey api request`. Sibling subcommands: `homey api schema`,
`homey api diagnose`, and one auto-generated subcommand per manager
(`homey api <manager> <operation>`, e.g. `homey api devices open-device --id <device-id>`).
See `references/cli-and-tooling.md`.

---

## 7. Realtime events {#realtime}

> "Your app can emit 'realtime' events, which are one-way events to a subscribing client, for example
> a browser showing a settings view page."

### Emitting from the app

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {

  async onInit() {
    await this.homey.api.realtime('my_event', 'my_json_stringifyable_value');
  }

  async pushStatus(status) {
    // fire-and-forget from non-async contexts
    this.homey.api.realtime('status_update', { status, at: Date.now() })
      .catch(this.error);
  }

}

module.exports = App;
```

| Method | Signature | Notes |
| --- | --- | --- |
| `homey.api.realtime` | `(async) realtime(event: string, data: any)` | `event` = name, `data` = payload. The payload must be JSON-stringifiable. |

The same call works from `api.js` (`homey.api.realtime(...)`), a Driver or a Device (`this.homey.api.realtime(...)`).

### Subscribing

| Client | How |
| --- | --- |
| App settings page | `Homey.on('my_event', (data) => { … })`. Also receives the system events `settings.set` and `settings.unset`. |
| Widget | `Homey.on('my_event', (data) => { … })` — "Listen to events emitted by your app." |
| Another app | `apiApp.on('realtime', handler)` on an `ApiApp` instance (see below). |

### Subscribing to another endpoint's realtime events (`getApi`)

`ManagerApi#getApi(uri)` creates an `Api` instance bound to any Homey endpoint URI and fires realtime
events on it. Manager URIs have the form `homey:manager:<managerId>` (e.g. `homey:manager:webserver`,
`homey:manager:devices`); app URIs have the form `homey:app:<appId>` — for apps, prefer
`getApiApp(appId)`, which additionally gives you `install`/`uninstall` events.

```javascript
// homey:manager:api covers "the ManagerApi methods to communicate with the Homey Web API",
// so subscribing to one of Homey's own managers needs that permission
const webserverApi = this.homey.api.getApi('homey:manager:webserver');

webserverApi.on('realtime', (event, data) => {
  this.log('webserver realtime:', event, data);
});

// later, stop receiving events
webserverApi.unregister();                    // === this.homey.api.unregisterApi(webserverApi)
```

**There is no documented `realtime` event on `ManagerApi` itself.** `this.homey.api` exposes only the
methods in [§9](#managerapi); realtime *reception* happens on `Api` / `ApiApp` instances returned by
`getApi()` / `getApiApp()`.

**Realtime callback shape:** the sources disagree on arity.

| Source | Shape shown |
| --- | --- |
| `Api` / `ApiApp` apidoc **event parameter table** | two parameters: `event` (string, "Name of the realtime event") and `data` (any, `<optional>`, "Data of the realtime event") |
| `ApiApp` apidoc **example** | one parameter: `.on('realtime', (result) => console.log('otherApp.onRealtime', result))` |
| Web API guide example | one parameter: `.on('realtime', (event) => { … })` |

Nothing in the sources supports object-destructuring (`({ event, data }) => …`). Take the parameter
table as the contract and write the handler defensively so both shapes work:

```javascript
otherAppApi.on('realtime', (event, data) => {
  const name    = typeof event === 'string' ? event : event?.event;
  const payload = typeof event === 'string' ? data  : event?.data;
  this.log('realtime', name, payload);
});
```

---

## 8. App-to-app communication (`ApiApp`) {#app-to-app}

Apps talk to each other through their Web APIs. **Homey Pro only.**

### 1. Declare the permission

```jsonc
// /.homeycompose/app.json
{
  "id": "com.athom.example",
  "permissions": [
    "homey:app:com.athom.otherApp"
  ]
}
```

Permissions for app-to-app communication look like `homey:app:<appId>`, e.g.
`homey:app:com.athom.example` or `homey:app:com.yahoo.weather`. One permission entry **per target
app**. Apps do **not** auto-update when new permissions are added, so adding one in an update leaves
existing installs on the old version until the user updates manually.

`homey:app:com.athom.homeyscript` is explicitly forbidden and fails validation.

### 2. Create the client and guard on availability

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {

  async onInit() {
    this.otherAppApi = this.homey.api.getApiApp('com.athom.otherApp');

    const isInstalled = await this.otherAppApi.getInstalled();
    const version = await this.otherAppApi.getVersion();
    this.log('otherApp installed:', isInstalled, 'version:', version);

    this.otherAppApi
      .on('install', () => this.log('otherApp is installed'))
      .on('uninstall', () => this.log('otherApp is uninstalled'))
      .on('realtime', (event, data) => this.log('otherApp.onRealtime', event, data));
  }

  async playBell() {
    if (!(await this.otherAppApi.getInstalled())) {
      throw new Error('The other app is not installed');
    }

    const getResponse = await this.otherAppApi.get('/');
    const postResponse = await this.otherAppApi.post('/play', { sound: 'bell' });
    return { getResponse, postResponse };
  }

  async onUninit() {
    this.otherAppApi.unregister();
  }

}

module.exports = App;
```

> **Always check whether the target app is installed and has a compatible version before trying to
> send requests. Failing to do so may cause your app to break unexpectedly when the target app is
> updated.**

Semver-guard version-sensitive calls:

```javascript
const semver = require('semver');   // add it to package.json dependencies

async assertOtherApp(minVersion = '2.0.0') {
  if (!(await this.otherAppApi.getInstalled())) {
    throw new Error('com.athom.otherApp is not installed, enabled or running');
  }
  const version = await this.otherAppApi.getVersion();
  if (!semver.gte(semver.coerce(version), minVersion)) {
    throw new Error(`com.athom.otherApp ${version} is too old, need >=${minVersion}`);
  }
}
```

### `ApiApp` reference

`ApiApp` **extends `Api`**. `this.homey.api.getApiApp(appId)` returns it (the apidoc's return column
says `Api`).

| Method | Signature | Description |
| --- | --- | --- |
| `get` | `(async) get(uri): Promise<any>` | GET, path relative to the app's endpoint. |
| `post` | `(async) post(uri, body): Promise<any>` | POST with body. |
| `put` | `(async) put(uri, body): Promise<any>` | PUT with body. |
| `delete` | `(async) delete(uri): Promise<any>` | DELETE. |
| `getInstalled` | `(async) getInstalled(): Promise<boolean>` | Short-hand for `ManagerApps#getInstalled`. True when the app is **installed, enabled and running**. |
| `getVersion` | `(async) getVersion(): Promise<string>` | Short-hand for `ManagerApps#getVersion`. |
| `unregister` | `unregister()` | Unregister the API. Short-hand for `ManagerApi#unregisterApi`. |

| Event | Fires when |
| --- | --- |
| `.on('install')` | The app is installed, enabled and running (accessible). |
| `.on('uninstall')` | The app is uninstalled, disabled **or crashed** (inaccessible). |
| `.on('realtime')` | A realtime event is received on this URI. Parameters: `event` (string, name), `data` (any, optional). |

`.on(...)` returns the instance, so listeners chain:
`otherApp.on('realtime', …).on('install', …).on('uninstall', …)`.

### `Api` reference (base class)

"This class represents an API endpoint on Homey. When registered, realtime events are fired on the
instance."

| Method | Signature |
| --- | --- |
| `get` | `(async) get(uri): Promise<any>` — path relative to the endpoint |
| `post` | `(async) post(uri, body): Promise<any>` |
| `put` | `(async) put(uri, body): Promise<any>` |
| `delete` | `(async) delete(uri): Promise<any>` |
| `unregister` | `unregister()` — short-hand for `ManagerApi#unregisterApi` |
| `.on('realtime')` | Event; parameters `event` (string), `data` (any, optional) |

### `ManagerApps` (`this.homey.apps`)

The same two checks without holding an `ApiApp` reference of your own:

| Method | Signature | Description |
| --- | --- | --- |
| `getInstalled` | `(async) getInstalled(appInstance: ApiApp): Promise<boolean>` | Check whether an app is installed, enabled and running. |
| `getVersion` | `(async) getVersion(appInstance: ApiApp): Promise<string>` | Get an installed app's version. |

```javascript
const otherApp = this.homey.api.getApiApp('com.athom.otherApp');
const installed = await this.homey.apps.getInstalled(otherApp);
const version = await this.homey.apps.getVersion(otherApp);
```

### TypeScript and Python equivalents

TypeScript — the class is exported from the `homey` module, so type the field:

```ts
// /app.mts
import Homey, { ApiApp } from "homey";

export default class App extends Homey.App {
  otherAppApi!: ApiApp;

  async onInit(): Promise<void> {
    this.otherAppApi = this.homey.api.getApiApp("com.athom.otherApp");

    const isInstalled = await this.otherAppApi.getInstalled();
    const version = await this.otherAppApi.getVersion();

    const getResponse = await this.otherAppApi.get("/");
    const postResponse = await this.otherAppApi.post("/play", { sound: "bell" });

    this.otherAppApi.on("realtime", event => {
      console.log("otherApp.onRealtime", event);
    });
  }
}
```

Python — snake_case methods, and the events are **registered through `on_<event>` methods**, not
through a generic `.on('name', …)`:

```python
# /app.py
from homey import app
from homey.api_app import ApiApp


class App(app.App):
    other_app_api: ApiApp

    async def on_init(self) -> None:
        self.other_app_api = self.homey.api.get_api_app("com.athom.otherApp")

        is_installed = await self.other_app_api.get_installed()
        version = await self.other_app_api.get_version()

        # Make a get request to "otherApp"s API
        get_response = await self.other_app_api.get("/")

        # Post some data to "otherApp", the second argument is the request body
        post_response = await self.other_app_api.post("/play", {"sound": "bell"})

        def on_install():
            print("otherApp is installed")

        self.other_app_api.on_install(on_install)

        def on_uninstall():
            print("otherApp is uninstalled")

        self.other_app_api.on_uninstall(on_uninstall)

        def on_realtime(event, *args):
            print("otherApp.onRealtime", event)

        self.other_app_api.on_realtime(on_realtime)


homey_export = App
```

| JavaScript | Python |
| --- | --- |
| `this.homey.api.getApiApp(appId)` | `self.homey.api.get_api_app(app_id)` |
| `await api.getInstalled()` | `await api.get_installed()` |
| `await api.getVersion()` | `await api.get_version()` |
| `api.get(uri)` / `post(uri, body)` / `put` / `delete` | same names (`get`, `post`, `put`, `delete`) |
| `api.on('install', fn)` | `api.on_install(fn)` |
| `api.on('uninstall', fn)` | `api.on_uninstall(fn)` |
| `api.on('realtime', fn)` | `api.on_realtime(fn)` — the documented handler is `def on_realtime(event, *args)` |
| `await this.homey.api.realtime(event, data)` | `await self.homey.api.realtime(event, data)` |

### Being a good API provider

> "Which APIs and events you can expect is up to the target app, so make sure to check the source
> code, read the documentation or ask the app's developer."

If **your** app is the one being called: document your routes and realtime event names in your README,
treat them as a public contract, keep `path`s stable across versions, and version-tag breaking changes
(a new path, not a changed one) — consumers guard on `getVersion()`.

---

## 9. `ManagerApi` full reference {#managerapi}

Access through `this.homey.api` (and `homey.api` inside API handlers).

| Method | Signature | Description |
| --- | --- | --- |
| `get` | `(async) get(uri): Promise<any>` | Perform a GET request. `uri` is **relative to `/api`**. |
| `post` | `(async) post(uri, body): Promise<any>` | Perform a POST request. |
| `put` | `(async) put(uri, body): Promise<any>` | Perform a PUT request. |
| `delete` | `(async) delete(uri): Promise<any>` | Perform a DELETE request. |
| `realtime` | `(async) realtime(event, data)` | Emit a realtime event. `event`: name, `data`: payload. |
| `getApi` | `getApi(uri): Api` | Create an `Api` instance to receive realtime events. `uri` = the endpoint URI, e.g. `homey:manager:webserver`. |
| `getApiApp` | `getApiApp(appId): Api` | Create an `ApiApp` instance to receive realtime events. `appId` e.g. `com.athom.foo`. |
| `unregisterApi` | `unregisterApi(api)` | Unregister an `Api` instance. |
| `getLocalUrl` | `(async) getLocalUrl(): Promise<string>` | Returns the url for local access. |
| `getOwnerApiToken` | `(async) getOwnerApiToken(): Promise<string>` | Starts a new API session on behalf of the Homey owner and returns the API token. **The token expires after not being used for two weeks.** Requires the `homey:manager:api` permission. |

Only `getOwnerApiToken` is *documented* as requiring `homey:manager:api`; `get`/`post`/`put`/`delete`
hit **Homey's own Web API** (the thing the permission description covers: "the ManagerApi methods to
communicate with the Homey Web API"), so treat them as requiring it too. `realtime`, `getApiApp`,
`unregisterApi` and `getLocalUrl` are what a normal app uses without the permission.

---

## 10. Using the Homey Web API from inside an app (`homey:manager:api`) {#homey-web-api}

```jsonc
// /.homeycompose/app.json
{ "permissions": ["homey:manager:api"] }
```

| Fact | Detail |
| --- | --- |
| What it unlocks | "Allows an app to use the ManagerApi methods to communicate with the Homey Web API" — control over **all** devices, Flows, etc., even those belonging to other apps. |
| Who may request it | Only apps whose *main functionality* requires it — i.e. **Tools**-category apps. Documented examples: a DIY Home Alarm system, HomeyScript, Device Groups. |
| Who may not | Apps that connect to a physical device (branded lightbulb/thermostat apps). Those submissions are **rejected**. |
| Review | "Apps that request the API permission will be reviewed more carefully when published to the App Store." The CLI warns at publish level: *"using the homey:manager:api permission will require a more thorough review. It may take longer than usual to review your app."* |
| Homey Cloud | **Not allowed.** |
| Runtime check | `this.homey.hasPermission('homey:manager:api')` |

### Raw calls with `this.homey.api`

`uri` is relative to `/api`, and Homey's own endpoints live under `/api/manager/<managerId>/…`, so:

```javascript
// GET /api/manager/system/
const system = await this.homey.api.get('/manager/system/');

// GET /api/manager/devices/device       (all devices)
const devices = await this.homey.api.get('/manager/devices/device');

// PUT /api/manager/devices/device/:id   (rename a device)
await this.homey.api.put(`/manager/devices/device/${id}`, { name: 'New name' });
```

Complete list of manager ids on the Homey Web API (URI `homey:manager:<id>`, path
`/api/manager/<id>/…`):

`alarms`, `api`, `apps`, `arp`, `backup`, `ble`, `clock`, `cloud`, `coprocessor`, `cron`,
`dashboards`, `database`, `devices`, `devkit`, `discovery`, `drivers`, `energy`, `energydongle`,
`experiments`, `flow`, `flowtoken`, `geolocation`, `google-assistant`, `i18n`, `icons`, `images`,
`insights`, `ledring`, `logic`, `matter`, `mobile`, `moods`, `notifications`, `presence`, `rf`,
`safety`, `satellites`, `security`, `sessions`, `system`, `thread`, `updates`, `users`, `vdevice`,
`videos`, `weather`, `webserver`, `zigbee`, `zones`, `zwave`.

(These are the Homey **Web API** managers — a superset of the Apps SDK managers; e.g. `cron` exists
on the Web API even though the Apps SDK has no `ManagerCron`.)

(Example operations on `devices`: `GET /device`, `GET /device/:id`, `PUT /device/:id`,
`DELETE /device/:id`, `GET /device/:deviceId/capability/:capabilityId`, `PUT /device/:id/settings`,
`GET /state`.)

Explore the exact operation set with the CLI rather than guessing:

```bash
homey api schema                                 # every manager + its operations
homey api schema --json --jq '.managers | keys'
```

---

## 11. `homey-api` (HomeyAPI) inside an app {#homey-api-package}

For anything beyond one-off requests, use Athom's official client instead of hand-rolling paths. It
is the npm package **`homey-api`** (repo `athombv/node-homey-api`; the Homey CLI itself depends on it).

```bash
npm install homey-api          # add it to the app's package.json dependencies
```

```javascript
// /app.js — requires the homey:manager:api permission
'use strict';

const Homey = require('homey');
const { HomeyAPI } = require('homey-api');

class App extends Homey.App {

  async onInit() {
    this.homeyApi = await HomeyAPI.createAppAPI({
      homey: this.homey,
      // debug: true,   // logs through homey.app.log('[homey-api]', …)
    });

    // Get all the devices, and log their names
    const devices = await this.homeyApi.devices.getDevices();
    for (const device of Object.values(devices)) {
      this.log(device.name);
    }

    // Realtime: subscribe to a manager's Socket.io namespace, then listen
    await this.homeyApi.devices.connect();
    this.homeyApi.devices.on('device.update', (device) => {
      this.log('device.update', device.id, device.name);
    });

    // Follow a single capability of a single device
    const device = await this.homeyApi.devices.getDevice({ id: '<device-uuid>' });
    this.onoffInstance = device.makeCapabilityInstance('onoff', (value) => {
      this.log('onoff changed to', value);
    });
    await this.onoffInstance.setValue(true);
  }

  async onUninit() {
    this.homeyApi.destroy();     // disconnects sockets and clears caches
  }

}

module.exports = App;
```

| API | Purpose |
| --- | --- |
| `HomeyAPI.createAppAPI({ homey, debug })` | **In-app** factory. Internally calls `homey.api.getOwnerApiToken()` + `homey.api.getLocalUrl()` + `homey.cloud.getHomeyId()` and returns a `HomeyAPIV2` (`platform: 'local'`, `platformVersion: 1`), `HomeyAPIV3Local` (`local`/`2`) or `HomeyAPIV3Cloud` (`cloud`/`2`) instance. Throws `Invalid Homey` without a `homey` instance and `Invalid Homey Platform Version: <n>` for any other combination. `debug` is a **function** (`null` by default); the literal `true` is special-cased into `(...props) => homey.app.log('[homey-api]', ...props)`. |
| `HomeyAPI.createLocalAPI({ address, token, debug })` | **External** projects: `address` e.g. `http://192.168.1.123`, `token` = a Personal Access Token created in the Homey Web App. Throws `Invalid Address` / `Invalid Token` when either is missing, and `No Homey Found At Address: <address>` when `GET <address>/api/manager/system/ping` comes back without an `X-Homey-ID` header. Always returns a `HomeyAPIV3Local`. |
| `homeyApi.<manager>` | Lazily-created manager properties: `devices`, `flow`, `zones`, `apps`, `drivers`, `insights`, `users`, `flowtoken`, … — one per manager in the table above, but named with the manager's **`idCamelCase`**, so the hyphenated id `google-assistant` is reached as `homeyApi.googleAssistant`. |
| `manager.connect()` / `disconnect()` / `isConnected()` | Join/leave the manager's realtime namespace. |
| `manager.on('<item>.create'\|'.update'\|'.delete', item)` | CRUD realtime events, e.g. `device.create`, `device.update`, `device.delete`. |
| `device.makeCapabilityInstance(capabilityId, listener)` | Realtime capability updates; the returned instance has `setValue(value)`. |
| `device.setCapabilityValue({ capabilityId, value, opts })` | Set a capability (legacy positional form `setCapabilityValue(capabilityId, value, opts)` still works). |
| `homeyApi.hasRole(roleId)` | Role of the session user: `owner`, `manager`, `user` or `guest`. |
| `homeyApi.destroy()` | Tear everything down — call it in `onUninit()`. |

Requests are sent as `<baseUrl>/api/manager/<managerId>/<path>` with `Authorization: Bearer <token>`
and `X-Homey-ID`.

**Gotcha (Node 22):** with older versions of the client you can hit
`RangeError: Maximum call stack size exceeded` when the socket closes, because socket.io uses native
Node sockets that changed behaviour in Node 22. **Update `homey-api` to 3.14.17 or newer.**

---

## 12. Homey Cloud restrictions {#cloud}

| Feature | Homey Pro / Self-Hosted | Homey Cloud |
| --- | --- | --- |
| App Web API (`api` manifest block + `/api.js`) | yes | **no** — "Apps on Homey Cloud are not allowed to expose a Web API." |
| `homey:manager:api` / `ManagerApi` HTTP methods | yes (heavily reviewed) | **no** |
| App-to-app (`homey:app:<appId>`, `getApiApp`) | yes | **no** |
| Custom app settings views (a main consumer of the Web API) | yes | **no** |
| Widgets (and therefore widget APIs) | yes — "Widgets do not work on Homey Cloud and require a compatibility of `>=12.3.0`" | **no** |
| Webhooks (`ManagerCloud#createWebhook`) | yes | **yes** — the documented replacement for inbound HTTP on Cloud |
| `ManagerCloud#getLocalAddress()` | yes | **no** |

> "Homey Cloud does not have support for App Web APIs. While this means that you cannot expose a
> complete REST API you can still receive Webhook updates."

Consequences for a `"platforms": ["local", "cloud"]` app:

- Never make core functionality depend on `/api.js`, `getApiApp()` or `this.homey.api.get/post/...`.
- Move inbound cloud traffic to **webhooks** (`references/cloud-oauth-webhooks.md`) and user input to
  **pairing / repair views** (`references/pairing.md`).
- Multi-tenancy applies to API handlers too: no mutable module-scope globals (several app instances
  share one Node.js process), always `homey.setTimeout`/`setInterval`, and always `.catch(this.error)`
  — unhandled promise rejections crash the app on Cloud. See `references/homey-cloud.md`.

---

## 13. Gotchas {#gotchas}

**Manifest & files**

- **SDK v3 no longer infers routes from `api.js`.** A handler that is not listed in the manifest's
  `api` object has no URL at all — the endpoint simply does not exist, and nothing warns you.
- **The app-level `api` block is not schema-validated.** `homey-lib`'s `app.json` JSON schema has no
  top-level `api` property (and the manifest allows unknown top-level keys), so `homey app validate`
  will **not** catch a misspelled `"methdo"`, a lowercase method or a route whose handler does not
  exist — it fails at runtime instead. Widget `api` blocks *are* validated: both `method` and `path`
  are `required`, and `method` is a single uppercase string from `GET|POST|PUT|DELETE` (so the
  app-level array form is invalid inside a widget).
- **The route key is the handler name, not the URL.** `"getSomething"` is a function name; the URL
  comes from `path`.
- **`/api.js` ≠ `/widgets/<id>/api.js`.** The widget file only serves that widget's webview and is
  declared in `widget.compose.json`; the app file is the external REST + realtime surface declared in
  the App Manifest. Same handler signature, different scope.
- **Explicit-extension api files need compatibility.** The presence of `api.mjs` *or* `api.cjs`
  (app-level and widget-level) requires `"compatibility": ">=12.0.1"`, otherwise validation throws
  `ESM apps require a compatibility of at least >=12.0.1. (<path>)`. Plain `api.js` is unaffected.
- **`GET` and `DELETE` arrive with an empty body** when called through `Homey.api` — put everything in
  `path` params or `query`.

**Permissions**

- **You do not need `homey:manager:api` to expose your own Web API.** That permission is only for
  *calling* Homey's Web API (controlling other apps' devices/Flows) — i.e. `this.homey.api.get/post/
  put/delete` and `getOwnerApiToken()`. Requesting it "just in case" gets the submission rejected.
- **App-to-app needs one `homey:app:<appId>` entry per target app**, and **apps do not auto-update
  when permissions change** — existing installs stay on the previous version until the user updates
  manually, so treat added permissions as a soft breaking change.
- `homey:app:com.athom.homeyscript` is forbidden and fails validation outright.
- **`getOwnerApiToken()` tokens expire after two weeks of non-use.** Do not cache one in
  settings/userdata and assume it lives forever — request a fresh one when a call fails with an auth
  error.

**Runtime**

- **Always guard app-to-app calls** with `getInstalled()` (true only when installed **and** enabled
  **and** running) plus a `getVersion()` check. The `uninstall` event also fires when the other app is
  merely **disabled or crashed**, so treat it as "temporarily unavailable", not "gone forever".
- **`unregister()` your `Api`/`ApiApp` instances in `onUninit()`** — the SDK's un-init hooks exist so
  an app instance releases its resources; a dangling registration keeps firing events at a dead
  instance.
- **Realtime is one-way and unacknowledged.** Nothing tells you whether a settings page or widget was
  listening. Never treat `realtime()` as a transport for state that the client cannot also fetch: have
  the client `Homey.api('GET', …)` once on load, then patch with realtime events.
- **Payloads must be JSON-stringifiable** (`'my_json_stringifyable_value'`). No `Date` semantics, no
  class instances, no `Buffer`.
- **Realtime handler arity differs between the apidoc's parameter table and every example** — the
  table documents `(event, data)`; the `ApiApp` apidoc example and the Web API guide example both
  take a single argument. No source shows object-destructuring (`({ event, data }) => …`) — do not
  write that. Use the defensive handler shown in [§7](#realtime).
- **`ManagerApi` itself has no documented events.** Use `getApi(uri)` / `getApiApp(appId)` instances to
  *receive* realtime.
- **`Homey.api` is callback-style in settings views and promise-style in widgets.** Promisify the
  settings one yourself rather than `await`ing it blindly.
- **Only `public: true` endpoints work without a token**, and the docs limit them to cases with no
  alternative (their example: sending a pin-code from another device to Homey). A public endpoint is
  reachable by anything that can reach the Homey — validate and rate-limit inside the handler.
- **Editing `api.js` requires a full app restart.** The `homey app run` refresh button only reloads
  files under a widget's `public/` folder ("For other file changes, a full restart is required"). That
  button also needs Docker, works only on **Homey 2023 and later**, and is **not available with
  `homey app run --remote`**.
- **`homey app run` runs your app in a Docker container on `NetworkMode: bridge` by default.** The CLI
  exposes it as `--network`/`-n` (`homey app run -n host`, "Must match name from `docker network ls`").
  Anything that depends on reaching the app from another machine on the LAN therefore behaves
  differently than under `homey app install`. Test external clients of your Web API with `install`.

---

## 14. Sources {#sources}

- <https://apps.developer.homey.app/advanced/web-api> — Web API, realtime events, app-to-app
- <https://apps.developer.homey.app/the-basics/app/permissions> — `homey:manager:api`, `homey:app:<appId>`
- <https://apps.developer.homey.app/advanced/custom-views/app-settings> — settings-view `Homey.api`, `Homey.on`
- <https://apps.developer.homey.app/the-basics/widgets> — widget `api` block, widget view API
- <https://apps.developer.homey.app/guides/homey-cloud> — Cloud restrictions on Web API and app-to-app
- <https://apps.developer.homey.app/upgrade-guides/upgrading-to-sdk-v3> — routes moved to the manifest
- <https://apps.developer.homey.app/upgrade-guides/node-22> — `homey-api` 3.14.17+ on Node 22
- <https://apps.developer.homey.app/the-basics/getting-started/homey-cli> — `homey api raw`, `homey api schema`
- <https://apps-sdk-v3.developer.homey.app/ManagerApi.html> — `ManagerApi`
- <https://apps-sdk-v3.developer.homey.app/Api.html> — `Api`
- <https://apps-sdk-v3.developer.homey.app/ApiApp.html> — `ApiApp`
- <https://apps-sdk-v3.developer.homey.app/ManagerApps.html> — `getInstalled`, `getVersion`
- <https://athombv.github.io/node-homey-api/HomeyAPI.html> — `HomeyAPI.createAppAPI` / `createLocalAPI`

Verified against the published npm packages (facts the prose docs do not state):

- `homey-lib@2.51.4` — `assets/app/schema.json` (no top-level `api` property; widget `api` requires
  uppercase-string `method` + `path`), `lib/App/index.js` (`checkEsm` on `api.mjs`/`api.cjs`,
  forbidden `homey:app:com.athom.homeyscript`, the `homey:manager:api` publish warning)
- `homey@4.4.1` — `bin/cmds/api/raw.mjs` + `lib/api/ApiCommandOptions.mjs` (`homey api raw` options,
  `--body` POST/PUT-only, `DEFAULT_TIMEOUT = 30 * 1000`), `bin/cmds/app/run.mjs`
  (`--network` default `bridge`)
- `homey-api@3.19.2` — `lib/HomeyAPI/HomeyAPI.js` (`createAppAPI`/`createLocalAPI`/`hasRole`),
  `assets/specifications/HomeyAPIV3Local.json` (the 50 manager ids and their operations)
