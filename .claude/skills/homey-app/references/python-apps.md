# Writing Homey Apps in Python

Homey Apps SDK v3 has a first-class Python runtime alongside Node.js. The manifest, Homey Compose,
capabilities, Flow cards, pairing views and App Store rules are identical — only the app code
changes. This file is the complete Python-specific reference: manifest keys, project layout, the
`homey_export` convention, the JS→Python naming map, every class and manager available in Python,
typing, dependency management and a full minimal app skeleton.

Cross-references: `references/app-and-manifest.md` (manifest, Compose, i18n, permissions),
`references/drivers-and-devices.md`, `references/capabilities.md`, `references/flow-cards.md`,
`references/widgets.md`, `references/cli-and-tooling.md`, `references/web-api-and-realtime.md`,
`references/wireless-lan-discovery.md`.

---

## 1. Prerequisites and hard requirements

| Requirement | Value | Why |
| --- | --- | --- |
| `"runtime"` | `"python"` | Manifest. Allowed runtimes are `nodejs` and `python`. |
| `"pythonVersion"` | `"3.14"` | Currently the only supported version. |
| `"compatibility"` | `">=13.0.0"` | The Python runtime example manifest declares this range. |
| `"sdk"` | `3` | Always. |
| Homey CLI | Node.js v24 or higher | The CLI itself is a Node package. |
| Docker | **Required** | "If you want to create apps written in Python, or that run in our Cloud environment, you will also need to have Docker running on your machine to test your apps." `homey app run` / `build` / `validate` / `publish` / `dependencies …` all shell out to Docker. |

> The Python version running on Homey platforms is the latest available full release, currently
> `3.14`. When the declared version becomes outdated a newer interpreter may be used to run the app,
> which may break it. Apps get roughly a year to move to a new full-release Python version.

### What is NOT available in Python

| Missing | Notes |
| --- | --- |
| `zigbee-clusters` (`node-zigbee-clusters`) | "It is currently not available for Python apps." Python Zigbee apps talk raw frames through `ZigbeeNode.send_frame()` / `handle_frame()`. |
| `homey-zigbeedriver`, `homey-zwavedriver`, `homey-rfdriver`, `homey-oauth2app`, `homey-log` | All official helper libraries are npm/Node.js modules. Python apps implement these patterns by hand on top of the raw SDK. |
| `ManagerAudio` (`homey.audio`) | JS-only; no `audio` attribute on the Python `Homey` instance. |
| `ManagerLedring` (`homey.ledring`), `LedringAnimation*` | JS-only. |
| `ManagerNFC` (`homey.nfc`) | JS-only. |
| `ManagerSpeechOutput` (`homey.speechOutput`), `homey.speechInput` | JS-only. |
| `--link-modules` | `homey app run --link-modules` links local **Node.js** modules only. |
| `Device.getStoreValue()` / `getStoreKeys()` | No Python equivalent method; use `get_store()` and read the mapping. |

Everything else — Wi-Fi/LAN discovery, BLE, Z-Wave, Zigbee (raw), 433/868 MHz, Infrared, cloud
OAuth2 and webhooks, images, videos/cameras, Insights, widgets, the app Web API — has a Python
equivalent.

---

## 2. App manifest

{% code title="/.homeycompose/app.json" %}

```json
{
  "id": "my.company.example",
  "version": "1.0.0",
  "compatibility": ">=13.0.0",
  "runtime": "python",
  "pythonVersion": "3.14",
  "pythonDependencies": [],
  "platforms": ["local", "cloud"],
  "sdk": 3,
  "brandColor": "#FF0000",
  "name": { "en": "My App" },
  "description": { "en": "Adds support for Example devices." },
  "category": "lights",
  "tags": { "en": ["example"] },
  "images": {
    "small": "/assets/images/small.png",
    "large": "/assets/images/large.png",
    "xlarge": "/assets/images/xlarge.png"
  },
  "permissions": ["homey:manager:api"],
  "author": {
    "email": "john@doe.com",
    "name": "John Doe"
  }
}
```

{% endcode %}

### Python-only manifest properties

| Property | Type | Description |
| --- | --- | --- |
| `runtime` | `"python"` | Selects the Python runtime. Allowed runtimes: `nodejs`, `python`. |
| `pythonVersion` | `string` | The Python version the app was developed for. Currently the only supported version is `"3.14"`. |
| `pythonDependencies` | `string[]` | Libraries added through the CLI, e.g. `["aiohttp>=3.13"]`. Stored in the manifest so compatibility with Homey platforms can be checked. |

```jsonc
{
  "id": "com.athom.example",
  // ...
  "runtime": "python",
  "pythonDependencies": [
    "aiohttp>=3.13"
  ]
}
```

> **Danger:** "Editing the dependencies in the app manifest without running
> `homey app dependencies install` results in the app being bundled with outdated libraries."
>
> **Warning:** "Installing dependencies through other means than `homey app dependencies install`
> results in those dependencies missing in the bundled app." Plain `pip install` / `uv add` into a
> local venv does **not** put anything in the bundle. Always re-test with `homey app install` or a
> remote run after changing dependencies.

Every other manifest property (`id`, `version`, `compatibility`, `platforms`, `sdk`, `brandColor`,
`name`, `description`, `category`, `tags`, `images`, `permissions`, `author`,
`platformLocalRequiredFeatures`, `contributors`, `contributing`, `bugs`, `homeyCommunityTopicId`,
`source`, `homepage`, `support`) behaves exactly as for Node.js apps — see
`references/app-and-manifest.md`.

---

## 3. Project layout

```
com.athom.example/
├─ .homeycompose/
│ ├─ app.json
│ └─ ...
├─ .python_cache/
│ └─ ...
├─ assets/
│ ├─ icon.svg
│ └─ images
│   ├─ small.png
│   ├─ large.png
│   └─ xlarge.png
├─ drivers/
│ ├─ my_driver/
│ │ ├─ assets/
│ │ │ ├─ icon.svg
│ │ │ └─ images/
│ │ │   ├─ small.png
│ │ │   ├─ large.png
│ │ │   └─ xlarge.png
│ │ ├─ device.py
│ │ └─ driver.py
│ └─ ...
├─ locales/
│ ├─ en.json
│ └─ nl.json
├─ settings/
│ └─ index.html
├─ api.py
├─ app.py
├─ app.json
├─ env.json
└─ README.txt
```

| Path | Node.js | TypeScript | Python |
| --- | --- | --- | --- |
| App class | `app.js` | `app.mts` | `app.py` |
| Driver class | `drivers/<id>/driver.js` | `driver.mts` | `drivers/<id>/driver.py` |
| Device class | `drivers/<id>/device.js` | `device.mts` | `drivers/<id>/device.py` |
| App Web API | `api.js` | `api.mts` | `api.py` |
| Widget API | `widgets/<id>/api.js` | `api.mts` | `widgets/<id>/api.py` |
| Dependency cache | `node_modules/` | `node_modules/` | `.python_cache/` |

`.python_cache/` holds the pre-compiled virtual environments produced by
`homey app dependencies …`. It is generated — treat it like `node_modules/`: do not hand-edit it,
and add it to `.gitignore`. Use `/.homeyignore` (same syntax as `.gitignore`) to keep files out of
the published bundle.

Non-Python-specific files are unchanged: `driver.compose.json`, `.homeycompose/flow/<type>/<id>.json`,
`locales/*.json`, `assets/`, `settings/index.html`, `env.json`, `README.txt`.

---

## 4. The `homey_export` convention

Every module that Homey loads must assign the class it exports to a module-level name
`homey_export`. This replaces `module.exports = …` (JS) and `export default …` (TS).

| File | Must assign | Base class |
| --- | --- | --- |
| `/app.py` | `homey_export = MyApp` | `homey.app.App` |
| `/drivers/<id>/driver.py` | `homey_export = MyDriver` | `homey.driver.Driver` |
| `/drivers/<id>/device.py` | `homey_export = MyDevice` | `homey.device.Device` |

The SDK reference states this explicitly for all three: *"App — Assigned to `homey_export` in
`app.py`; Driver — Assigned to `homey_export` in `driver.py`; Device — Assigned to `homey_export` in
`device.py`."*

`api.py` and `widgets/<id>/api.py` are the exception: they export **async functions** whose names
match the route names in the manifest, listed in `__all__` (see §11).

```python
from homey.app import App

class MyApp(App):
    """My Homey app"""

    async def on_init(self):
        self.log("MyApp has been initialized")

homey_export = MyApp
```

### Import styles

Both forms appear in the official docs and are equivalent:

```python
from homey import app            # then: class MyApp(app.App)
from homey.app import App        # then: class MyApp(App)
```

