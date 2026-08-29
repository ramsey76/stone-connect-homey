# 433 MHz / 868 MHz RF & Infrared

Signal definitions in `.homeycompose/signals/{433,868,ir}/<id>.json`, the `ManagerRF` / `Signal` runtime API
(`this.homey.rf`), and the `homey-rfdriver` library (`RFSignal`, `RFDriver`, `RFDevice`, `RFUtil`, `RFError`)
with its copy/generate/imitate pairing templates.

Related: `references/pairing.md`, `references/drivers-and-devices.md`, `references/app-and-manifest.md`,
`references/capabilities.md`, `references/homey-cloud.md`, `references/cli-and-tooling.md`.

## Platform support & permissions

| Frequency | Manager method | Permission | Driver `connectivity` | Availability |
| --- | --- | --- | --- | --- |
| 433 MHz | `this.homey.rf.getSignal433(id)` | `homey:wireless:433` | `rf433` | Homey Pro + Homey Bridge (Cloud) |
| 868 MHz | `this.homey.rf.getSignal868(id)` | `homey:wireless:868` | `rf868` | **Homey Pro (2016—2019) only**; "not possible with Homey Bridge" |
| Infrared | `this.homey.rf.getSignalInfrared(id)` | `homey:wireless:ir` | `infrared` | Homey Pro + Homey Bridge (Cloud) |

```json
{
  "id": "com.example.rf",
  "permissions": ["homey:wireless:433", "homey:wireless:ir"]
}
```

- Permissions go in `/.homeycompose/app.json` → `permissions`. Without the permission the corresponding
  `ManagerRF` method throws.
- Apps do **not** auto-update on Homey when new permissions are added — users must re-approve.
- `homey-lib` rejects a driver whose **own** `platforms` array contains `cloud` when its `connectivity`
  contains `rf868` (error:
  `drivers.<id> invalid 'connectivity': Platform 'cloud' does not support 'lan', 'matter' or 'rf868'.`).
  `rf433` and `infrared` are fine on Cloud.
- App Store guideline 1.1.3: *"You may not include protocol names (Zigbee, Z-Wave, 433 MHz, Infrared etc.) in
  your app's name."*

### Scaffolding with the CLI

`homey app driver create` → "What type of device is this?" offers `Infrared`, `433 Mhz`, `868 Mhz`. Each branch
asks *"Do you want to install homey-rfdriver?"* (default yes → `npm install homey-rfdriver`) and writes
`drivers/<id>/driver.compose.json` with:

| Choice | Protocol-specific manifest keys |
| --- | --- |
| `Infrared` | `"connectivity": ["infrared"]` |
| `433 Mhz` | `"connectivity": ["rf433"]` |
| `868 Mhz` | `"platforms": ["local"]`, `"connectivity": ["rf868"]` |

Every branch additionally writes `name`, `class`, `capabilities`, `images` and a `platforms` array — for
`Infrared`/`433 Mhz` copied from the app manifest's `platforms`, for `868 Mhz` forced to `["local"]`.

The CLI then prints the doc link for the chosen protocol. It does **not** generate a signal definition or copy
the pairing templates — do both by hand.

## How signals work

A signal is a block-wave data signal carried on an electromagnetic carrier. Homey has separate 433 MHz and
868 MHz antennas plus an IR emitter/receiver.

- **Modulation.** ASK (amplitude shift keying), FSK (frequency shift keying), and the ASK variant **OOK**
  (on-off keying) used by most 433 MHz devices — one amplitude level for high, absence of carrier for low.
- **Receive band.** Homey's receive band is broadened by 325 kHz so deviating device carriers (e.g. 433.89 MHz)
  are still heard: **433.76 – 434.08 MHz** and **868.14 – 868.46 MHz**. Devices outside that band cannot be
  received.
- **Encoding.** Either duration-based (e.g. X10) or edge-based (e.g. Manchester). Homey supports both.
- **Signal Manager.** Homey matches every incoming raw block-wave against all registered signal definitions;
  on a match it decodes the payload and routes it to the owning app. Transmission is the same path reversed.

### Obtaining a signal

The official route is a logic analyzer / oscilloscope capture of the remote plus the devtools: *"It is possible
to make Homey record raw data for a short period of time using the devtools"* (<https://tools.developer.homey.app>).
There is no CLI command for signal capture.

### Signal requirements (hard limits)

| Signal characteristic | Description | Min | Max |
| --- | --- | --- | --- |
| Converted time-intervals | Number of time-intervals used to generate the signal | 1 | 256 |
| Signal duration | Total duration of a signal being sent | 5 us | 1 s |

> The radio controller cannot handle time-interval arrays larger than 256 intervals. A too-long signal blocks
> other apps from transmitting.

### Fixed receiver configuration

The receiver's filter bandwidth in listening mode is **shared with every other app** and cannot be changed by a
developer.

**433 MHz**

| Attribute | Value |
| --- | --- |
| Carrier frequency | 433890000 Hz |
| Channel spacing | 325000 Hz |
| BaudRate | 12004 Bd |
| Modulation | ASK |

**868 MHz** *(Homey Pro 2016—2019 only)*

| Attribute | Value |
| --- | --- |
| Carrier frequency | 868300000 Hz |
| Channel spacing | 325000 Hz |
| BaudRate | 12004 Bd |
| Modulation | ASK |

## Signal definition files

Location — one JSON file per signal, per frequency directory:

```
/.homeycompose/signals/433/<signal_id>.json
/.homeycompose/signals/868/<signal_id>.json
/.homeycompose/signals/ir/<signal_id>.json
```

Homey Compose collapses these into `app.json`:

```json
{
  "signals": {
    "433": { "my_signal": { /* … */ } },
    "868": { "…": {} },
    "ir":  { "lg": { /* … */ } }
  }
}
```

- The signal id is the **file basename** unless the JSON contains a `$id` property, which wins.
- `app.json`'s `signals` object only accepts the keys `433`, `868`, `ir` (`additionalProperties: false`).
- Signals live at **app** level, not driver level — several drivers can share one signal (that is exactly what
  `RFDriver.getRFSignal()` caches). There is no `signals` key inside a driver object.
- `signals` is **optional** — it is not in the manifest schema's `required` list (`id`, `name`, `version`,
  `compatibility`, `author`).

The complete JSON Schema for the top-level `signals` property is:

```json
"signals": {
  "type": "object",
  "patternProperties": { "^(433|868|ir)$": { "type": "object" } },
  "additionalProperties": false
}
```

That is the *whole* schema: each frequency value is a bare `object`, so the JSON Schema constrains **nothing**
about an individual signal definition. Every property rule in the next sections comes from `homey-lib`'s
`Signal` class (`lib/Signal/validators.js`), which `homey app validate` runs *after* the schema pass — the two
layers report errors in different formats (`manifest.signals…` vs `Invalid signal: <frequency>.<signalId>`).

