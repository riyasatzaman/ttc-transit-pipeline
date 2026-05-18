"""Fetch live TTC vehicle positions and write them to Snowflake RAW.vehicle_positions.

Run locally:
    python -m ingestion.fetch_vehicle_positions --dry-run    # parses, skips Snowflake
    python -m ingestion.fetch_vehicle_positions              # full run with Snowflake load
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

import requests

from ingestion.utils import (
    get_snowflake_connection,
    insert_vehicle_positions,
    parse_vehicle_record,
    save_raw_payload,
    utc_now,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("ttc_ingestion")

DEFAULT_FEED_URL = (
    "https://retro.umoiq.com/service/publicJSONFeed?command=vehicleLocations&a=ttc"
)


def fetch_feed(url: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main(dry_run: bool = False) -> int:
    url = os.environ.get("TTC_VEHICLE_FEED_URL", DEFAULT_FEED_URL)
    ingested_at = utc_now()

    log.info("Fetching feed: %s", url)
    payload = fetch_feed(url)
    raw_vehicles = payload.get("vehicle") or []
    log.info("Feed returned %d vehicles", len(raw_vehicles))

    raw_path = save_raw_payload(payload, ingested_at)
    log.info("Saved raw payload: %s", raw_path)

    records: list[dict] = []
    skipped = 0
    for v in raw_vehicles:
        rec = parse_vehicle_record(v, ingested_at, str(raw_path))
        if rec is None:
            skipped += 1
        else:
            records.append(rec)
    log.info("Parsed %d records (skipped %d malformed)", len(records), skipped)

    if dry_run:
        sample = records[0] if records else None
        log.info("Dry-run: skipping Snowflake load. Sample record: %s", sample)
        return 0

    log.info("Connecting to Snowflake...")
    with get_snowflake_connection() as conn:
        n = insert_vehicle_positions(conn, records)
    log.info("Inserted %d rows into RAW.vehicle_positions", n)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip Snowflake write.")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
