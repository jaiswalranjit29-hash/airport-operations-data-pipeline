"""Clean, validate, enrich, and classify flight records."""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable

import pandas as pd

from src.config import DELAY_THRESHOLD_MINUTES

LOGGER = logging.getLogger("airport_pipeline.transform")

REQUIRED_COLUMNS = {
    "flight_id", "airline", "origin", "destination", "scheduled_time",
    "actual_time", "passengers", "status", "gate",
}
VALID_STATUSES = {"ON_TIME", "DELAYED", "CANCELLED"}
STATUS_ALIASES = {
    "ON TIME": "ON_TIME",
    "ON-TIME": "ON_TIME",
    "CANCELED": "CANCELLED",
}
RULE_METADATA = {
    "missing flight_id": ("DQ001", "Completeness", "High"),
    "invalid flight_id format": ("DQ002", "Validity", "Medium"),
    "duplicate flight_id": ("DQ003", "Uniqueness", "High"),
    "missing airline": ("DQ004", "Completeness", "High"),
    "invalid origin": ("DQ005", "Validity", "High"),
    "invalid destination": ("DQ006", "Validity", "High"),
    "origin equals destination": ("DQ007", "Consistency", "High"),
    "invalid scheduled_time": ("DQ008", "Validity", "High"),
    "actual_time required for non-cancelled flight": ("DQ009", "Completeness", "Medium"),
    "invalid status": ("DQ010", "Validity", "High"),
    "passengers must be a non-negative integer": ("DQ011", "Validity", "High"),
}


