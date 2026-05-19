"""Download static TTC route reference data and append to RAW.routes.

Uses the UMOIQ routeList endpoint rather than the full GTFS static feed:
it returns just (tag, title) per route, which is all we need for the MVP.
Short/long name parsing happens in the dbt staging model.

Run locally:
    python -m ingestion.fetch_static_gtfs --dry-run    # parses, skips Snowflake
    python -m ingestion.fetch_static_gtfs              # full run with Snowflake load
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

import requests

from ingestion.utils import (
    get_snowflake_connection,
    save_raw_payload,
    utc_now,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("ttc_routes_ingestion")

DEFAULT_ROUTES_URL = (
    "https://retro.umoiq.com/service/publicJSONFeed?command=routeList&a=ttc"
)

ROUTES_COLS = ["route_id", "route_title", "_ingested_at", "source_file"]


def fetch_routes(url: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_route(raw: dict, ingested_at, source_file: str) -> dict | None:
    tag = raw.get("tag")
    if not tag:
        return None
    return {
        "route_id": str(tag),
        "route_title": raw.get("title"),
        "_ingested_at": ingested_at.replace(tzinfo=None),
        "source_file": source_file,
    }


def insert_routes(conn, records: list[dict]) -> int:
    if not records:
        return 0
    placeholders = ", ".join(["%s"] * len(ROUTES_COLS))
    col_list = ", ".join(ROUTES_COLS)
    sql = f"INSERT INTO routes ({col_list}) VALUES ({placeholders})"
    rows = [tuple(r[c] for c in ROUTES_COLS) for r in records]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


def main(dry_run: bool = False) -> int:
    url = os.environ.get("TTC_ROUTES_URL", DEFAULT_ROUTES_URL)
    ingested_at = utc_now()

    log.info("Fetching routes: %s", url)
    payload = fetch_routes(url)
    raw_routes = payload.get("route") or []
    log.info("Feed returned %d routes", len(raw_routes))

    raw_path = save_raw_payload(payload, ingested_at, prefix="routes")
    log.info("Saved raw payload: %s", raw_path)

    records: list[dict] = []
    skipped = 0
    for r in raw_routes:
        rec = parse_route(r, ingested_at, str(raw_path))
        if rec is None:
            skipped += 1
        else:
            records.append(rec)
    log.info("Parsed %d records (skipped %d)", len(records), skipped)

    if dry_run:
        sample = records[0] if records else None
        log.info("Dry-run: skipping Snowflake load. Sample record: %s", sample)
        return 0

    log.info("Connecting to Snowflake...")
    with get_snowflake_connection() as conn:
        n = insert_routes(conn, records)
    log.info("Inserted %d rows into RAW.routes", n)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip Snowflake write.")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
