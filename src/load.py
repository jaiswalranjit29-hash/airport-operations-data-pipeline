"""Load pipeline outputs to CSV and optionally PostgreSQL."""
from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DatabaseConfig, POSTGRES_SCHEMA

LOGGER = logging.getLogger("airport_pipeline.load")


def load_csv(dataframe: pd.DataFrame, output_path: Path) -> None:
    """Write a DataFrame to CSV, creating the output directory when needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(
        output_path,
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
    )
    LOGGER.info("Saved %d rows to %s", len(dataframe), output_path)


def _python_value(value: Any) -> Any:
    """Convert pandas/numpy scalar values into psycopg-friendly Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, (datetime, date)):
        return value
    return value


def load_postgresql(
    flights: pd.DataFrame,
    quality_issues: pd.DataFrame,
    config: DatabaseConfig,
    schema_path: Path,
    metrics: dict[str, int],
) -> None:
    """Create the PostgreSQL schema and load dimensions, facts, and audit data."""
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL loading needs psycopg. Install requirements first."
        ) from exc

    try:
        with psycopg.connect(
            host=config.host,
            port=config.port,
            dbname=config.database,
            user=config.user,
            password=config.password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(schema_path.read_text(encoding="utf-8"))
                cursor.execute(f"SET search_path TO {POSTGRES_SCHEMA}, public")

                airlines = sorted(flights["airline"].dropna().unique())
                cursor.executemany(
                    """
                    INSERT INTO dim_airline (airline_name)
                    VALUES (%s)
                    ON CONFLICT (airline_name) DO NOTHING
                    """,
                    [(value,) for value in airlines],
                )

                airports = sorted(
                    set(flights["origin"]).union(set(flights["destination"]))
                )
                cursor.executemany(
                    """
                    INSERT INTO dim_airport (airport_code)
                    VALUES (%s)
                    ON CONFLICT (airport_code) DO NOTHING
                    """,
                    [(value,) for value in airports],
                )

                dates = sorted(flights["flight_date"].unique())
                cursor.executemany(
                    """
                    INSERT INTO dim_date (
                        date_key,
                        full_date,
                        year,
                        quarter,
                        month_number,
                        month_name,
                        week_number,
                        weekday_number,
                        weekday_name
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (date_key) DO NOTHING
                    """,
                    [
                        (
                            int(pd.Timestamp(value).strftime("%Y%m%d")),
                            value,
                            pd.Timestamp(value).year,
                            f"Q{pd.Timestamp(value).quarter}",
                            pd.Timestamp(value).month,
                            pd.Timestamp(value).month_name(),
                            int(pd.Timestamp(value).isocalendar().week),
                            pd.Timestamp(value).weekday() + 1,
                            pd.Timestamp(value).day_name(),
                        )
                        for value in dates
                    ],
                )

                upsert_flight = """
                    INSERT INTO fact_flight (
                        flight_id, airline_key, origin_airport_key,
                        destination_airport_key, date_key, scheduled_time,
                        actual_time, route, gate, status, passengers,
                        delay_minutes, delay_band, is_on_time, is_delayed,
                        is_cancelled, source_row_number
                    )
                    SELECT
                        %s, a.airline_key, o.airport_key, d.airport_key, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    FROM dim_airline a, dim_airport o, dim_airport d
                    WHERE a.airline_name=%s
                      AND o.airport_code=%s
                      AND d.airport_code=%s
                    ON CONFLICT (flight_id) DO UPDATE SET
                        airline_key=EXCLUDED.airline_key,
                        origin_airport_key=EXCLUDED.origin_airport_key,
                        destination_airport_key=EXCLUDED.destination_airport_key,
                        date_key=EXCLUDED.date_key,
                        scheduled_time=EXCLUDED.scheduled_time,
                        actual_time=EXCLUDED.actual_time,
                        route=EXCLUDED.route,
                        gate=EXCLUDED.gate,
                        status=EXCLUDED.status,
                        passengers=EXCLUDED.passengers,
                        delay_minutes=EXCLUDED.delay_minutes,
                        delay_band=EXCLUDED.delay_band,
                        is_on_time=EXCLUDED.is_on_time,
                        is_delayed=EXCLUDED.is_delayed,
                        is_cancelled=EXCLUDED.is_cancelled,
                        source_row_number=EXCLUDED.source_row_number,
                        updated_at=CURRENT_TIMESTAMP
                """
                flight_rows = []
                for row in flights.to_dict("records"):
                    flight_rows.append(
                        (
                            row["flight_id"],
                            int(pd.Timestamp(row["flight_date"]).strftime("%Y%m%d")),
                            _python_value(row["scheduled_time"]),
                            _python_value(row["actual_time"]),
                            row["route"],
                            row["gate"],
                            row["status"],
                            int(row["passengers"]),
                            int(row["delay_minutes"]),
                            row["delay_band"],
                            bool(row["is_on_time"]),
                            bool(row["is_delayed"]),
                            bool(row["is_cancelled"]),
                            int(row["source_row_number"]),
                            row["airline"],
                            row["origin"],
                            row["destination"],
                        )
                    )
                cursor.executemany(upsert_flight, flight_rows)

                cursor.execute("TRUNCATE TABLE fact_quality_issue RESTART IDENTITY")
                if not quality_issues.empty:
                    issue_rows = [
                        tuple(_python_value(value) for value in row)
                        for row in quality_issues.itertuples(index=False, name=None)
                    ]
                    cursor.executemany(
                        """
                        INSERT INTO fact_quality_issue (
                            issue_id, source_row_number, flight_id, rule_code,
                            quality_dimension, severity, issue_description,
                            workflow_status, owner_name, resolution_notes
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        issue_rows,
                    )

                cursor.execute(
                    """
                    INSERT INTO pipeline_run (
                        extracted_records,
                        accepted_records,
                        rejected_records,
                        run_status
                    )
                    VALUES (%s,%s,%s,'SUCCESS')
                    """,
                    (
                        metrics["extracted"],
                        metrics["valid"],
                        metrics["rejected"],
                    ),
                )
            connection.commit()

        LOGGER.info(
            "Loaded %d valid flights and %d quality issues into PostgreSQL",
            len(flights),
            len(quality_issues),
        )
    except Exception as exc:
        raise RuntimeError(f"PostgreSQL load failed: {exc}") from exc
