"""
Theia SDK — Batch API Examples

Demonstrates how to use the Theia SDK batch prediction methods for
cognitive load and drowsiness analysis on pre-recorded gaze data.

Prerequisites:
    - A valid Theia license key (set via THEIA_LICENSE_KEY environment variable)
    - A gaze data CSV file (gaze_and_eye_state.csv) in the same directory
    - A scene camera calibration file (scene_camera.json) in the same directory

Usage:
    python test_batch_api_compiled.py
"""

import sys
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

import harmoneyes_theia

PROJECT_ROOT = Path(__file__).parent
DATA_PATH = PROJECT_ROOT / "gaze_and_eye_state.csv"
SCENE_CAMERA_JSON = "scene_camera.json"


def _create_sdk() -> harmoneyes_theia.TheiaSDK:
    """Create and return a configured TheiaSDK instance.

    The license key is read from the THEIA_LICENSE_KEY environment variable.
    Set it before running:  export THEIA_LICENSE_KEY="YOUR-LICENSE-KEY"
    """
    import os

    license_key = "your-license-key-here"
    if not license_key:
        raise RuntimeError(
            "THEIA_LICENSE_KEY environment variable is not set. "
            "Set it with: export THEIA_LICENSE_KEY=\"YOUR-LICENSE-KEY\""
        )

    return harmoneyes_theia.TheiaSDK(
        license_key=license_key,
        platform="WT",
        cog_load_prediction_method="sdk",
    )


