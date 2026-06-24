"""
Draft 2 resilience test for the Data Analytics track.

This script creates a temporary copy of the raw data, deliberately breaks key
columns, then runs the Silver and Gold pipeline to confirm the process keeps
running and writes a resilience incident report.
"""

import shutil
import tempfile
from pathlib import Path

import pandas as pd

import clean_silver_layer
import build_gold_layer


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"


def create_broken_raw_data(target_raw_dir):
    shutil.copytree(RAW_DIR, target_raw_dir, dirs_exist_ok=True)

    events_path = target_raw_dir / "event_logs.csv"
    events = pd.read_csv(events_path)
    events = events.drop(columns=["amount"])
    events.to_csv(events_path, index=False)

    marketing_path = target_raw_dir / "marketing_summary.csv"
    marketing = pd.read_csv(marketing_path)
    marketing["total_sales"] = marketing["total_sales"].astype("object")
    marketing.loc[0:4, "total_sales"] = "CORRUPTED_VALUE"
    marketing.to_csv(marketing_path, index=False)


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        temp_raw = temp_root / "raw"
        temp_silver = temp_root / "silver"
        temp_gold = temp_root / "gold"

        create_broken_raw_data(temp_raw)

        clean_silver_layer.RAW_DIR = temp_raw
        clean_silver_layer.SILVER_DIR = temp_silver
        clean_silver_layer.SILVER_DIR.mkdir(parents=True, exist_ok=True)
        clean_silver_layer.clean_all()

        build_gold_layer.SILVER_DIR = temp_silver
        build_gold_layer.GOLD_DIR = temp_gold
        build_gold_layer.GOLD_DIR.mkdir(parents=True, exist_ok=True)
        build_gold_layer.build_all()

        incidents = pd.read_csv(temp_silver / "resilience_incident_report.csv")
        print("\nDraft 2 resilience test result:")
        print(incidents)
        print("\nPASS: Pipeline completed even with a missing amount column and corrupted total_sales values.")


if __name__ == "__main__":
    main()
