# Flow Cards, Arguments & Tokens

Flow is Homey's automation engine: a Flow is a series of Flow cards in three columns — *when* (triggers), *…and…* (conditions), *…then* (actions). An app exposes cards by declaring them in the App Manifest and registering listeners with `this.homey.flow.*` in SDK v3.

Related: `references/app-and-manifest.md` (compose/manifest mechanics, locales), `references/drivers-and-devices.md` (Driver/Device classes), `references/capabilities.md` (system cards, `duration`, `preventTag`), `references/advanced-features.md` (`Image`, image tokens, clock/timezone).

## 1. The three card types

| Column | Card type | Manifest section | Getter | Class | Listener must return |
|---|---|---|---|---|---|
| *when…* | trigger | `flow.triggers` | `this.homey.flow.getTriggerCard(id)` | `FlowCardTrigger` | `true`/`false` (only needed when the card has arguments — the "state match") |
| *when…* (device-scoped) | trigger | `flow.triggers` | `this.homey.flow.getDeviceTriggerCard(id)` | `FlowCardTriggerDevice` | same |
| *…and…* | condition | `flow.conditions` | `this.homey.flow.getConditionCard(id)` | `FlowCardCondition` | `true` → Flow continues, `false` → Flow stops, throw/reject → Flow stops |
| *…then* | action | `flow.actions` | `this.homey.flow.getActionCard(id)` | `FlowCardAction` | nothing, or an object of Advanced-Flow tokens |

All four classes extend `FlowCard`.

> Often it is not necessary to define your own Flow cards: most device classes and capabilities automatically add their own Flow cards. Check `references/capabilities.md` before inventing a card.

## 2. Where Flow cards live

`app.json` in the project root is **generated** — never hand-edit it. Author cards in Homey Compose files.

```
com.athom.example/
├─ .homeycompose/
│  ├─ flow/
│  │  ├─ triggers/<id>.json        # app-level trigger; card id = filename
│  │  ├─ conditions/<id>.json      # app-level condition
│  │  └─ actions/<id>.json         # app-level action
│  └─ drivers/
│     └─ flow/
│        ├─ triggers/<id>.json     # driver card templates, shared via $extends
│        ├─ conditions/<id>.json
│        └─ actions/<id>.json
└─ drivers/<driver_id>/
   └─ driver.flow.compose.json     # cards scoped to this driver only
```

| Location | Scope | `id` comes from | Shape |
|---|---|---|---|
| `.homeycompose/flow/<type>/<id>.json` | whole app | the filename (override with `$id`) | a single card object |
| `.homeycompose/drivers/flow/<type>/<id>.json` | template pulled into `driver.flow.compose.json` via `$extends` | the filename or `$id` | a single card object |
| `drivers/<driver_id>/driver.flow.compose.json` | that driver's devices only | the explicit `"id"` key | `{ "triggers": [], "conditions": [], "actions": [] }` |
| generated `app.json` → `"flow": { "triggers": [], "conditions": [], "actions": [] }` | — | explicit `"id"` | arrays; produced by compose |

CLI generators (preferred over hand-writing — they emit the current schema):

```bash
homey app flow create     # interactive: app-level card → .homeycompose/flow/<type>/<id>.json
homey app driver flow     # interactive: driver-scoped card → drivers/<id>/driver.flow.compose.json
```

## 3. Card manifest schema

**Required properties** (`flowCard` definition in the app.json schema): exactly `id` and `title`. Everything else is optional. In `.homeycompose/flow/**` the `id` is filled in by Compose from the filename, so you only write `title` — but the *generated* `app.json` must have both, and `homey app validate` fails on a card missing either.

| Key | Type | Card types | Description |
|---|---|---|---|
| `id` | `string` | all (**required**) | Referenced from source code. Implicit (filename) in `.homeycompose/flow/**`; explicit in `driver.flow.compose.json` and `app.json`. |
| `title` | translation object | all (**required**) | Shown to the user. Short and clear. Supports the `!{{…\|…}}` inversion syntax on conditions. |
| `titleFormatted` | translation object | all | Title with `[[argName]]` placeholders so argument values appear inline. Required in practice for any card with arguments — see §4. |
| `hint` | translation object | all | Extra explanation that does not fit in the title. Not declared in the schema — see the note below. |
| `args` | `array` | all | Argument definitions — see §6. |
| `tokens` | `array` | triggers, actions | Local tokens the card emits — see §7. On a **then**-card this implies `"advanced": true`. |
| `droptoken` | `"string"\|"number"\|"boolean"\|"image"`, or an `array` of those | all | A single token-only input. See §6.13. |
| `duration` | `boolean` | actions only | Lets the user pick a duration; delivered as `args.duration` in **milliseconds**. Not declared in the schema — see the note below. |
| `deprecated` | `true` only | all | Card keeps working in existing Flows but disappears from the 'Add Card' list. |
| `advanced` | `true` only | all | Card is only offered in Advanced Flow. |
| `highlight` | `true` only | all | Card appears in the "Highlighted Cards" list above all other cards. |
| `platforms` | `array` of `"local"\|"cloud"` (unique) | all | Required per-card when the app targets Homey Cloud. |
| `$filter` | `string` or `object` | `driver.flow.compose.json` cards | Restrict which devices the card shows up for — see §5.2. |
| `$deviceName` | `string` | `driver.flow.compose.json` cards | Rename the auto-inserted `device` argument (default `device`). Compose-only; see `references/app-and-manifest.md`. |
| `$id` | `string` | `.homeycompose/flow/**` files | Override the id derived from the filename. |
| `$extends` | `string`/`array` | driver flow cards | Merge one or more `.homeycompose/drivers/flow/**` templates. |

The `$`-prefixed keys are Homey Compose directives; Compose consumes them and they never reach `app.json`, so they are (correctly) absent from the schema.

**Schema notes** (from the `flowCard` definition — these outrank the prose docs):

* `deprecated`, `advanced` and `highlight` are declared as `"type": "boolean", "enum": [true]`. Only the literal `true` validates — writing `"deprecated": false` is a **validation error**, not a no-op. Omit the key instead.
* `platforms` is a `uniqueItems` array; a duplicate entry (`["local", "local"]`) fails validation.
* **Discrepancy — `hint` and `duration` are not declared in the schema.** The prose documentation documents both, published Athom apps ship both, and they validate fine because the `flowCard` definition does *not* set `additionalProperties: false` (the generated types end each object with `[k: string]: unknown`). So they are safe to use, but the schema neither type-checks nor restricts them: nothing stops you from putting `"duration": true` on a trigger or condition card, where it does nothing.
* The same permissiveness applies to argument objects: undeclared keys such as `required` (§6.12) pass validation. See §6 for which keys the schema actually declares per type.

### 3.1 Minimal cards

```json
// /.homeycompose/flow/triggers/rain_start.json
{
  "title": { "en": "It starts raining" },
  "hint": { "en": "When it starts raining more than 0.1 mm/h." }
}
```

```json
// /.homeycompose/flow/conditions/is_raining.json
{
  "title": { "en": "It !{{is|isn't}} raining" },
  "hint": { "en": "Checks if it is currently raining more than 0.1 mm/h." }
}
```

