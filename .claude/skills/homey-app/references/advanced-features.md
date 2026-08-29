# Advanced Features: Images, Videos, LED Ring, Insights & Misc Managers

Everything reachable through `this.homey.<manager>` that is not drivers, Flow cards, widgets or wireless.
Managers are also available on `Driver` and `Device` instances (same `this.homey`) and inside app Web-API handlers (`{ homey }`).

Siblings: `references/flow-cards.md` (Flow tokens & droptokens), `references/drivers-and-devices.md` (capabilities, `capabilitiesOptions.preventInsights`), `references/app-and-manifest.md` (permissions, `platformLocalRequiredFeatures`), `references/web-api-and-realtime.md` (`this.homey.api`, app-to-app), `references/widgets.md` (`this.homey.dashboards`).

---

## 0. Platform & feature gating

Several managers only work on certain hardware. Gate at runtime, and/or refuse installation at manifest level.

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.log('platform', this.homey.platform, 'v', this.homey.platformVersion);

    // hasFeature() is available since Homey v12.7.1
    if (this.homey.hasFeature('ledring')) {
      await this.startLedring().catch(this.error);
    }
  }
}

module.exports = App;
```

| Gate | Where | Values |
|---|---|---|
| `this.homey.platform` | runtime property | `'local'` \| `'cloud'` (may be `undefined` on old Homey Pro → assume `'local'`) |
| `this.homey.platformVersion` | runtime property | `1` \| `2` (may be `undefined` → assume `1`) |
| `this.homey.platformFeatures` | runtime property | `Array.<string>` of supported features |
| `this.homey.hasFeature(feature)` | runtime method, since Homey **v12.7.1** | `speaker`, `ledring`, `nfc`, `camera-streaming`, `matter` (also `ble-advertisements`, see `references/wireless-ble-matter.md`) |
| `platformLocalRequiredFeatures` | App Manifest array | `nfc`, `ledring`, `speaker`, `matter` — makes the app **uninstallable** on Homey Pros lacking any listed feature |
| `permissions` | App Manifest array | see the permission column of the quick-map in §7 |

`platformVersion` per product: Homey Cloud → `cloud`/`1`; Homey (Early 2016/2018/2019) and Homey Pro (Early 2019) → `local`/`1`; Homey Pro (Early 2023), Homey Pro mini (2025), Homey Pro (2026), Homey Self-Hosted Server → `local`/`2`.

**Gotcha:** permissions are checked at call time, not at install time — *"In case a permission is not requested by the App, the manager methods that require that permission will throw an error."* Also, **apps do not auto-update on a Homey when new permissions are added**; the user must approve the update manually. Adding a permission in a patch release therefore silently strands existing users.

---

## 1. Images — `this.homey.images` (ManagerImages)

An `Image` is a lazily-fetched image handle. It is registered with Homey; the actual bytes are pulled only when something (Flow token consumer, camera tile, album art) needs them.

* **Hard limit: 5 MB per image.**
* Debug live images in the Developer Tools: <https://tools.developer.homey.app/tools/images>.

### 1.1 ManagerImages API

| Method | Signature | Notes |
|---|---|---|
| `createImage` | `async createImage(): Promise<Image>` | Creates **and registers** an image |
| `getImage` | `getImage(id): Image` | Synchronous; get a previously registered image by id |
| `unregisterImage` | `async unregisterImage(imageInstance): Promise<void>` | Takes the `Image` instance, not the id |

### 1.2 Image API

| Member | Signature | Notes |
|---|---|---|
| `setUrl` | `setUrl(url)` | Absolute URL, **must start with `https://`** and be reachable from any network. Not async. |
| `setPath` | `setPath(path)` | Relative path to your image, e.g. `/userdata/kitten.jpg`. Not async. |
| `setStream` | `setStream(source)` | `source` is a function called with `(stream)` when someone pipes this image; pipe the content into it. Requires Homey **>= 2.2.0**. Not async. |
| `update` | `async update(): Promise<any>` | Notify that the contents changed → front-ends re-download; a `setStream` source function is invoked again |
| `getStream` | `async getStream(): Promise<NodeJS.ReadableStream>` | Readable stream carrying `Image.ImageStreamMetadata` |
| `pipe` | `async pipe(stream): Promise<Image.ImageStreamMetadata>` | Pipe into a `NodeJS.WritableStream`, resolves with the metadata |
| `unregister` | `async unregister()` | Shorthand for `ManagerImages#unregisterImage` |

`Image.ImageStreamMetadata`:

| Property | Type | Description |
|---|---|---|
| `filename` | `string` | A filename for this image |
| `contentType` | `string` | The mime type of this image |
| `contentLength` | `number` *(optional)* | The size in bytes, if available |

**There is no `setBuffer()` / `getBuffer()` / `getFormat()` / `format` in SDK v3** — those deprecated APIs were removed in the v3 upgrade. To publish a `Buffer`, wrap it in a readable stream inside `setStream()` (see §1.6).

### 1.3 Creating an image — the three delivery types

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    // (a) URL — image is publicly reachable on the internet
    this.urlImage = await this.homey.images.createImage();
    this.urlImage.setUrl('https://www.example.com/image.png'); // must start with https://

    // (b) Path — image is a local file (shipped asset or /userdata)
    this.pathImage = await this.homey.images.createImage();
    this.pathImage.setPath('/userdata/image.png');

    // (c) Stream — image must be fetched from somewhere Homey cannot reach directly
    this.streamImage = await this.homey.images.createImage();
    this.streamImage.setStream(async (stream) => {
      const res = await fetch('http://192.168.1.100/image.png');
      if (!res.ok) {
        throw new Error('Invalid Response');
      }
      return res.body.pipe(stream);
    });
  }
}

module.exports = App;
```

Use a **URL** when the image is publicly available, a **stream** when it is behind LAN-only or authenticated endpoints (the classic camera snapshot case), a **path** when the file is shipped with the app or written to `/userdata`.

You may switch delivery type at any time by calling `setPath()`, `setStream()` or `setUrl()` again on the same instance.

### 1.4 Updating an image

```javascript
// after the camera produced a new snapshot
await this.image.update().catch(this.error);
```

`update()` tells every front-end that the contents changed. With a stream-backed image, the function you passed to `setStream()` is called again — so keep that function stateless and re-entrant; do not close over a single-use stream.

### 1.5 Consuming an image (Flow droptokens, uploads)

```javascript
'use strict';

