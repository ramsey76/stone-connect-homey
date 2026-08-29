# Cloud APIs: OAuth2 & Webhooks

How a Homey app authenticates against a manufacturer's Web API (OAuth2 through Athom's callback relay) and how it receives realtime push updates from that API (webhooks through Athom's forwarding service). Both exist because Homey sits behind the user's NAT and has no public, static URL.

Related: `references/pairing.md` (pair/repair sessions and system views), `references/wireless-lan-discovery.md` (local discovery) and the `references/wireless-*.md` files (Z-Wave, Zigbee, BLE, RF), `references/homey-cloud.md` (Bridge/Cloud platform restrictions).

---

## 1. `ManagerCloud` — the full API surface

Accessed as `this.homey.cloud` on App, Driver and Device.

| Method | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `createOAuth2Callback` | `(async) createOAuth2Callback(apiUrl)` | `Promise<CloudOAuth2Callback>` | `apiUrl: string` — Generate an OAuth2 Callback. |
| `createWebhook` | `(async) createWebhook(id, secret, data)` | `Promise<CloudWebhook>` | `id: string` (Webhook ID), `secret: string` (Webhook Secret), `data: object` (Webhook Data). |
| `getHomeyId` | `(async) getHomeyId()` | `Promise<string>` | Get Homey's Cloud ID. |
| `getLocalAddress` | `(async) getLocalAddress()` | `Promise<string>` | Get Homey's local address & port. **Not supported on Homey Cloud.** |
| `unregisterWebhook` | `(async) unregisterWebhook(webhook)` | `Promise<any>` | `webhook: CloudWebhook`. |

### `CloudOAuth2Callback`

> A OAuth2 Callback class that can be used to log-in using OAuth2.

| Event | Payload | Description |
| --- | --- | --- |
| `url` | `url: string` | The absolute URL to the sign-in page. The user must be redirected to this URL to complete the sign-in process. |
| `code` | `code: string \| Error` | The OAuth2 code, **or an `Error`** when something went wrong. The code can usually be swapped by the app for an access token. |

Both are `.on()` EventEmitter events and the object is chainable:

```javascript
let myOAuth2Callback = await this.homey.cloud.createOAuth2Callback(apiUrl);

myOAuth2Callback
  .on('url', url => {
    // the URL which should open in a popup for the user to login
  })
  .on('code', code => {
    // ... swap your code here for an access token
  });
```

### `CloudWebhook`

> A webhook class that can receive incoming messages.

| Member | Kind | Description |
| --- | --- | --- |
| `unregister()` | `(async) → Promise<any>` | Unregister the webhook. Shortcut for `ManagerCloud#unregisterWebhook`. |
| `.on('message')` | event | Fired when a webhook message has been received. |

`message` event payload — a single `args: object` with exactly three keys:

| Key | Type | Description |
| --- | --- | --- |
| `headers` | `object` | Received HTTP headers |
| `query` | `object` | Received HTTP query string |
| `body` | `object` | Received HTTP body |

---

## 2. OAuth2 — how Homey's callback relay works

OAuth2 is the standard smart-home manufacturers use to delegate user access to their Web API. You normally register an OAuth2 client on a developer website owned by the manufacturer, providing a *Name*, *Redirect URL*, *Scopes* and/or an *Image*.

Almost every provider requires the Redirect URL to be registered in advance for security reasons. Homey is behind a NAT and has no static URL to redirect to, so Athom hosts a fixed public redirect endpoint that relays the resulting `code` back into your app over Homey's cloud connection.

```
User taps "Log in" in the pair view
  → driver calls this.homey.cloud.createOAuth2Callback(authorizeUrl)
  → callback emits 'url'  →  driver does session.emit('url', url)
  → pair view opens that URL in a popup
  → user signs in at the provider
  → provider redirects to https://callback.athom.com/oauth2/callback?code=…
  → Athom relays the code to this Homey
  → callback emits 'code'  →  driver swaps code for tokens at TOKEN_URL
  → driver does session.emit('authorized')  →  view advances
```

**The Athom redirect URI is `https://callback.athom.com/oauth2/callback`.** It is the default `REDIRECT_URL` of `homey-oauth2app`'s `OAuth2Client`. It must be registered verbatim as an authorized redirect URI on the provider's OAuth2 client.

> Note: the official system-view example writes it with a trailing slash (`https://callback.athom.com/oauth2/callback/`) while `homey-oauth2app` uses it **without** the trailing slash. Most providers treat these as two different URIs — register the exact string your app sends, and prefer the no-trailing-slash form so it matches the library default.

---

## 3. The `login_oauth2` system pair view

**Usage:** `"template": "login_oauth2"` in a `pair` (and/or `repair`) step.

```json
{
  "name": { "en": "My Driver" },
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png"
  },
  "pair": [
    {
      "id": "login_oauth2",
      "template": "login_oauth2",
      "options": {
        "hint": "Login with your credentials",
        "button": "Log-in"
      }
    },
    {
      "id": "list_devices",
      "template": "list_devices",
      "navigation": { "next": "add_devices" }
    },
    {
      "id": "add_devices",
      "template": "add_devices"
    }
  ],
  "repair": [
    { "id": "login_oauth2", "template": "login_oauth2" }
  ]
}
```

### `login_oauth2` options

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `title` | translation object | | |
| `subtitle` | translation object | | |
| `hint` | translation object | `""` | |
| `button` | translation object | `""` | |

When either `hint` or `button` are set to a value, a button will appear and wait for the user to click it before opening the popup.

### The view ↔ driver event protocol

| Direction | Event | Payload | Meaning |
| --- | --- | --- | --- |
| driver → view | `session.emit('url', url)` | `string` | Open this URL in the login popup. |
| driver → view | `session.emit('authorized')` | — | Login succeeded; the view advances to the next step. |
| driver → view | `session.emit('error', message)` | `string` | Login failed; the view shows the error. |
| view → driver | `session.setHandler('showView', viewId => …)` | `string` | Called with `'login_oauth2'` when the view becomes visible — this is where you start the flow. |

`PairSession` methods you will use (from `Driver#onPair` / `Driver#onRepair`):

| Method | Returns | Description |
| --- | --- | --- |
| `emit(event, data)` | `Promise<any>` | Send an event to the pair view. |
| `setHandler(event, handler)` | `this` | Register an (async) handler for an event from the pair view. Chainable. |
| `showView(viewId)` | `Promise<void>` | Show a specific pairing step by its id. |
| `nextView()` | `Promise<void>` | Go to the next pairing step. |
| `prevView()` | `Promise<void>` | Go back to the previous pairing step. |
| `done()` | `Promise<void>` | Close the pairing session. |

---

## 4. Manual OAuth2 with `createOAuth2Callback()`

Use this when the provider deviates enough from RFC 6749 that `homey-oauth2app` is more fight than help, or when you need full control over token storage. Everything in this section applies to the library path too, because the library uses the exact same callback under the hood.

Minimal official shape:

```javascript
'use strict';

const Homey = require('homey');

const API_URL = 'https://api.myservice.com/oauth2/authorise?response_type=code';
// The official doc writes this with a trailing slash ('…/oauth2/callback/').
// Whichever form you pick, register that exact string at the provider — see §2.
const CALLBACK_URL = 'https://callback.athom.com/oauth2/callback';
const CLIENT_ID = Homey.env.CLIENT_ID;
const OAUTH_URL = `${API_URL}&client_id=${CLIENT_ID}&redirect_uri=${CALLBACK_URL}`;

class Driver extends Homey.Driver {

  async onPair(session) {
    const myOAuth2Callback = await this.homey.cloud.createOAuth2Callback(OAUTH_URL);

    myOAuth2Callback
      .on('url', (url) => {
        // send the URL to the front-end to open a popup
        session.emit('url', url).catch(this.error);
      })
      .on('code', (code) => {
        // ... swap your code here for an access token

        // tell the front-end we're done
        session.emit('authorized').catch(this.error);
      });
  }

}

module.exports = Driver;
```

### Complete, field-tested pair + repair driver

```javascript
'use strict';

const Homey = require('homey');

const CLIENT_ID = Homey.env.CLIENT_ID;
const REDIRECT_URI = 'https://callback.athom.com/oauth2/callback';
const SCOPES = [
  // A write scope does NOT imply read — request read scopes explicitly.
  'https://www.googleapis.com/auth/fitness.activity.read',
];

class MyDriver extends Homey.Driver {

  buildAuthorizeUrl() {
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,          // Pitfall 1: must be present here
      response_type: 'code',
      scope: SCOPES.join(' '),
      access_type: 'offline',              // ask for a refresh token
      prompt: 'consent',                   // force the refresh token even on re-auth
    });
    return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
  }

  async _handleOAuth2(session) {
    let started = false;                   // Pitfall 3: single-run latch
    const callback = await this.homey.cloud.createOAuth2Callback(this.buildAuthorizeUrl());

    callback
      .on('url', (url) => session.emit('url', url).catch(this.error))
      .on('code', async (code) => {
        if (started) return;
        started = true;
        try {
          if (code instanceof Error) throw code;            // 'code' may be an Error
          const tokens = await this.exchangeCode(code);      // POST to the token endpoint
          this._tokens = tokens;
          await session.emit('authorized');                  // Pitfall 2: BEFORE any done()
        } catch (err) {
          started = false;                                   // allow a retry in this session
          this.error(err);
          await session.emit('error', err.message || 'Login failed');
        }
      });
  }

  async onPair(session) {
    session.setHandler('showView', async (viewId) => {
      if (viewId === 'login_oauth2') await this._handleOAuth2(session);
    });

    session.setHandler('list_devices', async () => {
      const accounts = await this.listAccounts(this._tokens);
      return accounts.map((a) => ({
        name: a.name,
        data: { id: a.id },
        store: { tokens: this._tokens },   // persist per-device tokens in the store
      }));
    });
  }

  // Repair reuses the same OAuth2 flow, then writes fresh tokens back to the device store.
  async onRepair(session, device) {
    session.setHandler('showView', async (viewId) => {
      if (viewId !== 'login_oauth2') return;
      let started = false;
      const callback = await this.homey.cloud.createOAuth2Callback(this.buildAuthorizeUrl());
      callback
        .on('url', (url) => session.emit('url', url).catch(this.error))
        .on('code', async (code) => {
          if (started) return;
          started = true;
          try {
            if (code instanceof Error) throw code;
            const tokens = await this.exchangeCode(code);
            await device.setStoreValue('tokens', tokens);
            await session.emit('authorized');               // BEFORE done()
          } catch (err) {
            started = false;
            this.error(err);
            await session.emit('error', err.message || 'Re-authentication failed');
          }
        });
    });
  }

}

module.exports = MyDriver;
```

### Manual refresh-on-401 pattern

```javascript
async apiFetch(device, path, init = {}, retried = false) {
  let tokens = device.getStoreValue('tokens');
  const res = await fetch(`https://api.example.com${path}`, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${tokens.access_token}` },
  });

  if (res.status === 401 && !retried) {
    tokens = await this.refreshTokens(tokens.refresh_token);   // POST refresh_token to TOKEN_URL
    await device.setStoreValue('tokens', tokens);
    return this.apiFetch(device, path, init, true);            // retry exactly once
  }
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}
```

---

## 5. OAuth2 gotchas (field-tested, not in the official docs)

### ⚠️ Pitfall 1 — `createOAuth2Callback` does NOT append `redirect_uri`

`createOAuth2Callback(authorizeUrl)` uses the URL you give it **verbatim**. It does not add a `redirect_uri`. So the `authorizeUrl` you build must already contain:

```
redirect_uri=https://callback.athom.com/oauth2/callback
```

and that **exact** URI must be registered as an authorized redirect URI on the provider's OAuth client. If you omit it, Google (and most providers) reject the request:

```
Error 400: invalid_request — Missing required parameter: redirect_uri
```

`https://callback.athom.com/oauth2/callback` is the correct Athom callback host for cloud pairing (it is also the default `REDIRECT_URL` used by `homey-oauth2app`).

