"""
Tobii Pro Glasses 3 — HarmonEyes Theia SDK Examples

Demonstrates batch and streaming processing of Tobii G3 gaze data.

  Batch:     Loads a full TSV export and processes it in one call,
             returning per-second mental workload and drowsiness predictions.

  Streaming: Feeds the same TSV one Eye Tracker row at a time, simulating
             a live session and polling for predictions as they arrive.

Prerequisites:
  1. Set LICENSE_KEY and TSV_PATH below.
  2. pip install harmoneyes-theia pandas

Usage:
  python theia-tobii-g3.py
  python theia-tobii-g3.py --batch-only
  python theia-tobii-g3.py --stream-only
  python theia-tobii-g3.py --rows 1000      # limit ET rows in streaming test
"""

import argparse
import sys
import time
import uuid
from collections import Counter
from pathlib import Path

import pandas as pd

import harmoneyes_theia

# ---------------------------------------------------------------------------
# Configuration — set these before running
# ---------------------------------------------------------------------------

LICENSE_KEY = "your-license-key-here"
TSV_PATH = Path("path/to/recording.tsv")  # Tobii G3 export TSV

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MW_LABELS = {0: "Low", 1: "Moderate", 2: "High"}
FATIGUE_LABELS = {0: "Alert", 1: "Mild", 2: "Moderate", 3: "Drowsy"}


def _print_header(title: str) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print("=" * 62)


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

def run_batch(tsv_df: pd.DataFrame) -> pd.DataFrame:
    """Process a full TSV export and return per-second predictions."""
    _print_header("BATCH — process_tobii_g3_data()")

    sdk = harmoneyes_theia.TheiaSDK(
        license_key=LICENSE_KEY,
        platform="WT",
    )

    t0 = time.perf_counter()
    result = sdk.process_tobii_g3_data(tsv_df)
    elapsed = time.perf_counter() - t0

    print(f"  {len(result)} second-windows in {elapsed:.1f}s")
    print(f"  Columns: {list(result.columns)}")

    if "mental_workload_general_level" in result.columns:
        col = result["mental_workload_general_level"].dropna()
        dist = dict(sorted(Counter(col.astype(int)).items()))
        print(f"  mental_workload_general_level  non-null={len(col)}/{len(result)}  dist={dist}")

    if "drowsiness_level" in result.columns:
        col = result["drowsiness_level"].dropna()
        dist = dict(sorted(Counter(col.astype(int)).items()))
        print(f"  drowsiness_level               non-null={len(col)}/{len(result)}  dist={dist}")

    display_cols = [
        "timestamp_s",
        "mental_workload_general_level",
        "drowsiness_level",
    ]
    display_cols = [c for c in display_cols if c in result.columns]
    print(f"\n  First 10 rows:")
    print(result[display_cols].head(10).to_string(index=False))

    return result


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

def run_streaming(tsv_df: pd.DataFrame, max_et_rows: int | None) -> list[dict]:
    """Feed ET rows one at a time and poll for real-time predictions."""
    _print_header("STREAMING — start_tobii_g3_stream() + push_tobii_g3_chunk()")

    et_rows = tsv_df[tsv_df["Sensor"] == "Eye Tracker"].copy().reset_index(drop=True)
    if max_et_rows:
        et_rows = et_rows.head(max_et_rows)

    print(f"  {len(et_rows)} ET rows to feed one-by-one")

    sdk = harmoneyes_theia.TheiaSDK(
        license_key=LICENSE_KEY,
        platform="WT",
    )

    sdk.start_new_session(session_uuid=str(uuid.uuid4()))
    sdk.start_tobii_g3_stream(sample_rate=50)

    t0 = time.perf_counter()
    for i in range(len(et_rows)):
        sdk.push_tobii_g3_chunk(et_rows.iloc[i : i + 1])
    print(f"  All rows pushed in {time.perf_counter() - t0:.2f}s — waiting for processing loop to drain...")

    # Poll for predictions until none arrive for 5 consecutive seconds.
    # get_mental_workload_levels() returns the latest prediction and clears it,
    # so each non-None result is a newly completed processing window.
    predictions: list[dict] = []
    stable = 0
    for _ in range(120):
        time.sleep(1)

        mw_levels = None
        fatigue = None

        try:
            mw_levels, batch_num, _ = sdk.get_mental_workload_levels()
        except Exception:
            batch_num = None

        try:
            fatigue, _ = sdk.get_fatigue_level()
        except Exception:
            pass

        if mw_levels is not None or fatigue is not None:
            predictions.append({
                "batch": batch_num,
                "mental_workload": dict(mw_levels) if mw_levels else None,
                "fatigue": fatigue,
            })
            sys.stdout.write(f"\r  {len(predictions)} predictions received...")
            sys.stdout.flush()
            stable = 0
        else:
            stable += 1
            if stable >= 5:
                break

    sdk.stop_processing()
    print()

    print(f"  Finished in {time.perf_counter() - t0:.1f}s — {len(predictions)} prediction snapshots captured")

    if predictions:
        mw_with_pred = [p for p in predictions if p["mental_workload"]]
        if mw_with_pred:
            all_levels = []
            for p in mw_with_pred:
                for data in p["mental_workload"].values():
                    lvl = data.get("prediction") if isinstance(data, dict) else data
                    if lvl is not None:
                        all_levels.append(int(lvl))
                    break  # first model key only for distribution summary
            dist = dict(sorted(Counter(all_levels).items()))
            print(f"  Mental workload distribution: {dist}")

        print(f"\n  First 10 predictions:")
        for p in predictions[:10]:
            mw = p["mental_workload"]
            if mw:
                data = next(iter(mw.values()))
                lvl = data.get("prediction") if isinstance(data, dict) else data
                conf = data.get("confidence") if isinstance(data, dict) else None
                conf_str = f"  conf={conf:.2f}" if conf is not None else ""
                print(f"    batch={str(p['batch']):>4}  MW={MW_LABELS.get(lvl, lvl)}({lvl}){conf_str}")

    return predictions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tsv", type=Path, default=TSV_PATH,
                        help="Path to Tobii G3 export TSV (default: TSV_PATH constant)")
    parser.add_argument("--rows", type=int, default=None,
                        help="Max ET rows fed to the streaming test (default: all)")
    parser.add_argument("--batch-only", action="store_true")
    parser.add_argument("--stream-only", action="store_true")
    args = parser.parse_args()

    if not args.tsv.exists():
        sys.exit(f"ERROR: TSV not found: {args.tsv}")

    print(f"Loading {args.tsv.name} ...")
    tsv_df = pd.read_csv(args.tsv, sep="\t", low_memory=False)
    et_count = (tsv_df["Sensor"] == "Eye Tracker").sum()
    print(f"  {len(tsv_df):,} total rows, {et_count:,} Eye Tracker rows")

    batch_result = stream_result = None

    if not args.stream_only:
        batch_result = run_batch(tsv_df)

    if not args.batch_only:
        stream_result = run_streaming(tsv_df, args.rows)

    if batch_result is not None and stream_result is not None:
        _print_header("SUMMARY")
        print(f"  Batch:     {len(batch_result)} second-windows returned")
        print(f"  Streaming: {len(stream_result)} prediction snapshots captured")
        if "mental_workload_general_level" in batch_result.columns:
            b_nn = batch_result["mental_workload_general_level"].notna().sum()
            print(f"  Batch MW predictions:     {b_nn}/{len(batch_result)}")
            print(f"  Streaming MW predictions: {len([p for p in stream_result if p['mental_workload']])}/{len(stream_result)}")

    print("\nDone.")


if __name__ == "__main__":
    main()