const fs = require('fs');
const path = require('path');
const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const card = this.homey.flow.getActionCard('image_action');

    card.registerRunListener(async (args, state) => {
      // droptokens are possibly null — always verify before use
      if (!args.droptoken) {
        throw new Error('No image provided');
      }

      const imageStream = await args.droptoken.getStream();
      this.log(`saving ${imageStream.meta.contentType} to: ${imageStream.meta.filename}`);

      const targetFile = fs.createWriteStream(path.join('/userdata', imageStream.meta.filename));
      imageStream.pipe(targetFile);
      return true;
    });
  }
}

module.exports = App;
```

**Gotcha — two different metadata shapes are documented.** The Flow-tokens documentation reads metadata off `imageStream.meta.contentType` / `imageStream.meta.filename`, while the Images documentation's Imgur example reads `stream.contentType` / `stream.filename` directly. Read defensively:

```javascript
const stream = await args.droptoken.getStream();
const meta = stream.meta ?? stream;
const { contentType, filename } = meta;
```

An image consumed in your app also exposes `image.cloudUrl` and `image.localUrl` (documented only in the Images example, not in the class property list — treat as best-effort, e.g. for putting a viewable link in a message body).

The official Images page uploads a consumed image to Imgur; the load-bearing details of that example are the metadata read and a documented `form-data` workaround:

```javascript
'use strict';

const { PassThrough } = require('stream');
const FormData = require('form-data');

// Uploads an image somewhere and returns a link
async function uploadImage(image) {
  const stream = await image.getStream();

  const form = new FormData();
  form.append('image', stream, {
    contentType: stream.contentType,
    filename: stream.filename,
    name: 'image',
  });
  form.append(
    'description',
    `This image can also be (temporarily) viewed at: ${image.cloudUrl} and ${image.localUrl}`,
  );

  const response = await fetch('https://api.imgur.com/3/image', {
    method: 'POST',
    // Pipe through a PassThrough stream — documented workaround for a node-fetch bug
    // involving form-data streams without a content length set.
    body: form.pipe(new PassThrough()),
    headers: {
      ...form.getHeaders(),
      Authorization: 'Client-ID <YOUR_CLIENT_ID>',
    },
  });

  if (!response.ok) {
    throw new Error(response.statusText);
  }

  const { data } = await response.json();
  return data.link;
}
```

### 1.6 Publishing a Buffer (no `setBuffer` in v3)

```javascript
'use strict';

const { Readable } = require('stream');
const Homey = require('homey');

class Device extends Homey.Device {
  async onInit() {
    this.snapshot = await this.homey.images.createImage();
    this.snapshot.setStream(async (stream) => {
      const buffer = await this.fetchSnapshotBuffer(); // your own code, returns a Buffer
      return Readable.from(buffer).pipe(stream);
    });

    await this.setCameraImage('front', 'Front', this.snapshot);
  }
}

module.exports = Device;
```

### 1.7 Attaching images to a Device

| Method | Signature | Purpose |
|---|---|---|
| `Device#setCameraImage` | `async setCameraImage(id, title, image): Promise<any>` | `id` = unique image id (e.g. `front`), `title` = human title (e.g. `Front`), `image` = `Image` instance |
| `Device#setAlbumArtImage` | `async setAlbumArtImage(image): Promise<any>` | Album art for `speaker`-class devices; takes only the `Image` |

```javascript
'use strict';

const Homey = require('homey');

class CameraDevice extends Homey.Device {
  async onInit() {
    this.image = await this.homey.images.createImage();
    this.image.setStream(async (stream) => {
      const res = await fetch(`http://${this.getSetting('ip')}/snapshot.jpg`);
      if (!res.ok) throw new Error('Invalid Response');
      return res.body.pipe(stream);
    });

    await this.setCameraImage('front', 'Front', this.image);

    // Refresh the snapshot every 30s; this.homey.setInterval auto-clears on destroy
    this.homey.setInterval(() => {
      this.image.update().catch(this.error);
    }, 30000);
  }
}

module.exports = CameraDevice;
```

### 1.8 Image Flow tokens

A Flow token (`FlowToken`, "Tag" in the UI) may have `type` `string`, `number`, `boolean` or **`image`**.

```javascript
'use strict';

const path = require('path');
const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const myImage = await this.homey.images.createImage();
    myImage.setPath(path.join(__dirname, 'assets', 'images', 'kitten.jpg'));

    const myImageToken = await this.homey.flow.createToken('my_token', {
      type: 'image',
      title: 'My Image Token',
    });
    await myImageToken.setValue(myImage);

    // Or hand the image straight to a trigger card's tokens:
    const myTriggerCard = this.homey.flow.getTriggerCard('image_trigger');
    await myTriggerCard.trigger({ my_image: myImage });
  }
}

module.exports = App;
```

`FlowToken#setValue(value)` accepts `string | number | boolean | Image` and must match the declared `type`. `FlowToken#unregister()` is shorthand for `ManagerFlow#unregisterToken`.

**Receiving** an image: declare a droptoken on the card manifest, restricted to the `image` type:

```json
{
  "title": { "en": "Upload image" },
  "titleFormatted": { "en": "Upload [[droptoken]]" },
  "droptoken": ["image"]
}
```

A Flow card can have **only one** droptoken, but it may allow multiple types (`["string", "number", "boolean", "image"]`). The value arrives as `args.droptoken`.

### 1.9 Image gotchas

* **Gotcha — 5 MB ceiling.** Images larger than 5 MB are rejected. Downscale camera snapshots server-side or in your stream callback.
* **Gotcha — `setUrl()` is https-only and must be internet-reachable.** A LAN URL (`http://192.168.x.x/...`) will not render for a phone outside the house; use `setStream()` so Homey brokers the fetch.
* **Gotcha — `/` differs per platform.** On Homey Pro apps are chroot'ed and `/` is your app directory; on Homey Cloud apps run in Docker and `/` is the Linux root. Always build shipped-asset paths with `path.join(__dirname, ...)` and reserve absolute `/userdata/...` for runtime files (Homey Pro only).
* **Gotcha — `/userdata/` is publicly served** at `https://<homey>/app/your.app.id/userdata/`. Never write predictable filenames; use a UUID (`a656d380-….jpg`) and store the mapping in App Settings.
* **Gotcha — `createImage()` is async, the setters are not.** `await this.homey.images.createImage()` then call `setUrl`/`setPath`/`setStream` synchronously. Forgetting the `await` yields a Promise with no `setUrl`.
* **Gotcha — no `setBuffer()`.** See §1.6.

---