### ⚠️ Pitfall 2 — `emit('authorized')` must come BEFORE `session.done()`

In both **pair** and **repair** handlers, signal success to the view first, then close the session. `session.done()` destroys the pair session; if you call it before emitting `authorized`, any subsequent emit/navigation targets a session that no longer exists and you get:

```
404 Not Found: PairSession with ID … not found
```

So the order is always: exchange the code → store tokens → `await session.emit('authorized')` → (only then, if you close it manually) `session.done()`. In the standard `login_oauth2` flow the built-in view advances to the device list on `authorized`, so you usually don't call `done()` yourself at all.

### ⚠️ Pitfall 3 — the `login_oauth2` event protocol & the "started" latch

The `login_oauth2` pair view speaks a small protocol with your driver:

1. The view triggers the login; your driver emits **`url`** → the view opens that URL in a popup.
2. The user signs in; Athom relays the **`code`** back → your driver exchanges it for tokens.
3. Your driver emits **`authorized`** (success) or **`error`** (failure) → the view advances or shows the error.

If you guard the exchange with a "started" flag to avoid double-runs, **reset it in the catch branch** so a failed code exchange can be retried within the same pair session (otherwise the user must cancel and restart pairing).

### Further practical rules

| Rule | Why |
| --- | --- |
| Request a refresh token up front: `access_type=offline` **and** `prompt=consent`. | Google only returns a refresh token when consent is forced; without it the integration dies after the first access token expires. |
| **Scopes are not implied.** A write scope does **not** grant read. | Request `…readonly`/`…read` scopes explicitly for a read-only integration. |
| Refresh on `401` and retry **once**; if it 401s again, surface an auth error and call `device.setUnavailable()`. | Prompts the user to run *repair* instead of silently looping. |
| `code` in the `'code'` event may be an `Error` instance. | Always `if (code instanceof Error) throw code;` before using it as a string. |
| Secrets live in `/env.json` (gitignored), never in `app.json`. | See §7. |

