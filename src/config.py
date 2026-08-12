"""Central configuration for paths, thresholds, and PostgreSQL settings."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "flights_raw.csv"
CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "flights_clean.csv"
REJECTED_DATA_PATH = PROJECT_ROOT / "data" / "rejected" / "flights_rejected.csv"
QUALITY_ISSUES_PATH = PROJECT_ROOT / "data" / "rejected" / "quality_issues.csv"
POWERBI_DATA_DIR = PROJECT_ROOT / "data" / "powerbi"
REPORT_DIR = PROJECT_ROOT / "reports"
LOG_PATH = PROJECT_ROOT / "logs" / "pipeline.log"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "01_postgresql_schema.sql"

AIRLINE_REPORT_PATH = REPORT_DIR / "airline_kpis.csv"
ROUTE_REPORT_PATH = REPORT_DIR / "route_kpis.csv"
DAILY_REPORT_PATH = REPORT_DIR / "daily_kpis.csv"
MONTHLY_REPORT_PATH = REPORT_DIR / "monthly_kpis.csv"
EXECUTIVE_REPORT_PATH = REPORT_DIR / "executive_summary.csv"
QUALITY_REPORT_PATH = REPORT_DIR / "data_quality_summary.csv"
DELAY_STATS_PATH = REPORT_DIR / "delay_statistics.csv"
MANAGEMENT_SUMMARY_PATH = REPORT_DIR / "management_summary.md"

POSTGRES_SCHEMA = "airport_ops"
DELAY_THRESHOLD_MINUTES = int(os.getenv("DELAY_THRESHOLD_MINUTES", "15"))


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL connection settings loaded from environment variables."""

    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "airport_data"),
        )
