from __future__ import annotations

import pandas as pd
import unittest

from src.report import create_airline_kpis, create_daily_kpis


def sample_flights() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "flight_id": ["LH1", "LH2", "BA1"],
            "airline": ["Lufthansa", "Lufthansa", "British Airways"],
            "flight_date": [
                pd.Timestamp("2026-07-20").date(),
                pd.Timestamp("2026-07-20").date(),
                pd.Timestamp("2026-07-21").date(),
            ],
            "delay_minutes": [10, 30, 20],
            "is_delayed": [False, True, True],
            "passengers": [100, 150, 120],
            "status": ["ON_TIME", "DELAYED", "CANCELLED"],
        }
    )


class ReportTests(unittest.TestCase):
    def test_airline_report_aggregates_metrics(self) -> None:
        report = create_airline_kpis(sample_flights())
        lufthansa = report.loc[report["airline"] == "Lufthansa"].iloc[0]

        self.assertEqual(lufthansa["total_flights"], 2)
        self.assertEqual(lufthansa["delayed_flights"], 1)
        self.assertEqual(lufthansa["average_delay_minutes"], 20)
        self.assertEqual(lufthansa["total_passengers"], 250)

    def test_daily_report_has_one_row_per_date(self) -> None:
        report = create_daily_kpis(sample_flights())

        self.assertEqual(len(report), 2)
        self.assertEqual(report["total_flights"].sum(), 3)


if __name__ == "__main__":
    unittest.main()