### Encoding properties

Times are in **microseconds** unless stated otherwise.

| Attribute | Description | Min. | Default | Max. | Type | Unit |
| --- | --- | --- | --- | --- | --- | --- |
| `agc` | AGC pulses | 5us | - | 32767us | Array of integers | Microseconds |
| `sof` | Start-of-frame | 5us | - | 32767us | Array of integers | Microseconds |
| `words` | Words | 5us | - | 32767us | Array of integers Array | Microseconds |
| `eof` | End-of-frame | 5us | - | 32767us | Array of integers | Microseconds |
| `interval` | Interval | 5us | 5000us | 32767us | Integer | Microseconds |
| `manchesterUnit` | ManchesterUnit | 5us | - | 32767us | Integer | Microseconds |
| `minimalLength` | Minimal payload length | 1 | 1 | Infinity | Integer | - |
| `maximalLength` | Maximal payload length | 1 | Infinity | Infinity | Integer | - |
| `prefixData` | Prepended data | 0 | - | words.length | Array of Integers | - |
| `postfixData` | Suffixed data | 0 | - | words.length | Array of Integers | - |
| `cmds` | Static commands | - | - | - | String => Integer Array Object | - |
| `toggleSof` | Toggled SOF | 5us | - | 32767us | Array of integers | Microseconds |
| `toggleBits` | Toggle bit indexes | 0 | - | words.length | Array of Integers | - |
| `sensitivity` | Sensitivity | 0.0 | 0.3 | 0.5 | float | - |
| `packing` | Packing | - | false | - | Boolean | - |
| `txOnly` | Disable receiving | - | false | - | Boolean | - |

Additional keys the `homey-lib` validator accepts but the documentation page does not list:

| Attribute | Type | Validation | Notes |
| --- | --- | --- | --- |
| `manchesterMaxUnits` | Integer | `>= 1` (bounds table: 1–1000) | Used together with `manchesterUnit` |
| `toggleIndexes` | Array of Integers | every index must be `< sof.length` | The validator bounds them by `sof.length` (and throws a `TypeError` when `sof` is absent), so they index into `sof`, not into the payload |
| `dutyCycle` | Number | must be a number (any frequency); 30–70 on `ir` | IR carrier duty cycle. The *type* check lives in `genericValidator`, so it runs for every regular signal; only the 30–70 **bounds** check is `ir`-only |
| `toggleCmds` | String ⇒ Prontohex String | prontohex signals only | Alternating command set |
| `type` | String | must be exactly `"prontohex"` if present | Any other value ⇒ `Invalid Signal type` |

### Radio configuration properties

| Attribute | Description | Min. | Default | Max. | Type | Unit |
| --- | --- | --- | --- | --- | --- | --- |
| `repetitions` | Repetitions | 1 | 10 | 255 | Integer | - |
| `rxTimeout` | rxTimeout | 0 | 10 | 255 | Integer | Milliseconds |
| `modulation.type` | Modulation | - | `'ASK'` | - | String (`ASK` \| `FSK` \| `GFSK`) | - |
| `modulation.channelSpacing` | Channel spacing | 58000 | 325000 | 812000 | Integer | Hertz |
| `modulation.channelDeviation` | Channel deviation | 5000 | 25000 | 50000 | Integer | Hertz |
| `modulation.baudRate` | baudRate | 1000 | 12004 | 200000 | Integer | Baud (Bd) |
| `carrier` | Carrier frequency | radio specific | radio specific | radio specific | Integer | Hertz |

Carrier ranges:

| Frequency | Documented min | Documented default | Documented max | `homey-lib` validator range |
| --- | --- | --- | --- | --- |
| 433 | 433000000 | 433920000 | 433990000 | 433000000 – 433990000 |
| 868 | 868000000 | 868300000 | 868990000 | 868000000 – **868900000** |
| ir | 30000 | 38000 | 45000 | 30000 – **58000** |

**Gotcha:** the documented 868 and IR maxima disagree with the shipped validator, and they disagree in
*opposite directions*: for 868 the validator is **stricter** than the docs (868900000 < 868990000), for IR the
validator is **looser** (58000 > 45000). Stay inside the intersection — 868: `868000000 – 868900000`,
IR: `30000 – 45000` — so both `homey app validate` and the documented radio range accept the signal.

### Property semantics

| Property | Meaning |
| --- | --- |
| `agc` | Automatic-Gain-Control preamble in time-intervals. Never changes. **Ignored when receiving, added when transmitting.** With Manchester encoding, fill it with `1`/`0` instead of durations. |
| `sof` | Start-of-frame preamble in time-intervals; used by devices to detect an incoming signal. Never changes. `[275, 2640]` = 275 us high, 2640 us low. |
| `words` | One entry per symbol. Single-level encoding = 2 words (`0` and `1`); multi-level encoding maps bit combinations (`00`,`01`,`10`,`11`) to more words. Each word is an array of alternating high/low durations. With Manchester encoding, words hold `1`/`0` instead of durations. |
| `eof` | End-sequence. Never changes. **Specify `minimalLength` when the EOF (partially) overlaps the words** — it increases the amount of proper matches. |
| `interval` | Time between two subsequent repetitions of the signal. |
| `manchesterUnit` | Enables Manchester encoding. `[1, 0]` with `manchesterUnit: 100` ⇒ 100 us high followed by 100 us low. Switches `words`/`agc`/`sof`/`toggleSof`/`eof` from durations to bits (allowed values then become 0–1, not 5–32767). |
| `minimalLength` | Minimal signal length **in words**. Devices with variable payload length need it. |
| `maximalLength` | Maximal signal length in words. |
| `prefixData` | Words prepended to every transmitted payload. On receive, incoming payloads are checked for the prefix; only on a match is it stripped and the remainder delivered to the app. |
| `postfixData` | Same as `prefixData`, appended instead of prepended. |
| `cmds` | Map of command identifier ⇒ payload array (**excluding** prefix/postfix data). For devices with a static command set and no dynamic address. Used by `Signal#cmd()` and the `cmd` event. |
| `toggleSof` | An alternate SOF alternated with the primary `sof` on each transmission. Works automatically for TX and RX and drives the `first` argument of the `cmd` and `payload` events. |
| `toggleBits` | Bit indexes inside the payload (**including** prefix/postfix) that flip on each new transmission. Works automatically for TX and RX and drives the `first` argument. The reported payload keeps the toggle bits **as transmitted** (unmodified). |
| `sensitivity` | Maximum relative deviation between definition and received signal (0.0–0.5). Higher = more tolerant. |
| `packing` | Send/receive **byte** arrays instead of bit arrays: every 8 bits are packed into one byte. Discouraged when the payload length is not a multiple of 8; **impossible unless the signal has exactly two words** (the validator enforces `words.length === 2`). |
| `txOnly` | Disables the receiving subsystem for this signal. **Use it whenever you never receive** — RX is expensive. |
| `repetitions` | How often the signal is transmitted. `1` = 1 transmit total, `2` = 2 transmits total. |
| `rxTimeout` | Receive-after-transmit: after transmitting, the radio stays in RX mode for this many **milliseconds** waiting for the device's answer, reusing the same radio configuration. |
| `modulation.type` | `ASK`, `FSK` or `GFSK`. |
| `modulation.channelSpacing` | Filter bandwidth in receive mode. **Only used when `rxTimeout > 0`.** |
| `modulation.channelDeviation` | Frequency deviation, for FSK/GFSK. |
| `modulation.baudRate` | Symbol changes per second. |
| `carrier` | Carrier frequency used while **sending**. Defaults to the default receive carrier. Needed for devices with deviating carriers (e.g. Somfy). |

