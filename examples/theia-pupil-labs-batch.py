"""
HarmonEyes Theia SDK Example: Pupil Labs Neon Batch

Demonstrates how to use the Theia SDK batch prediction methods for
cognitive load and fatigue analysis on a pre-recorded Pupil Labs Neon
export. Runs the recording through the native ACE feature pipeline (the
same one a live Neon session uses) and scores each window with the ACE
cognitive-load and fatigue predictors.

Prerequisites:
    - export THEIA_API_KEY_ID=... THEIA_API_KEY_SECRET=...   # your HarmonEyes API key
      (see the README, "Device Lease")
    - A Pupil Cloud "gaze_and_eye_state.csv" export in the same directory

No scene-camera calibration file is needed: Neon's own Cloud export already
carries 3D optical-axis vectors directly (unlike older Pupil Core exports).

Usage:
    python theia-pupil-labs-batch.py
"""

import sys
import traceback
from pathlib import Path

import pandas as pd

import harmoneyes_theia

PROJECT_ROOT = Path(__file__).parent
DATA_PATH = PROJECT_ROOT / "gaze_and_eye_state.csv"


def _create_sdk() -> harmoneyes_theia.TheiaSDK:
    """Create and return a configured TheiaSDK instance."""
    try:
        return harmoneyes_theia.TheiaSDK(
            platform="WT",
        )
    except harmoneyes_theia.LeaseVerificationError as e:
        sys.exit(
            f"[TheiaSDK] Lease rejected: {e}\n"
            "Set THEIA_API_KEY_ID and THEIA_API_KEY_SECRET to your HarmonEyes API key "
            "(see the README, \"Device Lease\")."
        )


def _print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_predict_cog_load_batch() -> bool:
    """Predict cognitive load from a CSV file path.

    Results contain per-window predictions (~1 Hz) after a ~30-second model
    warmup period (10s calibration + 20s first window).

    Each result dict contains:
        - timestamp (float): seconds from start of recording
        - value (int):       0 = low, 1 = moderate, 2 = high
        - label (str):       human-readable cognitive load level
        - confidence (float): model confidence in [0.0, 1.0]
    """
    _print_header("Test 1: Cognitive Load Batch Prediction (CSV path)")

    sdk = _create_sdk()
    print("SDK initialized")

    if not DATA_PATH.exists():
        print(f"ERROR: Data file not found: {DATA_PATH}")
        return False

    print(f"Using data: {DATA_PATH.name}")

    try:
        print("\nRunning predict_cog_load_batch()...")

        results = sdk.predict_cog_load_batch(str(DATA_PATH))

        print(f"\nPredictions returned: {len(results)}")

        if len(results) == 0:
            print("  ERROR: No results returned")
            return False

        # Validate result structure
        first = results[0]
        required_keys = {"timestamp", "value", "label", "confidence"}
        if not required_keys.issubset(first.keys()):
            print(
                f"  ERROR: Missing keys. Expected {required_keys}, got {set(first.keys())}"
            )
            return False

        # Validate value ranges
        if not (0 <= first["value"] <= 2):
            print(f"  ERROR: value={first['value']} out of expected range 0-2")
            return False
        if not (0.0 <= first["confidence"] <= 1.0):
            print(
                f"  ERROR: confidence={first['confidence']} out of expected range 0.0-1.0"
            )
            return False

        # Display first result
        print("\n  First result:")
        print(f"    timestamp:  {first['timestamp']}")
        print(f"    label:      {first['label']}")
        print(f"    value:      {first['value']}")
        print(f"    confidence: {first['confidence']:.3f}")

        # Sample predictions across the full recording
        print("\n  Sample predictions (evenly spaced):")
        for i in [0, len(results) // 4, len(results) // 2, -1]:
            r = results[i]
            print(
                f"    t={r['timestamp']:6.1f}s  label={r['label']}  conf={r['confidence']:.3f}"
            )

        print("\nPASSED: predict_cog_load_batch()")
        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
        return False


def test_predict_fatigue_batch() -> bool:
    """Predict fatigue from a CSV file path.

    Fatigue's rolling window (~120s) only emits periodically, so this
    returns far fewer entries than predict_cog_load_batch() — one per
    emitted result, not one per window.

    Each result dict contains:
        - timestamp (float): seconds from start of recording
        - value (int):       0 = alert, 1 = somewhat fatigued, 2 = fatigued
        - label (str):       human-readable fatigue level
        - confidence (float): model confidence in [0.0, 1.0]
    """
    _print_header("Test 2: Fatigue Batch Prediction (CSV path)")

    sdk = _create_sdk()
    print("SDK initialized")

    if not DATA_PATH.exists():
        print(f"ERROR: Data file not found: {DATA_PATH}")
        return False

    print(f"Using data: {DATA_PATH.name}")

    try:
        print("\nRunning fatigue batch prediction...")

        results = sdk.predict_fatigue_batch(str(DATA_PATH))

        print(f"\nPredictions returned: {len(results)}")

        if len(results) == 0:
            print("  No fatigue results emitted — recording is likely too "
                  "short (fatigue needs ~120s of data after warmup).")
            return True

        first = results[0]
        required_keys = {"timestamp", "value", "label", "confidence"}
        if not required_keys.issubset(first.keys()):
            print(
                f"  ERROR: Missing keys. Expected {required_keys}, got {set(first.keys())}"
            )
            return False

        if not (0 <= first["value"] <= 2):
            print(f"  ERROR: value={first['value']} out of expected range 0-2")
            return False

        print("\n  All predictions:")
        for r in results:
            print(f"    t={r['timestamp']:6.1f}s  fatigue={r['label']}")

        print("\nPASSED: fatigue batch prediction")
        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
        return False


def test_batch_api_with_dataframe() -> bool:
    """Predict cognitive load from a pandas DataFrame (instead of a CSV path).

    Both batch methods accept either a file path (str) or a pandas
    DataFrame read from one.
    """
    _print_header("Test 3: Cognitive Load Batch Prediction (DataFrame input)")

    sdk = _create_sdk()
    print("SDK initialized")

    if not DATA_PATH.exists():
        print(f"ERROR: Data file not found: {DATA_PATH}")
        return False

    try:
        print(f"\nLoading {DATA_PATH.name} into a DataFrame...")
        df = pd.read_csv(DATA_PATH)
        print(f"  {len(df):,} rows")

        print("\nRunning predict_cog_load_batch() with DataFrame input...")
        results = sdk.predict_cog_load_batch(df)

        print(f"\nPredictions returned: {len(results)}")

        if len(results) > 0:
            print("\n  First 5 predictions:")
            for r in results[:5]:
                print(
                    f"    t={r['timestamp']:6.1f}s  label={r['label']}  conf={r['confidence']:.3f}"
                )

        print("\nPASSED: predict_cog_load_batch() with DataFrame input")
        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
        return False


def main() -> int:
    """Run all batch API examples and print a summary."""
    _print_header("Theia SDK — Batch API Examples")
    print(f"Data file: {DATA_PATH}")

    results = {
        "Cognitive Load Batch (CSV)": test_predict_cog_load_batch(),
        "Fatigue Batch (CSV)": test_predict_fatigue_batch(),
        "Cognitive Load Batch (DataFrame)": test_batch_api_with_dataframe(),
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