---

## 6. `homey-oauth2app` — the recommended library

> The recommended way to create a Homey app for an OAuth2 Web API is by using `homey-oauth2app`. This module does all the heavy lifting related to OAuth2, such as logging in, obtaining an access token, refreshing tokens and making API calls. Because no API is the same, the module has been designed specifically to be extended to fit your Web API. Even if your device's Web API differs from the OAuth2 specification, methods can be overloaded to change behaviour.

Requires Homey Apps SDK v3. Current version: **3.7.2**.

```bash
npm install homey-oauth2app
```

Exports (`require('homey-oauth2app')`): `OAuth2App`, `OAuth2Driver`, `OAuth2Device`, `OAuth2Client`, `OAuth2Error`, `OAuth2Token`, `OAuth2Util`, and `fetch` (re-exported `node-fetch` v2).

**Rule of thumb:** all methods starting with `on` (for example `onRequestError`) are meant to be overloaded. Overloading any other method might break in the future, so be careful.

### 6.1 `OAuth2App` (extends `Homey.App`)

Statics:

| Static | Type | Default | Description |
| --- | --- | --- | --- |
| `OAUTH2_CLIENT` | `OAuth2Client` subclass | `OAuth2Client` | The client class instantiated per session. |
| `OAUTH2_DEBUG` | `boolean` | `false` | When `true`, calls `enableOAuth2Debug()` in `onInit` so `debug` events are logged. |
| `OAUTH2_MULTI_SESSION` | `boolean` | `false` | Allow more than one saved account. |
| `OAUTH2_DRIVERS` | `string[]` | every driver id in `Homey.manifest.drivers` | Drivers that use OAuth2. **Exclude drivers that never become ready**, otherwise session cleanup waits forever on `driver.ready()`. |

Do **not** override `onInit`/`onUninit` — override `onOAuth2Init` / `onOAuth2Uninit` instead. `onInit` enables debug, calls `setOAuth2Config()` automatically **only if** `OAUTH2_CLIENT.API_URL` **and** `OAUTH2_CLIENT.TOKEN_URL` are both set, then awaits `onOAuth2Init()`.

Methods:

| Method | Description |
| --- | --- |
| `async onOAuth2Init()` | Overload me. Your app logic (register Flow cards, etc.). |
| `async onOAuth2Uninit()` | Overload me. Called from `onUninit`. |
| `enableOAuth2Debug()` / `disableOAuth2Debug()` | Toggle logging of client `debug` events. |
| `setOAuth2Config({ … })` | Register a config. See table below. Throws `OAuth2Error('Duplicate Config ID')` if the id already exists. |
| `hasConfig({ configId })` → `boolean` | |
| `checkHasConfig({ configId })` | Throws `OAuth2Error('Invalid OAuth2 Config')`. |
| `getConfig({ configId })` | Returns the stored config object. |
| `hasOAuth2Client({ sessionId, configId })` → `boolean` | |
| `checkHasOAuth2Client({ sessionId, configId })` | Throws `OAuth2Error('Invalid OAuth2 Client')`. |
| `createOAuth2Client({ sessionId, configId })` → `OAuth2Client` | Instantiates and wires `log`/`error`/`debug`/`save`/`destroy` events, then calls `client.init()`. Throws `OAuth2Error('OAuth2 Client already exists')` when a client for that `sessionId`+`configId` is already in memory. |
| `getOAuth2Client({ sessionId, configId })` → `OAuth2Client` | Returns the in-memory client, or rehydrates one from settings. Throws `OAuth2Error('Could not get OAuth2Client')`. |
| `saveOAuth2Client({ configId, sessionId, client })` | Persists `{ configId, title, token }` into settings. |
| `deleteOAuth2Client({ sessionId, configId })` | Removes the saved session and the in-memory client. |
| `getSavedOAuth2Sessions()` → `object` | Raw `homey.settings.get('OAuth2Sessions')` (or `{}`). |
| `getFirstSavedOAuth2Client()` → `OAuth2Client` | First saved session's client. Throws `OAuth2Error('No OAuth2 Client Found')` when there are none. **Use this from `app.js` Flow-card handlers that are not device-bound.** |
| `tryCleanSession({ sessionId, configId })` | Fire-and-forget: deletes the session if `onShouldDeleteSession` resolves `true`. |
| `async onShouldDeleteSession({ sessionId, configId })` → `boolean` | Overloadable. Default: `true` when no devices reference the session. |
| `async getOAuth2Devices({ sessionId, configId })` → `Device[]` | All devices whose store has this `OAuth2SessionId` + `OAuth2ConfigId`. |

`setOAuth2Config()` argument table (all optional; every value is validated and throws an `OAuth2Error` when the type is wrong):

| Arg | Type | Default | Validation error thrown |
| --- | --- | --- | --- |
| `configId` | `string` | `'default'` | `Invalid Config ID` / `Duplicate Config ID` |
| `client` | `OAuth2Client` subclass | `this.constructor.OAUTH2_CLIENT` | `Invalid Client, must extend OAuth2Client` |
| `clientId` | `string` | `client.CLIENT_ID` | `Invalid Client ID` |
| `clientSecret` | `string` | `client.CLIENT_SECRET` | `Invalid Client Secret` |
| `apiUrl` | `string` | `client.API_URL` | `Invalid API URL` |
| `token` | `OAuth2Token` subclass | `client.TOKEN` | `Invalid Token, must extend OAuth2Token` |
| `tokenUrl` | `string` | `client.TOKEN_URL` | `Invalid Token URL` |
| `authorizationUrl` | `string \| null \| undefined` | `client.AUTHORIZATION_URL` | `Invalid Authorization URL` |
| `redirectUrl` | `string` | `client.REDIRECT_URL` | `Invalid Redirect URL` |
| `scopes` | `string[]` | `client.SCOPES` | `Invalid Scopes Array` |
| `allowMultiSession` | `boolean` | `this.constructor.OAUTH2_MULTI_SESSION` | `Invalid Allow Multi Session` |

