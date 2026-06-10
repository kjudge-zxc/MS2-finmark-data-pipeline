import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
SILVER_DIR = BASE_DIR / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

validation_rows = []
issue_rows = []

def col_junk(df):
    return [c for c in df.columns if c.startswith("col_")]

def add_validation(file, check, status, details):
    validation_rows.append({"file": file, "check": check, "status": status, "details": details})

def add_issue(file, issue_type, count, handling):
    issue_rows.append({"file": file, "issue_type": issue_type, "count": int(count), "handling": handling})

def clean_event_logs():
    file = "event_logs.csv"
    df = pd.read_csv(RAW_DIR / file)
    junk = col_junk(df)
    df = df.drop(columns=junk)
    add_validation(file, "Dropped undocumented junk columns", "PASS", f"Dropped {len(junk)} columns")

    before = len(df)
    df = df.drop_duplicates().copy()
    add_issue(file, "Exact duplicate rows", before - len(df), "Removed before Silver export")

    for c in ["user_id", "event_type", "product_id"]:
        df[c] = df[c].astype(str).str.strip()
    df["user_id"] = df["user_id"].str.upper()
    df["product_id"] = df["product_id"].str.upper()
    df["event_type"] = df["event_type"].str.lower()

    df["event_timestamp"] = pd.to_datetime(df["event_time"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["event_date"] = df["event_timestamp"].dt.date.astype("string")
    df["event_hour"] = df["event_timestamp"].dt.hour.astype("Int64")
    df["is_checkout"] = df["event_type"].eq("checkout")
    df["is_amount_missing"] = df["amount"].isna()
    df["amount_quality_status"] = np.select(
        [df["is_checkout"] & df["amount"].isna(),
         df["is_checkout"] & df["amount"].notna() & (df["amount"] > 0),
         ~df["is_checkout"] & df["amount"].notna(),
         ~df["is_checkout"] & df["amount"].isna()],
        ["missing_checkout_amount", "valid_checkout_amount", "non_checkout_amount_present", "not_applicable"],
        default="review_required"
    )

    valid_events = {"login", "logout", "checkout", "wishlist_add", "profile_update", "page_view", "search", "add_to_cart"}
    invalid_event_count = (~df["event_type"].isin(valid_events)).sum()
    add_validation(file, "Allowed event_type values", "PASS" if invalid_event_count == 0 else "FAIL", f"{invalid_event_count} invalid values")

    missing_checkout = ((df["event_type"] == "checkout") & df["amount"].isna()).sum()
    non_checkout_amt = ((df["event_type"] != "checkout") & df["amount"].notna()).sum()
    add_issue(file, "Checkout rows with missing amount", missing_checkout, "Kept rows and flagged")
    add_issue(file, "Non-checkout rows with amount present", non_checkout_amt, "Kept rows and flagged")

    df = df[["user_id", "event_type", "event_timestamp", "event_date", "event_hour", "product_id", "amount", "is_checkout", "is_amount_missing", "amount_quality_status"]]
    df.to_csv(SILVER_DIR / "event_logs_clean.csv", index=False)
    return df

def clean_marketing_summary():
    file = "marketing_summary.csv"
    df = pd.read_csv(RAW_DIR / file)
    junk = col_junk(df)
    df = df.drop(columns=junk)
    add_validation(file, "Dropped undocumented junk columns", "PASS", f"Dropped {len(junk)} columns")

    before = len(df)
    df = df.drop_duplicates().copy()
    add_issue(file, "Exact duplicate rows", before - len(df), "Removed before Silver export")

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")
    df["users_active"] = pd.to_numeric(df["users_active"], errors="coerce").astype("Int64")
    df["total_sales"] = pd.to_numeric(df["total_sales"], errors="coerce")
    df["new_customers"] = pd.to_numeric(df["new_customers"], errors="coerce").astype("Int64")
    df["report_generated"] = pd.to_datetime(df["report_generated"], errors="coerce")
    df["report_hour"] = df["report_generated"].dt.hour.astype("Int64")
    df["is_1600_batch_report"] = df["report_hour"].eq(16)

    for c in ["date", "users_active", "total_sales", "new_customers", "report_generated"]:
        n = df[c].isna().sum()
        add_validation(file, f"Required field: {c}", "PASS" if n == 0 else "FAIL", f"{n} missing/invalid values")

    df = df[["date", "users_active", "total_sales", "new_customers", "report_generated", "report_hour", "is_1600_batch_report"]]
    df.to_csv(SILVER_DIR / "marketing_summary_clean.csv", index=False)
    return df

def clean_trend_report():
    file = "trend_report.csv"
    df = pd.read_csv(RAW_DIR / file)
    junk = col_junk(df)
    df = df.drop(columns=junk)
    add_validation(file, "Dropped undocumented junk columns", "PASS", f"Dropped {len(junk)} columns")

    before = len(df)
    df = df.drop_duplicates().copy()
    add_issue(file, "Exact duplicate rows", before - len(df), "Removed before Silver export")

    df["week"] = df["week"].astype(str).str.strip()
    df["avg_users"] = pd.to_numeric(df["avg_users"], errors="coerce").astype("Int64")
    df["sales_growth_rate"] = pd.to_numeric(df["sales_growth_rate"], errors="coerce")
    df["week_start_date"] = pd.to_datetime(df["week"] + "-1", format="%G-W%V-%u", errors="coerce").dt.date.astype("string")

    for c in ["week", "week_start_date", "avg_users", "sales_growth_rate"]:
        n = df[c].isna().sum()
        add_validation(file, f"Required field: {c}", "PASS" if n == 0 else "FAIL", f"{n} missing/invalid values")

    df = df[["week", "week_start_date", "avg_users", "sales_growth_rate"]]
    df.to_csv(SILVER_DIR / "trend_report_clean.csv", index=False)
    return df

if __name__ == "__main__":
    clean_event_logs()
    clean_marketing_summary()
    clean_trend_report()
    pd.DataFrame(validation_rows).to_csv(SILVER_DIR / "silver_validation_report.csv", index=False)
    pd.DataFrame(issue_rows).to_csv(SILVER_DIR / "silver_quality_issues.csv", index=False)
    print("Silver Layer cleaning completed. Outputs saved to data/silver/.")
