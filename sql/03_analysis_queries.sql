SET search_path TO airport_ops, public;

-- 1. SELECT, WHERE, ORDER BY: severe operational delays.
SELECT flight_id, airline, route, scheduled_time, delay_minutes
FROM vw_flight_operations
WHERE delay_minutes > 60 AND status <> 'CANCELLED'
ORDER BY delay_minutes DESC;

-- 2. JOIN + GROUP BY + aggregate functions: airline performance.
SELECT
    a.airline_name,
    COUNT(*) AS total_flights,
    ROUND(AVG(f.delay_minutes)::numeric, 2) AS average_delay_minutes,
    SUM(f.passengers) AS total_passengers
FROM fact_flight f
JOIN dim_airline a ON a.airline_key = f.airline_key
GROUP BY a.airline_name
ORDER BY average_delay_minutes DESC;

-- 3. CASE: classify operational performance.
SELECT
    flight_id,
    delay_minutes,
    CASE
        WHEN is_cancelled THEN 'Cancelled'
        WHEN delay_minutes <= 15 THEN 'On time'
        WHEN delay_minutes <= 60 THEN 'Moderate delay'
        ELSE 'Severe delay'
    END AS service_classification
FROM fact_flight;

-- 4. Subquery: flights delayed more than the overall average.
SELECT flight_id, route, delay_minutes
FROM fact_flight
WHERE delay_minutes > (SELECT AVG(delay_minutes) FROM fact_flight)
ORDER BY delay_minutes DESC;

-- 5. CTE: busiest routes with a minimum volume threshold.
WITH route_summary AS (
    SELECT
        route,
        COUNT(*) AS total_flights,
        SUM(passengers) AS total_passengers,
        ROUND(AVG(delay_minutes)::numeric, 2) AS average_delay_minutes
    FROM fact_flight
    GROUP BY route
)
SELECT *
FROM route_summary
WHERE total_flights >= 10
ORDER BY total_passengers DESC;

-- 6. Window function: rank airlines by delay rate.
WITH airline_rates AS (
    SELECT
        a.airline_name,
        COUNT(*) AS total_flights,
        ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_delayed) / NULLIF(COUNT(*), 0), 2) AS delay_rate_pct
    FROM fact_flight f
    JOIN dim_airline a ON a.airline_key = f.airline_key
    GROUP BY a.airline_name
)
SELECT
    airline_name,
    total_flights,
    delay_rate_pct,
    DENSE_RANK() OVER (ORDER BY delay_rate_pct DESC) AS delay_rank
FROM airline_rates;

-- 7. Window functions: running passenger total and previous-day comparison.
WITH daily AS (
    SELECT
        d.full_date,
        SUM(f.passengers) AS passengers,
        COUNT(*) FILTER (WHERE f.is_delayed) AS delayed_flights
    FROM fact_flight f
    JOIN dim_date d ON d.date_key = f.date_key
    GROUP BY d.full_date
)
SELECT
    full_date,
    passengers,
    SUM(passengers) OVER (ORDER BY full_date) AS running_passenger_total,
    passengers - LAG(passengers) OVER (ORDER BY full_date) AS change_vs_previous_day,
    delayed_flights
FROM daily
ORDER BY full_date;

-- 8. Top route per airline with ROW_NUMBER.
WITH route_by_airline AS (
    SELECT
        a.airline_name,
        f.route,
        COUNT(*) AS total_flights,
        ROW_NUMBER() OVER (
            PARTITION BY a.airline_name
            ORDER BY COUNT(*) DESC, f.route
        ) AS route_rank
    FROM fact_flight f
    JOIN dim_airline a ON a.airline_key = f.airline_key
    GROUP BY a.airline_name, f.route
)
SELECT airline_name, route, total_flights
FROM route_by_airline
WHERE route_rank = 1
ORDER BY airline_name;

-- 9. Data-quality issue distribution.
SELECT
    quality_dimension,
    severity,
    COUNT(*) AS issue_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_of_all_issues_pct
FROM fact_quality_issue
GROUP BY quality_dimension, severity
ORDER BY issue_count DESC;

-- 10. Transaction example for resolving a quality issue.
BEGIN;
UPDATE fact_quality_issue
SET workflow_status = 'Closed',
    owner_name = 'Data Steward',
    resolution_notes = 'Source record corrected and reprocessed.'
WHERE issue_id = 'ISS-00001';
COMMIT;