```json
// /.homeycompose/flow/actions/stop_raining.json
{
  "title": { "en": "Make it stop raining." }
}
```

### 3.2 A fully-loaded card

```json
// /.homeycompose/flow/conditions/raining_in.json
{
  "title": { "en": "It !{{is|isn't}} going to rain in..." },
  "titleFormatted": { "en": "It !{{is|isn't}} going to rain in [[when]]" },
  "hint": { "en": "Checks if it will/will not rain more than 0.1 mm/h within the given amount of time." },
  "highlight": true,
  "platforms": ["local", "cloud"],
  "args": [
    {
      "name": "when",
      "type": "dropdown",
      "title": { "en": "When it will rain" },
      "values": [
        { "id": "5", "title": { "en": "5 minutes" } },
        { "id": "10", "title": { "en": "10 minutes" } },
        { "id": "15", "title": { "en": "15 minutes" } }
      ]
    }
  ]
}
```

### 3.3 Highlighted cards

`"highlight": true` puts the card in a separate "Highlighted Cards" list shown *above* all other cards, so users can find the important cards of an app that exposes many. Some built-in Flow cards are always highlighted, for example "Motion alarm turned on".

## 4. Titles: `titleFormatted` and inversion

**Placeholders.** `titleFormatted` embeds argument values with `[[argName]]`, where `argName` is the argument's `name`:

```json
{
  "title": { "en": "Button was pressed" },
  "titleFormatted": { "en": "[[buttontype]] button was pressed [[scene]]" }
}
```

A `droptoken` is referenced in `titleFormatted` as `[[droptoken]]`.

**What `homey app validate` enforces on `titleFormatted`** (rules implemented in `homey-lib`, not spelled out in the prose docs):

* As soon as a card has at least one argument (other than the Compose-inserted device argument), a missing `titleFormatted` is a **warning** at `--level publish` and a hard **error** at `--level verified`.
* Every one of those arguments must appear in `titleFormatted` **exactly once**. Omitting one → `Missing [[argName]]`; a placeholder that matches no argument → `Invalid [[argName]]`; the same placeholder twice → `Duplicate [[argName]]`. Each language of the translation object is checked separately.
* A card-level `droptoken` counts as an argument named `droptoken`, so `[[droptoken]]` is mandatory too once the card has any other argument.
* The **first** `device` argument whose `filter` contains `driver_id` (or the alias `driverId` — the validator parses the filter as a querystring and accepts either key) — the one Compose inserts into `driver.flow.compose.json` cards — is excluded from this check. Do not write `[[device]]` for it.
* At `--level verified` every argument additionally needs its own `title`.
* Two cards of the same type may not share an `id` (error on SDK v3, warning on older SDKs).

**Inversion.** Condition titles support `!{{a|b}}`: the text before the pipe is shown for the normal card, the text after it for the inverted card. `"It !{{is|isn't}} raining"` renders as *It is raining* / *It isn't raining*. This works in `title` and in `titleFormatted`.

