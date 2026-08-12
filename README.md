# Airport Operations Data Pipeline

A reproducible data engineering portfolio project for validating, cleaning, modelling, and reporting synthetic airport flight operations data. The pipeline uses Python and pandas for ETL, records traceable data-quality issues, generates KPI outputs, prepares a star schema for Power BI, and can optionally load validated data into PostgreSQL.

All flight data in this repository is synthetic and generated locally with a fixed seed.

## Problem statement

Operational CSV data is rarely analysis-ready. Missing identifiers, invalid airport codes, duplicate records, inconsistent routes, broken timestamps, and invalid passenger counts can distort downstream reporting if they are not caught before loading and analysis.

This project separates accepted and rejected records, records the reason for each rejection, and creates reporting datasets only from validated flights.

## Objectives

- Build a clear extract-transform-load workflow in Python.
- Apply explicit data-quality rules before analytics.
- Preserve rejected records and quality issues for traceability.
- Generate airline, route, daily, monthly, executive, and data-quality reports.
- Export a simple star schema for Power BI.
- Demonstrate optional PostgreSQL loading and SQL analysis.
- Keep the project reproducible with tests and GitHub Actions.

## Demo results

The deterministic demo run generates 800 synthetic flight records covering six months.

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

A successful run ends with:

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
                                     (optional)
```

## ETL workflow

1. **Extract** — `src/extract.py` reads a non-empty CSV into a pandas DataFrame.
2. **Transform** — `src/transform.py` normalizes fields, validates required values, rejects invalid rows, calculates delays, classifies delay bands, and adds reporting fields.
3. **Quality tracking** — rejected rows become issue records with a rule code, quality dimension, severity, workflow status, and source-row reference.
4. **Load** — clean data, rejected data, quality issues, KPI reports, and Power BI tables are written to CSV.
5. **Database load (optional)** — `--with-db` creates the PostgreSQL schema and upserts dimensions and flight facts using `psycopg`.
6. **Reporting** — Python creates operational KPI outputs and a management-facing Markdown summary.

## Data-quality rules

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

A non-cancelled flight is classified as delayed when calculated delay is greater than `DELAY_THRESHOLD_MINUTES` (15 minutes by default).

## Technologies

| Area | Technology |
|---|---|
| Data processing | Python 3, pandas |
| Database | PostgreSQL, psycopg |
| SQL | Schema design, views, joins, CTEs, aggregates, window functions |
| Data modelling | Fact and dimension tables / star-schema export |
| BI preparation | Power BI, DAX, Power Query |
| Testing | Python `unittest` |
| CI | GitHub Actions |
| Logging | Python `logging` |

## Repository structure

```text
airport-operations-data-pipeline/
├── .github/workflows/python-tests.yml
├── data/
│   ├── raw/flights_raw.csv
│   ├── processed/flights_clean.csv
│   ├── rejected/
│   └── powerbi/
├── docs/data_dictionary.md
├── powerbi/
│   ├── power_query/
│   ├── dax_measures.md
│   ├── model_guide.md
│   └── README.md
├── reports/
├── scripts/generate_demo_data.py
├── sql/
├── src/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The committed data and report CSVs are generated from the synthetic demo source so reviewers can inspect the outputs without running the project first.

## Installation and local run

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate the demo input and run the pipeline:

```bash
python scripts/generate_demo_data.py --rows 800 --seed 42 --output data/raw/flights_raw.csv
python -m src.main
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

To process another CSV with the same required columns:

```bash
python -m src.main --input path/to/flights.csv
```

## PostgreSQL usage

Database loading is optional. Set connection values as environment variables:

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

The pipeline executes `sql/01_postgresql_schema.sql` and loads dimension, fact, quality-issue, and pipeline-run tables. Reporting views can then be created with:

```bash
psql -d airport_data -f sql/02_views.sql
```

`sql/03_analysis_queries.sql` contains analytical SQL including CTEs and window functions. `sql/04_data_quality_queries.sql` contains monitoring and integrity checks.

> `.env.example` is a configuration reference. The application reads environment variables directly and does not automatically load a `.env` file.

## Important outputs

- `data/processed/flights_clean.csv` — accepted and enriched records.
- `data/rejected/flights_rejected.csv` — rejected records with rejection reasons.
- `data/rejected/quality_issues.csv` — traceable issue records.
- `data/powerbi/` — BI-ready fact and dimension CSVs.
- `reports/executive_summary.csv` — overall operational and quality KPIs.
- `reports/airline_kpis.csv` and `reports/route_kpis.csv` — performance summaries.
- `reports/daily_kpis.csv` and `reports/monthly_kpis.csv` — time trends.
- `reports/data_quality_summary.csv` — grouped rule failures.
- `reports/delay_statistics.csv` — descriptive delay statistics.
- `reports/management_summary.md` — short management-facing narrative.

See `docs/data_dictionary.md` for the main datasets and columns.

## Power BI preparation

The pipeline writes BI-ready fact and dimension CSVs to `data/powerbi/`. The `powerbi/` directory contains DAX measures, Power Query scripts, and model/relationship documentation that can be used to rebuild the report in Power BI Desktop.

The original development `.pbix` is intentionally not public because Power BI binaries can retain environment-specific connection metadata.

## Tests and CI

The test suite covers transformation rules, duplicate handling, cancelled flights, report aggregation, executive count reconciliation, quality-issue creation, Power BI star-schema export, and the edge case where every input row is rejected.

GitHub Actions runs Python compilation, unit tests, and a full pipeline smoke test on pushes and pull requests.

## Skills demonstrated

- Python ETL design and pandas transformations
- rule-based data quality and rejected-record handling
- data lineage through source row numbers and issue IDs
- KPI generation and descriptive analytics
- relational schema design and analytical SQL
- PostgreSQL loading and upsert logic
- star-schema preparation for BI tools
- DAX and Power Query documentation
- unit testing, logging, and CI

## Possible next improvements

- incremental processing instead of full-file runs
- orchestration with Prefect or Airflow
- Docker for a repeatable Python/PostgreSQL environment
- run-to-run data-quality trend monitoring
- additional ingestion sources such as an API or object storage
- a newly sanitized `.pbix` built only from local project sources
