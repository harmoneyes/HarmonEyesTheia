"""
HarmonEyes Theia SDK Example: Tobii Pro Glasses 3

Tobii G3 is processed as POST-RECORDED BATCH data only — there is no real-time
streaming API. Load a full Tobii Pro Lab export (TSV) and process it in one call
through the SDK's ACE pipeline:

    sdk = harmoneyes_theia.TheiaSDK(license_key=..., platform="TobiiG3")
    result = sdk.process_tobii_g3_data(tsv_df)   # per-second predictions DataFrame

The returned DataFrame has one row per ACE window (~1 Hz after the model warmup):

    timestamp_s             seconds from the recording start
    cog_load_level          0=Low, 1=Moderate, 2=High
    cog_load_label          human-readable cognitive-load level
    cog_load_confidence     model confidence in [0, 1]
    fatigue_level           0=Alert … 3=Drowsy (None during warmup)
    fatigue_label           human-readable fatigue level
    fatigue_confidence      model confidence in [0, 1]

Prerequisites:
  1. export THEIA_LICENSE_KEY=...      # SDK license
  2. pip install harmoneyes-theia pandas

Usage:
  python theia-tobii-g3.py --tsv path/to/recording.tsv
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

import harmoneyes_theia

LICENSE_KEY = os.environ.get("THEIA_LICENSE_KEY", "your-license-key-here")
TSV_PATH = Path("path/to/recording.tsv")  # Tobii G3 export TSV

COG_LOAD_LABELS = {0: "Low", 1: "Moderate", 2: "High"}


def run_batch(tsv_df: pd.DataFrame) -> "pd.DataFrame | None":
    """Process a full Tobii G3 export and return per-second predictions."""
    sdk = harmoneyes_theia.TheiaSDK(
        license_key=LICENSE_KEY,
        platform="TobiiG3",
    )

    result = sdk.process_tobii_g3_data(tsv_df)

    print(f"  {len(result)} second-windows returned")
    print(f"  Columns: {list(result.columns)}")

    if "cog_load_level" in result.columns:
        col = result["cog_load_level"].dropna()
        dist = dict(sorted(Counter(col.astype(int)).items()))
        readable = {COG_LOAD_LABELS.get(k, k): v for k, v in dist.items()}
        print(f"  Cognitive-load distribution: {readable}")

    if "fatigue_level" in result.columns:
        col = result["fatigue_level"].dropna()
        if len(col):
            print(f"  Fatigue windows predicted: {len(col)}")

    print("\n  First 10 rows:")
    print(result.head(10).to_string(index=False))
    print("\n  Last 10 rows:")
    print(result.tail(10).to_string(index=False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tsv",
        type=Path,
        default=TSV_PATH,
        help="Path to Tobii G3 export TSV (default: TSV_PATH constant)",
    )
    args = parser.parse_args()

    if not args.tsv.exists():
        sys.exit(f"ERROR: TSV not found: {args.tsv}")

    print(f"Loading {args.tsv.name} ...")
    tsv_df = pd.read_csv(args.tsv, sep="\t", low_memory=False)
    et_count = (
        (tsv_df["Sensor"] == "Eye Tracker").sum() if "Sensor" in tsv_df.columns else 0
    )
    print(f"  {len(tsv_df):,} total rows, {et_count:,} Eye Tracker rows")

    run_batch(tsv_df)
    print("\nDone.")


if __name__ == "__main__":
    main()