| Symbol | Module |
| --- | --- |
| `App` | `homey.app` |
| `Driver`, `ListDeviceProperties` | `homey.driver` |
| `Device`, `CapabilityListener`, `MultipleCapabilityListener`, `CapabilityValue` | `homey.device` |
| `Homey` | `homey.homey` |
| `SimpleClass` | `homey.simple_class` |
| `PairSession` | `homey.pair_session` |
| `FlowCard`, `ArgumentAutocompleteResult`, `ArgumentAutocompleteListener`, `RunListener` | `homey.flow_card` |
| `FlowCardAction` / `FlowCardCondition` / `FlowCardTrigger` / `FlowCardTriggerDevice` | `homey.flow_card_action` / `…_condition` / `…_trigger` / `…_trigger_device` |
| `FlowArgument` | `homey.flow_argument` |
| `FlowToken` | `homey.flow_token` |
| `Image`, `ImageStreamMetadata`, `StreamReturn`, `Writable` | `homey.image` |
| `InsightsLog` | `homey.insights_log` |
| `Api`, `ApiRequest` | `homey.api` |
| `ApiApp` | `homey.api_app` |
| `Widget`, `SettingAutocompleteResult`, `SettingAutocompleteListener` | `homey.widget` |
| `WidgetSetting` | `homey.widget_setting` |
| `CloudWebhook`, `WebhookMessage` | `homey.cloud_webhook` |
| `CloudOAuth2Callback` | `homey.cloud_oauth2_callback` |
| `DiscoveryStrategy` | `homey.discovery_strategy` |
| `DiscoveryResult` / `DiscoveryResultMAC` / `DiscoveryResultMDNSSD` / `DiscoveryResultSSDP` | `homey.discovery_result` / `…_mac` / `…_mdns_sd` / `…_ssdp` |
| `BleAdvertisement`, `ServiceData` | `homey.ble_advertisement` |
| `BlePeripheral` / `BleService` / `BleCharacteristic` / `BleDescriptor` | `homey.ble_peripheral` / `…_service` / `…_characteristic` / `…_descriptor` |
| `Signal` / `Signal433` / `Signal868` / `SignalInfrared` | `homey.signal` / `homey.signal_433` / `homey.signal_868` / `homey.signal_infrared` |
| `Video`, `VideoWithURL`, `VideoWebRTC` (+ `WebRTCAnswer`), `VideoRTSP`, `VideoRTMP`, `VideoHLS`, `VideoDASH`, `VideoOther` | `homey.video`, `homey.video_with_url`, `homey.video_web_rtc`, `homey.video_rtsp`, `homey.video_rtmp`, `homey.video_hls`, `homey.video_dash`, `homey.video_other` |
| `ZigbeeNode` | `homey.zigbee_node` |
| `ZWaveNode`, `ZWaveCommandClass`, `Command` | `homey.zwave_node`, `homey.zwave_command_class` |
| `Manager` and all `Manager*` classes | `homey.manager.<name>` (e.g. `homey.manager.flow.ManagerFlow`) |

### Cross-file imports

```python
# /drivers/<driver_id>/driver.py
from .device import Device                 # sibling module in the driver folder

# /drivers/<driver_id>/device.py
from ...app import App                     # app.py at the app root (two levels up)
from .driver import Driver                 # sibling

# /api.py
from .app import App

# /widgets/<widget_id>/api.py
from ...app import App
```

Modules at the app root can also be imported absolutely (the docs do this for helper modules):
`from device_api import DeviceApi`, `from rain_api import RainApi`,
`from your_external_api_client import ApiClient`.

---

## 5. Naming conventions — JS ⇄ Python

Rules:

1. Methods and properties become **`snake_case`**: `onInit` → `on_init`,
   `setCapabilityValue` → `set_capability_value`.
2. Class names stay **`PascalCase`**; Z-Wave classes are spelled `ZWaveNode` / `ZWaveCommandClass`
   (JS uses `ZwaveNode` / `ZwaveCommandClass`); Zigbee is `ZigbeeNode` (JS: `ZigBeeNode`).
3. Manifest keys stay **`camelCase`** — including inside Python dicts (`capabilitiesOptions`,
   `answerSdp`, `streamId`, `contentType`, `contentLength`).
4. Callbacks are `async def` unless the reference types them as `Callable[..., None]`.
5. JS `.on('event', handler)` becomes a typed registrar `on_<event>(handler)` returning `Self`
   (`EventEmitter.on(name, handler)` also still works — see §6).
6. JS `state` (second argument of a Flow run listener / `trigger()`) becomes Python **keyword
   arguments** (`**trigger_kwargs`).

### Lifecycle (App / Driver / Device)

| JavaScript | Python | Notes |
| --- | --- | --- |
| `onInit()` | `on_init()` | App, Driver, Device |
| `onUninit()` | `on_uninit()` | App, Driver, Device |
| `ready()` | `ready()` | Driver, Device, Homey |
| `onAdded()` | `on_added()` | Device |
| `onDeleted()` | `on_deleted()` | Device |
| `onRenamed(name)` | `on_renamed(name)` | Device |
| `onSettings({ oldSettings, newSettings, changedKeys })` | `on_settings(old_settings, new_settings, changed_keys)` | Device — **positional args in Python, not a destructured object** |
| `onDiscoveryResult(result)` | `on_discovery_result(discovery_result)` | Device |
| `onDiscoveryAvailable(result)` | `on_discovery_available(discovery_result)` | Device |
| `onDiscoveryAddressChanged(result)` | `on_discovery_address_changed(discovery_result)` | Device |
| `onDiscoveryLastSeenChanged(result)` | `on_discovery_last_seen_changed(discovery_result)` | Device |
| `onPair(session)` | `on_pair(session)` | Driver |
| `onRepair(session, device)` | `on_repair(session, device=None)` | Driver |
| — | `on_unpair(session, device=None)` | Driver — documented in the Python reference |
| `onPairListDevices()` | `on_pair_list_devices(view_data)` | Driver — Python receives the view data |
| `onMapDeviceClass(device)` | `on_map_device_class(device)` | Driver |

### Device methods

| JavaScript | Python | Async in Python? |
| --- | --- | --- |
| `getCapabilityValue(id)` | `get_capability_value(id)` | no |
| `setCapabilityValue(id, value)` | `set_capability_value(id, value)` | **yes** |
| `getState()` | `get_state()` | no |
| `hasCapability(id)` | `has_capability(id)` | no |
| `getCapabilities()` | `get_capabilities()` | no |
| `addCapability(id)` | `add_capability(id)` | **yes** |
| `removeCapability(id)` | `remove_capability(id)` | **yes** |
| `getCapabilityOptions(id)` | `get_capability_options(id)` | no |
| `setCapabilityOptions(id, options)` | `set_capability_options(id, options)` | **yes** |
| `registerCapabilityListener(id, fn)` | `register_capability_listener(capability_id, listener)` | no (listener is async) |
| `registerMultipleCapabilityListener(ids, fn, timeout)` | `register_multiple_capability_listener(capability_ids, listener, debounce_timeout=250)` | no (listener is async) |
| `triggerCapabilityListener(id, value, opts)` | `trigger_capability_listener(capability_id, value, **kwargs)` | **yes** |
| `getSetting(key)` | `get_setting(key)` | no |
| `getSettings()` | `get_settings()` | no |
| `setSettings(settings)` | `set_settings(settings)` | **yes** |
| `getData()` | `get_data()` | no |
| `getStore()` | `get_store()` | no |
| `getStoreValue(key)` | *(none)* → `get_store().get(key)` | — |
| `getStoreKeys()` | *(none)* → `get_store().keys()` | — |
| `setStoreValue(key, value)` | `set_store_value(key, value)` | **yes** |
| `unsetStoreValue(key)` | `unset_store_value(key)` | **yes** |
| `getName()` | `get_name()` | no |
| — *(no JS equivalent; JS reads `this.getData()`)* | `get_id()` | no |
| `getClass()` | `get_class()` | no |
| `setClass(cls)` | `set_class(device_class)` | **yes** |
| `getAvailable()` | `get_available()` | no |
| `setAvailable()` | `set_available()` | **yes** |
| `setUnavailable(message)` | `set_unavailable(message=None)` | **yes** |
| `setWarning(message)` | `set_warning(message=None)` | **yes** |
| `unsetWarning()` | `unset_warning()` | **yes** |
| `getEnergy()` | `get_energy()` | no |
| `setEnergy(energy)` | `set_energy(energy)` | **yes** |
| `setAlbumArtImage(image)` | `set_album_art_image(image)` | **yes** |
| `setCameraImage(id, title, image)` | `set_camera_image(id, title, image)` | **yes** |
| `setCameraVideo(id, title, video)` | `set_camera_video(id, title, video)` | **yes** |
| `setLastSeenAt()` | `set_last_seen_at()` | **yes** |

### Homey instance

| JavaScript | Python |
| --- | --- |
| `this.homey.__(key, tags)` | `self.homey.translate(key, **tags)` |
| `this.homey.i18n.__(key, tags)` | `self.homey.i18n.translate(key, **tags)` |
| `this.homey.setTimeout(fn, ms)` | `self.homey.set_timeout(callback, ms, *args, **kwargs)` |
| `this.homey.clearTimeout(id)` | `self.homey.clear_timeout(id)` |
| `this.homey.setInterval(fn, ms)` | `self.homey.set_interval(callback, ms, *args, **kwargs)` |
| `this.homey.clearInterval(id)` | `self.homey.clear_interval(id)` |
| `this.homey.platformVersion` | `self.homey.platform_version` |
| `this.homey.platformFeatures` | `self.homey.platform_features` |
| `this.homey.hasFeature(f)` | `self.homey.has_feature(f)` |
| `this.homey.env.CLIENT_ID` | `self.homey.env["CLIENT_ID"]` |
| `this.homey.on('unload', fn)` | `self.homey.on_unload(fn)` |
| `this.homey.on('cpuwarn', fn)` | `self.homey.on_cpuwarn(fn)` |
| `this.homey.on('memwarn', fn)` | `self.homey.on_memwarn(fn)` |

