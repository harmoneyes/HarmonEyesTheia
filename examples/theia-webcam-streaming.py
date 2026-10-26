"""
HarmonEyes Theia SDK Example: Webcam

Requirements
------------
  * Your HarmonEyes API key in THEIA_API_KEY_ID and THEIA_API_KEY_SECRET
    (see the README, "Device Lease").
  * About 160 MB of free disk in your home directory: the first start unpacks
    the gaze sidecar into ~/.theia/webcam-sidecar/.
  * A connected webcam.

Usage:
  python theia-webcam-streaming.py
"""

import csv
import os
import sys
import time
import uuid
from datetime import datetime

import harmoneyes_theia

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Duration in seconds to collect data.
# Fatigue updates every ~120s, so 400s captures at least 3 updates.
COLLECTION_DURATION = 400

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COG_LOAD_LABELS = {0: "Low", 1: "Moderate", 2: "High"}
FATIGUE_LABELS = {0: "Alert", 1: "Somewhat Fatigued", 2: "Fatigued"}

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
    filename = f"webcam_session_{timestamp}_{session_id[:8]}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = [
        "timestamp",
        "elapsed_s",
        "cog_load",
        "cog_load_label",
        "fatigue",
        "fatigue_label",
        "attention_level",
        "attention_label",
    ]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"[TheiaSDK] Results saved to {filepath} ({len(results)} rows)")
    return filepath


def results_line(sdk, cog_load: str, fatigue: str) -> str:
    """Every result on one line. Cognitive load and fatigue are the newest the
    SDK handed over; attention style and mental readiness are running states,
    read on the spot."""
    attention = sdk.get_attention_style()
    readiness = sdk.get_mental_readiness()
    return (f"Cognitive load: {cog_load} | Fatigue: {fatigue} | "
            f"Attention: {attention['label'] if attention else 'not yet'} | "
            f"Mental readiness: {readiness['label'] if readiness else 'not yet'}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    try:
        sdk = harmoneyes_theia.TheiaSDK(
            platform="Webcam",
        )
    except harmoneyes_theia.LeaseVerificationError as e:
        sys.exit(
            f"[TheiaSDK] Lease rejected: {e}\n"
            "Set THEIA_API_KEY_ID and THEIA_API_KEY_SECRET to your HarmonEyes API key "
            "(see the README, \"Device Lease\")."
        )

    # Inject the Tobii Nexus webcam gaze source. Spawning it (below, on
    # start_realtime_data) opens the camera and starts the gaze sidecar.
    sdk.tracker.set_tracker(harmoneyes_theia.NexusWebcamTracker())

    session_id = str(uuid.uuid4())

    print(f"[TheiaSDK] Starting session {session_id}")
    sdk.start_new_session(session_uuid=session_id)

    print("[TheiaSDK] Starting webcam + gaze sidecar")
    sdk.start_realtime_data()

    results = []
    start_time = time.time()

    print(f"Collecting data for {COLLECTION_DURATION}s — Ctrl+C to stop early\n")

    # get_cog_load_levels() and get_fatigue_level() hand over each result once,
    # so keep the newest for the printed line.
    cog_load_now, fatigue_now = "warming up", "not yet"
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
                "attention_level": None,
                "attention_label": None,
            }

            try:
                cog_levels, _, _ = sdk.get_cog_load_levels()
                if cog_levels is not None:
                    prediction = next(iter(cog_levels.values()))["prediction"]
                    label = format_cog_load(prediction)
                    row["cog_load"] = prediction
                    row["cog_load_label"] = label
                    cog_load_now = label
            except AttributeError:
                pass

            try:
                fatigue, _ = sdk.get_fatigue_level()
                if fatigue is not None:
                    fatigue_value = next(iter(fatigue.values()))
                    fatigue_label = format_fatigue(fatigue_value)
                    row["fatigue"] = fatigue_value
                    row["fatigue_label"] = fatigue_label
                    fatigue_now = fatigue_label
            except AttributeError:
                pass

            try:
                attention = sdk.get_attention_style()
                if attention is not None:
                    row["attention_level"] = attention["level"]
                    row["attention_label"] = attention["label"]
            except AttributeError:
                pass

            print(f"[{elapsed:5.1f}s] {results_line(sdk, cog_load_now, fatigue_now)}", flush=True)

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
