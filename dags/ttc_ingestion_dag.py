"""Airflow DAG: ingest live TTC vehicle positions every 15 minutes.

Three tasks, chained via XCom:
    fetch_and_save  ->  validate  ->  load_to_snowflake

XCom only carries a small metadata dict (raw file path + ingest timestamp),
not the records themselves. The downstream tasks re-read the raw JSON from
disk, so each task is independently retryable.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pendulum
from airflow.decorators import dag, task

from ingestion.fetch_vehicle_positions import DEFAULT_FEED_URL, fetch_feed
from ingestion.utils import (
    get_snowflake_connection,
    insert_vehicle_positions,
    parse_vehicle_record,
    save_raw_payload,
    utc_now,
)

log = logging.getLogger(__name__)


@dag(
    dag_id="ttc_ingestion_dag",
    description="Fetch live TTC vehicle positions and append to RAW.vehicle_positions.",
    schedule="*/15 * * * *",
    start_date=pendulum.datetime(2026, 5, 17, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "riyasat",
        "retries": 1,
        "retry_delay": pendulum.duration(minutes=2),
    },
    tags=["ttc", "ingestion"],
)
def ttc_ingestion_dag():

    @task
    def fetch_and_save() -> dict:
        """Hit the live feed, write the raw JSON snapshot to disk."""
        ingested_at = utc_now()
        url = os.environ.get("TTC_VEHICLE_FEED_URL", DEFAULT_FEED_URL)
        log.info("Fetching feed: %s", url)
        payload = fetch_feed(url)
        vehicles = payload.get("vehicle") or []
        raw_path = save_raw_payload(payload, ingested_at)
        log.info("Saved %d vehicles -> %s", len(vehicles), raw_path)
        return {
            "raw_path": str(raw_path),
            "ingested_at": ingested_at.isoformat(),
            "vehicle_count": len(vehicles),
        }

    @task
    def validate(meta: dict) -> dict:
        """Sanity checks before we touch Snowflake."""
        path = Path(meta["raw_path"])
        if not path.exists():
            raise FileNotFoundError(f"Raw file missing: {path}")
        payload = json.loads(path.read_text())
        vehicles = payload.get("vehicle") or []
        if not vehicles:
            raise ValueError("Feed returned no vehicles")
        with_ids = sum(1 for v in vehicles if v.get("id") and v.get("routeTag"))
        if with_ids == 0:
            raise ValueError("No vehicles had both id and routeTag")
        log.info(
            "Validated %d vehicles, %d with required keys",
            len(vehicles), with_ids,
        )
        return meta

    @task
    def load_to_snowflake(meta: dict) -> int:
        """Parse the raw JSON and bulk-insert rows into RAW.vehicle_positions."""
        path = Path(meta["raw_path"])
        ingested_at = datetime.fromisoformat(meta["ingested_at"])
        payload = json.loads(path.read_text())
        vehicles = payload.get("vehicle") or []

        records = []
        for v in vehicles:
            rec = parse_vehicle_record(v, ingested_at, str(path))
            if rec is not None:
                records.append(rec)
        log.info("Parsed %d records, loading to Snowflake", len(records))

        with get_snowflake_connection() as conn:
            n = insert_vehicle_positions(conn, records)
        log.info("Inserted %d rows into RAW.vehicle_positions", n)
        return n

    load_to_snowflake(validate(fetch_and_save()))


ttc_ingestion_dag()