### Flow

| JavaScript | Python |
| --- | --- |
| `this.homey.flow.getActionCard(id)` | `self.homey.flow.get_action_card(id)` |
| `this.homey.flow.getConditionCard(id)` | `self.homey.flow.get_condition_card(id)` |
| `this.homey.flow.getTriggerCard(id)` | `self.homey.flow.get_trigger_card(id)` |
| `this.homey.flow.getDeviceTriggerCard(id)` | `self.homey.flow.get_device_trigger_card(id)` |
| `this.homey.flow.createToken(id, opts)` | `self.homey.flow.create_token(id, type, title, value=None)` |
| `this.homey.flow.getToken(id)` | `self.homey.flow.get_token(id)` |
| `this.homey.flow.unregisterToken(token)` | `self.homey.flow.unregister_token(token)` |
| `card.registerRunListener(async (args, state) => …)` | `card.register_run_listener(listener)` — `async def listener(card_arguments, **trigger_kwargs)` |
| `card.registerArgumentAutocompleteListener(name, fn)` | `card.register_argument_autocomplete_listener(name, listener)` |
| `card.getArgumentValues()` | `card.get_argument_values()` |
| `card.on('update', fn)` | `card.on_update(fn)` |
| `card.trigger(tokens, state)` | `card.trigger(tokens, **trigger_kwargs)` |
| `deviceCard.trigger(device, tokens, state)` | `device_card.trigger(device, tokens, **trigger_kwargs)` |
| `token.setValue(v)` | `token.set_value(v)` |

### Pairing

| JavaScript | Python |
| --- | --- |
| `session.setHandler(event, fn)` | `session.set_handler(event, listener)` |
| `session.showView(id)` | `session.show_view(id)` |
| `session.nextView()` | `session.next_view()` |
| `session.prevView()` | `session.prev_view()` |
| `session.emit(event, data)` | `session.emit(event, data=None)` |
| `session.done()` | `session.done()` |

---

## 6. Async and event model

Everything in the Python SDK that touches Homey is `async`. Listener callbacks come in two shapes:

**Async listeners** (capability listeners, Flow run listeners, autocomplete listeners, pair handlers,
video URL/offer listeners) — declared `async def` and awaited by the SDK.

**Sync event callbacks** (`on_log`, `on_error`, `on_debug`, `on_update`, `on_unload`, `on_cpuwarn`,
`on_memwarn`, `on_message`, `on_url`, `on_code`, `on_realtime`, `on_install`, `on_uninstall`,
`on_payload`, `on_online`, `on_report`, `on_nif`, `on_unknown_report`, `on_disconnect`,
`on_timezone_change`, `on_address_changed`, `on_last_seen_changed`) — typed
`Callable[..., None]`. To do async work inside them, schedule a task:

```python
import asyncio

def on_state_changed(is_on: bool) -> None:
    asyncio.create_task(
        self.set_capability_value("onoff", is_on)
    ).add_done_callback(
        lambda result: self.error(result.exception()) if result.exception() else None
    )

DeviceApi.on("state-changed", on_state_changed)
```

This is the Python equivalent of the JS `….catch(this.error)` idiom — an unhandled exception in a
fire-and-forget task is silently swallowed otherwise.

Every class that descends from `SimpleClass` — `App`, `Driver`, `Device`, `Homey`, every `Manager*`,
`FlowCard`, `FlowArgument`, `Widget`, `WidgetSetting`, `Signal`, `DiscoveryResult`,
`DiscoveryStrategy`, `CloudWebhook`, `CloudOAuth2Callback`, the `Ble*` classes, `ZigbeeNode`,
`ZWaveNode`, `ZWaveCommandClass` — as well as `Api` and `ApiApp`, descends from
`homey.util.event_emitter.EventEmitter`, so the generic `instance.on("<event>", handler)` form is
also valid and is used in the docs for events without a typed registrar. (`Image`, `Video` and its
subclasses, `InsightsLog`, `FlowToken` and `PairSession` are **not** EventEmitters — they have no
`.on()`.)

```python
discovery_strategy.on("result", self.handle_discovery_result)
node.on("online", on_online)
node.command_classes["COMMAND_CLASS_BASIC"].on("report", on_report)
```

### Timers

`self.homey.set_interval(callback, ms, *args, **kwargs) -> int` and
`self.homey.set_timeout(callback, ms, *args, **kwargs) -> int` mirror JS (delay is the **second**
argument, in milliseconds) and are automatically cleared when the Homey instance is destroyed.
Clear them explicitly with `clear_interval(id)` / `clear_timeout(id)`. `callback` may be an
`async def` function:

```python
self.poll_interval = self.homey.set_interval(self.poll, POLL_INTERVAL)
...
self.homey.clear_interval(self.poll_interval)
```

Prefer these over `asyncio.sleep` loops so timers die with the app.

---

## 7. Class reference

### `SimpleClass` (`homey.simple_class`)

Base of `App`, `Driver`, `Device`, `Homey`, `Manager`, `FlowCard`, `FlowArgument`, `Widget`,
`WidgetSetting`, `Signal`, `DiscoveryResult`, `DiscoveryStrategy`, `CloudWebhook`,
`CloudOAuth2Callback`, `Ble*`, `ZigbeeNode`, `ZWaveNode`, `ZWaveCommandClass`.

| Method | Signature | Description |
| --- | --- | --- |
| `log` | `log(*args) -> None` | Log; emits a `__log` event. Replaces `this.log(...)`. |
| `error` | `error(*args) -> None` | Log an error; emits `__error`. Replaces `this.error(...)`. |
| `debug` | `debug(*args) -> None` | Log debug output; emits `__debug`. |
| `on_log` | `on_log(f: Callable[..., None]) -> Self` | Fires when `log()` is called. |
| `on_error` | `on_error(f: Callable[..., None]) -> Self` | Fires when `error()` is called. |
| `on_debug` | `on_debug(f: Callable[..., None]) -> Self` | Fires when `debug()` is called. |

### `App` (`homey.app`)

| Member | Type | Description |
| --- | --- | --- |
| `homey` | `Final[Homey]` | The Homey instance this app runs on. |
| `id` | `Final[str]` | App ID. |
| `manifest` | `Final[Any]` | The `app.json` manifest. |
| `sdk` | `Final[int]` | SDK version. |
| `on_init()` | `async` | Called when initializing the app. Override for setup. |
| `on_uninit()` | `async` | Called when unloading the app. Override for cleanup. |

### `Driver` (`homey.driver`)

Never instantiate it yourself — Homey constructs it at app start. Generic over the device class:
`class MyDriver(driver.Driver[MyDevice])`.

| Member | Signature | Description |
| --- | --- | --- |
| `homey` | `Final[Homey]` | |
| `manifest` | `Final[Any]` | The driver's section of `app.json`. |
| `id` | `Final[str]` | Driver ID. |
| `on_init()` | `async` | Called when the driver is loaded and its devices are available. |
| `on_uninit()` | `async` | Called when unloading the driver. |
| `ready()` | `async` | Resolves when the driver is ready (i.e. `on_init` has run). |
| `on_pair(session)` | `async` | Called when a pairing session starts. Default implementation supports the standard flow. |
| `on_repair(session, device=None)` | `async` | Called when a re-pairing session starts. |
| `on_unpair(session, device=None)` | `async` | Called when an unpairing session starts. |
| `on_pair_list_devices(view_data)` | `async -> list[ListDeviceProperties]` | Called when `on_pair` is not overridden and the `list_devices` view asks for devices. |
| `on_map_device_class(device)` | `async -> type[Device]` | Called when initializing a device to decide which class to construct it with. The `device` argument is typed **`ListDeviceProperties`** (a dict), not a `Device`. |
| `get_device(device_data)` | `-> Device` | Get a device matching the given `data`. Raises `NotFound`. |
| `get_device_by_id(device_id)` | `-> Device` | Get a device by the ID Homey assigned. Raises `NotFound`. |
| `get_devices()` | `-> tuple[Device, ...]` | All devices of this driver. |
| `get_discovery_strategy()` | `-> DiscoveryStrategy \| None` | The discovery strategy from `app.json`. |

Quoted verbatim from the Python reference (see the caveat below it):

```python
from homey.driver import Driver
from device import MyDevice, MyDimDevice

class MyDriver(Driver):
    def on_map_device_class(self, device):
        return MyDimDevice if device.has_capability("dim") else MyDevice

homey_export = MyDriver
```

> The reference documents `on_map_device_class` as
> `async def on_map_device_class(self, device: ListDeviceProperties) -> type[Device]`, while its own
> example is a plain `def` that calls `device.has_capability("dim")` — a method a
> `ListDeviceProperties` dict does not have. Follow the documented example shape when in doubt,
> read the capability list off the mapping (`"dim" in device.get("capabilities", [])`), and return
> the class object, never an instance.

#### `ListDeviceProperties` (TypedDict, `homey.driver`)

The dict shape returned from `on_pair_list_devices()` or a `list_devices` handler. **Only `data` is
required.**

