# Airport Operations Data Pipeline

A small end-to-end data engineering project for validating, cleaning, modelling, and reporting synthetic airport flight operations data. The pipeline uses Python and pandas for ETL, produces traceable data-quality issues and KPI outputs, prepares a star schema for Power BI, and can optionally load validated data into PostgreSQL.

The repository is designed as a reproducible portfolio project rather than a production aviation system. All included flight data is synthetic.


## Problem statement

Operational CSV data is rarely analysis-ready. Missing identifiers, invalid airport codes, duplicate records, inconsistent routes, broken timestamps, and invalid passenger counts can distort downstream reports if they are not handled before loading and analysis.

This project separates accepted and rejected records, records the reason for each rejection, creates reporting datasets from valid flights, and keeps the workflow reproducible from source data to dashboard-ready outputs.

## Project objectives

- Build a clear CSV-based ETL pipeline with separate extract, transform, load, and reporting modules.
- Apply explicit data-quality rules before records reach analytics outputs.
- Preserve rejected records and create traceable quality-issue records instead of silently dropping bad data.
- Generate operational KPI reports for airlines, routes, dates, and management summaries.
- Prepare a simple star schema for Power BI.
- Demonstrate optional relational loading and SQL analysis with PostgreSQL.
- Keep the project testable and easy to run locally.

## Demo results

The committed demo dataset is deterministic and contains 800 synthetic flight records covering six months.

| Metric | Result |
|---|---:|
| Extracted records | 800 |
| Accepted records | 728 |
| Rejected records | 72 |
| Data-quality issues | 72 |
| Acceptance rate | 91.00% |
| Valid-flight passengers | 136,120 |
| Airlines | 8 |
| Routes | 12 |

A normal run ends with:

```text
Pipeline completed | extracted=800 | valid=728 | rejected=72 | issues=72
```

## Pipeline architecture

```text
Synthetic / custom CSV input
          |
          v
     Extract (pandas)
          |
          v
Normalize + validate + enrich
          |
     +----+------------------+
     |                       |
     v                       v
Valid flight records     Rejected records
     |                       |
     |                       v
     |                Quality issue log
     |
     +----------+------------+
                |
       +--------+---------+----------------+
       |                  |                |
       v                  v                v
 KPI / CSV reports   Power BI tables   PostgreSQL
                                     (optional load)
```

### ETL workflow

1. **Extract** - `src/extract.py` reads a non-empty CSV source into a pandas DataFrame.
2. **Transform** - `src/transform.py` normalizes text, validates required fields, rejects invalid rows, calculates delays, classifies delay bands, and adds reporting fields.
3. **Quality tracking** - rejected rows are converted into issue records with a rule code, quality dimension, severity, workflow status, and source-row reference.
4. **Load** - clean data, rejected data, quality issues, KPI reports, and Power BI tables are written to CSV.
5. **Database load (optional)** - `--with-db` creates the PostgreSQL schema and upserts dimensions and flight facts using `psycopg`.
6. **Reporting** - Python creates airline, route, daily, monthly, executive, quality, and delay-statistics outputs plus a Markdown management summary.

## Data-quality checks

The current implementation contains these rules:

| Rule | Dimension | Check | Severity |
|---|---|---|---|
| DQ001 | Completeness | Missing flight ID | High |
| DQ002 | Validity | Invalid flight ID format | Medium |
| DQ003 | Uniqueness | Duplicate flight ID | High |
| DQ004 | Completeness | Missing airline | High |
| DQ005 | Validity | Invalid origin airport code | High |
| DQ006 | Validity | Invalid destination airport code | High |
| DQ007 | Consistency | Origin equals destination | High |
| DQ008 | Validity | Invalid scheduled timestamp | High |
| DQ009 | Completeness | Missing actual time for a non-cancelled flight | Medium |
| DQ010 | Validity | Invalid flight status | High |
| DQ011 | Validity | Passenger count is not a non-negative integer | High |

A non-cancelled flight is classified as delayed when its calculated delay is greater than `DELAY_THRESHOLD_MINUTES` (15 minutes by default).

## Technologies used

| Area | Technology |
|---|---|
| Data processing | Python 3, pandas |
| Database | PostgreSQL, psycopg |
| SQL | Schema design, views, joins, CTEs, aggregates, window functions |
| Data modelling | Fact and dimension tables / star-schema export |
| BI | Power BI, DAX, Power Query |
| Spreadsheet reporting | Excel |
| Testing | Python `unittest` |
| CI | GitHub Actions |
| Logging | Python `logging` |

## Repository structure

