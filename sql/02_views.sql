SET search_path TO airport_ops, public;

CREATE OR REPLACE VIEW vw_flight_operations AS
SELECT
    f.flight_id,
    a.airline_name AS airline,
    o.airport_code AS origin,
    d.airport_code AS destination,
    f.route,
    dt.full_date AS flight_date,
    f.scheduled_time,
    f.actual_time,
    f.gate,
    f.status,
    f.passengers,
    f.delay_minutes,
    f.delay_band,
    f.is_on_time,
    f.is_delayed,
    f.is_cancelled
FROM fact_flight f
JOIN dim_airline a ON a.airline_key = f.airline_key
JOIN dim_airport o ON o.airport_key = f.origin_airport_key
JOIN dim_airport d ON d.airport_key = f.destination_airport_key
JOIN dim_date dt ON dt.date_key = f.date_key;

CREATE OR REPLACE VIEW vw_airline_performance AS
SELECT
    a.airline_name,
    COUNT(*) AS total_flights,
    COUNT(*) FILTER (WHERE f.is_on_time) AS on_time_flights,
    COUNT(*) FILTER (WHERE f.is_delayed) AS delayed_flights,
    COUNT(*) FILTER (WHERE f.is_cancelled) AS cancelled_flights,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_on_time) / NULLIF(COUNT(*), 0), 2) AS on_time_rate_pct,
    ROUND(AVG(f.delay_minutes)::numeric, 2) AS average_delay_minutes,
    SUM(f.passengers) AS total_passengers
FROM fact_flight f
JOIN dim_airline a ON a.airline_key = f.airline_key
GROUP BY a.airline_name;

CREATE OR REPLACE VIEW vw_open_quality_issues AS
SELECT
    issue_id,
    source_row_number,
    flight_id,
    rule_code,
    quality_dimension,
    severity,
    issue_description,
    workflow_status,
    owner_name,
    resolution_notes,
    created_at
FROM fact_quality_issue
WHERE workflow_status <> 'Closed';