| Key | Type | Description |
| --- | --- | --- |
| `data` | `dict[str, Any]` | **Required.** Immutable data of the device. By default `data["id"]` distinguishes devices. Use something stable (MAC, serial) — never an IP address. |
| `store` | `dict[str, Any]` | Mutable data that should persist. |
| `settings` | `dict[str, bool \| float \| str \| None]` | Initial values for the device's settings. |
| `capabilities` | `list[str]` | Capabilities of this particular device. |
| `capabilitiesOptions` | `dict[str, dict[str, Any]]` | Per-capability options. **camelCase key** — it maps onto the manifest. |
| `name` | `str` | Display name in the UI. |
| `icon` | `str` | Filename of the icon, relative to `/drivers/<driver_id>/assets/`. |

```python
from homey.driver import Driver, ListDeviceProperties

class MyDriver(Driver):
    async def on_pair_list_devices(self, view_data: dict) -> list[ListDeviceProperties]:
        api_devices = await get_api_devices()
        pair_devices: list[ListDeviceProperties] = [
            {"data": {"id": api_device.id}}
            for api_device in api_devices
            if api_device.type == 5
        ]
        return pair_devices

homey_export = MyDriver
```

### `Device` (`homey.device`)

| Member | Signature | Notes |
| --- | --- | --- |
| `driver` | `Final[Driver]` | |
| `homey` | `Final[Homey]` | |
| `on_init()` | `async` | Data, settings and capabilities are available. |
| `on_uninit()` | `async` | Cleanup. |
| `ready()` | `async` | Resolves once `on_init()` has run. |
| `on_added()` | `async` | Device added by a user. |
| `on_deleted()` | `async` | Device removed by a user. |
| `on_renamed(name)` | `async` | Device renamed by a user. |
| `on_settings(old_settings, new_settings, changed_keys)` | `async -> str \| None` | Return a custom message to show the user, or `None`. Raise to reject the settings; the message is shown to the user. |
| `get_capability_value(id)` | `-> bool \| float \| str \| None` | Raises `NotFound`. |
| `set_capability_value(id, value)` | `async` | Raises `NotFound`. |
| `get_state()` | `-> mappingproxy[str, bool \| float \| str \| None]` | All capability values. |
| `has_capability(id)` | `-> bool` | |
| `get_capabilities()` | `-> tuple[str, ...]` | |
| `add_capability(id)` | `async` | Expensive — guard with `has_capability`. |
| `remove_capability(id)` | `async` | Expensive; breaks Flows that use the capability. |
| `get_capability_options(id)` | `-> mappingproxy[str, Any]` | Raises `NotFound`. |
| `set_capability_options(id, options)` | `async` | Expensive. Raises `NotFound`. |
| `register_capability_listener(capability_id, listener)` | `-> None` | Listener is async. |
| `register_multiple_capability_listener(capability_ids, listener, debounce_timeout=250)` | `-> None` | Debounce in ms. |
| `trigger_capability_listener(capability_id, value, **kwargs)` | `async` | Also updates the capability value. |
| `get_setting(key)` / `get_settings()` | sync | |
| `set_settings(settings)` | `async` | May be a subset. **Does not** call `on_settings()`. |
| `get_id()` / `get_data()` / `get_store()` | sync | `get_data()` and `get_store()` return `mappingproxy`. |
| `set_store_value(key, value)` / `unset_store_value(key)` | `async` | |
| `set_album_art_image(image)` | `async` | |
| `set_camera_image(id, title, image)` | `async` | `id` e.g. `"front"`, `title` e.g. `"Front Camera"`. |
| `set_camera_video(id, title, video)` | `async` | Same id/title semantics; an image with the same `id` becomes the loading background. |
| `get_energy()` / `set_energy(energy)` | sync / `async` | `set_energy` overwrites the **whole** energy object and permanently overrides `driver.compose.json`. |
| `get_available()` | `-> bool` | |
| `set_available()` / `set_unavailable(message=None)` | `async` | Unavailable blocks all capabilities and Flow actions. |
| `set_warning(message=None)` / `unset_warning()` | `async` | Persistent — unset it yourself. |
| `get_class()` / `set_class(device_class)` | sync / `async` | Changing the class can break Flows. |
| `get_name()` | `-> str` | |
| `set_last_seen_at()` | `async` | Call when the device is known to be alive. |
| `on_discovery_result(discovery_result)` | `async -> bool` | Default compares `data.id`. |
| `on_discovery_available(discovery_result)` | `async` | Raising here makes the device unavailable with that message. |
| `on_discovery_last_seen_changed(discovery_result)` | `async` | |
| `on_discovery_address_changed(discovery_result)` | `async` | |

#### Capability listeners

`CapabilityListener` — `async def __call__(value, **kwargs) -> None`. Optional Flow arguments such as
`duration` arrive as keyword arguments. Raising an exception aborts the change and shows the error
message to the user.

```python
from device_api import DeviceApi
from homey import device

DEFAULT_DIM_DURATION = 1000

class Device(device.Device):
    async def on_init(self) -> None:
        async def dim_listener(value: bool, *, duration: int | None, **kwargs) -> None:
            await DeviceApi.set_my_device_state(
                {"on": value, "duration": duration or DEFAULT_DIM_DURATION}
            )

        self.register_capability_listener("dim", dim_listener)

homey_export = Device
```

`MultipleCapabilityListener` — `async def __call__(values, **kwargs: dict[str, Any]) -> None`.
`values` maps capability id → new value; each keyword argument is the option mapping for one
capability, e.g. the SDK calls `listener({"onoff": True, "dim": 0.8}, dim={"duration": 300})`.

```python
from typing import TypedDict

from device_api import DeviceApi
from homey import device


class LightCapabilityValues(TypedDict, extra_items=device.CapabilityValue):
    onoff: bool
    dim: float


class Device(device.Device):
    async def on_init(self) -> None:
        async def light_capability_listener(values: LightCapabilityValues, **kwargs) -> None:
            onoff, dim = values["onoff"], values["dim"]
            if dim > 0 and not onoff:
                await DeviceApi.set_on_off_async(False)   # turn off
            elif dim <= 0 and onoff:
                await DeviceApi.set_on_off_async(True)    # turn on
            else:
                await DeviceApi.set_on_off_and_dim_async(**values)

        self.register_multiple_capability_listener(["onoff", "dim"], light_capability_listener)


homey_export = Device
```

### `Homey` (`homey.homey`)

Reachable as `self.homey` on `App`, `Driver` and `Device`, and passed into every `api.py` handler.

| Property | Type |
| --- | --- |
| `app` | `Final[App]` — this app |
| `manifest` | `Final[Any]` — the app manifest |
| `version` | `Final[str]` |
| `env` | `Final[dict]` — variables from `env.json` |
| `platform` | `Final[Literal['local', 'cloud']]` |
| `platform_version` | `Final[Literal[1, 2]]` |
| `platform_features` | `Final[tuple[Literal['speaker', 'ledring', 'nfc', 'camera-streaming', 'matter', 'ble-advertisements'] \| str, ...]]` |

| Product | `platform` | `platform_version` |
| --- | --- | --- |
| Homey Cloud | `cloud` | `1` |
| Homey Pro (Early 2023) | `local` | `2` |

| Method | Signature | Description |
| --- | --- | --- |
| `ready()` | `async` | Resolves when Homey is ready (`App.on_init()` has run). |
| `translate(key, **tags)` | `-> str \| None` | Translate from `/locales/<language>.json`. Dots denote nesting (`"errors.missing"`). Returns `None` if the key is missing. |
| `set_interval(callback, ms, *args, **kwargs)` | `-> int` | Auto-cleared on destroy. |
| `clear_interval(id)` | `-> None` | |
| `set_timeout(callback, ms, *args, **kwargs)` | `-> int` | Auto-cleared on destroy. |
| `clear_timeout(id)` | `-> None` | |
| `has_feature(feature)` | `-> bool` | Available since Homey v12.7.1. |
| `has_permission(permission)` | `-> bool` | |
| `on_cpuwarn(f)` | `Callable[[int, int], None]` | Receives (warnings sent, max warnings before kill). |
| `on_memwarn(f)` | `Callable[[int, int], None]` | Same shape. |
| `on_unload(f)` | `Callable[[], None]` | Fired when the app is stopped. |

```python
# /locales/en.json : { "welcome": "Welcome, __name__!" }
welcome_message = self.homey.translate("welcome", name="Dave")
self.log(welcome_message)
```

**Environment variables.** The documented instance property is `self.homey.env`, a `dict`. The docs
also show module-level access `import homey` → `homey.env["WEBHOOK_ID"]` and
`from homey.homey import Homey` → `Homey.env.get("CLIENT_ID")` for module-scope constants. Samples
that write `Homey.env.CLIENT_ID` (attribute access) are unconverted JavaScript — use subscript or
`.get()`.

### Managers on the `Homey` instance

