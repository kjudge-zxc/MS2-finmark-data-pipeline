"""
Bronze Layer Profiling
=======================
Profiles the three raw FinMark CSVs (event_logs, marketing_summary, trend_report)
and writes a consolidated data quality summary to data/bronze/.
"""

import shutil
from pathlib import Path

import pandas as pd

# --- Path setup: ---
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
BRONZE_DIR = BASE_DIR / "data" / "bronze"
BRONZE_RAW_DIR = BRONZE_DIR / "raw"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)
BRONZE_RAW_DIR.mkdir(parents=True, exist_ok=True)


def col_junk(df):
    return [c for c in df.columns if c.startswith("col_")]


def ingest_raw_data() -> pd.DataFrame:
    """Copy each raw CSV into a bronze-side raw folder and record the transfer."""
    filenames = ["event_logs.csv", "marketing_summary.csv", "trend_report.csv"]
    manifest_rows = []

    for filename in filenames:
        source_path = RAW_DIR / filename
        destination_path = BRONZE_RAW_DIR / filename
        shutil.copy2(source_path, destination_path)
        manifest_rows.append({
            "filename": filename,
            "source_path": str(source_path.relative_to(BASE_DIR)),
            "destination_path": str(destination_path.relative_to(BASE_DIR)),
        })

    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(BRONZE_DIR / "bronze_ingestion_manifest.csv", index=False)
    print(f"\nCopied raw files into {BRONZE_RAW_DIR.relative_to(BASE_DIR)}")
    print(manifest.to_string(index=False))
    return manifest


def profile_dataset(filename: str) -> dict:
    """Load a CSV and produce a structured profiling report."""
    print(f"\n{'='*70}")
    print(f"PROFILING: {filename}")
    print('='*70)

    df = pd.read_csv(RAW_DIR / filename)

    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

    meaningful_cols = [c for c in df.columns if not c.startswith("col_")]
    junk_cols = col_junk(df)
    print(f"\nMeaningful columns ({len(meaningful_cols)}): {meaningful_cols}")
    print(f"Junk/unnamed columns ({len(junk_cols)})")

    print(f"\nData types of meaningful columns:")
    print(df[meaningful_cols].dtypes.to_string())

    missing = df[meaningful_cols].isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
    missing_df = missing_df[missing_df["missing_count"] > 0]
    if len(missing_df) > 0:
        print(f"\nMissing values in meaningful columns:")
        print(missing_df.to_string())
    else:
        print("\nNo missing values in meaningful columns.")

    dup_count = df.duplicated().sum()
    print(f"\nFully duplicated rows: {dup_count}")

    return {
        "filename": filename,
        "rows": df.shape[0],
        "cols": df.shape[1],
        "meaningful_cols": len(meaningful_cols),
        "junk_cols": len(junk_cols),
        "missing_values": int(missing.sum()),
        "duplicates": int(dup_count),
    }


def check_event_logs():
    """Suspect-value checks specific to event_logs.csv."""
    df = pd.read_csv(RAW_DIR / "event_logs.csv")

    checkout_null = df[(df["event_type"] == "checkout") & (df["amount"].isnull())]
    total_checkout = (df["event_type"] == "checkout").sum()
    print(f"\nCheckout events: {total_checkout}")
    print(f"Checkout events with NULL amount: {len(checkout_null)}")
    print(f"Percentage of checkouts missing amount: {len(checkout_null)/total_checkout*100:.1f}%")

    print("\nEvent type counts:")
    print(df["event_type"].value_counts().to_string())


def check_marketing_summary():
    """Confirms batch (non-real-time) report generation pattern."""
    df = pd.read_csv(RAW_DIR / "marketing_summary.csv")
    df["report_generated"] = pd.to_datetime(df["report_generated"], errors="coerce")

    hours = df["report_generated"].dt.hour.dropna().unique()
    print(f"\nUnique hours in report_generated: {sorted(hours)}")
    print(f"Number of unique hours: {len(hours)}")


def check_trend_report():
    """Inspects the undocumented junk columns in trend_report.csv."""
    df = pd.read_csv(RAW_DIR / "trend_report.csv")
    junk_cols = col_junk(df)
    print(f"\nNumber of junk columns: {len(junk_cols)}")
    print(f"First 10 junk column names: {junk_cols[:10]}")


def profile_all() -> pd.DataFrame:
    """Ingest raw data into bronze, profile all three datasets, and write the outputs."""
    ingest_manifest = ingest_raw_data()

    profile_events = profile_dataset("event_logs.csv")
    check_event_logs()

    profile_marketing = profile_dataset("marketing_summary.csv")
    check_marketing_summary()

    profile_trends = profile_dataset("trend_report.csv")
    check_trend_report()

    summary = pd.DataFrame([profile_events, profile_marketing, profile_trends])
    summary["pct_missing_overall"] = (
        summary["missing_values"] / (summary["rows"] * summary["meaningful_cols"]) * 100
    ).round(2)
    summary["ingested_to_bronze"] = True
    summary["bronze_copy_path"] = [
        str((BRONZE_RAW_DIR / row["filename"]).relative_to(BASE_DIR))
        for _, row in summary[["filename"]].iterrows()
    ]

    summary.to_csv(BRONZE_DIR / "bronze_quality_report.csv", index=False)
    print(f"\n{'='*70}")
    print("Saved: data/bronze/bronze_quality_report.csv")
    print('='*70)
    print(summary.to_string(index=False))

    return summary


if __name__ == "__main__":
    profile_all()