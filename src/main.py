"""CLI entry point for the airport operations data pipeline."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import (
    AIRLINE_REPORT_PATH,
    CLEAN_DATA_PATH,
    DAILY_REPORT_PATH,
    DELAY_STATS_PATH,
    EXECUTIVE_REPORT_PATH,
    LOG_PATH,
    MANAGEMENT_SUMMARY_PATH,
    MONTHLY_REPORT_PATH,
    POWERBI_DATA_DIR,
    QUALITY_ISSUES_PATH,
    QUALITY_REPORT_PATH,
    RAW_DATA_PATH,
    REJECTED_DATA_PATH,
    ROUTE_REPORT_PATH,
    SCHEMA_PATH,
    DatabaseConfig,
)
from src.extract import extract_csv
from src.load import load_csv, load_postgresql
from src.logger_config import configure_logging
from src.management_summary import create_management_summary
from src.report import create_all_reports, create_powerbi_star_schema
from src.transform import create_quality_issues, transform_flights

LOGGER = logging.getLogger("airport_pipeline.main")


def run_pipeline(
    input_path: Path = RAW_DATA_PATH,
    *,
    with_db: bool = False,
) -> dict[str, int]:
    """Run the complete ETL, quality, reporting, and optional database workflow."""
    LOGGER.info("Pipeline started with input %s", input_path)
    raw_df = extract_csv(input_path)
    valid_df, rejected_df = transform_flights(raw_df)
    quality_issues = create_quality_issues(rejected_df)

    load_csv(valid_df, CLEAN_DATA_PATH)
    load_csv(rejected_df, REJECTED_DATA_PATH)
    load_csv(quality_issues, QUALITY_ISSUES_PATH)

    reports = create_all_reports(
        valid_df,
        rejected_df,
        quality_issues,
        len(raw_df),
    )
    report_paths = {
        "airline": AIRLINE_REPORT_PATH,
        "route": ROUTE_REPORT_PATH,
        "daily": DAILY_REPORT_PATH,
        "monthly": MONTHLY_REPORT_PATH,
        "executive": EXECUTIVE_REPORT_PATH,
        "quality": QUALITY_REPORT_PATH,
        "delay_statistics": DELAY_STATS_PATH,
    }
    for name, dataframe in reports.items():
        load_csv(dataframe, report_paths[name])

    management_summary = create_management_summary(reports)
    MANAGEMENT_SUMMARY_PATH.write_text(management_summary, encoding="utf-8")
    LOGGER.info("Saved management summary to %s", MANAGEMENT_SUMMARY_PATH)

    create_powerbi_star_schema(valid_df, quality_issues, POWERBI_DATA_DIR)
    metrics = {
        "extracted": len(raw_df),
        "valid": len(valid_df),
        "rejected": len(rejected_df),
        "issues": len(quality_issues),
    }

    if with_db:
        load_postgresql(
            valid_df,
            quality_issues,
            DatabaseConfig.from_environment(),
            SCHEMA_PATH,
            metrics,
        )
    else:
        LOGGER.info("PostgreSQL load skipped; use --with-db to enable it")

    LOGGER.info("Pipeline completed successfully: %s", metrics)
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate airport flight data, create quality outputs and KPI reports, "
            "and prepare Power BI tables."
        )
    )
    parser.add_argument("--input", type=Path, default=RAW_DATA_PATH)
    parser.add_argument(
        "--with-db",
        action="store_true",
        help="Load validated outputs into PostgreSQL.",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging(LOG_PATH)
    args = parse_args()
    try:
        metrics = run_pipeline(args.input, with_db=args.with_db)
        print(
            "\nPipeline completed | "
            f"extracted={metrics['extracted']} | valid={metrics['valid']} | "
            f"rejected={metrics['rejected']} | issues={metrics['issues']}"
        )
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        LOGGER.error("Pipeline failed: %s", exc)
        return 1
    except Exception:
        LOGGER.exception("Unexpected pipeline failure")
        return 99


if __name__ == "__main__":
    raise SystemExit(main())