| Attribute | Class | Module | Purpose |
| --- | --- | --- | --- |
| `api` | `ManagerApi` | `homey.manager.api` | Homey Web API access, realtime events, app-to-app. |
| `apps` | `ManagerApps` | `homey.manager.apps` | Query other installed apps. |
| `arp` | `ManagerArp` | `homey.manager.arp` | Address Resolution Protocol. |
| `ble` | `ManagerBLE` | `homey.manager.ble` | Bluetooth Low Energy. |
| `clock` | `ManagerClock` | `homey.manager.clock` | Timezone. |
| `cloud` | `ManagerCloud` | `homey.manager.cloud` | OAuth2 callbacks, webhooks, Homey ID. |
| `dashboards` | `ManagerDashboards` | `homey.manager.dashboards` | User dashboards / widgets. |
| `discovery` | `ManagerDiscovery` | `homey.manager.discovery` | mDNS-SD / SSDP / MAC discovery. |
| `drivers` | `ManagerDrivers` | `homey.manager.drivers` | Drivers in this app. |
| `flow` | `ManagerFlow` | `homey.manager.flow` | Flow cards and tokens. |
| `geolocation` | `ManagerGeolocation` | `homey.manager.geolocation` | Homey's location. |
| `i18n` | `ManagerI18n` | `homey.manager.i18n` | Translations, language, units. |
| `images` | `ManagerImages` | `homey.manager.images` | Images. |
| `insights` | `ManagerInsights` | `homey.manager.insights` | Insights logs. |
| `notifications` | `ManagerNotifications` | `homey.manager.notifications` | Timeline notifications. |
| `rf` | `ManagerRF` | `homey.manager.rf` | 433 MHz / 868 MHz / Infrared. |
| `settings` | `ManagerSettings` | `homey.manager.settings` | Persistent app settings. |
| `videos` | `ManagerVideos` | `homey.manager.videos` | Camera video streams. |
| `zigbee` | `ManagerZigbee` | `homey.manager.zigbee` | Zigbee nodes. |
| `zwave` | `ManagerZWave` | `homey.manager.zwave` | Z-Wave nodes. |

Every manager extends `Manager` → `SimpleClass`, so `log` / `error` / `debug` / `on_log` /
`on_error` / `on_debug` are available on all of them.

#### Manager method summaries

| Manager | Methods |
| --- | --- |
| `ManagerApi` | `get(uri)`, `post(uri, body)`, `put(uri, body)`, `delete(uri)`, `realtime(event, data)`, `get_api(uri)`, `get_api_app(app_id)`, `unregister_api(api)`, `get_local_url()`, `get_owner_api_token()` (requires `homey:manager:api`; token expires after two weeks unused) |
| `ManagerApps` | `get_installed(app)`, `get_version(app)` — both take an `ApiApp` |
| `ManagerArp` | `get_mac(ip)` |
| `ManagerBLE` | `discover(service_filter=None)`, `find(peripheral_uuid)`, `subscribe_to_advertisements(peripheral_uuid, callback, rate_limit_ms=1000)`, `unsubscribe_from_advertisements(peripheral_uuid)` — all require `homey:wireless:ble`; advertisement subscriptions require `has_feature("ble-advertisements")` and only one callback per peripheral |
| `ManagerClock` | `get_timezone()`, `on_timezone_change(f)` |
| `ManagerCloud` | `create_oauth2_callback(url)`, `create_webhook(id, secret, data={})`, `unregister_webhook(webhook)`, `get_homey_id()`, `get_local_address()` |
| `ManagerDashboards` | `get_widget(id)` → `Widget`; raises `NotFound` |
| `ManagerDiscovery` | `get_strategy(id)` → `DiscoveryStrategy`; raises `NotFound` |
| `ManagerDrivers` | `get_driver(id)`, `get_drivers()` → `mappingproxy[str, Driver]` |
| `ManagerFlow` | `get_action_card(id)`, `get_condition_card(id)`, `get_trigger_card(id)`, `get_device_trigger_card(id)`, `create_token(id, type, title, value=None)`, `get_token(id)`, `unregister_token(token)` |
| `ManagerGeolocation` | `get_latitude()`, `get_longitude()`, `get_accuracy()` (all require `homey:manager:geolocation`), `get_mode()` → `Literal['auto','manual'] \| None` |
| `ManagerI18n` | `get_strings()`, `translate(key, **tags)`, `get_language()` (2-char code), `get_units()` → `Literal['metric','imperial']` |
| `ManagerImages` | `create_image()`, `get_image(id)`, `unregister_image(image)` |
| `ManagerInsights` | `create_log(id, title, units=None, decimals=None)` (raises `AlreadyExists`), `delete_log(log)`, `get_log(id)`, `get_logs()` |
| `ManagerNotifications` | `create_notification(message)` — `**double asterisks**` makes variables bold |
| `ManagerRF` | `cmd(signal, command_id, repetitions=None, device=None)`, `tx(signal, frame, repetitions=None, device=None)`, `enable_signal_rx(signal)`, `disable_signal_rx(signal)`, `get_signal_433(id)`, `get_signal_868(id)`, `get_signal_infrared(id)` — require `homey:wireless:433` / `:868` / `:ir` |
| `ManagerSettings` | `get(key)`, `set(key, value)`, `unset(key)`, `get_settings()` |
| `ManagerVideos` | `create_video_web_rtc(data_channel=True)`, `create_video_rtsp(...)`, `create_video_rtmp(...)`, `create_video_hls(...)`, `create_video_dash(...)`, `create_video_other(...)`, `get_video(id)`, `unregister_video(video)`. The URL-based creators accept `allow_invalid_certificates=False` and `demuxer: Literal['h264','h265','mpegts','ts'] \| None` |
| `ManagerZigbee` | `get_node(device)` → `ZigbeeNode` |
| `ManagerZWave` | `get_node(device)` → `ZWaveNode` |

### `Api` (`homey.api`) and `ApiApp` (`homey.api_app`)

`Api` is a Homey Web API endpoint registered through `ManagerApi.get_api(uri)` (e.g.
`"homey:manager:webserver"`); `ApiApp` is the same thing for another app, from
`ManagerApi.get_api_app(app_id)`. Both are EventEmitters, so realtime events sent to the endpoint
fire on the instance. Neither getter is `async`.

| Class | Members |
| --- | --- |
| `Api` | `get(uri)`, `post(uri, body)`, `put(uri, body)`, `delete(uri)` — all `async`, `uri` relative to `/api`; `unregister()` (**sync**); `on_realtime(f)` → `Self` — `f(event: str, data: Any)` |
| `ApiApp` | everything on `Api`, plus `get_installed()` → `bool` (installed **and** enabled **and** running) and `get_version()` → `str`, both `async`; `on_install(f)` / `on_uninstall(f)` → `Self` — `f()` receives no data |

`ApiRequest` (`homey.api`) is the shape handed to each `api.py` handler: `query`, `params`, `body`
(JSON auto-parsed) and `homey`. See §11.

### `PairSession` (`homey.pair_session`)

Passed into `on_pair` / `on_repair` / `on_unpair`; never construct it.

| Method | Signature | Description |
| --- | --- | --- |
| `set_handler(event, listener)` | `-> Self` | Register an async listener for an event emitted by the pairing view. Anything it returns is sent back to the view. Chainable. |
| `emit(event, data=None)` | `async -> Any` | Emit to the pairing view; returns whatever the view's handler returns. |
| `show_view(id)` | `async` | Show a view by id, as defined in `app.json`. |
| `next_view()` / `prev_view()` | `async` | Navigate the pairing flow. |
| `done()` | `async` | Close the pairing session. |

```python
from homey import driver
from homey.pair_session import PairSession


class Driver(driver.Driver):
    async def on_pair(self, session: PairSession) -> None:
        async def on_show_view(view_id: str) -> None:
            self.log("View:", view_id)

        session.set_handler("showView", on_show_view)


homey_export = Driver
```

### Flow cards

`FlowCard` is the base of `FlowCardAction`, `FlowCardCondition`, `FlowCardTrigger` and
`FlowCardTriggerDevice`. Get instances from `ManagerFlow`; never construct them.

| Method | Description |
| --- | --- |
| `get_argument(name)` | → `FlowArgument`. Raises `NotFound`. |
| `get_argument_values()` | `async` → tuple of mappings, one per card instance, with the user's current selections. |
| `register_argument_autocomplete_listener(name, listener)` | → `Self`. Raises `AlreadyExists` / `NotFound`. |
| `register_run_listener(listener)` | → `Self`. Raises `AlreadyExists`. Raising inside the listener fails the Flow with that message. |
| `on_update(f)` | → `Self`. Fired when the user edits/saves a Flow using the card. `f` is `Callable[[], None]` — it receives **no** arguments; re-read the values with `await get_argument_values()`. |

Return type of the run listener per card type:

| Class | `register_run_listener` return | Extra |
| --- | --- | --- |
| `FlowCardAction` | `None \| dict` — return a dict of Advanced Flow tokens | |
| `FlowCardCondition` | `bool` — whether the condition is met | |
| `FlowCardTrigger` | `bool` — whether the Flow should start | `trigger(tokens={}, **trigger_kwargs)` |
| `FlowCardTriggerDevice` | `bool` | `trigger(device, tokens={}, **trigger_kwargs)` — card must declare a `device` argument with a `driver_id` filter |

`RunListener` — `async def __call__(card_arguments: Mapping[str, Any], **trigger_kwargs) -> ReturnType`.
`card_arguments` holds the values the user selected in the card; `trigger_kwargs` holds whatever was
passed to `trigger()`.

`ArgumentAutocompleteListener` — `async def __call__(query: str, **kwargs) -> list[ArgumentAutocompleteResult]`,
where `kwargs` are the other card arguments as currently selected.

