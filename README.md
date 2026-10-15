# HarmonEyes Theia SDK

Python SDK for real-time eye tracking analysis, cognitive load prediction, and fatigue detection.

> This package distributes **compiled binaries** of the HarmonEyes Theia SDK.
> No source ships here.

> **Upgrading from an earlier release?** See [`MIGRATION.md`](MIGRATION.md)
> for the full list of breaking changes, new capabilities, and a migration
> checklist.

## Installation

### Direct from GitHub

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
- **Node.js 20+** — required **only for the Webcam (Tobii Nexus) platform**,
  whose gaze sidecar runs on Node. Not needed for Pupil Labs, Ganzin, batch, or
  Tobii G3. Install from [nodejs.org](https://nodejs.org) and ensure `node` is on
  your `PATH`.
- **Device Lease:** a valid device lease is required to use the SDK — see
  below.

## Device Lease

This SDK runs on customer machines with no connection back to HarmonEyes, so
it authenticates with a **device lease** instead of a live login: a signed,
time-boxed token that's verified entirely offline, rather than a plain
license key checked against a server.

**Getting your first lease:** contact support@harmoneyes.com. HarmonEyes
staff issues a lease for your device and sends you the token — you don't
need to request or manage any credentials yourself.

**Using it:** set `THEIA_LEASE` in your environment, or pass
`lease_token=` directly when constructing `TheiaSDK`. The examples also
accept the older `THEIA_LICENSE_KEY` name, if you already have that set from
before this SDK switched to lease-based auth.

```bash
export THEIA_LEASE="<the token you were given>"
```

```python
sdk = harmoneyes_theia.TheiaSDK(lease_token="<the token you were given>", platform="PL")
```

An invalid, expired, or missing lease raises
`harmoneyes_theia.LeaseVerificationError` (or a more specific subclass —
`LeaseExpiredError`, `LeaseMalformedError`, etc.) immediately when
constructing `TheiaSDK`, before any device or model work happens. **Leases
expire** — when yours is nearing expiry, request a new one the same way you
got the first; a long-running process can swap it in without restarting via
`sdk.set_lease_token(new_token)`.

### Using pyenv for Python 3.12

```bash
brew install pyenv          # macOS; see pyenv docs for other platforms
pyenv install 3.12
pyenv local 3.12
python3 --version
#> Python 3.12.X
```

## Platform Setup

### Pupil Labs Neon

```python
import harmoneyes_theia

sdk = harmoneyes_theia.TheiaSDK(
    lease_token="your-device-lease",
    platform="PL",
)
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
sdk = harmoneyes_theia.TheiaSDK(
    lease_token="your-device-lease",
    platform="Ganzin",
)
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
sdk = harmoneyes_theia.TheiaSDK(lease_token="your-device-lease", platform="WT")
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

sdk = harmoneyes_theia.TheiaSDK(lease_token="your-device-lease", platform="TobiiG3")
df = pd.read_csv("recording.tsv", sep="\t", low_memory=False)
result = sdk.process_tobii_g3_data(df)   # per-second predictions DataFrame
```

`result` has one row per ACE window (~1 Hz after warmup) with columns:
`timestamp_s`, `cog_load_level` (0/1/2) + `cog_load_label` + `cog_load_confidence`,
and `fatigue_level` (0=Alert, 1=Somewhat Fatigued, 2=Fatigued) + `fatigue_label` + `fatigue_confidence`. See
[`examples/theia-tobii-g3.py`](examples/theia-tobii-g3.py).

### Webcam (Tobii Nexus)

The Webcam platform turns on your webcam and estimates gaze with the bundled
Tobii Nexus engine. Inject `NexusWebcamTracker` — it spawns a small Node sidecar
(shipped with this package) that hosts the Tobii Nexus engine + camera capture
and feeds gaze into the SDK:

```python
import harmoneyes_theia

sdk = harmoneyes_theia.TheiaSDK(lease_token="your-device-lease", platform="Webcam")
sdk.tracker.set_tracker(harmoneyes_theia.NexusWebcamTracker())
sdk.start_new_session(session_uuid)
sdk.start_realtime_data()   # opens the camera + starts the gaze sidecar
```

**Requirements:** **Node.js 20+** on your `PATH` (the gaze sidecar runs on Node).
The Tobii Nexus license endpoint is baked into the distributed build, so no
configuration is needed; to point at a different signing server, set
`TOBII_LICENSE_URL` (or `FASTAPI_URL`).

> You can still supply your own gaze source instead: pass any object with
> `get_buffered_data()` (yielding `{"timestamp": <ms>, "leftEyeX": …}` sample
> dicts) to `set_tracker(...)`.

See [`examples/theia-webcam-streaming.py`](examples/theia-webcam-streaming.py).

## License & Usage

This software is proprietary and requires a valid device lease to operate
(see [Device Lease](#device-lease) above). The compiled binaries are publicly
distributed but will not function without one.

- **Copyright**: © RightEye LLC / HarmonEyes
- **License Type**: Proprietary / Commercial
- **Obtaining a Device Lease**: contact sales@harmoneyes.com

## Support

For issues, questions, or feature requests, please contact support@harmoneyes.com
or create an issue on GitHub.