## 2. Videos (camera streams) — `this.homey.videos` (ManagerVideos)

Available on **Homey Pro (2023 – 2026)** and **Homey Pro mini** since **v12.7.0**, and on **Homey Cloud**. Homey does **no transcoding**: your app is a broker that hands the front-end a URL (or an SDP answer) plus stream options.

Supported types: **WebRTC, RTSP, RTMP, HLS, DASH**. Other types *may* work — the Homey Mobile App embeds a VLC media player, so `createVideoOther()` is worth trying for anything VLC can play.

### 2.1 Class hierarchy

```
Video                       // base, only unregister()
├── VideoWebRTC             // registerOfferListener / registerKeepAliveListener
└── VideoWithURL            // registerVideoUrlListener  (do not use directly)
    ├── VideoHLS
    ├── VideoDASH
    ├── VideoRTSP
    ├── VideoRTMP
    └── VideoOther
```

### 2.2 ManagerVideos API

| Method | Returns | Options |
|---|---|---|
| `async createVideoWebRTC(options?)` | `Promise<VideoWebRTC>` | `dataChannel` |
| `async createVideoRTSP(options?)` | `Promise<VideoRTSP>` | `acceptInvalidCertificates`, `demuxer`, `disableWebRTCProxy` |
| `async createVideoRTMP(options?)` | `Promise<VideoRTMP>` | `acceptInvalidCertificates`, `demuxer`, `disableWebRTCProxy` |
| `async createVideoHLS(options?)` | `Promise<VideoHLS>` | `acceptInvalidCertificates`, `demuxer`, `disableWebRTCProxy` |
| `async createVideoDASH(options?)` | `Promise<VideoDASH>` | `acceptInvalidCertificates`, `demuxer`, `disableWebRTCProxy` |
| `async createVideoOther(options?)` | `Promise<VideoOther>` | `acceptInvalidCertificates`, `demuxer`, `disableWebRTCProxy` |
| `getVideo(id)` | `VideoWebRTC \| VideoRTSP \| VideoHLS \| VideoDASH \| VideoRTMP \| VideoOther` | — |
| `async unregisterVideo(videoInstance)` | `Promise<void>` | takes the instance |

`options` defaults to `{}`.

### 2.3 Constructor options — exact semantics

| Option | Type | Default | Applies to | Description |
|---|---|---|---|---|
| `acceptInvalidCertificates` | `boolean` | `false` | RTSP, RTMP, HLS, DASH, Other | Whether the frontend should accept invalid certificates |
| `demuxer` | `string` | *(none → default demuxer)* | RTSP, RTMP, HLS, DASH, Other | The demuxer to use for the stream. Only used for **raw** streams. One of `'h264'`, `'h265'`, `'mpegts'`, `'ts'` |
| `disableWebRTCProxy` | `boolean` | `false` | RTSP, RTMP, HLS, DASH, Other | Frontends default to using the WebRTC streaming proxy when supported. `true` disables the proxy and uses direct URL playback. **When disabled, videos cannot be played on web platforms or outside the local network.** |
| `dataChannel` | `boolean` | `true` | WebRTC only | Whether the frontend should set up a WebRTC data channel for bidirectional communication. Some video streams don't work with a data channel and some don't work without it. |

**Gotcha — option-name discrepancy in the official docs.** The ManagerVideos SDK reference documents the option as **`acceptInvalidCertificates`** (for RTSP, RTMP, HLS, DASH and Other alike). The RTSP walkthrough on the Videos page instead passes `allowInvalidCertificates: true` — and its Python tab passes the matching `allow_invalid_certificates=True`, so this is not a one-off typo on the guide page. The API reference is the more authoritative surface, so prefer `acceptInvalidCertificates`; because unknown keys are ignored, the safe move when certificate errors persist is to pass **both** keys and see which one takes effect.

**Gotcha — WebRTC options shape.** The `VideoWebRTC` class example shows `createVideoWebRTC({ options: {} })`, but both the ManagerVideos reference and the Videos guide take the option object **flat**: `createVideoWebRTC({ dataChannel: false })`. Use the flat form.

### 2.4 WebRTC proxy behaviour

Since **Homey Pro (2023 – 2026) / Homey Pro mini / Homey Self-Hosted Server v12.12.0**, Homey **automatically re-serves all videos as WebRTC to the frontend**. This is what makes camera streams visible in the Homey Web App and reachable from outside the local network. Opt out only if the proxy breaks your specific stream:

```javascript
const video = await this.homey.videos.createVideoRTSP({ disableWebRTCProxy: true });
// consequence: no Web App playback, LAN-only viewing
```

### 2.5 `Device#setCameraVideo`

| Method | Signature |
|---|---|
| `Device#setCameraVideo` | `async setCameraVideo(id, title, video): Promise<any>` — `id` unique video id (e.g. `front_door`), `title` human title (e.g. `Front Door`), `video` a `Video` subclass instance |

**When a device has both an image and a video with the same `id`, the image is used as the background image for the video while it is loading.** Pair `setCameraImage('front_door', …)` with `setCameraVideo('front_door', …)` to get a poster frame for free.

### 2.6 URL-based streams (RTSP / RTMP / HLS / DASH / Other)

`VideoWithURL#registerVideoUrlListener(listener)` → returns `VideoWithURL` (chainable). The listener takes **no arguments** and must resolve to an object of the form `{ url: '…' }`. It is invoked every time Homey needs the stream URL, so it is the right place to mint short-lived signed URLs or read fresh credentials.

```javascript
'use strict';

const Homey = require('homey');

class RtspCameraDevice extends Homey.Device {
  async onInit() {
    try {
      const video = await this.homey.videos.createVideoRTSP({
        acceptInvalidCertificates: true,
        demuxer: 'h265',
      });

      video.registerVideoUrlListener(async () => {
        const { username, password } = this.getSettings();
        // Normally you would get the IP from Discovery, or another method
        return { url: `rtsp://${username}:${password}@192.168.1.100:554/stream` };
      });

      await this.setCameraVideo('main', 'Main Camera', video);
    } catch (err) {
      this.error('Error creating camera:', err);
    }
  }
}

module.exports = RtspCameraDevice;
```

The other URL protocols are identical apart from the factory and the URL scheme:

| Protocol | Factory | Typical URL returned |
|---|---|---|
| RTSP | `createVideoRTSP()` | `rtsp://<ip>:554/stream` |
| RTMP | `createVideoRTMP()` | `rtmp://<ip>:1935/stream` |
| HLS | `createVideoHLS()` | `http://<ip>/stream.m3u8` |
| DASH | `createVideoDASH()` | `http://<ip>/stream.mpd` |
| Other | `createVideoOther()` | any VLC-playable URL, e.g. `https://<ip>/stream.mp4` |

