"""Reusable UI primitives + global CSS for the TTC dashboard.

This file is the visual design system. Every page calls inject_global_css()
once at the top, then uses the helpers (hero, kpi_card, pill, insight_box,
arch_step, page_preview_card, footer) to keep the look consistent.

Backend logic lives elsewhere — nothing in this file touches Snowflake, dbt,
Airflow, or any calculation.
"""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

# --- Palette ---------------------------------------------------------------
TTC_RED          = "#DA291C"
TTC_RED_GLOW     = "rgba(218, 41, 28, 0.22)"
TTC_RED_TINT     = "rgba(218, 41, 28, 0.10)"
TTC_RED_BORDER   = "rgba(218, 41, 28, 0.42)"

BG               = "#080B10"
SIDEBAR_BG       = "#11151D"
CARD_BG          = "#141820"
ELEVATED_BG      = "#1A1F2B"
BORDER           = "#2A2F3A"

SUCCESS          = "#22C55E"
SUCCESS_BG       = "rgba(34, 197, 94, 0.10)"
SUCCESS_BORDER   = "rgba(34, 197, 94, 0.40)"

TEXT_PRIMARY     = "#F5F7FA"
TEXT_SECONDARY   = "#A7ADB7"
TEXT_MUTED       = "#737B88"

PLOTLY_TEMPLATE  = "plotly_dark"