`ArgumentAutocompleteResult` keys: `name` (shown and used), `description`, `icon` (path to an `.svg`),
`image` (path to a non-SVG image), `data` (free-form, handed to the run listener).

`FlowArgument.register_autocomplete_listener(listener)` does the same for a single argument.

`FlowToken`: `get_value()`, `set_value(value)` (`async`), `unregister()` (`async`) — both raise
`NotRegistered`. Token types: `"string"`, `"number"`, `"boolean"`, `"image"`.

```python
from homey import app
from rain_api import RainApi


class App(app.App):
    async def on_init(self) -> None:
        rain_start_trigger = self.homey.flow.get_trigger_card("rain_start")

        async def run_listener(card_arguments, **trigger_kwargs) -> bool:
            # card_arguments is the user input, e.g. {"location": "New York"}
            # trigger_kwargs are the parameters passed in trigger()
            return card_arguments.get("location") == trigger_kwargs.get("location")

        rain_start_trigger.register_run_listener(run_listener)

        async def on_raining(city: str, amount: float) -> None:
            tokens = {"mm_per_hour": amount}
            try:
                self.log(await rain_start_trigger.trigger(tokens, location=city))
            except Exception as e:
                self.error(e)

        RainApi.on("raining", on_raining)


homey_export = App
```

Device trigger cards live on the driver and are fired from the device:

```python
# /drivers/<driver_id>/driver.py
from homey import driver
from homey.flow_card_trigger_device import FlowCardTriggerDevice

from .device import Device


class Driver(driver.Driver):
    device_turned_on: FlowCardTriggerDevice | None

    async def on_init(self) -> None:
        self.device_turned_on = self.homey.flow.get_device_trigger_card("turned_on")

    async def trigger_my_flow(self, device: Device, tokens: dict, state: dict) -> None:
        if self.device_turned_on:
            await self.device_turned_on.trigger(device, tokens, **state)


homey_export = Driver
```

### Widgets — `ManagerDashboards`, `Widget`, `WidgetSetting`

| Class | Members |
| --- | --- |
| `ManagerDashboards` | `get_widget(id)` → `Widget` (raises `NotFound`) |
| `Widget` | `register_setting_autocomplete_listener(id, listener)` → `Self` (raises `AlreadyExists` / `NotFound`); `get_setting(id)` → `WidgetSetting` (raises `NotFound`) |
| `WidgetSetting` | `register_autocomplete_listener(listener)` (raises `AlreadyExists`) |

`SettingAutocompleteListener` — `async def __call__(query: str, settings: dict[str, SettingValue | SettingAutocompleteResult]) -> list[SettingAutocompleteResult]`.
Note the second parameter is **positional `settings`**, unlike Flow autocomplete which spreads the
other arguments as keywords.

`SettingAutocompleteResult` keys: `name`, `description`, `icon`, `image`, `data`.

```python
from homey import app
from homey.widget import SettingAutocompleteResult


class App(app.App):
    async def on_init(self) -> None:
        widget = self.homey.dashboards.get_widget("my-widget")

        async def autocomplete_listener(query, settings) -> list[SettingAutocompleteResult]:
            results: list[SettingAutocompleteResult] = [
                {
                    "name": "Mozart",
                    "description": "...",
                    "image": "https://some.url/",
                    "data": {"id": "mozart"},
                },
                {"name": "Amadeus", "data": {"id": "amadeus"}},
            ]
            return [r for r in results if query.lower() in r["name"].lower()]

        widget.register_setting_autocomplete_listener("artist", autocomplete_listener)


homey_export = App
```

> In the widget frontend the extra properties of a Python autocomplete result are read back under
> `data`: `Homey.getSettings()['mySettingId'].data`. See `references/widgets.md`.

### Images, Insights, Videos

`Image` (from `ManagerImages.create_image()`): `set_path(path)` (e.g. `/userdata/kitten.jpg`),
`set_url(url)` (must be `https://`, raises `ValueError` otherwise), `set_stream(source)`,
`get_stream()` → `StreamReturn`, `pipe(stream)` → `ImageStreamMetadata`, `update()`, `unregister()`.
`get_stream()` and `pipe()` raise `HomeyError` if the image is not registered; `update()` and
`unregister()` raise `NotRegistered`. `pipe()` also raises `ValueError` if the stream is not
writable.

`StreamReturn` is a dict with two keys: `data` (a `Writable`, whose `.buffer` is the underlying
`io.BytesIO`) and `meta` (an `ImageStreamMetadata`). `ImageStreamMetadata` keys are `filename`,
`contentType` and `contentLength` (camelCase); `contentLength` is not required when it can be
inferred. Reading an image token in a Flow run listener therefore looks like:

```python
image_stream = await card_arguments["droptoken"].get_stream()
self.log(image_stream["meta"]["contentType"], image_stream["meta"]["filename"])
with open(os.path.join("/userdata", image_stream["meta"]["filename"]), "wb") as target_file:
    target_file.write(image_stream["data"].buffer.read())
```

`set_path()`, `set_url()` and `set_stream()` are **sync**; `update()` and `unregister()` are `async`.
You can switch delivery type at any time by calling a different setter. Image streams require Homey
v2.2.0 or higher.

```python
from io import BytesIO

import aiohttp
from homey import app


class App(app.App):
    async def on_init(self) -> None:
        my_image = await self.homey.images.create_image()

        async def stream_image(stream: BytesIO):
            async with aiohttp.ClientSession() as session:
                async with session.get("http://192.168.1.100/image.png") as res:
                    if not res.ok:
                        raise Exception("Invalid Response")
                    stream.write(await res.read())

        my_image.set_stream(stream_image)


homey_export = App
```

`InsightsLog.create_entry(value)` (`async`) adds a data point.

`Video` → `VideoWithURL` → `VideoWebRTC` / `VideoRTSP` / `VideoRTMP` / `VideoHLS` / `VideoDASH` /
`VideoOther`. `VideoWithURL.register_video_url_listener(listener)` takes an async callable returning
the URL. `VideoWebRTC` adds `register_offer_listener(listener)` (async, receives the SDP offer,
returns `WebRTCAnswer` = `{"answerSdp": str, "streamId": str | None}`) and
`register_keep_alive_listener(listener)` (async, receives a stream id). Attach with
`Device.set_camera_video(id, title, video)`.

```python
# /drivers/my-rtsp-camera/device.py
from homey import device


class Device(device.Device):
    async def on_init(self) -> None:
        try:
            video = await self.homey.videos.create_video_rtsp(
                allow_invalid_certificates=True, demuxer="h265"
            )

            async def url_listener() -> str:
                settings = self.get_settings()
                username, password = settings.get("username"), settings.get("password")
                return f"rtsp://{username}:{password}@192.168.1.100:554/stream"

            video.register_video_url_listener(url_listener)
            await self.set_camera_video("main", "Main Camera", video)
        except Exception as err:
            self.error("Error creating camera:", err)


homey_export = Device
```

### Discovery, BLE, RF, Zigbee, Z-Wave classes

| Class | Key members |
| --- | --- |
| `DiscoveryStrategy` | `get_discovery_results()` → `mappingproxy[str, Result]`; `.on("result", handler)` |
| `DiscoveryResult` | `id`, `address`, `last_seen` (`datetime`), `on_address_changed(f)`, `on_last_seen_changed(f)` |
| `DiscoveryResultMAC` | `+ mac` |
| `DiscoveryResultMDNSSD` | `+ full_name`, `name`, `host`, `port`, `txt` |
| `DiscoveryResultSSDP` | `+ port`, `headers` |
| `BleAdvertisement` | `id`, `uuid`, `local_name`, `address`, `address_type` (`'random' \| 'public'`), `connectable`, `manufacturer_data`, `service_data` (tuple of `ServiceData(uuid, data)` named tuples), `service_uuids`, `rssi`, `timestamp` (Unix epoch ms); `connect()` → `BlePeripheral`, raises `NotConnected` if not connectable |
| `BlePeripheral` | `id`, `uuid`, `address`, `address_type` (`'random' \| 'public' \| 'unknown'`), `connectable`, `state` (`'error' \| 'connecting' \| 'connected' \| 'disconnecting' \| 'disconnected'`), `connected`, `rssi`, `services` (only filled after `discover_services()` / `discover_all()`); `connect()`, `disconnect()`, `get_service(uuid)`, `discover_services(uuid_filter=None)`, `discover_all()`, `update_rssi()`, `read(service_uuid, characteristic_uuid)`, `write(service_uuid, characteristic_uuid, data)`, `on_disconnect(f)` — `f()` receives no data |
| `BleService` | `id`, `uuid`, `characteristics`; `get_characteristic(uuid)`, `discover_characteristics(uuid_filter=None)`, `read(characteristic_uuid)`, `write(characteristic_uuid, data)` |
| `BleCharacteristic` | `id`, `uuid`, `value`, `properties` (`'broadcast' \| 'read' \| 'writeWithoutResponse' \| 'write' \| 'notify' \| 'indicate' \| 'authenticatedSignedWrites' \| 'extendedProperties'`), `descriptors`; `read()`, `write(data)`, `discover_descriptors(uuid_filter=None)`, `subscribe_to_notifications(callback)` (one callback at a time), `unsubscribe_from_notification()` |
| `BleDescriptor` | `id`, `uuid`, `value`; `read()`, `write(data)` |
| `Signal` / `Signal433` / `Signal868` / `SignalInfrared` | `cmd(command_id, repetitions=None, device=None)`, `tx(frame, repetitions=None, device=None)`, `enable_rx()`, `disable_rx()`, `on_payload(f)` — `f(payload: tuple[int, ...], first: bool)` |
| `ZigbeeNode` | `ieee_address`, `manufacturer_name`, `product_id`; `send_frame(endpoint_id, cluster_id, frame)`; **override `handle_frame(endpoint_id, cluster_id, frame, meta)` or it throws when a frame arrives** |
| `ZWaveNode` | `battery`, `device_class_basic/generic/specific`, `firmware_id`, `manufacturer_id`, `product_id`, `product_type_id`, `node_id`, `multi_channel_node`, `multi_channel_node_id`, `multi_channel_nodes`, `online`, `command_classes`; `send_command(command_class_id, command_id, params=None)`, `on_online(f)`, `on_nif(f)`, `on_unknown_report(f)` |
| `ZWaveCommandClass` | `send_command(command, arguments=None)` → the device's response; `on_report(f)` — the reference types `f` as `Callable[[Command, dict, int], None]`, i.e. `f(command, report, node_id)`, while the Z-Wave guide's example declares only `f(command, report)`. Accept `*args` or a trailing default if you are unsure. `Command` is a dict with `name` and `value`. |
| `CloudWebhook` | `on_message(f)` — `f(WebhookMessage)` with `headers`, `query`, `body`; `unregister()` |
| `CloudOAuth2Callback` | `on_url(f)` — `f(url: str)`, the absolute sign-in URL the user must be sent to; `on_code(f)` — `f(code: str \| Exception)`, the OAuth2 code to swap for an access token, or an `Exception` if something went wrong |