```javascript
'use strict';

const Homey = require('homey');

class HlsCameraDevice extends Homey.Device {
  async onInit() {
    try {
      const video = await this.homey.videos.createVideoHLS();
      video.registerVideoUrlListener(async () => ({
        url: `http://${this.getSetting('ip')}/stream.m3u8`,
      }));
      await this.setCameraVideo('front_door', 'Front Door', video);
    } catch (err) {
      this.error('Error creating camera:', err);
    }
  }
}

module.exports = HlsCameraDevice;
```

HTTP Basic Authentication embedded in the URL (`rtsp://username:password@host/…`) is the documented way to authenticate RTSP streams.

### 2.7 WebRTC streams

| Method | Signature | Description |
|---|---|---|
| `registerOfferListener(listener)` | returns `VideoWebRTC` | Invoked when Homey requests an SDP answer for a WebRTC offer. Receives the **offer SDP** and resolves with the **answer**. |
| `registerKeepAliveListener(listener)` | returns `VideoWebRTC` | Invoked when Homey sends keep-alive signals for active WebRTC streams. Receives the **stream ID**. |

The offer listener resolves with `{ answerSdp }`, plus `streamId` when you also use a keep-alive listener:

```javascript
'use strict';

const Homey = require('homey');

class WebRtcCameraDevice extends Homey.Device {
  /*
   * WebRTC works by creating an offer SDP in the frontend, exchanging it for
   * an answer SDP through the camera's API, and using that answer SDP in the
   * frontend to set up the connection.
   */
  async onInit() {
    try {
      const video = await this.homey.videos.createVideoWebRTC({
        dataChannel: false, // default: true
      });

      video.registerOfferListener(async (offerSdp) => {
        const result = await this.oAuth2Client.createStream(offerSdp);
        return {
          answerSdp: result.answerSdp,
          streamId: result.streamId, // only needed if a keep-alive listener is used
        };
      });

      video.registerKeepAliveListener(async (streamId) => {
        await this.oAuth2Client.extendStream(streamId);
      });

      await this.setCameraVideo('main', 'Main Camera', video);
    } catch (err) {
      this.error('Error creating camera:', err);
    }
  }
}

module.exports = WebRtcCameraDevice;
```

### 2.8 Video gotchas

* **Gotcha — `dataChannel` is a coin flip per camera.** "Some cameras require a data channel in order to work, while other cameras only work when the offer does not contain a data channel." If a WebRTC stream negotiates but never renders, flip `dataChannel`.
* **Gotcha — short-lived streams.** Many cloud camera APIs keep a stream open for only a few minutes. Register a `registerKeepAliveListener` and return a `streamId` from the offer listener so you can identify which stream to extend.
* **Gotcha — `disableWebRTCProxy: true` kills Web App and remote playback.** Only set it when the proxy demonstrably breaks the stream.
* **Gotcha — `demuxer` only affects raw streams.** Setting `demuxer` on an HLS/DASH manifest URL does nothing; it exists for raw `h264`/`h265`/`mpegts`/`ts` payloads.
* **Gotcha — gate on the platform.** Videos need Homey Pro (2023 – 2026)/mini ≥ v12.7.0 or Homey Cloud. Check `this.homey.hasFeature('camera-streaming')` before creating videos on older firmware, and wrap creation in `try/catch` (all the official examples do).
* **Gotcha — the URL listener is called on every view.** Do not cache a one-time signed URL forever; re-mint it inside the listener.

---

## 3. LED Ring — `this.homey.ledring` (ManagerLedring)

**Controllable only on Homey Pro (Early 2019) and older models.** Add `"ledring"` to `platformLocalRequiredFeatures` in the App Manifest so the app cannot be installed on Homey Pros without a controllable LED Ring, and request the **`homey:manager:ledring`** permission — every `ManagerLedring` method requires it.

```json
{
  "id": "com.athom.example",
  "permissions": ["homey:manager:ledring"],
  "platformLocalRequiredFeatures": ["ledring"]
}
```

### 3.1 ManagerLedring API

| Method | Signature | Notes |
|---|---|---|
| `createAnimation` | `async createAnimation(opts): Promise<LedringAnimation>` | Custom animation, see §3.2 |
| `createSystemAnimation` | `async createSystemAnimation(systemId, opts): Promise<LedringAnimation>` | Built-in animation, see §3.4 |
| `createProgressAnimation` | `async createProgressAnimation(opts)` | Progress animation, see §3.5 |
| `registerAnimation` | `async registerAnimation(animation): Promise<LedringAnimation>` | Register a LED Ring animation |
| `unregisterAnimation` | `async unregisterAnimation(animation): Promise<LedringAnimation>` | |
| `registerScreensaver` | `async registerScreensaver(name, animation): Promise<any>` | `name` as defined in your app's `app.json` |
| `unregisterScreensaver` | `async unregisterScreensaver(name, animation): Promise<any>` | |

### 3.2 `createAnimation(opts)` — full option set

| Key | Type | Default | Description |
|---|---|---|---|
| `frames` | `Array<LedringAnimation.Frame>` | — | An array of frames. A frame is an Array of **24** objects with an `r`, `g` and `b` property, numbers between 0 and 255. |
| `priority` | `string` | — | Position on the priority stack: `INFORMATIVE`, `FEEDBACK` or `CRITICAL` |
| `transition` | `number` | `300` | Transition time (ms) — how fast to fade the information in |
| `duration` | `number \| Boolean` | `false` | How long (ms) the animation should be shown. **`false` is required for screensavers** (infinite). |
| `options.fps` | `number` | — | Frames per second (real frames) |
| `options.tfps` | `number` | — | Target frames per second (**must be divisible by `fps`**) — each real frame is interpolated up to `tfps` |
| `options.rpm` | `number` | — | Rotations per minute |

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.myAnimation = await this.homey.ledring.createAnimation({
      options: {
        fps: 1,    // real frames per second
        tfps: 60,  // target frames per second: every frame is interpolated 60 times
        rpm: 0,    // rotations per minute
      },
      frames: this.buildFrames(),
      priority: 'INFORMATIVE', // or FEEDBACK, or CRITICAL
      duration: 3000,          // ms, or false for infinite
    });

    this.myAnimation
      .on('start', () => this.log('animation started'))
      .on('stop', () => this.log('animation stopped'))
      .on('finish', () => this.log('animation finished (duration reached)'));

    await this.myAnimation.start();
  }

  buildFrames() {
    // A spinning red dot: one frame of 24 pixels, rotated by `rpm`.
    const frames = [];
    const frame = [];

    for (let pixelIndex = 0; pixelIndex < 24; pixelIndex++) {
      const colors = { r: 0, g: 0, b: 0 };
      if (pixelIndex === 0) {
        colors.r = 255;
      }
      frame.push(colors);
    }

    frames.push(frame);
    return frames;
  }
}