# --- Global CSS ------------------------------------------------------------
def inject_global_css() -> None:
    """Inject the base theme. Call once at the top of every page."""
    st.markdown(
        f"""
        <style>
        :root {{
            --ttc-red:        {TTC_RED};
            --ttc-bg:         {BG};
            --ttc-sidebar:    {SIDEBAR_BG};
            --ttc-card:       {CARD_BG};
            --ttc-elevated:   {ELEVATED_BG};
            --ttc-border:     {BORDER};
            --ttc-text:       {TEXT_PRIMARY};
            --ttc-text-sec:   {TEXT_SECONDARY};
            --ttc-text-muted: {TEXT_MUTED};
            --ttc-success:    {SUCCESS};
        }}

        /* Page chrome */
        .stApp {{ background-color: var(--ttc-bg); color: var(--ttc-text); }}
        header[data-testid="stHeader"] {{ background: transparent; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: var(--ttc-sidebar);
            border-right: 1px solid var(--ttc-border);
        }}

        /* Main content width + top padding */
        .main .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }}

        /* Headings */
        h1, h2, h3, h4 {{
            color: var(--ttc-text);
            letter-spacing: -0.01em;
        }}
        h3 {{
            font-size: 1.15rem; font-weight: 600;
            margin-top: 1.75rem; margin-bottom: 0.75rem;
        }}

        /* Native st.metric -> card look (used as a fallback if any page
           still uses st.metric directly) */
        [data-testid="stMetric"] {{
            background-color: var(--ttc-card);
            border: 1px solid var(--ttc-border);
            border-radius: 14px;
            padding: 1rem 1.2rem;
        }}

        /* Plotly chart wrapper */
        div[data-testid="stPlotlyChart"] {{
            background-color: var(--ttc-card);
            border: 1px solid var(--ttc-border);
            border-radius: 14px;
            padding: 0.85rem 0.5rem 0.5rem 0.5rem;
            margin-top: 0.25rem;
        }}

        /* DataFrame */
        [data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid var(--ttc-border);
        }}

        /* Expanders */
        [data-testid="stExpander"] {{
            background-color: var(--ttc-card);
            border: 1px solid var(--ttc-border) !important;
            border-radius: 12px;
        }}

        /* Slider thumb -> TTC red */
        [data-baseweb="slider"] [role="slider"] {{
            background-color: var(--ttc-red) !important;
        }}

        /* Selectbox + caption text color tweaks */
        [data-testid="stCaptionContainer"], .stCaption {{
            color: var(--ttc-text-muted) !important;
        }}

        /* Hide Streamlit footer */
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Sidebar branding ------------------------------------------------------
def sidebar_branding() -> None:
    """Polished product-card branding block at the top of the sidebar."""
    st.sidebar.markdown(
        f"""
        <div style='
            background-color: {ELEVATED_BG};
            border: 1px solid {BORDER};
            border-left: 3px solid {TTC_RED};
            border-radius: 12px;
            padding: 0.85rem 0.95rem;
            margin: 0.25rem 0 1.1rem 0;
        '>
            <div style='color: {TTC_RED}; font-weight: 700; font-size: 1.05rem;
                        letter-spacing: -0.01em; line-height: 1.15;'>
                🚇 TTC Reliability Monitor
            </div>
            <div style='color: {TEXT_SECONDARY}; font-size: 0.86rem; margin-top: 0.2rem;'>
                Live transit insights
            </div>
            <div style='color: {TEXT_MUTED}; font-size: 0.74rem; margin-top: 0.55rem;
                        letter-spacing: 0.04em; text-transform: uppercase;'>
                Airflow · dbt · Snowflake
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Hero ------------------------------------------------------------------
def hero(title: str, subtitle: str, footnote: str = "") -> None:
    """Big rounded hero card for the landing page."""
    foot = (
        f"<div style='color: {TEXT_MUTED}; font-size: 0.92rem; margin-top: 0.95rem;"
        f"line-height: 1.5;'>{footnote}</div>"
        if footnote else ""
    )
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, {ELEVATED_BG} 0%, {CARD_BG} 100%);
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 1.85rem 2.1rem;
            margin: 0.25rem 0 1.5rem 0;
            position: relative;
            overflow: hidden;
        '>
            <div style='position: absolute; top: 0; left: 0; right: 0; height: 3px;
                        background: linear-gradient(90deg, {TTC_RED} 0%,
                        rgba(218,41,28,0) 70%);'></div>
            <div style='color: {TTC_RED}; font-size: 2.05rem; font-weight: 700;
                        letter-spacing: -0.025em; line-height: 1.1;'>
                {title}
            </div>
            <div style='color: {TEXT_SECONDARY}; font-size: 1.05rem; margin-top: 0.7rem;
                        line-height: 1.55; max-width: 820px;'>
                {subtitle}
            </div>
            {foot}
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Page header for sub-pages --------------------------------------------
def page_header(title: str, emoji: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div style='margin: 0.25rem 0 1.25rem 0;'>
            <div style='color: {TTC_RED}; font-size: 1.75rem; font-weight: 700;
                        letter-spacing: -0.02em; line-height: 1.15;'>
                {emoji} {title}
            </div>
            <div style='color: {TEXT_SECONDARY}; font-size: 1rem; margin-top: 0.45rem;
                        line-height: 1.55; max-width: 800px;'>
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- KPI cards -------------------------------------------------------------
def kpi_card(label: str, value: str, sub: str = "", sub_color: str = "muted") -> str:
    """Return HTML for one KPI card. Use inside `col.markdown(..., unsafe_allow_html=True)`.

    sub_color: 'muted' (default), 'success' (green), 'danger' (red).
    """
    color_map = {
        "muted":   TEXT_MUTED,
        "success": SUCCESS,
        "danger":  TTC_RED,
    }
    sub_clr = color_map.get(sub_color, TEXT_MUTED)
    sub_html = (
        f"<div style='color: {sub_clr}; font-size: 0.82rem; margin-top: 0.5rem;'>{sub}</div>"
        if sub else ""
    )
    return f"""
    <div style='
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 1rem 1.2rem;
        height: 100%;
        position: relative;
        overflow: hidden;
    '>
        <div style='position: absolute; top: 0; bottom: 0; left: 0; width: 3px;
                    background-color: {TTC_RED};'></div>
        <div style='color: {TEXT_SECONDARY}; font-size: 0.82rem; font-weight: 500;
                    letter-spacing: 0.01em;'>{label}</div>
        <div style='color: {TEXT_PRIMARY}; font-size: 1.55rem; font-weight: 700;
                    margin-top: 0.4rem; letter-spacing: -0.02em; line-height: 1.15;
                    word-break: break-word;'>{value}</div>
        {sub_html}
    </div>
    """


def kpi_card_custom(label: str, value_html: str) -> str:
    """Like kpi_card but lets you pass arbitrary HTML for the value area
    (e.g. a row of pill badges instead of a single number)."""
    return f"""
    <div style='
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 1rem 1.2rem;
        height: 100%;
        position: relative;
        overflow: hidden;
    '>
        <div style='position: absolute; top: 0; bottom: 0; left: 0; width: 3px;
                    background-color: {TTC_RED};'></div>
        <div style='color: {TEXT_SECONDARY}; font-size: 0.82rem; font-weight: 500;'>{label}</div>
        <div style='margin-top: 0.5rem;'>{value_html}</div>
    </div>
    """


# --- Pill badges -----------------------------------------------------------
def pill(text: str, variant: str = "default") -> str:
    """Single pill badge. Variants: 'default' (gray), 'success' (green dot), 'accent' (red)."""
    if variant == "success":
        bg, border, color = SUCCESS_BG, SUCCESS_BORDER, TEXT_PRIMARY
        dot = (f"<span style='display:inline-block;width:0.55rem;height:0.55rem;"
               f"border-radius:999px;background-color:{SUCCESS};margin-right:0.5rem;"
               f"vertical-align:middle;'></span>")
    elif variant == "accent":
        bg, border, color, dot = TTC_RED_TINT, TTC_RED_BORDER, TEXT_PRIMARY, ""
    else:
        bg, border, color, dot = ELEVATED_BG, BORDER, TEXT_SECONDARY, ""
    return (
        f"<span style='display:inline-block;padding:0.4rem 0.85rem;"
        f"margin:0.2rem 0.4rem 0.2rem 0;border-radius:999px;background-color:{bg};"
        f"border:1px solid {border};color:{color};font-size:0.88rem;"
        f"white-space:nowrap;line-height:1.3;font-weight:500;vertical-align:middle;'>"
        f"{dot}{text}</span>"
    )


def pill_row(pills_html: list[str]) -> None:
    st.markdown(
        f"<div style='margin: 0.1rem 0 1.5rem 0;'>{''.join(pills_html)}</div>",
        unsafe_allow_html=True,
    )


# --- Insight callout -------------------------------------------------------
def insight_box(html_text: str) -> None:
    """TTC-red bordered insight callout for at-a-glance summaries."""
    st.markdown(
        f"""
        <div style='
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-left: 3px solid {TTC_RED};
            border-radius: 12px;
            padding: 0.95rem 1.15rem;
            margin: 0.75rem 0 1.25rem 0;
            color: {TEXT_PRIMARY};
            line-height: 1.55;
            font-size: 0.95rem;
        '>{html_text}</div>
        """,
        unsafe_allow_html=True,
    )


# --- Page preview cards (homepage) -----------------------------------------
def page_preview_card(emoji: str, title: str, body: str) -> str:
    return f"""
    <div style='
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 1.2rem 1.3rem;
        height: 100%;
        min-height: 160px;
    '>
        <div style='color: {TEXT_PRIMARY}; font-weight: 600; font-size: 1.02rem;'>
            <span style='font-size: 1.15rem; margin-right: 0.25rem;'>{emoji}</span>{title}
        </div>
        <div style='color: {TEXT_SECONDARY}; font-size: 0.92rem; margin-top: 0.6rem;
                    line-height: 1.55;'>{body}</div>
    </div>
    """


# --- Architecture step + arrow --------------------------------------------
def arch_step(emoji: str, label: str, sub: str = "") -> str:
    sub_html = (
        f"<div style='color:{TEXT_MUTED};font-size:0.85rem;margin-top:0.3rem;"
        f"word-break:keep-all;overflow-wrap:normal;'>{sub}</div>"
        if sub else ""
    )
    return f"""
    <div style='background-color:{CARD_BG};border:1px solid {BORDER};
                border-left:3px solid {TTC_RED};border-radius:12px;
                padding:0.95rem 1.15rem;margin:0.4rem 0;'>
        <div style='color:{TEXT_PRIMARY};font-size:1rem;font-weight:600;
                    word-break:keep-all;overflow-wrap:normal;'>
            {emoji} {label}
        </div>{sub_html}</div>
    """


def arch_arrow(note: str = "") -> str:
    note_html = (
        f"<span style='color:{TEXT_MUTED};font-size:0.82rem;margin-left:0.55rem;'>{note}</span>"
        if note else ""
    )
    return (
        f"<div style='text-align:center;color:{TTC_RED};font-size:1.3rem;"
        f"line-height:1;margin:0.1rem 0;'>↓{note_html}</div>"
    )


# --- Horizontal flow (homepage pipeline) ----------------------------------
def horizontal_flow(steps: list[tuple[str, str, str]]) -> None:
    """Render a horizontal stack of card-steps separated by arrows.
    Each step is (emoji, label, sub)."""
    parts: list[str] = []
    for i, (emoji, label, sub) in enumerate(steps):
        parts.append(
            f"<div style='flex:1 1 0;min-width:120px;background-color:{CARD_BG};"
            f"border:1px solid {BORDER};border-radius:12px;padding:0.85rem 0.7rem;"
            f"text-align:center;'>"
            f"<div style='font-size:1.4rem;'>{emoji}</div>"
            f"<div style='color:{TEXT_PRIMARY};font-weight:600;font-size:0.9rem;"
            f"margin-top:0.3rem;'>{label}</div>"
            f"<div style='color:{TEXT_MUTED};font-size:0.74rem;margin-top:0.2rem;'>"
            f"{sub}</div></div>"
        )
        if i < len(steps) - 1:
            parts.append(
                f"<div style='color:{TTC_RED};font-size:1.25rem;align-self:center;"
                f"padding:0 0.15rem;flex:0 0 auto;'>→</div>"
            )
    st.markdown(
        f"<div style='display:flex;flex-wrap:wrap;gap:0.4rem;align-items:stretch;"
        f"margin:0.25rem 0 1.5rem 0;'>{''.join(parts)}</div>",
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
        <hr style='margin-top: 2.5rem; border: none; border-top: 1px solid {BORDER};'>
        <p style='color: {TEXT_MUTED}; font-size: 0.82rem; margin-top: 0.85rem;'>
            Unofficial analytics project · Not affiliated with TTC ·
            Built by Riyasat Zaman · Airflow + dbt + Snowflake + Streamlit ·
            <a href='https://github.com/riyasatzaman/ttc-transit-pipeline'
               style='color: {TTC_RED}; text-decoration: none;'>Source on GitHub</a>
        </p>
        """,
        unsafe_allow_html=True,
    )