**App Store review rules for titles** (Athom's human review, not the validator):

| Column | Do | Don't |
|---|---|---|
| When | `Unknown face is detected` | `Netatmo Presence detected an unknown face.` |
| And | `Is !{{on\|off}}` | `And the light is off` |
| Then | `Lock door` | `Going to lock the door` |

* Do not mention the device name in the title.
* Do not repeat the When/And/Then statement in the title.
* Do not use parentheses in Flow titles.
* Keep the title readable *after* the arguments are substituted.
* Use `hint` when the function is not obvious: `"hint": { "en": "This card starts a Flow when a change in the battery state is observed." }`.

**Gotcha — the App Store guidelines page spells the property `titleFormated` (one `t`) in prose.** The correct manifest key is `titleFormatted`, as used everywhere in the Flow documentation and in every code sample.

## 5. Device cards

Device cards belong to a specific device rather than to the app, and are defined in `/drivers/<driver_id>/driver.flow.compose.json`. If your driver's `class` is one Homey already supports (`light`, `socket`, …), your custom cards are appended to the built-in stack ("Turn on", "Turn off", "Dim", "Set color", **"Disco mode"**).

```json
// /drivers/<driver_id>/driver.flow.compose.json
{
  "triggers": [
    {
      "id": "turned_on",
      "title": { "en": "Turned on" }
    }
  ],
  "conditions": [],
  "actions": [
    {
      "id": "disco_mode",
      "title": { "en": "Disco mode" }
    }
  ]
}
```

Compose automatically inserts the `device` argument with `driver_id=<driver_id>` as the first argument of every card in this file; do not write it yourself (rename it with `$deviceName` if `device` clashes with another argument name).

### 5.1 Device trigger cards

A trigger that must only start Flows for **one** device requires `getDeviceTriggerCard()` — not `getTriggerCard()` — so that `trigger()` accepts the `device` as its first parameter.

```javascript
// /drivers/<driver_id>/driver.js
'use strict';

const Homey = require('homey');

class Driver extends Homey.Driver {
  async onInit() {
    this._deviceTurnedOn = this.homey.flow.getDeviceTriggerCard('turned_on');
  }

  triggerMyFlow(device, tokens, state) {
    this._deviceTurnedOn
      .trigger(device, tokens, state)
      .then(this.log)
      .catch(this.error);
  }
}

module.exports = Driver;
```

```javascript
// /drivers/<driver_id>/device.js
'use strict';

const Homey = require('homey');

class Device extends Homey.Device {
  async onInit() {
    const device = this; // We're in a Device instance
    const tokens = {};
    const state = {};

    this.driver.ready()
      .then(() => this.driver.triggerMyFlow(device, tokens, state))
      .catch(this.error);
  }
}

module.exports = Device;
```

`FlowCardTriggerDevice#getArgumentValues(device)` returns the argument values for one specific device; the same method on `FlowCardTrigger` / `FlowCardCondition` / `FlowCardAction` takes no arguments and returns the values for every Flow card instance.

### 5.2 `$filter` — restricting which devices show the card

`$filter` on a card in `driver.flow.compose.json` supports three properties:

| Property | Matches on |
|---|---|
| `class` | the device class |
| `capabilities` | available capabilities — **note: `addCapability()` / `removeCapability()` do not update this filter** |
| `flags` | additional device properties (see the wireless flags below) |

Syntax:

* `|` = OR between values of one property → `"class=socket|light"`
* `,` = AND between values (for `capabilities` and `flags`) → `"capabilities=onoff,dim"`
* `&` = combine properties → `"class=socket|light&capabilities=onoff,dim"`

```json
{
  "actions": [
    {
      "id": "disco_mode",
      "title": { "en": "Disco mode" },
      "$filter": "class=socket"
    }
  ]
}
```

Wireless-specific flags:

| Filter | Effect |
|---|---|
| `"$filter": "flags=zwaveMultiChannel"` | Z-Wave: target only multi channel node devices |
| `"$filter": "flags=zwaveRoot"` | Z-Wave: target only root node devices |
| `"$filter": "flags=zigbeeSubDevice"` | Zigbee: target only sub devices |

### 5.3 App-level cards that take a device

An app-level card can also address devices, by declaring a `device` argument with a `filter` (see §6.11). The card then shows up under the matching devices; `args.<name>` is the `Device` instance in the run listener.

## 6. Argument reference

Arguments are the user's input to a card. Declared in the card's `args` array; each has a `name` (the key in `args` in the run listener) and a `type`.

> Don't overuse arguments. Flow cards with just one or two arguments are the most popular.

**Attributes available on every argument**

| Name | Type | Description |
|---|---|---|
| `name` | `string` (**required**) | Key used in `args` and in `[[…]]` placeholders. |
| `type` | `string` (**required**) | One of the types below. |
| `title` | translation object | Text shown above the argument. Optional to the schema; **required at `--level verified`** for every argument except the Compose-inserted device argument. |
| `required` | `boolean` | Default `true`. Set `false` to make it optional. Not declared in the schema (see §3), but accepted and honoured at runtime. |

`name` and `type` are the only two keys the schema requires on every argument. Three types require more: `dropdown` also requires `values`; `multiselect` requires `values` **and** `conjunction`; a `device` argument matched against the schema's device-specific branch also requires `filter` (see §6.11).

**Complete list of argument types the schema accepts**: `text`, `autocomplete`, `number`, `range`, `date`, `time`, `dropdown`, `multiselect`, `checkbox`, `color`, `device`, `code`. Anything else is a validation error. `droptoken` is a **card-level** property, not an `args` entry.

**Discrepancy — `code` is schema-only.** The `flowCard` schema lists `code` alongside `text`/`autocomplete`/`date`/`time`/`color`/`checkbox`/`device`, but the Arguments documentation page does not mention it and no published Athom app uses it. Treat it as an undocumented/internal type: it validates, but its front-end behaviour is unspecified. Prefer `text`.

**Attributes the schema declares per type** (authoritative; the schema groups the types into five branches):

| Type(s) | Declared attributes (beyond `name`/`type`) | Required beyond `name`/`type` |
|---|---|---|
| `text`, `autocomplete`, `date`, `time`, `color`, `checkbox`, `code`, `device` | `title`, `placeholder`, `filter`, `items` | — |
| `device` (device-specific branch) | `filter` | `filter` |
| `number`, `range` | `title`, `min`, `max`, `step` (≥ 0), `label`, `labelMultiplier`, `labelDecimals` (≤ 10) | — |
| `dropdown` | `title`, `values[]` — each value `{ id (required), title }` | `values` |
| `multiselect` | `title`, `conjunction` (`"and"`\|`"or"`), `values[]` — each value `{ id, title }`, **both required** | `values`, `conjunction` |

Consequences worth knowing:

* `label`, `labelMultiplier` and `labelDecimals` are declared for **`number` as well as `range`**, not just `range` as §6.4 might suggest.
* `placeholder` is **not** declared for `number` and `range` — yet the official docs' `number` example uses it and published apps ship it. It validates only because the schema does not forbid extra keys (§3). It is not an error, just undeclared.
* `filter` and `items` are declared for `text`, `autocomplete`, `date`, `time`, `color`, `checkbox` and `code` too, not only for `device` — the schema simply groups those types together. `filter` is only meaningful on `device`.
* `items` accepts exactly `"variable"`, `"flow_or_advanced_flow"` or `"user"`. It appears nowhere in the prose documentation or in any published app; assume it is internal to Homey's own apps and do not use it.
* `min`/`max`/`step` are declared **only** for `number` and `range`. Putting `min` on a `text` argument is undeclared and has no effect.

### 6.1 `text`

Regular text input. Text, Number and Boolean tokens can be dropped in this field as well.

| Name | Type | Description | Example |
|---|---|---|---|
| `placeholder` | translation object | Text to show without input | `{ "en": "Hello, World!", "nl": "Hallo, Wereld!" }` |
| `title` | translation object | Text shown above argument | `{ "en": "Sentence", "nl": "Zin" }` |

```json
// /.homeycompose/flow/actions/greet.json
{
  "title": { "en": "Say a greeting" },
  "titleFormatted": { "en": "Say [[sentence]]" },
  "args": [
    {
      "type": "text",
      "name": "sentence",
      "title": { "en": "Sentence" },
      "placeholder": { "en": "Hello!" }
    }
  ]
}
```

### 6.2 `autocomplete`

Same as a text input, but with an autocomplete popup. The value delivered to the run listener is **one of the objects returned by the autocomplete listener** — not a plain string. Requires `FlowCard#registerArgumentAutocompleteListener()`.

| Name | Type | Description | Example |
|---|---|---|---|
| `placeholder` | translation object | Text to show without input | `{ "en": "YouTube", "nl": "Dumpert" }` |
| `title` | translation object | Text shown above argument | `{ "en": "Application", "nl": "Applicatie" }` |

```json
// /.homeycompose/flow/actions/play_artist.json
{
  "title": { "en": "Play an Artist" },
  "titleFormatted": { "en": "Play an Artist [[artist]]" },
  "args": [
    {
      "type": "autocomplete",
      "name": "artist",
      "title": { "en": "Artist" },
      "placeholder": { "en": "Ludwig van Beethoven" }
    }
  ]
}
```

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const playArtistCard = this.homey.flow.getActionCard('play_artist');

    playArtistCard.registerArgumentAutocompleteListener('artist', async (query, args) => {
      const results = [
        {
          name: 'Wolfgang Amadeus Mozart',
          description: 'Joannes Chrysostomus Wolfgangus Theophilus Mozart',
          icon: 'https://path.to/icon.svg',
          // For images that are not svg use:
          // image: 'https://path.to/icon.png',

          // You can freely add additional properties
          // that you can access in registerRunListener
          id: '...',
        },
      ];

      // filter based on the query
      return results.filter((result) => {
        return result.name.toLowerCase().includes(query.toLowerCase());
      });
    });

    playArtistCard.registerRunListener(async (args, state) => {
      // args.artist is the whole result object, incl. the extra `id`
      await this.musicApi.play(args.artist.id);
    });
  }
}