### Repetitions resolution order

Highest priority first:

1. the `repetitions` option of `Signal#tx()` / `Signal#cmd()`;
2. the `repetitions` attribute in the signal definition;
3. otherwise **20**.

> Repetition behaviour was aligned across products as of Homey Pro (2016—2019) v10.0.6, Homey Pro (Early 2023)
> v10.3.1 and Homey Bridge v85.

**Gotcha:** the radio-configuration table says the `repetitions` default is `10`, while the prose says the
fallback is `20`. Set `repetitions` explicitly in every signal definition and the ambiguity disappears.

### Validation rules enforced by `homey app validate`

`homey-lib` builds a `Signal` per `app.json` entry and reports `Invalid signal: <frequency>.<signalId>` plus one
of the messages below. Only properties that are **present** are validated; unknown keys are silently ignored
(this is why a stray `$id` left in the file by Homey Compose is harmless).

Which validator engines run depends on the signal *kind* and the *frequency directory*:

| Signal | Engines that run |
| --- | --- |
| Regular (`type` absent) | `genericValidator` + `rfValidator`, then the per-frequency engine |
| Prontohex (`type: "prontohex"`) | `prontoValidator` only (`cmds`, `toggleCmds`, `repetitions`), then the per-frequency engine |
| Frequency `433` | `modulationValidator` + `rf433Validator` |
| Frequency `868` | `modulationValidator` + `rf868Validator` |
| Frequency `ir` | `irValidator` only (`carrier`, `dutyCycle`) — **no** `modulationValidator` |

| Rule | Error message |
| --- | --- |
| Frequency directory must be `433`, `868` or `ir` | `Invalid Frequency` |
| `type` present and ≠ `prontohex` | `Invalid Signal type` |
| Regular signal must contain at least one of `sof`, `eof`, `words` | `mandatory_fields` |
| Prontohex signal must contain `cmds` | `mandatory_fields` |
| `words` must be an array with **more than one** word, each word an array with **more than one** interval | `invalid_words` |
| `agc`/`sof`/`toggleSof`/`eof` must be arrays | `invalid_agc` / `invalid_sof` / `invalid_toggleSof` / `invalid_eof` |
| Interval values in `words`/`agc`/`sof`/`toggleSof`/`eof`: 5–32767 (or 0–1 when `manchesterUnit` is set) | `word_interval_out_of_bounds` / `agc_out_of_bounds` / `sof_out_of_bounds` / `toggleSof_out_of_bounds` / `eof_out_of_bounds` |
| `manchesterUnit` number, 5–32767 | `invalid_manchesterUnit` / `manchesterUnit_out_of_bounds` |
| `manchesterMaxUnits` number `>= 1` | `invalid_manchesterMaxUnits` |
| `sensitivity` number, 0.0–0.5 | `invalid_sensitivity` |
| `interval` number, 5–32767 | `invalid_signalinterval` / `interval_out_of_bounds` |
| `minimalLength`/`maximalLength` `> 0` | `invalid_minimalLength` / `invalid_maximalLength` |
| `packing` boolean **and** `words.length === 2` | `invalid_packing` |
| `txOnly` boolean | `invalid_txOnly` |
| `dutyCycle` number; on `ir`: 30–70 | `invalid_dutyCycle` / `dutyCycle_out_of_bounds` |
| `cmds` values: arrays of valid word indexes, or bytes `0x00`–`0xFF` when `packing` is true | `invalid_cmd` |
| `prefixData`/`postfixData`: same rule as `cmds` values | `invalid_prefixData` / `invalid_postfixData` |
| `toggleIndexes` array; every value `< sof.length` | `invalid_toggleIndexes` |
| `toggleBits` array | `invalid_toggleBits` |
| `repetitions` 1–255 | `repetitions_out_of_bounds` |
| `rxTimeout` 0–255 | `rxTimeout_out_of_bounds` |
| `modulation` present ⇒ **all four** of `type`, `baudRate`, `channelSpacing`, `channelDeviation` required; `type ∈ {ASK, FSK, GFSK}`; `baudRate` 1000–200000; `channelSpacing` 58000–812000; `channelDeviation` 5000–50000. Validated for `433`/`868` only. | `invalid_modulation_properties` |
| `carrier` inside the frequency range (see table above) | `carrier_out_of_bounds` (433/868) / `invalid_carrier` (ir) |
| Prontohex `cmds`/`toggleCmds` strings match `/^(([0-9a-f]{4}\s?){2}){2,}$/i` | `invalid_pronto_cmds` / `invalid_pronto_toggleCmds` |

**Gotcha:** a `modulation` object is all-or-nothing. Adding only `{"type": "FSK"}` fails validation — you must
also supply `baudRate`, `channelSpacing` and `channelDeviation`.

**Gotcha:** `homey-lib`'s own bundled example uses a `dsof` key that no validator recognises. It is neither
documented nor validated — do not copy it.

### Worked example — KlikAanKlikUit (433 MHz)

Captured with a logic analyzer: red = `sof`, yellow = `words[0]` (0/LOW), green = `words[1]` (1/HIGH),
blue = `eof`, purple = `interval`.

```json
{
  "sof": [275, 2640],
  "eof": [275],
  "words": [
    [250, 275, 250, 1250],
    [250, 1250, 250, 275]
  ],
  "interval": 10000,
  "sensitivity": 0.5,
  "repetitions": 20,
  "minimalLength": 32,
  "maximalLength": 36
}
```

The frame in the capture decodes to `00111111010001010100110110010000` — 32 bits, split by the app into
homecode, unitcode and dim/onoff value.

The shipped example app `athombv/nl.klikaanklikuit-example` defines three signals; `kaku-new-dim` and
`kaku-old` are **multi-level** (three words), which is why `payloadToCommand` sees values other than 0/1:

