-- One-shot Snowflake bootstrap for the TTC Transit Analytics Pipeline.
--
-- Paste into a Snowsight worksheet and run all. Idempotent — every CREATE is
-- `IF NOT EXISTS`, so re-running is safe.

USE ROLE ACCOUNTADMIN;

-- Warehouse: small, auto-suspends after 60s to keep credits low.
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- Database + four schemas, one per pipeline layer.
CREATE DATABASE IF NOT EXISTS TTC_ANALYTICS;
USE DATABASE TTC_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS MARTS;

-- ---------------------------------------------------------------------------
-- RAW tables — append-only landing zone for ingestion.
-- ---------------------------------------------------------------------------
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS vehicle_positions (
    vehicle_id           VARCHAR        NOT NULL,
    route_id             VARCHAR        NOT NULL,
    direction_tag        VARCHAR,           -- raw dirTag, e.g. "339_0_MANW"
    direction_id         NUMBER(1, 0),      -- 0 or 1, parsed from dirTag
    latitude             FLOAT,
    longitude            FLOAT,
    speed_kmh            NUMBER(5, 2),
    heading              NUMBER(5, 2),
    secs_since_report    NUMBER(10, 0),
    recorded_at          TIMESTAMP_NTZ,     -- ingest_time - secs_since_report
    _ingested_at         TIMESTAMP_NTZ      NOT NULL,
    source_file          VARCHAR
);

CREATE TABLE IF NOT EXISTS routes (
    route_id     VARCHAR        NOT NULL,
    route_title  VARCHAR,                    -- raw "title" from the feed, e.g. "7-Bathurst"
    _ingested_at TIMESTAMP_NTZ  NOT NULL,
    source_file  VARCHAR
);

-- Sanity check: both should be 0 on a fresh setup.
SELECT 'vehicle_positions' AS table_name, COUNT(*) AS row_count FROM vehicle_positions
UNION ALL
SELECT 'routes',                          COUNT(*)               FROM routes;
