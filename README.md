# HarmonEyes Theia SDK

Python SDK for real-time eye tracking analysis, cognitive load prediction, and sleepiness detection.

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
# Clone the repository
git clone https://github.com/harmoneyes/HarmonEyesTheia.git
cd HarmonEyesTheia

# Install the package
pip install .
```


## Requirements
- Python 3.12 only
- No additional dependencies (all compiled into the binary)
- **Git LFS**: Required to install from GitHub — run `git lfs install` once before installing
- **License Key**: A valid license key is required to use the SDK.

### Using pyenv for Python 3.12

```bash
# Install pyenv
brew install pyenv
# Install Python 3.12
pyenv install 3.12
# Set local Python version
pyenv local 3.12

python3 --version
#> Python 3.12.X
```

## Platform Setup

### Pupil Labs Neon

```python
sdk = harmoneyes_theia.TheiaSDK(
    license_key="your-license-key",
    platform="PL",
)
```

See [`examples/theia-pupil-labs-streaming.py`](examples/theia-pupil-labs-streaming.py) for a full example.

### Ganzin Sol

The Ganzin Sol connects over TCP. You must configure the device's IP address and port before starting a session.

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

**Ganzin dependencies**

**MacOS**
```bash
brew install libomp portaudio
```

**Linux**
```bash
apt install portaudio19-dev
```

> **Tip:** Make sure the Ganzin Sol is powered on and reachable at the configured IP before running. 

See [`examples/theia-ganzin-streaming.py`](examples/theia-ganzin-streaming.py) for a full example.

### Webcam

The Webcam platform uses the device's built-in or attached USB webcam — no external eye tracker required.

```python
sdk = harmoneyes_theia.TheiaSDK(
    license_key="your-license-key",
    platform="Webcam",
)
```

**Selecting which webcam to use**

You do **not** need to set this — by default the SDK uses the system's built-in camera (`"0"`). Only set the `THEIA_CAMERA_DEVICE` environment variable if you want to override the default and pick a different camera. Set it before launching your script (or before constructing `TheiaSDK` in-process).

| Platform | Backend | Value format | Example |
|----------|---------|--------------|---------|
| macOS    | avfoundation | numeric index | `"0"`, `"1"` |
| Linux    | v4l2         | device path   | `"/dev/video0"` |
| Windows  | dshow        | friendly name | `"Logitech BRIO"` |

```bash
# macOS / Linux
export THEIA_CAMERA_DEVICE=1
python theia-webcam-streaming.py
```

```powershell
# Windows (PowerShell)
$env:THEIA_CAMERA_DEVICE = "Logitech BRIO"
python theia-webcam-streaming.py
```

**Discovering available cameras**

| Platform | Command |
|----------|---------|
| macOS    | `ffmpeg -hide_banner -f avfoundation -list_devices true -i ""` |
| Linux    | `v4l2-ctl --list-devices` (or `ls /dev/video*`) |
| Windows  | `ffmpeg -hide_banner -f dshow -list_devices true -i dummy` |

See [`examples/theia-webcam-streaming.py`](examples/theia-webcam-streaming.py) for a full example.

## License & Usage

This software is proprietary and requires a valid license key to operate. The compiled binaries are publicly distributed but will not function without proper licensing credentials.

- **Copyright**: © RightEye LLC / HarmonEyes
- **License Type**: Proprietary / Commercial
- **Obtaining a License**: contact sales@harmoneyes.com

## Support

For issues, questions, or feature requests, please contact support@harmoneyes.com or create an issue on GitHub.
