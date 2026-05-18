"""Shared helpers for TTC ingestion: parsing, raw-file IO, and Snowflake load."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import snowflake.connector
from dotenv import load_dotenv

# Load .env once at import so callers don't each have to remember.
load_dotenv()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def raw_data_dir() -> Path:
    # Defaults to ./data/raw so the same code works on the host and inside Airflow,
    # where docker-compose bind-mounts ./data -> /opt/airflow/data.
    return Path(os.getenv("RAW_DATA_DIR", "data/raw"))


def save_raw_payload(payload: dict, ingested_at: datetime) -> Path:
    out_dir = raw_data_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"vehicle_positions_{ingested_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    path = out_dir / fname
    path.write_text(json.dumps(payload))
    return path


def _safe_float(val: Any) -> float | None:
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> int | None:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def parse_direction_id(dir_tag: str | None) -> int | None:
    # dirTag looks like "339_0_MANW" — middle segment is the 0/1 direction.
    if not dir_tag:
        return None
    parts = dir_tag.split("_")
    if len(parts) < 2:
        return None
    return _safe_int(parts[1])


def parse_vehicle_record(
    raw: dict, ingested_at: datetime, source_file: str
) -> dict | None:
    """Map one feed entry to a row dict. Returns None if required keys are missing."""
    vehicle_id = raw.get("id")
    route_id = raw.get("routeTag")
    if not vehicle_id or not route_id:
        return None

    secs_since = _safe_int(raw.get("secsSinceReport"))
    recorded_at = (
        ingested_at - timedelta(seconds=secs_since) if secs_since is not None else None
    )
    dir_tag = raw.get("dirTag")

    # Snowflake TIMESTAMP_NTZ wants naive datetimes; strip tz here.
    return {
        "vehicle_id": str(vehicle_id),
        "route_id": str(route_id),
        "direction_tag": dir_tag,
        "direction_id": parse_direction_id(dir_tag),
        "latitude": _safe_float(raw.get("lat")),
        "longitude": _safe_float(raw.get("lon")),
        "speed_kmh": _safe_float(raw.get("speedKmHr")),
        "heading": _safe_float(raw.get("heading")),
        "secs_since_report": secs_since,
        "recorded_at": recorded_at.replace(tzinfo=None) if recorded_at else None,
        "_ingested_at": ingested_at.replace(tzinfo=None),
        "source_file": source_file,
    }


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "TTC_ANALYTICS"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
    )


VEHICLE_POSITION_COLS = [
    "vehicle_id", "route_id", "direction_tag", "direction_id",
    "latitude", "longitude", "speed_kmh", "heading",
    "secs_since_report", "recorded_at", "_ingested_at", "source_file",
]


def insert_vehicle_positions(conn, records: list[dict]) -> int:
    """Append-only bulk insert into RAW.vehicle_positions. Returns rows written."""
    if not records:
        return 0

    placeholders = ", ".join(["%s"] * len(VEHICLE_POSITION_COLS))
    col_list = ", ".join(VEHICLE_POSITION_COLS)
    sql = f"INSERT INTO vehicle_positions ({col_list}) VALUES ({placeholders})"
    rows = [tuple(r[c] for c in VEHICLE_POSITION_COLS) for r in records]

    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)
