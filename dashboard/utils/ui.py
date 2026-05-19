"""Small reusable UI helpers so every page renders with a consistent look."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

# TTC's official streetcar/bus red. Re-used everywhere we want an accent.
TTC_RED = "#DA291C"
PLOTLY_TEMPLATE = "plotly_dark"


def page_header(title: str, emoji: str, subtitle: str) -> None:
    """Standard page header: small TTC-red title + 1-line subtitle."""
    st.markdown(
        f"<h1 style='color: {TTC_RED}; margin-bottom: 0;'>{emoji} {title}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color: #bbb; margin-top: 0.25rem;'>{subtitle}</p>",
        unsafe_allow_html=True,
    )


def format_relative(dt: datetime) -> str:
    """Render a datetime as 'X minutes ago' / 'X hours ago' for KPI tiles.

    Assumes `dt` is naive UTC (matches what our marts store).
    """
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60} min ago"
    if secs < 86400:
        return f"{secs // 3600} hr ago"
    return f"{secs // 86400} d ago"


def footer() -> None:
    """Tiny consistent footer for every page."""
    st.markdown(
        f"""
        <hr style='margin-top: 2rem; border: none; border-top: 1px solid #333;'>
        <p style='color: #666; font-size: 0.85rem;'>
            Unofficial analytics project · Not affiliated with TTC ·
            Built by Riyasat Zaman · Airflow + dbt + Snowflake + Streamlit ·
            <a href='https://github.com/riyasatzaman/ttc-transit-pipeline'
               style='color: {TTC_RED};'>Source on GitHub</a>
        </p>
        """,
        unsafe_allow_html=True,
    )
