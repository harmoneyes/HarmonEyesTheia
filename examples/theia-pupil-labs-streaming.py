"""
Pupil Labs Neon — HarmonEyes Theia SDK Example

Connects to a Pupil Labs Neon eye tracker, streams gaze data,
and prints real-time cognitive load and drowsiness predictions.

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


def format_cog_load(prediction: int) -> str:
    """Map a numeric cognitive load prediction to a human-readable label."""
    return COG_LOAD_LABELS.get(prediction, f"Unknown ({prediction})")


def save_results_to_csv(results: list[dict], session_id: str) -> str:
    """Save collected results to a CSV file and return the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pupil_labs_session_{timestamp}_{session_id[:8]}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = ["timestamp", "elapsed_s", "cognitive_load", "cognitive_load_label", "drowsiness"]
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
                "cognitive_load": None,
                "cognitive_load_label": None,
                "drowsiness": None,
            }

            # Cognitive load predictions (updates every 5-second window)
            try:
                cog_levels, batch_num, _ = sdk.get_cog_load_levels()
                if cog_levels is not None:
                    prediction = cog_levels["cog-load-general-smoothed"]["prediction"]
                    row["cognitive_load"] = prediction
                    row["cognitive_load_label"] = format_cog_load(prediction)
                    print(f"  Cognitive Load: {format_cog_load(prediction)}")
            except AttributeError:
                pass  # SDK not ready yet (warmup period)

            # Drowsiness predictions (updates every ~120 seconds)
            try:
                drowsiness, drowsiness_batch = sdk.get_drowsiness_level()
                if drowsiness is not None:
                    row["drowsiness"] = drowsiness
                    print(f"  Drowsiness: {drowsiness}")
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
