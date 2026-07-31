"""
HarmonEyes Theia SDK Example: Ganzin Sol

Connects to a Ganzin Sol eye tracker over the network, streams gaze data,
and prints real-time cognitive load and fatigue predictions.

Prerequisites:
  1. export THEIA_LICENSE_KEY=...      # SDK license
  2. Ensure the Ganzin Sol device is reachable at the configured IP/port.

Usage:
  python theia-ganzin-streaming.py
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

GANZIN_IP = "192.168.1.100"
GANZIN_PORT = 8080

# Duration in seconds to collect data.
# Fatigue updates every ~120s, so 400s captures at least 3 updates.
COLLECTION_DURATION = 400

# ---------------------------------------------------------------------------
# License setup
# ---------------------------------------------------------------------------

LICENSE_KEY = os.environ.get("THEIA_LICENSE_KEY", "your-license-key")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COG_LOAD_LABELS = {0: "Low", 1: "Moderate", 2: "High"}
FATIGUE_LABELS = {0: "Alert", 1: "Mild", 2: "Moderate", 3: "Drowsy"}

# Output directory for CSV files
OUTPUT_DIR = "results"


def format_cog_load(prediction: int) -> str:
    """Map a numeric cognitive load prediction to a human-readable label."""
    return COG_LOAD_LABELS.get(prediction, f"Unknown ({prediction})")


def format_fatigue(level: int) -> str:
    """Map a numeric fatigue level to a human-readable label."""
    return FATIGUE_LABELS.get(level, f"Unknown ({level})")


def save_results_to_csv(results: list[dict], session_id: str) -> str:
    """Save collected results to a CSV file and return the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ganzin_session_{timestamp}_{session_id[:8]}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = ["timestamp", "elapsed_s", "cog_load", "cog_load_label", "fatigue", "fatigue_label"]
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
    # Initialize the SDK with the Ganzin Sol platform
    sdk = harmoneyes_theia.TheiaSDK(
        license_key=LICENSE_KEY,
        platform="Ganzin",
    )
    sdk.ip = GANZIN_IP
    sdk.port = GANZIN_PORT

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
                "cog_load": None,
                "cog_load_label": None,
                "fatigue": None,
                "fatigue_label": None,
            }

            # Cognitive load predictions (updates every 5-second window)
            try:
                cog_levels, batch_num, _ = sdk.get_cog_load_levels()
                if cog_levels:
                    # levels is keyed by model name ("general" / "hierarchical");
                    # take whichever model produced this window.
                    prediction = next(iter(cog_levels.values()))["prediction"]
                    row["cog_load"] = prediction
                    row["cog_load_label"] = format_cog_load(prediction)
                    print(f"  Cognitive Load: {format_cog_load(prediction)}")
            except AttributeError:
                pass  # SDK not ready yet (warmup period)

            # Fatigue predictions (updates every ~120 seconds)
            try:
                fatigue, fatigue_batch = sdk.get_fatigue_level()
                if fatigue:
                    # keyed by model name; take whichever produced this window.
                    level = next(iter(fatigue.values()))
                    row["fatigue"] = level
                    row["fatigue_label"] = format_fatigue(level)
                    print(f"  Fatigue: {format_fatigue(level)}")
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
