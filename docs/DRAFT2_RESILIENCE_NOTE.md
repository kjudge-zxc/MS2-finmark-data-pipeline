# Milestone 2 Draft 2 Resilience Note

## Track

Data Analytics

## Challenge Scenario

During a data run, a crucial sales or transaction column may be missing or corrupted. For this prototype, the affected fields are:

| Dataset | Crucial column | Why it matters |
|---|---|---|
| `event_logs.csv` | `amount` | Used to check checkout transaction quality |
| `marketing_summary.csv` | `total_sales` | Used for revenue KPIs and Tableau dashboard summaries |

If either field breaks, the pipeline should not crash unexpectedly. It should detect the problem, document it, apply a controlled fallback, and continue processing.

## What Was Improved

The Silver Layer cleaning script was strengthened with schema and data-quality validation:

1. Checks required source columns before processing.
2. Logs missing required columns as validation failures.
3. Creates fallback columns when a required column is missing.
4. Converts corrupted numeric values into nulls instead of allowing the script to fail.
5. Uses a zero fallback for daily summary numeric fields when needed so downstream Gold outputs can still be generated.
6. Writes a dedicated incident report at `data/silver/resilience_incident_report.csv`.
7. Updates the Gold Layer compliance summary to include high- and medium-severity resilience incidents.

## Fallback Logic

| Issue | Fallback behavior |
|---|---|
| Missing `amount` in `event_logs.csv` | Create `amount` as null, continue processing, and flag checkout records as missing amount |
| Corrupted `amount` values | Convert invalid values to null and log the issue |
| Missing `total_sales` in `marketing_summary.csv` | Create `total_sales` as `0`, continue processing, and mark affected sales values for review |
| Corrupted `total_sales` values | Convert invalid values to null, fill with `0`, and log the issue |

This fallback approach keeps the pipeline running while preventing corrupted values from being treated as valid revenue.

## Files Updated or Added

| File | Purpose |
|---|---|
| `scripts/clean_silver_layer.py` | Added schema checks, fallback logic, and incident logging |
| `scripts/build_gold_layer.py` | Added incident-report loading and resilience metrics in the Gold compliance output |
| `scripts/test_resilience_scenario.py` | Simulates missing/corrupted columns and proves the pipeline still completes |
| `data/silver/resilience_incident_report.csv` | Stores detected resilience incidents from the latest Silver run |

## How to Test

Run the normal pipeline:

```bash
python scripts/clean_silver_layer.py
python scripts/build_gold_layer.py
```

Run the Draft 2 resilience test:

```bash
python scripts/test_resilience_scenario.py
```

Expected result:

```text
PASS: Pipeline completed even with a missing amount column and corrupted total_sales values.
```

## Brief Explanation

We solved the Data Analytics challenge by adding schema validation and fallback handling before the pipeline performs Silver and Gold transformations. If a crucial column is missing or corrupted, the pipeline now logs the issue, applies a controlled fallback, and continues producing cleaned and dashboard-ready outputs instead of failing midway.