```json
// /.homeycompose/signals/433/kaku-new.json
{ "sof": [265, 2580], "eof": [265],
  "words": [[265, 295, 265, 1280], [265, 1280, 265, 295]],
  "interval": 10665, "sensitivity": 0.4, "repetitions": 20,
  "minimalLength": 32, "maximalLength": 36 }

// /.homeycompose/signals/433/kaku-new-dim.json
{ "sof": [225, 2774], "eof": [236],
  "words": [[265, 295, 265, 1280], [265, 1280, 265, 295], [265, 295, 265, 295]],
  "interval": 10665, "sensitivity": 0.4, "repetitions": 20,
  "minimalLength": 32, "maximalLength": 36 }

// /.homeycompose/signals/433/kaku-old.json   (empty sof is legal)
{ "sof": [], "eof": [312],
  "words": [[312, 1090, 312, 1090], [312, 1090, 990, 400], [312, 1090, 312, 380]],
  "interval": 11300, "repetitions": 6, "sensitivity": 0.5,
  "minimalLength": 12, "maximalLength": 12 }
```

## Runtime API — `ManagerRF` and `Signal`

`this.homey.rf` is a `ManagerRF`.

### ManagerRF

| Method | Returns | Notes |
| --- | --- | --- |
| `getSignal433(id)` | `Signal433` | **sync.** `id` (string) as defined in `app.json` → `signals.433` |
| `getSignal868(id)` | `Signal868` | **sync.** `signals.868` |
| `getSignalInfrared(id)` | `SignalInfrared` | **sync.** `signals.ir` |
| `enableSignalRX(signal)` | `Promise<T>` | async. Enable receiving for the signal |
| `disableSignalRX(signal)` | `Promise<void>` | async. Disable receiving |
| `tx(signal, frame, [opts])` | `Promise` | async. `frame` is `Array<number>` or `Buffer` |
| `cmd(signal, commandId, [opts])` | `Promise` | async. `commandId` (string) as specified in the app manifest |

All of these require `homey:wireless:433`, `homey:wireless:868` and/or `homey:wireless:ir`.

### Signal (base of `Signal433`, `Signal868`, `SignalInfrared`)

| Member | Returns | Description |
| --- | --- | --- |
| `tx(frame, [opts])` | `Promise<any>` | Transmit a frame — `frame` is `Array<number>`, an **array of word indexes** |
| `cmd(commandId, [opts])` | `Promise<any>` | Transmit a predefined command from `cmds`; `commandId` is a string |
| `enableRX()` | `Promise<void>` | Shorthand for `ManagerRF#enableSignalRX` |
| `disableRX()` | `Promise<void>` | Shorthand for `ManagerRF#disableSignalRX` |
| `.on('payload', (payload, first) => {})` | — | `payload`: array of word indexes; `first`: whether this is the first detected repetition |
| `.on('cmd', (commandId) => {})` | — | A predefined command was received |

`opts` for both `tx` and `cmd`:

| Option | Type | Description |
| --- | --- | --- |
| `repetitions` | number | Custom repetition count. 1 = 1 transmit in total, 2 = 2 transmits in total, … |
| `device` | `Device` | The device being transmitted to |

`Signal433`, `Signal868` and `SignalInfrared` add no members of their own — they are typed subclasses of
`Signal`.

### Raw usage

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    // Create & register a signal using the id from the signal manifest.
    this.signal = this.homey.rf.getSignal433('my_signal');

    this.signal.on('payload', (payload, first) => {
      this.log(`received data: ${payload.join('')} isRepetition=${!first}`);
    });

    this.signal.on('cmd', (commandId) => {
      this.log('received command:', commandId);
    });

    // Only enable RX when something actually needs it.
    await this.signal.enableRX();

    // Transmit the bits 01011001.
    await this.signal.tx([0, 1, 0, 1, 1, 0, 0, 1]);

    // Transmit a predefined command, three times.
    await this.signal.cmd('ONOFF', { repetitions: 3 });
  }

  async onUninit() {
    if (this.signal) {
      await this.signal.disableRX().catch(this.error);
    }
  }

}

module.exports = MyApp;
```

**Gotcha:** *"Please only register a signal if there are any devices paired, because receiving signals is quite
performance intensive."* Enable RX lazily (that is exactly what `RFSignal#registerRXListener` does) and set
`"txOnly": true` on signals you only ever transmit.

## `homey-rfdriver`

```bash
npm install homey-rfdriver
```

SDK v3 only. Requires `homey:wireless:433`, `homey:wireless:868` and/or `homey:wireless:ir`.
Exports: `RFDevice`, `RFDriver`, `RFSignal`, `RFUtil`, `RFError`.

Typical layout:

```
/.homeycompose/signals/433/my_signal.json
/lib/MySignal.js                          (extends RFSignal)
/drivers/my_driver/driver.js              (extends RFDriver)
/drivers/my_driver/device.js              (extends RFDevice)
/drivers/my_driver/pair/rf_receiver_learn.html
/drivers/my_driver/pair/rf_receiver_add.html
/drivers/my_driver/pair/image.svg
```

A driver is either a **transmitter** (a remote — Homey listens) or a **receiver** (a socket/light — Homey
transmits). Copy the matching files from the module's `/pair` folder into your driver's `/pair` folder.

### RFSignal

The JSON says how to turn a wave into bits; `RFSignal` says how to turn those bits into a JavaScript command
object and back.

| Member | Kind | Description |
| --- | --- | --- |
| `static ID` | string | Signal id, must match the manifest signal key |
| `static FREQUENCY` | `'433'` \| `'868'` \| `'ir'` | Picks `getSignal433` / `getSignal868` / `getSignalInfrared`; anything else throws `Invalid Signal Frequency` |
| `this.manifest` | object | `Homey.manifest.signals[FREQUENCY][ID]` — the raw signal definition |
| `this.signal` | `Signal` | The underlying SDK signal |
| `static commandToPayload(command)` | override | Command object ⇒ payload (array of word indexes) |
| `static payloadToCommand(payload)` | override | Payload ⇒ command object. Returning `null`/`undefined` raises `Command Not Found For Payload: …` |
| `static commandToDeviceData(command)` | override | Command ⇒ device-unique `data` object |
| `static createPairCommand()` | override | Invent a command when pairing a **receiver** (as if a remote button was pressed) |
| `registerRXListener(listener)` | async | Adds the listener; calls `signal.enableRX()` when it is the **first** listener |
| `unregisterRXListener(listener)` | async | Removes it; calls `signal.disableRX()` when the **last** one goes |
| `tx(command, props)` | async | `Buffer` passes through untouched, otherwise `commandToPayload(command)`; then `signal.tx(payload, props)` |
| `cmd(command, props)` | async | Straight to `signal.cmd(command, props)` |
| `onRX(payload, isFirst)` | internal | Decodes and fans out to listeners as `listener(command, { isFirst })`; errors go to `this.homey.app.error` |

