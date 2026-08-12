CREATE SCHEMA IF NOT EXISTS airport_ops;
SET search_path TO airport_ops, public;

CREATE TABLE IF NOT EXISTS dim_airline (
    airline_key BIGSERIAL PRIMARY KEY,
    airline_name VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_airport (
    airport_key BIGSERIAL PRIMARY KEY,
    airport_code CHAR(3) NOT NULL UNIQUE,
    CONSTRAINT ck_airport_code CHECK (airport_code ~ '^[A-Z]{3}$')
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    quarter CHAR(2) NOT NULL,
    month_number SMALLINT NOT NULL,
    month_name VARCHAR(12) NOT NULL,
    week_number SMALLINT NOT NULL,
    weekday_number SMALLINT NOT NULL,
    weekday_name VARCHAR(12) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_flight (
    flight_key BIGSERIAL PRIMARY KEY,
    flight_id VARCHAR(16) NOT NULL UNIQUE,
    airline_key BIGINT NOT NULL REFERENCES dim_airline(airline_key),
    origin_airport_key BIGINT NOT NULL REFERENCES dim_airport(airport_key),
    destination_airport_key BIGINT NOT NULL REFERENCES dim_airport(airport_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    scheduled_time TIMESTAMP NOT NULL,
    actual_time TIMESTAMP NULL,
    route CHAR(7) NOT NULL,
    gate VARCHAR(10),
    status VARCHAR(12) NOT NULL CHECK (status IN ('ON_TIME', 'DELAYED', 'CANCELLED')),
    passengers INTEGER NOT NULL CHECK (passengers >= 0),
    delay_minutes INTEGER NOT NULL CHECK (delay_minutes >= 0),
    delay_band VARCHAR(12) NOT NULL,
    is_on_time BOOLEAN NOT NULL,
    is_delayed BOOLEAN NOT NULL,
    is_cancelled BOOLEAN NOT NULL,
    source_row_number INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_different_airports CHECK (origin_airport_key <> destination_airport_key)
);

CREATE TABLE IF NOT EXISTS fact_quality_issue (
    quality_issue_key BIGSERIAL PRIMARY KEY,
    issue_id VARCHAR(20) NOT NULL UNIQUE,
    source_row_number INTEGER NOT NULL,
    flight_id VARCHAR(16),
    rule_code VARCHAR(10) NOT NULL,
    quality_dimension VARCHAR(30) NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
    issue_description VARCHAR(250) NOT NULL,
    workflow_status VARCHAR(20) NOT NULL DEFAULT 'Open',
    owner_name VARCHAR(120),
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_run (
    pipeline_run_key BIGSERIAL PRIMARY KEY,
    run_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    extracted_records INTEGER NOT NULL,
    accepted_records INTEGER NOT NULL,
    rejected_records INTEGER NOT NULL,
    run_status VARCHAR(20) NOT NULL,
    CONSTRAINT ck_pipeline_counts CHECK (
        extracted_records >= 0 AND accepted_records >= 0 AND rejected_records >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_fact_flight_date ON fact_flight(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_flight_airline ON fact_flight(airline_key);
CREATE INDEX IF NOT EXISTS idx_fact_flight_route ON fact_flight(route);
CREATE INDEX IF NOT EXISTS idx_fact_flight_delay ON fact_flight(delay_minutes);
CREATE INDEX IF NOT EXISTS idx_quality_rule ON fact_quality_issue(rule_code);
CREATE INDEX IF NOT EXISTS idx_quality_status ON fact_quality_issue(workflow_status);
