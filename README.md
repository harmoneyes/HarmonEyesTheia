# HarmonEyes Theia SDK

Python SDK for real-time eye tracking analysis, cognitive load prediction, and fatigue detection.

> This package distributes **compiled binaries** of the HarmonEyes Theia SDK.
> No source ships here.

> **Upgrading from an earlier release?** See [`MIGRATION.md`](MIGRATION.md)
> for the full list of breaking changes, new capabilities, and a migration
> checklist.

## Installation

### Direct from GitHub

Install a release rather than `main`, which moves between releases: add
`@vX.Y.Z`, the newest tag on the repository's Releases page, to the URLs below
(for example `git+https://github.com/harmoneyes/HarmonEyesTheia.git@vX.Y.Z`).

```bash
# Install directly with pip
pip install git+https://github.com/harmoneyes/HarmonEyesTheia.git

# Or add to requirements.txt
git+https://github.com/harmoneyes/HarmonEyesTheia.git

# Or add to pyproject.toml
[project]
dependencies = [
    "harmoneyes-theia @ git+https://github.com/harmoneyes/HarmonEyesTheia.git"
]
```

### Install from Local Clone

```bash
git clone https://github.com/harmoneyes/HarmonEyesTheia.git
cd HarmonEyesTheia
pip install .
```

## Requirements

- **Python 3.12 only.** The compiled extensions and bytecode are built for
  CPython 3.12 (`requires-python = ">=3.12,<3.13"`).
- **Platforms:** Linux x86_64, Linux aarch64, macOS arm64 (Apple Silicon), Windows x86_64.
- **Runtime dependencies** (`numpy`, `pandas`) install automatically. Everything
  else is bundled inside the compiled extension — nothing else to install.