```javascript
'use strict';

const { RFSignal, RFError, RFUtil } = require('homey-rfdriver');

// Protocol: [ address (1 byte, 0x00-0xFF), state (0x00 = off, 0xFF = on) ]
module.exports = class MySignal extends RFSignal {

  static FREQUENCY = '433';
  static ID = 'my_signal';

  static commandToPayload({ address, state }) {
    if (typeof address !== 'number') throw new RFError('Invalid Address');
    if (typeof state !== 'boolean') throw new RFError('Invalid State');
    return [address, state ? 0x00 : 0xFF];
  }

  static payloadToCommand(payload) {
    const address = Number(payload[0]);
    const state = Boolean(payload[1]);
    return { address, state };
  }

  static commandToDeviceData(command) {
    return { address: command.address };
  }

  static createPairCommand() {
    return {
      address: Math.round(Math.random() * 255),
      state: true,
    };
  }

};
```

Real-world variant from `nl.klikaanklikuit-example` (bit strings instead of bytes, base class shared by several
signal ids):

```javascript
'use strict';

const { RFSignal } = require('homey-rfdriver');

module.exports = class RFSignalKlikAanKlikUit extends RFSignal {

  static FREQUENCY = '433';

  static commandToDeviceData(command) {
    return {
      address: command.address,
      channel: command.channel,
      unit: command.unit,
    };
  }

};
```

```javascript
'use strict';

const { RFUtil, RFError } = require('homey-rfdriver');
const RFSignalKlikAanKlikUit = require('./RFSignalKlikAanKlikUit');

// 26-bit address | 1 bit group | 1 bit state | 2 bits channel | 2 bits unit = 32 bits
module.exports = class RFSignalKlikAanKlikUitNew extends RFSignalKlikAanKlikUit {

  static ID = 'kaku-new';

  static commandToPayload({ address, group, state, channel, unit }) {
    if (typeof address !== 'string' || address.length !== 26) throw new RFError(`Invalid Address: ${address}`);
    if (typeof group !== 'boolean') throw new RFError(`Invalid Group: ${group}`);
    if (typeof state !== 'boolean') throw new RFError(`Invalid State: ${state}`);
    if (typeof channel !== 'string' || channel.length !== 2) throw new RFError(`Invalid Channel: ${channel}`);
    if (typeof unit !== 'string' || unit.length !== 2) throw new RFError(`Invalid Unit: ${unit}`);

    return [].concat(
      RFUtil.bitStringToBitArray(address),
      group ? 1 : 0,
      state ? 1 : 0,
      RFUtil.bitStringToBitArray(channel),
      RFUtil.bitStringToBitArray(unit),
    );
  }

  static payloadToCommand(payload) {
    return {
      address: String(payload.slice(0, 26).join('')),
      group: Boolean(payload.slice(26, 27)[0]),
      state: Boolean(payload.slice(27, 28)[0]),
      channel: String(payload.slice(28, 30).join('')),
      unit: String(payload.slice(30, 32).join('')),
    };
  }

  static createPairCommand() {
    return {
      address: RFUtil.generateRandomBitString(26),
      group: false,
      state: true,
      channel: RFUtil.generateRandomBitString(2),
      unit: RFUtil.generateRandomBitString(2),
    };
  }

};
```

### RFDriver

Extends `Homey.Driver`.

| Member | Kind | Description |
| --- | --- | --- |
| `static SIGNAL` | `RFSignal` subclass | Must extend `RFSignal` or `getRFSignal()` throws `Signal class does not extend RFSignal` |
| `onRFInit()` | override | Use **instead of** `onInit()` |
| `onRFUninit()` | override | Use **instead of** `onUninit()` |
| `getRFSignal()` | async | Returns the app-wide cached `RFSignal` instance (one per signal, shared by all drivers) |
| `enableRX(listener)` / `disableRX(listener)` | async | Register/unregister an RX listener on the shared signal |
| `cmd(command, props)` / `tx(payload, props)` | async | Delegate to the signal |
| `onPair(session)` | provided | Routes `showView` to the handlers below |
| `onPairRFReceiverLearn(session)` | provided | For `rf_receiver_learn`: builds `createPairCommand()`, answers `tx` and `createDevice` |
| `onPairRFTransmitter(session)` | provided | For `rf_transmitter_learn`: listens for the first RX command and emits `createDevice`; also installs `showView` (to track whether its own view is active) and `disconnect` (to unregister the RX listener) handlers |
| `onPairIRRemoteAdd(session)` | provided | For `rf_ir_remote_add`: emits `createDevice` with only a `uuid` |

`RFDriver#onInit` also sets `this.manifest` and reads the localized driver name (`this.homey.__(manifest.name)`)
— that name becomes the paired device's name.

```javascript
'use strict';

const { RFDriver } = require('homey-rfdriver');
const MySignal = require('../../lib/MySignal');

module.exports = class MyDriver extends RFDriver {

  static SIGNAL = MySignal;

  async onRFInit() {
    this.log('MyDriver initialised');
  }

};
```

Device `data` created by the built-in pairing handlers:

| Handler | `data` |
| --- | --- |
| `onPairRFReceiverLearn` | `{ uuid, ...commandToDeviceData(command), copiedFromRemote: false }` |
| `onPairRFTransmitter` | `{ uuid, ...commandToDeviceData(command), copiedFromRemote: true }` |
| `onPairIRRemoteAdd` | `{ uuid }` — IR remotes have no unique data, so a UUID v4 is the identity |

### RFDevice

Extends `Homey.Device`.

| Member | Kind | Description |
| --- | --- | --- |
| `static RX_ENABLED` | boolean, default `false` | `true` for transmitter devices (Homey listens) |
| `static CAPABILITIES` | object | capability id ⇒ command name / value map / function |
| `onRFInit()` | override | Use **instead of** `onInit()` |
| `onRFUninit()` | override | Use **instead of** `onUninit()` |
| `onRFDeleted()` | override | Use **instead of** `onDeleted()` |
| `onCommandMatch(command)` | override | Decide whether an RX command belongs to this device |
| `onCommand(command, { isFirst })` | override | Called for every matching RX repetition |
| `onCommandFirst(command, flags)` | override | Called once per new transmission (`isFirst === true`) |
| `onRX(command, { isFirst, ...flags })` | internal | The RX listener registered on the driver; runs `onCommandMatch` then `onCommand` / `onCommandFirst` |
| `onCapability(capabilityId, value, opts = {})` | provided | The generic capability listener |

