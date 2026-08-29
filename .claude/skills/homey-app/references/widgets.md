# Dashboard Widgets

Homey Apps can ship custom **widgets**: plain web pages (HTML/CSS/JS) rendered on the user's dashboard, with access to a global injected `Homey` object for talking back to your app. This file covers the widget folder layout, `widget.compose.json`, the `index.html` frontend contract, the widget-scoped `api.js`, widget settings (including the device picker and autocomplete listeners), the complete Homey CSS style library, preview images, and debugging.

Related: `references/app-and-manifest.md` (manifest, compatibility, permissions), `references/drivers-and-devices.md` (device settings, Insights), `references/advanced-features.md` (Web API, custom views), `references/publishing.md` (App Store guidelines), `references/cli-and-tooling.md` (CLI).

---

## 1. Platform requirements and limits

| Constraint | Value |
| --- | --- |
| App `compatibility` | `>=12.3.0` (widget support was added in that release) |
| Homey Cloud | **Not supported** — widgets do not work on Homey Cloud |
| Live reload during `homey app run` | Requires Docker; `homey app run` enforces Docker usage |
| Live reload — supported hardware | Homey 2023 and later models only |
| Live reload on pre-2023 models | Not available |
| Live reload with `homey app run --remote` | Not available |

The documented gate on widgets is the app's `compatibility`, **not** a hardware model — "Homey 2023 and later" is documented only for the live-reload refresh button. Set `"compatibility": ">=12.3.0"` and let that decide where the app installs.

