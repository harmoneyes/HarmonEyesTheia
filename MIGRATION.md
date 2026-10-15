# Migrating to v3 (the native SDK)

`harmoneyes-theia` v3.0.0 replaces the old Python-heavy SDK (v1.x) with a
thin wrapper over a compiled C++ native core (`theia-native`). This is a
breaking release — most existing integrations need the changes below, but
most of them are mechanical.

## Breaking changes

### 1. Auth: `license_key=` → `lease_token=`

The SDK no longer validates a license key against a server. It verifies an
offline, signed **device lease** instead.

```python
# Before (v1.x)
sdk = harmoneyes_theia.TheiaSDK(license_key="your-license-key-here", platform="PL")

# After (v3.x)
sdk = harmoneyes_theia.TheiaSDK(lease_token="your-device-lease", platform="PL")
```

- Set `THEIA_LEASE` in your environment (recommended) or pass `lease_token=`
  directly. **`THEIA_LICENSE_KEY` still works as a fallback** if you already
  have that env var set — you don't have to rename it immediately.
- A missing/invalid/expired lease now raises `harmoneyes_theia.LeaseVerificationError`
  (or a subclass — `LeaseExpiredError`, `LeaseMalformedError`) **at construction
  time**, before any device or model work happens. Wrap construction in a
  `try/except` (every bundled example now does this).
- Contact support@harmoneyes.com for a lease the same way you'd have
  contacted sales for a license key.

### 2. Fatigue is now a 3-class result, not 4-class

The old 4-class fatigue model (`0=Alert, 1=Mild, 2=Moderate, 3=Drowsy`) has
been replaced by a 3-class model:

```
0 = Alert
1 = Somewhat Fatigued
2 = Fatigued
```

Class `3` no longer exists and will never be returned. If your code has its
own label dict (the bundled examples used to), update it — three bundled
examples (`theia-webcam-streaming.py`, `theia-ganzin-streaming.py`,
`theia-pupil-labs-streaming.py`) had a stale 4-class dict that's been fixed
as of this migration; if you forked them earlier, re-sync.

### 3. Tobii G3 is now batch-only

v1.x's `theia-tobii-g3.py` example supported both one-shot batch processing
*and* a `--stream-only` mode that simulated a live session by feeding a
recorded TSV row-by-row. v3.x drops the streaming simulation — Tobii G3 is
post-recorded batch data only, through a single entry point:

```python
df = pd.read_csv("recording.tsv", sep="\t", low_memory=False)
result = sdk.process_tobii_g3_data(df)   # DataFrame, ~1 row per ACE window (~1Hz)
```

`result` columns: `timestamp_s`, `cog_load_level/label/confidence`,
`fatigue_level/label/confidence`.

### 4. Webcam platform: new capture mechanism, Node.js now required

v1.x's Webcam platform used OS-native camera capture (ffmpeg-based) with no
extra runtime dependency, and let you pick a camera via `THEIA_CAMERA_DEVICE`.
v3.x's Webcam platform runs on the Tobii Nexus gaze engine via a bundled
Node.js sidecar:

```python
sdk.tracker.set_tracker(harmoneyes_theia.NexusWebcamTracker())
sdk.start_realtime_data()   # opens the camera + starts the Node sidecar
```

- **Requires Node.js 20+ on `PATH`.** Nothing else needs installing — the
  sidecar and the Tobii Nexus engine ship inside the package.
- **`THEIA_CAMERA_DEVICE` has no replacement yet.** If you were selecting a
  specific camera on a multi-camera machine, there's currently no equivalent
  knob — this is a known gap, not something you're missing in the docs.
  Flag it if it blocks you; it isn't addressed in this release.

### 5. Dependencies: most of them are gone

v1.x pulled in ~45 runtime dependencies (xgboost, opencv-python, av, pyaudio,
aiohttp/aiodns/aiortsp, pupil-labs-\*, protobuf, pydantic, rich, …) because it
ran ML/feature code in Python. v3.x's native core statically links its heavy
C/C++ dependencies (libcurl, OpenSSL, XGBoost) into the compiled extension,
so the only runtime requirements are:

