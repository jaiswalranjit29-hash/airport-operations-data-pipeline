"""Generate a deterministic synthetic airport dataset with realistic quality problems."""
from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

AIRLINES = [
    ("LH", "Lufthansa"),
    ("DE", "Condor"),
    ("BA", "British Airways"),
    ("AF", "Air France"),
    ("KL", "KLM"),
    ("EK", "Emirates"),
    ("UA", "United Airlines"),
    ("IB", "Iberia"),
]
ROUTES = [
    ("FRA", "BER"), ("FRA", "MUC"), ("FRA", "HAM"), ("FRA", "LHR"),
    ("FRA", "CDG"), ("FRA", "AMS"), ("FRA", "MAD"), ("FRA", "VIE"),
    ("FRA", "ZRH"), ("FRA", "PMI"), ("FRA", "JFK"), ("FRA", "DXB"),
]
GATES = ["A05", "A12", "A18", "B03", "B09", "B16", "C07", "D04", "E02", "Z15"]


def generate_rows(count: int, seed: int) -> list[dict[str, object]]:
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, 5, 30)
    rows: list[dict[str, object]] = []

    for index in range(1, count + 1):
        code, airline = rng.choice(AIRLINES)
        origin, destination = rng.choice(ROUTES)
        scheduled = start + timedelta(
            days=rng.randint(0, 179),
            hours=rng.randint(0, 17),
            minutes=rng.choice([0, 5, 10, 15, 20, 30, 40, 45, 50, 55]),
        )
        cancelled = rng.random() < 0.045
        delay = max(-15, round(rng.gauss(14, 24)))
        if rng.random() < 0.08:
            delay += rng.randint(45, 150)
        actual = None if cancelled else scheduled + timedelta(minutes=delay)
        status = "CANCELLED" if cancelled else ("DELAYED" if max(delay, 0) > 15 else "ON_TIME")
        row = {
            "flight_id": f"{code}{scheduled:%m%d}{index:04d}",
            "airline": airline,
            "origin": origin,
            "destination": destination,
            "scheduled_time": scheduled.strftime("%Y-%m-%d %H:%M"),
            "actual_time": "" if actual is None else actual.strftime("%Y-%m-%d %H:%M"),
            "passengers": rng.randint(55, 330) if not cancelled else rng.randint(0, 25),
            "status": status,
            "gate": rng.choice(GATES),
        }
        rows.append(row)

    # Inject realistic data-quality problems into about 9% of rows.
    problem_indices = rng.sample(range(count), k=max(12, int(count * 0.09)))
    problem_types = [
        "missing_id", "duplicate_id", "bad_origin", "same_airport", "bad_date",
        "missing_actual", "negative_passengers", "bad_status", "missing_airline",
    ]
    for position, row_index in enumerate(problem_indices):
        issue = problem_types[position % len(problem_types)]
        row = rows[row_index]
        if issue == "missing_id":
            row["flight_id"] = ""
        elif issue == "duplicate_id" and row_index > 0:
            row["flight_id"] = rows[row_index - 1]["flight_id"]
        elif issue == "bad_origin":
            row["origin"] = "FR"
        elif issue == "same_airport":
            row["destination"] = row["origin"]
        elif issue == "bad_date":
            row["scheduled_time"] = "not-a-date"
        elif issue == "missing_actual":
            row["actual_time"] = ""
            row["status"] = "DELAYED"
        elif issue == "negative_passengers":
            row["passengers"] = -rng.randint(1, 20)
        elif issue == "bad_status":
            row["status"] = "BOARDING"
        elif issue == "missing_airline":
            row["airline"] = ""

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/raw/flights_raw.csv"))
    args = parser.parse_args()

    rows = generate_rows(args.rows, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} synthetic rows at {args.output}")


if __name__ == "__main__":
    main()