`onInit` registers a capability listener for every key in `CAPABILITIES` **that the device actually has**
(`hasCapability`), then enables RX when `RX_ENABLED === true` **or** `getData().copiedFromRemote === true`.
`onUninit` disables RX again under exactly the same condition (the capability listeners are not
unregistered — Homey tears the device instance down anyway).

The three accepted `CAPABILITIES` value shapes:

| Shape | Example | Effect |
| --- | --- | --- |
| Object (value map) | `onoff: { 'true': 'POWER_ON', 'false': 'POWER_OFF' }` | Looks up `String(value)`; missing key ⇒ `Missing Command For Capability <id> Value: <value>`; then `driver.cmd(command, { device })` |
| String | `volume_up: 'VOLUME_UP'` | `driver.cmd('VOLUME_UP', { device })` |
| Function | `onoff: ({ value, data }) => ({ ...data, state: !!value })` | Called with `this` = the device and one object `{ value, opts, data }`; the returned command goes to `driver.tx(command, { device })` |

Anything else throws `Invalid Capability Listener: <id>`.

```javascript
'use strict';

const { RFDevice } = require('homey-rfdriver');

module.exports = class MyDevice extends RFDevice {

  static RX_ENABLED = false; // true for transmitter devices

  static CAPABILITIES = {
    // 'data' is this device's data object
    onoff: ({ value, data }) => ({
      address: data.address,
      state: value === true,
    }),
  };

};
```

Receiving side (a remote): `onRX(command, { isFirst })` → `onCommandMatch(command)` → when it matches,
`onCommand()` runs for every repetition and `onCommandFirst()` runs only on the first one.

```javascript
'use strict';

const RFDeviceBase = require('./RFDeviceBase');

module.exports = class MyRemote extends RFDeviceBase {

  static RX_ENABLED = true;

  // The default implementation deep-compares the WHOLE data object — override it.
  async onCommandMatch(command) {
    const { address } = this.getData();
    return address === command.address;
  }

  async onCommandFirst(command) {
    await this.setCapabilityValue('onoff', command.state).catch(this.error);
    await this.homey.flow
      .getDeviceTriggerCard('button_pressed')
      .trigger(this, {}, {})
      .catch(this.error);
  }

};
```

### RFUtil

| Method | Signature | Example |
| --- | --- | --- |
| `deepEqual(a, b)` | boolean | `util.isDeepStrictEqual` |
| `generateRandomBitString(length)` | string | `RFUtil.generateRandomBitString(6)` |
| `bitStringToBitArray(str)` | `number[]` | `'011201'` ⇒ `[0,1,1,2,0,1]`; throws on non-integers |
| `bitArrayToString(arr)` | string | `[0,1,1,2,0,1]` ⇒ `'011201'` |
| `bitArrayToNumber(arr)` | number | `[0,1,1,0,0,1]` ⇒ `25`; throws on non-binary values |
| `numberToBitArray(n, length)` | `number[]` | `(25, 6)` ⇒ `[0,1,1,0,0,1]`; left-padded, truncated to `length` |
| `generateUUIDv4()` | string | Used for device `data.uuid` |

**Gotcha:** despite the JSDoc example, `generateRandomBitString(length)` returns a **string** (it `join('')`s),
which is exactly what `bitStringToBitArray` expects.

### RFError

`class RFError extends Error` — nothing more. Throw it from `commandToPayload` / `payloadToCommand` so RF
protocol failures are distinguishable from other errors.

## Pairing templates

Copy the `.html` files from `node_modules/homey-rfdriver/pair/` (or
<https://github.com/athombv/node-homey-rfdriver/tree/master/pair>) into `/drivers/<driver_id>/pair/`. The file
name **is** the view id used in `driver.compose.json`; these are plain custom views, not `template` views.

| File / view id | Used for | Reads `options` | Front-end behaviour |
| --- | --- | --- | --- |
| `rf_transmitter_learn.html` | Transmitter (remote) — imitate | `title`, `instruction` | Waits; on `createDevice` from the driver calls `Homey.createDevice()` then `Homey.done()` |
| `rf_receiver_learn.html` | Receiver — generate a new address | `title`, `instruction`, `copyFromRemote` | If `copyFromRemote` is set, shows a link that calls `Homey.showView('rf_transmitter_learn')` |
| `rf_receiver_add.html` | Receiver — confirm | `instruction` | Emits `tx` on load (device should react), then ⨯ = `Homey.prevView()`, ✓ = `Homey.emit('createDevice')` + `Homey.createDevice()` + `Homey.done()` |
| `rf_ir_remote_learn.html` | IR remote — instruction screen | `title`, `instruction` | Purely informational; navigate `next` to `rf_ir_remote_add` |
| `rf_ir_remote_add.html` | IR remote — create | — | On `createDevice` from the driver calls `Homey.createDevice()` then `Homey.done()` |

All five templates render a `image.svg` from the **same pair folder** as a background
(`background: url(image.svg)`), sized `80vw × 80vw`. **Ship `/drivers/<driver_id>/pair/image.svg`** or the view
shows an empty box. `rf_receiver_add.html` styles its buttons with the Homey style-library classes
`hy-button` / `hy-button-primary`.

### Transmitter (a remote imitated by Homey)

```json
{
  "rf433": { "satelliteMode": true },
  "pair": [
    {
      "id": "rf_transmitter_learn",
      "options": {
        "title": { "en": "Press any button" },
        "instruction": { "en": "Press any button on your device." }
      }
    }
  ]
}
```

### Receiver (Homey generates an address and the device learns it)

```json
{
  "pair": [
    {
      "id": "rf_receiver_learn",
      "navigation": { "next": "rf_receiver_add" },
      "options": {
        "title": { "en": "Press the button..." },
        "instruction": { "en": "Press the button on your device once." }
      }
    },
    {
      "id": "rf_receiver_add",
      "options": {
        "instruction": { "en": "Did the device turn off and on?" }
      }
    }
  ]
}
```

### Receiver + copy from an existing remote

For built-in modules that are hard to reach, let the user choose between generating a new signal and copying an
existing remote. Copy `rf_transmitter_learn.html` in as well and add the `copyFromRemote` option:

```json
{
  "pair": [
    {
      "id": "rf_receiver_learn",
      "navigation": { "next": "rf_receiver_add" },
      "options": {
        "title": { "en": "Press the button..." },
        "instruction": { "en": "Press the button on your device once." },
        "copyFromRemote": { "en": "Copy from Remote" }
      }
    },
    {
      "id": "rf_transmitter_learn",
      "navigation": { "prev": "rf_receiver_learn" },
      "options": {
        "instruction": { "en": "Press any button on your remote." }
      }
    },
    {
      "id": "rf_receiver_add",
      "navigation": { "prev": "rf_receiver_learn" },
      "options": {
        "instruction": { "en": "Did the device turn off and on?" }
      }
    }
  ]
}
```

A device paired this way gets `data.copiedFromRemote === true`, which makes `RFDevice#onInit` enable RX even
when `RX_ENABLED` is `false` — so the physical remote and Homey stay in sync.

### `satelliteMode`

`driver.compose.json` accepts `rf433` and `infrared` objects, each with a single boolean `satelliteMode`
(there is no `rf868` object in the schema):

```json
"rf433":    { "satelliteMode": true }
"infrared": { "satelliteMode": true }
```

Both are defined identically and completely in the app manifest schema — `satelliteMode` is the **only**
property either object has:

```json
"rf433":    { "type": "object", "properties": { "satelliteMode": { "type": "boolean" } } },
"infrared": { "type": "object", "properties": { "satelliteMode": { "type": "boolean" } } }
```

Consequences of that exact wording:

- No `required` — `"rf433": {}` is valid, and the whole object may be omitted.
- No `additionalProperties: false` — the schema will not *reject* a typo'd key inside `rf433`/`infrared`, it
  just ignores it. Do not rely on `homey app validate` to catch a misspelled `sateliteMode`.
- There is **no `rf868` driver object** in the schema at any level. An 868 MHz driver gets
  `"connectivity": ["rf868"]` and nothing else; a `"rf868": { … }` key is not schema-defined (it passes only
  because driver objects have no `additionalProperties: false` either).
- Unlike `matter`, the validator does **not** cross-check these objects against `connectivity`: a driver may
  carry `rf433`/`infrared` without the matching `connectivity` entry, and vice versa. (`matter` is the only
  protocol object `homey-lib` links to `connectivity` in both directions.)

Set it as shown in the official examples. Note that neither of Athom's two example apps
(`nl.klikaanklikuit-example`, `com.lg.ir-example`) actually sets it — it is optional.

**Gotcha:** `satellite_mode_` is one of `homey-lib`'s reserved driver-**settings** id prefixes (alongside
`homey:`, `zw_`, `zb_`, `mtr_`, `thread_`, `zone_`, `energy_`, `homekit_`). Never name your own driver setting
`satellite_mode_*` — Homey owns that namespace for the settings it generates for satellite-mode drivers.

