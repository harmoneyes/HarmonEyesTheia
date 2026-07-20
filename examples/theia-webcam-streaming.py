"""
HarmonEyes Theia SDK Example: Webcam

Requirements
------------
  * A valid license key (set ``THEIA_LICENSE_KEY`` or edit below).
  * **Node.js 20+** on your PATH (the gaze sidecar runs on Node).
  * A connected webcam.

Usage:
  export THEIA_LICENSE_KEY=...      # SDK license
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

LICENSE_KEY = os.environ.get("THEIA_LICENSE_KEY", "your-license-key-here")

# Duration in seconds to collect data.
# Fatigue updates every ~120s, so 400s captures at least 3 updates.
COLLECTION_DURATION = 400

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COG_LOAD_LABELS = {0: "Low", 1: "Moderate", 2: "High"}
DROWSINESS_LABELS = {0: "Alert", 1: "Mild", 2: "Moderate", 3: "Drowsy"}

OUTPUT_DIR = "results"


def format_cog_load(prediction: int) -> str:
    """Map a numeric cognitive load prediction to a human-readable label."""
    return COG_LOAD_LABELS.get(prediction, f"Unknown ({prediction})")


def format_drowsiness(level: int) -> str:
    """Map a numeric drowsiness level to a human-readable label."""
    return DROWSINESS_LABELS.get(level, f"Unknown ({level})")


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
        "drowsiness",
        "drowsiness_label",
        "attention_level",
        "attention_label",
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

    # Inject the Tobii Nexus webcam gaze source. Spawning it (below, on
    # start_realtime_data) opens the camera and starts the Node gaze sidecar.
    sdk.tracker.set_tracker(harmoneyes_theia.NexusWebcamTracker())

    # Mental readiness normally requires 10 minutes; lower the gate for short sessions.
    sdk.set_mental_fatigue_min_session_seconds(30)

    session_id = str(uuid.uuid4())

    print(f"[TheiaSDK] Starting session {session_id}")
    sdk.start_new_session(session_uuid=session_id)

    print("[TheiaSDK] Starting webcam + gaze sidecar")
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
                "cog_load": None,
                "cog_load_label": None,
                "drowsiness": None,
                "drowsiness_label": None,
                "attention_level": None,
                "attention_label": None,
            }

            parts = []

            try:
                cog_levels, _, lookahead = sdk.get_cog_load_levels()
                if cog_levels is not None:
                    prediction = next(iter(cog_levels.values()))["prediction"]
                    label = format_cog_load(prediction)
                    row["cog_load"] = prediction
                    row["cog_load_label"] = label
                    cog_str = f"CogLoad={label}"
                    if lookahead is not None:
                        cog_str += f"({lookahead:.3f})"
                    parts.append(cog_str)
            except AttributeError:
                pass

            try:
                drowsiness, _ = sdk.get_drowsiness_level()
                if drowsiness is not None:
                    drowsiness_value = next(iter(drowsiness.values()))
                    drowsiness_label = format_drowsiness(drowsiness_value)
                    row["drowsiness"] = drowsiness_value
                    row["drowsiness_label"] = drowsiness_label
                    parts.append(f"Drowsiness={drowsiness_label}")
            except AttributeError:
                pass

            try:
                attention = sdk.get_attention_style()
                if attention is not None:
                    row["attention_level"] = attention["level"]
                    row["attention_label"] = attention["label"]
                    parts.append(
                        f"Attention={attention['label']}(lvl {attention['level']})"
                    )
            except AttributeError:
                pass

            try:
                mental_readiness = sdk.get_mental_fatigue(elapsed_seconds=elapsed)
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
