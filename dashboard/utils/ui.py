"""Reusable UI primitives + global CSS for the TTC dashboard.

This file is the visual design system: every page calls inject_global_css()
once at the top, then uses these HTML-based helpers (page_header, kpi_row,
insight_box, section_label, html_table, sidebar_brand, footer) instead of
Streamlit's native st.metric/st.dataframe chrome.

Backend logic lives elsewhere — nothing in this file touches Snowflake, dbt,
Airflow, or any calculation.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# --- Design tokens -----------------------------------------------------
BG           = "#0B0F14"
CARD         = "#111827"
CARD_BORDER  = "#1F2937"
ACCENT       = "#DA291C"
ACCENT_DIM   = "#7F1D1D"
TEXT_1       = "#F9FAFB"
TEXT_2       = "#9CA3AF"
TEXT_3       = "#4B5563"
GREEN        = "#22C55E"
GREEN_DIM    = "#14532D"
AMBER        = "#F59E0B"

SIDEBAR_BG   = "#0D1117"
ROW_ALT      = "#0D1116"

PLOTLY_TEMPLATE = "plotly_dark"


# --- Global CSS ----------------------------------------------------------
def inject_global_css() -> None:
    """Inject the base theme. Call once at the top of every page."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
            background-color: {BG} !important;
        }}
        .stApp {{ background-color: {BG}; }}
        #MainMenu, footer, header {{ visibility: hidden; }}
        .block-container {{
            padding: 2rem 2.5rem !important;
            max-width: 1400px;
        }}

        /* Remove Streamlit widget chrome */
        [data-testid="stVerticalBlock"] > div {{ gap: 0; }}
        div[data-testid="metric-container"] {{ display: none; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: {SIDEBAR_BG} !important;
            border-right: 1px solid {CARD_BORDER};
        }}

        /* Selectbox */
        [data-testid="stSelectbox"] > div > div {{
            background: {CARD} !important;
            border: 1px solid {CARD_BORDER} !important;
            border-radius: 8px !important;
            color: {TEXT_1} !important;
        }}

        /* Slider */
        [data-testid="stSlider"] > div {{ padding: 0; }}
        .stSlider [data-baseweb="slider"] {{ padding-top: 1rem; }}

        /* Expander */
        [data-testid="stExpander"] {{
            background: {CARD} !important;
            border: 1px solid {CARD_BORDER} !important;
            border-radius: 8px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Sidebar brand ---------------------------------------------------------
def sidebar_brand() -> None:
    st.sidebar.markdown(
        f"""
        <div style="padding:1.25rem 1rem 1rem;border-bottom:1px solid {CARD_BORDER};margin-bottom:0.5rem">
            <div style="font-size:1rem;font-weight:700;color:{ACCENT};letter-spacing:-0.01em">
                TTC Analytics
            </div>
            <div style="font-size:0.72rem;color:#6B7280;margin-top:2px">Live Pipeline Dashboard</div>
            <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">
                <span style="font-size:0.6rem;color:{TEXT_3};background:{CARD};border:1px solid {CARD_BORDER};
                             border-radius:4px;padding:2px 6px;letter-spacing:0.06em">AIRFLOW</span>
                <span style="font-size:0.6rem;color:{TEXT_3};background:{CARD};border:1px solid {CARD_BORDER};
                             border-radius:4px;padding:2px 6px;letter-spacing:0.06em">DBT</span>
                <span style="font-size:0.6rem;color:{TEXT_3};background:{CARD};border:1px solid {CARD_BORDER};
                             border-radius:4px;padding:2px 6px;letter-spacing:0.06em">SNOWFLAKE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Page header -----------------------------------------------------------
def page_header(title: str, subtitle: str = "") -> None:
    sub_html = (
        f'<div style="font-size:0.9rem;color:{TEXT_2};margin-top:4px">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid {CARD_BORDER}">'
        f'<div style="font-size:1.75rem;font-weight:700;color:{ACCENT}">{title}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


# --- KPI row -----------------------------------------------------------
def kpi_row(cards: list[dict]) -> None:
    """cards = [{"label": str, "value": str, "sub": str, "accent": bool}]

    Renders a full-width responsive grid of KPI cards. `sub` may contain
    inline HTML (e.g. a colored <span>) for success/danger emphasis.

    Built as single-line HTML per card — a blank line inside a block passed
    to st.markdown(unsafe_allow_html=True) ends the raw-HTML block early and
    dumps everything after it onto the page as literal text.
    """
    cards_html = ""
    for c in cards:
        border = ACCENT if c.get("accent") else CARD_BORDER
        sub = (
            f'<div style="font-size:0.72rem;color:{TEXT_2};margin-top:4px">{c["sub"]}</div>'
            if c.get("sub") else ""
        )
        cards_html += (
            f'<div style="background:{CARD};border:1px solid {border};border-radius:10px;'
            f'padding:1.25rem 1.5rem;flex:1;min-width:0;">'
            f'<div style="font-size:0.7rem;font-weight:600;color:#6B7280;'
            f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">{c["label"]}</div>'
            f'<div style="font-size:1.75rem;font-weight:700;color:{TEXT_1};line-height:1.1">{c["value"]}</div>'
            f'{sub}</div>'
        )
    st.markdown(
        f'<div style="display:flex;gap:1rem;margin:1rem 0 1.5rem 0">{cards_html}</div>',
        unsafe_allow_html=True,
    )


# --- Insight callout ---------------------------------------------------
def insight_box(text: str) -> None:
    st.markdown(
        f"""
        <div style="background:{CARD};border-left:3px solid {ACCENT};border-radius:0 8px 8px 0;
                    padding:0.9rem 1.2rem;margin:1rem 0;font-size:0.875rem;color:{TEXT_1}">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Section label -------------------------------------------------------
def section_label(text: str) -> None:
    st.markdown(
        f"""
        <div style="font-size:0.7rem;font-weight:600;color:{TEXT_3};text-transform:uppercase;
                    letter-spacing:0.1em;margin:1.5rem 0 0.75rem 0;padding-bottom:0.5rem;
                    border-bottom:1px solid {CARD_BORDER}">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- HTML table --------------------------------------------------------
def html_table(df: pd.DataFrame, progress_col: str | None = None) -> None:
    """Render a DataFrame as a styled HTML table.

    Every column is rendered as-is (format values before calling this).
    `progress_col`, if given, must hold 0-100 floats and renders as an
    inline progress bar instead of plain text.
    """
    header_cells = "".join(
        f'<th style="text-align:left;padding:0.65rem 1rem;font-size:0.7rem;font-weight:600;'
        f'color:{TEXT_2};text-transform:uppercase;letter-spacing:0.06em;'
        f'border-bottom:1px solid {CARD_BORDER};white-space:nowrap">{col}</th>'
        for col in df.columns
    )

    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        row_bg = CARD if i % 2 == 0 else ROW_ALT
        cells = []
        for col in df.columns:
            val = row[col]
            if col == progress_col:
                pct = float(val)
                cell = f"""
                <div style="display:flex;align-items:center;gap:8px">
                    <div style="flex:1;background:{CARD_BORDER};border-radius:99px;height:4px">
                        <div style="width:{pct}%;background:{ACCENT};border-radius:99px;height:4px"></div>
                    </div>
                    <span style="font-size:0.8rem;color:{TEXT_1};white-space:nowrap">{pct:.1f}%</span>
                </div>
                """
            else:
                cell = f'<span style="font-size:0.85rem;color:{TEXT_1};white-space:nowrap">{val}</span>'
            cells.append(
                f'<td style="padding:0.65rem 1rem;border-bottom:1px solid {CARD_BORDER}">{cell}</td>'
            )
        rows.append(f'<tr style="background:{row_bg}">{"".join(cells)}</tr>')

    st.markdown(
        f"""
        <div style="overflow-x:auto;border:1px solid {CARD_BORDER};border-radius:10px">
            <table style="width:100%;border-collapse:collapse">
                <thead><tr style="background:{CARD_BORDER}">{header_cells}</tr></thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Misc ------------------------------------------------------------------
def format_relative(dt) -> str:
    """Render a naive-UTC datetime as 'X min ago' etc."""
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    secs = int(delta.total_seconds())
    if secs < 60:    return "just now"
    if secs < 3600:  return f"{secs // 60} min ago"
    if secs < 86400: return f"{secs // 3600} hr ago"
    return f"{secs // 86400} d ago"


def footer() -> None:
    st.markdown(
        f"""
        <hr style="margin-top: 2.5rem; border: none; border-top: 1px solid {CARD_BORDER};">
        <p style="color: {TEXT_3}; font-size: 0.82rem; margin-top: 0.85rem;">
            Unofficial analytics project · Not affiliated with TTC ·
            Built by Riyasat Zaman · Airflow + dbt + Snowflake + Streamlit ·
            <a href="https://github.com/riyasatzaman/ttc-transit-pipeline"
               style="color: {ACCENT}; text-decoration: none;">Source on GitHub</a>
        </p>
        """,
        unsafe_allow_html=True,
    )