**Persistence:** sessions are stored in app settings under the key **`OAuth2Sessions`**, shaped `{ [sessionId]: { configId, title, token } }` where `token` is `OAuth2Token#toJSON()` or `null`. Do not reuse that settings key for anything else.

### 6.2 `OAuth2Client` (extends `EventEmitter`)

> This class handles all api and token requests, and should be extended by the app.

Statics:

| Static | Type | Default |
| --- | --- | --- |
| `CLIENT_ID` | `string` | `Homey.env.CLIENT_ID` |
| `CLIENT_SECRET` | `string` | `Homey.env.CLIENT_SECRET` |
| `API_URL` | `string` | `null` — **required** |
| `TOKEN_URL` | `string` | `null` — **required** |
| `AUTHORIZATION_URL` | `string` | `null` — **required** for the `login_oauth2` flow |
| `SCOPES` | `string[]` | `[]` |
| `TOKEN` | `OAuth2Token` subclass | `OAuth2Token` |
| `REDIRECT_URL` | `string` | `'https://callback.athom.com/oauth2/callback'` |

Request helpers — all take `{ path, query, headers }` (+ `{ json, body }` for write methods) and return `Promise<*>`:

| Method | HTTP |
| --- | --- |
| `get({ path, query, headers })` | `GET` |
| `delete({ path, query, headers })` | `delete` |
| `post({ path, query, json, body, headers })` | `POST` |
| `patch({ path, query, json, body, headers })` | `PATCH` |
| `put({ path, query, json, body, headers })` | `PUT` |

- `path` starting with `http://` or `https://` is used absolutely; otherwise it is appended to `API_URL`.
- Passing both `body` and `json` throws `OAuth2Error('Both body and json provided')`.
- `json` sets `Content-Type: application/json` (unless you already set one) and `JSON.stringify`s the value.

Token / session methods:

| Method | Description |
| --- | --- |
| `async getTokenByCode({ code })` | Calls `onGetTokenByCode`, validates the result is an `OAuth2Token`, stores it. Throws `Invalid Token returned in onGetTokenByCode` otherwise. |
| `async getTokenByCredentials({ username, password })` | Same for the password grant. Note the error string differs: `Invalid Token returned in getTokenByCredentials`. |
| `getToken()` / `setToken({ token })` | In-memory token accessors. |
| `getTitle()` / `setTitle({ title })` | Human-readable session title. |
| `getAuthorizationUrl({ scopes, state })` | Builds the authorize URL via `onHandleAuthorizationURL`. `scopes` defaults to the configured scopes, `state` to `OAuth2Util.getRandomId()`. |
| `async refreshToken(...args)` | De-duplicates concurrent refreshes: the in-flight promise is reused, and `_executeRequest` awaits it before issuing new requests. |
| `init()` | Called by `OAuth2App#createOAuth2Client`; calls `onInit()`. |
| `save()` | Emits `save` → the app persists the session. |
| `destroy()` | Calls `onUninit()` then emits `destroy` → the app deletes the session. |
| `log(...)` / `error(...)` / `debug(...)` | Emit `log` / `error` / `debug` events which the app forwards to its logger. |

Overloadable `on*` methods (the extension surface):

