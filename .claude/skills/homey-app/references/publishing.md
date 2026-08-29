# App Store Guidelines & Publishing

Everything needed to get a Homey app through certification: the complete App Store Guidelines
reproduced with Athom's original numbering, the reviewer-only rules that are enforced but not on the
public page, the exact asset dimensions, the publish → build → test → certification → live lifecycle,
versioning, the Verified Developer programme, and a pre-submission self-check.

`homey app validate --level publish` passing is **necessary but not sufficient**. Almost none of the
guidelines below are machine-checked — they are enforced by `homey app review` (Athom's AI reviewer,
shipped in `homey-lib`) and by a human reviewer at Athom.

---

## Lifecycle at a glance

| Stage | Who does it | Command / place | Result |
| --- | --- | --- | --- |
| Validate | you | `homey app validate --level publish` | machine-checkable manifest/asset errors |
| Self-review | you | `homey app review` | blocker/warning/suggestion findings + verdict |
| Publish a build | you | `homey app publish` | version bump, changelog, upload → **Draft** build |
| Release to Test | you | [tools.developer.homey.app](https://tools.developer.homey.app) → *Apps SDK* → *My Apps* | build reachable at the test URL only |
| Submit for certification | you | same dashboard | Athom review, up to 2 weeks |
| Live | Athom approves, you release | same dashboard | visible in the public Homey App Store |

Key CLI/dashboard URLs (emitted by the CLI itself):

- App overview: `https://tools.developer.homey.app/apps/app/<APP_ID>` (`homey app manage` opens it)
- The build you just uploaded: `https://tools.developer.homey.app/apps/app/<APP_ID>/build/<BUILD_ID>`
- Test channel: `https://homey.app/en-us/app/<APP_ID>/test/`

---

## Before you submit your app

From the guidelines page, verbatim in substance:

- Test your app for any crashes or bugs.
- Double check for any spelling errors.
- Check that your app follows the guidelines below.
- Provide Athom with the necessary devices to test your app *(for Verified Developers only)*.

Apps submitted for review for the first time need to be **complete** — icons, images and required
texts must be present. Once approved, the app can be released to the Homey App Store by the
developer.

---

## The complete Homey App Store Guidelines

Source of the public rules: <https://apps.developer.homey.app/app-store/guidelines>.

Rules marked **[reviewer-only]** come from Athom's own reviewer material shipped inside the
`homey-lib` npm package at `lib/AIReviewer/data/` (`guidelines.md`, `checklist.md`, `templates.md`).
`guidelines.md`'s own header calls its extras *"known drift (pending developer-docs sync) — enforced by
reviewers but not yet on the public site"*. They are: the donation-links clarification in 1.3, the
default-rocket-icon rule in 1.5, and the two sections **1.14 SDK Version** and **1.15 Permissions**,
which do not exist on the public page at all.

Rules marked **[reviewer-only checklist]** come from `checklist.md` instead — the reviewers' working
companion. Some of its items (the app-ID substring rule, the 4-word boundary, the Platform item,
driver-level "required" items) have no numbered section on the public page; they are filed here under
the nearest guideline number, or as **1.13a** where none applies.

## 1. Design

A coherent look and feel in both the Homey App Store and Homey's various user interfaces is essential
to how users experience Homey. The overall appearance of each submitted app is a key factor in the
review process.

### 1.1. App name

A clear app name is essential for new customers to find your app and understand what it's about. In
most cases, the app's name should be exactly the same as the brand name.

1. In case your app supports a specific brand, use the brand name for your app. **Company names are
   not allowed.**
2. You **may not use the trademarks Homey or Athom** in your app's name.
3. You **may not include protocol names** (Zigbee, Z-Wave, 433 MHz, Infrared etc.) in your app's name.
4. **Names that are longer than 4 words are not allowed.** An app name should be short and simple, one
   that immediately clarifies what the app does.

| Do | Don't |
| --- | --- |
| Philips Hue | Lights by Philips Hue |
| tado° | Tado Gmbh |

**[reviewer-only] closed list of prohibited terms** (`homey-lib` guidelines.md 1.1 + prompt
interpretation conventions). Only these count as a 1.1 violation:

- `Homey` or `Athom` as a **whole word / CamelCase token / dotted segment**.
- Protocol / product-category names, closed set: `Zigbee`, `Z-Wave`, `433 MHz` / `433MHz`,
  `Infrared` / `IR`, `BLE` / `Bluetooth Low Energy`, `Thread`, `Matter`.
- 5 or more whitespace-separated words. **Exactly 4 words is at the limit and allowed.** Hyphenated
  pairs count as one word.

Generic English descriptors — "Monitor", "Controller", "Hub", "Manager", "Assistant", "Connector",
"Tools", "Dashboard", "Studio" — are **not** prohibited.

**Trademark matching is whole-word only, never substring:**

| Violation | Not a violation |
| --- | --- |
| `io.athom.weather` (dotted segment) | `io.home-assistant` (`home` ≠ `Homey`) |
| `com.example.homey-companion` (hyphenated token) | app name `"Home Assistant"` |
| `MyHomeyApp` (CamelCase token) | `com.athletic.tracker` (`Ath` ≠ `Athom`) |
| app names `"Homey Plus"`, `"Homeyscript"`, `"AthomTools"` | `com.weather.athens` |

**App ID [reviewer-only checklist]:** the app **id** must not contain "Athom" or "Homey" → reject.
Apps approved in the past that contain either name are **grandfathered**.

### 1.2. Description

The description field is a required field to provide your app with a catchy tagline to grab the
user's attention. The description is shown beneath your app's name and above the readme in the App
Store. In case your app supports devices by a specific brand, consider using their slogan as your
description.

1. Using your app's name or repeating text from the readme in your description is **not allowed**.
2. The description field is not meant for an extensive text. Provide an engaging one-liner that
   highlights the purpose of your app. In case your app supports devices by a specific brand,
   consider using their slogan as your description.
3. All apps in the Homey App Store add support for something to Homey, that is why they are there. So
   avoid descriptions such as these:
   - "Adds support for Sonos"
   - "Integrates Philips Hue with Homey"
   - "Control your Ikea devices with the Ikea app"

What we'd like to see:

- Philips Hue — "Transform the way you experience light"
- Ikea — "Create the right atmosphere for every mood"
- Rituals — "Your home never smelled smarter"
- Heimdall — "Turn Homey into a surveillance system"

### 1.3. Readme

The app's `readme.txt` must be used to provide an engaging summary of your app's purpose. Describe why
your app's integration is useful in day-to-day life.

1. Keep the text short and concise, **one to two paragraphs tops**. The text should be pleasant to
   read, so stick to single line spacing and avoid unnecessary indentations. Headers or titles are not
   needed.
2. In order to keep your readme short, **do not list all the different features, capabilities and Flow
   cards** available in your app. Give credit to contributors in your App Manifest instead of your
   readme.
3. The readme text is displayed in plain text, any **Markdown format in your readme is not allowed**
   and will not be rendered.
4. **URLs in the readme are not allowed.** See section [URLs](#18-urls) for more information.
5. **Don't create a changelog in your readme.** In case you are updating your app, use the Changelog
   functionality of the Homey App Store. When publishing your app, Homey will ask you "What's new?"
   and a `.homeychangelog.json` file is automatically created in the root directory of your app.
   Describe your changes clearly, so your users know what has changed.

**[reviewer-only] donation-links clarification** (`homey-lib` guidelines.md 1.3): the "no URLs" rule
"includes donation/sponsorship links (PayPal, Ko-fi, Buy Me a Coffee, GitHub Sponsors, etc.); use the
`contributing.donate` field in `app.json` instead." Per the reviewer prompt, `contributing.donate` in
`app.json` is the **only allowed place** for donation info — a donation link in `README.txt`, in
`settings/*.html`, in in-app UI, or anywhere else in `app.json` is a rejection trigger.

**[reviewer-only] scope of 1.3.** The "no URLs" and "no changelog" rules apply **strictly to
`README.txt` per locale**. These are explicitly *not* violations:

| Location | URLs allowed? | Changelog-shaped text allowed? |
| --- | --- | --- |
| `README.txt` / `README.<lang>.txt` | no | no |
| `README.md` (GitHub-only, filtered out of review) | yes | yes |
| `CHANGELOG.md` at repo root | yes | yes |
| `settings/*.html` | yes | — |
| `drivers/<id>/pair/*.html` | yes | — |
| source code / comments | yes | yes |
| `app.json` `homepage`, `support`, `bugs`, `source`, `contributing.donate` | yes | `version` field is fine |

### 1.4. Images

Images are a great way to uplift your app's experience. Both the app and driver images are prominently
visible on the Homey App Store page, so make sure they are visually compelling. Use brand images if
this is possible. If you want to create custom images, keep it clean, simple and **do not use a Homey
or Homey logo in the images**. Make sure the image is clear, well designed and recognizable for the
respective brand or purpose.

#### 1.4.1. Format & resolutions

All images must be provided in either `.jpg` or `.png` format. Each chosen image should be included in
two resolutions. **Small and large are mandatory**, but you can add a third: XLarge for better
resolution on large or high-resolution screens.

Resolutions for the **app image**:

- Small **250 x 175**
- Large **500 x 350**
- XLarge **1000 x 700**

Resolutions for the **driver images**:

- Small **75 x 75**
- Large **500 x 500**
- XLarge **1000 x 1000**

The guidelines page also links a downloadable *Homey App Store template for Sketch*.

#### 1.4.2. App images

The app image should be a lively, visually appealing image that represents the purpose of your app.
Lifestyle images and brand images are great examples and are strongly encouraged.

**Images that consist of a single flat shape or icon on a plain, monochrome or transparent background
are not approved.** For example, a black shape on a white background will look flat and unappealing in
the Homey App Store, rather than inviting.

- Avoid a logo as app image.
- Avoid clipart or icon type of images.
- Avoid images that solely contain Android or iOS app examples.

> **Do not use the Homey logo, name or device in any of your images.**

#### 1.4.3. Driver images

In case your app has drivers, make sure to provide **individual images for each driver**. A driver
image **should have a white background** and a recognizable picture of the device it supports.

- Don't use the app image as a driver image.
- Don't use your app icon as a driver image.

### 1.5. App Icons

The app icon is one of the first things users will see when they search for your app in the Homey App
Store. It is therefore important that it is immediately recognisable and representative of your app or
brand.

The app icon is a clean, **vector-based** drawing that should accurately represent the brand or purpose
of your app. It should be recognisable at small sizes, and have a **transparent background**. So do not
use images, filled illustrations, gradients, or background colours in your app icon. Submitting a
filled image or illustration as an icon will cause it to appear as a solid shape, which is not
recognisable at small sizes and **will not be approved**.

Key points:

- If your app supports a specific brand, use the company's brand icon.
- Icons must have a transparent background.
- Always use the **full canvas (960x960px)** so the icon is displayed properly.
- Don't use a driver icon as your app icon.
- Don't use a background color in your icon.

**[reviewer-only] default rocket icon** (`homey-lib` guidelines.md 1.5 + checklist:icon): *"The default
Homey rocket icon (the placeholder shipped by `homey app create`) is not allowed as the final app
icon."* → **reject**.

### 1.6. Driver icons

Driver icons are visible once an app has been installed and the user adds a device to Homey. **Each
individual driver your app supports must have its own unique icon** that clearly represents the device.

An icon is a clean, vector-based drawing that accurately represents the device it belongs to. It should
be recognisable at small sizes, so use the full canvas, and have a transparent background. Icons are
drawn using lines and shapes to depict the form of the device, with dimension added through the use of
angles and line work.

Avoid using images, filled illustrations, gradients, or background colours. Submitting a filled image
or illustration as an icon will cause it to appear as a solid shape, which is not recognisable and will
not be approved.

Things to keep in mind when drawing your own driver icons:

1. The canvas size should be **960x960px**.
2. Always use the full canvas, so the icon is displayed properly.
3. Where possible, **use an angle from the right side** rather than a front facing view, to add
   dimension to the icon.
4. Icons must have a **transparent background**.
5. **Do not re-use the app icon for your drivers.**
6. Make sure to use the correct line width.

Don'ts: don't use driver images as an icon; don't re-use the app's icon for your drivers; don't use a
background color.

> If you do not have suitable icons for your app or drivers Athom can provide a handmade icon. Request
> one by creating an issue in the [Homey Vectors](https://github.com/athombv/homey-vectors-public)
> repository, including as much information about your app as possible and pictures of the devices.

### 1.7. Brand color

The property `brandColor` is a **mandatory** value which needs to be added to your App Manifest. The
defined color is used as a backdrop for your icons in e.g. Flows, Add devices and the App Store.

Both your app icon and driver icons must be **clearly visible against the background color**. Use brand
colors to complement the icons and make them more recognizable.

### 1.8. URLs

Offer extra help or information to your users, simply by adding a URL to your App Manifest. Each URL
will be visible as a clickable link, at the lower section of your app page. See
`references/app-and-manifest.md` for the manifest fields.

**[reviewer-only] checklist:urls** — every URL present in `app.json` must resolve:

| Field | Rule |
| --- | --- |
| `bugs.url` | if present, verify it works |
| `homepage` | if present, must be a working URL |
| `support` | if present, must be a working URL. **Mandatory for Official (verified) apps** |
| `source` | if present, must be a working URL to the app source |
| `homeyCommunityTopicId` | if present, must resolve to a working Homey Community Topic page |

### 1.9. Flow

Flow is an essential part of Homey. Incorporate When-And-Then Flow cards, so that users can integrate
your app in their automated home environment.

#### 1.9.1. Titles

Flow card titles need to be short and clear, so the user instantly knows what the trigger, condition or
action does. **Device names should not be mentioned in the title. Don't add the When, And, Then
statements to the title. Do not use parentheses in Flow titles.**

|  | Do | Don't |
| --- | --- | --- |
| When | Unknown face is detected | Netatmo Presence detected an unknown face. |
| And | Is !{{on\|off}} | And the light is off |
| Then | Lock door | Going to lock the door |

#### 1.9.2. Formatted titles

Flow cards may contain arguments. To integrate an argument into the title of the Flow card the
`titleFormatted` property must be used. Make sure that the title is still straightforward and clear
with the arguments incorporated.

```json
"title": { "en": "Run a script" },
"titleFormatted": { "en": "Run [[Script]]" }
```

**Example**: a remote or wall switch can have multiple buttons, with several actions to trigger them —
pressed once, twice, or a long press. Instead of creating several Flow cards for all these triggers,
one Flow card can be created containing several arguments.

```json
"title": { "en": "Button was pressed" },
"titleFormatted": { "en": "[[buttontype]] button was pressed [[scene]]" }
```

#### 1.9.3. Hint

In case the function of the Flow card is not obvious use the `hint` property to give additional
information.

```json
"title": { "en": "Battery state changed" },
"hint": { "en": "This card starts a Flow when a change in the battery state is observed." }
```

### 1.10. Widget Previews

The Widget Preview is a simplified representation of your Widget. If your app includes a Widget, the
preview will be displayed on the App Store page of your app as well as in the Widget picker within the
Homey Mobile app. The preview should give users an idea of the Widget's appearance without revealing
too much detail. **Both light and dark mode versions should be provided.**

Athom highly recommends the
[Figma Template](https://www.figma.com/community/file/1392859749687789493/widget-previews-template).
The template includes the proper color styles and shadows, automatically generates a dark mode version,
provides examples, and ensures export in the correct dimensions (**1024x1024**).

**Don't use screenshots or provide over detailed designs:**

- Don't include text.
- Use simple shapes.

**Use the color styles provided in the Figma template for basic elements:**

- Don't use the same colors as the Widget picker background.
- Try not to use too many different colors.
- Use the shadow styles provided in the template.

**Don't use a background color or image:**

- Previews should have a **transparent background**.

### 1.11. Language & Translations

English is the required language for your app, however additional languages are also allowed and
encouraged.

1. Make sure your app doesn't have any typos, language or spelling errors. **Your app will be rejected
   if spelling errors are found.**
2. Consistency in translations is vital. A partially translated app is very confusing for users. So
   avoid sporadic translations throughout the app. If the description is translated to a certain
   language, the readme should be translated to that language as well. In case you translate Flow
   cards, make sure to translate **all** Flow cards, device settings, capabilities, etc.

### 1.12. Dependencies

Apps may communicate to other apps using App-to-App communication to enhance an app's functionality. It
is however **not permitted to make one app fully dependent on another app**. An app's core
functionality must always work standalone.

It is also **not allowed to publish an app which does not add any value by itself**, but is meant to be
used by other apps. In such scenarios, embed such an app's functionality directly.

### 1.13. Account

Your app will be published with your Athom account. A developer account name **cannot contain emojis,
special characters or inappropriate language**. Account names can be adjusted via
[accounts.athom.com](https://accounts.athom.com).

If your account has the verified developer badge, the account name should be the **name of the company
publishing the app**. Examples:

- *Bosch-Siemens Home Connect* published by **Home Connect GmbH**
- *Frient* published by **frient A/S**
- *Yale Access* published by **Yale Access**
- *Plugwise* published by **Plugwise B.V.**

### 1.13a. Platform — **[reviewer-only checklist, no public guideline section]**

The reviewer checklist carries a *Platform* item for both new and update submissions, with only the
bare guidelines URL as its reference (there is no numbered public section for it):

- `"platforms"` is **usually `["local"]` only**.
- Official (verified) apps *should ideally* support **both local and cloud**, unless cloud is
  technically infeasible → `should`/`ideally` wording, so warning/suggestion severity, never a
  blocker.
- `local` = works on Homey Pro. `cloud` = works on Homey Cloud.
- Same item on the driver: *"usually local; Official apps add cloud unless infeasible."*
- **Update submissions:** if `cloud` is **newly added** to an existing app, that app has just become
  Official — **the app must be tested before approval**. Expect a slower review and a request for
  sample devices or a screen recording.

### 1.14. SDK Version — **[reviewer-only, not on the public page]**

Verbatim from `homey-lib` `lib/AIReviewer/data/guidelines.md`:

- New apps **must** be built on Homey Apps SDK v3. Submissions on older SDK versions will be rejected.
- Existing apps already live on an older SDK may keep their SDK, but new development should target v3.

The reviewer checklist restates it as: *"New apps **must** use SDK v3. Reject if SDK v2 or older."*

### 1.15. Permissions — **[reviewer-only, not on the public page]**

Verbatim from `homey-lib` `lib/AIReviewer/data/guidelines.md`:

- Permissions in `app.json` must be **justified by the app's core functionality**. Do not request more
  than the app actually needs.
- The `manager:homey:api` permission is a broad grant and is only appropriate for apps whose primary
  purpose requires programmatic access to Homey (e.g. tooling, automations that inspect Homey state).
  It is **not needed to control devices via drivers**, and requests that are not clearly justified will
  be rejected.

Reviewer checklist: *"If `manager:homey:api` is requested, the app must be a tool whose primary
function justifies it. It is **not** needed to switch on a light bulb. Reject if usage doesn't justify
the permission."* For an **update** submission the checklist softens this: a newly added permission is
*"verify with the developer why — flag for follow-up rather than auto-reject."*

> **Naming caution:** the reviewer documents misspell this permission two different ways —
> `manager:homey:api` (in `guidelines.md` 1.15 and `checklist.md`) and `homey.manager.api` (in
> `templates.md`). The actual value in `app.json` — the one `homey-lib` validates against — is
> **`homey:manager:api`**. The complete permission enum (`homey-lib`
> `assets/app/permissions.json`, 13 entries) is:
> `homey:manager:geolocation`, `homey:manager:ledring`, `homey:manager:media`,
> `homey:manager:speech-input`, `homey:manager:speech-output`, `homey:manager:api`,
> `homey:wireless:433`, `homey:wireless:868`, `homey:wireless:ir`, `homey:wireless:zwave`,
> `homey:wireless:zigbee`, `homey:wireless:nfc`, `homey:wireless:ble`, plus `homey:app:<app.id>` for
> app-to-app.

`homey-lib` validation behaviour for permissions (mechanical, runs in `homey app validate`):

| Permission | Behaviour |
| --- | --- |
| `homey:app:com.athom.homeyscript` | hard error — `Forbidden permission` |
| `homey:manager:api` | at `publish`/`verified`: warning — *"using the homey:manager:api permission will require a more thorough review. It may take longer than usual to review your app."* |
| `homey:manager:speech-input` | at `verified`: hard error *"Unsupported permission … please remove any speech input related functionality"*; otherwise a warning |
| anything not in the enum and not `homey:app:` | hard error `Invalid permission` |

## 2. Legal

### 2.1. Duplicate

#### 2.1.1. App

As a community developer, you are part of a community that is working towards a common goal of making
home automation accessible to everyone. This means we must keep things simple. **Ideally there is only
one app per brand or concept in the App Store**, because too many apps with the same purpose will
confuse users.

Before submitting your app, please check the Homey App Store to see if a similar app already exists. If
it does, you are encouraged to reach out to the existing developer first and explore the possibility of
working together, for example by contributing via a Pull Request.

If collaboration is not possible, you are still welcome to submit your app. However, please make sure
to **clarify in your submission why collaboration was not possible**, and why a separate app is
necessary. **Submissions that resemble an existing app without any clarification will be rejected.**

In case an existing app is no longer maintained and a new alternative has been submitted, Athom may
reach out to the original developer to discuss transferring the app or removing it from the App Store.

**[reviewer-only] exception:** *"a community app **and** a verified app for the same brand may
coexist."*

#### 2.1.2. Code

There is a lively and open Homey community, with many developers that keep their source code open for
others to view, or even contribute. **Copying or using code created by fellow developers without
consent is an infringement on their intellectual property.**

If your code is based on source code that is not your own, always ask for permission and **give credit
to the original source in the app manifest**. If at any point it is revealed that code has been used
without consent your app will be at risk of being removed from the Homey App Store.

### 2.2. Explicit content

Apps with adult content (e.g. pornography) are **not allowed**.

### 2.3. Compensation

**Apps that require payment for partial or all functionality are not allowed. Apps should be free of
charge for all users.** You are encouraged to add
[donation options](https://apps.developer.homey.app/the-basics/app/manifest#contributing) to your app.

Apps whose goal is to connect to a service that requires payment (for example a Premium-tier for a
smart thermostat), and the payment happens on the integration product's end, **can still be offered
for free** in the Homey App Store.

## 3. After app submission

Once an app has been submitted for certification, the app will be reviewed according to the various
criteria mentioned in these guidelines. **Athom holds the right to make the final decision** if an app
will be approved or removed from the Homey App Store.

### 3.1. Review duration

After your app has been submitted, your submission will be reviewed. **This process can take up to 2
weeks.** Within this time an app can either be approved, receive feedback, or Athom might inquire more
information before proceeding with the review. If an app meets all the requirements upon submission,
the review process can go much faster.

The review process for a new app created by a Verified Developer can take longer, depending on the size
of the app and all its capabilities.

### 3.2. Testing your app (Verified Developers only)

It is imperative that an app created by a Verified Developer is of the highest quality and delivers a
great user experience. An app created by a Verified Developer will be thoroughly tested before its
approval.

In order for the app to be tested by the testing team, **make sure to provide a few sample devices
prior to your submission**. For cloud apps a **demo account** can be an option as well. If devices are
too large or not available, consult with Athom to determine how to proceed with the review.

Athom expects an app to have been thoroughly tested **before** it is submitted for certification. Once
the app has been published to **Test** in the [Developer Tools](https://tools.developer.homey.app/apps)
a testing URL will be available which can be shared with beta testers:

```
https://homey.app/en-us/app/APP.ID/test/
```

Make sure to test the following:

- [ ] Use the device controls in Homey to update the device state.
- [ ] Update the device advanced settings in Homey (if available).
- [ ] Create Flows with custom Flow cards (if available) and trigger/execute the Flow.
- [ ] Manually adjust device state outside of the Homey app, and verify that state is updated in Homey.
      For example when manually setting a temperature on your thermostat, the set temperature should be
      updated in Homey.

An app will be tested not only on correct functionality, but also user experience and usability. So
make sure that:

- [ ] The pairing instructions for all drivers are accurate and clear.
- [ ] Error messages are understandable.
- [ ] Flow card titles are intuitive and understandable.
- [ ] Label and hint texts for driver advanced settings are clear and understandable.
- [ ] Every aspect of the app has been accurately translated.

Apps with a history of high quality submissions will often experience a faster review process.

**[reviewer-only] checklist:** if devices cannot be provided (too large, etc.), the developer **must
instead submit a screen recording** of: the pairing process, available device controls, device advanced
settings (if available), app settings (if available), and custom Flow cards (if available).

### 3.3. Feedback

Any findings or feedback during the review process will be shared with the developer and **is expected
to be implemented**.

### 3.4. Removal

Apps may be hidden or removed from the Homey App Store if they are no longer compatible with Homey,
functioning correctly, or actively maintained.

Apps that have not received an update in **two years or more** may be considered abandoned. However, an
app will not automatically be marked as abandoned solely based on its last update date. If the app is
still functioning correctly, it will remain available in the Homey App Store.

An app may be hidden or removed if one or more of the following applies:

- The app has not been updated in two years or more and/or is no longer functioning correctly
- The app has not been updated in two years or more and a working alternative has been submitted by
  another developer

If your app has been marked as abandoned Athom will let you know. If you are no longer able to maintain
your app, consider transferring it to another developer.

---

## The app-image vs driver-image background contradiction

These two rules look contradictory because they *are* different rules for different assets. Get them
the wrong way round and you fail certification twice.

| Asset | Background rule | Source | Severity if wrong |
| --- | --- | --- | --- |
| **App image** (`/assets/images/{small,large,xlarge}.png`) | **NOT white, NOT transparent.** The brand-background colour must fill all edges. White borders/letterboxing is a rejection trigger. A flat shape on a plain/monochrome/transparent background is "not approved". | guideline 1.4 / 1.4.2 + `checklist:images` | **blocker** |
| **Driver image** (`/drivers/<id>/assets/images/{small,large,xlarge}.png`) | **SHOULD be white or transparent**, depicting the device itself. White is preferred; transparent is accepted. | guideline 1.4.3 + `checklist:driver-images` | **warning**, never blocker — only flagged when the background is clearly something else (coloured, photographic, scene-based) |

Mnemonic: **app image = marketing photo (rich, edge-to-edge). Driver image = product shot (cut out on
white).**

---

## Exact asset requirements

### File layout

```
/assets/icon.svg                                  app icon      (required, validated to exist)
/assets/images/small.png                          250 x 175     (required at --level publish)
/assets/images/large.png                          500 x 350     (required at --level publish)
/assets/images/xlarge.png                         1000 x 700    (optional)
/drivers/<id>/assets/icon.svg                     driver icon
/drivers/<id>/assets/images/small.png             75 x 75       (required at --level publish)
/drivers/<id>/assets/images/large.png             500 x 500     (required at --level publish)
/drivers/<id>/assets/images/xlarge.png            1000 x 1000   (optional)
/widgets/<id>/preview-light.png                   1024 x 1024
/widgets/<id>/preview-dark.png                    1024 x 1024
/README.txt                                       store readme  (required by `homey app publish`)
/README.<lang>.txt                                translated readmes
/.homeychangelog.json                             changelog, keyed by version then language
```

### Dimensions (enforced exactly by `homey-lib` at `--level publish`)

| Asset | small | large | xlarge |
| --- | --- | --- | --- |
| App image | **250 × 175** | **500 × 350** | 1000 × 700 (optional) |
| Driver image | **75 × 75** | **500 × 500** | 1000 × 1000 (optional) |

`homey app validate --level publish` reads the file header bytes and the real pixel dimensions. A
mismatch is a hard error: `Invalid image size (WxH) …\nRequired: WxH`. Allowed extensions are `.jpg`,
`.jpeg`, `.png` — and the magic bytes must match (`FF D8` for JPEG, `89 50 4E 47` for PNG), so a PNG
renamed to `.jpg` fails with `Invalid image`.

Only `small` and `large` are validated/required; `xlarge` is optional and the AI reviewer is explicitly
told **not** to emit a finding when `xlarge` is absent.

### Icons (SVG)

| Property | App icon | Driver icon |
| --- | --- | --- |
| Path | `/assets/icon.svg` | `/drivers/<id>/assets/icon.svg` |
| Canvas | 960 × 960, use the **full** canvas | 960 × 960, use the **full** canvas |
| Background | transparent | transparent |
| Style | vector line/shape drawing; no images, filled illustrations, gradients, background colours | same, plus prefer a right-side angle over front-facing, correct line width |
| Reuse | may not be a driver icon | may not be the app icon |
| Default rocket placeholder | not allowed **[reviewer-only]** | — |

`homey app validate` only checks that `/assets/icon.svg` **exists** (case-sensitively). Everything else
about icons is a human/AI judgement call.

What the AI reviewer explicitly **does not** flag on icons (so don't over-engineer for it):
canvas size / `viewBox` / aspect-ratio; "each driver has a unique icon"; consistent line widths;
"visible against `brandColor`". App-icon/driver-icon reuse is only flagged when the SVG files are
**byte-equivalent or near-byte-equivalent** — shared visual style is not a violation.

### `brandColor`

- Required at `--level publish`; the value must be **exactly `#RRGGBB`**. The manifest schema pins
  `minLength: 7` and `maxLength: 7`, so the 3-digit shorthand `#RGB` is rejected even though the
  schema's regex alternation still mentions it.
- Hard-validated for brightness: `tinycolor(color).getBrightness() <= 184`. Too bright fails with
  *"The color defined in `brandColor` is too bright. **Icons are rendered white**, so choose a darker
  color that has enough contrast."*

### Widget previews

- `1024 × 1024`, **both** `preview-light.png` and `preview-dark.png` per widget.
- Transparent background, no text, simple shapes, few colours, not the same colour as the widget-picker
  background, not a screenshot.
- Use the [Figma template](https://www.figma.com/community/file/1392859749687789493/widget-previews-template)
  — it exports at the right size and generates the dark variant.
- See `references/widgets.md` for the manifest side.

---

## README.txt rules

The store readme is `/README.txt` in the **app root** — plain text, not `README.md`.

| Rule | Detail |
| --- | --- |
| Filename | `README.txt`. `homey app publish` aborts with *"Missing file `/README.txt`. Please provide a README for your app. The contents of this file will be visible in the App Store."* |
| Translations | `README.<languageCode>.txt`, e.g. `README.nl.txt`. The code is checked against `homey-lib`'s `getAppLocales()` — the **full ISO 639-1 two-letter list** (~180 codes, `ab`…`zu`), not just Homey's UI languages. Unrecognised codes (and anything longer than two letters, e.g. `README.en-US.txt`) are silently skipped at publish time and simply never reach the store. |
| Length | one to two paragraphs, tops |
| Formatting | plain text only; Markdown is not rendered and is a rejection trigger; single line spacing, no extra blank lines, no headers/titles |
| URLs | none — including donation/sponsorship links |
| Changelog | none — use `.homeychangelog.json` |
| Feature lists | no lists of features, capabilities or Flow cards |
| Setup instructions | not needed — pairing views should guide the user |
| Credits | credit contributors in `app.json` `contributors`, not the readme |
| Accuracy | must match what the app actually does — a readme describing a removed feature is misleading |

**Gotcha:** the public guidelines page writes the filename lowercase (`readme.txt`) but the CLI reads
`README.txt` case-sensitively on a case-sensitive filesystem. Always use `README.txt`.

**Gotcha:** `README.md` is *not* the store readme. It is filtered out of the AI review entirely
("README.md is GitHub-facing and routinely contains markdown, URLs and donation links — none of which
are store-rejection triggers there"). Markdown, URLs and donation links in `README.md` are fine.

---

## What actually gets rejected

Every explicit **reject** trigger from Athom's reviewer checklist (`homey-lib`
`lib/AIReviewer/data/checklist.md`), grouped by area. Each line is a testable statement — if it is
true of your app, expect a blocker.

### App ID

- The app `id` contains the whole word "Athom" or "Homey" (dotted segment, hyphenated token, or
  CamelCase token) — unless the app was approved before and is grandfathered.

### App name

- The name contains "Homey" or "Athom" as a whole word.
- The name is a **company** name rather than a brand name.
- The name is **5 or more words** (exactly 4 is allowed).
- The name contains a protocol name: Zigbee, Z-Wave, 433 MHz/433MHz, Infrared/IR, BLE/Bluetooth Low
  Energy, Thread, Matter.
- *(Driver names follow the same rule: "Homey" in a driver name is not allowed.)*

### Readme (`README.txt` per locale)

- The readme contains a **changelog**.
- The readme contains **Markdown syntax**.
- The readme and the description are **identical or near-identical**.
- The readme contains a **donation link**.
- The readme contains any **other URL** (those belong in `app.json`: bugs/support/homepage/source).

### Description

- The **app name is** the description.
- The description is identical to the readme.
- The description is obvious filler such as "Adds support for …".

### App icon

- The app has **no icon**.
- The icon is the **default rocket** placeholder.
- The app icon is the **same file** as a driver icon (byte-equivalent).
- *(Transparent background is "should" → warning, not a blocker.)*

### Driver icons and driver metadata

- A driver has **no icon** (*"Driver icon is required"* — checklist:driver-icon).
- A driver has **no name** (*"Required"* — checklist:driver-name).
- A driver name contains "Homey".
- A driver icon is **byte-equivalent** to `assets/icon.svg` (app-icon reuse).
- *(An icon that merely does not resemble the driver, or lacks a transparent background, is "should"
  → warning. "Each driver has a unique icon" is explicitly **not** a reviewer trigger.)*

### App images

- The app has **no image**.
- The image has a **white or transparent background** (e.g. a black shape on white).
- The image contains the **Homey name or logo** — the literal text "Homey"/"Athom" (blocker), or an
  unmistakable reproduction of the multi-coloured rainbow ring from the Homey brand mark (blocker;
  warning if genuinely uncertain).
- The image is **pixelated / upscaled / not clear**.
- The image is a **logo only**, clipart, or an iOS/Android device mockup holding the Homey interface.

Explicitly **not** violations: a stylised letter "H" in any font or colour; a single-colour, gradient
or two-tone circular shape; a colourful graphic that merely shares the Homey aesthetic.

### Driver images

- A driver has **no image**.
- The driver image is the **app image**.
- The driver image is the **app/driver icon** rather than a photo of the device.
- Multiple drivers **reuse the same image**.
- Background is clearly neither white nor transparent → **warning**, not a blocker.
- Text that is part of the device or its packaging is **fine** — only composited marketing overlay text
  is a concern, and only as a warning.

### Widget previews

- The preview is **missing or empty** (a preview is required).
- Only one of light/dark is present.
- The preview is a **screenshot** of the widget.
- The preview **contains text**.
- All widgets share an **identical** preview.

### Permissions

- `homey:manager:api` is requested by an app whose primary function does not justify it (it is not
  needed to switch on a light bulb).

### Duplicate

- The submission resembles an existing App Store app **with no clarification** of why collaboration was
  not possible.
- Exception: a community app and a verified app for the same brand may coexist.

### SDK

- A **new** app on SDK v2 or older.

### Flow cards

- A card has **no title** (*"Title: required"* — checklist:flow), or the title is too long.
- Titles start with "When", "And" or "Then".
- Titles contain spelling errors.
- Custom Flow cards duplicate the standard cards Homey auto-generates for a system capability.
- *(The checklist also has the reviewer validate argument **types and titles**, the readability of
  `titleFormatted` with the arguments substituted in, and the presence of a `hint` explaining what
  the card does — those are "make sure"/"should" items → warnings. `titleFormatted` missing is a
  `homey-lib` warning at `--level publish` and a hard error at `--level verified`.)*

### Capabilities (double UI components)

- A driver uses both `alarm_battery` **and** `measure_battery`.
- A driver uses both `windowcoverings_state` **and** `windowcoverings_set`.

### Other

- The user has to **manually enter an IP address** — use `ManagerDiscovery` instead.

### Verified/Official apps additionally

- The publishing account name is not the company name.
- No `support` URL or e-mail in the manifest.
- No sample devices provided and no screen recording supplied instead.
- On an **update**: `cloud` was newly added to `platforms` (the app has just become Official) and the
  app has not been tested — the checklist requires testing before approval.

---

## Severity model

The reviewer parses guideline verbs literally. This is how a rule's wording maps to a severity, and
how severities map to the overall verdict.

| Wording in the guideline / checklist | Severity | Meaning |
| --- | --- | --- |
| "must", "is required", "is mandatory", "is not allowed", "will be rejected", "always reject", an explicit **reject** trigger | `blocker` | you will be rejected |
| "should", "avoid", "make sure", "we encourage"; partial translations; minor visual issues; "verify with developer" items | `warning` | approve-with-feedback; you are expected to fix it |
| "ideally", "consider"; optional best practice | `suggestion` | advisory |

Verdict derivation is deterministic:

| Findings present | Verdict |
| --- | --- |
| any `blocker` (of either kind) | `reject` |
| `kind: review` warnings, no blockers | `request_changes` |
| only suggestions, only `kind: code` warnings/suggestions, or nothing | `approve` |

Two tracks of findings exist. `kind: "review"` = guideline/checklist/security/SDK violations — these
drive the verdict and are what gets sent to you. `kind: "code"` = code-quality observations
(`console.log` instead of `this.log`, leaked listeners, class name not matching filename, hardcoded
values, dead code, missing non-English translations). Code findings are **advisory and never affect the
verdict** — except a code **blocker**, which is reserved for a real runtime bug (crash on startup, a
broken SDK lifecycle handler, a reference to a non-existent property that throws).

Borderline visual/interpretive calls are deliberately biased toward being flagged as `warning` rather
than skipped — expect some false positives you can push back on. Three checks keep the opposite rule
("when in doubt, skip") because a wrong flag would be embarrassing: SVG byte-equivalence (app-icon vs
driver-icon reuse), pixel-resolution mismatches, and Homey/Athom substring-vs-whole-word matches.

Consistency rules that shape the output you get back:

- **One rule + one violation = one finding**, however many places it occurs. The same violation across
  several drivers/files/images is emitted **once**, with every locus enumerated in `evidence` — not
  once per driver. Two *different* rules on the same file are two findings (a `README.txt` with both a
  changelog and a donation link produces two).
- **Stable ordering**: findings come back in guideline order (1.1 before 1.4 before 2.x), blockers
  before warnings before suggestions within a section.
- **Severity is derived from wording**, and *"if you cannot point to the wording that drove the
  severity, downgrade by one level"* — so a rule you cannot quote lands one notch lower than you might
  expect.
- **Evidence must quote verbatim.** Image findings without a concrete visual description (what shape,
  what colour, where in the frame) are not allowed to be emitted at all — if you get "the image does
  not meet the requirements", that is out-of-spec output, not a real finding.
- The verdict is **recomputed from the findings** by `homey-lib` itself (`_deriveVerdict`), so the
  model's own `verdict` field cannot drift from the severities it emitted.

---

## Reviewer feedback templates

These are the actual sentences the Homey review team sends (`homey-lib`
`lib/AIReviewer/data/templates.md`). Recognise the wording and you know exactly which rule you tripped.
The AI reviewer is instructed to reuse them **verbatim** as the base of every `explanation`, replacing
only the `[PLACEHOLDER]` slots with real values, and to keep the App Store Guidelines URL each template
embeds. The complete set, by category (the trailing
`https://apps.developer.homey.app/app-store/guidelines#…` links are elided here — every template that
carries one keeps it):

**Permissions**
> "Your app uses the `homey.manager.api`, could you clarify why your app uses this permission?"

**Duplicate apps**
> "After reviewing your submission, we have found that your app is similar to an already existing app,
> namely \[EXISTING APP NAME] by \[EXISTING DEVELOPER NAME] (https://homey.app/a/\[APP ID]). Ideally we
> would like to see one app per \[brand/concept] in the App Store, as this makes it clear and easy for
> end-users.
>
> We noticed that your app \[LIST A DIFFERENCE]. It would be great if this could be integrated with the
> existing \[EXISTING APP NAME] app, so all features and functions are available within one app.
> Therefore we would like to encourage you to reach out to \[EXISTING DEVELOPER NAME] and collaborate,
> or submit a Pull Request to their repository.
>
> If you have already tried to collaborate with \[EXISTING DEVELOPER NAME] and were unable to reach an
> agreement, or if you feel a separate app is absolutely necessary, please resubmit and clarify your
> reasoning. We are happy to discuss this further and see how we can move forward.
>
> If you need any help getting in touch with \[EXISTING DEVELOPER NAME], please do not hesitate to
> reach out."

**App ID**
> "Your app's ID contains the name Athom/Homey, this is not allowed. Please adjust your app ID."

**App name**
> "Your app's name contains the company/brand name Athom/Homey, please change your app's name. An
> app's name should be easy to remember and hint to what your app does."
>
> "Your app's name \[LIST MISTAKE], please change your app's name. An app's name should be easy to
> remember and hint to what your app does."

**Readme** — nine templates
> "Your app's readme contains an unclear description of your app. Please add more information for your
> users so they know what your app can do for them. Keep it short and simple, preferably one or two
> paragraphs."
>
> "Your app's readme starts with the app name as a title. Please remove the title from the readme. The
> name of your app will be shown at the top of your App Store page."
>
> "Your app's readme starts with a header that contains the same text as in your Description. Please
> remove this from the readme or change the Description field. The Description will be shown above your
> readme in the App Store, therefore repetition should be avoided."
>
> "Your app's readme contains a list of all the Flow options. Please delete this from the readme. The
> available Flow cards will be visible on your app page in the new section Flow Cards."
>
> "Your app's readme contains a lot of technical information and is too long. The readme is meant to
> provide a short summary of the app's features and its purpose. Ideally the text is around 1 to 2
> paragraphs. If you wish to provide additional information consider creating a Homey Community topic
> to which you can link in the App Manifest."
>
> "Your app's readme contains a donation URL, this is not allowed. Please remove this URL from the
> readme. You can add a donation button to the app.json which will appear as a clickable button on your
> App Store page."
>
> "In your app's readme there is a lot of white spacing between sentences/paragraphs. Please remove the
> extra white spacing, stick to a single white space per paragraph. This will make it easier to read
> for the user."
>
> "Your app's readme seems to be in \[LANGUAGE]. Please use English language in your main `readme.txt`
> and add a translated file `readme.[LANGUAGECODE].txt` to add \[LANGUAGE] translations to your app."
>
> "Your app's readme currently contains setup instructions. These are not needed in the readme, as the
> pairing views within the app should be clear enough to guide users through the setup process. The
> readme should be a short, engaging summary of the app's purpose in one to two plain text paragraphs."

**Description** — four templates
> "The text in your app's Description property (`app.json`) is not up to our standards, it's identical
> to your `readme.txt`. The description is shown above your readme in the App Store, therefore
> repetition should be avoided. Please sell your app in one short sentence, think of it as the slogan
> or tagline of your app."
>
> "The text in your app's Description property (`app.json`) is identical to your app's name. Please use
> the description property to describe your app's purpose in one short sentence. For example
> '\[GIVE EXAMPLE]'."
>
> "The text in your app's Description property (`app.json`) is not up to our standards. Please sell your
> app's purpose in one short sentence. Apps for a specific brand often use the brand slogan or tagline
> as the Description."
>
> "Your app's Description (`app.json`) is not up to our standards, avoid descriptions such as: 'Adds
> support for \[XXXXX]'. Please sell your app in one short sentence, think of it as the slogan or
> tagline of your app."

**URLs**
> "The \[TYPE] URL you specified is not working. Please enter a valid URL."
>
> "Please provide a support URL or e-mail address in the `homeycompose/app.json`."

**App icons**
> "Your app does not have an icon. Please add an icon that represents your app."
>
> "The app icon is \[LIST WHAT IS WRONG]. Please add an icon that represents your app; in case of a
> brand app consider using the logo for the icon."
>
> "The app icon is an image rather than an icon. This makes it appear as a solid shape and is therefore
> not recognizable. Please add an icon that represents your app; in case of a brand app consider using
> the logo for the icon."

**Driver icons**
> "Some of your app's driver icons are identical to the app icon. Please make sure each driver has its
> own icon so users can easily recognize the driver they need."
>
> "The driver icons do not meet our design standards. \[LIST WHAT IS WRONG] … Consider putting in a
> request for custom icons on the Homey Vector page."

**Images** (app + driver) — six templates
> "Your app's images contain the Homey logo; this is not allowed. Please make sure your images are
> visually appealing and represent your app."
>
> "Your app's images are mainly white with a black shape, unfortunately this won't look appealing in
> the Homey App Store. Please make sure your images are visually appealing and represent your app;
> consider using images similar to those used on the \[BRAND NAME] website."
>
> "Your app image is an image of the brand logo, this is not up to our standards. Please have a look at
> our App Store Guidelines and adjust the image accordingly."
>
> "Your driver images are identical to your app's image. Please provide a unique driver image that
> depicts the device or service it supports on a white background."
>
> "Your driver image shows the driver icon. Please provide a unique driver image that depicts the
> device it supports on a white background."
>
> "Your driver image does not have a white or transparent background. Please provide a unique driver
> image that depicts the device or service it supports on a white background."

**Flow** — six templates
> "Some of the Flow card titles could be improved. Keep them simple and to the point without making
> them too technical, for example: \[FLOW TITLE] should be \[IMPROVED TITLE]. In case you want to add
> more information about a Flow card's function, use the Hint field."
>
> "The formatted titles of your Flow cards can be improved; make sure the arguments are integrated in
> the formulation of the title. For example: \[FLOW TITLE] should be \[IMPROVED TITLE]."
>
> "The Flow card titles start with When, And or Then; this is not allowed. Please remove this from the
> title."
>
> "The Flow cards are missing the formatted titles. Please make sure to add formatted titles to your
> Flow cards."
>
> "Some of your app's Flow card titles contain spelling errors. Please adjust the spelling for the
> following Flow cards: \[LIST FLOW CARDS]."
>
> "Several Flow cards are duplicates. Since the system capability `[CAPABILITY]` has been used, Homey
> will automatically generate standard Flow cards. Please remove the additional custom flow cards
> \[LIST]."

**Widget previews** — four templates
> "Your Widget preview seems to be a screenshot of the Widget. This is not allowed."
>
> "Your Widget preview contains text. This is not allowed."
>
> "The Widget preview for all widgets seems to be identical. Please make sure each preview represents
> the widget itself."
>
> "The Widget preview seems to be missing or empty. A widget preview is required."

**Other**
> "It seems that users need to manually enter their IP address in your app. This is no longer allowed.
> Please use the `ManagerDiscovery` to make it easy for your users to pair their devices."
>
> "Device \[NAME] uses both the `alarm_battery` and `measure_battery` capability; this is not allowed.
> This will result in a double UI component. Please only use one of the two capabilities."
>
> "Device \[NAME] uses both the `windowcoverings_state` and `windowcoverings_set` capability; this is
> not allowed. This will result in a double UI component. Please only use one of the two capabilities."

**No reply follow-up**
> "Since we did not receive an answer to our earlier question we have decided to reject your submission
> for now. However, you can resubmit the app for a new review any time. If you do, please be sure to
> include a short explanation addressing the earlier points raised in our earlier message."

---

## `homey app review` — the pre-submission self-check

`homey app review` runs Athom's own AI reviewer (`AIReviewer` from `homey-lib`) locally against the
same guidelines, checklist and templates the human reviewer uses. Run it before every submission.

```bash
export OPENAI_API_KEY="sk-…"       # or ANTHROPIC_API_KEY for an anthropic/… model
homey app review                    # defaults: --type new --model openai/gpt-5.4
homey app review --type update      # for an app that is already live
homey app review --json             # machine-readable output
homey app review --verbose          # token counts, timings
```

| Flag | Values | Default | Notes |
| --- | --- | --- | --- |
| `--type` | `new`, `update` | `new` | selects the NEW-app or UPDATE section of the reviewer checklist |
| `--model` | `<provider>/<model>` | `openai/gpt-5.4` | must contain a `/`. Supported providers: `openai` (needs `OPENAI_API_KEY`), `anthropic` (needs `ANTHROPIC_API_KEY`). Any **other provider** is a hard error (`Unsupported provider "x". Supported: openai, anthropic.`), as is a missing API key. A supported provider with a **different model** only prints the warning *"⚠ Using "…" — Athom's official review uses openai/gpt-5.4. Results may differ."*, and that warning is suppressed under `--json`. |
| `--json` | boolean | `false` | emits the raw result object instead of the pretty terminal render |
| `--verbose`, `-v` | boolean | `false` | prints model, duration, and `in/out/cacheRead/cacheCreate` token counts |

Behaviour:

- Must be run from an app directory (an `app.json` must exist, or pass `--path`).
- **Exit code is `1` when the verdict is `reject`**, `0` otherwise — usable as a CI gate.
- Output is grouped by category; each finding shows severity, title, explanation, `evidence`, and
  `ref` (the guideline section or `checklist:<key>`).

### `.homeyreview.md` — app-specific reviewer instructions

If a file named `.homeyreview.md` exists in the app root, its contents are loaded as
*"App-specific reviewer instructions"* and injected into the review. Use it to encode context the
reviewer would otherwise flag:

```markdown
<!-- .homeyreview.md -->
This app is grandfathered for an app id containing "athom" — it was approved in 2019.

The rainbow-ish arc in assets/images/large.png is the vendor's own brand mark, not the Homey
brand ring; this was confirmed with the review team.

A separate app from "Acme Classic" is justified: the two device generations use incompatible
cloud APIs and the Acme Classic maintainer declined a PR (see issue #212).
```

How the reviewer treats it:

- If it **relaxes** a rule, the rule is not flagged.
- If it **adds** checks, they become additional `kind: review` findings.
- If it **conflicts** with the official guidelines, the guidelines win unless the instructions
  explicitly say to override.
- If absent, review runs purely against the guidelines and checklist.

### What the reviewer actually sees

Source files it reads (so anything here is fair game for a finding): `.js .ts .mjs .cjs .jsx .tsx
.json .md .txt .css .html .xml .yaml .yml .svg .env .gitignore .npmignore .eslintrc .prettierrc`, plus
extensionless and dotfiles. **Skipped**: `node_modules`, `.git`, `.github`, `dist`, `build`,
`.homeybuild`, any file over 100 KB, any file containing a NUL byte, and `README.md`. SVGs are limited
to `assets/icon.svg`, `drivers/<id>/assets/icon.svg` and `widgets/<id>/assets/icon.svg` — per-driver
icon *collections* (`drivers/<id>/assets/icons/*.svg`) are deliberately excluded. Files are sorted
`app.json` → `package.json` → any other `app.json` → the rest.

Images it attaches for visual review:

| Label | File |
| --- | --- |
| `reference: homey-brand-icon` (and any other `reference: …`) | bundled Athom brand assets from `homey-lib` `lib/AIReviewer/data/references/` — **not** part of your submission |
| `app imageLarge (target 500×350)` | `manifest.images.large` |
| `app imageSmall (target 250×175)` | `manifest.images.small` |
| `app imageXLarge (target 1000×700, optional)` | `manifest.images.xlarge` |
| `driver "<id>" imageLarge (target 500×500)` | each driver's `images.large` |
| `widget "<id>" preview-light` | `/widgets/<id>/preview-light.png` |
| `widget "<id>" preview-dark` | `/widgets/<id>/preview-dark.png` |

The `reference:` blocks are the visual anchor for the "no Homey name or logo in the image" rule: the
prompt describes `reference: homey-logo` as the rainbow ring **plus** the "Homey" wordmark and
`reference: homey-brand-icon` as the rainbow ring alone, and forbids emitting any finding *against* a
reference image. A match must reproduce the rainbow ribbon in the Homey brand colours
(red → orange → yellow → green → blue → purple) forming a ring.

Note that `homey app review` **never sends a driver's `imageSmall`** — only `imageLarge` per driver —
so a 75×75 problem will not be caught locally.

Limits: **5 MB per image**, **20 MB total** — oversized assets error out before the request is sent.
Accepted image extensions for attachment: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`.

Athom's server-side pipeline can additionally pass a **"Similar live apps in the store"** JSON block
(brand-name token matches) that drives the duplicate/`similarity` findings; the CLI does not populate
it, so `homey app review` locally will under-report duplicate-app risk.

Finding shape (from the `submit_review` tool schema; `kind`, `severity`, `category`, `title` and
`explanation` are required, `guidelineRef` and `evidence` are optional):

```json
{
  "verdict": "approve | request_changes | reject",
  "findings": [
    {
      "kind": "review | code",
      "severity": "blocker | warning | suggestion",
      "category": "manifest | code_quality | sdk_usage | drivers | security | flow_cards | localization | documentation | description | images | markdown | brand_color | changelog | duplicate_urls | similarity | other",
      "title": "Short, imperative summary",
      "explanation": "Why it is a problem and what to do",
      "guidelineRef": "1.1 | 1.4.3 | checklist:duplicate | security | sdk",
      "evidence": "file path / manifest field / asset reference"
    }
  ]
}
```

---

## Publishing: publish → build → test → certification → live

### 1. Validate

```bash
homey app validate                    # --level defaults to "publish" in the CLI
homey app validate --level publish
homey app validate --level verified
```

| Validation level | Description |
| --- | --- |
| `debug` | Used during development. Various app manifest properties, such as `images`, `brandColor`, and `category` are optional at this level. |
| `publish` | Your app needs to pass this level to be published to the Homey App Store for Homey Pro. |
| `verified` | If you are a verified app developer your app needs to pass this level. Required for Homey Cloud. Adds requirements such as `platforms`, `connectivity`, and `support` in your manifest. |

What `--level publish` adds over `debug` (mechanical, from `homey-lib`):

- `category` is required and must be one of: `lights`, `video`, `music`, `appliances`, `security`,
  `climate`, `tools`, `internet`, `localization`, `energy`.
- `images` is required on the app **and** on every driver, files must exist with exact dimensions and
  matching magic bytes.
- `brandColor` is required and must pass the brightness check (`<= 184`).
- Drivers using `measure_battery` / `alarm_battery` must declare `energy.batteries` (or
  `energy.homeBattery` / `energy.electricCar`).
- No symlinked modules in `node_modules` (i.e. no leftover `npm link`).
- Python apps with `pythonPackages` need cross-platform venvs under `python_packages/<platform>/`.

What `--level verified` adds on top:

- `platforms` and `support` are required on the app manifest.
- `platforms` and `connectivity` are required on **every** driver.
- Every non-device Flow-card argument requires a `title`.
- `titleFormatted` is **required** on every Flow card (a warning at `publish` level).
- `homey:manager:speech-input` becomes a hard error.

### 2. Publish a build

```bash
homey app publish
```

In one run the CLI:

1. Warns if the git working tree has **uncommitted changes** and asks whether to continue.
2. Prints the guidelines URL and requires you to confirm *"I have read the Homey App Store
   guidelines"*.
3. Offers a version bump — **Patch / Minor / Major** (or keep the current version), writing `version`
   into `app.json` and `.homeycompose/app.json`.
4. Runs `preprocess` (Homey Compose) and then `validate` at level `verified` if your account has the
   `app_developer_trusted` role, otherwise `publish`. Invalid → abort.
5. Prompts **"(Changelog) What's new in \<App\> v\<x.y.z\>?"** if `.homeychangelog.json` has no `en`
   entry for this version, and writes it.
6. Reads `/README.txt` plus every `README.<lang>.txt` whose language code is a recognised app locale.
7. Creates a build on the App Store API, uploads the packed archive, and prints
   `Visit https://tools.developer.homey.app/apps/app/<APP_ID>/build/<BUILD_ID> to publish your app.`
8. Optionally commits (and tags) the version bump / changelog to git.

Headless mode: set `HOMEY_HEADLESS=1` to skip the interactive prompts — the uncommitted-changes
confirmation, the guidelines confirmation and the version-bump wizard are all skipped. Because the
version bump is skipped, **headless publish never bumps the version for you**: run `homey app version
patch|minor|major` first, or the upload will collide with an already-published version. A missing
changelog for the version is a hard error in this mode
(`Missing changelog for vX.Y.Z, and running in headless mode.`).

Files excluded from the uploaded archive come from `.homeyignore` (plus the CLI's default ignore
rules).

### 3. Promote the build in the Developer Dashboard

Go to <https://tools.developer.homey.app>, tap *Apps SDK* and choose *My Apps* (or run
`homey app manage`). Each build moves through **Draft → Test → Live**:

| Stage | Who sees it | How you get there |
| --- | --- | --- |
| **Draft** | only you | default state of every uploaded build |
| **Test** | anyone with the test link `https://homey.app/en-us/app/<APP_ID>/test/` | *Release to Test* in the dashboard. No certification needed. |
| **Certification** | Athom reviewers | *Submit for certification*. Up to 2 weeks. |
| **Live** | all Homey users, public App Store | after approval, released by you |

**Apps that have never been released to the Homey App Store need to be certified before becoming
publicly available.** If you want a **Test**-only release of a brand-new app, **disable the "publish
directly after approval" checkbox** when submitting for certification.

### Visibility on the App Store overview page

The Homey App Store overview page shows categories in which apps are sorted. Only the best, most
popular and visually appealing apps are shown there. To get featured, make sure the app not only works
great but also looks amazing: a catchy Description, a beautiful App Image, a great Icon.

### Automating in GitHub Actions

Athom publishes three Marketplace Actions:

- <https://github.com/marketplace/actions/homey-app-validate>
- <https://github.com/marketplace/actions/homey-app-update-version>
- <https://github.com/marketplace/actions/homey-app-publish>

`homey app create` can scaffold them (`homey-app-validate.yml`, `homey-app-version.yml`,
`homey-app-publish.yml`); `homey app add-github-workflows` adds them to an existing app. See
`references/ecosystem-and-ci.md`.

---

## Versioning and `.homeychangelog.json`

### Semver

The version of your app must be [semver](https://semver.org). Homey uses it to decide whether to update
a user's install: **if a higher version is available for a user, it is automatically installed.** The
app you submit must therefore have a version *higher* than the current **Live** version.

> **Homey will never downgrade apps.** If you want to undo a release, re-submit an older build with a
> higher version number.

```bash
homey app version patch          # 1.2.3 -> 1.2.4
homey app version minor          # 1.2.3 -> 1.3.0
homey app version major          # 1.2.3 -> 2.0.0
homey app version 1.4.0          # explicit semver

# with a changelog and a git commit + tag in one go
homey app version patch \
  --changelog.en "Add new feature" \
  --changelog.de "Neue Funktionalität" \
  --commit
```

`homey app version <next>` accepts `patch`, `minor`, `major`, or a valid semver string; anything else
errors with `Invalid version. Must be either patch, minor or major.`

### `.homeychangelog.json`

Created/updated automatically in the app root. Keyed by **version**, then **language**; `en` is
required and is the fallback.

```json
{
  "1.0.0": {
    "en": "First version!"
  },
  "1.1.0": {
    "en": "Added support for the outdoor sensor and fixed a reconnect loop.",
    "nl": "Ondersteuning voor de buitensensor toegevoegd en een reconnect-lus opgelost."
  }
}
```

What users want to see — only name changes relevant to them:

| Keyword | Use for |
| --- | --- |
| **Added** | new features |
| **Changed** | changes in existing functionality |
| **Deprecated** | soon-to-be removed features |
| **Removed** | (temporary) removed features |
| **Fixed** | any bug fixes |
| **Security** | in case of vulnerabilities |

If you changed e.g. your readme because of review feedback, there is **no need to mention it** in the
changelog. Only changes made since the previous **Live** version are important.

### Patching Live while a newer Test build exists

Submitting a patch with a version **lower** than the current *Test* version **replaces** the current
Test version.

Worked example from the docs:

1. Live is `1.0.0`, Test is `2.0.0`. `1.0.0` has a critical bug.
2. Submit the fix as `1.0.1`. → `1.0.1` becomes the **Test** version; `2.0.0` becomes unavailable, but
   existing users of `2.0.0` keep using it.
3. Verify the fix, then set `1.0.1` to **Live**. Users of `1.0.0` auto-update. Users of `2.0.0` do
   **not** downgrade.
4. To put the old Test branch back, resubmit it as `2.0.1` — `2.0.0` is already taken by a previous
   build. Test users on `2.0.0` then auto-update to `2.0.1`.

Rule of thumb: to make a previous Test version available again, release it with a version **higher than
the highest version ever released**.

---

## Verified Developer

A verified developer is recognisable by the blue **Official** badge behind the developer name in the
[Homey App Store](https://homey.app/en-nl/apps/homey-pro/). The badge signals that the app was created
by or on behalf of the brand itself, or by Athom.

| Topic | Detail |
| --- | --- |
| **What it unlocks** | Publishing an app for **Homey Cloud** — required when `"platforms"` includes `"cloud"`. Also: code-level support and in-depth app reviews. |
| **Who can get it** | A [Homey Verified Developer](https://homey.app/en-ca/homey-verified-developer/) subscription, *"solely intended for companies, brands or a third party developer commissioned by said brand/company"*. |
| **Community developers** | Apps published by community developers with a verified subscription **will not be approved** without proof of a partnership with the brand/company. |
| **How to apply** | Contact Athom's partnerships team at <partners@athom.com>. This can lead to becoming an official *Talks With Homey* partner (cross-marketing etc.). |
| **Homey Pro** | Publishing apps for Homey Pro does **not** require a subscription and will always remain free. |
| **Validation** | `homey app validate --level verified` (applied automatically when logged in with an account holding the `app_developer_trusted` role). |
| **Manifest extras** | `platforms` + `support` on the app; `platforms` + `connectivity` on every driver; `titleFormatted` and argument `title`s on every Flow card. |
| **Account name** | Must be the company name (guideline 1.13). |
| **Support URL** | Mandatory (reviewer checklist). |
| **Testing** | Sample devices (or a demo account for cloud apps, or a screen recording) must be provided before submission (guideline 3.2). |
| **Donate button** | Donate buttons are only visible for **non-verified** developers. |
| **Cloud approval scope** | *"Only official app integrations will be approved"* on Homey Cloud — an app submitted by a brand, or by a third-party developer commissioned by that brand. |

---

## Hardware Discount programme

Athom offers Homey Community Developers a discount on hardware for building & testing apps.

**Eligibility**

- You must have developed at least one app that has been **approved & published** in the Homey App
  Store.
- You may not have previously made use of this discount — **limited to one purchase per developer**.

**Pricing** (excluding shipping; the device might be refurbished with visible external damage, inner
parts verified working)

| Product | Discounted price |
| --- | --- |
| Homey Pro (Early 2023) | €225 |
| Homey Bridge (2022) | €49 |

**How to buy** — e-mail <community-developer-discount@athom.com> **from the same e-mail address as your
developer account**, stating the product(s) you want and the shipping country. Athom verifies the
request and replies with a payment webpage.

---

## Gotchas

**Gotcha — publishing for Homey Cloud needs an approved (verified) account.** `"platforms": ["cloud"]`
or `["local", "cloud"]` cannot be published without a Homey Verified Developer subscription, and only
*official* integrations (from the brand, or a developer commissioned by the brand) are approved. Ship
community apps as `"platforms": ["local"]`.

**Gotcha — the app `id` is effectively immutable.** It is the store identity and the install key.
Choose the final reverse-DNS id before the first publish, and make sure it contains neither `athom` nor
`homey` as a token — the reviewer rejects on that alone.

**Gotcha — icons are rendered white on the `brandColor` backdrop.** This is not folklore: `homey-lib`
says so in its own error text (*"Icons are rendered white, so choose a darker color that has enough
contrast"*) and enforces `brightness <= 184` on `brandColor`. Design the icon as a **solid silhouette
that reads in white** — the *shape* carries the icon, not the fill colour.

**Gotcha — gradients / `<defs>` / `clipPath` / stroke-only SVGs have been observed to render as an
empty coloured disc, and `homey app validate --level publish` does not warn.** Use a single solid
`<path>` and express cutouts with `fill-rule="evenodd"`. This applies to app icons, driver icons and
custom-capability icons alike.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960">
  <path fill-rule="evenodd" d="M480 80a400 400 0 100 800 400 400 0 100-800Zm0 120a280 280 0 110 560 280 280 0 110-560Z"/>
</svg>
```

**Gotcha — every widget needs *both* `preview-light.png` and `preview-dark.png`.** A missing one fails
the build with `ENOENT` and the reviewer flags "preview missing or empty" as a blocker.

**Gotcha — `homey app validate` defaults to `--level publish`, not `debug`.** Running bare
`homey app validate` on a work-in-progress app will complain about missing `images`, `brandColor` and
`category`. Use `--level debug` during development.

**Gotcha — `README.md` ≠ `README.txt`.** The store readme is `/README.txt`; `README.md` is GitHub-only
and is deliberately excluded from review. A donation link is a rejection trigger in the former and
completely fine in the latter.

**Gotcha — the "no URLs" readme rule is scoped to `README.txt` only.** URLs in `settings/*.html`, pair
views, source code, and the `app.json` metadata fields are expected and fine.

**Gotcha — a partially translated app is a rejection, not a nicety.** Decide your language set up front
and apply it consistently across `locales/*.json`, every `*.compose.json` translation object,
`README.<lang>.txt`, and `.homeychangelog.json`. If the description is translated to a language, the
readme must be too; if any Flow card is translated, all of them must be (plus device settings and
custom capabilities).

**Gotcha — `homeyCommunityTopicId` is a `number`, not a URL.** Take the numeric id out of the forum
topic's URL. See `references/app-and-manifest.md`.

**Gotcha — donation info goes in `contributing.donate`, nowhere else.** Supported providers in the
schema: `paypal` (`username` / `email` / `fundraiserCharityId` / `currency`), `bunq` (`username`),
`patreon` (`username`), `githubSponsors` (`username`). Credit humans with `contributors.developers[]`
and `contributors.translators[]`, not in the readme.

**Gotcha — uncommitted changes at publish time.** `homey app publish` will ask before continuing; a
dirty tree usually means the build you upload is not the code you tagged.

**Gotcha — third-party service integrations (Jellyfin, Plex, Spotify…).** Documented rules: use the
**brand** name (not the company name), no Homey/Athom, and don't use the third party's logo as your app
icon (unless you *are* the brand — guideline 1.5 says brand apps should use the company's brand icon).
Beyond the docs, the widely-followed community conventions for an unofficial integration are: name it
after the service (`"<App> for <Brand>"` is a common nominative-fair-use pattern — mind the 4-word
limit), draw your own icon, and add an "unofficial / not affiliated with \<Brand\>" note. The naming and
no-logo points are documented; the "for Brand" pattern and the disclaimer are conventions, not official
requirements.

**Gotcha — custom capabilities need an `icon`.** Without one they render as a dashed placeholder box in
the device UI, which reviewers notice. See `references/capabilities.md`.

---

## Pre-publish certification checklist

### A. Machine-checkable — `homey app validate --level publish` must pass

- [ ] `homey app validate --level publish` (or `--level verified`) exits 0
- [ ] `"sdk": 3`
- [ ] App `id` is reverse-DNS, **final**, and contains neither `athom` nor `homey` as a token
- [ ] `"platforms": ["local"]` unless you hold a Verified Developer subscription
- [ ] `category` set, from: `lights`, `video`, `music`, `appliances`, `security`, `climate`, `tools`,
      `internet`, `localization`, `energy`
- [ ] `brandColor` set, `#RRGGBB`, brightness ≤ 184
- [ ] `/assets/icon.svg` exists (case-sensitive)
- [ ] App images: `small` 250×175 and `large` 500×350 exist, real PNG/JPG bytes
- [ ] Driver images: `small` 75×75 and `large` 500×500 exist for **every** driver
- [ ] Every widget has both `preview-light.png` and `preview-dark.png` (checked at **build/pack**
      time, not by `validate` — a missing file throws `ENOENT` when the CLI generates the
      `__assets__` 1x/1.5x/2x/3x/4x thumbnails; the 1024×1024 source size itself is not machine-checked)
- [ ] `/README.txt` exists in the app root
- [ ] Battery drivers declare `energy.batteries`
- [ ] No symlinked packages in `node_modules` (no leftover `npm link`)
- [ ] `.homeyignore` excludes non-essential files; `env.json` is in `.gitignore`

### B. Reviewer-enforced — what `validate` does NOT catch

- [ ] **App name** ≤ 4 words, brand-based, no company name, no protocol name, no Homey/Athom (1.1)
- [ ] **Description** is a one-line tagline; not the app name, not the readme, not "Adds support for…"
      (1.2)
- [ ] **README.txt** is 1–2 promotional paragraphs — no feature/Flow lists, no setup steps, no author
      line, no Markdown, no URLs, no donation link, no changelog (1.3)
- [ ] **README matches actual behaviour** — no removed feature still described
- [ ] **App icon** is a single monochrome silhouette that reads in white; no gradients/defs/clip/stroke;
      transparent background; full 960×960 canvas; **not the default rocket** (1.5)
- [ ] **Driver icons** are unique per driver, transparent, right-side angle where possible, and are not
      the app icon (1.6)
- [ ] **App images** are rich brand/lifestyle imagery — **no white or transparent background**, no
      logo-only, no clipart, no phone/tablet mockups, no Homey name or logo (1.4.2)
- [ ] **Driver images** show the device itself on a **white or transparent** background; not the app
      image, not an icon, unique per driver (1.4.3)
- [ ] **Widget previews**: light + dark, transparent, no screenshots, no text, simple shapes, few
      colours (1.10)
- [ ] **Flow card titles** are short, no device names, no "When"/"And"/"Then", no parentheses;
      `titleFormatted` used for arguments; `hint` where the function isn't obvious (1.9)
- [ ] No custom Flow cards that duplicate auto-generated system-capability cards
- [ ] No `alarm_battery` + `measure_battery` together; no `windowcoverings_state` +
      `windowcoverings_set` together
- [ ] **No manual IP entry** — use `ManagerDiscovery` (`references/wireless-lan-discovery.md`)
- [ ] **Translations complete per language** — description ⇒ readme; any Flow card ⇒ all Flow cards,
      settings, capabilities (1.11)
- [ ] **No typos / spelling errors** in any language — spelling errors are a rejection (1.11)
- [ ] Every URL in the manifest resolves; `support` present (mandatory for verified apps) (1.8)
- [ ] **Permissions justified**; `homey:manager:api` only if the app's primary purpose needs it (1.15)
- [ ] **App works standalone**, adds value by itself, not fully dependent on another app (1.12)
- [ ] **App is free** — no paywall for any functionality (2.3)
- [ ] **Not a duplicate** — searched the store; if similar, reached out to the existing developer and
      documented in the submission why a separate app is necessary (2.1.1)
- [ ] Third-party code credited in the manifest, with permission (2.1.2)
- [ ] Developer account name has no emoji/special characters; company name if verified (1.13)
- [ ] Third-party integration: your own icon, consider an "unofficial" note

### C. Code hygiene (advisory `kind: code` findings, but cheap to fix)

- [ ] No `console.log` / `console.error` — use `this.log()` / `this.error()`
- [ ] Every promise handled (`.catch(this.error)`)
- [ ] `this.homey.setTimeout` / `this.homey.setInterval`, never the globals
- [ ] Listeners cleaned up in `onUninit` / `onDeleted`
- [ ] Class names match filenames; no references to non-existent drivers/properties

### D. Final gate

- [ ] `homey app review --type new` (or `--type update`) returns verdict `approve`
- [ ] Tested on real hardware: device controls, advanced settings, Flow creation + execution, and
      out-of-band state changes reflected in Homey (3.2)
- [ ] Version is **higher** than the current Live version
- [ ] `.homeychangelog.json` has a clear `en` entry for this version

---

## Sources

- App Store Guidelines — <https://apps.developer.homey.app/app-store/guidelines>
- Publishing — <https://apps.developer.homey.app/app-store/publishing>
- Updating — <https://apps.developer.homey.app/app-store/updates>
- Verified Developer — <https://apps.developer.homey.app/app-store/verified-developer>
- Hardware Discount — <https://apps.developer.homey.app/guides/hardware-discount>
- Homey Cloud (verified apps) — <https://apps.developer.homey.app/guides/homey-cloud>
- App Manifest (`contributing.donate`, `contributors`, URLs) — <https://apps.developer.homey.app/the-basics/app/manifest>
- Internationalization — <https://apps.developer.homey.app/the-basics/app/internationalization>
- Battery status best practice — <https://apps.developer.homey.app/the-basics/devices/best-practices/battery-status>
- Window coverings best practice — <https://apps.developer.homey.app/the-basics/devices/best-practices/window-coverings>
- Homey Vectors (free icon requests) — <https://github.com/athombv/homey-vectors-public>
- Widget preview Figma template — <https://www.figma.com/community/file/1392859749687789493/widget-previews-template>
- Reviewer-only rules, rejection triggers, severity model and feedback templates: the `homey-lib` npm
  package, `lib/AIReviewer/data/` (`guidelines.md`, `checklist.md`, `templates.md`) and
  `lib/AIReviewer/{prompt,schema,enums,extract,images,references,index}.js` — the material
  `homey app review` and Athom's review team run against.
- Mechanical validation behaviour (image sizes and magic bytes, `brandColor` brightness, category and
  permission enums, per-level requirements): `homey-lib` `lib/App/index.js` + `assets/app/schema.json`
  and `assets/app/permissions.json`.
- CLI behaviour (`review`, `publish`, `version`, `validate`, `manage`, `HOMEY_HEADLESS`, README locale
  handling, widget-preview packing): the `homey` npm package, `bin/cmds/app/*.mjs` and `lib/App.js`.
