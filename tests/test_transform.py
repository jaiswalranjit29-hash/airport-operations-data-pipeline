from __future__ import annotations

import pandas as pd
import unittest

from src.transform import transform_flights


def make_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "flight_id": "LH1234",
        "airline": "Lufthansa",
        "origin": "fra",
        "destination": "ber",
        "scheduled_time": "2026-07-20 10:00",
        "actual_time": "2026-07-20 10:40",
        "passengers": "150",
        "status": "delayed",
        "gate": "A12",
    }
    row.update(overrides)
    return row


class TransformFlightsTests(unittest.TestCase):
    def test_valid_row_is_cleaned_and_enriched(self) -> None:
        valid, rejected = transform_flights(pd.DataFrame([make_row()]))

        self.assertTrue(rejected.empty)
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid.loc[0, "origin"], "FRA")
        self.assertEqual(valid.loc[0, "destination"], "BER")
        self.assertEqual(valid.loc[0, "status"], "DELAYED")
        self.assertEqual(valid.loc[0, "route"], "FRA-BER")
        self.assertEqual(valid.loc[0, "delay_minutes"], 40)
        self.assertTrue(bool(valid.loc[0, "is_delayed"]))

    def test_invalid_rows_are_rejected(self) -> None:
        examples = [
            ({"flight_id": None}, "missing flight_id"),
            ({"destination": "XX"}, "invalid destination"),
            ({"passengers": "-1"}, "passengers must be a non-negative integer"),
            ({"scheduled_time": "not-a-date"}, "invalid scheduled_time"),
            ({"status": "BOARDING"}, "invalid status"),
        ]
        for overrides, reason in examples:
            with self.subTest(reason=reason):
                valid, rejected = transform_flights(
                    pd.DataFrame([make_row(**overrides)])
                )
                self.assertTrue(valid.empty)
                self.assertEqual(len(rejected), 1)
                self.assertIn(reason, rejected.loc[0, "rejection_reason"])

    def test_duplicate_flight_id_rejects_later_row(self) -> None:
        rows = [make_row(), make_row(actual_time="2026-07-20 10:45")]
        valid, rejected = transform_flights(pd.DataFrame(rows))

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 1)
        self.assertIn("duplicate flight_id", rejected.loc[0, "rejection_reason"])

    def test_cancelled_flight_may_have_no_actual_time(self) -> None:
        row = make_row(status="cancelled", actual_time=None, passengers="0")
        valid, rejected = transform_flights(pd.DataFrame([row]))

        self.assertTrue(rejected.empty)
        self.assertEqual(valid.loc[0, "status"], "CANCELLED")
        self.assertEqual(valid.loc[0, "delay_minutes"], 0)
        self.assertFalse(bool(valid.loc[0, "is_delayed"]))

    def test_early_flight_has_zero_delay(self) -> None:
        row = make_row(actual_time="2026-07-20 09:50", status="on time")
        valid, _ = transform_flights(pd.DataFrame([row]))

        self.assertEqual(valid.loc[0, "delay_minutes"], 0)

    def test_missing_required_column_fails_fast(self) -> None:
        dataframe = pd.DataFrame([make_row()]).drop(columns=["status"])

        with self.assertRaisesRegex(ValueError, "Missing required columns: status"):
            transform_flights(dataframe)


if __name__ == "__main__":
    unittest.main()