module.exports = App;
```

### 3.3 LedringAnimation API & events

| Member | Signature | Notes |
|---|---|---|
| `start` | `async start(): Promise<any>` | Start the animation |
| `stop` | `async stop(): Promise<any>` | Stop the animation |
| `updateFrames` | `async updateFrames(frames): Promise<any>` | Swap the frames of a running animation — this is how you build "live" screensavers |
| `registerScreensaver` | `async registerScreensaver(screensaverName): Promise<any>` | Shorthand for `ManagerLedring#registerScreensaver` |
| `unregisterScreensaver` | `async unregisterScreensaver(screensaverName): Promise<any>` | |
| `unregister` | `async unregister(): Promise<LedringAnimation>` | Shorthand for `ManagerLedring#unregisterAnimation` |
| `.on('start')` | event | The animation has started |
| `.on('stop')` | event | The animation has stopped |
| `.on('finish')` | event | The animation has finished (duration has been reached) |

`LedringAnimation.Frame` = object with `r`, `g`, `b`, each a number between 0 and 255. A *frame* is an array of 24 such objects (one per LED).

### 3.4 System animations

`createSystemAnimation(systemId, opts)` keeps the user experience consistent with the rest of Homey. The SDK reference documents the return type as `Promise<LedringAnimation>`; the instance you get back is a `LedringAnimationSystem` (extends `LedringAnimation`, same methods and events).

| `systemId` | |
|---|---|
| `colorwipe` | |
| `loading` | |
| `off` | |
| `progress` | |
| `pulse` | |
| `rainbow` | |
| `rgb` | |
| `solid` | |

`opts`: `priority` (`INFORMATIVE` \| `FEEDBACK` \| `CRITICAL`) and `duration` (`number | boolean`, default `false`; `false` is required for screensavers).

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const pulseAnimation = await this.homey.ledring.createSystemAnimation('pulse');
    await pulseAnimation.start();
  }
}

module.exports = App;
```

### 3.5 Progress animations

`createProgressAnimation(opts)` where `opts` = `{ priority, options: { color } }`:

| Key | Type | Default | Description |
|---|---|---|---|
| `priority` | `string` | — | `INFORMATIVE`, `FEEDBACK` or `CRITICAL` |
| `options.color` | `string` | `#0092ff` | A HEX string |

The SDK reference documents **no** return type for `createProgressAnimation`, but the instance you get back is a `LedringAnimationSystemProgress` (extends `LedringAnimationSystem`) — the only class that exposes:

| Method | Signature | Description |
|---|---|---|
| `setProgress` | `async setProgress(progress): Promise<any>` | A progress number between **0 – 1** |

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.progress = await this.homey.ledring.createProgressAnimation({
      priority: 'FEEDBACK',
      options: { color: '#0092ff' },
    });

    await this.progress.start();
    await this.progress.setProgress(0.25);
    await this.progress.setProgress(1);
    await this.progress.stop();
  }
}

module.exports = App;
```

### 3.6 Screensavers

A screensaver is an animation Homey plays while idling. The user picks it in **Settings → LED Ring**.

Declare each screensaver as its own Compose file — the filename (without extension) is the screensaver id:

```json
// /.homeycompose/screensavers/weather.json
{
  "title": {
    "en": "Weather",
    "nl": "Weer"
  }
}
```

Then register an animation instance against that id:

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.screensaver = await this.homey.ledring.createAnimation({
      options: { fps: 1, tfps: 60, rpm: 0 },
      frames: this.buildFrames(),
      priority: 'INFORMATIVE',
      duration: false, // required for screensavers
    });

    // 'weather' is the screensaver name defined in app.json
    this.screensaver.registerScreensaver('weather')
      .then(this.log)
      .catch(this.error);
  }

  async refresh() {
    // For live animations, simply update the frames when needed
    await this.screensaver.updateFrames(this.buildFrames()).catch(this.error);
  }

  buildFrames() { /* … 24-pixel frames … */ return []; }
}

module.exports = App;
```

### 3.7 LED Ring gotchas

* **Gotcha — hardware-limited.** Homey Pro (Early 2023), Homey Pro mini (2025), Homey Pro (2026), Homey Self-Hosted Server and Homey Cloud have no controllable LED Ring. Ship `platformLocalRequiredFeatures: ["ledring"]` if the app is useless without it; otherwise guard with `this.homey.hasFeature('ledring')` and degrade gracefully.
* **Gotcha — every method throws without `homey:manager:ledring`.** The permission is not implied by the manager being present on `this.homey`.
* **Gotcha — exactly 24 pixels per frame.** Not 12, not the number of LEDs you counted in a photo.
* **Gotcha — `duration` must be `false` for screensavers**, not `0` and not omitted-with-a-default-you-assumed.
* **Gotcha — `tfps` must be divisible by `fps`.** `fps: 1, tfps: 60` is valid; `fps: 7, tfps: 60` is not.
* **Gotcha — don't rebuild the animation to change it.** Call `updateFrames()` on the existing instance; re-creating animations leaks registrations.

---

## 4. Insights — `this.homey.insights` (ManagerInsights)

Insights logs are the long-term charts users see in the Homey app. Capability values are logged automatically (opt out per capability with `capabilitiesOptions: { "<capability>": { "preventInsights": true } }`); `ManagerInsights` is for **extra, non-capability** series your app wants to chart.

### 4.1 API

| Method | Signature | Notes |
|---|---|---|
| `createLog` | `async createLog(id, options): Promise<InsightsLog>` | `id` **must be lowercase, alphanumeric** |
| `getLog` | `async getLog(id): Promise<InsightsLog>` | Get a specific log belonging to this app |
| `getLogs` | `async getLogs(): Promise<Array<InsightsLog>>` | All logs belonging to this app |
| `deleteLog` | `async deleteLog(log): Promise<any>` | Takes the `InsightsLog` instance |
| `InsightsLog#createEntry` | `async createEntry(value): Promise<any>` | `value` is a `number` or `boolean`, matching the log's `type` |

