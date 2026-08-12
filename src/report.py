"""Generate business KPIs, data-quality summaries, statistics, and Power BI tables."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger("airport_pipeline.report")


def _ensure_flags(flights: pd.DataFrame) -> pd.DataFrame:
    """Support report creation from both enriched and minimal input frames."""
    frame = flights.copy()
    if "is_cancelled" not in frame:
        frame["is_cancelled"] = frame["status"].eq("CANCELLED")
    if "is_delayed" not in frame:
        frame["is_delayed"] = (~frame["is_cancelled"]) & frame["delay_minutes"].gt(15)
    if "is_on_time" not in frame:
        frame["is_on_time"] = (~frame["is_cancelled"]) & (~frame["is_delayed"])
    return frame


def _percentage(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return (numerator.div(denominator.where(denominator.ne(0))) * 100).fillna(0).round(2)


def create_airline_kpis(flights: pd.DataFrame) -> pd.DataFrame:
    flights = _ensure_flags(flights)
    report = flights.groupby("airline", as_index=False).agg(
        total_flights=("flight_id", "count"),
        on_time_flights=("is_on_time", "sum"),
        delayed_flights=("is_delayed", "sum"),
        cancelled_flights=("is_cancelled", "sum"),
        average_delay_minutes=("delay_minutes", "mean"),
        p90_delay_minutes=("delay_minutes", lambda values: values.quantile(0.90)),
        total_passengers=("passengers", "sum"),
    )
    report["on_time_rate_pct"] = _percentage(
        report["on_time_flights"], report["total_flights"]
    )
    report["delay_rate_pct"] = _percentage(
        report["delayed_flights"], report["total_flights"]
    )
    report["cancellation_rate_pct"] = _percentage(
        report["cancelled_flights"], report["total_flights"]
    )
    delay_columns = ["average_delay_minutes", "p90_delay_minutes"]
    report[delay_columns] = report[delay_columns].round(2)
    return report.sort_values(
        ["delay_rate_pct", "average_delay_minutes"],
        ascending=[False, False],
    ).reset_index(drop=True)


def create_route_kpis(flights: pd.DataFrame) -> pd.DataFrame:
    flights = _ensure_flags(flights)
    report = flights.groupby(["route", "origin", "destination"], as_index=False).agg(
        total_flights=("flight_id", "count"),
        delayed_flights=("is_delayed", "sum"),
        cancelled_flights=("is_cancelled", "sum"),
        average_delay_minutes=("delay_minutes", "mean"),
        maximum_delay_minutes=("delay_minutes", "max"),
        total_passengers=("passengers", "sum"),
    )
    report["delay_rate_pct"] = _percentage(
        report["delayed_flights"], report["total_flights"]
    )
    report["average_delay_minutes"] = report["average_delay_minutes"].round(2)
    return report.sort_values(
        ["delay_rate_pct", "total_flights"],
        ascending=[False, False],
    ).reset_index(drop=True)


def create_daily_kpis(flights: pd.DataFrame) -> pd.DataFrame:
    flights = _ensure_flags(flights)
    report = flights.groupby("flight_date", as_index=False).agg(
        total_flights=("flight_id", "count"),
        on_time_flights=("is_on_time", "sum"),
        delayed_flights=("is_delayed", "sum"),
        cancelled_flights=("is_cancelled", "sum"),
        average_delay_minutes=("delay_minutes", "mean"),
        total_passengers=("passengers", "sum"),
    )
    report["on_time_rate_pct"] = _percentage(
        report["on_time_flights"], report["total_flights"]
    )
    report["delay_rate_pct"] = _percentage(
        report["delayed_flights"], report["total_flights"]
    )
    report["average_delay_minutes"] = report["average_delay_minutes"].round(2)
    return report.sort_values("flight_date").reset_index(drop=True)


def create_monthly_kpis(flights: pd.DataFrame) -> pd.DataFrame:
    flights = _ensure_flags(flights)
    report = flights.groupby("month", as_index=False).agg(
        total_flights=("flight_id", "count"),
        on_time_flights=("is_on_time", "sum"),
        delayed_flights=("is_delayed", "sum"),
        cancelled_flights=("is_cancelled", "sum"),
        average_delay_minutes=("delay_minutes", "mean"),
        total_passengers=("passengers", "sum"),
    )
    report["on_time_rate_pct"] = _percentage(
        report["on_time_flights"], report["total_flights"]
    )
    report["delay_rate_pct"] = _percentage(
        report["delayed_flights"], report["total_flights"]
    )
    report["average_delay_minutes"] = report["average_delay_minutes"].round(2)
    return report.sort_values("month").reset_index(drop=True)


def create_executive_summary(
    flights: pd.DataFrame,
    rejected: pd.DataFrame,
    extracted_count: int,
) -> pd.DataFrame:
    valid_count = len(flights)
    rejected_count = len(rejected)
    summary = {
        "extracted_records": extracted_count,
        "accepted_records": valid_count,
        "rejected_records": rejected_count,
        "acceptance_rate_pct": (
            round(valid_count / extracted_count * 100, 2) if extracted_count else 0
        ),
        "rejection_rate_pct": (
            round(rejected_count / extracted_count * 100, 2) if extracted_count else 0
        ),
        "total_flights": valid_count,
        "total_passengers": int(flights["passengers"].sum()) if valid_count else 0,
        "on_time_rate_pct": (
            round(flights["is_on_time"].mean() * 100, 2) if valid_count else 0
        ),
        "delay_rate_pct": (
            round(flights["is_delayed"].mean() * 100, 2) if valid_count else 0
        ),
        "cancellation_rate_pct": (
            round(flights["is_cancelled"].mean() * 100, 2) if valid_count else 0
        ),
        "average_delay_minutes": (
            round(float(flights["delay_minutes"].mean()), 2) if valid_count else 0
        ),
        "median_delay_minutes": (
            round(float(flights["delay_minutes"].median()), 2) if valid_count else 0
        ),
        "p90_delay_minutes": (
            round(float(flights["delay_minutes"].quantile(0.90)), 2)
            if valid_count
            else 0
        ),
    }
    return pd.DataFrame([summary])


def create_quality_summary(
    quality_issues: pd.DataFrame,
    extracted_count: int,
) -> pd.DataFrame:
    columns = [
        "rule_code",
        "quality_dimension",
        "severity",
        "issue_description",
        "issue_count",
        "affected_record_rate_pct",
    ]
    if quality_issues.empty:
        return pd.DataFrame(columns=columns)
    summary = quality_issues.groupby(
        ["rule_code", "quality_dimension", "severity", "issue_description"], as_index=False
    ).agg(issue_count=("issue_id", "count"))
    summary["affected_record_rate_pct"] = (
        (summary["issue_count"] / extracted_count * 100).round(2)
        if extracted_count
        else 0
    )
    return summary.sort_values(
        ["issue_count", "rule_code"],
        ascending=[False, True],
    ).reset_index(drop=True)


def create_delay_statistics(flights: pd.DataFrame) -> pd.DataFrame:
    non_cancelled = flights.loc[~flights["is_cancelled"], "delay_minutes"]
    if non_cancelled.empty:
        return pd.DataFrame(columns=["metric", "value"])
    metrics = {
        "count": len(non_cancelled),
        "mean": non_cancelled.mean(),
        "median": non_cancelled.median(),
        "standard_deviation": non_cancelled.std(ddof=1),
        "minimum": non_cancelled.min(),
        "p25": non_cancelled.quantile(0.25),
        "p75": non_cancelled.quantile(0.75),
        "p90": non_cancelled.quantile(0.90),
        "p95": non_cancelled.quantile(0.95),
        "maximum": non_cancelled.max(),
    }
    return pd.DataFrame(
        [
            {"metric": key, "value": round(float(value), 2)}
            for key, value in metrics.items()
        ]
    )


def create_powerbi_star_schema(
    flights: pd.DataFrame,
    quality_issues: pd.DataFrame,
    output_dir: Path,
) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)

    dim_airline = pd.DataFrame(
        {"airline": sorted(flights["airline"].dropna().unique())}
    )
    dim_airline.insert(0, "airline_key", range(1, len(dim_airline) + 1))

    airport_codes = sorted(
        set(flights["origin"].dropna()).union(set(flights["destination"].dropna()))
    )
    dim_airport = pd.DataFrame({"airport_code": airport_codes})
    dim_airport.insert(0, "airport_key", range(1, len(dim_airport) + 1))

    dates = pd.Series(
        pd.to_datetime(sorted(flights["flight_date"].dropna().unique())),
        dtype="datetime64[ns]",
    )
    dim_date = pd.DataFrame({"date": dates.dt.date})
    dim_date["date_key"] = dates.dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dates.dt.year
    dim_date["quarter"] = "Q" + dates.dt.quarter.astype(str)
    dim_date["month_number"] = dates.dt.month
    dim_date["month_name"] = dates.dt.month_name()
    dim_date["week_number"] = dates.dt.isocalendar().week.astype(int)
    dim_date["weekday_number"] = dates.dt.weekday + 1
    dim_date["weekday_name"] = dates.dt.day_name()
    dim_date = dim_date[
        [
            "date_key",
            "date",
            "year",
            "quarter",
            "month_number",
            "month_name",
            "week_number",
            "weekday_number",
            "weekday_name",
        ]
    ]

    airline_map = dim_airline.set_index("airline")["airline_key"]
    airport_map = dim_airport.set_index("airport_code")["airport_key"]
    fact = flights.copy()
    fact.insert(0, "flight_key", range(1, len(fact) + 1))
    fact["airline_key"] = fact["airline"].map(airline_map)
    fact["origin_airport_key"] = fact["origin"].map(airport_map)
    fact["destination_airport_key"] = fact["destination"].map(airport_map)
    fact["date_key"] = (
        pd.to_datetime(fact["flight_date"]).dt.strftime("%Y%m%d").astype(int)
    )
    fact_flights = fact[[
        "flight_key", "flight_id", "airline_key", "origin_airport_key", "destination_airport_key",
        "date_key", "scheduled_time", "actual_time", "scheduled_hour", "route", "gate", "status",
        "passengers", "delay_minutes", "delay_band", "is_on_time", "is_delayed", "is_cancelled",
    ]]

    fact_quality = quality_issues.copy()
    tables = {
        "fact_flights": fact_flights,
        "dim_airline": dim_airline,
        "dim_airport": dim_airport,
        "dim_date": dim_date,
        "fact_quality_issues": fact_quality,
    }
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    LOGGER.info("Created Power BI star-schema CSVs in %s", output_dir)
    return tables


def create_all_reports(
    flights: pd.DataFrame,
    rejected: pd.DataFrame,
    quality_issues: pd.DataFrame,
    extracted_count: int,
) -> dict[str, pd.DataFrame]:
    reports = {
        "airline": create_airline_kpis(flights),
        "route": create_route_kpis(flights),
        "daily": create_daily_kpis(flights),
        "monthly": create_monthly_kpis(flights),
        "executive": create_executive_summary(flights, rejected, extracted_count),
        "quality": create_quality_summary(quality_issues, extracted_count),
        "delay_statistics": create_delay_statistics(flights),
    }
    LOGGER.info("Created operational, quality, and statistical reports")
    return reports
