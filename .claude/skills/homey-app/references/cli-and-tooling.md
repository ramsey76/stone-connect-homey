# Homey CLI, TypeScript, ESM & Tooling

Complete reference for the `homey` command-line interface (every command, subcommand and option),
the validation levels, live debugging, the Homey Developer Tools site, the TypeScript build step,
ECMAScript Modules support, and `.homeyignore`.

Siblings: `references/app-and-manifest.md` (Homey Compose, manifest keys, `.homeyignore` in context),
`references/publishing.md` (App Store submission), `references/widgets.md` (widget webview debugging),
`references/migration-and-breaking-changes.md` (Node 22 upgrade, SDK v2 → v3),
`references/python-apps.md` (Python runtime), `references/ecosystem-and-ci.md` (GitHub Actions).

---

## 1. Prerequisites & installation

| Requirement | Detail |
| ----------- | ------ |
| **Node.js v24 or higher** | Required to *run the CLI itself*. Install from [nodejs.org](https://nodejs.org/) or, recommended, via [nvm](https://github.com/nvm-sh/nvm) so you can switch versions. |
| **Docker** | Required for Homey Cloud, Homey Pro and Homey Self-Hosted Server targets, and for apps written in Python. Download from [docker.com](https://docs.docker.com/desktop/). |

```bash
npm install --global homey     # installs the CLI and exposes the `homey` command
```

> You may need superuser rights to install packages globally.

**Gotcha — two different Node versions are in play.** The CLI needs **Node.js v24+** on your
workstation; the app you are building runs on **Node.js v22** on Homey (Homey v12.9.0+). Do not
assume a language/stdlib feature available in your local Node 24 is available on Homey. See
`references/migration-and-breaking-changes.md` for the full per-platform Node matrix.

### How `homey app run` executes per platform

| Target | Execution mode | Notes |
| ------ | -------------- | ----- |
| Homey Pro (Early 2023), Homey Pro mini, Homey Cloud, Homey Self-Hosted Server | Local **Docker container** on your machine, exposed to the selected Homey | Docker daemon must be running for `run`, `build`, `validate` and `publish`. |
| Homey Pro (2016—2019) | Uploaded to the Homey and run **remotely** | `--remote` is enabled automatically; Docker cannot be used. Rebuilds are slower than Docker mode. |

Before `homey app run` works, Homey must be either directly connected to your PC/laptop over USB, or
on the same Wi-Fi network as the machine you are working on.

---

## 2. Command map

All `homey app …` commands expect a Homey app in the current working directory (override with
`--path`).

| Command | Purpose |
| ------- | ------- |
| `homey app create` | Scaffold a new app (interactive). |
| `homey app driver create` | Add a driver (interactive). |
| `homey app driver capabilities` | Toggle a driver's capabilities (interactive). |
| `homey app driver firmware` | Attach Zigbee/Z-Wave firmware updates to a driver. |
| `homey app driver flow` | Add a driver-scoped Flow card (interactive). |
| `homey app flow create` | Add an app-level Flow card (interactive). |
| `homey app widget create` | Scaffold a dashboard widget (interactive). |
| `homey app discovery create` | Add a discovery strategy (interactive). |
| `homey app add-types` | Install SDK type declarations + `jsconfig.json`/`tsconfig.json`. |
| `homey app add-github-workflows` | Copy ready-made GitHub Actions into `.github/workflows/`. |
| `homey app build` | Production build (TypeScript compile + Homey Compose + tarball). |
| `homey app compose` | Split a legacy monolithic `app.json` into `.homeycompose/`. |
| `homey app validate` | Validate manifest, assets and compose files. |
| `homey app run` | Build + run in development mode with streaming logs. |
| `homey app install` | Build + install on the selected Homey and leave it installed. |
| `homey app manage` | Open the app in Homey Developer Tools. |
| `homey app publish` | Validate, build and upload to the Homey App Store. |
| `homey app version` | Bump the semver version and write the changelog. |
| `homey app translate` | AI-translate JSON fields and `README.txt`. |
| `homey app review` | AI pre-review against the App Store Guidelines. |
| `homey app view` | Open the app's App Store page. |
| `homey app dependencies install\|add\|remove\|list` | Python dependency management. |
| `homey api schema\|diagnose\|raw\|<manager> <operation>` | Direct Homey API access. |
| `homey login` / `logout` / `whoami` | Athom account authentication. |
| `homey list` / `select` / `select current` / `unselect` | Homey selection. |
| `homey tools` / `homey docs` | Open Developer Tools / the SDK documentation. |
| `homey completion` | Print the shell completion script. |

---

## 3. App commands

### 3.1 `homey app create`

```bash
homey app create
```

Interactive wizard that scaffolds a new empty Homey app. Prompts for the **App ID**, name,
description, category, color, and language, and asks whether to initialize the app with **TypeScript
utilities**. Creates `app.json`, the `.homeycompose/` layout, `README.md`, locale files, and installs
dependencies. The new app lands in a directory named after the chosen App ID.

The App ID must be in [reverse domain name notation](https://en.wikipedia.org/wiki/Reverse_domain_name_notation)
— for `https://solarpanels.acme.org` the ID is `org.acme.solarpanels`.

> The Homey or Athom name cannot be used in your app ID.

**Gotcha:** the app `id` is effectively permanent — changing it after the first publish creates a new
App Store listing and loses installs and reviews.

### 3.2 `homey app driver create`

```bash
homey app driver create
```

Adds a new driver. Prompts for the driver ID, display name, class, capabilities, and pairing method.
Generates `drivers/<id>/` including `driver.js`, `device.js`, and `driver.compose.json`.

When `tsconfig.json` exists in the app root, the CLI **defaults to TypeScript** for generated drivers
(`driver.mts` / `device.mts`).

### 3.3 `homey app driver capabilities`

```bash
homey app driver capabilities
```

Interactive editor listing every available Homey capability; toggle which ones the driver exposes.
Writes the result back to the driver's `driver.compose.json`.

### 3.4 `homey app driver firmware`

```bash
homey app driver firmware --driver <path> --firmware <file> [--firmware <file>...]
```

Register a device firmware update against a driver. Supported for Zigbee and Z-Wave drivers.

| Option | Type | Description |
| ------ | ---- | ----------- |
| `--driver` | string | Path to the driver folder that the firmware update should be attached to. |
| `--firmware` | string (array) | Path to a firmware file. Repeat to attach multiple firmware files at once. |

```bash
homey app driver firmware \
  --driver ./drivers/my-plug \
  --firmware ./firmware/v1.2.3.bin
```

### 3.5 `homey app driver flow`

```bash
homey app driver flow
```

Interactive wizard for a Flow card scoped to a specific driver. Prompts for the card type (trigger,
condition, or action), title and tokens, and generates the card under
`drivers/<id>/driver.flow.compose.json`.

### 3.6 `homey app flow create`

```bash
homey app flow create
```

Same wizard, for app-level Flow cards (not tied to a driver). Writes the card to
`.homeycompose/flow/<type>/<id>.json`.

### 3.7 `homey app widget create`

```bash
homey app widget create
```

Interactive wizard that scaffolds a new dashboard widget: the HTML/CSS/JS files,
`widget.compose.json`, and the light/dark preview images.

**Gotcha:** both `preview-light.png` and `preview-dark.png` must exist — `homey app validate --level
publish` fails with `ENOENT` if either is missing. See `references/widgets.md`.

### 3.8 `homey app discovery create`

```bash
homey app discovery create
```

Interactive wizard that adds a discovery strategy (mDNS-SD, SSDP, or MAC) to
`.homeycompose/discovery/`. See `references/wireless-lan-discovery.md`.

### 3.9 `homey app add-types`

```bash
homey app add-types
```

Installs the Homey Apps SDK type declarations and configures `jsconfig.json` / `tsconfig.json` so
your IDE and the TypeScript compiler can type-check the app. Also used when converting an existing
JavaScript app to TypeScript (see §13.2). The official guide notes the TypeScript config file must
already be present in the app root before you run this command.

### 3.10 `homey app add-github-workflows`

```bash
homey app add-github-workflows
```

Copies ready-made GitHub Actions into `.github/workflows/` for validating, versioning and publishing
your app on push. The published Actions are:

* <https://github.com/marketplace/actions/homey-app-validate>
* <https://github.com/marketplace/actions/homey-app-update-version>
* <https://github.com/marketplace/actions/homey-app-publish>

CI authenticates with the `HOMEY_PAT` environment variable instead of `homey login`.

### 3.11 `homey app build`

```bash
homey app build [options]
```

Creates a production build: compiles TypeScript (if applicable), runs Homey Compose, and produces the
tarball that `install` and `publish` use.

| Option | Type | Description |
| ------ | ---- | ----------- |
| `--docker-socket-path` | string | Path to the Docker socket. Useful when Docker runs on a non-standard socket (Colima, Rancher Desktop, etc.). |
| `--find-links` | string | Additional location to search for candidate Python package distributions (Python apps only). |

### 3.12 `homey app compose`

```bash
homey app compose
```

Splits a legacy monolithic `app.json` into the `.homeycompose/` file layout. Existing files are
preserved. Only useful for apps that predate Homey Compose.

**Gotcha:** the command refuses to run with uncommitted git changes — commit or stash first.

### 3.13 `homey app validate`

```bash
homey app validate [--level debug|publish|verified] [options]
```

Validates the app manifest, assets and compose files. `run`, `install` and `publish` call it
automatically.

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--level`, `-l` | string | `publish` | Validation strictness. See §4. |
| `--docker-socket-path` | string | — | Path to the Docker socket. |
| `--find-links` | string | — | Additional location to search for Python package distributions. |

```bash
homey app validate
homey app validate --level verified
```

### 3.14 `homey app run`

```bash
homey app run [options]
```

Runs and debugs your app. By default it runs in a local Docker container that exposes the app to your
selected Homey. For Homey Pro (2016—2019) the app is automatically uploaded to the Homey and run
remotely. Console output streams to your terminal. Quitting (`Ctrl+C`) **uninstalls** the app from
Homey.

The first time you run a Homey app, a browser window opens asking you to log in with your Athom
account. After logging in, the CLI prints the list of Homeys linked to the account in the terminal;
pick the one to run on and the app starts uploading and running automatically.

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--clean`, `-c` | boolean | `false` | Delete all userdata, paired devices, and settings before running. Useful when testing pairing flows. |
| `--remote`, `-r` | boolean | `false` | Force the app to run on the Homey instead of locally in Docker. Automatically enabled on Homey Pro (2016—2019). |
| `--skip-build`, `-s` | boolean | `false` | Skip the build step. Use only if you know the build output is already up-to-date. |
| `--link-modules`, `-l` | string | `""` | Comma-separated list of local Node.js modules to link into the runner. Docker mode only. |
| `--network`, `-n` | string | `bridge` | Docker network mode. Must match a name from `docker network ls`. Use `host` if your app needs LAN discovery from the host. Docker mode only. |
| `--docker-socket-path` | string | — | Path to the Docker socket. |
| `--find-links` | string | — | Additional location to search for Python package distributions. |

```bash
homey app run
homey app run --clean
homey app run --remote
homey app run --link-modules ../my-library,../another-library
homey app run --network host
```

**Gotcha — Docker `bridge` networking hides your ports.** In the default Docker mode the app runs in
a `bridge` network on your workstation, not on the Homey. A TCP/HTTP port your app opens (a local
server, a webhook receiver, a discovery responder) is **not reachable** from your phone or from other
LAN devices. Use `--network host` (macOS/Linux) when the app needs host-level LAN access, or use
`homey app install` to test LAN-facing behaviour under production networking.

**Gotcha — `--clean` really does wipe everything.** All userdata, paired devices and settings for
that app are deleted. Do not use it on a Homey where you have painstakingly paired real hardware.

**Gotcha — `--link-modules` short flag collides mentally with `--level`.** On `run` the short `-l` is
`--link-modules`; on `validate` the short `-l` is `--level`.

### 3.15 `homey app install`

```bash
homey app install [options]
```

Builds the app and installs it on the currently selected Homey. Unlike `homey app run`, this leaves
the app installed after the command exits and does not stream logs. Good for long-running tests, and
the only way to exercise production networking.

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--clean`, `-c` | boolean | `false` | Delete all userdata, paired devices, and settings before installing. |
| `--skip-build`, `-s` | boolean | `false` | Skip the build step. |

### 3.16 `homey app manage`

```bash
homey app manage
```

Opens `https://tools.developer.homey.app/apps/app/<app-id>` in your default browser.

### 3.17 `homey app publish`

```bash
homey app publish [options]
```

Validates, builds and uploads the app to the Homey App Store. You are prompted to bump the version
and add a changelog if you have not already. The app is compressed and sent to the App Store for
processing; it is submitted as **Draft** by default. Manage releases at
<https://tools.developer.homey.app> → *Apps SDK* → *My Apps*.

| Option | Type | Description |
| ------ | ---- | ----------- |
| `--docker-socket-path` | string | Path to the Docker socket. |
| `--find-links` | string | Additional location to search for Python package distributions. |

Both options are passed through to the internal build step (see `homey app build`). Most developers
can ignore them.

**Gotcha:** `homey app validate --level publish` passing is **not** certification. Athom's human
reviewers reject things the validator never checks (icons, images, naming, Flow card titles). Run
`homey app review` and read `references/publishing.md` first.

**Gotcha:** publishing an app for **Homey Cloud** requires a Verified Developer account — the
`verified` validation level (with `platforms`, `connectivity`, `support`) is what the store enforces
for it.

### 3.18 `homey app version`

```bash
homey app version <next> [--changelog.<lang> "..."] [--commit]
```

Bumps `version` in `app.json`. Homey apps use [semver](https://semver.org/).

| Argument / Option | Type | Description |
| ----------------- | ---- | ----------- |
| `<next>` | string (required) | `patch`, `minor`, `major`, or an explicit semver like `2.0.0`. |
| `--changelog.<lang>` | string | Changelog text for a specific language. Repeat to translate. Written to `.homeychangelog.json`. |
| `--commit` | boolean | Create a git commit and matching tag for the new version. |

```bash
homey app version patch
homey app version minor --commit
homey app version 2.0.0 \
  --changelog.en "Added support for the Awesome Widget" \
  --changelog.nl "Ondersteuning voor de Awesome Widget toegevoegd"
```

### 3.19 `homey app translate`

```bash
homey app translate [options]
```

Uses the OpenAI API to translate your app's `.json` fields and `README.txt` into every language your
app targets. Requires `OPENAI_API_KEY` to be set (or passed with `--api-key`).

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--languages` | string | app's target langs | Comma-separated list of target language codes (e.g. `nl,de,fr`). |
| `--api-key` | string | `$OPENAI_API_KEY` | OpenAI API key. Prefer setting the environment variable. |
| `--model` | string | `gpt-4o` | OpenAI model to use. |
| `--file` | string | — | Absolute path to a single file to translate. Useful when you only edited one string. |

> AI translations vary in quality. Always review the diff before committing.

**Field note:** translating a normal-sized app costs well under one US dollar of OpenAI credit; the
`--file` flag keeps incremental re-translations cheap.

### 3.20 `homey app review`

```bash
homey app review [options]
```

Runs an AI review of your app against the Homey App Store Guidelines before you submit for
certification. The reviewer analyses `app.json`, driver metadata, and every image (app icon, driver
images, widget previews). Returns a verdict of `approve`, `request_changes`, or `reject`, plus
findings grouped by severity (`blocker`, `warning`, `suggestion`).

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--type` | string | `new` | `new` for a first submission, `update` if the app is already live. |
| `--model` | string | Athom's default | Model in `<provider>/<model>` form. Supported providers: `openai`, `anthropic`. Any non-default model prints a warning. |
| `--json` | boolean | `false` | Emit machine-readable JSON instead of pretty output. |
| `--verbose`, `-v` | boolean | `false` | Print token counts, model info, and duration. |

The command reads optional app-specific instructions from a `.homeyreview.md` file at the app root.
Requires `OPENAI_API_KEY` (for OpenAI models) or `ANTHROPIC_API_KEY` (for Anthropic models). **Exits
with code 1 if the verdict is `reject`** — usable as a CI gate.

```bash
export OPENAI_API_KEY="sk-..."
homey app review
homey app review --type update
homey app review --json > review.json
homey app review --model anthropic/claude-opus-4-7 --verbose
```

### 3.21 `homey app view`

```bash
homey app view
```

Opens `https://homey.app/a/<app-id>` in your default browser.

### 3.22 `homey app dependencies` (Python apps)

```bash
homey app dependencies <install|add|remove|list>
```

Manages Python dependencies for Python-based Homey apps. All subcommands accept `--find-links` and
`--docker-socket-path`. Pre-compiled environments are cached in `.python_cache/` in the project
folder. See `references/python-apps.md`.

| Subcommand | Signature | Behaviour |
| ---------- | --------- | --------- |
| `install` | `homey app dependencies install` | Installs libraries listed in the app's dependency file and pre-compiles them for distribution with the app. |
| `add` | `homey app dependencies add [dev] <package>[@<version>] [...]` | Adds one or more libraries as a dependency. With the leading `dev` keyword they are added as development-only dependencies. Adding an already-installed package updates its version constraint. |
| `remove` | `homey app dependencies remove [dev] <package> [...]` | Removes libraries. Use the leading `dev` keyword to remove from dev dependencies. |
| `list` | `homey app dependencies list` | Prints all installed dependencies with their resolved versions. |

```bash
homey app dependencies add requests
homey app dependencies add "numpy>=1.26,<2.0"
homey app dependencies add dev pytest
```

---

## 4. Validation levels

`homey app validate --level <debug|publish|verified>` (default `publish`; the `verified` level is
applied by default when you are logged in with a verified developer account).

| Level | When to use | What it enforces |
| ----- | ----------- | ---------------- |
| `debug` | During development. | Relaxed: manifest properties such as `images`, `brandColor` and `category` are **optional**. |
| `publish` | Required to publish to the Homey App Store for **Homey Pro**. | The full App Store manifest/asset requirements. |
| `verified` | Required for **verified developers** and for **Homey Cloud**. Applied by default for verified accounts. | Everything in `publish` **plus** `platforms`, `connectivity` and `support` in the manifest. |

```bash
homey app validate --level publish     # before shipping to Homey Pro
homey app validate --level verified    # Homey Cloud / Verified Developer
```

---

## 5. `homey api` — direct Homey API access

```bash
homey api <subcommand>
```

| Subcommand | Purpose |
| ---------- | ------- |
| `homey api schema` | Inspect available managers and operations. |
| `homey api diagnose` | Diagnose local discovery / connectivity. |
| `homey api raw` | Perform an arbitrary HTTP request against the Homey. |
| `homey api <manager> <operation>` | Call a manager method. Generated automatically from the Homey API schema. |

### 5.1 `homey api schema`

```bash
homey api schema [--json] [--jq "<expr>"]
```

Prints a human-readable overview of every available API manager and its operations. With `--json` you
get the raw schema, which you can filter with `--jq`.

```bash
homey api schema
homey api schema --json --jq '.managers | keys'
```

### 5.2 `homey api diagnose`

```bash
homey api diagnose [--homey-id <id>] [--json] [--jq "<expr>"]
```

Tries every discovery strategy (local address, mDNS, cloud tunnel, WebSocket relay) against the
selected Homey and prints which ones work, how long they take to respond, and which one is used.
**Exits 0 if at least one strategy is available, 1 otherwise.** This is the first thing to run when
`homey app run` cannot reach your Homey.

| Option | Description |
| ------ | ----------- |
| `--homey-id` | Diagnose a cached Homey by ID instead of the selected Homey. |
| `--json` | Output the diagnosis as JSON. |
| `--jq` | Filter JSON output with a jq expression. |

### 5.3 `homey api raw`

```bash
homey api raw --path <api-path> [--method GET|POST|PUT|...] [options]
```

Aliases: `homey api call`, `homey api request`. Performs an arbitrary Homey API request — useful for
quick debugging, scripting, or exploring the API.

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--path` | string | — | **Required.** Homey API path, must start with `/` (e.g. `/api/manager/system/`). |
| `--method`, `-X` | string | `GET` | HTTP method. Case-insensitive. |
| `--header`, `-H` | string | — | Request header in `"name:value"` form. Repeatable. |
| `--body` | string | — | Request body. Inline JSON, or `@path/to/file.json` to load from disk. |
| `--request-json` | boolean | `true` | Encode the request body as JSON. Disable for raw bodies. |
| `--include` | boolean | `false` | Print status line and response headers in addition to the body. |
| `--verbose` | boolean | `false` | Print the resolved request URL, method, headers and timing to stderr. Sensitive headers are redacted. |
| `--token` | string | — | Use a session token instead of the selected Homey. Requires `--address` or `--homey-id`. |
| `--address` | string | — | Homey base URL for token mode (e.g. `http://192.168.1.100`). |
| `--homey-id` | string | — | Target a cached Homey by ID. |
| `--timeout` | number | `30000` | Request timeout in milliseconds. |
| `--json` | boolean | `false` | Force JSON output even when the response is a plain string. |
| `--jq` | string | — | Filter JSON output with a jq expression. |

```bash
homey api raw --path /api/manager/system/
homey api raw --path /api/manager/system/ --jq '.value.homeyVersion'

homey api raw \
  -X POST \
  --path /api/manager/flow/flow \
  --body '{"name":"Test flow"}'

homey api raw \
  -X POST \
  --path /api/manager/flow/flow \
  --body @./flow.json --verbose
```

### 5.4 `homey api <manager> <operation>`

Every manager in the Homey API is exposed as its own subcommand:

```bash
homey api devices open-device --id <device-id>
```

Run `homey api --help` for the list of available managers, or `homey api schema` to inspect
operations. Each manager command inherits `--homey-id`.

---

## 6. Additional commands

| Command | Behaviour |
| ------- | --------- |
| `homey login` | Opens the OAuth2 dialog in your default browser and stores the resulting session in `~/.homey/`. Required before `homey app run`, `install` or `publish`. For CI/CD, set `HOMEY_PAT` instead. |
| `homey logout` | Clears the stored session from `~/.homey/`. |
| `homey whoami [--json] [--jq "<expr>"]` | Prints the first name, last name and email of the authenticated Athom user. Verified developers are marked as such. |
| `homey list [--json] [--jq "<expr>"]` | Lists every Homey linked to the account with ID, name, platform, version, region and role. Sorted by state (online Homeys first). |
| `homey select [--id <id> \| --name <name>]` | Sets the active Homey for `homey app run`, `homey app install` and every `homey api` command. Without arguments an interactive picker is shown; `--id`/`--name` select non-interactively (scripts). |
| `homey select current [--json] [--jq "<expr>"]` | Prints the currently selected Homey. Exits with a helpful message when nothing is selected. |
| `homey unselect` | Clears the currently selected Homey so subsequent commands prompt for one. |
| `homey tools` | Opens `https://tools.developer.homey.app` in your default browser. |
| `homey docs` | Opens `https://apps.developer.homey.app` in your default browser. |
| `homey completion` | Prints the shell completion script (see §8). |

```bash
homey list --json --jq '.[].name'
homey select --name "Living Room Homey"
```

---

## 7. Global options

| Option | Description |
| ------ | ----------- |
| `--help` | Show help for the current command, including all options and subcommands. |
| `--version`, `-v` | Print the installed CLI version. |
| `--path`, `-p` | Available on every `homey app …` command. Points at the app directory. Defaults to `process.cwd()`. |

Commands that produce structured output additionally support:

| Option | Description |
| ------ | ----------- |
| `--json` | Emit machine-readable JSON. Combine with your own parsing or with `--jq`. |
| `--jq "<expr>"` | Filter the JSON output with a [jq](https://jqlang.org/) expression before printing. |

Commands that currently support `--json`/`--jq`: `homey whoami`, `homey list`, `homey select
current`, `homey api schema`, `homey api diagnose`, `homey api raw`, and (partially) `homey app
review`.

Discovery of everything else:

```bash
homey --help          # all top-level commands
homey app --help      # all app subcommands
homey api --help      # all API managers
```

---

## 8. Shell completion

The CLI ships tab-completion for `bash`, `zsh` and `fish` via yargs.

```bash
homey completion            # print the completion script for your current shell
```

```bash
# zsh
homey completion >> ~/.zshrc
source ~/.zshrc

# bash
homey completion >> ~/.bashrc
source ~/.bashrc

# fish
homey completion > ~/.config/fish/completions/homey.fish
```

After sourcing, `homey <TAB>` completes commands, subcommands and options. `homey api <TAB>`
additionally completes manager names discovered from the Homey API.

---

## 9. Environment variables & CLI state

| Variable | Used by | Description |
| -------- | ------- | ----------- |
| `HOMEY_PAT` | Every command that talks to Athom Cloud | Personal Access Token. Bypasses the interactive login flow. Recommended for CI/CD. |
| `OPENAI_API_KEY` | `homey app translate`, `homey app review` | OpenAI API key. Required unless you pass `--api-key`. |
| `ANTHROPIC_API_KEY` | `homey app review` | Anthropic API key. Required when `--model anthropic/…` is used. |

Persistent state — session tokens, cached Homeys, the selected Homey — lives in **`~/.homey/`**.
Delete this directory to fully reset the CLI.

> Do not confuse these with the app's own secrets: those live in `/env.json` and are read at runtime
> via `Homey.env.NAME`. See `references/app-and-manifest.md`.

---

## 10. Troubleshooting

**"No Homey is currently selected."**
Run `homey select` (interactive) or `homey select --name "<homey>"`. Check the current selection with
`homey select current`.

**"Cannot connect to the Docker daemon."**
`homey app run`, `build`, `validate` and `publish` require Docker to be running on Homey Pro (Early
2023) and later. Start Docker Desktop / Colima / Rancher Desktop. If Docker runs on a non-default
socket, pass `--docker-socket-path <path>`.

**Cannot reach the Homey from Docker.**
Run `homey api diagnose` to see which discovery strategies work. `homey app run --network host`
(macOS/Linux) often helps when local mDNS discovery is required.

**Homey Pro (2016—2019) cannot use Docker.**
Pass `--remote` (or let the CLI do it automatically) to upload and run the app directly on the Homey.
Console output still streams to your terminal but rebuilds are slower than in Docker mode.

**Login flow doesn't open a browser.**
Copy the URL from the terminal into your browser manually.

**`homey app publish` rejects the app because of validation errors.**
Run `homey app validate --level publish` (or `--level verified` for verified developers) locally and
fix each error. See `references/publishing.md` for the full requirements matrix.

**`homey app review` fails with a missing-key error.**
Set `OPENAI_API_KEY` (for OpenAI models) or `ANTHROPIC_API_KEY` (for Anthropic models) in your shell
before running the command.

**Reset the CLI to a clean state.**
Remove `~/.homey/` to clear all sessions, cached Homeys and the current selection.

**`ENOENT: no such file or directory, open 'app.json'` on a fresh Compose-only checkout.**
*(Field-tested, not in the official docs.)* Homey Compose reads the root `/app.json` **first** and
only then overlays `.homeycompose/app.json`, so a missing `/app.json` breaks `homey app build`,
`run`, `validate` and `publish` alike — building does **not** bootstrap it. Fix by committing the
generated `app.json` (which is what `homey app create` produces), or by dropping a placeholder
`app.json` containing `{}` in the app root before the first Compose run; the next run replaces it
with the real generated manifest. Never hand-edit the generated file afterwards.

**A port the app opens is unreachable while `homey app run` is active.**
Default Docker networking is `bridge`. Use `--network host`, or `homey app install` to test with
production networking.

---

## 11. Live debugging & logging

* `homey app run` streams the app's console output to your terminal while it runs; `Ctrl+C`
  terminates it **and uninstalls the app** from Homey.
* Log with **`this.log()` / `this.error()`** on `Homey.App`, `Homey.Driver` and `Homey.Device` — never
  `console.log`. These are prefixed and routed into Homey's log stream.
* Attach `.catch(this.error)` to every fire-and-forget promise (for example `setCapabilityValue()`,
  which returns a promise). On **Homey Cloud** an unhandled promise rejection crashes the app; on
  every platform it can cause memory leaks and signals that the app is not handling errors properly.
* Use `this.homey.setTimeout` / `setInterval` / `clearTimeout` / `clearInterval` instead of the
  globals — they are cleared automatically when the app is destroyed, so a crashed/reloaded dev
  session does not leak timers.

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    this.log('MyApp has been initialized');

    this.pollInterval = this.homey.setInterval(() => {
      this.poll().catch(this.error);
    }, 30_000);
  }

  async poll() {
    const res = await fetch('https://api.example.com/state');
    if (!res.ok) throw new Error(`Unexpected status ${res.status}`);

    const data = await res.json();
    this.log('Polled state:', data);
  }

  async onUninit() {
    this.homey.clearInterval(this.pollInterval);
  }

}

module.exports = MyApp;
```

**Debug loop cheatsheet**

| Situation | Command |
| --------- | ------- |
| Iterate on code, watch logs | `homey app run` |
| Re-test pairing from scratch | `homey app run --clean` |
| App must be reachable on the LAN | `homey app run --network host` or `homey app install` |
| Long-running/background test, no terminal attached | `homey app install` |
| Local dependency under development | `homey app run --link-modules ../my-lib` |
| CLI cannot find/reach the Homey | `homey api diagnose` |
| Poke Homey's own API while debugging | `homey api raw --path /api/manager/system/` |

Widgets and custom views run in a **webview** in the mobile app and are debugged with the Chrome
inspector (Android, `chrome://inspect/#devices`) or the Safari Web Inspector (iOS) — see
`references/widgets.md`. Zigbee wire-level debug logging is enabled with `debug(true)` from
`zigbee-clusters` — see the Zigbee reference.

---

## 12. Homey Developer Tools (`tools.developer.homey.app`)

The Developer Portal complements the CLI. `homey tools` opens the portal; `homey app manage` opens
the current app's page.

| URL | Purpose |
| --- | ------- |
| `https://tools.developer.homey.app` | Portal home. |
| `https://tools.developer.homey.app/apps/app/<app-id>` | Your app's dashboard (opened by `homey app manage`). |
| *Apps SDK* → *My Apps* | Manage Draft / Test / Live releases and submit for certification. |
| `https://tools.developer.homey.app/tools/ble` | **Bluetooth LE Devtools** — list all advertisements near Homey sorted by RSSI, connect to a peripheral, discover services/characteristics/descriptors, read/write, update RSSI. |
| `https://tools.developer.homey.app/tools/zigbee` | **Zigbee Devtools** — nodes table (Node ID, IEEE Address, Network Address, Type, Online, Receive When Idle, Manufacturer, Model ID, Route), node *Interview* (endpoint descriptors, clusters, commands, attributes as JSON), *Refresh Nodes*, and Zigbee chip system information. |
| `https://homey.app/a/<app-id>` | Public App Store page (opened by `homey app view`). |

### 12.1 Bluetooth LE Devtools

The tool follows the BLE hierarchy: **All Advertisements → Peripheral → Service → Characteristic →
Descriptor**.

* **Advertisements** — every device Homey detects, sorted on signal strength (`RSSI`). A *Discover
  devices* button at the top of the column re-scans. Clicking an advertisement opens the peripheral.
* **Peripheral** — connect/disconnect (some devices cannot be connected to at all, e.g. when all
  data is already in the advertisement). Once connected you can discover services and
  characteristics and update the RSSI. *"Discover Services"* and *"Discover Services &
  Characteristics"* start out identical; the latter saves time in the service column.
* **Services** — each service is a collection of one or more characteristics, which must be
  discovered before details are shown.
* **Characteristics** — read and/or write per characteristic; read data is rendered in multiple
  formats. Writes are entered as a decimal buffer (e.g. `[255, 0, 0]`).
* **BLE Notifications** — you can subscribe to notifications and watch a live feed of everything the
  device sends. The buttons are disabled when the device does not support notifications.
* **Descriptors** — not always present; provide extra information about their characteristic (a user
  description, subscription status). Reading the *Characteristic User Description* descriptor is
  often the quickest way to learn what a characteristic's raw values mean.

### 12.2 Zigbee Devtools

Two sections: the **nodes table** on top and **system information** below.

Nodes-table columns: *Node ID* (arbitrary row identifier), *IEEE Address* (the device's unique
identifier), *Network Address*, *Type* (`Router` = mains-powered repeater, `EndDevice` = mostly
sleeping battery device), *Online* (refreshed by the refresh button; whether the node answers a
ping), *Receive When Idle* (only routers can), *Manufacturer*, *Model ID*, and *Route* (the last
known route used, often not the shortest path — the Zigbee protocol, not Homey, decides routing).

* **Interview** — lists the endpoints, clusters, commands and attributes a node supports; the node
  must be online and EndDevices are slow. The resulting JSON contains `modelId` and
  `manufacturerName` for the driver manifest, `endpointDescriptors` (all endpoints and their
  clusters), and `endpoints` (per-cluster commands, attributes and attribute reporting config).
* **Refresh Nodes** — pings all router nodes to update *Online*. Takes a while and briefly loads the
  network heavily.

System information: *Channel* (also a selector), *Pan ID*, *Extended PAN ID*, *IEEE Address* (of
Homey), *Network Key*, *Network Address* (always `0` — Homey is the coordinator), *Current Command*.

> **Changing the channel is drastic.** All Zigbee routers must be online so they receive the switch
> message, it can take up to 10 minutes, and some devices may still need to be re-paired afterwards.

The nodes table's *Manufacturer* column is the `manufacturerName` and *Model ID* is the `productId`
you put in a driver manifest; the interview output gives you the same values as `manufacturerName` /
`modelId` in JSON.

---

## 13. TypeScript

TypeScript **transpiles** to JavaScript: the CLI invokes the TypeScript compiler as an extra build
step, compiling into `.homeybuild/` in the app root, after which Homey bundles all JavaScript files
into one app.

### 13.1 New app

Run `homey app create` and answer **Yes** when the CLI asks to initialize the app with TypeScript
utilities. All necessary and recommended dependencies and files are created for you.

### 13.2 Converting an existing JavaScript app

Conversion is manual, but can be done **file by file** — TypeScript and JavaScript files coexist.

**1. Add `tsconfig.json` to the app root.** This is what makes Homey recognise the app as a
TypeScript app. Configure it freely, with two constraints: `outDir` must remain `.homeybuild/`, and
`sourceMap: true` is strongly recommended.

> **Doc contradiction:** the prose of the official TypeScript guide twice calls this file
> `.tsconfig.json` (leading dot), but its own code-block title says `/tsconfig.json` and the
> driver-generation rule keys off `tsconfig.json`. Use **`tsconfig.json`** — the dotted name is a
> documentation typo.

```json
{
  "extends": "@tsconfig/node12/tsconfig.json",
  "compilerOptions": {
    "outDir": ".homeybuild/",
    "sourceMap": true
  }
}
```

**2. Install dependencies.**

```bash
homey app add-types
```

**3. Change the app entrypoint.** The guide says to rename `app.js` → `app.ts` (CLI-scaffolded
TypeScript apps use `app.mts` instead — see §13.3) and add source-map support at the top. You can
remove `'use strict'`:

```typescript
import sourceMapSupport from 'source-map-support';
sourceMapSupport.install();
```

**4. Add the build step** to `package.json`:

```json
{
  "scripts": {
    "build": "tsc"
  }
}
```

**5. Run it.** `homey app run` prints `Compiling TypeScript...` before starting the app if everything
is wired up correctly.

### 13.3 File extensions

| Runtime | App | Driver / Device | Web API | Build |
| ------- | --- | --------------- | ------- | ----- |
| JavaScript (CJS) | `app.js` | `driver.js`, `device.js` | `api.js` | — |
| JavaScript (ESM) | `app.mjs` | `driver.mjs`, `device.mjs` | `api.mjs` | — |
| TypeScript | `app.mts` | `driver.mts`, `device.mts` | `api.mts` | `tsc` with `outDir: .homeybuild/` |

The current documented project layout uses the **`.mts`** extension for TypeScript sources (ESM
TypeScript). The older conversion guide describes renaming `app.js` → `app.ts`; both compile through
the same `tsc` step, but new apps scaffolded by the CLI use `.mts`.

### 13.4 Gotchas

* **`tsconfig.json` is the TypeScript switch.** When it is present in the app root, `homey app driver
  create` generates TypeScript drivers. Remove or rename it to get JavaScript drivers back — but
  removing/renaming it **also stops the TypeScript compiler from being invoked** when
  running/installing/publishing the app.
* **`outDir` must stay `.homeybuild/`.** Any other output directory breaks the build; Homey bundles
  from `.homeybuild/`.
* **Keep `sourceMap: true`** and install `source-map-support` in the entrypoint, otherwise runtime
  stack traces point at compiled JavaScript instead of your sources.
* **The `@tsconfig/node12` base in the official example is stale** — Homey apps run on Node.js 22
  (Homey v12.9.0+). Pick a base matching the runtime you target.
* `.homeybuild/` belongs in `.gitignore` (the scaffold does this).

---

## 14. ESM (ECMAScript Modules)

Supported since **Homey v12.0.1**. Bump the manifest `compatibility` to `>=12.0.1` when you use it.

### 14.1 CJS vs ESM

```javascript
// CommonJS
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {
  async onInit() {
    this.log('MyApp has been initialized');
  }
}

module.exports = MyApp;
```

```javascript
// ESM
import Homey from 'homey';

class MyApp extends Homey.App {
  async onInit() {
    this.log('MyApp has been initialized');
  }
}

export default MyApp;
```

### 14.2 Opting in

There is currently **one** way to opt into ESM: **use the `.mjs` extension.** Rename your JavaScript
files to `.mjs` — this tells Node.js to treat them as ESM modules. You can migrate file by file;
files still using CommonJS keep `require()` / `module.exports` and coexist with the ESM parts.

### 14.3 Migration checklist

1. Replace `require()` with `import`:
   ```javascript
   const Homey = require('homey');  // Before
   import Homey from 'homey';       // After
   ```
2. Replace `module.exports` with `export`:
   ```javascript
   module.exports = MyApp;  // Before
   export default MyApp;    // After
   ```
3. Check that any third-party modules you use also support ESM.
4. Upgrade your app's `compatibility` to **`>=12.0.1`** in the manifest.

### 14.4 Gotchas

* **No `require()` in ESM.** Load a CommonJS module with dynamic `import()`:
  ```javascript
  const cjsModule = await import('cjs-module');
  ```
* **No `__dirname` / `__filename` in ESM.** Derive them:
  ```javascript
  import { dirname } from 'path';
  import { fileURLToPath } from 'url';

  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);
  ```
* **Mixing ESM and CJS is risky.** ESM loads asynchronously, CJS synchronously — some patterns behave
  differently.
* ESM modules are always in **strict mode**, so `'use strict'` is unnecessary (and `this` at module
  scope is `undefined`).

### 14.5 Why ESM

Asynchronous module loading; alignment with modern JavaScript syntax; cleaner structure and named
exports; better static analysis (autocomplete, refactoring, error checking); native browser support
for shared code; strict mode by default; **top-level `await`**; future-proofing.

---

## 15. `.homeyignore`

`/.homeyignore` in the app root prevents files or folders from being included in the app when
publishing. It works the same way as `.gitignore`. **By default every file in the app directory is
included** — use `.homeyignore` for documentation, design files and images you want in version
control but not in the shipped bundle.

```
comments.txt
docs/*
```

Related: `/env.json` holds runtime secrets and ships **inside** the app bundle (so it is not a
security boundary), while `.gitignore` — not `.homeyignore` — is what keeps it out of version
control.

---

## 16. Runtime versions (summary)

| Runtime | Version on Homey |
| ------- | ---------------- |
| Node.js | **v22** on all platforms as of Homey v12.9.0. Homey Cloud apps move to Node 22 only after publishing a new version after 2 December 2025. |
| Python | Latest full release, currently **3.14**. |
| Homey CLI (your machine) | **Node.js v24+**. |

Earlier Node versions per platform, the Node 22 known issues (`node-fetch` `ECONNRESET`, the Node 20
`Host`-header requirement, `node-homey-api` < 3.14.17 stack overflow) and the SDK v2 → v3 migration
live in `references/migration-and-breaking-changes.md`.

---

## Sources

* <https://apps.developer.homey.app/the-basics/getting-started>
* <https://apps.developer.homey.app/the-basics/getting-started/homey-cli>
* <https://apps.developer.homey.app/guides/tools>
* <https://apps.developer.homey.app/guides/tools/typescript>
* <https://apps.developer.homey.app/guides/tools/bluetooth>
* <https://apps.developer.homey.app/guides/tools/zigbee>
* <https://apps.developer.homey.app/guides/using-esm-in-homey-apps>
* <https://apps.developer.homey.app/the-basics/app>
* <https://apps.developer.homey.app/the-basics/widgets/debugging>
* <https://apps.developer.homey.app/app-store/publishing>
* <https://apps.developer.homey.app/upgrade-guides/node-22>