### 4.2 `createLog(id, options)` options

| Key | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | yes | Log's title |
| `type` | `string` | yes | Value type: `number` or `boolean` |
| `units` | `string` | optional | Units of the values, e.g. `°C` |
| `decimals` | `number` | optional | Number of decimals visible |

### 4.3 Idiomatic create-or-get

`createLog()` on an existing id is not the documented way to fetch an existing log — `getLog()` is, and it rejects when the log does not exist. The safe pattern:

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.tempLog = await this.getOrCreateLog('outsidetemperature', {
      title: 'Outside Temperature',
      type: 'number',
      units: '°C',
      decimals: 1,
    });

    this.homey.setInterval(() => {
      this.sample().catch(this.error);
    }, 5 * 60 * 1000);
  }

  async getOrCreateLog(id, options) {
    try {
      return await this.homey.insights.getLog(id);
    } catch (err) {
      return this.homey.insights.createLog(id, options);
    }
  }

  async sample() {
    const value = await this.readSensor(); // your own code
    await this.tempLog.createEntry(value);
  }
}

module.exports = App;
```

Boolean logs work the same way:

```javascript
this.motionLog = await this.homey.insights.createLog('motiondetected', {
  title: 'Motion Detected',
  type: 'boolean',
});
await this.motionLog.createEntry(true);
```

### 4.4 Insights gotchas

* **Gotcha — Insights is write-only from an app.** `ManagerInsights` exposes only `createLog` / `getLog` / `getLogs` / `deleteLog`, and `InsightsLog` exposes only `createEntry`. There is **no** `getEntries()` / `getEntriesForLog()` in the Apps SDK v3. An app can push data points but can never read its own history back. If your app needs the history (e.g. to compute a daily total), keep your own rolling aggregate in `this.homey.settings` or the Device Store — do not plan to query Insights.
* **Gotcha — log ids are lowercase alphanumeric.** `outside_temperature` and `outsideTemperature` are not safe; use `outsidetemperature`.
* **Gotcha — `type` is immutable in practice.** Changing `type`/`units` for an existing id does not retroactively convert stored entries; delete the log (`deleteLog`) and create a new id if the shape changes.
* **Gotcha — capability logs already exist.** Don't shadow a capability (e.g. `measure_temperature`) with a hand-rolled Insights log; users end up with two charts. Use `preventInsights` if you want to suppress the automatic one.
* **Gotcha — `deleteLog(log)` takes the instance,** not the id string; fetch with `getLog(id)` first.

---

## 5. Speech, Geolocation, Clock, NFC, Audio, Notifications, Apps

### 5.1 Speech output — `this.homey.speechOutput` (ManagerSpeechOutput)

Permission: **`homey:manager:speech-output`**.

| Method | Signature | Notes |
|---|---|---|
| `say` | `async say(text, opts): Promise<any>` | **Limit of 255 characters.** `opts.session` is the session of the speech — leave empty to use Homey's built-in speaker. |

```javascript
this.homey.speechOutput.say('Hello world!')
  .then(this.log)
  .catch(this.error);
```

**Gotcha — 255 characters, hard.** Chunk longer text yourself. **Gotcha — needs a speaker**: gate with `this.homey.hasFeature('speaker')` or declare `platformLocalRequiredFeatures: ["speaker"]`.

`this.homey.speechInput` also exists as a property (type `ManagerSpeechInput`), but has **no published API reference page** in the SDK v3 docs — do not build on it.

### 5.2 Geolocation — `this.homey.geolocation` (ManagerGeolocation)

Permission: **`homey:manager:geolocation`** (required for every method *and* for the event).

| Member | Signature | Returns |
|---|---|---|
| `getLatitude` | `getLatitude(): number` | latitude |
| `getLongitude` | `getLongitude(): number` | longitude |
| `getAccuracy` | `getAccuracy(): number` | accuracy **in meters** |
| `getMode` | `getMode(): string` | `auto` or `manual` |
| `.on('location')` | event | Fired when the location is updated |

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.log('lat', this.homey.geolocation.getLatitude());
    this.log('lon', this.homey.geolocation.getLongitude());
    this.log('accuracy', this.homey.geolocation.getAccuracy(), 'm');
    this.log('mode', this.homey.geolocation.getMode()); // auto | manual

    this.homey.geolocation.on('location', () => {
      this.log('location changed', this.homey.geolocation.getLatitude());
    });
  }
}

module.exports = App;
```

**Gotcha — the getters are synchronous**, unlike almost everything else in the SDK. Do not `await` them; do re-read them inside the `location` handler rather than caching at `onInit`.

### 5.3 Clock & timers — `this.homey.clock` (ManagerClock)

| Member | Signature | Notes |
|---|---|---|
| `getTimezone` | `getTimezone(): string` | The current time zone, e.g. `Europe/Amsterdam` |
| `.on('timezoneChange')` | event, param `timezone: string` | Fired when the system timezone changes |

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    this.timezone = this.homey.clock.getTimezone();

    this.homey.clock.on('timezoneChange', (timezone) => {
      this.timezone = timezone;
      this.log('timezone is now', timezone);
    });

    this.log(this.formatLocal(new Date()));
  }

  formatLocal(date) {
    return new Intl.DateTimeFormat('en-GB', {
      timeZone: this.timezone,
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date);
  }
}

module.exports = App;
```

**Gotcha — the app process runs in UTC.** `new Date().getHours()`, `toLocaleString()` without an explicit `timeZone`, and any naive date math operate in UTC, *not* in the user's local time. Always take the zone from `this.homey.clock.getTimezone()` and pass it to `Intl.DateTimeFormat`/`toLocaleString`. This is the single most common source of "my Flow fires an hour early" bugs.

**Timers — `this.homey.setTimeout` / `setInterval` / `clearTimeout` / `clearInterval`:**

| Method | Signature | Notes |
|---|---|---|
| `setTimeout` | `setTimeout(callback, ms, ...args): NodeJS.Timer` | Alias to `setTimeout` that ensures the timeout is correctly disposed of when the Homey instance gets destroyed |
| `setInterval` | `setInterval(callback, ms, ...args): NodeJS.Timer` | Same, for intervals |
| `clearTimeout` | `clearTimeout(timeoutId)` | |
| `clearInterval` | `clearInterval(timeoutId)` | |

```javascript
// GOOD: automatically cleared when the app instance is destroyed
this.pollTimer = this.homey.setInterval(() => {
  this.poll().catch(this.error);
}, 10000);

