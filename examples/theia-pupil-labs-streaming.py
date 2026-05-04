"""
Pupil Labs Neon — HarmonEyes Theia SDK Example

Connects to a Pupil Labs Neon eye tracker, streams gaze data,
and prints real-time mental workload and fatigue predictions.

Prerequisites:
  1. Set your license key below or in a .env file at the project root.
  2. Ensure the Pupil Labs Neon device is paired and reachable.

Usage:
  python theia-pupil-labs-streaming.py
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
# Drowsiness updates every ~120s, so 400s captures at least 3 updates.
COLLECTION_DURATION = 400

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COG_LOAD_LABELS = {0: "Low", 1: "Moderate", 2: "High"}

# Output directory for CSV files
OUTPUT_DIR = "results"


def format_mental_workload(prediction: int) -> str:
    """Map a numeric mental workload prediction to a human-readable label."""
    return COG_LOAD_LABELS.get(prediction, f"Unknown ({prediction})")


def save_results_to_csv(results: list[dict], session_id: str) -> str:
    """Save collected results to a CSV file and return the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pupil_labs_session_{timestamp}_{session_id[:8]}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = ["timestamp", "elapsed_s", "mental_workload", "mental_workload_label", "fatigue"]
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
    # Initialize the SDK with the Pupil Labs Neon platform
    sdk = harmoneyes_theia.TheiaSDK(
        license_key=LICENSE_KEY,
        platform="PL",  # Pupil Labs Neon
    )

    session_id = str(uuid.uuid4())

    print(f"[TheiaSDK] Starting session {session_id}")
    sdk.start_new_session(session_uuid=session_id)

    print("[TheiaSDK] Starting data stream")
    sdk.start_realtime_data()

    results = []
    start_time = time.time()
    try:
        while (time.time() - start_time) < COLLECTION_DURATION:
            elapsed = time.time() - start_time
            row = {
                "timestamp": datetime.now().isoformat(),
                "elapsed_s": round(elapsed, 2),
                "mental_workload": None,
                "mental_workload_label": None,
                "fatigue": None,
            }

            # Mental workload predictions (updates every 5-second window)
            try:
                mw_levels, batch_num, _ = sdk.get_mental_workload_levels()
                if mw_levels is not None:
                    prediction = mw_levels["cog-load-general-smoothed"]["prediction"]
                    row["mental_workload"] = prediction
                    row["mental_workload_label"] = format_mental_workload(prediction)
                    print(f"  Mental Workload: {format_mental_workload(prediction)}")
            except AttributeError:
                pass  # SDK not ready yet (warmup period)

            # Fatigue predictions (updates every ~120 seconds)
            try:
                fatigue, fatigue_batch = sdk.get_fatigue_level()
                if fatigue is not None:
                    row["fatigue"] = fatigue
                    print(f"  Fatigue: {fatigue}")
            except AttributeError:
                pass  # SDK not ready yet (warmup period)

            results.append(row)

            # Poll at 1 Hz
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