module.exports = App;
```

**Autocomplete result object** (`FlowCard.ArgumentAutocompleteResults`)

| Property | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | yes | Displayed value; also what you filter on. |
| `description` | `string` | no | Second line under the name. |
| `icon` | `string` | no | URL/path to an **SVG**. |
| `image` | `string` | no | URL/path for non-SVG images (PNG, …). |
| *(any extra key)* | any | no | Freely added; delivered untouched to `registerRunListener`. |

`ArgumentAutocompleteCallback(query, args)` → `Promise<ArgumentAutocompleteResults> | ArgumentAutocompleteResults`. `query` is the typed query; `args` is the current state of the card's arguments as selected by the user in the front-end (useful to scope results to an already-picked device).

**Gotcha — you must filter on `query` yourself.** Homey does not filter for you. If you return an unfiltered list the autocomplete appears unresponsive. The easiest correct filter is a lowercase `includes` on `name`.

### 6.3 `number`

Regular text input, numeric. Tokens can be dropped in this field as well.

| Name | Type | Description | Example |
|---|---|---|---|
| `min` | `number` | Minimum input value | `40` |
| `max` | `number` | Maximum input value | `90` |
| `step` | `number` (≥ 0) | Step size | `10` |
| `label` | translation object (a plain `string` is also valid) | The units after the number | `°C` |
| `labelMultiplier` | `number` | Number is shown after multiplying by this factor | `1` |
| `labelDecimals` | `number` (≤ 10) | Number of decimals to round to | `1` |
| `placeholder` | translation object | Text to show without input. **Not declared in the schema for `number`/`range`** — accepted because extra keys are allowed (§3), and used by the official example below. | `{ "en": "In degree celsius", "nl": "In graden celsius" }` |
| `title` | translation object | Text shown above argument | `{ "en": "Temperature", "nl": "Temperatuur" }` |

`label`, `labelMultiplier` and `labelDecimals` work on `number` exactly as they do on `range` (§6.4) — the schema declares one attribute set for both types.

```json
// /.homeycompose/flow/actions/wash_clothes.json
{
  "title": { "en": "Wash clothes" },
  "titleFormatted": { "en": "Wash clothes at [[temperature]] degrees celsius" },
  "args": [
    {
      "type": "number",
      "name": "temperature",
      "title": { "en": "Temperature" },
      "placeholder": { "en": "In degree celsius" },
      "min": 40,
      "max": 90,
      "step": 10
    }
  ]
}
```

### 6.4 `range`

A slider with a minimum and maximum value.

| Name | Type | Description | Example |
|---|---|---|---|
| `min` | `number` | Minimum input value | `0` |
| `max` | `number` | Maximum input value | `1` |
| `step` | `number` (≥ 0) | Step size | `0.01` |
| `label` | `string` (a translation object is also accepted) | The units after the number | `%` |
| `labelMultiplier` | `number` | Number is shown after multiplying by this factor | `100` |
| `labelDecimals` | `number` (≤ 10) | Number of decimals to round to | `2` |
| `title` | translation object | Text shown above argument | `{ "en": "Brightness", "nl": "Helderheid" }` |

```json
// /.homeycompose/flow/actions/set_brightness.json
{
  "title": { "en": "Set brightness" },
  "titleFormatted": { "en": "Set brightness to [[brightness]]" },
  "args": [
    {
      "type": "range",
      "name": "brightness",
      "title": { "en": "Brightness" },
      "min": 0,
      "max": 1,
      "step": 0.01,
      "label": "%",
      "labelMultiplier": 100,
      "labelDecimals": 2
    }
  ]
}
```

The run listener receives the **raw** value (`0 … 1` here); `labelMultiplier` only affects the displayed label.

### 6.5 `date`

Date input, presented as `dd-mm-yyyy`.

| Name | Type | Description | Example |
|---|---|---|---|
| `placeholder` | translation object | Text to show without input | `{ "en": "When to ..", "nl": "Wanneer te .." }` |
| `title` | translation object | Text shown above argument | `{ "en": "Birthday", "nl": "Verjaardag" }` |

```json
// /.homeycompose/flow/actions/birthday_surprise.json
{
  "title": { "en": "Birthday surprise" },
  "titleFormatted": { "en": "Surprise you on [[birthday]]" },
  "args": [
    {
      "type": "date",
      "name": "birthday",
      "title": { "en": "Birthday" },
      "placeholder": { "en": "18-05-1994" }
    }
  ]
}
```

### 6.6 `time`

Time input, presented as `HH:mm`.

| Name | Type | Description | Example |
|---|---|---|---|
| `placeholder` | translation object | Text to show without input | `{ "en": "When to ..", "nl": "Wanneer te .." }` |
| `title` | translation object | Text shown above argument | `{ "en": "Time", "nl": "Tijd" }` |

```json
// /.homeycompose/flow/actions/activate_alarm.json
{
  "title": { "en": "Activate the alarm" },
  "titleFormatted": { "en": "Activate the alarm at [[activationtime]]" },
  "args": [
    {
      "type": "time",
      "name": "activationtime",
      "title": { "en": "Time" },
      "placeholder": { "en": "13:37" }
    }
  ]
}
```

### 6.7 `dropdown`

A dropdown list with pre-defined values.

| Name | Type | Description | Example |
|---|---|---|---|
| `values` | `array` (**required**) | An array of possible values. Each entry requires `id`; `title` is optional to the schema but always supply it (it is what the user sees). | `[ { "id": "value1", "title": { "en": "Value 1" } } ]` |
| `title` | translation object | Text shown above argument | `{ "en": "My title", "nl": "Mijn titel" }` |

```json
// /.homeycompose/flow/triggers/rain_start.json
{
  "title": { "en": "It is going to rain in..." },
  "titleFormatted": { "en": "It is going to rain in [[when]]" },
  "args": [
    {
      "type": "dropdown",
      "name": "when",
      "title": { "en": "When it will rain" },
      "values": [
        { "id": "5", "title": { "en": "5 minutes" } },
        { "id": "10", "title": { "en": "10 minutes" } },
        { "id": "15", "title": { "en": "15 minutes" } }
      ]
    }
  ]
}
```

The run listener receives the selected **`id`** as a string (`args.when === '10'`).

**Gotcha — `title` vs `label` inside `values`.** The Arguments documentation consistently uses `{ "id": …, "title": { … } }`, and the locale-override path for value labels is `$flow.<type>.<cardId>.args.<argName>.values.<valueId>.title`. One example on the Flow overview page instead writes `{ "id": "5", "label": { "en": "5 minutes" } }`. **Use `title`.** (`label` *is* a real key, but on a `number`/`range` argument, where it is the unit shown after the number.)

### 6.8 `multiselect`

A multiselect list with pre-defined values.

| Name | Type | Description | Example |
|---|---|---|---|
| `values` | `array` (**required**) | An array of possible values. Unlike `dropdown`, each entry requires **both** `id` and `title`. | `[ { "id": "value1", "title": { "en": "Value 1" } } ]` |
| `title` | translation object | Text shown above argument | `{ "en": "My title", "nl": "Mijn titel" }` |
| `conjunction` | `"and"` \| `"or"` (**required**) | The conjunction of the argument in the preview for users. The app.json schema rejects a `multiselect` without it, and rejects any value other than `and`/`or`. | `or` |

`multiselect` requires the App Manifest's `compatibility` to be at least `>=12.5.0`; `homey app validate` errors out otherwise.

```json
// /.homeycompose/flow/conditions/today_is_a_day.json
{
  "title": { "en": "Today is a" },
  "titleFormatted": { "en": "Today is a [[days]]" },
  "args": [
    {
      "title": { "en": "Day" },
      "name": "days",
      "type": "multiselect",
      "conjunction": "or",
      "values": [
        { "id": "mon", "title": { "en": "Monday" } },
        { "id": "tue", "title": { "en": "Tuesday" } },
        { "id": "wed", "title": { "en": "Wednesday" } },
        { "id": "thu", "title": { "en": "Thursday" } },
        { "id": "fri", "title": { "en": "Friday" } },
        { "id": "sat", "title": { "en": "Saturday" } },
        { "id": "sun", "title": { "en": "Sunday" } }
      ]
    }
  ]
}
```

### 6.9 `checkbox`

A dropdown list with a true and false option that supports boolean tokens.

| Name | Type | Description | Example |
|---|---|---|---|
| `title` | translation object | Text shown above argument | `{ "en": "My title", "nl": "Mijn titel" }` |
| `placeholder` | translation object | Schema-allowed (the schema groups `checkbox` with `text`), but the docs list no use for it on a checkbox. | — |

```json
// /.homeycompose/flow/actions/set_enabled.json
{
  "title": { "en": "Set enabled to..." },
  "titleFormatted": { "en": "Set enabled to [[enabled]]" },
  "args": [
    {
      "type": "checkbox",
      "name": "enabled",
      "title": { "en": "Enabled" }
    }
  ]
}
```

### 6.10 `color`

A color picker that returns a HEX color, e.g. `#FF0000`. No type-specific attributes are documented; the schema puts `color` in the same branch as `text`, so `title`, `placeholder`, `filter` and `items` all validate — only `title` is meaningful.

