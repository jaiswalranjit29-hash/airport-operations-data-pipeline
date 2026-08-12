# Power BI Model and Dashboard Guide

## Import tables

Import all CSV files from `data/powerbi/`.

## Relationships

Create these one-to-many relationships with single-direction filtering:

- `DimAirline[airline_key]` → `FactFlights[airline_key]`
- `DimAirport[airport_key]` → `FactFlights[origin_airport_key]` (active)
- `DimAirport[airport_key]` → `FactFlights[destination_airport_key]` (inactive)
- `DimDate[date_key]` → `FactFlights[date_key]`

`FactQualityIssues` is intentionally a separate fact table. It has no reliable flight relationship because rejected rows may have missing or invalid flight IDs. Analyse it by rule, dimension, severity, and workflow status.

## Model rules

- Mark `DimDate[date]` as the date table.
- Hide technical keys from report view.
- Sort `month_name` by `month_number`.
- Sort `weekday_name` by `weekday_number`.
- Prefer measures over calculated columns for aggregations.
- Keep relationships one-to-many and avoid bidirectional filtering unless justified.

## Page 1: Executive Overview

KPI cards:

- Total Flights
- Total Passengers
- On-Time Rate
- Delay Rate
- Cancellation Rate
- Average Delay
- Open High-Severity Issues

Visual:

- line chart: On-Time Rate by date.

## Page 2: Flight Performance

- bar chart: Delay Rate by airline;
- donut chart: Total Flights by delay band;
- bar chart: Total Passengers by route;
- airline matrix with flights, passengers, average delay, on-time rate, and cancellation rate.

## Page 3: Data Quality

- total issues;
- open issues;
- high-severity open issues;
- issue count by rule;
- issue distribution by severity.

## Page 4: Issue Details

- slicers for severity, quality dimension, and workflow status;
- detail table with issue ID, flight ID, rule, dimension, severity, status, owner, description, and resolution notes.

## Management narrative

The report should answer:

1. Are operations becoming more or less punctual?
2. Which airlines and routes have the highest delay risk?
3. How many passengers are affected?
4. Which data-quality rules fail most often?
5. Which high-severity issues are still unresolved?
