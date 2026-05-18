"""Unit tests for the ingestion parser logic."""
from datetime import datetime, timezone

from ingestion.utils import parse_direction_id, parse_vehicle_record

INGESTED_AT = datetime(2026, 5, 18, 8, 0, 0, tzinfo=timezone.utc)


def _feed_entry(**overrides):
    """Build a feed-shaped vehicle entry; override any field per-test."""
    base = {
        "id": "3635",
        "routeTag": "339",
        "dirTag": "339_0_MANW",
        "lat": "43.79428",
        "lon": "-79.23889",
        "speedKmHr": "37",
        "heading": "329",
        "secsSinceReport": "17",
    }
    base.update(overrides)
    return base


def test_parse_happy_path():
    rec = parse_vehicle_record(_feed_entry(), INGESTED_AT, "source.json")

    assert rec is not None
    assert rec["vehicle_id"] == "3635"
    assert rec["route_id"] == "339"
    assert rec["direction_tag"] == "339_0_MANW"
    assert rec["direction_id"] == 0
    assert rec["latitude"] == 43.79428
    assert rec["longitude"] == -79.23889
    assert rec["speed_kmh"] == 37.0
    assert rec["heading"] == 329.0
    assert rec["secs_since_report"] == 17
    assert rec["source_file"] == "source.json"


def test_recorded_at_is_ingested_at_minus_secs_since_report():
    rec = parse_vehicle_record(_feed_entry(secsSinceReport="60"), INGESTED_AT, "x")

    # Snowflake TIMESTAMP_NTZ expects naive datetimes; both fields should be naive.
    assert rec["_ingested_at"].tzinfo is None
    assert rec["recorded_at"].tzinfo is None
    assert (rec["_ingested_at"] - rec["recorded_at"]).total_seconds() == 60


def test_missing_vehicle_id_skips_record():
    entry = _feed_entry()
    del entry["id"]
    assert parse_vehicle_record(entry, INGESTED_AT, "x") is None


def test_missing_route_id_skips_record():
    entry = _feed_entry()
    del entry["routeTag"]
    assert parse_vehicle_record(entry, INGESTED_AT, "x") is None


def test_non_numeric_speed_does_not_crash():
    # Feed occasionally returns garbage strings; the record should still come
    # through with speed_kmh set to None rather than raising.
    rec = parse_vehicle_record(_feed_entry(speedKmHr="N/A"), INGESTED_AT, "x")
    assert rec is not None
    assert rec["speed_kmh"] is None


def test_parse_direction_id_variants():
    assert parse_direction_id("339_0_MANW") == 0
    assert parse_direction_id("510_1_510") == 1
    assert parse_direction_id("noDirSuffix") is None
    assert parse_direction_id(None) is None
    assert parse_direction_id("") is None