def _print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_predict_cog_load_batch() -> bool:
    """Predict cognitive load from a CSV file path.

    Loads ~20 minutes of 200 Hz gaze data (240,000 rows) and runs batch
    cognitive load prediction. Results contain per-second predictions after
    a 20-second model warmup period.

    Each result dict contains:
        - timestamp (float): seconds from start of recording
        - value (int):       0 = low, 1 = medium, 2 = high
        - label (str):       human-readable cognitive load level
        - confidence (float): model confidence in [0.0, 1.0]
    """
    _print_header("Test 1: Cognitive Load Batch Prediction (CSV path)")

    sdk = _create_sdk()
    print("SDK initialized")

    if not DATA_PATH.exists():
        print(f"ERROR: Data file not found: {DATA_PATH}")
        return False

    print(f"Using data: {DATA_PATH.name} (240,000 rows = 20 min at 200 Hz)")

    try:
        print("\nRunning predict_cog_load_batch()...")
        print("  This may take a minute to process 20 minutes of data.")

        results = sdk.predict_cog_load_batch(
            data=str(DATA_PATH),
            n_jobs=4,
            scene_camera_json=SCENE_CAMERA_JSON,
        )

        print(f"\nPredictions returned: {len(results)}")
        print("  Expected: ~1180 (1200 seconds - 20 second warmup)")

        if len(results) == 0:
            print("  ERROR: No results returned")
            return False

        # Validate result structure
        first = results[0]
        required_keys = {"timestamp", "value", "label", "confidence"}
        if not required_keys.issubset(first.keys()):
            print(f"  ERROR: Missing keys. Expected {required_keys}, got {set(first.keys())}")
            return False

        # Validate value ranges
        if not (0 <= first["value"] <= 2):
            print(f"  ERROR: value={first['value']} out of expected range 0-2")
            return False
        if not (0.0 <= first["confidence"] <= 1.0):
            print(f"  ERROR: confidence={first['confidence']} out of expected range 0.0-1.0")
            return False

        # Display first result
        print(f"\n  First result:")
        print(f"    timestamp:  {first['timestamp']}")
        print(f"    label:      {first['label']}")
        print(f"    value:      {first['value']}")
        print(f"    confidence: {first['confidence']:.3f}")

        # Sample predictions across the full recording
        print("\n  Sample predictions (evenly spaced):")
        for i in [0, len(results) // 4, len(results) // 2, -1]:
            r = results[i]
            print(f"    t={r['timestamp']:6.1f}s  label={r['label']}  conf={r['confidence']:.3f}")

        print("\nPASSED: predict_cog_load_batch()")
        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
        return False


def test_predict_drowsiness_batch() -> bool:
    """Predict drowsiness from a CSV file path.

    Uses a prediction_stride of 120 seconds so predictions are generated
    every 2 minutes instead of every second. A timezone is required for
    the drowsiness model's time-of-day feature encoding.

    Each result dict contains:
        - timestamp (float): seconds from start of recording
        - value (int):       0 = alert, 1 = mild, 2 = moderate, 3 = severe
        - label (str):       human-readable drowsiness level
        - confidence (float): model confidence in [0.0, 1.0]
    """
    _print_header("Test 2: Drowsiness Batch Prediction (CSV path)")

    sdk = _create_sdk()
    print("SDK initialized")

    if not DATA_PATH.exists():
        print(f"ERROR: Data file not found: {DATA_PATH}")
        return False

    print(f"Using data: {DATA_PATH.name}")

    try:
        # Timezone is required — the drowsiness model uses time-of-day as a feature
        tz = ZoneInfo("America/New_York")

        print("\nRunning predict_drowsiness_batch()...")
        print("  prediction_stride=120  (one prediction every 2 minutes)")
        print(f"  timezone={tz}")

        results = sdk.predict_drowsiness_batch(
            data=str(DATA_PATH),
            timezone=tz,
            prediction_stride=120,
            n_jobs=4,
            scene_camera_json=SCENE_CAMERA_JSON,
        )

        print(f"\nPredictions returned: {len(results)}")
        print("  Expected: ~9 (20 min of data, every 120 sec, with warmup)")

        if len(results) == 0:
            print("  ERROR: No results returned")
            return False

        # Validate result structure
        first = results[0]
        required_keys = {"timestamp", "value", "label", "confidence"}
        if not required_keys.issubset(first.keys()):
            print(f"  ERROR: Missing keys. Expected {required_keys}, got {set(first.keys())}")
            return False

        if not (0 <= first["value"] <= 3):
            print(f"  ERROR: value={first['value']} out of expected range 0-3")
            return False

        # With stride=120, there are few enough predictions to display them all
        print("\n  All predictions:")
        for r in results:
            print(f"    t={r['timestamp']:6.1f}s  drowsiness={r['label']}")

        print("\nPASSED: predict_drowsiness_batch()")
        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
        return False


def test_batch_api_with_dataframe() -> bool:
    """Predict cognitive load from a pandas DataFrame (instead of a CSV path).

    The batch API accepts either a file path (str) or a pandas DataFrame.
    This test loads the CSV into a DataFrame, takes a 50-second subset
    (10,000 rows at 200 Hz), and passes it directly to the SDK.
    """
    _print_header("Test 3: Cognitive Load Batch Prediction (DataFrame input)")

    sdk = _create_sdk()
    print("SDK initialized")

    try:
        print(f"\nLoading {DATA_PATH.name} into a DataFrame...")
        df = pd.read_csv(DATA_PATH)
        print(f"  Full dataset: {len(df):,} rows")

        # Use a small subset for faster execution
        df_subset = df.head(10_000)
        print(f"  Using first 10,000 rows (50 seconds at 200 Hz)")

        print("\nRunning predict_cog_load_batch() with DataFrame input...")
        results = sdk.predict_cog_load_batch(
            data=df_subset,
            n_jobs=4,
            scene_camera_json=SCENE_CAMERA_JSON,
        )

        print(f"\nPredictions returned: {len(results)}")
        print("  Expected: ~30 (50 seconds - 20 second warmup)")

        if len(results) > 0:
            print("\n  First 5 predictions:")
            for r in results[:5]:
                print(f"    t={r['timestamp']:6.1f}s  label={r['label']}  conf={r['confidence']:.3f}")

        print("\nPASSED: predict_cog_load_batch() with DataFrame input")
        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
        return False


def main() -> int:
    """Run all batch API examples and print a summary."""
    _print_header("Theia SDK — Batch API Examples")
    print(f"Data file:    {DATA_PATH}")
    print(f"Scene camera: {SCENE_CAMERA_JSON}")

    results = {
        "predict_cog_load_batch (CSV)":       test_predict_cog_load_batch(),
        "predict_drowsiness_batch (CSV)":     test_predict_drowsiness_batch(),
        "predict_cog_load_batch (DataFrame)": test_batch_api_with_dataframe(),
    }

    # Summary
    _print_header("Summary")
    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"  [{status}] {name}")

    print(f"\n{passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