```json
// /.homeycompose/flow/actions/set_tile_color.json
{
  "title": { "en": "Set tile color" },
  "titleFormatted": { "en": "Set tile color to [[background]]" },
  "args": [
    {
      "type": "color",
      "name": "background"
    }
  ]
}
```

### 6.11 `device`

A device picker. With a `filter` containing `driver_id=…`, the Flow card is only displayed for devices belonging to that driver. If the device already appears because its class is a supported device class (e.g. `light`), your cards are appended to the existing stack of cards.

If a card has **more than one** device field, the additional fields behave like an autocomplete-style argument listing devices paired in your app.

The `filter` uses the same querystring syntax as `$filter` (§5.2), plus `driver_id`. It may also be given as an object instead of a querystring — the schema accepts `string` or `object` — but every documented example and every published app uses the string form.

The schema describes `device` twice: once in a device-specific branch where `filter` is **required**, and once in the shared `text`-style branch where it is optional. Because the two branches are combined with `anyOf`, a `device` argument without a `filter` still validates (it then offers every device in the app — the "second device field" behaviour described above).

```json
// /.homeycompose/flow/actions/my_action.json
{
  "title": {
    "en": "I will show up under all devices with a driver id of mydriver and with the custom capability id mycustomcapability."
  },
  "args": [
    {
      "type": "device",
      "name": "device",
      "title": { "en": "Device" },
      "filter": "driver_id=mydriver&capabilities=mycustomcapability"
    }
  ]
}
```

In the run listener `args.device` is a live `Device` instance — you can call its methods and capability getters directly.

### 6.12 Optional arguments

All arguments are required by default. `"required": false` makes one optional.

**Discrepancy — `required` is not declared in the app.json schema.** It is documented prose, it is honoured at runtime, and it validates only because argument objects allow undeclared keys (§3). The consequence is that the validator will not catch a typo such as `"require": false` — it silently passes and the argument stays mandatory.

```json
// /.homeycompose/flow/actions/post_data.json
{
  "title": { "en": "Post data to URL" },
  "titleFormatted": { "en": "Post [[data]] to [[url]]" },
  "args": [
    {
      "type": "text",
      "name": "url",
      "title": { "en": "URL" },
      "placeholder": { "en": "https://example.com" }
    },
    {
      "type": "text",
      "name": "data",
      "required": false,
      "title": { "en": "Body" },
      "placeholder": { "en": "message" }
    }
  ]
}
```

**Gotcha — an optional argument the user left empty arrives as `undefined`.** Always null-check before use.

### 6.13 `droptoken` (card-level)

A droptoken is a special Flow card argument that only accepts a Flow Token or Homey Logic variable — the user cannot type a literal. It is declared at card level, **not** inside `args`.

* Allowed types: `string`, `number`, `boolean`, `image`.
* A card can have **only one** droptoken, but may allow multiple types: `"droptoken": ["string", "number"]`.
* The value arrives as `args.droptoken`.
* Reference it in `titleFormatted` as `[[droptoken]]`.

```json
// /.homeycompose/flow/conditions/equal.json
{
  "title": { "en": "Is equal" },
  "titleFormatted": { "en": "[[droptoken]] equals [[value]]" },
  "droptoken": ["number"],
  "args": [
    {
      "type": "number",
      "name": "value"
    }
  ]
}
```

**Gotcha — droptokens are possibly `null`.** Verify the droptoken exists before using it:

```javascript
card.registerRunListener(async (args, state) => {
  if (args.droptoken == null) throw new Error('No token provided');
  return args.droptoken === args.value;
});
```

For `"droptoken": ["image"]` the value is an `Image`; consume it with `await args.droptoken.getStream()` — see §7.5 and `references/advanced-features.md`.

### 6.14 Action card `duration`

Only for action cards (the *…then* column). `"duration": true` lets the user pick a duration; it is delivered to the run listener as `args.duration` in **milliseconds**.

```json
// /.homeycompose/flow/actions/run_animation.json
{
  "title": { "en": "Run animation" },
  "titleFormatted": { "en": "Run animation [[animation]]" },
  "duration": true,
  "args": [
    {
      "type": "dropdown",
      "name": "animation",
      "title": { "en": "Animation" },
      "values": [
        { "id": "rainbow", "title": { "en": "Rainbow" } },
        { "id": "kitt", "title": { "en": "KITT" } },
        { "id": "pulse", "title": { "en": "Pulse" } }
      ]
    }
  ]
}
```

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const runAnimationAction = this.homey.flow.getActionCard('run_animation');

    runAnimationAction.registerRunListener(async (args, state) => {
      if (args.duration != null) {
        // do something with the duration
        // (e.g. run an animation for duration milliseconds)
      }
    });
  }
}

module.exports = App;
```

**Gotcha — `"duration": true` has precedence over an argument named `duration`.** Both land on the same handler key. Never define a card with `"duration": true` *and* an argument named `"duration"`.

For built-in capabilities, `duration` is also a capability option; when you enable it there you must additionally set `"duration": true` on the associated action Flow card (see `references/capabilities.md`).

## 7. Registering listeners and triggering

### 7.1 Where to register

**Gotcha — register each Flow card exactly once**, in `App#onInit()` (app-level cards) or `Driver#onInit()` (driver/device cards). Never in `Device#onInit()`: registering per device installs N listeners for one card and produces duplicated Flow executions. `Driver#onInit()` runs before any device exists, which is exactly what you want.

### 7.2 `registerRunListener`

`FlowCard#registerRunListener(listener)` where `listener` is `RunCallback(args, state) → Promise<any>|any`:

* `args` — the card's arguments, keys as defined in `app.json`, values as chosen by the user.
* `state` — the state of the Flow (the object you passed as `state` to `trigger()`).

Register a run listener for **every** condition and action card. For a **trigger** card a run listener is only necessary when the card has one or more arguments (see §7.4).

```javascript
// /app.js
'use strict';

const Homey = require('homey');
const RainApi = require('rain-api');

class App extends Homey.App {
  async onInit() {
    const rainingCondition = this.homey.flow.getConditionCard('is_raining');
    rainingCondition.registerRunListener(async (args, state) => {
      const raining = await RainApi.isItRaining(); // true or false
      return raining;
    });

    const stopRainingAction = this.homey.flow.getActionCard('stop_raining');
    stopRainingAction.registerRunListener(async (args, state) => {
      await RainApi.makeItStopRaining();
    });
  }
}

module.exports = App;
```

