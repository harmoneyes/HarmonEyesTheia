"""
Webcam — HarmonEyes Theia SDK Example

Uses the device webcam to stream gaze data and prints real-time
mental workload, fatigue, attention, and mental readiness predictions.

Prerequisites:
  1. Set your license key below.
  2. Ensure your webcam is accessible.

Usage:
  python theia-webcam-streaming.py
"""

import csv
import os
import time
import uuid
from datetime import datetime

import harmoneyes_theia

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LICENSE_KEY = "your-license-key-here"

# Duration in seconds to collect data.
# Fatigue updates every ~120s, so 400s captures at least 3 updates.
COLLECTION_DURATION = 400

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MW_LABELS = {0: "Low", 1: "Moderate", 2: "High"}
FATIGUE_LABELS = {0: "Alert", 1: "Mild", 2: "Moderate", 3: "Drowsy"}

OUTPUT_DIR = "results"


def format_mental_workload(prediction: int) -> str:
    """Map a numeric mental workload prediction to a human-readable label."""
    return MW_LABELS.get(prediction, f"Unknown ({prediction})")


def format_fatigue(level: int) -> str:
    """Map a numeric fatigue level to a human-readable label."""
    return FATIGUE_LABELS.get(level, f"Unknown ({level})")


def save_results_to_csv(results: list[dict], session_id: str) -> str:
    """Save collected results to a CSV file and return the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"webcam_session_{timestamp}_{session_id[:8]}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = [
        "timestamp", "elapsed_s",
        "mental_workload", "mental_workload_label",
        "fatigue", "fatigue_label",
        "attention_level", "attention_label",
    ]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"[TheiaSDK] Results saved to {filepath} ({len(results)} rows)")
    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    sdk = harmoneyes_theia.TheiaSDK(
        license_key=LICENSE_KEY,
        platform="Webcam",
    )

    # Mental readiness normally requires 10 minutes; lower the gate for short sessions.
    sdk.set_mental_readiness_min_session_seconds(30)

    session_id = str(uuid.uuid4())

    print(f"[TheiaSDK] Starting session {session_id}")
    sdk.start_new_session(session_uuid=session_id)

    print("[TheiaSDK] Starting data stream")
    sdk.start_realtime_data()

    results = []
    start_time = time.time()

    print(f"Collecting data for {COLLECTION_DURATION}s — Ctrl+C to stop early\n")

    try:
        while (time.time() - start_time) < COLLECTION_DURATION:
            elapsed = time.time() - start_time
            row = {
                "timestamp": datetime.now().isoformat(),
                "elapsed_s": round(elapsed, 2),
                "mental_workload": None,
                "mental_workload_label": None,
                "fatigue": None,
                "fatigue_label": None,
                "attention_level": None,
                "attention_label": None,
            }

            parts = []

            try:
                mw_levels, _, lookahead = sdk.get_mental_workload_levels()
                if mw_levels is not None:
                    prediction = next(iter(mw_levels.values()))["prediction"]
                    label = format_mental_workload(prediction)
                    row["mental_workload"] = prediction
                    row["mental_workload_label"] = label
                    mw_str = f"MW={label}"
                    if lookahead is not None:
                        mw_str += f"({lookahead:.3f})"
                    parts.append(mw_str)
            except AttributeError:
                pass

            try:
                fatigue, _ = sdk.get_fatigue_level()
                if fatigue is not None:
                    fatigue_value = next(iter(fatigue.values()))
                    fatigue_label = format_fatigue(fatigue_value)
                    row["fatigue"] = fatigue_value
                    row["fatigue_label"] = fatigue_label
                    parts.append(f"Fatigue={fatigue_label}")
            except AttributeError:
                pass

            try:
                attention = sdk.get_attention()
                if attention is not None:
                    row["attention_level"] = attention["level"]
                    row["attention_label"] = attention["label"]
                    parts.append(f"Attention={attention['label']}(lvl {attention['level']})")
            except AttributeError:
                pass

            try:
                mental_readiness = sdk.get_mental_readiness(elapsed_seconds=elapsed)
                if mental_readiness is not None:
                    parts.append(
                        f"Readiness: lo={mental_readiness['low_percentage']:.1f}%"
                        f" mod={mental_readiness['moderate_percentage']:.1f}%"
                        f" hi={mental_readiness['high_percentage']:.1f}%"
                    )
            except AttributeError:
                pass

            status = "  |  ".join(parts) if parts else "(warming up...)"
            print(f"[{elapsed:5.1f}s] {status}", flush=True)

            results.append(row)
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[TheiaSDK] Interrupted by user")
    finally:
        print("[TheiaSDK] Stopping session")
        sdk.stop_processing()
        if results:
            save_results_to_csv(results, session_id)


if __name__ == "__main__":
    main()
