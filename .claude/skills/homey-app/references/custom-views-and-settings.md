# Custom Views & App Settings Reference

Custom views are plain web pages (HTML/CSS/JS) that Homey renders inside the Homey app, with a global
`Homey` object for talking to your app. This file covers the `/settings/index.html` App Settings
page, the complete front-end `Homey` API surface of every custom-view type, and the Homey HTML & CSS
style library. Pairing/repair views are in `references/pairing.md`; widgets in
`references/widgets.md`.

## Table of Contents

1. [The three custom view types](#view-types)
2. [App Settings page contract](#settings-contract)
3. [Settings-view `Homey` API](#settings-api)
4. [Front-end `Homey` API — full index across all view types](#full-api)
5. [Back-end counterpart: `ManagerSettings`, realtime events, Web API](#backend)
6. [Worked examples](#examples)
7. [Homey style library — HTML & CSS](#style-library)
8. [Design tokens (CSS custom properties)](#tokens)
9. [Right-to-left (RTL) styling](#rtl)
10. [Homey Cloud restrictions](#homey-cloud)
11. [Legacy manifest `settings` array](#legacy-settings)
12. [Gotchas](#gotchas)

---

## The three custom view types {#view-types}

| Type | Location | Docs | Reference file |
| --- | --- | --- | --- |
| **App Settings** | `/settings/index.html` | `/advanced/custom-views/app-settings` | this file |
| **Custom Pairing Views** | `/drivers/<driver_id>/pair/<view_id>.html` (and `/repair/`) | `/advanced/custom-views/custom-pairing-views` | `references/pairing.md` |
| **Widgets** | `/widgets/<widgetId>/public/index.html` | `/the-basics/widgets` | `references/widgets.md` |

All three share the Homey style library (`/advanced/custom-views/html-and-css-styling`) and the
`data-i18n` / `Homey.__()` translation mechanism, but each has a **different** `Homey` object — see
[the full API index](#full-api). Widget *styling* is explicitly documented as **not** identical to
custom-view styling ("While there are some variables and classes with the same name, the actual
styling might differ").

> **Custom app settings views are not allowed on Homey Cloud.** Ask for whatever the app needs during
> pairing, and use *re-pair* views to update it later. See [Homey Cloud restrictions](#homey-cloud).

---

## App Settings page contract {#settings-contract}

An app can store settings that persist across reboots through `ManagerSettings`
(`this.homey.settings`). An App Settings page is the optional UI on top of that store.

### 1. Create `/settings/index.html`

Create a folder named `/settings/` in the app root containing `index.html`. That is the only required
file; anything else you reference (CSS, JS, images) lives beside it.

```
com.athom.example/
├─ app.js
└─ settings/
   └─ index.html
```

### 2. Include `/homey.js` with `data-origin="settings"`

```html
<head>
  <!-- ... -->
  <script
    type="text/javascript"
    src="/homey.js"
    data-origin="settings"
  ></script>
</head>
```

The `src` is the absolute path `/homey.js` — it is served by Homey, not by your app; do not ship a
copy. The `data-origin="settings"` attribute is mandatory for settings views.

### 3. Define `onHomeyReady(Homey)` and call `Homey.ready()`

```html
<script type="text/javascript">
  function onHomeyReady(Homey) {
    // ...

    Homey.ready();
  }
</script>
```

- A **global function named `onHomeyReady`** must exist; Homey calls it with the `Homey` instance.
- The view stays **hidden until `Homey.ready()` is called**. Use that window to do your API calls so
  the page does not flicker while loading.

### Manifest / validator side effects

| Rule | Detail |
| --- | --- |
| `hasSettings: true` | The CLI injects this key into the generated `/app.json` when `/settings/index.html` exists (`homey/lib/App.js`). Never write it by hand. It is **not a property of the app.json JSON Schema**; it passes validation only because the schema sets no `additionalProperties: false` at the top level. It is CLI output, not manifest input. |
| Validator | If a `/settings/` folder exists, `/settings/index.html` **must** exist, otherwise validation fails. (homey-lib `App#validate`: if `settings` exists, it asserts `settings/index.html` exists, case-sensitively.) |
| Homey Cloud | An app with `"platforms": ["cloud"]` may not ship a custom settings view. **Not enforced by `homey app validate`** — homey-lib contains no such check; this is a platform / App-Store-review restriction, so validation passing does not mean the view will work on Cloud. |

### Full minimal page

```html
<!DOCTYPE html>
<html>
  <head>
    <!-- The '/homey.js' script must be included in your settings view to work -->
    <script
      type="text/javascript"
      src="/homey.js"
      data-origin="settings"
    ></script>
  </head>
  <body>
    <header class="homey-header">
      <h1 class="homey-title" data-i18n="settings.title">
        <!-- This will be filled with the translated string with key 'settings.title'. -->
      </h1>
      <p class="homey-subtitle" data-i18n="settings.subtitle">
        <!-- This field will also be translated -->
      </p>
    </header>

    <fieldset class="homey-form-fieldset">
      <legend class="homey-form-legend">My Settings</legend>

      <div class="homey-form-group">
        <label class="homey-form-label" for="username">Username</label>
        <input class="homey-form-input" id="username" type="text" value="" />
      </div>
      <div class="homey-form-group">
        <label class="homey-form-label" for="password">Password</label>
        <input class="homey-form-input" id="password" type="password" value="" />
      </div>
    </fieldset>

    <button id="save" class="homey-button-primary-full">Save changes</button>

    <script type="text/javascript">
      // a method named 'onHomeyReady' must be present in your code
      function onHomeyReady(Homey) {
        // Tell Homey we're ready to be displayed
        Homey.ready();

        var usernameElement = document.getElementById("username");
        var passwordElement = document.getElementById("password");
        var saveElement = document.getElementById("save");

        Homey.get("username", function (err, username) {
          if (err) return Homey.alert(err);
          usernameElement.value = username;
        });

        Homey.get("password", function (err, password) {
          if (err) return Homey.alert(err);
          passwordElement.value = password;
        });

        saveElement.addEventListener("click", function (e) {
          Homey.set("username", usernameElement.value, function (err) {
            if (err) return Homey.alert(err);
          });
          Homey.set("password", passwordElement.value, function (err) {
            if (err) return Homey.alert(err);
          });
        });
      }
    </script>
  </body>
</html>
```

```json
// /locales/en.json
{
  "settings": {
    "title": "My Settings Page",
    "subtitle": "Please log in"
  }
}
```

### Translations in custom views

Two mechanisms, both reading `/locales/<language>.json`:

```html
<!-- declarative: the element's content is replaced with the translated string -->
<span data-i18n="pair.title"></span>
<p data-i18n="settings.intro"></p>

<script type="application/javascript">
  // programmatic
  function onHomeyReady(Homey) {
    alert(Homey.__('settings.title'));
    Homey.ready();
  }
</script>
```

Dot notation addresses nested keys; the optional second argument of `Homey.__()` is a token object
(`{ name: 'Dave' }` replaces `__name__`). See `references/app-and-manifest.md` for the locale-file
format and the supported language codes.

---

## Settings-view `Homey` API {#settings-api}

All methods accept **either** a Node-style callback **or** return a Promise. Since SDK v3 "all methods
in the Custom pair and App settings views now support callbacks and promises… It is advised to update
your code to use promises only for any API, because callbacks will be removed in a later SDK
version."

| Method | Signature | Description |
| --- | --- | --- |
| `Homey.ready()` | `Homey.ready()` | The settings view stays **hidden** until this is called. Use the extra time to make required API calls to prevent flickering on screen. |
| `Homey.get()` | `Homey.get( [String name,] Function callback )` | Gets a single setting's value when `name` is provided, or an object with **all** settings when `name` is omitted. |
| `Homey.set()` | `Homey.set( String name, Mixed value, Function callback )` | Sets a single setting's value. The value must be **JSON-serializable**. |
| `Homey.unset()` | `Homey.unset( String name, Function callback )` | Unsets a single setting's value. |
| `Homey.on()` | `Homey.on( String event, Function callback )` | Register an event listener for your app's **realtime events**. System events when modifying settings are `settings.set` and `settings.unset`. |
| `Homey.api()` | `Homey.api( String method, String path, Mixed body, Function callback )` | Call your app's Web API. `method` is `GET`, `POST`, `PUT` or `DELETE`. `path` is relative to your app's API endpoint. `body` is optional — pass `null` to ignore it. |
| `Homey.alert()` | `Homey.alert( String message, Function callback )` | Show an alert dialog. |
| `Homey.confirm()` | `Homey.confirm( String message, Function callback )` | Show a confirm dialog. The callback's **2nd** argument is `true` when the user pressed `OK`. |
| `Homey.popup()` | `Homey.popup( String url[, Object opts] )` | Show a popup (new window). `opts` may have `width` and `height` of type `number`; both default to `400`. |
| `Homey.openURL()` | `Homey.openURL( String url )` | Show a new window. |
| `Homey.__()` | `Homey.__( String key [, Object tokens] )` | Translate a string programmatically. `key` is the id in `/locales/<language>.json`; use dots for sub-properties (`settings.title`). `tokens` is an object with replacers. |

### `Homey.api()` in detail

The call is proxied to `/api/app/<your.app.id><path>` — the routes you declared under `api` in the
App Manifest and implemented in `/api.js`.

```html
<script type="text/javascript">
  // make a PUT call to /api/app/com.your.app/hello
  Homey.api("PUT", "/hello", { foo: "bar" }, function (err, result) {
    if (err) return Homey.alert(err);
  });
</script>
```

Promise form:

```html
<script type="text/javascript">
  async function onHomeyReady(Homey) {
    Homey.ready();

    try {
      const result = await Homey.api('PUT', '/hello', { foo: 'bar' });
      console.log(result);
    } catch (err) {
      await Homey.alert(err.message || String(err));
    }
  }
</script>
```

Apps on Homey Cloud are not allowed to expose a Web API, so `Homey.api()` is a Homey Pro / Self-Hosted
Server tool. See `references/web-api-and-realtime.md`.

### `Homey.on()` in detail

`Homey.on()` receives the one-way realtime events your app emits with
`this.homey.api.realtime(event, data)`, plus the two built-in settings events.

| Event | Emitted when |
| --- | --- |
| `settings.set` | A setting has been set (also when set from your app's back-end). |
| `settings.unset` | A setting has been unset. |
| *(any custom name)* | Your app called `await this.homey.api.realtime('my_event', value)`. |

```html
<script type="text/javascript">
  function onHomeyReady(Homey) {
    Homey.ready();

    Homey.on('settings.set', function (key) {
      console.log('setting changed:', key);
    });

    Homey.on('my_event', function (data) {
      document.getElementById('status').textContent = String(data);
    });
  }
</script>
```

---

## Front-end `Homey` API — full index across all view types {#full-api}

The `Homey` object differs per view type. **Do not assume a member exists in a view type where it is
not documented.** `S` = App Settings view, `P` = custom pair/repair view, `W` = widget.

| Member | Signature | S | P | W | Notes |
| --- | --- | :-: | :-: | :-: | --- |
| `ready` | `Homey.ready()` | ● | — | — | Settings view stays hidden until this is called. **Not documented in the custom-pairing-views front-end API** — pair views also receive `onHomeyReady(Homey)`, but the docs never list `Homey.ready()` for them. |
| `ready` (widget) | `Homey.ready(args?: { height: number \| string }): void` | — | — | ● | Call when the widget is ready to be shown; removes the widget loading state. `height` overrides `widget.compose.json`. |
| `get` | `Homey.get( [String name,] Function callback )` | ● | — | — | App settings value(s). |
| `set` | `Homey.set( String name, Mixed value, Function callback )` | ● | — | — | JSON-serializable values only. |
| `unset` | `Homey.unset( String name, Function callback )` | ● | — | — | |
| `api` | `Homey.api( String method, String path, Mixed body, Function callback )` | ● | — | — | App Web API (`/api/app/<id>/…`). |
| `api` (widget) | `Homey.api(method: string, path: string, body?: object): Promise<unknown>` | — | — | ● | Widget-scoped API from `widget.compose.json` → `api`. |
| `on` | `Homey.on( String event, Function callback )` | ● | ● | — | Settings: realtime events + `settings.set`/`settings.unset`. Pair: messages from `session.emit()`; the callback may return a value or Promise as the reply. |
| `on` (widget) | `Homey.on(event: string, callback: (...args[]: any) => void): void` | — | — | ● | Listen to events emitted by your app. |
| `emit` | `Homey.emit( String event, Mixed data ): Promise<any>` | — | ● | — | Calls the handler registered with `session.setHandler(event, cb)` in the driver. |
| `alert` | `Homey.alert( String message, Function callback )` | ● | — | — | |
| `alert` (pair) | `Homey.alert( String message[, String icon] ): Promise<void>` | — | ● | — | `icon` = `null`, `error`, `warning` or `info`. |
| `confirm` | `Homey.confirm( String message, Function callback )` | ● | — | — | Callback's 2nd argument is `true` on OK. |
| `confirm` (pair) | `Homey.confirm( String message[, String icon] ): Promise<boolean>` | — | ● | — | `icon` = `null`, `error`, `warning` or `info`. Resolves `true` when the user pressed OK. |
| `popup` | `Homey.popup( String url[, Object opts] )` | ● | — | — | `opts.width` / `opts.height`, default `400`. |
| `popup` (pair) | `Homey.popup( String url )` | — | ● | — | Show a popup with a remote website. |
| `popup` (widget) | `Homey.popup(url: string): Promise<void>` | — | — | ● | Opens an in-app browser view. |
| `openURL` | `Homey.openURL( String url )` | ● | — | — | Show a new window. |
| `__` | `Homey.__( String key [, Object tokens] )` | ● | ● | ● | Widget signature: `Homey.__(input: string, tokens?: object): string`. |
| `setTitle` | `Homey.setTitle( String title )` | — | ● | — | Set the window's title. |
| `setSubtitle` | `Homey.setSubtitle( String subtitle )` | — | ● | — | Set the window's subtitle. |
| `showView` | `Homey.showView( String viewId )` | — | ● | — | Navigate to another view id from the manifest. |
| `prevView` | `Homey.prevView()` | — | ● | — | |
| `nextView` | `Homey.nextView()` | — | ● | — | |
| `getCurrentView` | `Homey.getCurrentView()` | — | ● | — | Returns the current view ID. |
| `createDevice` | `Homey.createDevice( Object device ): Promise<Object>` | — | ● | — | `device` must contain `data` and `name`; may contain `icon`, `class`, `capabilities`, `capabilitiesOptions`, `store`, `settings`. |
| `getZone` | `Homey.getZone(): Promise<string>` | — | ● | — | Zone ID of the active zone. |
| `getOptions` | `Homey.getOptions( [String viewId] ): Promise<Object>` | — | ● | — | Resolves the `viewOptions` of that view (current view when omitted). |
| `setNavigationClose` | `Homey.setNavigationClose()` | — | ● | — | Remove all navigation buttons, show a single *Close* button. |
| `done` | `Homey.done()` | — | ● | — | Close the pairing window. |
| `showLoadingOverlay` | `Homey.showLoadingOverlay()` | — | ● | — | Shows the loading overlay. |
| `hideLoadingOverlay` | `Homey.hideLoadingOverlay()` | — | ● | — | Hides the loading overlay. |
| `getViewStoreValue` | `Homey.getViewStoreValue( String viewId, String key ): Promise<any>` | — | ● | — | |
| `setViewStoreValue` | `Homey.setViewStoreValue( String viewId, String key, Mixed value ): Promise<void>` | — | ● | — | Used to feed e.g. `add_devices` its `devices` array. |
| `getWidgetInstanceId` | `Homey.getWidgetInstanceId(): string` | — | — | ● | Unique id per widget instance on a dashboard. |
| `getSettings` | `Homey.getSettings(): { [key: string]: unknown }` | — | — | ● | The **widget's** settings as filled in by the user — *not* app settings. |
| `setHeight` | `Homey.setHeight(height: number \| string \| null): Promise<void>` | — | — | ● | Change widget height at runtime. |
| `hapticFeedback` | `Homey.hapticFeedback(): void` | — | — | ● | Only callable shortly after a touch event. |
| `getDeviceIds` | `Homey.getDeviceIds(): string[]` | — | — | ● | IDs selected in the widget's *Devices* setting. |

> **Not documented — do not use:** there is no documented `Homey.getLanguage()` in any custom view
> (settings, pair or widget). Translate with `Homey.__()` / `data-i18n`, or expose the language from
> your app through the Web API (`this.homey.i18n.getLanguage()` server-side) if you truly need the
> raw code. Likewise, `Homey.showLoadingOverlay()` / `hideLoadingOverlay()`, `setTitle()`,
> `setSubtitle()` and `emit()` are documented for **pairing views only** — do not assume they exist
> in a settings page. In the other direction, `Homey.ready()` is documented only for the **App
> Settings** view and for **widgets**; the custom-pairing-views front-end API does not list it.

---

## Back-end counterpart: `ManagerSettings`, realtime events, Web API {#backend}

### Reading app settings from the app

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const username = this.homey.settings.get('username');
    this.log('username is', username);

    // React to what the settings page writes
    this.homey.settings.on('set', (key) => {
      if (key === 'username' || key === 'password') {
        this.reconnect().catch(this.error);
      }
    });

    this.homey.settings.on('unset', (key) => {
      this.log('setting removed:', key);
    });
  }

  async reconnect() {
    // ...
  }

}

module.exports = MyApp;
```

| `ManagerSettings` member | Signature | Description |
| --- | --- | --- |
| `get(key)` | `any` | Get a setting. |
| `set(key, value)` | — | Set a setting; must be JSON-serializable. |
| `unset(key)` | — | Delete a setting. |
| `getKeys()` | `string[]` | All setting keys. |
| `.on('set', key => …)` | — | Fired when a setting has been set. |
| `.on('unset', key => …)` | — | Fired when a setting has been unset. |

App settings survive app restarts and are deleted when the app is uninstalled. Full storage-options
comparison (device settings vs device store vs app settings vs `/userdata/` vs `env.json`) is in
`references/app-and-manifest.md`.

### Pushing data to an open settings page

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.pollInterval = this.homey.setInterval(() => {
      this.pushStatus().catch(this.error);
    }, 10_000);
  }

  async pushStatus() {
    // One-way event to any subscribing client, e.g. a browser showing a settings view page
    await this.homey.api.realtime('status', { online: true, at: Date.now() });
  }

  async onUninit() {
    this.homey.clearInterval(this.pollInterval);
  }

}

module.exports = MyApp;
```

The settings page receives it with `Homey.on('status', data => …)`.

### Web API routes used by a settings page

```jsonc
// /.homeycompose/app.json
{
  "api": {
    "getStatus": { "method": "GET",  "path": "/status" },
    "testLogin": { "method": "POST", "path": "/login" }
  }
}
```

```javascript
// /api.js
'use strict';

module.exports = {
  async getStatus({ homey }) {
    return homey.app.getStatus();
  },

  async testLogin({ homey, body }) {
    return homey.app.testLogin(body.username, body.password);
  },
};
```

Route options: `method` (`"GET"`, `"POST"`, `"PUT"`, `"DELETE"` or an array of these), `path`
(`"/"`, `"/:foo"`, `"/bar/:foo"`) and `public` (default `false`). Endpoints are protected by default;
the requesting user needs permission to your app, which is granted by default after installation.
Details in `references/web-api-and-realtime.md`.

---

## Worked examples {#examples}

### Promise-based settings page with validation and a loading button

```html
<!DOCTYPE html>
<html>
  <head>
    <script type="text/javascript" src="/homey.js" data-origin="settings"></script>
  </head>
  <body>
    <header class="homey-header">
      <h1 class="homey-title" data-i18n="settings.title"></h1>
      <p class="homey-subtitle" data-i18n="settings.subtitle"></p>
    </header>

    <form class="homey-form" id="form">
      <fieldset class="homey-form-fieldset">
        <legend class="homey-form-legend">Account</legend>

        <div class="homey-form-group">
          <label class="homey-form-label" for="host">Host</label>
          <input class="homey-form-input" id="host" type="url" value="" />
        </div>

        <div class="homey-form-group">
          <label class="homey-form-label" for="username">Username</label>
          <input class="homey-form-input" id="username" type="text" value="" />
        </div>

        <div class="homey-form-group">
          <label class="homey-form-label" for="password">Password</label>
          <input class="homey-form-input" id="password" type="password" value="" />
        </div>

        <div class="homey-form-group">
          <label class="homey-form-label" for="interval">Poll interval (s)</label>
          <select class="homey-form-select" id="interval">
            <option value="30">30</option>
            <option value="60">60</option>
            <option value="300">300</option>
          </select>
        </div>
      </fieldset>

      <button type="button" id="save" class="homey-button-primary-full">Save changes</button>
    </form>

    <script type="text/javascript">
      async function onHomeyReady(Homey) {
        const $ = (id) => document.getElementById(id);
        const save = $('save');

        // Load everything BEFORE calling ready() to avoid flickering
        try {
          const settings = await Homey.get();            // all settings at once
          $('host').value = settings.host || '';
          $('username').value = settings.username || '';
          $('password').value = settings.password || '';
          $('interval').value = String(settings.interval || 60);
        } catch (err) {
          await Homey.alert(err.message || String(err));
        }

        Homey.ready();

        save.addEventListener('click', async () => {
          save.classList.add('is-loading');
          save.setAttribute('disabled', 'disabled');
          try {
            const ok = await Homey.api('POST', '/login', {
              host: $('host').value,
              username: $('username').value,
              password: $('password').value,
            });
            if (!ok) throw new Error(Homey.__('settings.error.invalid_credentials'));

            await Homey.set('host', $('host').value);
            await Homey.set('username', $('username').value);
            await Homey.set('password', $('password').value);
            await Homey.set('interval', Number($('interval').value));

            await Homey.alert(Homey.__('settings.saved'));
          } catch (err) {
            await Homey.alert(err.message || String(err));
          } finally {
            save.classList.remove('is-loading');
            save.removeAttribute('disabled');
          }
        });
      }
    </script>
  </body>
</html>
```

### Destructive action behind a confirm dialog

```html
<button id="reset" class="homey-button-danger-shadow">Reset all data</button>

<script type="text/javascript">
  document.getElementById('reset').addEventListener('click', async () => {
    const ok = await Homey.confirm(Homey.__('settings.confirm_reset'));
    if (!ok) return;

    await Homey.api('POST', '/reset', null);
    await Homey.alert(Homey.__('settings.reset_done'));
  });
</script>
```

Callback form of the same dialog (legacy, still supported):

```javascript
Homey.confirm('Reset all data?', function (err, ok) {
  if (err) return Homey.alert(err);
  if (!ok) return;
  Homey.api('POST', '/reset', null, function (err2) {
    if (err2) return Homey.alert(err2);
  });
});
```

---

## Homey style library — HTML & CSS {#style-library}

> Availability: "These CSS classes are available on Homey Cloud, and on Homey Pro since **v8.1.0**."
> Individual classes marked **v8.1.1** below need that version.

The style library is the key to a consistent user experience across all Homey apps; prefer it over
custom styling. None of the documented examples import a stylesheet — the classes come with the view
itself, so just use them.

### Header and titles

For custom pairing screens and app settings you might want to use the default header with title and
an optional subtitle. `homey-header` creates the spacing and the divider line between your title(s)
and the rest of the page.

| CSS class | HTML |
| --- | --- |
| `.homey-header` | `<header class="homey-header"></header>` |
| `.homey-title` | `<h1 class="homey-title"></h1>` |
| `.homey-subtitle` | `<p class="homey-subtitle"></p>` |

```html
<header class="homey-header">
  <h1 class="homey-title" data-i18n="settings.title">
    <!-- This will be filled with the translated string with key 'settings.title'. -->
  </h1>
  <p class="homey-subtitle" data-i18n="settings.subtitle">
    <!-- This will be filled with the translated string with key 'settings.subtitle'. -->
  </p>
</header>
```

### Forms

| CSS class | HTML |
| --- | --- |
| `.homey-form` | `<form class="homey-form"></form>` |

```html
<form class="homey-form">
 <!-- Your form html here -->
</form>
```

#### Fieldset and legend

A fieldset creates larger sections in your form. **Always** give it a
`<legend class="homey-form-legend">` title.

| CSS class | HTML |
| --- | --- |
| `.homey-form-fieldset` | `<fieldset class="homey-form-fieldset"></fieldset>` |
| `.homey-form-legend` | `<legend class="homey-form-legend"></legend>` |

```html
<fieldset class="homey-form-fieldset">
  <legend class="homey-form-legend"></legend>
  <!-- ... -->
</fieldset>
```

#### Groups

`homey-form-group` combines a label with an input field and creates equal vertical spacing between
all inputs.

| CSS class | HTML |
| --- | --- |
| `.homey-form-group` | `<div class="homey-form-group"></div>` |

```html
<div class="homey-form-group">
  <label class="homey-form-label" for="target">label</label>
  <input class="homey-form-input" id="target" type="text" value=""/>
</div>
```

#### Basic input & label

| CSS class | HTML |
| --- | --- |
| `.homey-form-label` | `<label class="homey-form-label" for="target"></label>` |
| `.homey-form-input` | `<input class="homey-form-input" id="target" type="text" value=""/>` |

`.homey-form-input` can be used for the input types `text`, `number`, `password` and `url`.

```html
<form class="homey-form">
  <fieldset class="homey-form-fieldset">
    <legend class="homey-form-legend">Login data</legend>

    <div class="homey-form-group">
      <label class="homey-form-label" for="username">Username</label>
      <input class="homey-form-input" id="username" type="text" value=""/>
    </div>
    <div class="homey-form-group">
      <label class="homey-form-label" for="password">Password</label>
      <input class="homey-form-input" id="password" type="password" value=""/>
    </div>
    <!-- ... -->
  </fieldset>
</form>
```

#### Radio input

Radio set:

| CSS class | HTML |
| --- | --- |
| `.homey-form-radio-set` | `<fieldset class="homey-form-radio-set"></fieldset>` |
| `.homey-form-radio-set-title` | `<legend class="homey-form-radio-set-title"></legend>` |

Radio buttons:

| CSS class | HTML |
| --- | --- |
| `.homey-form-radio` | `<label class="homey-form-radio"></label>` |
| `.homey-form-radio-input` | `<input class="homey-form-radio-input">` |
| `.homey-form-radio-checkmark` | `<span class="homey-form-radio-checkmark"></span>` |
| `.homey-form-radio-text` | `<span class="homey-form-radio-text"></span>` |

Radio buttons should be grouped in fieldsets; you can nest fieldsets with different classes.

```html
<form class="homey-form">
  <!-- ... -->
  <fieldset class="homey-form-fieldset">
    <legend class="homey-form-legend">Multiple choice questions</legend>

    <div class="homey-form-group">
      <fieldset class="homey-form-radio-set">
        <legend class="homey-form-radio-set-title">Group of radio buttons</legend>

        <label class="homey-form-radio">
          <input class="homey-form-radio-input" type="radio" name="radio-example"/>
          <span class="homey-form-radio-checkmark"></span>
          <span class="homey-form-radio-text">Radio label 1</span>
        </label>

        <label class="homey-form-radio">
          <input class="homey-form-radio-input" type="radio" name="radio-example"/>
          <span class="homey-form-radio-checkmark"></span>
          <span class="homey-form-radio-text">Radio label 2</span>
        </label>

        <label class="homey-form-radio">
          <input class="homey-form-radio-input" type="radio" name="radio-example"/>
          <span class="homey-form-radio-checkmark"></span>
          <span class="homey-form-radio-text">Radio label 3</span>
        </label>
      </fieldset>
    </div>
    <!-- ... -->
  </fieldset>
</form>
```

#### Checkbox input

Checkbox set:

| CSS class | HTML |
| --- | --- |
| `.homey-form-checkbox-set` | `<fieldset class="homey-form-checkbox-set"></fieldset>` |
| `.homey-form-checkbox-set-title` | `<legend class="homey-form-checkbox-set-title"></legend>` |

Checkboxes:

| CSS class | HTML |
| --- | --- |
| `.homey-form-checkbox` | `<label class="homey-form-checkbox"></label>` |
| `.homey-form-checkbox-input` | `<input class="homey-form-checkbox-input">` |
| `.homey-form-checkbox-checkmark` | `<span class="homey-form-checkbox-checkmark"></span>` |
| `.homey-form-checkbox-text` | `<span class="homey-form-checkbox-text"></span>` |

> **Doc inconsistency:** the styleguide's checkbox-set table shows the HTML snippet
> `<legend class="homey-form-radio-checkbox-set-title">` while naming the class
> `.homey-form-checkbox-set-title`. The worked example on the same page uses
> `homey-form-checkbox-set-title` — use that one.

```html
<div class="homey-form-group">
  <fieldset class="homey-form-checkbox-set">
    <legend class="homey-form-checkbox-set-title">Group of checkbox buttons</legend>

    <label class="homey-form-checkbox">
      <input class="homey-form-checkbox-input" type="checkbox" name="checkbox-example"/>
      <span class="homey-form-checkbox-checkmark"></span>
      <span class="homey-form-checkbox-text">Checkbox label 1</span>
    </label>

    <label class="homey-form-checkbox">
      <input class="homey-form-checkbox-input" type="checkbox" name="checkbox-example"/>
      <span class="homey-form-checkbox-checkmark"></span>
      <span class="homey-form-checkbox-text">Checkbox label 2</span>
    </label>

    <label class="homey-form-checkbox">
      <input class="homey-form-checkbox-input" type="checkbox" name="checkbox-example"/>
      <span class="homey-form-checkbox-checkmark"></span>
      <span class="homey-form-checkbox-text">Checkbox label 3</span>
    </label>
  </fieldset>
</div>
```

#### Select

| CSS class | HTML |
| --- | --- |
| `.homey-form-select` | `<select class="homey-form-select"><option value="1">Option 1</option></select>` |

```html
<div class="homey-form-group">
  <label class="homey-form-label" for="select-example">Select your option</label>
  <select class="homey-form-select" name="select-example" id="select-example">
    <option value="1">Option 1</option>
    <option value="2">Option 2</option>
    <option value="3">Option 3</option>
  </select>
</div>
```

#### Textarea

| CSS class | HTML |
| --- | --- |
| `.homey-form-textarea` | `<textarea class="homey-form-textarea"></textarea>` |

```html
<div class="homey-form-group">
  <label for="textarea-example-1" class="homey-form-label">Label for textarea</label>
  <textarea class="homey-form-textarea" name="textarea-example-1" id="textarea-example-1" rows="10"
            placeholder="type here your text"></textarea>
</div>
```

### Buttons

**Composition rule:** every button class starts with `.homey-button`, followed by a *color variant*
(`-primary`, `-secondary`, `-danger`), which you can further adjust with the `-full`, `-shadow` and
`-small` parameters — ending up with a class such as `.homey-button-primary-shadow-full`.

| CSS class | HTML | Since |
| --- | --- | --- |
| `.homey-button-primary` | `<button class="homey-button-primary"></button>` | v8.1.0 |
| `.homey-button-primary-full` | `<button class="homey-button-primary-full"></button>` | v8.1.0 |
| `.homey-button-primary-shadow` | `<button class="homey-button-primary-shadow"></button>` | v8.1.0 |
| `.homey-button-primary-shadow-full` | `<button class="homey-button-primary-shadow-full"></button>` | v8.1.0 |
| `.homey-button-transparent` | `<button class="homey-button-transparent"></button>` | v8.1.0 |
| `.homey-button-secondary-shadow` | `<button class="homey-button-secondary-shadow"></button>` | **v8.1.1** |
| `.homey-button-danger-shadow` | `<button class="homey-button-danger-shadow"></button>` | **v8.1.1** |
| `.homey-button-small` | `<button class="homey-button-small"></button>` | **v8.1.1** |

#### Disabled state

| CSS class | HTML |
| --- | --- |
| `.homey-button-{variant}.is-disabled` | `<button class="homey-button-primary is-disabled"></button>` |
| `.homey-button-{variant}[disabled=disabled]` | `<button class="homey-button-primary" disabled="disabled"></button>` |

#### Loading state

| CSS class | HTML |
| --- | --- |
| `.homey-button-{variant}.is-loading` | `<button class="homey-button-primary-full is-loading"></button>` |

*(The styleguide writes this row as `.homey-button-primary-{variant}.is-loading`; its own example is
`.homey-button-primary-full.is-loading`, i.e. append `.is-loading` to whatever button class you use.)*

### Complete class index (custom views)

| Group | Classes |
| --- | --- |
| Header | `.homey-header`, `.homey-title`, `.homey-subtitle` |
| Form containers | `.homey-form`, `.homey-form-fieldset`, `.homey-form-legend`, `.homey-form-group` |
| Text inputs | `.homey-form-label`, `.homey-form-input`, `.homey-form-select`, `.homey-form-textarea` |
| Radio | `.homey-form-radio-set`, `.homey-form-radio-set-title`, `.homey-form-radio`, `.homey-form-radio-input`, `.homey-form-radio-checkmark`, `.homey-form-radio-text` |
| Checkbox | `.homey-form-checkbox-set`, `.homey-form-checkbox-set-title`, `.homey-form-checkbox`, `.homey-form-checkbox-input`, `.homey-form-checkbox-checkmark`, `.homey-form-checkbox-text` |
| Buttons | `.homey-button-primary`, `.homey-button-primary-full`, `.homey-button-primary-shadow`, `.homey-button-primary-shadow-full`, `.homey-button-transparent`, `.homey-button-secondary-shadow`, `.homey-button-danger-shadow`, `.homey-button-small` |
| Button states | `.is-disabled`, `.is-loading`, `[disabled=disabled]` |

> **There is no documented list, card, table, badge, toggle/switch, slider, tab or modal component**
> in the custom-views style library, and no documented dark-mode class for settings/pair views. If you
> need one, write your own CSS — do not invent `.homey-*` class names, they will simply not exist.

---

## Design tokens (CSS custom properties) {#tokens}

> **Scope warning.** The CSS custom properties below are documented on the **widget** styling page
> (`/the-basics/widgets/styling`), which states up front: *"Styling for widgets is not the same as for
> custom views. While there are some variables and classes with the same name, the actual styling
> might differ."* The custom-views styleguide documents **no** CSS variables at all. Treat these as
> widget tokens; if you use them in a settings or pairing view, always supply a fallback —
> `padding: var(--homey-su-4, 16px)` — and verify visually on a real Homey. Full widget context is in
> `references/widgets.md`.

### Space units

Base unit is 4px; every derived variable is a multiple of it. Space units are for margins/padding,
not for `width`/`height`.

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

### Font size

| CSS variable | Value | Purpose |
| --- | --- | --- |
| `--homey-font-size-xxlarge` | 32px | Used for numbers only. |
| `--homey-font-size-xlarge` | 24px | Use sparingly, only for short phrases or single words that really have to stand out. |
| `--homey-font-size-large` | 20px | Used for numbers only. |
| `--homey-font-size-default` | 17px | Default for most text. |
| `--homey-font-size-small` | 14px | For captions, tables, underneath other text, or inside specific elements. |

### Line height (always pair with the matching font size)

| CSS variable | Value | Use with |
| --- | --- | --- |
| `--homey-line-height-xxlarge` | 40px | `--homey-font-size-xxlarge` |
| `--homey-line-height-xlarge` | 32px | `--homey-font-size-xlarge` |
| `--homey-line-height-large` | 28px | `--homey-font-size-large` |
| `--homey-line-height-default` | 24px | `--homey-font-size-default` |
| `--homey-line-height-small` | 20px | `--homey-font-size-small` |

### Font weight

| CSS variable | Value | Purpose |
| --- | --- | --- |
| `--homey-font-weight-bold` | 700 | Used for titles. |
| `--homey-font-weight-medium` | 500 | Used to make text stand out, for strong text or subtitles. |
| `--homey-font-weight-regular` | 400 | Default for most text. |

Allowed size/weight combinations: `xxlarge` → bold only; `xlarge` → bold only; `large` → medium only;
`default` → regular, medium or bold; `small` → regular only.

### Text color

| CSS variable | Purpose |
| --- | --- |
| `--homey-text-color` | Default text color. |
| `--homey-text-color-light` | Text that's less important, or disabled. |
| `--homey-text-color-white` | White text, independent of light or dark mode. For dark or colored backgrounds. |
| `--homey-text-color-blue` | Blue text. |
| `--homey-text-color-green` | Green text. |
| `--homey-text-color-orange` | Orange text. |
| `--homey-text-color-red` | Red text. |
| `--homey-text-color-highlight` | Text to highlight something. |
| `--homey-text-color-success` | Text for success case. |
| `--homey-text-color-warning` | Text for warnings. |
| `--homey-text-color-danger` | Text for errors. |

### Background, palette and semantic colors

| CSS variable | Value / purpose |
| --- | --- |
| `--homey-background-color` | `--homey-color-mono-000` (white) in light mode, dark grey in dark mode. |
| `--homey-color-mono-000` … `--homey-color-mono-1000` | Grayscale ramp; `000` is white in light mode, `1000` is black in light mode. |
| `--homey-color-blue-050` … `--homey-color-blue-900` | Blue ramp; identical in light and dark mode. |
| `--homey-color-green-050` … `--homey-color-green-900` | Green ramp. |
| `--homey-color-orange-500` | Orange — **only the `500` value exists**. |
| `--homey-color-red-050` … `--homey-color-red-900` | Red ramp. |
| `--homey-color-white` | White, independent of light or dark mode. |
| `--homey-color-blue` | General purpose blue. |
| `--homey-color-green` | General purpose green. |
| `--homey-color-orange` | General purpose orange. |
| `--homey-color-red` | General purpose red. |
| `--homey-color-highlight` | Highlight. |
| `--homey-color-success` | Success. |
| `--homey-color-warning` | Warning. |
| `--homey-color-danger` | Danger. |

Prefer the semantic variables over raw palette values — they are defined *in terms of* the palette,
so no new colors are introduced.

### Lines, borders and radius

| CSS variable | Purpose |
| --- | --- |
| `--homey-line-color` | Default line color, used for most lines. |
| `--homey-line-color-light` | Light lines that should stand out less. |
| `--homey-line` | Complete 1px solid line shorthand for most lines. |
| `--homey-line-light` | Complete shorthand for light lines. |
| `--homey-border-radius-default` | Default border radius. |
| `--homey-border-radius-small` | Only where the default border radius is too big. |

### Icons

| CSS variable | Value | Purpose |
| --- | --- | --- |
| `--homey-icon-color-dark` | — | Default icon color. |
| `--homey-icon-color-light` | — | Less important icons or disabled states. |
| `--homey-icon-color-white` | — | White icons, independent of light or dark mode. |
| `--homey-icon-color-blue` | — | Blue icons. |
| `--homey-icon-color-green` | — | Green icons. |
| `--homey-icon-color-orange` | — | Orange icons. |
| `--homey-icon-color-red` | — | Red icons. |
| `--homey-icon-size-medium` | 20px | Default icon size. |
| `--homey-icon-size-regular` | 16px | In line with regular text. |
| `--homey-icon-size-small` | 14px | In line with small text. |

A `.homey-custom-icon-*` element is coloured and sized by setting the `--homey-icon-color` and
`--homey-icon-size` custom properties on it from one of the variables above:

```css
.homey-custom-icon-example {
  --homey-icon-color: var(--homey-icon-color-green);
  --homey-icon-size: var(--homey-icon-size-small);

  -webkit-mask-image: url('example.svg'); /* Browser support. */
  mask-image: url('example.svg');
}
```

### Light & dark mode (widgets)

The dashboard switches between light and dark mode based on the user's settings; every palette
variable adapts automatically (the actual color may differ between modes). Adding `.homey-dark-mode`
to an element forces dark mode regardless of the user's setting, and `.homey-dark-mode my-selector`
lets you target dark mode from your own CSS.

```html
<body class="homey-widget homey-dark-mode">
  <!-- Content of you widget here. -->
</body>
```

### Widget-only classes (for completeness)

| Group | Classes |
| --- | --- |
| Padding | `.homey-widget` (`--homey-su-4`), `.homey-widget-small` (`--homey-su-2`), `.homey-widget-full` (0) |
| Text presets | `.homey-text-bold`, `.homey-text-medium`, `.homey-text-regular`, `.homey-text-small`, `.homey-text-small-light` |
| Alignment | `.homey-text-align-left`, `.homey-text-align-center`, `.homey-text-align-right` |
| Borders | `.homey-border`, `.homey-border-top`, `.homey-border-right`, `.homey-border-bottom`, `.homey-border-left` |
| Tables | `.homey-table`, `.homey-table-striped` |
| Dark mode | `.homey-dark-mode` |
| Custom icons | any class starting with `.homey-custom-icon-` (set `mask-image` + `-webkit-mask-image`) |

---

## Right-to-left (RTL) styling {#rtl}

Homey supports RTL layouts for languages such as Arabic (`ar`). RTL layout direction is handled
automatically by Homey and all **built-in** pairing views support it out of the box, but **custom**
views may require additional styling. Keep RTL in mind from the start.

**Prefer logical properties over left/right:**

```css
/* Preferred */
padding-inline-start: 16px;
padding-inline-end: 16px;
margin-inline-start: 8px;

/* Avoid */
padding-left: 16px;
padding-right: 16px;
margin-left: 8px;
```

**Use direction-aware text alignment** — `text-align: start;` — and avoid hard-coding left or right
unless absolutely necessary.

**Use `:dir(rtl)` for direction-specific adjustments.** Some visuals are inherently directional:

```css
.chevron:dir(rtl) {
  transform: scaleX(-1);
}
```

Common cases: arrows and chevrons, animations and transitions, progress indicators, absolute
positioning.

**Be careful with absolute positioning** — prefer logical positioning (`inset-inline-start: 0;`) and
only fall back to `left` / `right` with a `:dir(rtl)` override when needed.

---

## Homey Cloud restrictions {#homey-cloud}

> "To simplify the user experience, custom app settings views are **not supported on Homey Cloud**."

| On Homey Cloud | Consequence |
| --- | --- |
| No `/settings/index.html` | Ask for the information during **pairing** instead. |
| Information needs updating later | Use the **"re-pair"** pairing views so the user's Flows don't break. |
| No app Web API | `Homey.api()` has nothing to call — apps on Homey Cloud are not allowed to expose a Web API. |
| No `ManagerCloud#getLocalAddress()`, no LAN access | The LAN-file trick in [Gotchas](#gotchas) is Homey Pro / Self-Hosted Server only. |
| Style library | The Homey CSS classes **are** available on Homey Cloud (they are used by pairing views). |

`ManagerSettings` itself still works on Homey Cloud — only the custom *view* is disallowed. Full
restriction list: `references/homey-cloud.md`.

---

## Legacy manifest `settings` array {#legacy-settings}

The App Manifest JSON Schema still accepts a top-level `settings` array (`#/definitions/appSettings`)
— a declarative, typed app-settings form. It is **not documented on the docs site**; the documented
way to build an app settings page is `/settings/index.html`. Do not use it for new apps — you will
find it only in old apps. Everything below is derived from `#/definitions/appSettings` in the schema
used by `homey app validate`, which is authoritative.

`settings` is an array of entries. Each entry matches exactly one of **five** shapes, selected by its
`type` — the ten types are spread across those five shapes:

| Shape (`type` values) | Required keys | Optional keys | `value` type |
| --- | --- | --- | --- |
| `text`, `password`, `textarea`, `label` | `id`, `type`, `title` | `hint`, `value`, `pattern` | `string` |
| `number`, `slider` | `id`, `type`, `title` | `hint`, `value`, `units`, `min`, `max`, `step` | `number` |
| `radio`, `dropdown` | `id`, `type`, `title`, `values` | `hint`, `value` | `string` |
| `checkbox` | `id`, `type`, `title` | `hint`, `value` | `boolean` |
| `group` | `type`, `title`, `children` | *(none)* | *(n/a)* |

Key reference — these are **all** the keys the schema defines; there are no others:

| Key | Type | Notes |
| --- | --- | --- |
| `id` | `string` | The `ManagerSettings` key the entry reads and writes. **Absent from the `group` shape** — a group has no `id`, and it is not in its required list either. |
| `type` | `string` | One of the ten types above. |
| `title` | i18n object | `{ "en": "…" }`. **Required on every shape, including `group`.** |
| `hint` | i18n object | Optional help text. Not defined on `group`. |
| `value` | per-shape | Default value; `string`, `number` or `boolean` per the table above. Not defined on `group`. |
| `pattern` | `string` | **`text` / `password` / `textarea` / `label` only.** |
| `units` | i18n object | **`number` / `slider` only.** |
| `min`, `max` | `number` | **`number` / `slider` only.** |
| `step` | `number`, `minimum: 0` | **`number` / `slider` only.** |
| `values` | array | **`radio` / `dropdown` only**, and **required** for them. Each item is an object with required `id` (`string`) and required `title` (i18n object) — nothing else. |
| `children` | array | **`group` only**, and **required** for it. Recursively another `appSettings` array, so groups may nest. |

Do not carry keys over from driver settings: `label`, `highlight`, `attr` and `zwave` exist in
`#/definitions/driverSettings` but **not** in `#/definitions/appSettings` (`label` is an app-settings
*type*, not a key). There is likewise no `name`, `description`, `placeholder`, `required`,
`decimals`, `multiple` or `platforms` key on an app-settings entry.

```json
// /.homeycompose/app.json (or /app.json)
{
  "settings": [
    {
      "type": "group",
      "title": { "en": "Account" },
      "children": [
        { "id": "username", "type": "text",     "title": { "en": "Username" }, "value": "" },
        { "id": "password", "type": "password", "title": { "en": "Password" }, "value": "" }
      ]
    },
    {
      "id": "interval",
      "type": "number",
      "title": { "en": "Poll interval" },
      "hint":  { "en": "How often to poll the device." },
      "units": { "en": "s" },
      "value": 60,
      "min": 10,
      "max": 3600,
      "step": 10
    },
    {
      "id": "mode",
      "type": "dropdown",
      "title": { "en": "Mode" },
      "value": "auto",
      "values": [
        { "id": "auto",   "title": { "en": "Automatic" } },
        { "id": "manual", "title": { "en": "Manual" } }
      ]
    },
    { "id": "verbose", "type": "checkbox", "title": { "en": "Verbose logging" }, "value": false }
  ]
}
```

> **Schema vs. docs discrepancy:** the documentation site describes no manifest-driven app-settings
> form at all, yet the validator schema fully defines and validates the top-level `settings` array.
> Following the schema, such a manifest passes `homey app validate` — but nothing in the published
> documentation promises how (or whether) it is rendered. Build `/settings/index.html` instead.
>
> **Gotcha — `oneOf`, not `anyOf`.** The five shapes are matched with `oneOf` and none of them sets
> `additionalProperties: false`, so a key borrowed from the wrong shape (`min` on a `text` entry,
> `units` on a `checkbox`) is silently accepted and then ignored — you get no error, just a setting
> that does not behave as intended. A misspelled `type`, by contrast, matches **zero** branches and
> fails with the unhelpful "should match exactly one schema in oneOf"; check the `type` string first
> when that error appears.

---

## Gotchas {#gotchas}

- **Custom app settings views are not allowed on Homey Cloud.** Design the app so all required
  information is collected during pairing, and expose updates through a *repair* view. Only add
  `/settings/` when the app targets `"platforms": ["local"]` (or accept that the page is invisible on
  Cloud).
- **Most apps should not have a settings page at all.** If the data belongs to one device, it belongs
  in **Device Settings** (user-visible) or the **Device Store** (internal) — see
  `references/drivers-and-devices.md`. App settings are for genuinely app-wide values.
- **The page is a sandboxed iframe.** `window.open`, `window.print` and browser downloads are
  **blocked**. To hand a user a generated file (a printable report, an export), serve it over the LAN
  from the app and open it with `Homey.openURL(url)`:

  ```javascript
  // app.js — serve the report over the LAN (Homey Pro only; Homey Cloud has no LAN access)
  'use strict';

  const Homey = require('homey');
  const http = require('http');
  const crypto = require('crypto');

  class MyApp extends Homey.App {

    async serveReport(html) {
      const token = crypto.randomBytes(16).toString('hex');       // random one-time token
      const server = http.createServer((req, res) => {
        if (req.url !== `/report?token=${token}`) { res.writeHead(403); return res.end(); }
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(html);
      });
      await new Promise((resolve) => server.listen(0, resolve));  // 0 = any free port
      const { port } = server.address();
      const address = await this.homey.cloud.getLocalAddress();   // e.g. "192.168.1.20:80"
      const host = address.split(':')[0];
      this.homey.setTimeout(() => server.close(), 5 * 60 * 1000); // short TTL, then tear down
      return `http://${host}:${port}/report?token=${token}`;
    }

  }

  module.exports = MyApp;
  ```

  ```javascript
  // settings/index.html — open it externally (works on desktop AND mobile)
  const url = await Homey.api('POST', '/report');   // your api.js returns the LAN URL
  Homey.openURL(url);
  ```

- **Never branch on the return value of `window.open`.** On **desktop** a blocked `window.open`
  returns `null` (easy to detect), but in the **mobile** Homey app it returns a **non-null but
  invisible** window — so `if (win) { win.document.write(html) }` silently swallows the content and
  the feature looks broken *only on mobile*. Use the LAN + `Homey.openURL(url)` path
  **unconditionally**.
- **`homey app run` uses Docker bridge networking**, so a LAN port the app opens is unreachable from
  your phone or PC. The same code works under `homey app install` (production networking). Test
  LAN-served content with `install`, not `run`.
- **Secure anything you serve over the LAN.** It is plain HTTP on the local network: gate it behind a
  generated one-time token/password, give it a short TTL, and tear the server down afterwards.
- **`Homey.ready()` is not optional.** Forget it and the settings page never appears — it looks like a
  blank/hanging screen with no error. Do your loading work first, then call it.
- **Do the initial `Homey.get()` before `Homey.ready()`** to prevent the fields visibly flickering
  from empty to filled.
- **`Homey.set()` values must be JSON-serializable.** `undefined`, functions, `Date` objects and class
  instances will not round-trip; store ISO strings/numbers.
- **Callbacks are Node-style, promises are the future.** `Homey.get(name, (err, value) => …)` — the
  error is the *first* argument, and `Homey.confirm(msg, (err, ok) => …)` puts the boolean *second*.
  Callbacks "will be removed in a later SDK version"; prefer `await`.
- **`/homey.js` must be loaded from the absolute path `/homey.js` with `data-origin="settings"`.**
  Copying the file into `/settings/` or omitting the attribute breaks the bridge and `onHomeyReady` is
  never called.
- **`onHomeyReady` must be a global function**, not a module-scoped one. Inside
  `<script type="module">` declarations are module-scoped and Homey will not find it — use a classic
  `<script>` (or assign `window.onHomeyReady = …`).
- **The `Homey` object differs per view type.** `Homey.emit()`, `Homey.setTitle()`,
  `Homey.showLoadingOverlay()`, `Homey.createDevice()` etc. are pairing-view API;
  `Homey.getSettings()` is the *widget's* settings, not app settings. See
  [the full index](#full-api).
- **`Homey.getLanguage()` is not documented anywhere** — do not call it.
- **`Homey.api()` needs `api` routes in the manifest and an `/api.js`**, and does not exist on Homey
  Cloud. A 404 from `Homey.api()` almost always means the route name/path in `.homeycompose/app.json`
  and the exported function name in `api.js` disagree.
- **If a `/settings/` folder exists, `/settings/index.html` must exist** or `homey app validate`
  fails. The CLI also injects `hasSettings: true` into the generated `/app.json` — never write it
  yourself.
- **Style-library classes need Homey Pro v8.1.0+** (v8.1.1 for `.homey-button-secondary-shadow`,
  `.homey-button-danger-shadow`, `.homey-button-small`). If your `compatibility` range dips below
  that, the page still works but renders unstyled on old firmware.
- **Widget CSS variables are not guaranteed in settings/pair views** — the docs explicitly separate
  the two styling systems. Use fallbacks: `var(--homey-su-4, 16px)`.
- **RTL is your responsibility in custom views.** Use logical properties and `:dir(rtl)`; only
  built-in pairing views get RTL for free.
- **`this.homey.settings.on('set')` also fires for writes made by the settings page**, so a naive
  "reconnect on every change" handler will fire once per `Homey.set()` call. Debounce, or save all
  fields through a single Web API call.

---

## Sources

- <https://apps.developer.homey.app/advanced/custom-views> — Custom Views
- <https://apps.developer.homey.app/advanced/custom-views/app-settings> — App Settings
- <https://apps.developer.homey.app/advanced/custom-views/html-and-css-styling> — HTML & CSS Styling
- <https://apps.developer.homey.app/advanced/custom-views/custom-pairing-views> — Custom Pairing Views
  (front-end `Homey` API)
- <https://apps.developer.homey.app/the-basics/widgets> — Widgets (widget View API)
- <https://apps.developer.homey.app/the-basics/widgets/styling> — Widget Styling (CSS custom properties)
- <https://apps.developer.homey.app/the-basics/app/internationalization> — Internationalization
  (`data-i18n`, RTL)
- <https://apps.developer.homey.app/advanced/web-api> — Web API (routes, realtime events)
- <https://apps.developer.homey.app/guides/homey-cloud> — Homey Cloud (App Settings restriction)
- <https://apps.developer.homey.app/upgrade-guides/upgrading-to-sdk-v3> — Promises in App settings /
  Custom pair views
- <https://apps-sdk-v3.developer.homey.app/ManagerSettings.html> — `ManagerSettings`