// BAD: a bare setInterval() leaks across app instances (fatal on multi-tenant Homey Cloud)
```

**Gotcha — there is no `ManagerCron` in SDK v3.** Scheduling is `this.homey.setTimeout` / `setInterval`, plus `App#onUninit()` / `Driver#onUninit()` / `Device#onUninit()` or `this.homey.on('unload', …)` for teardown.

Related lifecycle events on `this.homey`: `.on('unload')` (app is being stopped), `.on('memwarn', ({ count, limit }) => …)` and `.on('cpuwarn', ({ count, limit }) => …)` — the app is killed if it keeps misbehaving after `limit` warnings.

### 5.4 NFC — `this.homey.nfc` (ManagerNFC)

Permission: **`homey:wireless:nfc`**. There are no instance methods — only an event.

| Event | Parameters |
|---|---|
| `.on('tag')` | `tag: object` with `tag.uid` — the UID of the tag |

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    if (!this.homey.hasFeature('nfc')) return;

    this.homey.nfc.on('tag', (tag) => {
      this.log('NFC tag scanned:', tag.uid);
    });
  }
}

module.exports = App;
```

**Gotcha — NFC is a Homey-hardware feature.** Declare `platformLocalRequiredFeatures: ["nfc"]` if the app is pointless without it, or check `hasFeature('nfc')`.

### 5.5 Audio — `this.homey.audio` (ManagerAudio)

Plays audio samples on Homey's built-in speaker. Samples are **cached in Homey by `sampleId`**: pass the payload once, then replay by id alone (faster).

| Method | Signature | Notes |
|---|---|---|
| `playMp3` | `async playMp3(sampleId, sample?): Promise<any>` | `sample` = `Buffer` with MP3 data **or** a path to an MP3 file. Omit `sample` to replay a cached sample. |
| `playWav` | `async playWav(sampleId, sample?): Promise<any>` | Same, for WAV |
| `removeMp3` | `async removeMp3(sampleId): Promise<any>` | Remove MP3 sample from cache |
| `removeWav` | `async removeWav(sampleId): Promise<any>` | Remove WAV sample from cache |

```javascript
'use strict';

const path = require('path');
const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    // First play: upload + cache
    await this.homey.audio
      .playMp3('doorbell', path.join(__dirname, 'assets', 'doorbell.mp3'))
      .catch(this.error);
  }

  async ring() {
    // Subsequent plays: cached, no payload needed
    await this.homey.audio.playMp3('doorbell').catch(this.error);
  }

  async onUninit() {
    await this.homey.audio.removeMp3('doorbell').catch(this.error);
  }
}

module.exports = App;
```

**Gotcha — `sampleId` must be unique across your app**, and cached samples survive restarts; clean up with `removeMp3`/`removeWav`. **Gotcha — needs a speaker** (`hasFeature('speaker')` / `platformLocalRequiredFeatures: ["speaker"]`). **Gotcha — use `path.join(__dirname, …)`** for shipped sounds, because `/` differs between Homey Pro and Homey Cloud.

### 5.6 Notifications (Timeline) — `this.homey.notifications` (ManagerNotifications)

| Method | Signature | Options |
|---|---|---|
| `createNotification` | `async createNotification(options)` | `options.excerpt` — a short message describing the notification. Use `**double asterisks**` to highlight variable words. |

```javascript
await this.homey.notifications.createNotification({
  excerpt: `The battery of **${this.getName()}** is low`,
}).catch(this.error);
```

**Gotcha — `excerpt` is the only documented option.** No title, no icon, no action. **Gotcha — notifications are user-visible and un-throttled by the SDK**; rate-limit yourself or users will disable the app.

### 5.7 Apps — `this.homey.apps` (ManagerApps)

Checks whether another Homey app is present. Both methods take an **`ApiApp`** instance (obtained via `this.homey.api.getApiApp('<appId>')`), not an id string.

| Method | Signature | Notes |
|---|---|---|
| `getInstalled` | `async getInstalled(appInstance): Promise<boolean>` | Whether an app is installed, **enabled and running** |
| `getVersion` | `async getVersion(appInstance): Promise<string>` | The installed app's version |

`ApiApp` (extends `Api`) provides the shorthands `apiApp.getInstalled()` and `apiApp.getVersion()`, plus `get/post/put/delete`, `unregister()` (shorthand for `ManagerApi#unregisterApi`) and the `install` / `uninstall` / `realtime` events.

| Event | Parameters | Fired when |
|---|---|---|
| `.on('install')` | — | The app is installed, **enabled and running** (accessible) |
| `.on('uninstall')` | — | The app is uninstalled, **disabled or crashed** (inaccessible) |
| `.on('realtime')` | `(event: string, data: any)` — **two positional arguments**, not one object | A realtime event is received on this URI |

```javascript
'use strict';

const Homey = require('homey');

class App extends Homey.App {
  async onInit() {
    const otherApp = this.homey.api.getApiApp('com.athom.otherApp');

    otherApp
      .on('install', () => this.log('other app became available'))
      .on('uninstall', () => this.log('other app went away'))
      // realtime passes (event, data) as two positional arguments
      .on('realtime', (event, data) => this.log('realtime', event, data));

    if (await otherApp.getInstalled()) {
      this.log('other app version', await otherApp.getVersion());
      await otherApp.post('/play', { sound: 'bell' }).catch(this.error);
    }
  }
}

module.exports = App;
```

**Gotcha — app-to-app requires the `homey:app:<appId>` permission** (e.g. `homey:app:com.athom.example`) and is **not supported on Homey Cloud**, along with the `homey:manager:api` permission and app Web APIs generally. Always check `getInstalled()` (and ideally the version) before calling; `getInstalled()` returns `false` for an app that is installed but disabled or crashed. See `references/web-api-and-realtime.md`.

---

## 6. Cross-cutting gotchas

* **Unhandled promise rejections crash the app on Homey Cloud.** Every fire-and-forget manager call needs `.catch(this.error)` — `update()`, `createEntry()`, `say()`, `playMp3()`, `createNotification()`, `start()`/`stop()`.
* **No global mutable state.** On Homey Cloud several app instances share one Node.js process; store manager handles (`this.image`, `this.tempLog`, `this.myAnimation`) on the `App`/`Driver`/`Device` instance, never in module scope.
* **Clean up in `onUninit()`.** Unregister images (`image.unregister()`), videos (`video.unregister()`), animations (`animation.unregister()`), screensavers (`animation.unregisterScreensaver(name)`) and cached audio samples. On Homey Pro the process dies anyway; on Homey Cloud it does not.
* **Relative vs absolute paths.** On Homey Pro `/` is your app directory; on Homey Cloud `/` is the Linux root. `path.join(__dirname, …)` for shipped assets; `/userdata/` only on Homey Pro.