```python
# /drivers/<driver_id>/device.py — raw Zigbee
from homey import device


class Device(device.Device):
    async def on_init(self) -> None:
        node = await self.homey.zigbee.get_node(self)

        async def handle_frame(endpoint_id: int, cluster_id: int, frame: bytes, meta: dict) -> None:
            if endpoint_id == 1 and cluster_id == 6:
                ...  # frame from endpoint 1, cluster 'onOff'

        node.handle_frame = handle_frame

        try:
            await node.send_frame(1, 6, bytes([1, 0, 1]))  # endpoint, cluster, [fc, tsn, cmd 'on']
        except Exception as e:
            self.error(e)


homey_export = Device
```

---

## 8. Typing with `homey-stubs` and pyright

The runtime `homey` module is provided by Homey, not by PyPI. Install the stub package for IDE
completion and static checking:

```bash
python -m pip install homey-stubs pyright
```

Install it into a project [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments),
or globally to have it available for all projects. To silence pyright's warning about the missing
source of the `homey` module:

```toml
# pyproject.toml
[tool.pyright]
reportMissingModuleSource = 'none'
```

`homey-stubs` is a **development-only** dependency. Do not add it with
`homey app dependencies add`; if you want it tracked by the CLI use the `dev` keyword
(`homey app dependencies add dev …`).

Typing patterns the docs use:

```python
from typing import TypedDict, cast

# 1. Narrow homey.app / self.driver, which are typed as the base classes
data = await cast(App, self.homey.app).client.get_data()
await cast(Driver, self.driver).trigger_my_flow(self, {}, {})

# 2. Parameterise generics
class Driver(driver.Driver[Device]): ...
discovery_strategy = cast(
    DiscoveryStrategy[DiscoveryResultMDNSSD], self.get_discovery_strategy()
)

# 3. Describe pair-view payloads and card arguments with TypedDict
class LoginData(TypedDict):
    username: str
    password: str
```

---

## 9. Dependency management

Python dependencies must be managed through the Homey CLI so they are pre-compiled for every Homey
platform and bundled with the app. The compiled environments land in `.python_cache/`.

| Command | Description |
| --- | --- |
| `homey app dependencies install` | Installs the libraries listed in the app's dependency file and pre-compiles them for distribution with the app. |
| `homey app dependencies add [dev] <package>[@<version>] [...]` | Adds one or more libraries. With the leading `dev` keyword they are development-only. Adding an already-installed package updates its version constraint. |
| `homey app dependencies remove [dev] <package> [...]` | Removes libraries; `dev` removes from dev dependencies. |
| `homey app dependencies list` | Prints all installed dependencies with resolved versions. |

All four subcommands accept `--find-links` and `--docker-socket-path`.

```bash
homey app dependencies add requests
homey app dependencies add "numpy>=1.26,<2.0"
homey app dependencies add dev pytest
homey app dependencies remove requests
homey app dependencies list
homey app dependencies install
```

### `--find-links` and `--docker-socket-path`

| Flag | Available on | Meaning |
| --- | --- | --- |
| `--find-links <location>` | `homey app build`, `validate`, `run`, `publish`, `dependencies *` | Additional location to search for candidate Python package distributions (Python apps only). Use it for wheels that are not on PyPI. |
| `--docker-socket-path <path>` | `homey app build`, `validate`, `run`, `publish`, `dependencies *` | Path to the Docker socket — needed for Colima, Rancher Desktop, and other non-standard sockets. |

### Why hand-editing `pythonDependencies` breaks the bundle

The manifest array is only a *record* of what the CLI resolved. The bytes that ship with the app come
from the pre-compiled environments in `.python_cache/`, produced by the CLI inside Docker for every
target architecture. Therefore:

* Adding a line to `pythonDependencies` without `homey app dependencies install` → the app is bundled
  with the **old** libraries; the new import fails at runtime on Homey.
* `pip install` / `uv add` into a local venv → the library works on your machine and is **missing
  entirely** from the bundle.
* Always verify with `homey app install` or `homey app run --remote` after touching dependencies.

---

## 10. Running, validating and publishing

No Python-specific commands beyond `dependencies`. The normal cycle applies:

```bash
homey app run                 # Docker container talking to the selected Homey; Ctrl+C uninstalls
homey app run --clean         # wipe userdata / paired devices / settings first
homey app run --remote        # run on the Homey itself
homey app run --network host  # when LAN discovery must come from the host
homey app validate --level debug|publish|verified
homey app install
homey app publish
```

Docker must be running for all of these on a Python app. If the daemon is on a non-default socket
pass `--docker-socket-path <path>`. `homey app run --link-modules` is Node.js-only. Full CLI
reference: `references/cli-and-tooling.md`.

---

## 11. The app Web API in Python (`api.py`)

Routes are declared in the manifest exactly as for Node.js apps:

{% code title="/.homeycompose/app.json" %}

```json
  "api": {
    "get_something":    { "method": "GET",    "path": "/" },
    "add_something":    { "method": "POST",   "path": "/" },
    "update_something": { "method": "PUT",    "path": "/:id" },
    "delete_something": { "method": "DELETE", "path": "/:id" }
  }
```

{% endcode %}

`api.py` exports **async functions** whose names match the route names, with **keyword-only**
parameters, and lists them in `__all__`:

{% code title="/api.py" %}

```python
from typing import Any, Never, cast

from homey.homey import Homey

from .app import App


async def get_something(
    *,
    homey: Homey,
    query: dict[str, str],
    params: dict[str, str],
    body: dict[Never, Never],  # Homey.API sends an empty body for GET requests
) -> Any:
    # query parameters like "/?foo=bar" are read through query.get("foo")
    # the App instance is reachable through homey.app
    result = cast(App, homey.app).get_something()
    return result


async def add_something(
    *, homey: Homey, query: dict[str, str], params: dict[str, str], body: dict[str, Any]
) -> Any:
    return cast(App, homey.app).add_something(body)


async def update_something(
    *, homey: Homey, query: dict[str, str], params: dict[str, str], body: dict[str, Any]
) -> Any:
    return cast(App, homey.app).update_something(body)


async def delete_something(
    *,
    homey: Homey,
    query: dict[str, str],
    params: dict[str, str],
    body: dict[Never, Never],  # Homey.API sends an empty body for DELETE requests
) -> Any:
    return cast(App, homey.app).delete_something(params["id"])


# Export all these methods as endpoints
__all__ = ["get_something", "add_something", "update_something", "delete_something"]
```

{% endcode %}

The `ApiRequest` shape is documented as: `query` (query parameters), `params` (parameters from the
endpoint path), `body` (request body, JSON automatically parsed), `homey` (the Homey instance, used
e.g. to reach the `App` instance).

Widget APIs use the same shape at `/widgets/<widget_id>/api.py` (with `from ...app import App`).

Realtime and app-to-app:

```python
await self.homey.api.realtime("my_event", "my_json_stringifyable_value")

other = self.homey.api.get_api_app("com.athom.otherApp")
is_installed = await other.get_installed()
version = await other.get_version()
get_response = await other.get("/")
post_response = await other.post("/play", {"sound": "bell"})
other.on_realtime(lambda event, *args: print("otherApp.onRealtime", event))
other.on_install(lambda: print("otherApp is installed"))
other.on_uninstall(lambda: print("otherApp is uninstalled"))
```

`homey:manager:api` and `homey:app:<appId>` permissions are not allowed on Homey Cloud.

---

## 12. Gotchas

* **`homey_export` is mandatory.** A module without it does not load. Assign the class, not an
  instance.