Condition semantics: resolve `true` → the Flow continues; resolve `false` → the Flow stops; reject/throw → the Flow stops as well (and the error surfaces to the user).

`registerRunListener` returns the `FlowCard`, so it chains:

```javascript
this._appLaunched = this.homey.flow
  .getDeviceTriggerCard('app_launched')
  .registerRunListener(async (args, state) => args.application.id === state.id);
```

### 7.3 `trigger()`

| Class | Signature |
|---|---|
| `FlowCardTrigger` | `async trigger(tokens?, state?) → Promise<any>` |
| `FlowCardTriggerDevice` | `async trigger(device, tokens?, state?) → Promise<any>` |

`tokens` is an object of the card's declared tokens and their typed values; `state` is an arbitrary object accessible throughout the Flow (and in the trigger's own run listener). The Promise resolves when the Flow is triggered.

```javascript
// /app.js
'use strict';

const Homey = require('homey');
const RainApi = require('rain-api');

class App extends Homey.App {
  async onInit() {
    const rainStartTrigger = this.homey.flow.getTriggerCard('rain_start');

    RainApi.on('raining', (city, amount) => {
      rainStartTrigger
        .trigger({ mm_per_hour: amount }, { location: city })
        .then(this.log)
        .catch(this.error);
    });
  }
}

module.exports = App;
```

**Gotcha — always `.catch(this.error)` on a fire-and-forget `trigger()`.** An unhandled rejection crashes the app process.

### 7.4 Flow State — filtering which Flows run

When a trigger card has arguments, the run listener decides per Flow whether that Flow should run. It is executed once for every Flow that uses the card.

```json
// /.homeycompose/flow/triggers/rain_start.json
{
  "title": { "en": "It starts raining" },
  "tokens": [
    {
      "name": "mm_per_hour",
      "type": "number",
      "title": { "en": "mm/h" },
      "placeholder": { "en": "5" }
    }
  ],
  "args": [
    {
      "name": "location",
      "type": "text"
    }
  ]
}
```

```javascript
// /app.js
'use strict';

const Homey = require('homey');
const RainApi = require('rain-api');

class App extends Homey.App {
  async onInit() {
    const rainStartTrigger = this.homey.flow.getTriggerCard('rain_start');

    rainStartTrigger.registerRunListener(async (args, state) => {
      // args is the user input,      e.g. { location: 'New York' }
      // state is what trigger() got, e.g. { location: 'Amsterdam' }
      return args.location === state.location; // true → this Flow runs
    });

    RainApi.on('raining', (city, amount) => {
      const tokens = { mm_per_hour: amount }; // for example 3
      const state = { location: city };       // for example "Amsterdam"

      rainStartTrigger.trigger(tokens, state)
        .then(this.log)
        .catch(this.error);
    });
  }
}

module.exports = App;
```

The same pattern for device triggers, comparing an autocomplete argument to the state:

```javascript
this._flowTriggerAppLaunched = this.homey.flow
  .getDeviceTriggerCard('app_launched')
  .registerRunListener(async (args, state) => args.application.id === state.id);

this._flowTriggerAppLaunched.registerArgumentAutocompleteListener(
  'application',
  // `args.device` is the Device the user already picked in the front-end
  // (rename it in the manifest with `$deviceName` if you prefer another key)
  async (query, args) => args.device.autocompleteApplicationArgument(query),
);
```

### 7.5 Autocomplete listeners — two equivalent APIs

| API | Signature |
|---|---|
| `FlowCard#registerArgumentAutocompleteListener(name, listener)` | returns `FlowCard` |
| `FlowCard#getArgument(name)` → `FlowArgument`, then `FlowArgument#registerAutocompleteListener(listener)` | returns `FlowArgument` |

```javascript
const myActionCard = this.homey.flow.getActionCard('my_action');
const myActionCardMyArg = myActionCard.getArgument('my_arg');

myActionCardMyArg.registerAutocompleteListener(async (query, args) => {
  const results = [
    {
      name: 'Value name',
      description: 'Optional description',
      icon: 'https://path.to/icon.svg',
      id: '...',
    },
  ];
  return results.filter((result) => result.name.toLowerCase().includes(query.toLowerCase()));
});
```

### 7.6 The `update` event and `getArgumentValues()`

`FlowCard` emits `update` when the card is changed by the user (e.g. a Flow has been saved). Combine it with `getArgumentValues()` to keep an internal subscription list in sync — the canonical example is a card that triggers on a hashtag: the app must know which hashtags to watch.

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const myTrigger = this.homey.flow.getTriggerCard('my_trigger');

    myTrigger.on('update', () => {
      this.log('update');

      myTrigger.getArgumentValues()
        .then((args) => {
          // args is [{ my_arg: 'user_value' }] — one entry per Flow card instance
        })
        .catch(this.error);
    });
  }
}

module.exports = App;
```

| Method | Returns |
|---|---|
| `FlowCardTrigger` / `FlowCardCondition` / `FlowCardAction` `#getArgumentValues()` | `Promise<Array<any>>` — array of key/value objects keyed by argument name, one entry per Flow card |
| `FlowCardTriggerDevice#getArgumentValues(device)` | same, but only for the given `Device` instance |

(The SDK reference documents `getArgumentValues()` on each of the four card subclasses, not on the base `FlowCard`.)

## 8. Tokens

Tokens are typed variables usable throughout a Flow. In the UI they are called **Tags**.

* **Local** — attached to a Flow's trigger card (e.g. the name of the user that came home), or emitted by a then-card in Advanced Flow.
* **Global** — available anywhere, without the app triggering anything (e.g. the current temperature).

Token `type` is one of `string`, `number`, `boolean`, `image`.

### 8.1 Local tokens on a trigger card

