# Data Dictionary

This project uses one raw flight input, a cleaned flight output, rejected-record outputs, reporting tables, and Power BI fact/dimension exports.

## Raw input: `data/raw/flights_raw.csv`

| Column | Meaning |
|---|---|
| `flight_id` | Flight identifier used for uniqueness checks |
| `airline` | Airline name |
| `origin` | Three-letter origin airport code |
| `destination` | Three-letter destination airport code |
| `scheduled_time` | Scheduled departure timestamp |
| `actual_time` | Actual departure timestamp; may be empty for cancelled flights |
| `passengers` | Passenger count |
| `status` | Expected values: `ON_TIME`, `DELAYED`, `CANCELLED` |
| `gate` | Gate identifier |

## Clean output: `data/processed/flights_clean.csv`

The clean dataset keeps the validated source fields and adds:

| Column | Meaning |
|---|---|
| `route` | `origin-destination` route label |
| `flight_date` | Date derived from `scheduled_time` |
| `month` | Calendar month in `YYYY-MM` format |
| `weekday` | Weekday name |
| `scheduled_hour` | Scheduled departure hour |
| `delay_minutes` | Non-negative calculated delay in minutes |
| `delay_band` | `ON_TIME`, `16-30`, `31-60`, `61-120`, `120+`, or `CANCELLED` |
| `is_on_time` | Boolean on-time flag |
| `is_delayed` | Boolean delayed flag |
| `is_cancelled` | Boolean cancellation flag |
| `source_row_number` | Original CSV row number including the header offset |

## Rejected records: `data/rejected/flights_rejected.csv`

Rejected rows retain the cleaned source fields and add `rejection_reason`. Multiple rule failures are separated by `; `.

## Quality issues: `data/rejected/quality_issues.csv`

| Column | Meaning |
|---|---|
| `issue_id` | Generated issue identifier such as `ISS-00001` |
| `source_row_number` | Source row that triggered the issue |
| `flight_id` | Flight ID when available |
| `rule_code` | Data-quality rule identifier (`DQ001`-`DQ011`) |
| `quality_dimension` | Completeness, Validity, Uniqueness, or Consistency |
| `severity` | Medium or High in the current ruleset |
| `issue_description` | Human-readable rule failure |
| `workflow_status` | Initial value is `Open` |
| `owner` | Optional data-quality owner |
| `resolution_notes` | Optional resolution notes |

## Power BI exports: `data/powerbi/`

- `fact_flights.csv` - flight-level fact table with integer dimension keys.
- `fact_quality_issues.csv` - quality-issue fact table.
- `dim_airline.csv` - airline dimension.
- `dim_airport.csv` - airport dimension.
- `dim_date.csv` - dates present in the accepted flight data with calendar attributes.

The quality-issue fact is intentionally not joined to the flight fact because rejected records can have missing or invalid flight IDs.
