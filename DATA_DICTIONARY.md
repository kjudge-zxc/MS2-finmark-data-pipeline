# FinMark Data Dictionary — Milestone 2

---

## Dataset Sources

All three datasets are sample reports provided by FinMark Corporation as part of the Project Finer FinMark brief. They were given to us as part of the four baseline references:

1. **Audit of the current app** — `app_modules_spec.csv`
2. **Current network's vulnerabilities** — `network_inventory.csv`, `traffic_logs.csv`
3. **Dataset for trends and platform integration** — `event_logs.csv`, `marketing_summary.csv`, `trend_report.csv` (our pipeline focus)
4. **Sample Reports for references** — the PDF versions of the three datasets above

The three CSVs sitting in `data/raw/` are the source datasets for this pipeline. None of them are real customer data — they are sample/synthetic files representative of FinMark's reporting outputs.

---

## File 1: `event_logs.csv`

**Description:** User interaction event log capturing actions taken by users on the FinMark platform.
**Rows:** 2,000
**Columns:** 50 (5 meaningful + 45 junk columns)
**Time range:** Mid-2023

| Column | Type | Description | Notes |
|---|---|---|---|
| `user_id` | string | Unique user identifier | Format `U####` (e.g. `U0099`) |
| `event_type` | string | The type of action the user performed | One of: `login`, `logout`, `checkout`, `wishlist_add`, `profile_update`, `page_view`, `search`, `add_to_cart` |
| `event_time` | datetime | When the event occurred | Format `YYYY-MM-DD HH:MM` |
| `product_id` | string | Product the event relates to (if any) | Format `P###` (e.g. `P010`) |
| `amount` | float | Transaction amount (PHP) | Nullable; 50.8% are blank — expected for non-transaction events like `login` and `page_view`, but 142 `checkout` events also have null amounts which is a data quality issue |
| `col_6` to `col_50` | mixed | Unnamed junk columns | No schema documentation; content is a mix of labels and numbers |

---

## File 2: `marketing_summary.csv`

**Description:** Daily marketing performance summary aggregating user activity, sales, and new customer counts.
**Rows:** 100 (≈ 100 days from 2023-06-01 to 2023-09-08)
**Columns:** 50 (5 meaningful + 45 junk columns)

| Column | Type | Description | Notes |
|---|---|---|---|
| `date` | datetime | Calendar date the row represents | Format `YYYY-MM-DD` |
| `users_active` | int | Daily active users | Range: 51 to 497 |
| `total_sales` | float | Total sales for the day (PHP) | Range: ~20,780 to ~89,585 |
| `new_customers` | int | Number of new customer signups that day | Average ≈ 7.6 per day |
| `report_generated` | datetime | When the daily report was generated | **All values are at 16:00** — direct evidence of FinMark's daily batch generation pattern |
| `col_6` to `col_50` | mixed | Unnamed junk columns | No schema documentation |

---

## File 3: `trend_report.csv`

**Description:** Weekly trend report aggregating users and sales growth rates.
**Rows:** 20 (weeks 2023-W21 to 2023-W40)
**Columns:** 50 (3 meaningful + 47 junk columns)

| Column | Type | Description | Notes |
|---|---|---|---|
| `week` | string | ISO week identifier | Format `YYYY-Www` (e.g. `2023-W21`) |
| `avg_users` | int | Average users for the week | Range: 125 to 393 |
| `sales_growth_rate` | float | Week-over-week sales growth rate | Range: -3.00% to +9.90% |
| `col_4` to `col_50` | mixed | Unnamed junk columns | **47 columns** with mixed string/numeric content; includes labels like "Rising", "Falling", "Stable" mixed with numeric values, but no documentation provided |

---

## Known Data Quality Issues

These issues were identified during raw data profiling. Recommended handling is noted for each, but actual cleaning is performed in the Silver Layer:

1. **Junk columns in all three files.** Each file has 45–47 unnamed columns containing inconsistent mixed-type content. No schema or data dictionary was provided for these. **Recommended action:** Drop in Silver.

2. **Null amounts on checkout events.** 142 of 260 checkout events in `event_logs.csv` have no transaction amount. **Recommended action:** Keep rows but add a flag column in Silver to mark these as suspect transactions.

3. **Batch-only report generation.** Every `report_generated` value in `marketing_summary.csv` is at exactly 16:00. This confirms the batch-only architecture finding from Milestone 1. **Recommended action:** No cleaning needed; log as evidence supporting the Milestone 1 assessment.

4. **Uniform event counts.** Event types are near-uniform (login 276 down to logout 213) which is unusual for real user behavior and suggests sampling or synthetic generation. **Recommended action:** Surface as an event type summary metric in Gold; the issue itself cannot be fixed at the pipeline level and should be escalated to FinMark as a data source concern.

5. **No session IDs or error logs.** The dataset has no session identifier linking events together and no system error tracking. **Recommended action:** Document as an upstream limitation and flag for follow-up with FinMark in a later milestone.