---

## 7. Manager quick-map

`this.homey.<property>` → class → permission. Managers with no permission listed require none.

| Access | Class | Permission | Highlights |
|---|---|---|---|
| `this.homey.api` | ManagerApi | `homey:manager:api` (Web API use only; **not on Homey Cloud**) | `realtime`, `getApi`, `getApiApp`, `getLocalUrl`, `getOwnerApiToken`, `get/post/put/delete`, `unregisterApi` |
| `this.homey.app` | App | — | Pointer to your `App` instance |
| `this.homey.apps` | ManagerApps | `homey:app:<appId>` for the target app | `getInstalled`, `getVersion` |
| `this.homey.arp` | ManagerArp | — | `getMAC` |
| `this.homey.audio` | ManagerAudio | — (needs `speaker` feature) | `playMp3`, `playWav`, `removeMp3`, `removeWav` |
| `this.homey.ble` | ManagerBLE | `homey:wireless:ble` | `discover`, `find` |
| `this.homey.clock` | ManagerClock | — | `getTimezone`, `.on('timezoneChange')` |
| `this.homey.cloud` | ManagerCloud | — | `createOAuth2Callback`, `createWebhook`, `unregisterWebhook`, `getHomeyId`, `getLocalAddress` (not on Homey Cloud) |
| `this.homey.dashboards` | ManagerDashboards | — | `getWidget()` (widget setting autocomplete — see `references/widgets.md`) |
| `this.homey.discovery` | ManagerDiscovery | — (not on Homey Cloud) | `getStrategy` |
| `this.homey.drivers` | ManagerDrivers | — | `getDriver`, `getDrivers` |
| `this.homey.env` | `any` | — | The `env.json` environment variables |
| `this.homey.flow` | ManagerFlow | — | `createToken`, `getToken`, `unregisterToken`, `getTriggerCard`, `getDeviceTriggerCard`, `getConditionCard`, `getActionCard` |
| `this.homey.geolocation` | ManagerGeolocation | `homey:manager:geolocation` | `getLatitude`, `getLongitude`, `getAccuracy`, `getMode`, `.on('location')` |
| `this.homey.i18n` | ManagerI18n | — | `getLanguage`, `getUnits` (`metric`/`imperial`); shorthand `this.homey.__()` |
| `this.homey.images` | ManagerImages | — | `createImage`, `getImage`, `unregisterImage` |
| `this.homey.insights` | ManagerInsights | — | `createLog`, `getLog`, `getLogs`, `deleteLog` (**write-only — entries cannot be read back**) |
| `this.homey.ledring` | ManagerLedring | `homey:manager:ledring` | `createAnimation`, `createSystemAnimation`, `createProgressAnimation`, `registerAnimation`, `registerScreensaver` |
| `this.homey.manifest` | `any` | — | The parsed `app.json` manifest |
| `this.homey.nfc` | ManagerNFC | `homey:wireless:nfc` | `.on('tag')` → `tag.uid` |
| `this.homey.notifications` | ManagerNotifications | — | `createNotification({ excerpt })` |
| `this.homey.rf` | ManagerRF | `homey:wireless:433` / `:868` / `:ir` | `getSignal433`, `getSignal868`, `getSignalInfrared`, `tx`, `cmd`, `enableSignalRX`, `disableSignalRX` |
| `this.homey.settings` | ManagerSettings | — | `get`, `set`, `unset`, `getKeys`, `.on('set')`, `.on('unset')` |
| `this.homey.speechInput` | ManagerSpeechInput | — | No published API reference page — do not rely on it |
| `this.homey.speechOutput` | ManagerSpeechOutput | `homey:manager:speech-output` | `say(text, opts)` (255 char limit) |
| `this.homey.videos` | ManagerVideos | — | `createVideoWebRTC/RTSP/RTMP/HLS/DASH/Other`, `getVideo`, `unregisterVideo` |
| `this.homey.zigbee` | ManagerZigBee | — | `getNode` |
| `this.homey.zwave` | ManagerZwave | — | `getNode` |

Non-manager members of the `Homey` instance worth knowing: `platform`, `platformVersion`, `platformFeatures`, `version` (Homey software version), `hasFeature()`, `hasPermission()`, `__()`, `log()`, `error()`, `setTimeout/setInterval/clearTimeout/clearInterval`, and the events `unload`, `memwarn`, `cpuwarn`.

---

## Sources

* Images — <https://apps.developer.homey.app/advanced/images>
* Videos — <https://apps.developer.homey.app/advanced/videos>
* LED Ring — <https://apps.developer.homey.app/advanced/ledring>
* Flow Tokens (image tokens, droptokens) — <https://apps.developer.homey.app/the-basics/flow/tokens>
* Flow Arguments (droptoken) — <https://apps.developer.homey.app/the-basics/flow/arguments>
* Permissions — <https://apps.developer.homey.app/the-basics/app/permissions>
* App Manifest (`platformLocalRequiredFeatures`) — <https://apps.developer.homey.app/the-basics/app/manifest>
* Persistent Storage (`/userdata`) — <https://apps.developer.homey.app/the-basics/app/persistent-storage>
* Homey Cloud (multi-tenancy, cleanup, path differences) — <https://apps.developer.homey.app/guides/homey-cloud>
* Upgrading to SDK v3 (removed `Image.setBuffer` etc.) — <https://apps.developer.homey.app/upgrade-guides/upgrading-to-sdk-v3>
* Apps SDK v3 API reference — <https://apps-sdk-v3.developer.homey.app/> (`Homey`, `ManagerImages`, `Image`, `ManagerVideos`, `Video`, `VideoWithURL`, `VideoHLS`, `VideoDASH`, `VideoRTSP`, `VideoRTMP`, `VideoWebRTC`, `VideoOther`, `ManagerLedring`, `LedringAnimation`, `LedringAnimationSystem`, `LedringAnimationSystemProgress`, `ManagerInsights`, `InsightsLog`, `ManagerSpeechOutput`, `ManagerGeolocation`, `ManagerClock`, `ManagerNFC`, `ManagerAudio`, `ManagerNotifications`, `ManagerApps`, `ApiApp`, `Device`)