- `numpy>=1.20`, `pandas>=1.5` (always)
- `opencv-python>=4.5.0` — only if you use `DefaultTrackerVideo` for MP4
  replay (`pip install harmoneyes-theia[video]`)

If your project pinned any of the old dependencies specifically for this
SDK, you can likely drop them.

### 6. Installing no longer requires Git LFS

v1.x tracked its per-platform webcam binaries via Git LFS
(`git lfs install` was a prerequisite). v3.x's vendor bundle is tracked as
regular Git objects — no LFS setup needed to `pip install` from GitHub.

## What's new

- **Batch predictions from a recorded Pupil Labs Neon export** — score a
  `gaze_and_eye_state.csv` with no live device:
  ```python
  sdk = harmoneyes_theia.TheiaSDK(lease_token="...", platform="WT")
  cog_load = sdk.predict_cog_load_batch("gaze_and_eye_state.csv")
  fatigue = sdk.predict_fatigue_batch("gaze_and_eye_state.csv")
  ```
  Both accept a file path or a pre-loaded DataFrame. No scene-camera
  calibration file needed — Neon's Cloud export already carries 3D
  optical-axis vectors. See `examples/theia-pupil-labs-batch.py` (new).
- **Mental readiness now emits on the same cadence as cognitive load**
  (as soon as there's at least one cog-load sample), instead of silently
  requiring 10 minutes of elapsed session time before producing a result.
- **No proprietary session data written to disk.** Earlier builds wrote
  full intermediate feature vectors and raw gaze rows to `sdk_files/` by
  default on every machine running the SDK. That's now disabled
  unconditionally for this package — nothing is written unless you've
  configured your own output path.
- **An alert-rule engine**: `set_alert_rules()`, `enable_alert_sync()` /
  `disable_alert_sync()`, `list_alert_rules()`, `alert_rules_status()`,
  `set_alert_subject()`, `refresh_alert_rules()`, `set_alert_callback()`.
- **Model refinement API**: `save_refined_model()`, `load_refined_model()`,
  `reset_to_base_model()`, `reset_models_batch()`, `get_model_info()`.
- **`get_cog_load_prediction_history()`** and **`get_drowsiness_ttt()`**
  (time-to-transition) for richer session introspection.

## Renamed methods (old names still work)

These are aliases, not breaking changes — existing code calling the old
names keeps working unmodified:

| Old name | New name |
|---|---|
| `get_mental_workload_levels()` | `get_cog_load_levels()` |
| `get_fatigue_level()` | `get_drowsiness_level()` |
| `get_attention()` | `get_attention_style()` |
| `get_mental_fatigue(elapsed_seconds)` | `get_mental_readiness(elapsed_seconds)` |
| `set_mental_fatigue_min_session_seconds(s)` | `set_mental_readiness_min_session_seconds(s)` |

## Quick checklist

- [ ] Rename `license_key=` → `lease_token=`; set `THEIA_LEASE` (or keep
      `THEIA_LICENSE_KEY` for now).
- [ ] Wrap `TheiaSDK(...)` construction in `try/except LeaseVerificationError`.
- [ ] Update any hardcoded 4-class fatigue label dict to the 3-class scheme.
- [ ] If using Tobii G3 streaming/simulation mode, switch to
      `process_tobii_g3_data()` batch processing.
- [ ] If using the Webcam platform, install Node.js 20+ and inject
      `NexusWebcamTracker()`; drop any `THEIA_CAMERA_DEVICE` usage (no
      replacement yet).
- [ ] Drop any now-unnecessary pinned dependencies (xgboost, opencv-python
      unless using video replay, av, pyaudio, aiohttp family, pupil-labs-\*,
      protobuf, pydantic, rich, etc.).
- [ ] Remove any `git lfs install` step from your install docs/CI.
