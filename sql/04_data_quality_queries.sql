SET search_path TO airport_ops, public;

-- Open high-severity issues requiring ownership and resolution.
SELECT issue_id, flight_id, rule_code, issue_description, owner_name
FROM fact_quality_issue
WHERE severity = 'High' AND workflow_status = 'Open'
ORDER BY created_at;

-- Quality trend based on pipeline audit history.
SELECT
    run_timestamp::date AS run_date,
    SUM(extracted_records) AS extracted_records,
    SUM(rejected_records) AS rejected_records,
    ROUND(100.0 * SUM(rejected_records) / NULLIF(SUM(extracted_records), 0), 2) AS rejection_rate_pct
FROM pipeline_run
GROUP BY run_timestamp::date
ORDER BY run_date;

-- Duplicate check retained as a database-side control.
SELECT flight_id, COUNT(*) AS duplicate_count
FROM fact_flight
GROUP BY flight_id
HAVING COUNT(*) > 1;

-- Referential integrity check (expected result: zero rows).
SELECT f.flight_id
FROM fact_flight f
LEFT JOIN dim_airline a ON a.airline_key = f.airline_key
LEFT JOIN dim_airport o ON o.airport_key = f.origin_airport_key
LEFT JOIN dim_airport d ON d.airport_key = f.destination_airport_key
WHERE a.airline_key IS NULL OR o.airport_key IS NULL OR d.airport_key IS NULL;
