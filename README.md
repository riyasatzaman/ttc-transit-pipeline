# TTC Transit Analytics Pipeline

End-to-end data engineering pipeline that ingests live Toronto TTC vehicle
location data every 15 minutes, lands it in Snowflake, transforms it with dbt
through staging / intermediate / mart layers, and serves a public Streamlit
dashboard for route reliability and delay analytics.

> Status: in active development. Day 1 setup (Snowflake + local scaffold + Airflow) in progress.

## Tech stack
- Python 3.11 (ingestion)
- Apache Airflow 2.8 via Docker Compose (orchestration)
- Snowflake (warehouse: `TTC_ANALYTICS`)
- dbt-core + dbt-snowflake (transformations)
- Streamlit (dashboard) deployed to Streamlit Cloud

## Folder layout
See the project spec. Top-level: `dags/`, `ingestion/`, `dbt_ttc/`, `dashboard/`, `tests/`.

## Quickstart (local)
1. Copy `.env.example` to `.env` and fill in Snowflake credentials.
2. `docker compose up airflow-init` (first time only).
3. `docker compose up` and open http://localhost:8080.

Full setup, architecture diagram, and screenshots will be added as the project lands.
