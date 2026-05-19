"""Snowflake connection helper for the Streamlit dashboard.

Reads credentials from `st.secrets["snowflake"]` when deployed to Streamlit
Cloud, or from .env / OS env vars when running locally. Both the connection
and the query results are cached so the dashboard stays snappy even when
multiple pages query the same mart.
"""
from __future__ import annotations

import decimal
import os
from pathlib import Path

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

# Load .env for local runs. No-op when running on Streamlit Cloud (no .env
# file present) — that path uses st.secrets instead.
load_dotenv()


def _secrets_file_exists() -> bool:
    """Check the two standard secrets.toml locations without touching st.secrets.

    Streamlit prints a noisy error banner the moment you access st.secrets
    if no secrets file is present, so we pre-check before touching it.
    """
    candidates = [
        Path.cwd() / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ]
    return any(p.exists() for p in candidates)


def _config_from_secrets() -> dict | None:
    """Read Snowflake creds from st.secrets (Streamlit Cloud)."""
    if not _secrets_file_exists():
        return None
    try:
        return dict(st.secrets["snowflake"])
    except Exception:
        return None


def _config_from_env() -> dict:
    """Fall back to env vars + .env for local development."""
    return {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "TTC_ANALYTICS"),
        "schema": "MARTS",
    }


@st.cache_resource(show_spinner=False)
def get_connection():
    """Open one Snowflake connection per Streamlit session and reuse it."""
    cfg = _config_from_secrets() or _config_from_env()
    return snowflake.connector.connect(**cfg)


def _coerce_decimals_to_float(df: pd.DataFrame) -> pd.DataFrame:
    """Convert decimal.Decimal columns to float in place.

    Snowflake's connector returns NUMBER columns as decimal.Decimal to
    preserve precision. That trips pandas quantile() and most numpy ops
    (TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and
    'float'). For dashboard analytics we want plain floats.
    """
    for col in df.columns:
        sample = df[col].dropna().head(1)
        if not sample.empty and isinstance(sample.iloc[0], decimal.Decimal):
            df[col] = df[col].astype(float)
    return df


@st.cache_data(ttl=300, show_spinner="Querying Snowflake...")
def query_df(sql: str) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Results cached for 5 minutes."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql)
        df = cur.fetch_pandas_all()
    return _coerce_decimals_to_float(df)