def normalize_column_name(column: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", column.strip().lower())
    return normalized.strip("_")


def _clean_text(series: pd.Series, *, uppercase: bool = False) -> pd.Series:
    cleaned = series.astype("string").str.strip().replace("", pd.NA)
    return cleaned.str.upper() if uppercase else cleaned


def _append_reason(reasons: pd.Series, mask: pd.Series, message: str) -> pd.Series:
    selected = mask.fillna(False)
    separator = reasons.loc[selected].map(lambda value: "; " if value else "")
    reasons.loc[selected] = reasons.loc[selected] + separator + message
    return reasons


def _is_integer_like(series: pd.Series) -> pd.Series:
    return series.notna() & (series % 1 == 0)


def _delay_band(row: pd.Series) -> str:
    if row["status"] == "CANCELLED":
        return "CANCELLED"
    delay = int(row["delay_minutes"])
    if delay <= DELAY_THRESHOLD_MINUTES:
        return "ON_TIME"
    if delay <= 30:
        return "16-30"
    if delay <= 60:
        return "31-60"
    if delay <= 120:
        return "61-120"
    return "120+"


def transform_flights(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return clean and rejected records after applying data-quality rules."""
    df = raw_df.copy()
    df.columns = [normalize_column_name(column) for column in df.columns]

    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    df = df[list(sorted(REQUIRED_COLUMNS))]
    df.insert(0, "source_row_number", range(2, len(df) + 2))

    for column in ["airline", "gate"]:
        df[column] = _clean_text(df[column])
    for column in ["flight_id", "origin", "destination"]:
        df[column] = _clean_text(df[column], uppercase=True)

    status = _clean_text(df["status"], uppercase=True).str.replace(r"\s+", " ", regex=True)
    df["status"] = status.replace(STATUS_ALIASES)
    df["scheduled_time"] = pd.to_datetime(df["scheduled_time"], errors="coerce")
    df["actual_time"] = pd.to_datetime(df["actual_time"], errors="coerce")
    df["passengers"] = pd.to_numeric(df["passengers"], errors="coerce")

    reasons = pd.Series("", index=df.index, dtype="string")
    reasons = _append_reason(reasons, df["flight_id"].isna(), "missing flight_id")
    reasons = _append_reason(
        reasons,
        df["flight_id"].notna() & ~df["flight_id"].str.fullmatch(r"[A-Z0-9-]{4,16}", na=False),
        "invalid flight_id format",
    )
    reasons = _append_reason(
        reasons,
        df["flight_id"].notna() & df.duplicated("flight_id", keep="first"),
        "duplicate flight_id",
    )
    reasons = _append_reason(reasons, df["airline"].isna(), "missing airline")
    for column in ["origin", "destination"]:
        reasons = _append_reason(
            reasons,
            ~df[column].str.fullmatch(r"[A-Z]{3}", na=False),
            f"invalid {column}",
        )
    reasons = _append_reason(
        reasons,
        df["origin"].notna() & df["destination"].notna() & df["origin"].eq(df["destination"]),
        "origin equals destination",
    )
    reasons = _append_reason(reasons, df["scheduled_time"].isna(), "invalid scheduled_time")
    reasons = _append_reason(
        reasons,
        df["status"].ne("CANCELLED") & df["actual_time"].isna(),
        "actual_time required for non-cancelled flight",
    )
    reasons = _append_reason(reasons, ~df["status"].isin(VALID_STATUSES), "invalid status")
    reasons = _append_reason(
        reasons,
        ~_is_integer_like(df["passengers"]) | df["passengers"].lt(0),
        "passengers must be a non-negative integer",
    )

    df["rejection_reason"] = reasons
    rejected_df = df.loc[df["rejection_reason"].ne("")].copy()
    valid_df = df.loc[df["rejection_reason"].eq("")].copy()

    delay = (
        (valid_df["actual_time"] - valid_df["scheduled_time"])
        .dt.total_seconds().div(60).clip(lower=0).round()
    )
    valid_df["delay_minutes"] = delay.fillna(0).astype("int64")
    valid_df["is_cancelled"] = valid_df["status"].eq("CANCELLED")
    valid_df["is_delayed"] = (~valid_df["is_cancelled"]) & valid_df[
        "delay_minutes"
    ].gt(DELAY_THRESHOLD_MINUTES)
    valid_df["is_on_time"] = (~valid_df["is_cancelled"]) & ~valid_df["is_delayed"]
    valid_df["route"] = valid_df["origin"] + "-" + valid_df["destination"]
    valid_df["flight_date"] = valid_df["scheduled_time"].dt.date
    valid_df["scheduled_hour"] = valid_df["scheduled_time"].dt.hour.astype("int64")
    valid_df["weekday"] = valid_df["scheduled_time"].dt.day_name()
    valid_df["month"] = valid_df["scheduled_time"].dt.to_period("M").astype(str)
    valid_df["passengers"] = valid_df["passengers"].astype("int64")
    if valid_df.empty:
        valid_df["delay_band"] = pd.Series(dtype="string")
    else:
        valid_df["delay_band"] = valid_df.apply(_delay_band, axis=1)
    valid_df = valid_df.drop(columns=["rejection_reason"])

    clean_columns: Iterable[str] = [
        "flight_id", "airline", "origin", "destination", "route",
        "scheduled_time", "actual_time", "flight_date", "month", "weekday",
        "scheduled_hour", "passengers", "status", "gate", "delay_minutes",
        "delay_band", "is_on_time", "is_delayed", "is_cancelled", "source_row_number",
    ]
    rejected_columns: Iterable[str] = [
        "source_row_number", "flight_id", "airline", "origin", "destination",
        "scheduled_time", "actual_time", "passengers", "status", "gate", "rejection_reason",
    ]
    valid_df = valid_df[list(clean_columns)].reset_index(drop=True)
    rejected_df = rejected_df[list(rejected_columns)].reset_index(drop=True)
    LOGGER.info("Transformation completed: %d valid rows, %d rejected rows", len(valid_df), len(rejected_df))
    return valid_df, rejected_df


def create_quality_issues(rejected_df: pd.DataFrame) -> pd.DataFrame:
    """Explode rejected rows into traceable data-quality issue records."""
    columns = [
        "issue_id", "source_row_number", "flight_id", "rule_code", "quality_dimension",
        "severity", "issue_description", "workflow_status", "owner", "resolution_notes",
    ]
    if rejected_df.empty:
        return pd.DataFrame(columns=columns)

    records: list[dict[str, object]] = []
    issue_number = 1
    for row in rejected_df.to_dict("records"):
        for reason in str(row["rejection_reason"]).split("; "):
            rule_code, dimension, severity = RULE_METADATA.get(reason, ("DQ999", "Other", "Medium"))
            records.append({
                "issue_id": f"ISS-{issue_number:05d}",
                "source_row_number": row["source_row_number"],
                "flight_id": row.get("flight_id"),
                "rule_code": rule_code,
                "quality_dimension": dimension,
                "severity": severity,
                "issue_description": reason,
                "workflow_status": "Open",
                "owner": "",
                "resolution_notes": "",
            })
            issue_number += 1
    return pd.DataFrame(records, columns=columns)
