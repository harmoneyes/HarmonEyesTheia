"""
Ganzin Sol — HarmonEyes Theia SDK Example

Connects to a Ganzin Sol eye tracker over the network, streams gaze data,
and prints real-time cognitive load and drowsiness predictions.

Prerequisites:
  1. Compile the SDK:  ./scripts/build_with_local_sdk.sh
  2. Set your license key in a .env file at the project root:
       THEIA_TEST_LICENSE_KEY=your-license-key
  3. Ensure the Ganzin Sol device is reachable at the configured IP/port.

Usage:
  python scripts/theia-ganzin-test.py
"""

import time
import uuid

import harmoneyes_theia

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GANZIN_IP = "192.168.1.100"
GANZIN_PORT = 8080

# Duration in seconds to collect data.
# Drowsiness updates every ~120s, so 400s captures at least 3 updates.
COLLECTION_DURATION = 400

# ---------------------------------------------------------------------------
# License setup
# ---------------------------------------------------------------------------

LICENSE_KEY = "your-license-key"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COG_LOAD_LABELS = {0: "Low", 1: "Moderate", 2: "High"}


def format_cog_load(prediction: int) -> str:
    """Map a numeric cognitive load prediction to a human-readable label."""
    return COG_LOAD_LABELS.get(prediction, f"Unknown ({prediction})")


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

    start_time = time.time()
    try:
        while (time.time() - start_time) < COLLECTION_DURATION:
            # Cognitive load predictions (updates every 5-second window)
            cog_levels, batch_num, _ = sdk.get_cog_load_levels()
            if cog_levels is not None:
                prediction = cog_levels["cog-load-general-smoothed"]["prediction"]
                print(f"  Cognitive Load: {format_cog_load(prediction)}")

            # Drowsiness predictions (updates every ~120 seconds)
            drowsiness, drowsiness_batch = sdk.get_drowsiness_level()
            if drowsiness is not None:
                print(f"  Drowsiness: {drowsiness}")

            # Poll at 1 Hz
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[TheiaSDK] Interrupted by user")
    finally:
        print("[TheiaSDK] Stopping session")
        sdk.stop_processing()


if __name__ == "__main__":
    main()