```text
airport-operations-data-pipeline/
├── .github/
│   └── workflows/
│       └── python-tests.yml
├── data/
│   ├── raw/
│   │   └── flights_raw.csv
│   ├── processed/
│   │   └── flights_clean.csv
│   ├── rejected/
│   │   ├── flights_rejected.csv
│   │   └── quality_issues.csv
│   └── powerbi/
│       ├── dim_airline.csv
│       ├── dim_airport.csv
│       ├── dim_date.csv
│       ├── fact_flights.csv
│       └── fact_quality_issues.csv
├── docs/
│   ├── images/
│   ├── data_dictionary.md
│   └── excel_power_query_guide.md
├── powerbi/
│   ├── power_query/
│   ├── airport_operations_dashboard.pdf
│   ├── dax_measures.md
│   ├── model_guide.md
│   └── README.md
├── reports/
│   ├── airport_operations_dashboard.xlsx
│   ├── executive_summary.csv
│   ├── management_summary.md
│   └── ...
├── scripts/
│   └── generate_demo_data.py
├── sql/
│   ├── 01_postgresql_schema.sql
│   ├── 02_views.sql
│   ├── 03_analysis_queries.sql
│   └── 04_data_quality_queries.sql
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── load.py
│   ├── logger_config.py
│   ├── main.py
│   ├── management_summary.py
│   ├── report.py
│   └── transform.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation and local run

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the pipeline

```bash
python -m src.main
```

To use another CSV with the same required columns:

```bash
python -m src.main --input path/to/flights.csv
```

### 4. Run the tests

```bash
python -m unittest discover -s tests -v
```

## Recreate the demo data

The source dataset can be regenerated with a fixed seed:

```bash
python scripts/generate_demo_data.py \
  --rows 800 \
  --seed 42 \
  --output data/raw/flights_raw.csv

python -m src.main
```

Changing `--rows` or `--seed` creates a different synthetic dataset while preserving the same schema and injected quality-problem types.

## PostgreSQL usage

The database load is optional. The default database name is `airport_data`, and the project uses the PostgreSQL schema `airport_ops`.

Set connection values in your shell before running the database load:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD="your_password"
export DB_NAME=airport_data
```

Then run:

```bash
python -m src.main --with-db
```

The pipeline executes `sql/01_postgresql_schema.sql` automatically and loads the dimension, fact, quality-issue, and pipeline-run tables. Reporting views can then be created separately:

```bash
psql -d airport_data -f sql/02_views.sql
```

`sql/03_analysis_queries.sql` contains example analytical SQL, including CTEs and window functions. `sql/04_data_quality_queries.sql` contains monitoring and integrity checks.

> `.env.example` is provided as a configuration reference. The application reads environment variables directly and does not automatically load a local `.env` file.

## Reporting outputs

Important generated outputs include:

- `data/processed/flights_clean.csv` - accepted and enriched flight records.
- `data/rejected/flights_rejected.csv` - rejected source records with rejection reasons.
- `data/rejected/quality_issues.csv` - one traceable issue record per detected quality failure.
- `reports/executive_summary.csv` - overall operational and quality KPIs.
- `reports/airline_kpis.csv` and `reports/route_kpis.csv` - performance summaries.
- `reports/daily_kpis.csv` and `reports/monthly_kpis.csv` - time-based trends.
- `reports/data_quality_summary.csv` - grouped rule failures.
- `reports/delay_statistics.csv` - descriptive delay statistics.
- `reports/management_summary.md` - short management-facing narrative.
- `reports/airport_operations_dashboard.xlsx` - static Excel dashboard/report snapshot.

See `docs/data_dictionary.md` for the main datasets and columns.

## Power BI assets

The pipeline writes BI-ready fact and dimension CSVs to `data/powerbi/`. The `powerbi/` directory contains:

- the exported dashboard PDF;
- DAX measures;
- model and relationship notes;
- Power Query scripts for loading the generated CSVs.

![Power BI data-quality page](docs/images/powerbi_data_quality.png)

The original development `.pbix` file is intentionally not included in this public-ready version because Power BI binaries can retain environment-specific service and connection metadata. The included PDF, DAX, Power Query, model documentation, and star-schema CSVs are enough to review and rebuild the report without publishing that metadata.

## Tests and CI

The test suite currently covers transformation rules, duplicate handling, cancelled flights, report aggregation, executive count reconciliation, quality-issue creation, Power BI star-schema export, and an edge case where every input row is rejected.

GitHub Actions runs three checks on every push and pull request:

1. Python compilation.
2. Unit tests.
3. A full pipeline smoke run against the committed demo input.

## Skills demonstrated

This project demonstrates practical junior-level experience with:

- modular Python ETL design;
- pandas data cleaning and transformation;
- rule-based data quality and rejected-record handling;
- data lineage through source row numbers and issue IDs;
- KPI generation and descriptive analytics;
- relational schema design and SQL analysis;
- PostgreSQL loading and upsert logic;
- star-schema preparation for BI tools;
- Power BI, DAX, Power Query, and Excel reporting;
- unit testing, logging, and GitHub Actions CI.

## Possible next improvements

These are not part of the current implementation, but would be reasonable next steps:

- make database views part of the automated database deployment step;
- add incremental processing instead of full-file runs;
- introduce a lightweight orchestration tool such as Prefect or Airflow;
- add Docker for a repeatable Python/PostgreSQL environment;
- add richer quality metrics and run-to-run trend monitoring;
- support another ingestion source such as an API or object storage;
- publish a newly sanitized `.pbix` built only from local project sources.
