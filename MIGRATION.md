# Migration guide

This release has several breaking changes from earlier releases. Most are
mechanical to update. This guide covers what changed, what's new, and a
checklist to work through.

## Breaking changes

### 1. Auth: `license_key=` → `lease_token=`

The SDK now authenticates with a **device lease** instead of a license key.

```python
# Before
sdk = harmoneyes_theia.TheiaSDK(license_key="your-license-key-here", platform="PL")

# After
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

The fatigue result changed from a 4-class scheme
(`0=Alert, 1=Mild, 2=Moderate, 3=Drowsy`) to 3-class:

```
0 = Alert
1 = Somewhat Fatigued
2 = Fatigued
```

Class `3` no longer exists and will never be returned. If your code has its
own label dict, update it.

### 3. Tobii G3 is now batch-only

The Tobii G3 example used to support both one-shot batch processing *and* a
`--stream-only` mode that simulated a live session from a recorded file.
Tobii G3 is now post-recorded batch data only, through a single entry point:

```python
df = pd.read_csv("recording.tsv", sep="\t", low_memory=False)
result = sdk.process_tobii_g3_data(df)   # DataFrame, ~1 row per ~1Hz window
```

`result` columns: `timestamp_s`, `cog_load_level/label/confidence`,
`fatigue_level/label/confidence`.

### 4. Webcam platform: new capture mechanism, Node.js now required

The Webcam platform's gaze engine now runs via a bundled Node.js sidecar:

```python
sdk.tracker.set_tracker(harmoneyes_theia.NexusWebcamTracker())
sdk.start_realtime_data()   # opens the camera + starts the gaze sidecar
```

- **Requires Node.js 20+ on `PATH`.** Nothing else needs installing — the
  sidecar ships inside the package.
- **Selecting a specific camera on a multi-camera machine has no supported
  mechanism yet.** This is a known gap, not something you're missing in the
  docs — flag it to support if it blocks you.

### 5. Dependencies: most of them are gone

Earlier releases pulled in roughly 45 runtime dependencies. This release
needs only:

- `numpy>=1.20`, `pandas>=1.5` (always)
- `opencv-python>=4.5.0` — only if you use `DefaultTrackerVideo` for MP4
  replay (`pip install harmoneyes-theia[video]`)

If your project pinned other dependencies specifically for this SDK, you can
likely drop them.

### 6. Installing no longer requires Git LFS

`git lfs install` is no longer a prerequisite — a plain `pip install` from
GitHub works on its own.

## What's new

- **Batch predictions from a recorded Pupil Labs Neon export** — score a
  `gaze_and_eye_state.csv` with no live device:
  ```python
  sdk = harmoneyes_theia.TheiaSDK(lease_token="...", platform="WT")
  cog_load = sdk.predict_cog_load_batch("gaze_and_eye_state.csv")
  fatigue = sdk.predict_fatigue_batch("gaze_and_eye_state.csv")
  ```
  Both accept a file path or a pre-loaded DataFrame. No scene-camera
  calibration file needed. See `examples/theia-pupil-labs-batch.py` (new).
- **Mental readiness now appears as soon as cognitive load does**, instead
  of requiring several minutes of elapsed session time before producing a
  result.
- **No session data is written to disk by default.** Earlier releases wrote
  intermediate data to a local folder on every machine running the SDK by
  default. That's disabled now — nothing is written unless you've
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
      `NexusWebcamTracker()`; drop any custom camera-device-selection logic
      (no replacement yet).
- [ ] Drop any now-unnecessary pinned dependencies.
- [ ] Remove any `git lfs install` step from your install docs/CI.