## Infrared

Infrared is a `Signal` like 433/868 MHz; everything above applies, with these differences:

- Directory `/.homeycompose/signals/ir/<id>.json`, `static FREQUENCY = 'ir'`, permission `homey:wireless:ir`,
  `"connectivity": ["infrared"]`.
- `carrier` is the **modulation frequency in Hz**, not a radio band: min 30000, default 38000, max 45000.
- The `modulation` object is **not** validated for `ir` (no `modulationValidator` runs); `dutyCycle` (30–70) is.
- Pairing uses `rf_ir_remote_learn` → `rf_ir_remote_add`; there is no address to learn, so the device identity
  is a UUID v4.

### Raw IR signal definition

```json
{
  "carrier": 37900,
  "sof": [4535, 4465],
  "eof": [590],
  "words": [
    [590, 590],
    [590, 1690]
  ],
  "prefixData": [1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
  "interval": 1000,
  "sensitivity": 0.5,
  "repetitions": 5,
  "minimalLength": 32,
  "maximalLength": 32,
  "cmds": {
    "POWER_ON":     [1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0],
    "POWER_OFF":    [0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0],
    "CHANNEL_UP":   [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1],
    "CHANNEL_DOWN": [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1]
  }
}
```

Note the 16-bit `prefixData` prepended to every 16-bit command, giving the 32 bits demanded by
`minimalLength`/`maximalLength`.

### Driver manifest, signal, driver and device

```json
{
  "name": { "en": "TV" },
  "class": "tv",
  "capabilities": ["onoff", "channel_up", "channel_down"],
  "images": {
    "small": "/drivers/my_driver/assets/images/small.jpg",
    "large": "/drivers/my_driver/assets/images/large.jpg"
  },
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

```javascript
// /drivers/<my_driver>/signal.js
'use strict';

const { RFSignal } = require('homey-rfdriver');

module.exports = class MySignal extends RFSignal {

  static FREQUENCY = 'ir';
  static ID = 'my_signal';

};
```

```javascript
// /drivers/<my_driver>/driver.js
'use strict';

const { RFDriver } = require('homey-rfdriver');
const MySignal = require('./signal.js');

module.exports = class MyDriver extends RFDriver {

  static SIGNAL = MySignal;

};
```

```javascript
// /drivers/<my_driver>/device.js
'use strict';

const { RFDevice } = require('homey-rfdriver');

module.exports = class MyDevice extends RFDevice {

  static CAPABILITIES = {
    onoff: {
      true: 'POWER_ON',
      false: 'POWER_OFF',
    },
    channel_up: 'CHANNEL_UP',
    channel_down: 'CHANNEL_DOWN',
  };

};
```

The real `com.lg.ir-example` device maps six capabilities to prontohex commands:

```javascript
static CAPABILITIES = {
  onoff: { true: 'POWER_ON', false: 'POWER_OFF' },
  volume_mute: 'MUTE_TOGGLE',
  volume_up: 'VOLUME_UP',
  volume_down: 'VOLUME_DOWN',
  channel_up: 'CHANNEL_UP',
  channel_down: 'CHANNEL_DOWN',
};
```

`RFDevice#onInit` special-cases these: when the capability is `volume_up` or `volume_down` **and** the device
also has `volume_mute`, it sets `volume_mute` to `false` before sending the command.

### Prontohex

Homey natively supports Prontohex definitions for IR.

| Attribute | Description | Remark |
| --- | --- | --- |
| `cmds` | Static commands | The Prontohex command string definition |
| `type` | Type of Signal | Set to `prontohex` to enable prontohex mode |

Plus `toggleCmds` (same string format) and `repetitions` (1–255), both accepted by the validator.

```json
{
  "type": "prontohex",
  "cmds": {
    "ON":  "0000 0073 0000 000D 0020 0020 0040 0020 0020 0020 0020 0020 0020 0020 0020 0020 0020 0040 0020 0020 0020 0020 0020 0020 0020 0020 0020 0020 0020 0CA4",
    "OFF": "0000 0073 0000 000C 0020 0020 0040 0020 0020 0020 0020 0020 0020 0020 0020 0020 0020 0040 0020 0020 0020 0020 0020 0020 0040 0040 0020 0CA4"
  }
}
```

```javascript
'use strict';

const Homey = require('homey');

class MyApp extends Homey.App {

  async onInit() {
    const philipsSignal = this.homey.rf.getSignalInfrared('philips');
    await philipsSignal.cmd('ON');
  }

}

module.exports = MyApp;
```