| Method | Default behaviour |
| --- | --- |
| `async onInit()` | no-op |
| `async onUninit()` | no-op |
| `async onBuildRequest({ method, path, json, body, query, headers })` | Builds `{ url, opts }`; calls `onRequestHeaders` and `onRequestQuery`. |
| `async onRequestQuery({ query })` | Returns `query` unchanged. Override to inject e.g. an `api_key`. |
| `async onRequestHeaders({ headers })` | Adds `Authorization: Bearer <access_token>`. Throws `OAuth2Error('Missing Token')` when there is no token. |
| `async onGetTokenByCode({ code })` | RFC 6749 §4.1.3: `POST TOKEN_URL` with `grant_type=authorization_code`, `client_id`, `client_secret`, `code`, `redirect_uri`. |
| `async onHandleGetTokenByCodeResponse({ response })` | Generic JSON → `new TOKEN({ ...oldToken, ...json })`. |
| `async onHandleGetTokenByCodeError({ response })` | Generic error extraction (see below). |
| `async onGetTokenByCredentials({ username, password })` | RFC 6749 §4.3.2: `grant_type=password` with `username`, `password`, `scope`, plus `client_id`/`client_secret` when set. |
| `async onHandleGetTokenByCredentialsResponse({ response })` | Generic JSON → token. |
| `async onHandleGetTokenByCredentialsError({ response })` | Generic error extraction. |
| `async onRefreshToken()` | RFC 6749 §6: requires `token.isRefreshable()` (else `OAuth2Error('Token cannot be refreshed')`); `POST TOKEN_URL` with `grant_type=refresh_token`, `client_id`, `client_secret`, `refresh_token`; on success calls `onHandleRefreshTokenResponse` then `save()`. |
| `async onHandleRefreshTokenResponse({ response })` | Generic JSON → token (merges with the previous token so a missing `refresh_token` in the refresh response is preserved). |
| `async onHandleRefreshTokenError({ response })` | Generic error extraction. |
| `async onRequestError({ req, url, opts, err })` | Called only when `fetch()` itself throws (network error). Default emits a `debug` line and rethrows `err`. The default implementation only destructures `err`, but all four keys are passed. |
| `async onRequestResponse({ req, url, opts, response, didRefreshToken })` | Orchestrates: `onShouldRefreshToken` → refresh + replay once (second failure throws `OAuth2Error('Token refresh failed')`) → `onIsRateLimited` → `onHandleResponse` → `onHandleResult`. |
| `async onShouldRefreshToken({ status })` | `return status === 401;` — **this is the library's own default; you do not need to write it.** Note it is invoked as `onShouldRefreshToken(response)` with the whole `fetch` response, so an override may also read `response.headers`. |
| `async onIsRateLimited({ status, headers })` | `return status === 429;` — a `true` result throws `OAuth2Error('Rate Limited')` (there is **no** automatic retry). |
| `async onHandleResponse({ response, status, statusText, headers, ok })` | `204` → `undefined`; `application/json` → `.json()`; `image/*` → `.buffer()`; otherwise `.text()`. On non-OK, calls `onHandleNotOK` and throws its return value (must be an `Error`, else `OAuth2Error('Invalid onHandleNotOK return value, expected: instanceof Error')`). |
| `async onHandleNotOK({ body, status, statusText, headers })` | Returns an `Error` whose message is `<status> <statusText>` (`statusText` falls back to `Unknown Error`), with `.status` / `.statusText` attached. **Override this to surface the provider's error message.** Must *return* (or throw) an `Error`. |
| `async onHandleResult({ result, status, statusText, headers })` | Returns `result` unchanged. |
| `onHandleAuthorizationURL({ scopes, state })` | Appends `state`, `client_id`, `response_type=code`, `scope`, `redirect_uri` to `AUTHORIZATION_URL` (using `&` if it already contains `?`). |
| `onHandleAuthorizationURLScopes({ scopes })` | `scopes.join(' ')` (RFC 6749 App. A.4). Override for APIs that use `,`. |
| `async onGetOAuth2SessionInformation()` | `{ id: OAuth2Util.getRandomId(), title: null }`. **Override to return a stable per-account id** (e.g. the account's user id) so re-pairing the same account reuses one session. |

Generic token-error extraction order (used by all three `onHandle*Error` defaults) on a JSON body: `error_description` → `error` → `message` → `errors[]` (joined) → otherwise `Error('Invalid Response (<status> <statusText>)')`. `OAuth2Error` is constructed with the message and the HTTP status. The JSON path is only taken when the response's `Content-Type` starts with `application/json`; anything else falls straight through to `Invalid Response (…)`.

**Gotcha:** the generic *success* parser (behind `onHandleGetTokenByCodeResponse` / `…CredentialsResponse` / `onHandleRefreshTokenResponse`) is equally strict — if the token endpoint answers with anything but `application/json` (some providers return `text/plain` or `application/x-www-form-urlencoded`), it throws `Error('Could not parse Token Response')`. Override the matching `onHandle*Response` method and build the `OAuth2Token` yourself in that case.

Events emitted by an `OAuth2Client`: `log`, `error`, `debug`, `save`, `destroy`.

**Gotcha:** `OAuth2Device` also listens for an **`expired`** event on the client, but the base `OAuth2Client` never emits it. If you want `onOAuth2Expired()` to fire (which marks the device unavailable with "The session has expired. Please re-authorize."), you must `this.emit('expired')` yourself from your client subclass — e.g. when a refresh fails with `invalid_grant`.

### 6.3 `OAuth2Token`

```javascript
new OAuth2Token({ access_token, refresh_token, token_type, expires_in })
```

| Member | Description |
| --- | --- |
| `access_token`, `refresh_token`, `token_type`, `expires_in` | Each defaults to `null` when falsy. |
| `isRefreshable()` → `boolean` | `!!this.refresh_token`. Gate used by `onRefreshToken`. |
| `toJSON()` | `{ access_token, refresh_token, token_type, expires_in }` — **this is exactly what gets persisted**. |

**Gotcha:** extra fields the provider returns (e.g. `id_token`, `scope`, `expires_at`) are **dropped** by the base `toJSON()`. Subclass `OAuth2Token`, add the fields in the constructor and extend `toJSON()`, then point `static TOKEN` at your subclass.

```javascript
'use strict';

const { OAuth2Token } = require('homey-oauth2app');

module.exports = class MyBrandOAuth2Token extends OAuth2Token {

  constructor(props) {
    super(props);
    this.user_id = props.user_id ?? null;
  }

  toJSON() {
    return { ...super.toJSON(), user_id: this.user_id };
  }

};
```

### 6.4 `OAuth2Driver` (extends `Homey.Driver`)

| Static | Default | Description |
| --- | --- | --- |
| `OAUTH2_CONFIG_ID` | `'default'` | Which `setOAuth2Config` entry this driver uses. |
| `OAUTH2_NEW_SESSION_TITLE` | `'New User'` | Label of the "add another account" row in `list_sessions`. |
| `OAUTH2_NEW_SESSION_ICON` | `null` | Icon for that row. |

| Method | Description |
| --- | --- |
| `async onOAuth2Init()` | Extend me — replaces `onInit`. Register Flow cards here. |
| `async onOAuth2Uninit()` | Extend me — replaces `onUninit`. |
| `async onPairListDevices({ oAuth2Client })` | Extend me. Return the device list; the library merges `OAuth2SessionId` + `OAuth2ConfigId` into each device's `store`. |
| `getOAuth2ConfigId()` / `setOAuth2ConfigId(id)` | Runtime config switching (e.g. per-region API). `setOAuth2ConfigId` throws `OAuth2Error('Invalid Config ID')` for non-strings. |

`onPair` / `onRepair` are **implemented by the library** — do not override them. The handlers it registers on the pair session:

| Handler | Purpose |
| --- | --- |
| `showView` | On `login_oauth2` starts the OAuth2 callback flow; on `login_credentials` skips ahead when a session already exists. |
| `login` | `{ username, password }` → `client.getTokenByCredentials(...)`. |
| `list_sessions` | Returns one row per saved session (`name` = the session's `title`, falling back to `Saved User 1`, `Saved User 2`, … ; `data.id` = the `sessionId`) plus a final `$new` row named `OAUTH2_NEW_SESSION_TITLE` with icon `OAUTH2_NEW_SESSION_ICON`. Throws when `allowMultiSession` is `false`. |
| `list_sessions_selection` | Selects an existing session id or `$new`. |
| `list_devices` | Delegates to `onListSessions` while the current view is `list_sessions`, otherwise to your `onPairListDevices`. |
| `add_device` | Calls `client.save()` — **the session is only persisted once at least one device is added.** |
| `disconnect` | Logs "Pair Session Disconnected". |

`onRepair(socket, device)` reads `OAuth2SessionId` / `OAuth2ConfigId` from the device store (falling back to a random id / the driver config id), reuses or creates the client, and on success does: `device.onOAuth2Uninit()` → write both store values → `client.save()` → `device.oAuth2Client = client` → `device.onOAuth2Init()` → `socket.emit('authorized')`.

**Multi-session manifest.** To let the user pick between saved accounts, add a pair view whose **id is `list_sessions`** using the `list_devices` template as the first step. The two settings must agree:

- `list_sessions` view present **and** `OAUTH2_MULTI_SESSION = true` → the account picker works.
- `list_sessions` view present **but** multi-session left at `false` → the `list_sessions` handler throws *"Multi-Session is disabled.\nPlease remove the list_devices from your App's manifest or allow Multi-Session support."* (The library tracks the active view in `currentViewId`, which starts at `'list_sessions'`, so this also fires if anything requests `list_devices` before the first `showView`.)
- No `list_sessions` view → the first `showView` moves `currentViewId` off `list_sessions`, so `list_devices` goes straight to your `onPairListDevices` and nothing throws.

Independently of the manifest: whenever `allowMultiSession` is `false` **and** at least one session is already saved, `onPair` selects that first saved session up front, so the `login_oauth2` view immediately emits `authorized` instead of opening a login popup. That is the single-account "already logged in, just add more devices" path — not a bug.

```json
{
  "pair": [
    {
      "id": "list_sessions",
      "template": "list_devices",
      "navigation": { "next": "login_oauth2" },
      "options": { "singular": true }
    },
    { "id": "login_oauth2", "template": "login_oauth2" },
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "add_devices" } },
    { "id": "add_devices", "template": "add_devices" }
  ],
  "repair": [
    { "id": "login_oauth2", "template": "login_oauth2" }
  ]
}
```

### 6.5 `OAuth2Device` (extends `Homey.Device`)

`onInit`, `onUninit`, `onAdded` and `onDeleted` are implemented by the library — override the `onOAuth2*` variants instead. After init, `this.oAuth2Client` is the session's client.

| Method | When |
| --- | --- |
| `async onOAuth2Init()` | Extend me. Runs after `this.oAuth2Client` is available. |
| `async onOAuth2Uninit()` | Extend me. From `onUninit` and before a repair rebinds the client. |
| `async onOAuth2Added()` | Extend me. From `onAdded`. |
| `async onOAuth2Deleted()` | Extend me. From `onDeleted`, after `tryCleanSession`. |
| `async onOAuth2Saved()` | Extend me. Fires on the client's `save` event (i.e. after a token refresh). |
| `async onOAuth2Destroyed()` | Default: `setUnavailable('The session has been revoked. Please re-authorize.')`. |
| `async onOAuth2Expired()` | Default: `setUnavailable('The session has expired. Please re-authorize.')`. |
| `async onOAuth2Migrate()` | **Optional**, only define it when migrating a legacy app. It runs at the top of `onInit` and **only when the store is missing `OAuth2SessionId` or `OAuth2ConfigId`**, so already-migrated devices skip it. Must return `{ sessionId, configId, token, title? }`; a falsy return (or a throw) makes the device unavailable with "Migration failed. Please re-authorize.". |
| `async onOAuth2MigrateSuccess()` | **Optional**, called after a successful migration (clean up legacy store keys here). |

Required store keys: `OAuth2SessionId` and `OAuth2ConfigId`. Missing either throws `OAuth2Error('Missing OAuth2SessionId' / 'Missing OAuth2ConfigId')` at init — which is exactly what happens if you hand-craft devices without going through `OAuth2Driver#onPairListDevices`.

### 6.6 `OAuth2Error` and `OAuth2Util`

- `OAuth2Error extends Error`; `toString()` returns `` `[OAuth2Error] ${super.toString()}` ``.
- `OAuth2Util.getRandomId()` → a v4-style UUID string. `OAuth2Util.wait(delay = 1000)` → `Promise<void>`.

### 6.7 Complete worked example

`/app.js`:

```javascript
'use strict';

const { OAuth2App } = require('homey-oauth2app');
const MyBrandOAuth2Client = require('./lib/MyBrandOAuth2Client');

module.exports = class MyBrandApp extends OAuth2App {

  static OAUTH2_CLIENT = MyBrandOAuth2Client; // Default: OAuth2Client
  static OAUTH2_DEBUG = true;                 // Default: false
  static OAUTH2_MULTI_SESSION = false;        // Default: false
  static OAUTH2_DRIVERS = ['my_driver'];      // Default: all drivers

  async onOAuth2Init() {
    // Do App logic here — e.g. a Flow action that is not device-bound:
    this.homey.flow.getActionCard('sync_now')
      .registerRunListener(async () => {
        const client = this.getFirstSavedOAuth2Client();
        await client.getThings({ color: 'red' });
      });
  }

};
```

`/lib/MyBrandOAuth2Client.js`:

```javascript
'use strict';

const { OAuth2Client, OAuth2Error } = require('homey-oauth2app');
const MyBrandOAuth2Token = require('./MyBrandOAuth2Token');

module.exports = class MyBrandOAuth2Client extends OAuth2Client {

  // Required:
  static API_URL = 'https://api.mybrand.com/v1';
  static TOKEN_URL = 'https://api.mybrand.com/oauth2/token';
  static AUTHORIZATION_URL = 'https://auth.mybrand.com';
  static SCOPES = ['my_scope'];

  // Optional:
  static TOKEN = MyBrandOAuth2Token; // Default: OAuth2Token
  static REDIRECT_URL = 'https://callback.athom.com/oauth2/callback'; // Default: the same

  // Overload what needs to be overloaded here

  async onHandleNotOK({ body }) {
    throw new OAuth2Error(body.error);
  }

  // Give the session a stable id + title so re-pairing reuses one session.
  async onGetOAuth2SessionInformation() {
    const me = await this.get({ path: '/me' });
    return { id: me.id, title: me.email };
  }

  async getThings({ color }) {
    return this.get({
      path: '/things',
      query: { color },
    });
  }

  async updateThing({ id, thing }) {
    return this.put({
      path: `/thing/${id}`,
      json: { thing },
    });
  }

};
```

`/drivers/<driver_id>/driver.compose.json`:

```json
{
  "id": "my_driver",
  "pair": [
    {
      "id": "login_oauth2",
      "template": "login_oauth2"
    },
    {
      "id": "list_devices",
      "template": "list_devices",
      "navigation": {
        "next": "add_devices"
      }
    },
    {
      "id": "add_devices",
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

`/drivers/<driver_id>/driver.js`:

```javascript
'use strict';

const { OAuth2Driver } = require('homey-oauth2app');

module.exports = class MyBrandDriver extends OAuth2Driver {

  async onOAuth2Init() {
    // Register Flow Cards etc.
  }

  async onPairListDevices({ oAuth2Client }) {
    const things = await oAuth2Client.getThings({ color: 'red' });
    return things.map(thing => {
      return {
        name: thing.name,
        data: {
          id: thing.id,
        },
      };
    });
  }

};
```

`/drivers/<driver_id>/device.js`:

```javascript
'use strict';

const { OAuth2Device } = require('homey-oauth2app');

module.exports = class MyBrandDevice extends OAuth2Device {

  async onOAuth2Init() {
    await this.oAuth2Client.getThingState()
      .then(async state => {
        await this.setCapabilityValue('onoff', !!state.on);
      });

    this._poll = this.homey.setInterval(() => {
      this.sync().catch(this.error);
    }, 5 * 60 * 1000);
  }

  async sync() {
    const state = await this.oAuth2Client.getThingState();
    await this.setCapabilityValue('onoff', !!state.on);
  }

  async onOAuth2Deleted() {
    // Clean up here
    if (this._poll) this.homey.clearInterval(this._poll);
  }

};
```

`/env.json` (gitignored):

```json
{
  "CLIENT_ID": "12345abcde",
  "CLIENT_SECRET": "182hr2389r824ilikepie1302r0832"
}
```

### 6.8 Method names that do **not** exist

Do not write these — they are not part of `homey-oauth2app@3.7.2` and will silently never be called:

| Wrong | Correct |
| --- | --- |
| `onHandleGetTokenByCode` | `onGetTokenByCode` (request) / `onHandleGetTokenByCodeResponse` (parse) / `onHandleGetTokenByCodeError` (error) |
| `onRequestQueue` | Request queueing is automatic: `refreshToken()` stores the in-flight promise and `_executeRequest` awaits it — there is no hook. |
| `onHandleRefreshToken` | `onRefreshToken` / `onHandleRefreshTokenResponse` / `onHandleRefreshTokenError` |
| `getSavedOAuth2Client` | `getOAuth2Client({ sessionId, configId })` or `getFirstSavedOAuth2Client()` |

---

## 7. Webhooks

> A webhook is an API concept that allows manufacturer's Web APIs to send realtime updates using regular HTTP requests. Because Homey connects to the internet through a router, your app is not publicly accessible from the internet. We provide a webhook-forwarding service to route all incoming webhooks to the right Homey.

Example inbound request as it arrives at Athom's forwarder:

```http
POST /webhook/56db7fb12dcf75604ea7977d HTTP/1.1
Host: webhooks.athom.com
Content-Type: application/json; charset=utf-8

{
  "device_id": "aaabbbccc",
  "turned_on": true
}
```

### Step 1 — Create the webhook in Developer Tools

Go to <https://tools.developer.homey.app/webhooks> and select `New Webhook`. Copy the ID & Secret to your app's `/env.json` file as `WEBHOOK_ID` and `WEBHOOK_SECRET`.

```json
{
  "WEBHOOK_ID": "56db7fb12dcf75604ea7977d",
  "WEBHOOK_SECRET": "2uhf83h83h4gg34..."
}
```

The resulting public URL is:

```
https://webhooks.athom.com/webhook/<WEBHOOK_ID>
```

`/env.json` values are available anywhere in your app as `Homey.env.<KEY>` (module scope, `const Homey = require('homey')`) or `this.homey.env.<KEY>` (inside App/Driver/Device). Keys must be uppercase and their values must be strings. `/env.json` must be listed in `/.gitignore`.

### Step 2 — Register the listener in your app

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {

  async onInit() {
    const id = Homey.env.WEBHOOK_ID; // "56db7fb12dcf75604ea7977d"
    const secret = Homey.env.WEBHOOK_SECRET; // "2uhf83h83h4gg34..."
    const data = {
      // Provide unique properties for this Homey here
      deviceId: 'aaabbbccc',
    };

    this.webhook = await this.homey.cloud.createWebhook(id, secret, data);

    this.webhook.on('message', args => {
      this.log('Got a webhook message!');
      this.log('headers:', args.headers);
      this.log('query:', args.query);
      this.log('body:', args.body);
    });
  }

  async onUninit() {
    if (this.webhook) {
      await this.webhook.unregister().catch(this.error);
    }
  }

}

module.exports = App;
```

### Step 3 — Choose a routing option

How does the webhook service know that only *this* Homey may receive the webhook? Three options, depending on how you register webhooks with the manufacturer's Web API.

| Option | When | `data` needed? | Mechanism |
| --- | --- | --- | --- |
| 1 — Query parameter | The API lets you register a webhook URL dynamically | No | Append `?homey=<homeyId>` to the URL you hand the provider |
| 2 — Key path | The URL must be fixed up front (developer portal) | Yes (`$key` / `$keys`) | The forwarder matches a value inside the request against your `data` |
| 3 — Cloud Function | Legacy, read-only | Yes | A stored JS expression evaluated per Homey |

#### Option 1 — Dynamic webhooks using Query Parameters

```javascript
'use strict';

const Homey = require('homey');
const fetch = require('node-fetch');

class App extends Homey.App {

  async onInit() {
    const homeyId = await this.homey.cloud.getHomeyId();
    const webhookUrl = `https://webhooks.athom.com/webhook/${Homey.env.WEBHOOK_ID}?homey=${homeyId}`;

    await fetch('https://myapi.com/webhook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: webhookUrl }),
    });
  }

}

