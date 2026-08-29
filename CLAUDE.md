.com# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Homey app for controlling a Stone Connect electric bathroom heater. Built on the Homey Apps SDK v3 with the Python runtime (Python 3.14), `local` platform only. Category: `climate`.

## Architecture

This is a Homey SDK 3 app that uses the **`homey-compose` source layout**. Two facts dominate how this repo is edited:

- **`app.json` at the repo root is generated.** Its first line says so. Never hand-edit it. The source of truth is `.homeycompose/app.json` plus the per-feature folders under `.homeycompose/` (`drivers/`, `flow/{actions,conditions,triggers}/`, `signals/{433,868,ir}/`, `capabilities/`, `discovery/`, `screensavers/`, `locales/`). The Homey CLI merges these into the root `app.json` at build/run time.
- **`.homeybuild/`** is the build output produced by the Homey CLI (gitignored). Do not edit files there; changes will be overwritten. Treat it as a read-only artifact useful for inspecting what the CLI actually produced.

The Python entry point is `app.py`, which exposes a `homey_export` symbol pointing to a subclass of `homey.app.App`. Drivers live under `drivers/<driver-id>/` with their composed definitions in `.homeycompose/drivers/<driver-id>/`. Driver/device modules also expose `homey_export` (pointing at the `Driver` / `Device` subclass). Method names are snake_case (`on_init`, `on_uninit`, `on_settings`, `register_capability_listener`, `set_capability_value`) — this differs from the Node.js SDK docs, which use camelCase.

Localized strings live in `.homeycompose/locales/<lang>.json` (and the merged result in `locales/`). The root `locales/en.json` holds the merged English strings.

### Heater integration

- **`drivers/heater/lib/stone_connect/`** — vendored copy of the async Python client (`StoneConnectHeater`) for the heater's local HTTPS API. Imported by `driver.py` and `device.py` via a `sys.path` insert anchored to `__file__` (the package isn't on the default Python path in the production runtime, so a relative-to-driver path is used instead of an app-root path). Upstream: https://github.com/tomasbedrich/stone-connect (local clone at `~/code/Heating/stone-connect`). **This copy is patched** in two places — reapply both if you re-pull from upstream:
  1. `client.py::_request` always sends a JSON body (defaulting to `{}`) — the firmware on this heater (PCB 571519332 v2.0, FW 1.0.2) rejects bodyless GETs with `"incorrect API request"`.
  2. `set_temperature_and_mode` (and the `set_*` methods that funnel through it: `set_temperature`, `set_operation_mode`, `set_comfort_mode`, `set_eco_mode`, `set_antifreeze_mode`, `set_manual_temperature`, `set_power_mode`, `set_standby`) returns `SetpointResponse` instead of `None`. The DTO is defined in `models.py` and exported from `__init__.py`. The heater's PUT /setpoint reply is a slimmed Status echo (`Client_ID`, `Operative_Mode`, `Set_Point`, `Daily_Energy`, `Last_Update`); upstream throws it away.