| Key | Type | Description |
|---|---|---|
| `name` | `string` (**required**) | Key used in the `tokens` object passed to `trigger()`. |
| `type` | `string` | `string` \| `number` \| `boolean` \| `image`. Defaults to `string`; omitting it makes `homey app validate` warn that an explicit type will be required in the future. |
| `title` | translation object (**required**) | Displayed name of the tag. |
| `example` | translation object, number or boolean | Sample value shown in the Flow editor. A bare string counts as a translation object (the schema's `i18nObject` is `string | { en, … }`), so `"example": "Amsterdam"` is valid too. |

Those four keys are the whole declared token schema — `name` and `title` are required, `type` and `example` optional. There is no `unit`, `id` or `placeholder` key on a token.

```json
// /.homeycompose/flow/triggers/rain_start.json
{
  "title": { "en": "It starts raining" },
  "tokens": [
    {
      "name": "mm_per_hour",
      "type": "number",
      "title": { "en": "mm/h" },
      "example": 5
    },
    {
      "name": "city",
      "type": "string",
      "title": { "en": "City" },
      "example": { "en": "Amsterdam" }
    }
  ]
}
```

```javascript
// /app.js
'use strict';

const Homey = require('homey');
const RainApi = require('rain-api');

class App extends Homey.App {
  async onInit() {
    const rainStartTrigger = this.homey.flow.getTriggerCard('rain_start');

    RainApi.on('raining', (city, amount) => {
      const tokens = {
        mm_per_hour: amount,
        city,
      };

      rainStartTrigger.trigger(tokens)
        .then(this.log)
        .catch(this.error);
    });
  }
}

module.exports = App;
```

**Gotcha — the docs show two different keys for a token's sample value.** The Tokens page and the auto-generated-capability example use `"example"` (`"example": 5`, `"example": { "en": "Clicks" }`); the Flow-State example on the Arguments page writes `"placeholder": { "en": "5" }` on a token. The locale-override path is `$flow.<type>.<cardId>.tokens.<tokenName>.{title,example}` — **use `example`**.

### 8.2 Tokens returned by a then-card (Advanced Flow)

An **action** card can output tokens: declare a `tokens` array exactly like on a trigger, and `return` an object with those keys from the run listener.

```json
{
  "title": { "en": "Make it stop raining" },
  "hint": { "en": "Hires a shaman to do a sunny dance. Might cost some money." },
  "tokens": [
    { "name": "shamanName", "type": "string", "title": { "en": "Name of the Shaman" } },
    { "name": "shamanCost", "type": "number", "title": { "en": "Cost of the Shaman (€)" } }
  ]
}
```

```javascript
const stopRainingAction = this.homey.flow.getActionCard('stop_raining');

stopRainingAction.registerRunListener(async (args, state) => {
  await RainApi.makeItStopRaining();

  // Return the Tokens for Advanced Flow
  return {
    shamanName: 'Alumbrada',
    shamanCost: 10,
  };
});
```

**Gotcha — declaring `tokens` on a then-card hides it from the standard Flow editor.** A then-card with `tokens` automatically implies `"advanced": true`, so it is only selectable when creating/editing an Advanced Flow. If the card must remain usable in a standard Flow, do not give it tokens (ship a second, token-less card instead).

### 8.3 Global tokens — `ManagerFlow`

| Method | Signature | Notes |
|---|---|---|
| `createToken` | `async createToken(id, opts) → Promise<FlowToken>` | `id` should be alphanumeric. `opts.type` = `string`\|`number`\|`boolean`\|`image`; `opts.title` = `string`; `opts.value` = initial value. |
| `getToken` | `getToken(id) → FlowToken` | `id` as provided to `createToken`. |
| `unregisterToken` | `async unregisterToken(tokenInstance) → Promise<any>` | Takes the `FlowToken` instance. |

| `FlowToken` method | Signature | Notes |
|---|---|---|
| `setValue` | `async setValue(value) → Promise<any>` | `string \| number \| boolean \| Image`; must match the declared `type`. |
| `unregister` | `async unregister() → Promise<any>` | Shorthand for `ManagerFlow#unregisterToken`. |

```javascript
// /app.js
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const myToken = await this.homey.flow.createToken('my_token', {
      type: 'number',
      title: 'My Token',
    });

    await myToken.setValue(23.5);
  }
}

module.exports = App;
```

**By default a device's capabilities are registered as global tokens.** Suppress that per capability with the `preventTag` capability option (see `references/capabilities.md`).

### 8.4 Image tokens

```javascript
// /app.js
'use strict';

const fs = require('fs');
const path = require('path');
const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const myImage = await this.homey.images.createImage();
    myImage.setPath(path.join(__dirname, 'assets', 'images', 'kitten.jpg'));

    // create a token & register it
    const myImageToken = await this.homey.flow.createToken('my_token', {
      type: 'image',
      title: 'My Image Token',
    });
    await myImageToken.setValue(myImage);

    // listen for a Flow action that receives an image droptoken
    const myActionCard = this.homey.flow.getActionCard('image_action');
    myActionCard.registerRunListener(async (args, state) => {
      if (args.droptoken == null) throw new Error('No image provided');

      const imageStream = await args.droptoken.getStream();
      this.log(`saving ${imageStream.meta.contentType} to: ${imageStream.meta.filename}`);

      const targetFile = fs.createWriteStream(path.join('/userdata', imageStream.meta.filename));
      imageStream.pipe(targetFile);
      return true;
    });

    // pass an image straight into a trigger's tokens
    const myTriggerCard = this.homey.flow.getTriggerCard('image_trigger');
    await myTriggerCard.trigger({ my_image: myImage });
  }
}

module.exports = App;
```

`createToken()` also accepts the initial value inline: `createToken('my_token', { type: 'image', title: 'My Image Token', value: myImage })`.

See `references/advanced-features.md` for `Image` creation, the 5 MB ceiling, `/userdata` behaviour, and the two documented stream-metadata shapes (`stream.meta.contentType` vs `stream.contentType`).

## 9. Advanced Flow

| Manifest | Effect |
|---|---|
| `"advanced": true` | The card is only available for use in Advanced Flow. |
| `"tokens": [ … ]` on a **then**-card | Automatically implies `"advanced": true`. |

Documented Advanced-Flow behaviour is limited to those two rules plus the token return value of §8.2 (`return { … }` from the action's run listener). Multiple named card outputs and any `$token` manifest syntax are **not** part of the documented Apps SDK v3 surface — do not invent manifest keys for them. Branching in Advanced Flow is expressed through condition cards, which resolve `true`/`false` exactly as in a standard Flow, and through a rejected run listener stopping the Flow.

## 10. Automatically generated Flow cards

**System capabilities generate their cards for you.** Declaring `onoff` already gives the user the triggers
`onoff_true` / `onoff_false`, the conditions `on` / `open`, and the actions `on` / `off` / `toggle` / `open` /
`close` — 404 such cards exist across 181 of the 184 system capabilities. The complete per-capability table is
in `references/capabilities.md`; check it before authoring a card, because redeclaring a generated card shows
the user a duplicate in the Flow editor.

For **custom** capabilities nothing is generated — but Homey still *runs* trigger cards with conventional ids
when you call `Device#setCapabilityValue()`, so you author the card and Homey fires it:

| Custom capability type | Trigger card id(s) run automatically |
|---|---|
| `number`, `enum`, `string` | `<capability_id>_changed` |
| `boolean` | `<capability_id>_true` and `<capability_id>_false` |

Define the card yourself (so it exists) and give it a token with the same name as the capability to receive the current value:

```json
// /drivers/<driver_id>/driver.flow.compose.json
{
  "triggers": [
    {
      "id": "measure_clicks_changed",
      "title": { "en": "Clicks updated" },
      "tokens": [
        {
          "name": "measure_clicks",
          "type": "number",
          "title": { "en": "clicks" },
          "example": { "en": "Clicks" }
        }
      ]
    }
  ]
}
```

This also works for sub-capabilities: updating `measure_clicks.inside` runs triggers with id `measure_clicks.inside_changed`.

**Gotcha — Flow cards are *not* auto-generated for sub-capabilities.** The system cards a capability normally provides are only created for the base capability; you must author cards for `measure_clicks.inside` yourself (see `references/capabilities.md`).

## 11. Deprecating and changing cards

Changing or removing Flow cards is a **breaking change**. Publishing breaking changes is generally not allowed — users expect their Flows to keep working across automatic app updates.

To retire a card, or to change how it is constructed (add/remove arguments), add `"deprecated": true` and ship a *new* card with the new shape:

```json
// /.homeycompose/flow/actions/stop_raining.json
{
  "title": { "en": "Flow Action Title" },
  "deprecated": true
}
```

* Deprecated cards keep working in existing Flows but disappear from the 'Add Card' list.
* The schema allows only `"deprecated": true`. To reverse a deprecation, **remove** the key — `"deprecated": false` fails validation.
* **Gotcha — do not remove or change the deprecated card's run listener.** Removing the listener still breaks existing Flows even though the manifest entry remains.
* Removing a capability removes its Flow cards; Flows using those cards break. Changing a device's class (`Device#setClass()`) can break Flows whose cards depend on that class.

## 12. Homey Cloud (`platforms`)

To run on Homey Cloud, add `platforms` to the **App, Driver and Flow** manifests. Missing it on a Flow card makes that card local-only.

```json
// /.homeycompose/flow/triggers/rain_start.json
{
  "title": { "en": "It starts raining" },
  "hint": { "en": "When it starts raining more than 0.1 mm/h." },
  "platforms": ["local", "cloud"]
}
```

A card's `platforms` must be a **subset** of the App manifest's `platforms`: listing `"cloud"` on a card while the app itself does not list `"cloud"` is a validation error (and the same for `"local"`). `platforms` on the App manifest is itself required to publish a verified app.

Only SDK v3 is supported on Homey Cloud. Validate with `homey app validate --level verified`. See `references/homey-cloud.md` and `references/publishing.md`.

## 13. Internationalization of card strings

Card strings can be inline translation objects (`{ "en": …, "nl": … }`) or a single plain string when no translation is needed. Always provide at least `en` — it is the fallback.

Translatable keys on Flow cards: `title`, `titleFormatted`, `hint`, argument `title` / `label` / `placeholder`, argument `values[].title`, token `title` / `example`.

Locale-file override paths (`.homeycompose/locales/<lang>.json`):

| Path | Targets |
|---|---|
| `$flow.<type>.<cardId>.{title,titleFormatted,hint}` | card strings |
| `$flow.<type>.<cardId>.args.<argName>.{title,label,placeholder}` | argument strings |
| `$flow.<type>.<cardId>.args.<argName>.values.<valueId>.title` | dropdown/multiselect value labels |
| `$flow.<type>.<cardId>.tokens.<tokenName>.{title,example}` | token strings |

```json
// /.homeycompose/locales/nl.json
{
  "$flow": { "actions": { "do_something": { "title": "Doe iets" } } }
}
```

Review rule: translations must be consistent. If you translate Flow cards into a language, translate *all* Flow cards, device settings and capabilities into it too.

## 14. Gotchas

* **Register each card once**, in `App#onInit()` or `Driver#onInit()` — never in `Device#onInit()`. Per-device registration duplicates listeners and fires Flows multiple times.
* **Always `.catch(this.error)` fire-and-forget `trigger()` calls.** An unhandled rejection crashes the app (fatal on Homey Cloud).
* **Device triggers need `getDeviceTriggerCard()`**, not `getTriggerCard()`; only the former's `trigger()` accepts a `device` first parameter. Wait for `this.driver.ready()` before triggering from a `Device`.
* **`$filter`'s `capabilities` is static**: `addCapability()` / `removeCapability()` at runtime do not change which devices the card is offered for.
* **Autocomplete: filter on `query` yourself**, otherwise the popup looks frozen.
* **Autocomplete values are objects, not strings** — `args.myArg.id`, not `args.myArg`.
* **Droptokens can be `null`**; optional (`"required": false`) arguments can be `undefined`. Null-check both.
* **One droptoken per card**, multiple allowed types.
* **`"duration": true` collides with an argument named `duration`** — never use both on one card.
* **`tokens` on a then-card silently makes it Advanced-Flow-only** (implies `"advanced": true`).
* **`"deprecated": false` is a validation error, not a no-op.** The schema declares `deprecated`, `advanced` and `highlight` as `enum: [true]` — the only valid value is the literal `true`. To un-deprecate a card, delete the key.
* **The `flowCard` schema does not forbid unknown keys.** A misspelled card or argument property (`titleFormated`, `require`, `lableDecimals`) passes `homey app validate` in silence and simply does nothing at runtime. Proofread rather than relying on the validator.
* **`hint`, `duration` and an argument's `required` are documented but undeclared in the schema.** They work; they are just not type-checked, so `"duration": true` on a trigger or condition card validates and does nothing.
* **Dropdown values only require `id`; multiselect values require `id` *and* `title`.** A `dropdown` value missing its `title` validates and then renders with no visible label.
* **`multiselect` also requires `conjunction`** (`"and"` or `"or"`) — the only argument type with a second mandatory key besides `values`.
* **Dropdown/multiselect values use `title`**, not `label`, despite one contradictory example in the Flow overview page.
* **Token sample values use `example`**, not `placeholder`, despite one contradictory example on the Arguments page.
* **The manifest key is `titleFormatted`** — the guidelines page's `titleFormated` is a typo.
* **`app.json` is generated.** Edit `.homeycompose/**` and `driver.flow.compose.json`; run `homey app build` / `homey app run` to regenerate. Never hand-edit `app.json`.
* **Every argument must appear exactly once in `titleFormatted`** (except the Compose-inserted `device` argument, and including `[[droptoken]]`). A missing `titleFormatted` is only a warning at `--level publish`, but a hard error at `--level verified`.
* **`homey app validate --level publish` is not certification.** Reviewers reject Flow card titles that mention device names, repeat When/And/Then, or use parentheses — none of which the validator checks.
* **The app process runs in UTC.** Naive `new Date().getHours()` inside a run listener is the classic cause of "my Flow fires an hour early". Take the zone from `this.homey.clock.getTimezone()` — see `references/advanced-features.md`.
* **Highlight sparingly.** A long "Highlighted Cards" list is as hard to navigate as the full list.

## Sources

* <https://apps.developer.homey.app/the-basics/flow>
* <https://apps.developer.homey.app/the-basics/flow/arguments>
* <https://apps.developer.homey.app/the-basics/flow/tokens>
* <https://apps.developer.homey.app/advanced/homey-compose>
* <https://apps.developer.homey.app/guides/homey-cloud>
* <https://apps.developer.homey.app/guides/how-to-breaking-changes>
* <https://apps.developer.homey.app/app-store/guidelines>
* <https://apps.developer.homey.app/the-basics/devices/capabilities>
* <https://apps.developer.homey.app/the-basics/app/internationalization>
* <https://apps-sdk-v3.developer.homey.app/ManagerFlow.html>
* <https://apps-sdk-v3.developer.homey.app/FlowCard.html>
* <https://apps-sdk-v3.developer.homey.app/FlowCardTrigger.html>
* <https://apps-sdk-v3.developer.homey.app/FlowCardTriggerDevice.html>
* <https://apps-sdk-v3.developer.homey.app/FlowCardCondition.html>
* <https://apps-sdk-v3.developer.homey.app/FlowCardAction.html>
* <https://apps-sdk-v3.developer.homey.app/FlowArgument.html>
* <https://apps-sdk-v3.developer.homey.app/FlowToken.html>