- The **carrier encoded in the Prontohex string overrides** the `carrier` in the signal's radio specification.
  The real `com.lg.ir-example` signal is therefore just `{"type": "prontohex", "repetitions": 10, "cmds": {…}}`
  with no `carrier` at all.
- String format: space-separated 4-hex-digit words, an **even** number of them, at least four
  (`/^(([0-9a-f]{4}\s?){2}){2,}$/i`). Mixed case is fine.
- A prontohex signal has no `words`/`sof`/`eof`, so it can only send predefined commands — `Signal#tx()` has
  nothing to encode.

### Receiving IR

`SignalInfrared` inherits `enableRX()`, `disableRX()` and the `payload` / `cmd` events from `Signal`, so RX is
exposed by the API. In practice IR capture is much less common: Athom's own IR example app states *"For now it
is not possible to listen to signals of the remote."* Use the devtools raw capture to obtain IR timings, then
express them as a raw `words`/`sof`/`eof` definition or as prontohex.

## Gotchas

- **Only enable RX when you need it.** Receiving is performance intensive and the filter bandwidth is shared
  with every other app on the Homey. Register the signal only when devices are paired; set `"txOnly": true` on
  transmit-only signals. `RFSignal#registerRXListener` already ref-counts this for you.
- **`RFDevice#onCommandMatch` does not work out of the box for devices paired with the built-in templates.**
  Its default implementation is `RFUtil.deepEqual(this.getData(), commandToDeviceData(command))`, but
  `onPairRFReceiverLearn` / `onPairRFTransmitter` store `data` as
  `{ uuid, ...commandToDeviceData(command), copiedFromRemote }` — the extra `uuid` and `copiedFromRemote` keys
  make the deep comparison fail. Override `onCommandMatch` and compare only the protocol fields (that is what
  `nl.klikaanklikuit-example` does: `return address === command.address;`).
- **`RFDriver.getRFSignal()` caches on `Homey.app`, keyed by `Signal.TYPE`** — but `RFSignal` declares
  `FREQUENCY`, not `TYPE`, so the frequency dimension of the cache key is always `undefined`. Two signal
  classes that share an `ID` across different frequencies collide in that cache. Keep signal ids unique across
  `433`/`868`/`ir` within one app.
- **`RFSignal`'s constructor reads `Homey.manifest.signals[FREQUENCY][ID]`.** If the signal file is missing,
  the id is misspelled, or you forgot to rebuild `app.json` from `.homeycompose`, driver init throws a
  `TypeError` on undefined instead of a helpful message.
- **Do not override `onInit`/`onUninit`/`onDeleted` in `RFDriver`/`RFDevice`.** The library implements them;
  override `onRFInit`, `onRFUninit` and `onRFDeleted` instead, or the RX registration and capability wiring
  never runs.
- **If you override `onPair` in an `RFDriver`, call `await super.onPair(session)` first**, otherwise the
  library's `showView` router — and therefore the `rf_receiver_learn` / `rf_transmitter_learn` /
  `rf_ir_remote_add` handlers — is never installed. Note that `onPairRFTransmitter` itself installs a second
  `showView` handler to track whether its view is active.
- **`modulation` is all-or-nothing:** `type`, `baudRate`, `channelSpacing` and `channelDeviation` must all be
  present, or `homey app validate` fails with `invalid_modulation_properties`.
- **`packing` requires exactly two words.** With three or more words (multi-level encoding such as
  `kaku-new-dim`) validation fails.
- **`rxTimeout` is milliseconds; every other timing field is microseconds.** `modulation.channelSpacing` only
  has an effect when `rxTimeout > 0`.
- **868 MHz is Homey Pro (2016—2019) only.** Newer Homey Pro models and Homey Bridge have no 868 MHz radio; a
  `rf868` driver is rejected on the `cloud` platform by `homey app validate`.
- **`agc` is transmit-only** — it is ignored while receiving but prepended when transmitting.
- **Manchester mode changes the meaning of every timing array.** Once `manchesterUnit` is present, `words`,
  `agc`, `sof`, `toggleSof` and `eof` must contain `1`/`0`, and the allowed value range collapses from
  5–32767 to 0–1.
- **Ship `pair/image.svg`.** All five pairing templates hard-code `background: url(image.svg)` relative to the
  driver's pair folder.
- **The doc example's `enableRX(); …; disableRX(); tx(); cmd();` sequence in `onInit` is illustrative, not a
  pattern.** Disabling RX immediately after enabling it defeats the purpose; structure the lifecycle around
  `RFDevice`/`RFDriver` instead.
- Payload arrays are **word indexes**, not bytes — unless `packing` is enabled, in which case they are bytes
  `0x00`–`0xFF`. `Signal#tx()` also accepts a `Buffer`, which `RFSignal#tx()` passes straight through without
  calling `commandToPayload`.

## Example apps

- <https://github.com/athombv/nl.klikaanklikuit-example> — 433 MHz, 87 drivers, three signals (including
  multi-level word sets), shared `lib/` base classes. Its 87 drivers use two pairing shapes —
  30 × `rf_transmitter_learn` alone, 51 × `rf_receiver_learn` → `rf_receiver_add` (6 declare no `pair` at
  all and fall back to Homey's default `list_devices` flow). It does **not** use
  `copyFromRemote`, does not set `satelliteMode`, and does not set `connectivity` on any driver — so treat
  the receiver+copy flow above as the library README's recipe, not as something this app demonstrates.
- <https://github.com/athombv/com.lg.ir-example> — Infrared, prontohex `cmds`, `rf_ir_remote_learn` /
  `rf_ir_remote_add`, capability-to-command map.

## Sources

- <https://apps.developer.homey.app/wireless/rf-433mhz-868mhz>
- <https://apps.developer.homey.app/wireless/infrared>
- <https://apps.developer.homey.app/the-basics/app/permissions>
- <https://apps.developer.homey.app/advanced/homey-compose>
- <https://apps.developer.homey.app/advanced/custom-views/custom-pairing-views>
- <https://apps.developer.homey.app/guides/homey-cloud>
- <https://apps-sdk-v3.developer.homey.app/ManagerRF.html>
- <https://apps-sdk-v3.developer.homey.app/Signal.html>
- <https://apps-sdk-v3.developer.homey.app/Signal433.html>
- <https://apps-sdk-v3.developer.homey.app/Signal868.html>
- <https://apps-sdk-v3.developer.homey.app/SignalInfrared.html>
- <https://athombv.github.io/node-homey-rfdriver/> (`RFSignal`, `RFDriver`, `RFDevice`, `RFUtil`, `RFError`)
- <https://github.com/athombv/node-homey-rfdriver> (`/pair` templates)
- <https://github.com/athombv/node-homey-lib> (`lib/Signal` — the validator `homey app validate` runs)