module.exports = App;
```

Homey's webhook forwarding service understands that webhooks with a `homey` query parameter should be forwarded to that Homey. When using query parameters, the `data` property is not required when registering your webhook using the `this.homey.cloud.createWebhook()` function.

#### Option 2 — Webhooks using Key Path properties

If the manufacturer's Web API requires you to specify the webhook URL beforehand, for example in their developer portal, then you can use the *key path* option when creating your webhook.

The *key path* describes which property from the webhook request contains the value that uniquely identifies a Homey. For example: `headers['X-Device-Id']`, note that these properties are **case-sensitive**. You can use `body`, `headers` and `query` in your Webhook *key path* filter.

> A *key path* is an ECMAScript expression consisting only of identifiers (`myVal`), member accesses (`foo.bar`) and key lookup with literal values (`arr[0]`, `obj['str-value'].bar.baz`).

Matching rules:

| Rule | Detail |
| --- | --- |
| Where the key path is configured | In Developer Tools, on the webhook definition — **not** in your app code. |
| What it matches against | The `data` object passed to `this.homey.cloud.createWebhook(id, secret, data)`. |
| Single value | `{ $key: "aaabbbccc" }` matches the value `aaabbbccc`. |
| Multiple values | `{ $keys: ["aaa", "bbb"] }` — the value at the key path must equal `aaa` **or** `bbb`. |
| Fan-out | The key path is checked for **each** Homey registered to this webhook. All Homeys with matching data receive the webhook in the `webhook.on('message', …)` listener. |

Example 1 — Headers (`headers['X-Device-Id']`):

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {

  async onInit() {
    const id = Homey.env.WEBHOOK_ID; // "56db7fb12dcf75604ea7977d"
    const secret = Homey.env.WEBHOOK_SECRET; // "2uhf83h83h4gg34..."
    const data = {
      // Provide unique properties for this Homey here
      $keys: ['aaa', 'bbb'],
    };

    const myWebhook = await this.homey.cloud.createWebhook(id, secret, data);

    myWebhook.on('message', args => {
      this.log('Got a webhook message!');
      this.log('headers:', args.headers);
      this.log('query:', args.query);
      this.log('body:', args.body);
    });
  }

}

module.exports = App;
```

