# HarmonEyes Theia SDK

Python SDK for real-time eye tracking analysis, cognitive load prediction, and sleepiness detection.

> This package distributes **compiled binaries** of the HarmonEyes Theia SDK
> (native C++ core with Python bindings). No source ships here. See
> [`VENDORING.md`](VENDORING.md) for how the binaries are produced.

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
- **Platforms:** Linux x86_64, macOS arm64 (Apple Silicon), Windows x86_64.
- **Runtime dependencies** (`numpy`, `pandas`) install automatically. The heavy
  native dependencies (libcurl, OpenSSL, XGBoost) are bundled inside the
  compiled extension — nothing else to install.
- **License Key:** a valid license key is required to use the SDK.

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
    license_key="your-license-key",
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
    license_key="your-license-key",
    platform="Ganzin",
)
sdk.ip = "192.168.1.100"
sdk.port = 8080
```

> **Tip:** Make sure the Ganzin Sol is powered on and reachable at the configured
> IP before running.

See [`examples/theia-ganzin-streaming.py`](examples/theia-ganzin-streaming.py) for a full example.

### Batch processing (recorded data)

Process recorded gaze data without a live device:

```python
sdk = harmoneyes_theia.TheiaSDK(license_key="your-license-key", platform="WT")
cog_load = sdk.predict_cog_load_batch(dataframe_or_csv_path)
drowsiness = sdk.predict_drowsiness_batch(dataframe_or_csv_path)
```

See [`examples/theia-pupil-labs-batch.py`](examples/theia-pupil-labs-batch.py).

### Tobii Pro Glasses 3

Tobii G3 is **post-recorded batch data only** — there is no real-time/streaming
API. Load a full Tobii Pro Lab export (TSV) and process it in one call through
the SDK's ACE pipeline:

```python
import pandas as pd
import harmoneyes_theia

sdk = harmoneyes_theia.TheiaSDK(license_key="your-license-key", platform="TobiiG3")
df = pd.read_csv("recording.tsv", sep="\t", low_memory=False)
result = sdk.process_tobii_g3_data(df)   # per-second predictions DataFrame
```

`result` has one row per ACE window (~1 Hz after warmup) with columns:
`timestamp_s`, `cog_load_level` (0/1/2) + `cog_load_label` + `cog_load_confidence`,
and `drowsiness_level` (0–3) + `drowsiness_label` + `drowsiness_confidence`. See
[`examples/theia-tobii-g3.py`](examples/theia-tobii-g3.py).

### Webcam

The Webcam platform analyzes a stream of gaze samples that **your application
provides** — the SDK does not open a camera itself. Construct the SDK with
`platform="Webcam"`, inject a tracker that yields gaze samples, then stream:

```python
sdk = harmoneyes_theia.TheiaSDK(license_key="your-license-key", platform="Webcam")
sdk.tracker.set_tracker(your_gaze_source)   # object with get_buffered_data()
sdk.start_new_session(session_uuid)
sdk.start_realtime_data()
```

See [`examples/theia-webcam-streaming.py`](examples/theia-webcam-streaming.py) for
the injection pattern.

## License & Usage

This software is proprietary and requires a valid license key to operate. The
compiled binaries are publicly distributed but will not function without proper
licensing credentials.

- **Copyright**: © RightEye LLC / HarmonEyes
- **License Type**: Proprietary / Commercial
- **Obtaining a License**: contact sales@harmoneyes.com

## Support

For issues, questions, or feature requests, please contact support@harmoneyes.com
or create an issue on GitHub.
