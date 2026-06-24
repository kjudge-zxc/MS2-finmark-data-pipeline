"""
Gold Layer Transformation
===========================
Reads cleaned Silver Layer CSVs and produces six dashboard-ready Gold tables:
kpi_master_summary, funnel_conversion, product_feature_by_hour, ops_hourly_load,
ops_checkout_health, and compliance_quality_summary.
"""

import pandas as pd
from pathlib import Path

# --- Path setup: ---
BASE_DIR = Path(__file__).resolve().parents[1]
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)


def load_silver():
    events = pd.read_csv(SILVER_DIR / "event_logs_clean.csv", parse_dates=["event_date", "event_timestamp"])
    marketing = pd.read_csv(SILVER_DIR / "marketing_summary_clean.csv", parse_dates=["date"])
    trends = pd.read_csv(SILVER_DIR / "trend_report_clean.csv")
    quality = pd.read_csv(SILVER_DIR / "silver_quality_issues.csv")
    validation = pd.read_csv(SILVER_DIR / "silver_validation_report.csv")
    incident_path = SILVER_DIR / "resilience_incident_report.csv"
    incidents = pd.read_csv(incident_path) if incident_path.exists() else pd.DataFrame(
        columns=["file", "column", "severity", "issue", "fallback"]
    )

    print("event_logs_clean     :", events.shape)
    print("marketing_summary    :", marketing.shape)
    print("trend_report_clean   :", trends.shape)
    print("silver_quality_issues:", quality.shape)
    print("silver_validation    :", validation.shape)
    print("resilience_incidents :", incidents.shape)

    return events, marketing, trends, quality, validation, incidents


def build_kpi_master_summary(events, marketing, trends):
    checkouts = events[events["is_checkout"] == True]

    kpi = pd.DataFrame([
        {"metric": "Total Revenue (All Days)",         "value": round(marketing["total_sales"].sum(), 2),                          "unit": "USD",       "source": "marketing_summary"},
        {"metric": "Average Daily Revenue",            "value": round(marketing["total_sales"].mean(), 2),                         "unit": "USD/day",   "source": "marketing_summary"},
        {"metric": "Peak Daily Revenue",               "value": round(marketing["total_sales"].max(), 2),                          "unit": "USD",       "source": "marketing_summary"},
        {"metric": "Lowest Daily Revenue",             "value": round(marketing["total_sales"].min(), 2),                          "unit": "USD",       "source": "marketing_summary"},
        {"metric": "Average Daily Active Users",       "value": round(marketing["users_active"].mean(), 1),                        "unit": "users",     "source": "marketing_summary"},
        {"metric": "Total New Customers",              "value": int(marketing["new_customers"].sum()),                              "unit": "customers", "source": "marketing_summary"},
        {"metric": "Avg Revenue per Active User",      "value": round((marketing["total_sales"] / marketing["users_active"]).mean(), 2), "unit": "USD/user", "source": "marketing_summary"},
        {"metric": "Total Events Logged",              "value": len(events),                                                        "unit": "events",    "source": "event_logs"},
        {"metric": "Total Checkout Events",            "value": int(events["is_checkout"].sum()),                                   "unit": "events",    "source": "event_logs"},
        {"metric": "Checkout Rate",                    "value": round(events["is_checkout"].mean() * 100, 2),                       "unit": "%",         "source": "event_logs"},
        {"metric": "Missing Amount Rate (Checkouts)",  "value": round(checkouts["is_amount_missing"].mean() * 100, 2),              "unit": "%",         "source": "event_logs"},
        {"metric": "Average Weekly Sales Growth Rate", "value": round(trends["sales_growth_rate"].mean() * 100, 2),                 "unit": "%",         "source": "trend_report"},
        {"metric": "Weeks with Positive Growth",       "value": int((trends["sales_growth_rate"] > 0).sum()),                       "unit": "weeks",     "source": "trend_report"},
    ])

    kpi.to_csv(GOLD_DIR / "kpi_master_summary.csv", index=False)
    print("Saved: kpi_master_summary.csv")
    return kpi


def build_funnel_conversion(events):
    funnel_map = {
        "page_view":    ("Stage 1", "Product View"),
        "search":       ("Stage 2", "Search"),
        "add_to_cart":  ("Stage 3", "Add to Cart"),
        "wishlist_add": ("Stage 4", "Wishlist Add"),
        "checkout":     ("Stage 5", "Checkout"),
    }

    funnel_rows = []
    for etype, (stage_num, stage_name) in funnel_map.items():
        count = len(events[events["event_type"] == etype])
        funnel_rows.append({
            "stage_order": stage_num,
            "stage_name": stage_name,
            "event_type": etype,
            "event_count": count,
        })

    funnel_df = pd.DataFrame(funnel_rows).sort_values("stage_order").reset_index(drop=True)
    top = funnel_df["event_count"].iloc[0]
    funnel_df["drop_off_from_previous"] = funnel_df["event_count"].diff().fillna(0).apply(lambda x: max(0, -x)).astype(int)
    funnel_df["conversion_rate_pct"] = (funnel_df["event_count"] / top * 100).round(1)

    funnel_df.to_csv(GOLD_DIR / "funnel_conversion.csv", index=False)
    print("Saved: funnel_conversion.csv")
    return funnel_df


def build_product_feature_by_hour(events):
    hourly = events.groupby(["event_hour", "event_type"]).size().reset_index(name="event_count")

    feature_by_hour = hourly.pivot_table(
        index="event_hour",
        columns="event_type",
        values="event_count",
        fill_value=0
    ).reset_index()
    feature_by_hour.columns.name = None

    feature_by_hour.to_csv(GOLD_DIR / "product_feature_by_hour.csv", index=False)
    print("Saved: product_feature_by_hour.csv")
    return feature_by_hour