```http
POST /webhook/56db7fb12dcf75604ea7977d HTTP/1.1
X-Device-Id: aaa
Host: webhooks.athom.com
Content-Type: application/json; charset=utf-8

{
  "turned_on": true
}
```

Homey's webhook service will match your webhook based on `headers['X-Device-Id']` with value `aaa` (or `bbb`) and forward this to that Homey. If the webhook service received value `ccc` it will **not** be forwarded.

Example 2 — Body. Using the same `data` object, you can also define your *key path* in the body of the webhook HTTP request:

```http
POST /webhook/56db7fb12dcf75604ea7977d HTTP/1.1
X-Device-Id: aaa
Host: webhooks.athom.com
Content-Type: application/json; charset=utf-8

{
  "X-Device-Id": "bbb",
  "turned_on": true
}
```

#### Option 3 — Static webhook URLs using the Cloud Function (legacy)

> Cloud Functions are now considered legacy and have been made "read-only", consider changing to Query Parameter or Key Path based webhooks.

If you had previously defined a custom *cloud function* on <https://tools.developer.homey.app/webhooks>, it is possible to view this function in the developer portal. Your function has to match an incoming webhook against the `data` object provided in `this.homey.cloud.createWebhook(id, secret, data)` — for example an object with `{ deviceId: "aaabbbccc" }`. If the webhook sends the Device's ID in the body as `device_id`, the cloud function becomes:

