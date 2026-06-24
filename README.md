# FinMark Data Pipeline — Milestone 2 (Bronze Layer)

**Course:** MO-IT151 - Platform Technologies
**Section / Group:** H3101 Group 12 (Data Analytics)
**Members:** Martin Sheen Cajucom, Karissa Mae Manicad, Rania Nabil Abdelfattah, Chadley Marie De Lara, Christian Noel Busalanan

---

## Overview

This repository contains the **Bronze Layer (Repository Setup + Raw Data Profiling)** portion of our Milestone 2 prototype for the FinMark data pipeline. It is part of a larger Bronze → Silver → Gold medallion pipeline based on the lakehouse architecture proposed in Milestone 1.

The scope here covers:
- Project repository structure
- Raw datasets stored in the Bronze layer
- A data dictionary documenting the dataset columns
- A profiling notebook that inspects the raw data and reports quality issues for the downstream Silver stage

The Silver Layer cleaning, Gold Layer transformations, and dashboard work are handled in separate notebooks.

## Milestone 2 Draft 2 Resilience Update

For the Data Analytics challenge scenario, the pipeline was updated to handle missing or corrupted transaction/revenue columns before processing. The Silver Layer now checks required columns, logs schema incidents, applies controlled fallbacks, and writes `data/silver/resilience_incident_report.csv`. The Gold Layer also includes resilience incident counts in the compliance quality summary.

Run the resilience test with:

```
python scripts/test_resilience_scenario.py
```

See `docs/DRAFT2_RESILIENCE_NOTE.md` for the short explanation of the solution.

## How to Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. The three FinMark CSVs are already in place at `data/raw/`:
   - `event_logs.csv`
   - `marketing_summary.csv`
   - `trend_report.csv`

3. Open and run the profiling notebook:
   ```
   jupyter notebook bronze_profiling.ipynb
   ```

## Folder Structure

```
finmark_pipeline/
├── data/
│   └── raw/                    ← input CSVs (untouched)
├── bronze_profiling.ipynb      ← raw data quality report
├── DATA_DICTIONARY.md          ← column-level documentation
├── requirements.txt
└── README.md
```

## What This Covers

| Step | Output |
|---|---|
| Set up project structure | Folders and repo organized |
| Store raw datasets in Bronze | Three CSVs in `data/raw/` |
| Document dataset columns | `DATA_DICTIONARY.md` |
| Profile raw data quality | `bronze_profiling.ipynb` |

## Key Findings from Profiling

- **event_logs.csv** — 2,000 rows × 50 columns. 1,016 nulls in the `amount` column (50.8%), including 142 checkout events with null amounts. 45 unnamed "junk" columns with no documentation. Event type counts are unusually uniform (login 276 down to logout 213), which suggests sampling or synthetic generation rather than real user behavior.
- **marketing_summary.csv** — 100 rows × 50 columns. No nulls in meaningful columns. Every `report_generated` value is at hour 16, supporting the batch-only finding from Milestone 1 with direct data evidence. 45 unnamed junk columns.
- **trend_report.csv** — 20 rows × 50 columns. No nulls in meaningful columns. 47 unnamed junk columns containing mixed string and numeric content. Only three meaningful columns survive: `week`, `avg_users`, `sales_growth_rate`.

## Mapping to Milestone 1

| Milestone 1 Design | Bronze Layer Implementation |
|---|---|
| Apache Kafka ingestion | Local raw CSV files |
| Delta Lake on Amazon S3 (Bronze) | `data/raw/` (raw source of truth) |
| Schema validation (Silver) | Handled in separate Silver submission |
| KPI tables (Gold) | Handled in separate Gold submission |
| Dashboards | Out of scope for Milestone 2 |
