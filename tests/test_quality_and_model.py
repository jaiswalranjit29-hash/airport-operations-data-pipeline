from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.management_summary import create_management_summary
from src.report import (
    create_all_reports,
    create_executive_summary,
    create_powerbi_star_schema,
)
from src.transform import create_quality_issues, transform_flights


class QualityAndModelTests(unittest.TestCase):
    def test_rejected_record_becomes_workflow_issue(self) -> None:
        raw = pd.DataFrame([{
            "flight_id": "AB1234",
            "airline": "Example Air",
            "origin": "FRA",
            "destination": "FRA",
            "scheduled_time": "2026-01-01 10:00",
            "actual_time": "2026-01-01 10:10",
            "passengers": "100",
            "status": "ON_TIME",
            "gate": "A01",
        }])
        valid, rejected = transform_flights(raw)
        issues = create_quality_issues(rejected)

        self.assertTrue(valid.empty)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues.loc[0, "rule_code"], "DQ007")
        self.assertEqual(issues.loc[0, "workflow_status"], "Open")

    def test_executive_summary_reconciles_counts(self) -> None:
        flights = pd.DataFrame({
            "flight_id": ["A1", "A2"],
            "passengers": [100, 150],
            "is_on_time": [True, False],
            "is_delayed": [False, True],
            "is_cancelled": [False, False],
            "delay_minutes": [5, 40],
        })
        rejected = pd.DataFrame({"flight_id": ["BAD"]})
        summary = create_executive_summary(flights, rejected, 3).iloc[0]

        self.assertEqual(summary["accepted_records"], 2)
        self.assertEqual(summary["rejected_records"], 1)
        self.assertEqual(summary["total_passengers"], 250)

    def test_powerbi_star_schema_exports_dimensions_and_fact(self) -> None:
        flights = pd.DataFrame({
            "flight_id": ["LH1"],
            "airline": ["Lufthansa"],
            "origin": ["FRA"],
            "destination": ["BER"],
            "flight_date": [pd.Timestamp("2026-01-01").date()],
            "scheduled_time": [pd.Timestamp("2026-01-01 10:00")],
            "actual_time": [pd.Timestamp("2026-01-01 10:20")],
            "scheduled_hour": [10],
            "route": ["FRA-BER"],
            "gate": ["A01"],
            "status": ["DELAYED"],
            "passengers": [120],
            "delay_minutes": [20],
            "delay_band": ["16-30"],
            "is_on_time": [False],
            "is_delayed": [True],
            "is_cancelled": [False],
        })
        issues = pd.DataFrame(columns=[
            "issue_id", "source_row_number", "flight_id", "rule_code", "quality_dimension",
            "severity", "issue_description", "workflow_status", "owner", "resolution_notes",
        ])
        with tempfile.TemporaryDirectory() as folder:
            tables = create_powerbi_star_schema(flights, issues, Path(folder))
            self.assertEqual(len(tables["fact_flights"]), 1)
            self.assertEqual(len(tables["dim_airport"]), 2)
            self.assertTrue((Path(folder) / "dim_date.csv").exists())

    def test_reports_handle_dataset_with_no_valid_flights(self) -> None:
        raw = pd.DataFrame([{
            "flight_id": "AB1234",
            "airline": "Example Air",
            "origin": "FRA",
            "destination": "FRA",
            "scheduled_time": "2026-01-01 10:00",
            "actual_time": "2026-01-01 10:10",
            "passengers": "100",
            "status": "ON_TIME",
            "gate": "A01",
        }])
        valid, rejected = transform_flights(raw)
        issues = create_quality_issues(rejected)
        reports = create_all_reports(valid, rejected, issues, len(raw))

        with tempfile.TemporaryDirectory() as folder:
            tables = create_powerbi_star_schema(valid, issues, Path(folder))
            self.assertTrue(tables["fact_flights"].empty)
            self.assertTrue((Path(folder) / "dim_date.csv").exists())

        summary = create_management_summary(reports)
        self.assertIn("no valid flights were accepted", summary.lower())


if __name__ == "__main__":
    unittest.main()