* **`get_store_value()` does not exist in Python.** Use `self.get_store().get("key")`; write with
  `await self.set_store_value(...)`.
* **`on_settings` takes three positional arguments**, not a destructured object like JS.
* **Manifest-shaped dict keys stay camelCase** inside Python: `capabilitiesOptions`, `answerSdp`,
  `streamId`, `contentType`, `contentLength`, `$keys`.
* **Sync event callbacks cannot `await`.** Wrap in `asyncio.create_task(...)` and attach a
  done-callback that reports `result.exception()` — otherwise errors vanish.
* **`get_data()` / `get_store()` / `get_settings()` / `get_state()` / `get_capability_options()`
  return `mappingproxy`** — read-only. Mutating them changes nothing; use the setter methods.
* **`add_capability` / `remove_capability` / `set_capability_options` are expensive.** Guard them
  with `has_capability()` / a version check; never call them unconditionally in `on_init`.
* **`set_settings()` does not fire `on_settings()`.**
* **`set_energy()` permanently overrides `driver.compose.json`** and needs the *complete* energy
  object; `get_energy()` returns only the override, not the manifest configuration.
* **Override `ZigbeeNode.handle_frame`** — it throws if a frame arrives and it is not overridden.
* **`Homey.env.CLIENT_ID` in the docs is an unconverted JS sample.** Use `self.homey.env["KEY"]` or
  `.get("KEY")`.
* **Never edit `pythonDependencies` (or `.python_cache/`) by hand.**
* **No `zigbee-clusters`, no `homey-zigbeedriver`, no `homey-oauth2app`** — those are npm packages.
  Python Zigbee/Z-Wave/OAuth2 apps talk to the raw SDK.

---

## 13. Complete minimal Python app skeleton

{% code title="/.homeycompose/app.json" %}

```json
{
  "id": "com.example.minimal",
  "version": "1.0.0",
  "compatibility": ">=13.0.0",
  "runtime": "python",
  "pythonVersion": "3.14",
  "pythonDependencies": [],
  "platforms": ["local"],
  "sdk": 3,
  "brandColor": "#1F8DD6",
  "name": { "en": "Minimal Python App" },
  "description": { "en": "Adds support for Example devices." },
  "category": "lights",
  "tags": { "en": ["example"] },
  "images": {
    "small": "/assets/images/small.png",
    "large": "/assets/images/large.png",
    "xlarge": "/assets/images/xlarge.png"
  },
  "author": {
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}
```

{% endcode %}

{% code title="/app.py" %}

```python
from homey import app

from example_client import ExampleClient


class App(app.App):
    client: ExampleClient

    async def on_init(self) -> None:
        # Shared, app-wide setup. Reachable from drivers/devices as self.homey.app.
        self.client = ExampleClient()
        self.log("Minimal Python App has been initialized")

    async def on_uninit(self) -> None:
        self.log("Minimal Python App is shutting down")


homey_export = App
```

{% endcode %}

{% code title="/drivers/my_driver/driver.compose.json" %}

```json
{
  "name": { "en": "My Device" },
  "class": "light",
  "capabilities": ["onoff", "dim"],
  "platforms": ["local"],
  "connectivity": ["lan"],
  "images": {
    "small": "/drivers/my_driver/assets/images/small.png",
    "large": "/drivers/my_driver/assets/images/large.png",
    "xlarge": "/drivers/my_driver/assets/images/xlarge.png"
  },
  "pair": [
    { "id": "list_devices", "template": "list_devices", "navigation": { "next": "add_devices" } },
    { "id": "add_devices", "template": "add_devices" }
  ]
}
```

{% endcode %}

{% code title="/drivers/my_driver/driver.py" %}

```python
from typing import cast

from homey import driver
from homey.driver import ListDeviceProperties

from ...app import App
from .device import Device


class Driver(driver.Driver[Device]):
    async def on_init(self) -> None:
        # App-level Flow cards belong in app.py; driver-scoped ones live here.
        toast_card = self.homey.flow.get_action_card("show_toast")

        async def on_show_toast(card_arguments, **trigger_kwargs) -> None:
            device: Device = card_arguments["device"]
            message: str = card_arguments["message"]
            await device.create_toast(message)

        toast_card.register_run_listener(on_show_toast)

    # Called when the user opens the 'list_devices' pairing view.
    async def on_pair_list_devices(self, view_data: dict) -> list[ListDeviceProperties]:
        client = cast(App, self.homey.app).client
        return [
            {
                "name": found.name,
                "data": {"id": found.id},
                "store": {"address": found.address},
            }
            for found in await client.discover()
        ]


homey_export = Driver
```

{% endcode %}

{% code title="/drivers/my_driver/device.py" %}

```python
import asyncio
from typing import cast

from homey import device

from ...app import App


class Device(device.Device):
    async def on_init(self) -> None:
        self.log("Device init:", self.get_name(), self.get_class())

        self.client = cast(App, self.homey.app).client
        self.address = self.get_store().get("address")

        self.register_capability_listener("onoff", self.on_capability_onoff)
        self.register_capability_listener("dim", self.on_capability_dim)

        def on_state_changed(is_on: bool) -> None:
            asyncio.create_task(
                self.set_capability_value("onoff", is_on)
            ).add_done_callback(
                lambda t: self.error(t.exception()) if t.exception() else None
            )

        self.client.on("state-changed", on_state_changed)

        await self.set_available()

    async def on_capability_onoff(self, value: bool, **kwargs) -> None:
        # Raising here aborts the change and shows the message to the user.
        await self.client.set_on_off(self.address, value)

    async def on_capability_dim(self, value: float, *, duration: int | None = None, **kwargs) -> None:
        await self.client.set_dim(self.address, value, duration)

    async def on_added(self) -> None:
        self.log("Device added")

    async def on_renamed(self, name: str) -> None:
        await self.client.rename(self.address, name)

    async def on_settings(self, old_settings, new_settings, changed_keys) -> str | None:
        if "address" in changed_keys:
            self.address = new_settings["address"]
        return None

    async def on_deleted(self) -> None:
        self.log("Device deleted")

    async def on_uninit(self) -> None:
        await self.client.disconnect(self.address)

    # Custom method used by the driver's Flow card.
    async def create_toast(self, message: str) -> None:
        await self.client.create_toast(self.address, message)


homey_export = Device
```

{% endcode %}

`homey app create` and `homey app driver create` scaffold the folder structure, assets, locales and
`driver.compose.json`, but generate `driver.js` / `device.js`. For a Python app, set
`runtime`/`pythonVersion`/`pythonDependencies` and `"compatibility": ">=13.0.0"` in
`/.homeycompose/app.json`, and replace the generated `.js` files with the `.py` files above.

---

## Sources

- https://apps.developer.homey.app/the-basics/app — project layout, App class, env, Python version, dependencies, typing, `.homeyignore`
- https://apps.developer.homey.app/the-basics/app/manifest — `runtime`, `pythonVersion`, `pythonDependencies`
- https://apps.developer.homey.app/the-basics/getting-started — Node.js v24, Docker requirement for Python apps
- https://apps.developer.homey.app/the-basics/getting-started/homey-cli — `homey app dependencies …`, `--find-links`, `--docker-socket-path`
- https://apps.developer.homey.app/the-basics/devices — driver/device layout, `on_pair_list_devices`
- https://apps.developer.homey.app/the-basics/devices/pairing — `ListDeviceProperties` fields, `on_repair`
- https://apps.developer.homey.app/the-basics/devices/capabilities — capability listeners
- https://apps.developer.homey.app/the-basics/devices/settings — `on_settings`, `set_settings`
- https://apps.developer.homey.app/the-basics/flow — Flow cards in Python
- https://apps.developer.homey.app/the-basics/flow/arguments — autocomplete, run listeners, `trigger_kwargs`
- https://apps.developer.homey.app/the-basics/flow/tokens — `create_token`, image tokens
- https://apps.developer.homey.app/the-basics/widgets — widget `api.py`
- https://apps.developer.homey.app/the-basics/widgets/settings — `register_setting_autocomplete_listener`
- https://apps.developer.homey.app/advanced/web-api — `api.py`, realtime, app-to-app
- https://apps.developer.homey.app/advanced/images — `Image` paths, URLs, streams
- https://apps.developer.homey.app/advanced/videos — camera videos
- https://apps.developer.homey.app/advanced/custom-views/custom-pairing-views — `PairSession` handlers
- https://apps.developer.homey.app/cloud/webhooks — `create_webhook`, `WebhookMessage`
- https://apps.developer.homey.app/wireless/bluetooth — BLE discovery, notifications, advertisement subscriptions
- https://apps.developer.homey.app/wireless/wi-fi/discovery — discovery strategies and results
- https://apps.developer.homey.app/wireless/zigbee — raw Zigbee frames; `zigbee-clusters` unavailable in Python
- https://apps.developer.homey.app/wireless/z-wave — command classes
- https://apps.developer.homey.app/guides/how-to-breaking-changes — `add_capability`, `remove_capability`, `set_class`
- https://python-apps-sdk-v3.developer.homey.app — full Python API reference (App, Driver, Device, Homey, SimpleClass, PairSession, all managers and classes)
- https://apps-sdk-v3.developer.homey.app — JavaScript API reference, used for the JS ⇄ Python mapping
- https://pypi.org/project/homey-stubs/ — type stubs