```javascript
return homey_data.deviceId === webhook_data.device_id;
```

This function will execute for each Homey that is registered to this webhook. All Homeys that returned `true` will receive the webhook in the `webhook.on('message', …)` listener.

### Unregistering

```javascript
await webhook.unregister();                        // instance shortcut
await this.homey.cloud.unregisterWebhook(webhook); // manager equivalent
```

### Webhook gotchas

| Gotcha | Detail |
| --- | --- |
| One registration per Homey per webhook id | Calling `createWebhook()` again with different `data` replaces the routing data for that Homey. Register **once** (in `App#onInit`), keep the handle on `this`, and re-register when the identifying data changes. |
| Register in the App, dispatch to Devices | A single webhook id serves the whole app. Keep the `CloudWebhook` on the App instance and route each `message` to the right device (e.g. by looking up `this.homey.drivers.getDriver(id).getDevices()`), instead of creating one webhook per device. |
| `data` is the *matching* payload, not app state | It is uploaded to Athom's forwarder. Put only identifiers there (account id, device id, `$key`/`$keys`) — never tokens or secrets. |
| Key paths are case-sensitive | `headers['X-Device-Id']` ≠ `headers['x-device-id']`. Check what the forwarder actually stores before assuming header casing is normalised. |
| No documented rate or size limits | The official docs specify no maximum request rate or body size for the forwarding service. Do not rely on high-frequency webhooks as a data pipe; treat delivery as best-effort and reconcile with a periodic poll (`this.homey.setInterval`). |
| `.catch(this.error)` inside the handler | The `message` handler is a plain (non-awaited) listener. An unhandled rejection inside it crashes the app on Homey Cloud. |
| Webhooks work on Homey Cloud | The App Web API (`/api.js`) is not supported on Homey Cloud, but webhooks are — this is the supported way to receive inbound HTTP on Bridge. |

---

## 8. `getHomeyId()` and `getLocalAddress()`

```javascript
const homeyId = await this.homey.cloud.getHomeyId();      // Homey's Cloud ID
const localAddress = await this.homey.cloud.getLocalAddress(); // "192.168.1.x:80"
```

| Method | Purpose | Homey Pro | Homey Cloud |
| --- | --- | --- | --- |
| `getHomeyId()` | Cloud ID — the value to pass as the `homey` query parameter, and a stable per-Homey identifier for provider-side webhook registration | ✅ | ✅ |
| `getLocalAddress()` | Homey's local address & port | ✅ | ❌ not supported (Homey Bridge has no local Wi-Fi stack) |

---

## 9. Manifest & platform notes for cloud drivers

- Drivers that use OAuth or Webhooks declare `"connectivity": ["cloud"]` — *"This means that your Driver uses OAuth or Webhooks to connect to a cloud service."*
- Homey can talk to the internet without any extra permission; no `homey:wireless:*` permission is needed for OAuth2 or webhooks.
- On Homey Cloud the app runs in a shared Node.js process (multi-tenancy): **no global mutable variables** — keep every client/token/webhook handle on `this`.
- On Homey Cloud `/` is the Linux root, not your app directory: always require relatively (`require('./lib/MyBrandOAuth2Client')`, `path.join(__dirname, …)`).
- Custom app-settings views are not supported on Homey Cloud — ask for anything the app needs during pairing, and use the *repair* views to update it.

---

## 10. Checklist

- [ ] OAuth client registered at the provider with redirect URI exactly `https://callback.athom.com/oauth2/callback`.
- [ ] `CLIENT_ID` / `CLIENT_SECRET` in `/env.json`; `/env.json` in `/.gitignore`.
- [ ] `authorizeUrl` contains `redirect_uri`, `response_type=code`, `client_id`, `scope` (and `access_type=offline` + `prompt=consent` where the provider needs it for a refresh token).
- [ ] Read scopes requested explicitly — write scopes do not imply read.
- [ ] `login_oauth2` step present in `pair` **and** `repair`.
- [ ] `code` handler checks `code instanceof Error`.
- [ ] `session.emit('authorized')` awaited **before** any `session.done()`.
- [ ] Retry latch reset in the `catch` branch.
- [ ] Refresh on 401, retry once, then `setUnavailable()` to steer the user to repair.
- [ ] Webhook ID + Secret created at <https://tools.developer.homey.app/webhooks> and stored in `/env.json`.
- [ ] Exactly one `createWebhook()` per app, handle kept on `this`, `unregister()` in `onUninit()`.
- [ ] Routing chosen: `?homey=<homeyId>` query param (dynamic) **or** `$key`/`$keys` key path (static URL).
- [ ] `"connectivity": ["cloud"]` on every cloud driver.

---

## Sources

- <https://apps.developer.homey.app/cloud/oauth2>
- <https://apps.developer.homey.app/cloud/webhooks>
- <https://apps.developer.homey.app/the-basics/devices/pairing/system-views/oauth2-login>
- <https://apps.developer.homey.app/the-basics/app> (Environment / `env.json`)
- <https://apps.developer.homey.app/guides/homey-cloud> (SDK differences between Homey Pro & Homey Cloud)
- <https://apps-sdk-v3.developer.homey.app/ManagerCloud.html>
- <https://apps-sdk-v3.developer.homey.app/CloudOAuth2Callback.html>
- <https://apps-sdk-v3.developer.homey.app/CloudWebhook.html>
- <https://apps-sdk-v3.developer.homey.app/PairSession.html>
- <https://athombv.github.io/node-homey-oauth2app> (`homey-oauth2app`, npm v3.7.2)
- <https://tools.developer.homey.app/webhooks>
- Example apps: <https://github.com/athombv/nl.thermosmart-example>, <https://github.com/athombv/nl.eneco.toon-example>, <https://github.com/athombv/io.nuki-example>