- **For the Webcam (Tobii Nexus) platform only, about 160 MB of free disk** in
  your home directory. The first time the webcam starts, the SDK unpacks its
  gaze sidecar there (see [Webcam](#webcam-tobii-nexus)). Nothing else to
  install; Node.js is not needed.
- **On Linux, CA certificates** (`apt install ca-certificates`), which minimal
  and container images may lack. Without them the SDK cannot reach HarmonEyes.
- **Your HarmonEyes API key,** which gives each machine its device lease; see
  [Device Lease](#device-lease).
- **A correct clock.** Leases are checked against the machine's clock, so keep
  it set by NTP. A clock that runs ahead makes a valid lease look expired, and
  the SDK will not start; one that runs behind (a board that boots without a
  battery-backed clock, say) holds off renewal until it is corrected.

### Using pyenv for Python 3.12

```bash
brew install pyenv          # macOS; see pyenv docs for other platforms
pyenv install 3.12
pyenv local 3.12
python3 --version
#> Python 3.12.X
```

## Device Lease

The SDK authenticates with a **device lease**: a signed token for one machine,
verified offline, so a machine keeps working without a connection until its
lease expires. How long that is, your **offline window** (a number of days),
is set on your HarmonEyes account. While a machine is online, the SDK keeps
its lease current by itself.

### Recommended: let the SDK manage the lease

Set your API key on each machine, or pass `lease_api_key_id=` and
`lease_api_key_secret=` to `TheiaSDK`:

```bash
export THEIA_API_KEY_ID="<your API key ID>"
export THEIA_API_KEY_SECRET="<your API key secret>"
```

Nothing else is needed:

- **On first start** the SDK obtains a lease for the machine from HarmonEyes
  (HTTPS to `identity.harmoneyes.io`) and saves it in `.theia/lease` in your
  home directory (`$HOME`, or `%USERPROFILE%` on Windows), readable by your
  user only. To keep it elsewhere, set `THEIA_LEASE_FILE` or pass `lease_file=`.
- **From then on** it renews the lease in the background before it is due,
  retrying every 30 minutes while HarmonEyes cannot be reached. The machine
  runs offline until its lease expires.
- **A machine offline for longer than its window** gets a new lease the next
  time it starts online.
- **Each machine registers as** `harmoneyes_theia.machine_device_identifier()`,
  a hash of its OS machine ID. Machines cloned from one disk image can share
  that ID, and containers usually have none (an empty `/etc/machine-id`); give
  each its own `lease_device_identifier=` (a serial number, say). In a
  container, also keep the lease on a volume, or each new container starts
  without one.
- `sdk.lease_info()` reports when the lease expires and how the last renewal
  went.

Your API key can obtain leases for any number of machines on your account, so
keep it as you would a password. HarmonEyes can list your machines and remove
one; a removed machine, or one whose API key was revoked, stops renewing and
does not get a new lease by itself.

### Without the API key on each machine

Give each machine its first lease and a lease file (`THEIA_LEASE_FILE`), and
put the lease in that file. The SDK renews it from then on; only a machine
that stays offline for longer than its window needs a new first lease. Get
first leases from support@harmoneyes.com, or with your API key, from an admin
machine:

```bash
token=$(curl -s -u "$THEIA_API_KEY_ID:$THEIA_API_KEY_SECRET" https://identity.harmoneyes.io/oidc/token \
  -d grant_type=client_credentials -d scope=account -d resource=https://identity.harmoneyes.io/api |
  sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
curl -s https://identity.harmoneyes.io/api/leases -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' -d '{"deviceIdentifier":"booth-2"}'
# {"lease":"..."}: one lease per machine, each with its own deviceIdentifier
```

A lease can also be passed directly, in `THEIA_LEASE` (or `THEIA_LICENSE_KEY`)
or as `lease_token=` (`license_key=` is still accepted). With a lease file set
too, the SDK starts from whichever is newer; without one, nothing keeps a
renewed lease across restarts.

### Errors

An invalid, expired, or missing lease raises
`harmoneyes_theia.LeaseVerificationError` (or a more specific subclass such as
`LeaseExpiredError`) when constructing `TheiaSDK`, before any device or model
work happens. `LeaseRenewalError`, also a `LeaseVerificationError`, means
HarmonEyes refused a lease or could not be reached; its message says which. A
running process can swap in a lease obtained elsewhere with
`sdk.set_lease_token(lease)`.

## Platform Setup

### Pupil Labs Neon

```python
import harmoneyes_theia

sdk = harmoneyes_theia.TheiaSDK(platform="PL")
```

See [`examples/theia-pupil-labs-streaming.py`](examples/theia-pupil-labs-streaming.py) for a full example.

### Ganzin Sol

The Ganzin Sol connects over the network. Configure the device's IP address and
port before starting a session.

| Setting | Default | Description |
|---------|---------|-------------|
| `ip`    | `192.168.1.100` | IP address of the Ganzin Sol device |
| `port`  | `8080`        | WebSocket port exposed by the device |

```python
sdk = harmoneyes_theia.TheiaSDK(platform="Ganzin")
sdk.ip = "192.168.1.100"
sdk.port = 8080
```

> **Tip:** Make sure the Ganzin Sol is powered on and reachable at the configured
> IP before running.

See [`examples/theia-ganzin-streaming.py`](examples/theia-ganzin-streaming.py) for a full example.

### Batch processing (recorded data)

Score a pre-recorded Pupil Labs Neon export (a Pupil Cloud
`gaze_and_eye_state.csv`) without a live device:

```python
sdk = harmoneyes_theia.TheiaSDK(platform="WT")
cog_load = sdk.predict_cog_load_batch("gaze_and_eye_state.csv")
fatigue = sdk.predict_fatigue_batch("gaze_and_eye_state.csv")
```

Each returns a list of `{"timestamp": <seconds from recording start>,
"value": int, "label": str, "confidence": float}` dicts — cog load one per
~1s window (0=Low, 1=Moderate, 2=High), fatigue one per emitted result
(0=Alert, 1=Somewhat Fatigued, 2=Fatigued; its rolling window only emits
periodically, so expect far fewer entries than cog load). No scene-camera
calibration file is needed — Neon's own export already carries 3D
optical-axis vectors directly.

See [`examples/theia-pupil-labs-batch.py`](examples/theia-pupil-labs-batch.py).

### Tobii Pro Glasses 3

Tobii G3 is **post-recorded batch data only** — there is no real-time/streaming
API. Load a full Tobii Pro Lab export (TSV) and process it in one call:

```python
import pandas as pd
import harmoneyes_theia

sdk = harmoneyes_theia.TheiaSDK(platform="TobiiG3")
df = pd.read_csv("recording.tsv", sep="\t", low_memory=False)
result = sdk.process_tobii_g3_data(df)   # per-second predictions DataFrame
```

`result` has one row per ACE window (~1 Hz after warmup) with columns:
`timestamp_s`, `cog_load_level` (0/1/2) + `cog_load_label` + `cog_load_confidence`,
and `fatigue_level` (0=Alert, 1=Somewhat Fatigued, 2=Fatigued) + `fatigue_label` + `fatigue_confidence`. See
[`examples/theia-tobii-g3.py`](examples/theia-tobii-g3.py).

### Webcam (Tobii Nexus)

The Webcam platform turns on your webcam and estimates gaze with the bundled
Tobii Nexus engine. Inject `NexusWebcamTracker` — it starts the gaze sidecar
shipped with this package, a compiled program that hosts the Tobii Nexus engine
and camera capture and feeds gaze into the SDK:

```python
import harmoneyes_theia

sdk = harmoneyes_theia.TheiaSDK(platform="Webcam")
sdk.tracker.set_tracker(harmoneyes_theia.NexusWebcamTracker())
sdk.start_new_session(session_uuid)
sdk.start_realtime_data()   # opens the camera + starts the gaze sidecar
```

**Requirements:** nothing to install. The first start unpacks the sidecar
(about 160 MB) into `~/.theia/webcam-sidecar/`, which takes a few seconds; later
starts reuse it, and a new release unpacks its own copy. Where there is no
writable home directory (a service account, say) it uses the system temp
directory instead. The SDK runs the sidecar only from a directory that no
other user can write to, and refuses to start it otherwise.
The Tobii Nexus license endpoint is baked into the distributed build, so no
configuration is needed; to point at a different signing server, set
`TOBII_LICENSE_URL` (or `FASTAPI_URL`).

> You can still supply your own gaze source instead: pass any object with
> `get_buffered_data()` (yielding `{"timestamp": <ms>, "leftEyeX": …}` sample
> dicts) to `set_tracker(...)`.

See [`examples/theia-webcam-streaming.py`](examples/theia-webcam-streaming.py).

### Your own head-mounted tracker

A tracker that calls you back with each frame can push its gaze with
`add_gaze_samples()`. Use `platform="TobiiG3"` (head-mounted gaze), start a
session, and push from that callback; there is no `start_realtime_data()` call.

```python
import harmoneyes_theia
from harmoneyes_theia import GazeSample

sdk = harmoneyes_theia.TheiaSDK(platform="TobiiG3")
sdk.start_new_session(session_uuid)

# in your tracker's frame callback:
sample = GazeSample()
sample.timestamp_ns = frame_time_ns                  # capture time, ns since the Unix epoch
sample.optical_axis_left_x, sample.optical_axis_left_y, sample.optical_axis_left_z = gx, gy, gz
sample.pupil_diameter_left = pupil_mm                # millimetres
sdk.add_gaze_samples([sample])                       # or several, in time order

# when the recording ends:
sdk.stop_processing()
```

Each eye's `optical_axis_*` is its gaze direction as a unit vector in the
head's frame: +x right, +y up, +z forward. Leave an eye at `(0, 0, 0)` when it
was not tracked; one eye is enough.

- **Check the y axis.** Many eye cameras count +y downwards; negate it if
  yours does.
- **Send pupil diameters if you can.** Blinks are detected from the pupil
  signal. Without it the SDK finds none, and cognitive load reads Low
  throughout.
- **It is tuned for Tobii Pro Glasses 3,** at 50 samples a second. Results
  from other headsets have not been validated, so contact
  support@harmoneyes.com before relying on them.

`add_gaze_samples()` may run on another thread, such as that callback, while
you call the `get_*` methods.

## Reading results

Poll about once a second, and print every result on one line:

```python
cog_load, fatigue = "warming up", "not yet"

# once a second:
levels, _, _ = sdk.get_cog_load_levels()
if levels:
    cog_load = {0: "Low", 1: "Moderate", 2: "High"}[next(iter(levels.values()))["prediction"]]
drowsiness, _ = sdk.get_fatigue_level()
if drowsiness:
    fatigue = {0: "Alert", 1: "Somewhat Fatigued", 2: "Fatigued"}[next(iter(drowsiness.values()))]
attention = sdk.get_attention_style()
readiness = sdk.get_mental_readiness()
print(f"Cognitive load: {cog_load} | Fatigue: {fatigue} | "
      f"Attention: {attention['label'] if attention else 'not yet'} | "
      f"Mental readiness: {readiness['label'] if readiness else 'not yet'}")
```

| Call | Returns | Updates |
|---|---|---|
| `get_cog_load_levels()` | the newest cognitive load (0=Low, 1=Moderate, 2=High), then nothing until the next | about once a second, after a ~30 s warmup |
| `get_fatigue_level()` | the newest fatigue (0=Alert, 1=Somewhat Fatigued, 2=Fatigued), then nothing until the next | about every 2 minutes |
| `get_attention_style()` | `level` (1=Narrow … 5=Broad) and `label` | continuously |
| `get_mental_readiness()` | `label` "High" or "Low", with the session's `low_percentage`, `moderate_percentage` and `high_percentage` of cognitive load. Readiness is High while low + moderate reach half; `set_mental_readiness_low_high_threshold()` moves the line. | continuously |

Each returns `None` until a result is available.

## Running as a service

An app running as a service (systemd, a Windows service) may have no home
directory, or none it can write, and the SDK keeps its lease and models there.
Set `THEIA_LEASE_FILE` and `THEIA_MODEL_CACHE_DIR` to paths the service can
write, and give it the API key the same way as an app.

## License & Usage

This software is proprietary and requires a valid device lease to operate
(see [Device Lease](#device-lease) above). The compiled binaries are publicly
distributed but will not function without one.

- **Copyright**: © RightEye LLC / HarmonEyes
- **License Type**: Proprietary / Commercial
- **Obtaining an API key**: contact sales@harmoneyes.com

## Support

For issues, questions, or feature requests, please contact support@harmoneyes.com
or create an issue on GitHub.