Field note (from `homey-lib`'s validator, not the docs): the presence of `widgets` is rejected below `>=12.1.0`, the `transparent` key is rejected below `>=12.1.0`, and the `deprecated` and `devices` keys are each rejected below `>=12.3.0`. `>=12.3.0` is the safe value for everything on this page.

Widths are fixed by the dashboard column — a widget cannot set its own width. Only height and background are under your control (see [§4](#4-sizing-height-and-width) and [§8](#8-styling)).

---

## 2. Creating a widget

```bash
homey app widget create
```

Interactive wizard: prompts for the widget's **name** and **ID**, then scaffolds `/widgets/<widgetId>/` with the HTML/CSS/JS files, `widget.compose.json` and the light/dark preview images. The documented file list is `widget.compose.json`, `public/index.html`, `api.js`, `preview-dark.png` and `preview-light.png`.

```
/widgets/
└── <widgetId>/                  # the folder name is the widget id
    ├── widget.compose.json      # widget definition
    ├── api.js                   # widget-scoped API implementation (api.mts for TS, api.py for Python)
    ├── public/
    │   └── index.html           # entry point; everything under public/ is hosted on Homey
    ├── preview-light.png        # 1024x1024 preview, light mode
    └── preview-dark.png         # 1024x1024 preview, dark mode
```

Field notes on the wizard (from the CLI implementation):

- It requires **Homey Compose**. In a non-Compose app it offers to run the migration first, otherwise it aborts with `This command requires Homey compose, run 'homey app compose' to migrate!`.
- The ID defaults to the name lowercased with spaces replaced by `-`, and only accepts letters, numbers, minus (`-`) and underscore (`_`). An existing `/widgets/<id>/` directory is rejected.
- The scaffolded `widget.compose.json` starts with `"height": 188`, an empty `"settings": []` and the four `getSomething` / `addSomething` / `updateSomething` / `deleteSomething` routes.

**`<widgetId>` is the folder name.** That same string is what you pass to `this.homey.dashboards.getWidget('<widgetId>')`. The documented `widget.compose.json` examples contain no `id` key — Compose derives it from the folder name and writes it into `app.json`, where the schema requires it. See the [Gotchas](#11-gotchas).

Everything under `public/` is hosted on the user's Homey, so put every asset referenced from `index.html` (SVG icons, CSS, JS) there.

---

## 3. `widget.compose.json`

Example showing every documented top-level key (the docs' own example shows only `name`, `settings`, `height` and `api`; `transparent`, `deprecated` and `devices` are documented in prose and in the settings page):

```json
{
  "name": {
    "en": "My Widget"
  },
  "settings": [
    {
      "id": "my-id",
      "type": "text",
      "title": {
        "en": "My Title"
      }
    }
  ],
  "height": 100,
  "transparent": false,
  "deprecated": false,
  "devices": {
    "type": "global",
    "singular": false,
    "filter": {
      "class": "socket",
      "capabilities": "onoff"
    }
  },
  "api": {
    "getSomething": {
      "method": "GET",
      "path": "/"
    },
    "addSomething": {
      "method": "POST",
      "path": "/"
    },
    "updateSomething": {
      "method": "PUT",
      "path": "/:id"
    },
    "deleteSomething": {
      "method": "DELETE",
      "path": "/:id"
    }
  }
}
```

### 3.1. Top-level keys

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | i18n object | **yes** | Widget name. Becomes the default title above the widget on the dashboard. The user may rename it or hide the title entirely. |
| `id` | `string` | **yes, in `app.json`** | The widget id. **Do not write it in `widget.compose.json`** — Homey Compose sets `widgets.<id>.id` to the widget's folder name while building `app.json`. Only a hand-written (non-Compose) `app.json` has to spell it out. |
| `settings` | array | no | Settings the user can change while selecting or editing a widget instance. Compose defaults it to `[]` when the key is absent. See [§7](#7-widget-settings). |
| `height` | `number` \| percentage string | no | Initial height on load. A number is an absolute pixel value; a percentage is an aspect ratio (`"100%"` = square). See [§4](#4-sizing-height-and-width). |
| `transparent` | `boolean` | no | Default `false` (opaque background using `--homey-background-color`). `true` makes the widget background fully transparent. |
| `deprecated` | `boolean` | no | `true` prevents users from selecting the widget when adding new ones; existing instances remain functional. |
| `devices` | object | no | Dedicated device-picker configuration (top-level, **not** a `settings` entry). Its own `type` and `singular` are both required. See [§7.8](#78-devices-device-picker). |
| `api` | object | no | Specification of the widget's API. **Scoped to the widget, not global.** See [§6](#6-apijs--the-widget-scoped-api). |

That is the complete set of keys in the validator schema (`app.json` → `widgets.<widgetId>`); there are no others.

Schema notes (the app manifest schema outranks the prose docs where they differ):

- **`id` is required by the schema but absent from every documented `widget.compose.json` example.** Both statements are true because they describe different files: the schema validates the *built* `app.json`, and Compose injects `id` from the folder name. See the [Gotchas](#11-gotchas).
- **`settings` is typed only as `array`** — the schema does not validate the individual setting entries at all. The six types in [§7](#7-widget-settings) come from the documentation, not from a schema constraint, so `homey app validate` passing is *not* evidence that a setting entry is well formed.
- The per-widget object does **not** set `additionalProperties: false`, so an unrecognised key inside a widget survives validation silently. Do not read "it validates" as "it is supported".

### 3.2. `api` route options

Each key of `api` is the **name of a function** exported from `api.js`. A widget route takes exactly two options, both **required**:

| Key | Type | Value |
| --- | --- | --- |
| `method` | `String` | Exactly one of `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`. |
| `path` | `String` | For example `"/"`, `"/:foo"`, `"/bar/:foo"`. Path segments prefixed with `:` become `params`. |

Differences from the **app** Web API route options (`/.homeycompose/app.json` → `api`), which are a similar but *not* identical shape:

- The app route `method` may also be an **array** of methods; the widget schema types `method` as a single string enum, so `"method": ["GET", "POST"]` is invalid in `widget.compose.json`. Declare one route per method.
- The app route option `public: true` (unauthenticated access) is **not** part of the widget route schema — widget endpoints are always reached through the widget's own `Homey.api()`.
- Both `method` and `path` are required on a widget route; the schema defines no other keys. It does not set `additionalProperties: false` on the route object either, so a stray `"public": true` is not *rejected* by `homey app validate` — it is simply ignored at runtime, which is the more dangerous failure mode.

---

## 4. Sizing: height and width

The widget always fills the **width** of the dashboard column it is placed in. `height` is the only sizing lever, and it has two distinct meanings:

| `height` value | Meaning | Example |
| --- | --- | --- |
| `number` | Absolute pixels | `"height": 200` → 200 px tall |
| percentage string | **Aspect ratio** — height relative to the widget's width | `"height": "100%"` → square widget; `"height": "50%"` → half as tall as wide |

Runtime overrides:

```javascript
Homey.ready({ height: 200 });   // overrides the height from widget.compose.json
Homey.setHeight(240);           // change height later; returns a Promise
Homey.setHeight('100%');        // aspect ratio at runtime
Homey.setHeight(null);          // clear the runtime height
```

Rules:

- It is **not advised** to set the height in both `widget.compose.json` and at runtime — that causes height shifts during load.
- After the first load, the height is **cached**, so subsequent loads have no layout shift. Prefer a stable height.

---

## 5. The frontend: `/widgets/<widgetId>/public/index.html`

`index.html` is the entry point and is loaded as soon as a user's dashboard requests your widget.

The page must define a **global function `onHomeyReady(Homey)`**. Homey calls it with the injected `Homey` instance. On initial load a loading state is shown; it is removed when you call `Homey.ready()` — so use the time before that call for initialization.

```html
<html>

<head>
...
</head>

<body>
  <div id="message"></div>
  <button id="my-button">Button</button>

  <script type="text/javascript">
    function onHomeyReady(Homey) {
      Homey.ready({ height: 200 });

      console.log('instanceId: ', Homey.getWidgetInstanceId());
      console.log('settings', Homey.getSettings());

      document.getElementById('my-button').addEventListener('click', () => {
        Homey.api('GET', '/', {})
          .then((result) => {
            document.getElementById('message').innerText = String(result);
          })
          .catch(console.error);
      });
    }
  </script>
</body>

</html>
```

### 5.1. View API — complete reference

Every method documented on the injected `Homey` object:

| Method | Signature | Purpose |
| --- | --- | --- |
| `Homey.ready` | `ready(args?: { height: number \| string }): void` | Call when your widget is ready to be shown; removes the loading state. The optional `height` overrides `widget.compose.json`. |
| `Homey.api` | `api(method: string, path: string, body?: object): Promise<unknown>` | Access your API as defined under `widget.compose.json` → `api`. |
| `Homey.on` | `on(event: string, callback: (...args[]: any) => void): void` | Listen to events emitted by your app. |
| `Homey.__` | `__(input: string, tokens?: object): string` | Translate a string programmatically. `input` is the name in `/locales/__language__.json`; use dots for sub-properties (e.g. `settings.title`). `tokens` is an object with replacers. |
| `Homey.getWidgetInstanceId` | `getWidgetInstanceId(): string` | Unique id for this instance of the widget. |
| `Homey.getSettings` | `getSettings(): { [key: string]: unknown }` | Get the settings for your widget as filled in by the user. **Synchronous.** |
| `Homey.setHeight` | `setHeight(height: number \| string \| null): Promise<void>` | Change the widget height during runtime. |
| `Homey.popup` | `popup(url: string): Promise<void>` | Open an in-app browser view. |
| `Homey.hapticFeedback` | `hapticFeedback(): void` | Provide haptic feedback on presses. **Only callable in a short window after a touch event.** |
| `Homey.getDeviceIds` | `getDeviceIds(): string[]` | IDs of the devices the user selected in the widget's `devices` setting. See [§7.8](#78-devices-device-picker). |

That list is the complete documented widget View API. Do **not** assume the custom-views / app-settings `Homey` API is available here — that is a different, callback-based surface (`Homey.get`, `Homey.set`, `Homey.unset`, `Homey.alert`, `Homey.confirm`, `Homey.openURL`), and widget styling and behaviour are explicitly documented as *not* the same as for custom views.

### 5.2. Widget instance id

Each time a user adds a widget to a dashboard, a unique id is generated. Read it with `Homey.getWidgetInstanceId()`. Typical use: key per-instance data stored on the app side.

```javascript
function onHomeyReady(Homey) {
  const instanceId = Homey.getWidgetInstanceId();
  Homey.api('GET', `/?instanceId=${encodeURIComponent(instanceId)}`)
    .then((state) => { /* render */ })
    .catch(console.error);
  Homey.ready();
}
```

### 5.3. Receiving events from the app (`Homey.on`)

`Homey.on(event, callback)` listens to events emitted by your app. On the app side, realtime events are emitted with the Web API realtime call:

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.homey.setInterval(() => {
      this.homey.api.realtime('status_update', { status: 'ok', t: Date.now() })
        .catch(this.error);
    }, 60 * 1000);
  }

}

module.exports = MyApp;
```

```javascript
// public/index.html
function onHomeyReady(Homey) {
  Homey.on('status_update', (data) => {
    document.getElementById('status').innerText = String(data.status);
  });
  Homey.ready();
}
```

### 5.4. Translations

Translations work the same as for custom pairing views and custom app settings views: declarative via the `data-i18n` attribute, or programmatically via `Homey.__()`.

```json
// /locales/en.json
{
  "widget": {
    "title": "My Title",
    "intro": "This is an example page."
  }
}
```

```html
<h1 data-i18n="widget.title"><!-- "My Title" will be placed here --></h1>
<p data-i18n="widget.intro"><!-- "This is an example page." will be placed here --></p>

<script type="text/javascript">
  function onHomeyReady(Homey) {
    console.log(Homey.__('widget.title'));
    Homey.ready();
  }
</script>
```

---

## 6. `api.js` — the widget-scoped API

`api.js` contains the implementation of the API declared in `widget.compose.json` → `api`. It exports **async functions whose names match the keys** in that block. As with the app-level Web API, you have access to the `homey` instance of your app.

```javascript
'use strict';

module.exports = {
  async getSomething({ homey, query }) {
    // you can access query parameters like "/?foo=bar" through `query.foo`

    // you can access the App instance through homey.app
    // const result = await homey.app.getSomething();
    // return result;

    // perform other logic like mapping result data

    return 'Hello from App';
  },

  async addSomething({ homey, body }) {
    // access the post body and perform some action on it.
    return homey.app.addSomething(body);
  },

  async updateSomething({ homey, params, body }) {
    return homey.app.setSomething(body);
  },

  async deleteSomething({ homey, params }) {
    return homey.app.deleteSomething(params.id);
  },
};
```

### 6.1. Handler argument

Every handler receives a single object with four properties:

| Property | Description |
| --- | --- |
| `homey` | The Homey instance. Reach your App instance through `homey.app`. |
| `body` | Object with the request body, for `POST` and `PUT`. JSON is automatically parsed. |
| `params` | The set of strings defined in your `path` (e.g. `/:id` → `params.id`). |
| `query` | The set of strings provided as query parameters, e.g. `?foo=bar` → `{ "foo": "bar" }`. |

`Homey.api` sends an **empty body** for `GET` and `DELETE` requests.

### 6.2. `Homey.api(...)` → handler mapping

`Homey.api()` takes a **method and path**, not a handler name. Homey resolves the pair against the `api` map:

| Frontend call | Matched `api` entry | Handler invoked | Handler sees |
| --- | --- | --- | --- |
| `Homey.api('GET', '/', {})` | `{"method":"GET","path":"/"}` | `getSomething` | `query`, `params` (empty) |
| `Homey.api('GET', '/?foo=bar')` | `{"method":"GET","path":"/"}` | `getSomething` | `query.foo === 'bar'` |
| `Homey.api('POST', '/', { a: 1 })` | `{"method":"POST","path":"/"}` | `addSomething` | `body.a === 1` |
| `Homey.api('PUT', '/42', { a: 1 })` | `{"method":"PUT","path":"/:id"}` | `updateSomething` | `params.id === '42'`, `body` |
| `Homey.api('DELETE', '/42')` | `{"method":"DELETE","path":"/:id"}` | `deleteSomething` | `params.id === '42'` |

`Homey.api()` returns a **Promise** (unlike the callback-style `Homey.api()` of app settings views).

### 6.3. TypeScript (`api.mts`)

```typescript
import type App from "../../app.mjs";

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
    return "Hello from App";
  },

  async addSomething({ homey, body }: RequestWithBody): Promise<any> {
    return (homey.app as App).addSomething(body);
  },

  async updateSomething({ homey, params, body }: RequestWithBody): Promise<any> {
    return (homey.app as App).updateSomething(body);
  },

  async deleteSomething({ homey, params }: RequestWithoutBody): Promise<any> {
    return (homey.app as App).deleteSomething(params.id);
  },
};
```

### 6.4. Python (`api.py`)

Python apps (`"runtime": "python"`, `compatibility >=13.0.0`) use module-level **keyword-only** async functions and export the endpoint names through `__all__`. All four properties are always passed as keyword arguments — `homey`, `query`, `params`, `body`:

```python
from typing import Any, Never, cast

from homey.homey import Homey

from ...app import App


async def get_something(
    *,
    homey: Homey,
    query: dict[str, str],
    params: dict[str, str],
    body: dict[Never, Never],  # Homey.API sends an empty body for GET requests
) -> Any:
    return "Hello from App"


async def add_something(
    *, homey: Homey, query: dict[str, str], params: dict[str, str], body: dict[str, Any]
) -> Any:
    return cast(App, homey.app).add_something(body)


async def delete_something(
    *,
    homey: Homey,
    query: dict[str, str],
    params: dict[str, str],
    body: dict[Never, Never],  # Homey.API sends an empty body for DELETE requests
) -> Any:
    return cast(App, homey.app).delete_something(params["id"])


# Export all these methods as endpoints
__all__ = ["get_something", "add_something", "delete_something"]
```

The `api` keys in `widget.compose.json` must match the Python function names (`"get_something"`, not `"getSomething"`). The import of the app is relative to the widget folder: `from ...app import App`.

---

## 7. Widget settings

Settings live in the `settings` array of `widget.compose.json` and are edited by the user while selecting or editing a widget instance. They work almost the same as [device settings](./drivers-and-devices.md), but the documented widget set is the six types below plus the separate top-level `devices` key.

```json
{
  "name": { "en": "My Widget" },
  "settings": [
    {
      "id": "text",
      "type": "text",
      "title": { "en": "Text" },
      "hint": { "en": "Your number" }
    },
    {
      "id": "number",
      "type": "number",
      "title": { "en": "Number" },
      "hint": { "en": "Your number" }
    }
  ]
}
```

Every setting has a `type` that determines what values it can hold and how it is presented. The `value` property is the **initial** value.

| Type | Value type | Extra properties |
| --- | --- | --- |
| `text` | `string \| null` | `pattern` (regex validation) |
| `textarea` | `string \| null` | `pattern` (regex validation) |
| `number` | `number \| null` | `min`, `max` |
| `dropdown` | `string \| null` | `values: [{ id, title }]` |
| `checkbox` | `boolean \| null` | — |
| `autocomplete` | `object \| null` | requires a runtime listener, see [§7.7](#77-autocomplete-listeners) |

Common properties on every setting: `id`, `type`, `title` (i18n), `hint` (i18n), `value` (initial value).

Field note: Homey Compose's locale merge (`/.homeycompose/locales/<lang>.json` → `$widgets.<widgetId>.settings.<settingId>`) recognises `title` **and** `placeholder` for a widget setting, so `placeholder` is accepted even though the settings page does not list it. `title` and `hint` are the only ones the docs guarantee.

### 7.1. Text

`string | null` — single-line text input. Optionally validate with a regex `pattern`.

```json
{
  "id": "text",
  "type": "text",
  "title": { "en": "Text" },
  "value": "My initial value",
  "hint": { "en": "My text hint." },
  "pattern": "[a-zA-Z]"
}
```

### 7.2. Textarea

`string | null` — multi-line text input.

```json
{
  "id": "description",
  "type": "textarea",
  "title": { "en": "Textarea" },
  "value": "Enter your description here.",
  "hint": { "en": "Provide a detailed description." },
  "pattern": "[a-zA-Z]"
}
```

### 7.3. Number

`number | null` — numerical input. `min` and `max` are optional and define the acceptable range.

```json
{
  "id": "age",
  "type": "number",
  "title": { "en": "Age" },
  "value": 25,
  "hint": { "en": "Your age." },
  "min": 0,
  "max": 120
}
```

### 7.4. Dropdown

`string | null` — select one value from a predefined list.

```json
{
  "id": "dropdown",
  "type": "dropdown",
  "title": { "en": "Dropdown", "nl": "Dropdown" },
  "value": "heating",
  "values": [
    { "id": "heating", "title": { "en": "Heating" } },
    { "id": "cooling", "title": { "en": "Cooling" } }
  ]
}
```

### 7.5. Checkbox

`boolean | null` — enable or disable a feature.

```json
{
  "id": "checkbox",
  "type": "checkbox",
  "value": true,
  "title": { "en": "Checkbox", "nl": "Checkbox" }
}
```

### 7.6. Autocomplete

`object | null` — an input that suggests options as the user types. The manifest entry is minimal; the options come from a listener registered at runtime.

```json
{
  "id": "composer",
  "type": "autocomplete",
  "title": { "en": "Composer" }
}
```

### 7.7. Autocomplete listeners

Register the listener from your app's `onInit()`, via `ManagerDashboards` (`this.homey.dashboards`).

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const widget = this.homey.dashboards.getWidget('my-widget')

    widget.registerSettingAutocompleteListener('composer', async (query, settings) => {
      return [
        {
          name: "Mozart",
          // Optionally provide the following properties.
          description: "...",
          image: "https://some.url/",

          // You can freely add additional properties
          // that you can access in Homey.getSettings()['mySettingId'].
          id: "mozart",
        },
        {
          name: "Amadeus",

          // You can freely add additional properties
          // that you can access in Homey.getSettings()['mySettingId'].
          id: "amadeus",
        },
      ].filter((item) => item.name.toLowerCase().includes(query.toLowerCase()));
    });
  }
}

module.exports = MyApp;
```

**API surface.** `ManagerDashboards`, `Widget` and `WidgetSetting` have no pages on the JS API-reference site; the shape below is taken from the Python SDK reference, with the JS spellings (camelCase) shown first and the Python spellings (snake_case) alongside:

| Call | Python spelling | Returns | Notes |
| --- | --- | --- | --- |
| `this.homey.dashboards.getWidget(id)` | `self.homey.dashboards.get_widget(id)` | `Widget` | Get the widget with the given ID, as defined in `app.json`. Raises `NotFound`. |
| `widget.registerSettingAutocompleteListener(id, listener)` | `widget.register_setting_autocomplete_listener(id, listener)` | the `Widget` (`Self`, chainable) | Register an autocomplete listener for the setting with the given `id`. Raises `AlreadyExists` if a listener is already registered for the setting; `NotFound` if no setting with that id exists. |
| `widget.getSetting(id)` | `widget.get_setting(id)` | `WidgetSetting` | Get the setting with the given id. Raises `NotFound`. Do not construct `WidgetSetting` yourself. |
| `widgetSetting.registerAutocompleteListener(listener)` | `widget_setting.register_autocomplete_listener(listener)` | `void` / `None` | Register an autocomplete listener for that setting. Raises `AlreadyExists` if one was already registered. |

`ManagerDashboards` is reachable as `this.homey.dashboards` (`self.homey.dashboards` in Python) and manages user dashboards; `getWidget` is its only documented method.

**Listener signature:** `async (query, settings) => SettingAutocompleteResult[]`
(Python: `async def listener(query: str, settings: dict[str, SettingValue | SettingAutocompleteResult]) -> list[SettingAutocompleteResult]`)

| Argument | Type | Description |
| --- | --- | --- |
| `query` | `string` | The query typed by the user. |
| `settings` | object / `dict[str, SettingValue \| SettingAutocompleteResult]` | The values of any settings in the widget, as currently selected by the user (autocomplete settings appear as their result object). |

**`SettingAutocompleteResult` properties:**

| Property | Type | Description |
| --- | --- | --- |
| `name` | `string` | The autocomplete value shown to the user and used in the widget. |
| `description` | `string` | A short description shown below the name. |
| `icon` | `string` | Path to an `.svg` file to show as icon for the result. |
| `image` | `string` | Path to an image that is **not** an `.svg` file to show as icon for the result. |
| `data` | `Any` | **Python only.** Any additional data you want to pass to the widget for this autocomplete value; read back as `Homey.getSettings()['mySettingId'].data`. |
| *(free-form)* | any | **JavaScript/TypeScript only.** Add extra properties directly on the result object (e.g. `id`); read them back via `Homey.getSettings()['mySettingId']`. |

TypeScript typing: `Widget.SettingAutocompleteResults`, imported as `import Homey, { Widget } from "homey";`.

Chained form (equivalent, using `getSetting`):

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    try {
      this.homey.dashboards
        .getWidget('my-widget')
        .getSetting('composer')
        .registerAutocompleteListener(async (query, settings) => {
          const items = await this.getComposers();
          return items
            .filter((item) => item.name.toLowerCase().includes(query.toLowerCase()))
            .map((item) => ({ name: item.name, description: item.era, id: item.id }));
        });
    } catch (err) {
      this.error('Could not register widget autocomplete listener:', err);
    }
  }

}

module.exports = MyApp;
```

### 7.8. `devices` — device picker

Many widgets display content for specific Homey devices. The dedicated `devices` picker is a **top-level key of `widget.compose.json`**, a sibling of `settings` — not an entry inside the `settings` array. Selected device IDs are read in the frontend with `Homey.getDeviceIds()`. Users can reorder selected devices via drag-and-drop.

| Property | Type | Required | Values |
| --- | --- | --- | --- |
| `singular` | boolean | required | `false` — allow selecting multiple devices. `true` — restrict to a single device. |
| `type` | string | required | `"app"` — limit selection to devices belonging to your app. `"global"` — allow selection from all Homey devices; only makes sense if the app has the `homey:manager:api` permission. |
| `filter` | object | optional | Selection criteria, see below. |
| `filter.class` | string | optional | Filter by device class (e.g. `"socket"`, `"light"`, `"sensor"`). Pipe (`\|`) acts as **OR**: `"socket\|light"`. |
| `filter.capabilities` | string | optional | Filter by required capabilities. `\|` = **OR** (`"onoff\|dim"` → at least one). `,` = **AND** (`"onoff,dim"` → all). Combined: `"onoff,dim\|light_mode"` → both `onoff` and `dim`, **OR** `light_mode`. |

```json
{
  "name": {
    "en": "My Widget"
  },
  "devices": {
    "type": "global",
    "singular": false,
    "filter": {
      "class": "socket",
      "capabilities": "onoff"
    }
  },
  "settings": [
    {
      "id": "text",
      "type": "text",
      "title": { "en": "Text" },
      "hint": { "en": "Your number" }
    },
    {
      "id": "number",
      "type": "number",
      "title": { "en": "Number" },
      "hint": { "en": "Your number" }
    }
  ]
}
```

### 7.9. Reading settings in the frontend

```html
<html>

<head>
...
</head>

<body>
  <script type="text/javascript">
    function onHomeyReady(Homey) {
      Homey.ready();

      for (const [settingId, settingValue] of Object.entries(Homey.getSettings())) {
        // Do something with the settings...
      }
    }
  </script>
</body>

</html>
```

`Homey.getSettings()` is synchronous and returns the whole settings object for this widget instance. An `autocomplete` setting's value is the **result object** you returned from the listener (not a plain string), so read it defensively:

```javascript
const settings = Homey.getSettings();
const composer = settings.composer;                      // object | null
const composerId = composer && typeof composer === 'object' ? composer.id : composer;

const deviceIds = Homey.getDeviceIds();                  // string[] from the `devices` picker
```

---

## 8. Styling

Homey provides a CSS style library so widgets share a consistent look. Variables are prefixed `--homey`, classes `.homey`. Use them as much as possible — most widgets need only these classes plus a few lines of custom CSS.

> Styling for widgets is **not** the same as for custom views. Some variables and classes share a name, but the actual styling may differ.

### 8.1. Widget anatomy

A widget consists of a **title**, a **frame**, and **your content**.

- **Title** — defaults to `name` from `widget.compose.json`. Users may change it or hide it entirely.
- **Frame** — rounded corners and a shadow. Border radius, shadow and width are **not** changeable. You control only the **height** and the **background colour**.
- `transparent: true` in `widget.compose.json` gives a fully transparent background — ideal for seamless widgets.

#### Background colour

| CSS Variable | Value |
| --- | --- |
| `--homey-background-color` | `--homey-color-mono-000` (white) in light mode and `--homey-color-mono-050` (dark grey) in dark mode. |

Apply a different background to the widget body:

```html
<body class="homey-widget my-custom-body">
  <!-- Content of you widget here. -->
</body>
```

```css
.my-custom-body {
    background-color: var(--homey-color-blue);
}
```

### 8.2. Spacing — space units

Base space unit is **4px**; every derived variable is a multiple of it.

```css
--homey-su: 4px;                         /* base */
--homey-su-1: calc(var(--homey-su) * 1); /*  4px */
--homey-su-2: calc(var(--homey-su) * 2); /*  8px */
--homey-su-3: calc(var(--homey-su) * 3); /* 12px */
--homey-su-4: calc(var(--homey-su) * 4); /* 16px */
--homey-su-5: calc(var(--homey-su) * 5); /* 20px */
--homey-su-6: calc(var(--homey-su) * 6); /* 24px */
--homey-su-7: calc(var(--homey-su) * 7); /* 28px */
--homey-su-8: calc(var(--homey-su) * 8); /* 32px */
```

Space units are for margins, padding and other spacing properties — **not** for sizing properties like `width` and `height`, which are usually determined by text length or remaining space (e.g. `width: 100%`).

```css
.widget-item {
  margin-left: var(--homey-su-2);
  padding: var(--homey-su-4)
}
```

### 8.3. Widget padding classes

| CSS Class | Purpose |
| --- | --- |
| `.homey-widget` | Default and recommended for most widgets. Applies a padding of `--homey-su-4` (16px). |
| `.homey-widget-small` | Saves space in small widgets; applies a padding of `--homey-su-2` (8px). |
| `.homey-widget-full` | For widgets that need the full space (e.g. tables or images). Padding 0. Omitting the class entirely has the same effect. |

`.homey-widget` is added to the `<body>` of your widget by default.

```html
<body class="homey-widget">
  <!-- Content of you widget here. -->
</body>
```

```html
<body class="homey-widget-small">
  <!-- Content of you widget here. -->
</body>
```

Full-bleed layout pattern — put the edge-to-edge element at the top level and move `.homey-widget` to a child for the rest:

```html
<body class="homey-widget-full">
  <!-- Full size element here. -->
  <div class="homey-widget">
    <!-- Content of you widget here. -->
  </div>
</body>
```

### 8.4. Text presets

Ready-made classes that apply a font size smaller than the widget title, with a font weight, line height and colour combination that establishes a clear hierarchy.

| CSS Class | Purpose |
| --- | --- |
| `.homey-text-bold` | Titles or a singular important text. |
| `.homey-text-medium` | Make text stand out; strong text or subtitles. |
| `.homey-text-regular` | Default for most text. |
| `.homey-text-small` | Small text on its own. |
| `.homey-text-small-light` | Small text next to other texts. |

```html
<h1 class="homey-text-bold">Hello World!</h1>
<p class="homey-text-regular">How are you?</p>
```

### 8.5. Font size

Use text sizes smaller than the title above the widget, which is 20px. Default text size is 17px.

| CSS Variable | Value | Purpose |
| --- | --- | --- |
| `--homey-font-size-xxlarge` | 32px | Used for numbers only. |
| `--homey-font-size-xlarge` | 24px | Use sparingly, only for short phrases or single words that really have to stand out. |
| `--homey-font-size-large` | 20px | Used for numbers only. |
| `--homey-font-size-default` | 17px | Default for most text. |
| `--homey-font-size-small` | 14px | For captions, tables, underneath other text, or inside specific elements. |

### 8.6. Line height

There is a specific line height for every font size; always use them together.

| CSS Variable | Value | Use with font size |
| --- | --- | --- |
| `--homey-line-height-xxlarge` | 40px | `--homey-font-size-xxlarge` |
| `--homey-line-height-xlarge` | 32px | `--homey-font-size-xlarge` |
| `--homey-line-height-large` | 28px | `--homey-font-size-large` |
| `--homey-line-height-default` | 24px | `--homey-font-size-default` |
| `--homey-line-height-small` | 20px | `--homey-font-size-small` |

### 8.7. Font weight

| CSS Variable | Value | Purpose |
| --- | --- | --- |
| `--homey-font-weight-bold` | 700 | Used for titles. |
| `--homey-font-weight-medium` | 500 | Make text stand out; strong text or subtitles. |
| `--homey-font-weight-regular` | 400 | Default for most text. |

#### Allowed font-size / font-weight combinations

| Font size | regular | medium | bold |
| --- | --- | --- | --- |
| xxlarge | no | no | **yes** |
| xlarge | no | no | **yes** |
| large | no | **yes** | no |
| default | **yes** | **yes** | **yes** |
| small | **yes** | no | no |

### 8.8. Text colour

Default text colour is `--homey-text-color`; it adapts to light/dark mode and sits well on `--homey-background-color`.

| CSS Variable | Purpose |
| --- | --- |
| `--homey-text-color` | Default text color. |
| `--homey-text-color-light` | Used for text that's less important, or disabled. |
| `--homey-text-color-white` | White text, independent of light or dark mode. Used for text on dark or coloured backgrounds. |
| `--homey-text-color-blue` | Blue text. |
| `--homey-text-color-green` | Green text. |
| `--homey-text-color-orange` | Orange text. |
| `--homey-text-color-red` | Red text. |
| `--homey-text-color-highlight` | Text to highlight something. |
| `--homey-text-color-success` | Text for success case. |
| `--homey-text-color-warning` | Text for warnings. |
| `--homey-text-color-danger` | Text for errors. |

```html
<p class="my-custom-text">HELP ME!</p>
```

```css
.my-custom-text {
    font-size: var(--homey-font-size-default);
    font-weight: var(--homey-font-weight-bold);
    line-height: var(--homey-line-height-default); /* Matches with font-size. */
    color: var(--homey-text-color-danger);
}
```

### 8.9. Text alignment

| CSS Class | Purpose |
| --- | --- |
| `.homey-text-align-left` | Align text left. |
| `.homey-text-align-center` | Align text center. |
| `.homey-text-align-right` | Align text right. |

### 8.10. Light and dark mode

The dashboard switches between light and dark mode based on the user's settings. Every colour variable adjusts automatically to the active mode, though the actual colour may differ between modes. By default the widget background is white in light mode and dark grey in dark mode.

| CSS Class | Purpose |
| --- | --- |
| `.homey-dark-mode` | Force widget to dark mode independent of user settings. |

```html
<body class="homey-widget homey-dark-mode">
  <!-- Content of you widget here. -->
</body>
```

To style conditionally on dark mode, use the selector `.homey-dark-mode my-selector`.

### 8.11. Colour palette

- Grayscale is prefixed `--homey-color-mono`, ranging from `--homey-color-mono-000` (white in light mode) to `--homey-color-mono-1000` (black in light mode).
- Chromatic ramps are `--homey-color-blue`, `--homey-color-green`, `--homey-color-orange`, `--homey-color-red`. They range from `050` to `900` — **except orange, which only has the `500` value**. These colours remain the same in both light and dark mode.

The only palette variable names spelled out in the documentation are `--homey-color-mono-000`, `--homey-color-mono-050` and `--homey-color-mono-1000`; the chromatic ramps are described only by their prefix and their `050`–`900` range. Prefer the **semantic** variables ([§8.12](#812-semantic-colours)) — they are fully named in the docs and defined in terms of this palette.

### 8.12. Semantic colours

Semantic variables are defined in terms of the palette above — no new colours, just intended use cases.

| CSS Variable | Purpose |
| --- | --- |
| `--homey-color-white` | White color independent of light or dark mode. |
| `--homey-color-blue` | General purpose blue color. |
| `--homey-color-green` | General purpose green color. |
| `--homey-color-orange` | General purpose orange color. |
| `--homey-color-red` | General purpose red color. |
| `--homey-color-highlight` | Highlight. |
| `--homey-color-success` | Success. |
| `--homey-color-warning` | Warning. |
| `--homey-color-danger` | Danger. |

Semantic variables for background, text, lines and icons live in their own sections above and below.

### 8.13. Lines and borders

The widget frame already has a shadow — avoid additional shadows on elements inside your widget.

| CSS Class | Purpose |
| --- | --- |
| `.homey-border` | Adds a border to all sides of the element. |
| `.homey-border-top` | Add a border to the top of the element. |
| `.homey-border-right` | Add a border to the right side of the element. |
| `.homey-border-bottom` | Add a border to the bottom of the element. |
| `.homey-border-left` | Add a border to the left side of the element. |

Line colours:

| CSS Variable | Purpose |
| --- | --- |
| `--homey-line-color` | Used for most lines. The default line color. |
| `--homey-line-color-light` | Used for light lines that should stand out less. |

Complete line shorthands (1px solid, using the colours above):

| CSS Variable | Purpose |
| --- | --- |
| `--homey-line` | Used for most lines. |
| `--homey-line-light` | Used for light lines that should stand out less. |

Border radius:

| CSS Variable | Purpose |
| --- | --- |
| `--homey-border-radius-small` | Only use where the default border radius is too big. |
| `--homey-border-radius-default` | Default border radius. |

```html
<div class="my-custom-item"></div>
```

```css
.my-custom-item {
    border: var(--homey-line-light);
    border-radius: var(--homey-border-radius-default);
}
```

### 8.14. Icons

Always use SVGs for icons. Put custom icons and other assets in your `public` folder.

Custom icons extend the `.homey-custom-icon-` class family: add a class starting with `.homey-custom-icon-` (e.g. `.homey-custom-icon-example`) to your element, and in CSS use the SVG as `mask-image` plus `-webkit-mask-image` for older browser support.

```html
<div class="homey-custom-icon-example"></div>
```

```css
.homey-custom-icon-example {
    -webkit-mask-image: url('example.svg'); /* Browser support. */
    mask-image: url('example.svg');
}
```

Icon colours:

| CSS Variable | Purpose |
| --- | --- |
| `--homey-icon-color-dark` | Default icon color. |
| `--homey-icon-color-light` | Used for less important icons or disabled states. |
| `--homey-icon-color-white` | White icons, independent of light or dark mode. |
| `--homey-icon-color-blue` | Blue icons. |
| `--homey-icon-color-green` | Green icons. |
| `--homey-icon-color-orange` | Orange icons. |
| `--homey-icon-color-red` | Red icons. |

Icon sizes:

| CSS Variable | Value | Purpose |
| --- | --- | --- |
| `--homey-icon-size-medium` | 20px | Default icon size. |
| `--homey-icon-size-regular` | 16px | Used in line with regular text. |
| `--homey-icon-size-small` | 14px | Used in line with small text. |

Set the per-icon colour and size through the `--homey-icon-color` and `--homey-icon-size` custom properties:

```html
<div class="homey-custom-icon-example"></div>
```

```css
.homey-custom-icon-example {
    --homey-icon-color: var(--homey-icon-color-green);
    --homey-icon-size: var(--homey-icon-size-small);

    -webkit-mask-image: url('example.svg');
    mask-image: url('example.svg');
}
```

### 8.15. Tables

| CSS Class | Purpose |
| --- | --- |
| `.homey-table` | Default table styling (lines between cells). |
| `.homey-table-striped` | Striped rows; use only for tables with a few columns, or when horizontal spacing makes dividing lines unnecessary. |

Apply the text-alignment classes to the table element to change cell alignment.

```html
<table class="homey-table homey-text-align-center">
  <thead>
  <tr>
    <th>Header 1</th>
    <th>Header 2</th>
    <th>Header 3</th>
  </tr>
  </thead>
  <tbody>
  <tr>
    <td>Row 1, Cell 1</td>
    <td>Row 1, Cell 2</td>
    <td>Row 1, Cell 3</td>
  </tr>
  <tr>
    <td>Row 2, Cell 1</td>
    <td>Row 2, Cell 2</td>
    <td>Row 2, Cell 3</td>
  </tr>
  <tr>
    <td>Row 3, Cell 1</td>
    <td>Row 3, Cell 2</td>
    <td>Row 3, Cell 3</td>
  </tr>
  </tbody>
</table>
```

---

## 9. Preview images

`preview-light.png` and `preview-dark.png` are shown on your app's App Store page and in the Widget picker in the Homey mobile app. Both light and dark mode versions should be provided.

Requirements and guidelines (App Store guideline 1.10):

- **Dimensions: 1024x1024.**
- Use the official [Figma template](https://www.figma.com/community/file/1392859749687789493/widget-previews-template) — it includes the proper colour styles and shadows, automatically generates a dark-mode version, provides examples, and ensures export in the correct dimensions.
- **Don't use screenshots or over-detailed designs.** Don't include text. Use simple shapes.
- **Use the colour styles from the Figma template** for basic elements. Don't use the same colours as the Widget picker background. Try not to use too many different colours. Use the shadow styles provided in the template.
- **Don't use a background colour or image** — previews should have a **transparent background**.
- Ensure the previews accurately represent the appearance of your widget.

---

## 10. Debugging

### 10.1. Live reload during `homey app run`

When running `homey app run`, a **refresh button** appears that reloads `index.html` without restarting the entire app.

- **Docker requirement:** Docker is required; `homey app run` will automatically enforce Docker usage.
- **Supported models:** Homey 2023 and later only.
- **Not available:** on models earlier than 2023, and when running remotely with `homey app run --remote`.
- Applies only to files in the `public` folder. **Any other file change requires a full restart.**

### 10.2. Webview inspector

The widget runs inside a webview in the mobile app, so use the Chrome inspector (Android) or Safari Web Inspector (iOS) to view the console and inspect the widget's HTML.

**Android**

1. Plug in your mobile device.
2. Enable USB debugging: **Settings** → **System** → **Developer options** → **USB debugging**.
3. On the PC, open **Chrome** and navigate to `chrome://inspect/#devices` (on **Edge**: `edge://inspect/#devices`).
4. Under **Remote Target**, look for **"WebView in app.homey."**
5. Click **Inspect**.

**iOS**

1. Plug in your mobile device.
2. Enable USB debugging: **Settings** → **System** → **About Phone** → **Developer options** → **USB debugging**.
3. On the PC, open **Safari** Settings → **Advanced** tab → enable **"Show Develop menu in menu bar."**
4. In **Safari**, go to **Develop** → **[device name]** → **[app name]** → **[url - title]**.

---

## 11. Gotchas

Field-tested notes, plus documentation traps.

**Gotcha: the widget id is the folder name.** `homey app widget create` asks for an ID and creates `/widgets/<widgetId>/`. The documented `widget.compose.json` examples contain **no `id` key** — the folder name is the id, and that is the exact string you pass to `this.homey.dashboards.getWidget('<widgetId>')`. A mismatch throws `NotFound` at app boot.

*Schema discrepancy:* the app manifest schema lists `id` as **required** on every `widgets.<widgetId>` entry, which looks like it contradicts the id-less examples. It does not — Compose assigns `widgetJson.id = <folderName>` (and defaults `settings` to `[]`) while building `app.json`, so the requirement is satisfied by the build, not by your source file. Adding `"id"` to `widget.compose.json` yourself is redundant, and a value that disagrees with the folder name is overwritten. Only an app that hand-maintains `app.json` without Compose must write `id` explicitly — omitting it there fails validation.

**Gotcha: `this.homey.dashboards` may not exist on older firmware.** Widgets require `compatibility >=12.3.0`. Wrap `getWidget(...)` / `registerSettingAutocompleteListener(...)` in `try/catch` so the app still boots on firmware without `ManagerDashboards`, and log with `this.error(...)`.

**Gotcha: forgetting `Homey.ready()` leaves the widget stuck on the loading state.** `onHomeyReady(Homey)` must be a **global** function on the page; the loading state is removed only when you call `Homey.ready()`.

**Gotcha: don't set the height twice.** Setting `height` in `widget.compose.json` *and* calling `Homey.ready({ height })` / `Homey.setHeight()` causes visible height shifts during load. Pick one. Heights are cached after the first load.

**Gotcha: a percentage height is an aspect ratio, not a percentage of the screen.** `"height": "100%"` yields a square widget.

**Gotcha: widgets cannot set their own width.** They fill the dashboard column. The frame's border radius, shadow and width are not customizable either — only height and background colour.

**Gotcha: `Homey.getSettings()` is synchronous.** It returns the object directly; there is no callback and no Promise. (This differs from the app-settings view API, where `Homey.get()` is callback-based.)

**Gotcha: autocomplete values are objects, not strings.** The stored value of an `autocomplete` setting is the whole result object you returned from the listener. In JS, extra properties live at the top level (`settings.mySetting.id`); in the Python SDK they live under `data` (`settings.mySetting.data.id`). Read defensively in the frontend.

**Gotcha: `devices` is a top-level key, not a `settings` entry.** Put `"devices": { "type": …, "singular": …, "filter": … }` next to `settings` in `widget.compose.json`. Inside `devices`, `type` means the **scope** (`"app"` / `"global"`), which is *not* the same meaning `type` has inside a `settings` entry. `"global"` only makes sense with the `homey:manager:api` permission.

**Gotcha: `Homey.api()` takes a method + path, not the handler name.** `Homey.api('GET', '/')` resolves against the `api` map to find the exported function. Renaming the handler without updating `widget.compose.json` silently breaks the call.

**Gotcha: widget API endpoints are scoped to the widget**, not to the app's global Web API. They live in `/widgets/<widgetId>/api.js`, separate from the app's root `/api.js`.

**Gotcha: a widget route's `method` is a single string, not an array.** `"method": ["GET", "POST"]` is valid for an *app* Web API route but not for a widget route — the widget schema types `method` as one of `"GET" | "POST" | "PUT" | "DELETE"`. Declare a separate route per method. There is likewise no `public` option on widget routes.

**Gotcha: `GET` and `DELETE` requests carry an empty body.** Put parameters in the query string or the path, never in the body, for those methods.

**Gotcha: `Homey.hapticFeedback()` only works inside a short window after a touch event.** Calling it from a timer or an async continuation silently does nothing.

**Gotcha: injected `<script>` tags do not execute.** Assigning `element.innerHTML = '<script>…</script>'` inserts the markup but the browser never runs it. If you must run logic against markup you build dynamically, stringify a named function and invoke it instead of relying on the tag firing:

```javascript
function render(root, data) { /* ...build DOM... */ }
const boot = `(${render.toString()})(document.getElementById('app'), ${JSON.stringify(data)});`;
// then execute `boot` in the target context instead of injecting a <script> tag
```

**Gotcha: Insights is write-only at runtime — you cannot draw a chart from it.** `insights: true` on a capability logs values, but the App SDK gives the app no way to read them back (see `references/drivers-and-devices.md` → Insights). To render a trend in a widget, keep your own **bounded rolling buffer** and serve it through `api.js`:

```javascript
// device.js — append a capped history sample each poll
async recordSample(value) {
  const history = this.getStoreValue('history') || [];
  history.push({ t: Date.now(), v: value });
  while (history.length > 96) history.shift();   // e.g. keep ~last 96 samples
  await this.setStoreValue('history', history);
}
```

```javascript
// widgets/<widgetId>/api.js — serve it to the widget
async getHistory({ homey, query }) {
  return homey.app.getDeviceHistory(query.device);   // returns the capped array
}
```

**Gotcha: both preview images are required.** `homey app validate --level publish` fails with `ENOENT` if either file is missing:

```
✖ ... ENOENT: no such file or directory, open '.../widgets/my-widget/preview-light.png'
```

**Gotcha: don't hardcode colours.** Always reference the `--homey-*` variables so the widget follows the user's light/dark theme.

**Doc trap: `--homey-font-size-medium` / `--homey-line-height-medium` are not real.** The styling page's usage example references them, but they do not appear in any documented variable table. The documented scale is `xxlarge | xlarge | large | default | small`.

**Doc trap: text alignment classes are prefixed.** The styling page's table example writes `class="homey-table text-align-center"`; the documented class is `.homey-text-align-center`.

**Doc trap: the dark-mode background variable is `--homey-color-mono-050`.** The styling page's background table prints it as `--color-mono-050`, which is missing the `homey-` prefix used by every other palette variable.

**Doc trap: the widget `index.html` example elides `<head>`.** Unlike custom app-settings views (which document `<script src="/homey.js" data-origin="settings">`), the widget docs do not specify a bootstrap script tag — and the CLI's scaffolded widget template has **no script tag in `<head>` at all**, only a `<style>` block. The `Homey` object is injected for you; do not copy the `/homey.js` tag from the app-settings docs into a widget.

**Note: deprecate, don't delete.** Setting `"deprecated": true` hides the widget from the picker for new instances while existing user instances keep working. Removing a widget folder breaks dashboards that use it.

---

## 12. Complete worked example

`/widgets/status-tile/widget.compose.json`

```json
{
  "name": { "en": "Status Tile", "nl": "Statustegel" },
  "height": "100%",
  "transparent": false,
  "devices": {
    "type": "app",
    "singular": true,
    "filter": { "class": "sensor", "capabilities": "measure_temperature" }
  },
  "settings": [
    {
      "id": "refreshInterval",
      "type": "number",
      "title": { "en": "Refresh interval" },
      "hint": { "en": "Seconds between refreshes." },
      "value": 30,
      "min": 5,
      "max": 3600
    },
    {
      "id": "unit",
      "type": "dropdown",
      "title": { "en": "Unit" },
      "value": "celsius",
      "values": [
        { "id": "celsius", "title": { "en": "Celsius" } },
        { "id": "fahrenheit", "title": { "en": "Fahrenheit" } }
      ]
    },
    {
      "id": "room",
      "type": "autocomplete",
      "title": { "en": "Room" }
    }
  ],
  "api": {
    "getStatus": { "method": "GET", "path": "/" },
    "setMode": { "method": "PUT", "path": "/:id" }
  }
}
```

`/widgets/status-tile/api.js`

```javascript
'use strict';

module.exports = {
  async getStatus({ homey, query }) {
    return homey.app.getWidgetStatus({
      deviceId: query.deviceId,
      unit: query.unit,
    });
  },

  async setMode({ homey, params, body }) {
    await homey.app.setMode(params.id, body.mode);
    return { success: true };
  },
};
```

`/widgets/status-tile/public/index.html`

```html
<html>

<head>
  <style>
    .tile { display: flex; flex-direction: column; gap: var(--homey-su-2); }
    .value {
      font-size: var(--homey-font-size-xxlarge);
      line-height: var(--homey-line-height-xxlarge);
      font-weight: var(--homey-font-weight-bold);
      color: var(--homey-text-color);
    }
    .value.warn { color: var(--homey-text-color-warning); }
    .meta { color: var(--homey-text-color-light); }
    .divider { border-top: var(--homey-line-light); }
  </style>
</head>

<body class="homey-widget">
  <div class="tile">
    <div id="value" class="value">--</div>
    <div class="divider"></div>
    <div id="meta" class="homey-text-small-light meta"></div>
  </div>

  <script type="text/javascript">
    function onHomeyReady(Homey) {
      const settings = Homey.getSettings();
      const intervalMs = (settings.refreshInterval || 30) * 1000;
      const unit = settings.unit || 'celsius';
      const room = settings.room; // autocomplete result object | null
      const deviceId = Homey.getDeviceIds()[0];

      const valueEl = document.getElementById('value');
      const metaEl = document.getElementById('meta');

      metaEl.innerText = room && room.name ? room.name : Homey.__('widget.noRoom');

      function refresh() {
        const path = `/?deviceId=${encodeURIComponent(deviceId || '')}&unit=${encodeURIComponent(unit)}`;
        Homey.api('GET', path)
          .then((result) => {
            valueEl.innerText = String(result.value);
            valueEl.classList.toggle('warn', result.value > 30);
          })
          .catch(console.error);
      }

      Homey.on('status_update', (data) => {
        valueEl.innerText = String(data.value);
      });

      refresh();
      setInterval(refresh, intervalMs);

      Homey.ready();
    }
  </script>
</body>

</html>
```

`/app.js`

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.log('MyApp has been initialized');

    try {
      this.homey.dashboards
        .getWidget('status-tile')
        .registerSettingAutocompleteListener('room', async (query, settings) => {
          const zones = await this.getZones();
          return zones
            .filter((zone) => zone.name.toLowerCase().includes(query.toLowerCase()))
            .map((zone) => ({
              name: zone.name,
              description: zone.parentName,
              id: zone.id,
            }));
        });
    } catch (err) {
      this.error('Could not register widget autocomplete listener:', err);
    }

    this.homey.setInterval(() => {
      this.homey.api.realtime('status_update', { value: this.lastValue })
        .catch(this.error);
    }, 60 * 1000);
  }

  async getWidgetStatus({ deviceId, unit }) {
    // ...
    return { value: 21.5, unit };
  }

}

module.exports = MyApp;
```

---

## Sources

- https://apps.developer.homey.app/the-basics/widgets
- https://apps.developer.homey.app/the-basics/widgets/settings
- https://apps.developer.homey.app/the-basics/widgets/styling
- https://apps.developer.homey.app/the-basics/widgets/debugging
- https://apps.developer.homey.app/app-store/guidelines (§1.10 Widget Previews)
- https://apps.developer.homey.app/the-basics/getting-started/homey-cli (`homey app widget create`)
- https://apps.developer.homey.app/advanced/web-api (api handler argument, realtime events)
- https://python-apps-sdk-v3.developer.homey.app — `ManagerDashboards`, `Widget`, `WidgetSetting`, `SettingAutocompleteResult`, `SettingAutocompleteListener`
- https://www.figma.com/community/file/1392859749687789493/widget-previews-template