- **`drivers/heater/`** — the only driver. `device.py` polls `GET /status` on a configurable interval (default 30s, settable per-device) and forwards capability writes (`onoff` → `set_operation_mode(MANUAL|STANDBY)`, `target_temperature` → `set_manual_temperature`, `boost_duration` → PUT /setpoint with BOOST) to the heater. Power/energy capabilities are populated only when `Info.load_size_watt != 0` (see `has_power_measurement_support()`).
- **UI capability set is intentionally minimal**: `onoff`, `target_temperature`, `boost_duration`, plus the auto-populated `measure_power` / `meter_power` / `alarm_generic`. There is no mode picker — setting a temperature always uses `MANUAL` and turning the device on maps to `MANUAL`. The full mode enum (Comfort/Eco/Antifreeze/High/Medium/Low/Manual) is exposed only through the `set_heater_mode` flow action, whose dropdown ids are the heater's three-letter codes (`CMF`, `ECO`, …) mapping directly to `OperationMode`. STANDBY is reached via `onoff=false`; BOOST is reached via `boost_duration` or the `activate_boost` flow action; SCHEDULE and HOLIDAY are not exposed.
- **Custom capability `boost_duration`** (defined in `.homeycompose/capabilities/boost_duration.json`) is a 0–120 minute slider in 30-minute steps. Values ≥ `BOOST_MINUTES_MIN` send `PUT /setpoint` with `Operative_Mode=BST` and `Set_Point=<minutes>`; values below that end boost by re-sending `MANUAL`. During BOOST the poll loop reads `Set_Point` as remaining minutes (not a temperature) and skips writing `target_temperature`.
- **Pair flow**: a custom `manual_ip.html` view collects host+port; the driver verifies by calling `get_info()`, keys the device by MAC address (`Info.mac_address`), and stores host/port/poll_interval in device settings (which are mutable; the immutable `data.id` is the MAC).
- **Note on the heater API**: there is no ambient-temperature sensor — `get_current_temperature()` on the client returns the *setpoint*, not a measurement. Don't expose `measure_temperature`.

## Commands

This project relies on the Homey CLI (`homey`); there is no package manager manifest in the repo. Typical workflow:

- `homey app run` — install on a paired Homey in development mode with live logs.
- `homey app build` — regenerate `app.json` and populate `.homeybuild/`.
- `homey app validate [--level publish]` — validate the composed app against the SDK schema; use `--level publish` before submitting to the App Store.
- `homey app install` — install the built app on the paired Homey.

There are no tests, lint, or formatter configs in the repo at this time.

Python runtime deps are in `requirements.txt` (currently just `aiohttp`, transitively via `stone_connect`).

### Local dev with podman instead of Docker

`homey app run` and `homey app install` (Python apps) require a Docker-API-compatible engine. On this machine podman replaces Docker. Three manual fixes were applied that get wiped by `brew upgrade homey` / `npm i -g homey`:

1. **`getLocalPlatform()` patch** in `/opt/homebrew/lib/node_modules/homey/lib/AppPython.js` — must return `'linux/amd64'` / `'linux/arm64'`, not the bare `'amd64'` / `'arm64'`. Used by `homey app run` (runner image pull). Docker Desktop tolerates the shorthand; podman rejects it.
2. **`uvCommand()` patch** in the same file — `createOptions.platform` must be set to `` `linux/${platform}` `` (the loop variable `platform` stays as the bare arch because it's also used as the cache folder name `python_packages/<arch>/`, and `_getPackStream`'s regex `\/python_packages\/\w+\/lib` requires a single-word folder). Used by `homey app dependencies install` and `homey app install`.
3. **Docker socket symlink**: `~/.docker/run/docker.sock` → `/var/run/docker.sock` (the path the Homey CLI hardcodes for Docker Desktop's user-space socket). The podman-machine forwarder maintains `/var/run/docker.sock` already.

If a future podman release accepts the bare `arm64`/`amd64` strings, points 1 and 2 become obsolete.

### Python dependencies on Homey Pro

`requirements.txt` is **not** read by Homey Pro at install time. Production deps must be declared in `pythonPackages` in `.homeycompose/app.json` (the Homey CLI manages this — use `homey app dependencies add <pkg>`). On `homey app dependencies install`, the CLI cross-compiles venvs into `python_packages/{arm64,amd64}/`. On `homey app install`, those venvs get bundled into the upload (archive grows from ~700 KB to ~25 MB). Without this, `from stone_connect import …` (which needs `aiohttp`) fails on the Homey, the driver never reaches `ready`, and the pair flow shows a perpetual spinner with `"Driver Not Ready"` in the API response.

## Versioning

App version is set in `.homeycompose/app.json` and propagated to the root `app.json` on build. Changelog entries go in `.homeychangelog.json`, keyed by version string, with per-locale messages.