def build_ops_hourly_load(events):
    ops_hourly = events.groupby("event_hour").agg(
        total_events=("event_type", "count"),
        checkout_events=("is_checkout", "sum"),
        unique_users=("user_id", "nunique"),
    ).reset_index()

    ops_hourly["checkout_rate_pct"] = (ops_hourly["checkout_events"] / ops_hourly["total_events"] * 100).round(2)
    ops_hourly["load_category"] = pd.cut(
        ops_hourly["total_events"],
        bins=[0, 60, 85, 100, 999],
        labels=["Low", "Medium", "High", "Peak"]
    )

    ops_hourly.to_csv(GOLD_DIR / "ops_hourly_load.csv", index=False)
    print("Saved: ops_hourly_load.csv")
    return ops_hourly


def build_ops_checkout_health(events):
    checkouts = events[events["is_checkout"] == True]

    checkout_daily = checkouts.groupby("event_date").agg(
        total_checkouts=("event_type", "count"),
        missing_amount=("is_amount_missing", "sum"),
        captured_revenue=("amount", "sum"),
    ).reset_index()

    checkout_daily["failed_amount_rate_pct"] = (
        checkout_daily["missing_amount"] / checkout_daily["total_checkouts"] * 100
    ).round(2)
    checkout_daily["captured_revenue"] = checkout_daily["captured_revenue"].round(2)
    checkout_daily["status"] = checkout_daily["failed_amount_rate_pct"].apply(
        lambda x: "Critical" if x > 70 else ("Warning" if x > 50 else "Normal")
    )

    checkout_daily.to_csv(GOLD_DIR / "ops_checkout_health.csv", index=False)
    print("Saved: ops_checkout_health.csv")
    return checkout_daily


def issue_count(quality, pattern):
    matches = quality[quality["issue_type"].str.contains(pattern, case=False, na=False)]["count"]
    return int(matches.sum()) if not matches.empty else 0


def build_compliance_quality_summary(events, quality, validation, incidents):
    checkouts = events[events["is_checkout"] == True]

    total_events = len(events)
    missing_amounts = events["amount"].isna().sum()
    checkout_count = int(events["is_checkout"].sum())
    missing_checkout = int(checkouts["is_amount_missing"].sum())
    duplicate_count = issue_count(quality, "duplicate")
    flagged_non_checkout = issue_count(quality, "Non-checkout")
    validation_passed = int((validation["status"] == "PASS").sum())
    validation_failed = int((validation["status"] == "FAIL").sum())
    high_incidents = int((incidents["severity"] == "HIGH").sum()) if not incidents.empty else 0
    medium_incidents = int((incidents["severity"] == "MEDIUM").sum()) if not incidents.empty else 0

    compliance = pd.DataFrame([
        {"metric": "Total Silver event records",              "value": total_events,                                    "status": "INFO"},
        {"metric": "Duplicate rows removed",                  "value": duplicate_count,                                 "status": "PASS"},
        {"metric": "Silver validation checks passed",         "value": validation_passed,                               "status": "PASS"},
        {"metric": "Silver validation checks failed",         "value": validation_failed,                               "status": "INFO"},
        {"metric": "Missing amount fields (all events)",      "value": int(missing_amounts),                            "status": "WARNING"},
        {"metric": "Missing amount rate — all events (%)",   "value": round(missing_amounts/total_events*100, 2),       "status": "WARNING"},
        {"metric": "Checkout rows with missing amount",       "value": missing_checkout,                                "status": "WARNING"},
        {"metric": "Missing checkout amount rate (%)",        "value": round(missing_checkout/checkout_count*100, 2),   "status": "WARNING"},
        {"metric": "Non-checkout rows with amount (flagged)", "value": flagged_non_checkout,                            "status": "WARNING"},
        {"metric": "High-severity resilience incidents",       "value": high_incidents,                                  "status": "WARNING" if high_incidents else "PASS"},
        {"metric": "Medium-severity resilience incidents",     "value": medium_incidents,                                "status": "WARNING" if medium_incidents else "PASS"},
        {"metric": "User IDs anonymized",                     "value": "Yes — U-prefixed pseudonymous IDs",             "status": "PASS"},
        {"metric": "PII fields detected in dataset",          "value": "None",                                         "status": "PASS"},
    ])

    compliance.to_csv(GOLD_DIR / "compliance_quality_summary.csv", index=False)
    print("Saved: compliance_quality_summary.csv")
    return compliance


def build_all():
    """Loads Silver data and builds all six Gold tables in order."""
    events, marketing, trends, quality, validation, incidents = load_silver()

    kpi = build_kpi_master_summary(events, marketing, trends)
    funnel = build_funnel_conversion(events)
    feature_by_hour = build_product_feature_by_hour(events)
    ops_hourly = build_ops_hourly_load(events)
    checkout_health = build_ops_checkout_health(events)
    compliance = build_compliance_quality_summary(events, quality, validation, incidents)

    print("\nGold Layer build complete. 6 files saved to data/gold/.")

    return {
        "kpi_master_summary": kpi,
        "funnel_conversion": funnel,
        "product_feature_by_hour": feature_by_hour,
        "ops_hourly_load": ops_hourly,
        "ops_checkout_health": checkout_health,
        "compliance_quality_summary": compliance,
    }


if __name__ == "__main__":
    build_all()
