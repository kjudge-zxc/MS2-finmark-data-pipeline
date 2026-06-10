# Silver Layer Cleaning and Validation

## Role Covered

This folder contains the **Silver Layer Cleaning and Validation** output for Milestone 2. The work starts from the raw Bronze Layer CSV files prepared by Martin, then produces cleaned and validated Silver Layer files for downstream Gold Layer transformation and dashboard preparation.

## Input Files

| Bronze input | Rows × Columns before cleaning | Notes from profiling |
|---|---:|---|
| `data/raw/event_logs.csv` | 2000 × 50 | User event records with 45 undocumented `col_*` junk columns and missing amounts on some checkout rows |
| `data/raw/marketing_summary.csv` | 100 × 50 | Daily marketing summary with 45 undocumented `col_*` junk columns |
| `data/raw/trend_report.csv` | 20 × 50 | Weekly trend summary with 47 undocumented `col_*` junk columns |

## Cleaning Rules Applied

1. **Removed undocumented junk columns**  
   All columns named `col_*` were dropped because they have no defined schema or business meaning in the data dictionary.

2. **Removed exact duplicate rows**  
   Exact duplicates were checked and removed before exporting to Silver.

3. **Standardized data types**  
   Date/time fields were converted to datetime or date formats, numeric fields were converted to numeric types, and ID/text fields were trimmed and standardized.

4. **Validated required fields**  
   Required fields such as `user_id`, `event_type`, `event_timestamp`, `date`, `report_generated`, `week`, and `week_start_date` were checked for missing or invalid values.

5. **Flagged suspicious transaction records**  
   Checkout events with missing amounts were not deleted or imputed. They were retained and flagged as `missing_checkout_amount` to preserve record count while making the issue visible for later analysis.

6. **Preserved source limitations**  
   Since the raw data appears synthetic and lacks session IDs/error logs, these issues were documented rather than force-fixed in the Silver Layer.

## Output Files

| Silver output | Description | Rows × Columns after cleaning |
|---|---|---:|
| `data/silver/event_logs_clean.csv` | Cleaned event log with event date/hour and amount quality flags | 2000 × 10 |
| `data/silver/marketing_summary_clean.csv` | Cleaned daily marketing summary with batch-report flag | 100 × 7 |
| `data/silver/trend_report_clean.csv` | Cleaned weekly trend report with ISO week start date | 20 × 4 |
| `data/silver/silver_validation_report.csv` | Checklist of validation checks and results | 27 rows |
| `data/silver/silver_quality_issues.csv` | Documented issues and how each was handled | 6 rows |

## Important Data Quality Findings

- `event_logs.csv` had 142 checkout events with missing transaction amounts. These were kept but flagged.
- `event_logs.csv` had 866 non-checkout events with amount values. These were kept but flagged because the business meaning needs confirmation.
- `marketing_summary.csv` report generation happened at 16:00 for all 100 rows, confirming the batch-reporting behavior noted in the Bronze profiling.
- All three files contained many undocumented `col_*` columns. These were excluded from Silver because they are not reliable for analysis.

## Why This Supports the Pipeline

The Silver Layer acts as the cleaned and validated version of the Bronze Layer. It prepares the data for Gold Layer transformations such as sales summaries, feature usage counts, top product performance, and dashboard-ready tables. This confirms that the proposed Bronze → Silver → Gold pipeline has started functioning as an actual prototype.

## What We Still Need Refinement

- Confirm with FinMark whether non-checkout events should contain amount values.
- Confirm whether checkout events with missing amounts should be corrected upstream or excluded from revenue calculations.
- Add stronger schema validation using Pandera once the team finalizes the official schema.
- Add session IDs, error logs, or source system identifiers in later milestones if available.
