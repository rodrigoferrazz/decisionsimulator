"""Reusable Streamlit UI sections for the AgroVision simulator."""

from __future__ import annotations

from datetime import datetime
from html import escape
from textwrap import dedent
from urllib.parse import quote

import pandas as pd
import plotly.express as px

import streamlit as st

from src.data.historical_indicators import (
    HOME_CONTEXT,
    QUICK_ACCESS_CARDS,
    get_at_a_glance,
    get_data_source_note,
    get_historical_insights,
    get_historical_insights_explanation,
)
from src.data.station_weather import load_station_weather_summary
from src.decision_engine import (
    DEFAULT_PAYOFF_MATRIX,
    DEFAULT_SCENARIO_PROBABILITIES,
    PayoffMatrix,
    ScenarioProbabilities,
    build_decision_summary,
)
from src.simulation_model import (
    DECISION_TREE_METHOD,
    PAYOFF_MATRIX_METHOD,
    build_decision_tree_simulation,
    build_payoff_matrix_simulation,
)
from src.weather_client import build_farm_weather_location, fetch_open_meteo_forecast


PRIMARY = "#2f5f3f"
PRIMARY_DARK = "#1f3f2d"
PRIMARY_SOFT = "#e8f2e8"
TEXT = "#263125"
MUTED = "#6f7468"
SURFACE = "#fffefa"
BACKGROUND = "#f5f3ea"
BORDER = "#e5e0d2"
CLAY = "#9b6a3f"


PAGE_NAMES = {
    "Home",
    "Start Simulation",
    "Historical Insights",
    "Recommendation Summary",
    "Compare Simulations",
}

SEED_TYPE_OPTIONS = ("soybean", "corn")
PLANTING_WINDOW_OPTIONS = ("Early", "Ideal", "Late")


def render_app_shell() -> None:
    """Render the application shell and route between prototype sections."""
    st.set_page_config(
        page_title="AgroVision Simulator",
        page_icon="AG",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_styles()

    query_page = st.query_params.get("page")
    if query_page in PAGE_NAMES:
        st.session_state["active_page"] = query_page
    if st.query_params.get("menu") == "closed":
        st.session_state["mobile_nav_open"] = False
        try:
            del st.query_params["menu"]
        except KeyError:
            pass

    _render_mobile_header()
    _render_mobile_drawer()
    _render_sidebar()

    page = st.session_state.get("active_page", "Home")

    if page == "Home":
        _render_home_page()
    elif page == "Start Simulation":
        _render_start_simulation_page()
    elif page == "Historical Insights":
        _render_historical_insights_page()
    elif page == "Recommendation Summary":
        _render_recommendation_page()
    elif page == "Compare Simulations":
        _render_compare_simulations_page()


def _inject_styles() -> None:
    """Apply lightweight styling inspired by the high-fidelity prototype."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
        :root {{
            --ag-bg: {BACKGROUND};
            --ag-surface: {SURFACE};
            --ag-ink: {TEXT};
            --ag-muted: {MUTED};
            --ag-line: {BORDER};
            --ag-leaf: {PRIMARY};
            --ag-leaf-dark: {PRIMARY_DARK};
            --ag-leaf-soft: {PRIMARY_SOFT};
            --ag-clay: {CLAY};
            --ag-serif: "Instrument Serif", Georgia, serif;
            --ag-ui: "Geist", -apple-system, BlinkMacSystemFont, sans-serif;
            --ag-mono: "JetBrains Mono", ui-monospace, Menlo, monospace;
        }}
        .stApp {{
            background: var(--ag-bg);
            color: var(--ag-ink);
            font-family: var(--ag-ui);
        }}
        .ag-mobile-nav-open,
        .ag-mobile-drawer-title,
        .ag-mobile-drawer,
        .ag-mobile-close-marker,
        .ag-mobile-header-marker,
        .ag-nav-active-marker,
        div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker),
        div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker) + div[data-testid="stElementContainer"],
        div[data-testid="stElementContainer"]:has(.ag-nav-active-marker),
        div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker),
        div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] {{
            background: var(--ag-surface);
            border-right: 1px solid var(--ag-line);
            transform: none !important;
            visibility: visible !important;
            height: 100dvh;
            overflow: hidden !important;
        }}
        section[data-testid="stSidebar"] > div,
        div[data-testid="stSidebarContent"] {{
            height: 100dvh;
            overflow: hidden !important;
        }}
        div[data-testid="stSidebarHeader"] {{
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
        }}
        section[data-testid="stSidebar"] * {{
            color: {TEXT};
        }}
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {{
            color: {TEXT} !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
            gap: 0.25rem;
        }}
        div[data-testid="stSidebarUserContent"] {{
            height: 100%;
            min-height: 0;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
            padding-top: 1.25rem;
            overflow: hidden !important;
        }}
        div[data-testid="stSidebarUserContent"] div[data-testid="stVerticalBlock"]:has(.ag-sidebar-footer) {{
            height: 100%;
            min-height: 0;
            display: flex;
            flex-direction: column;
        }}
        div[data-testid="stSidebarUserContent"] div[data-testid="stElementContainer"]:has(.ag-sidebar-footer) {{
            margin-top: auto !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
            width: 100%;
            justify-content: flex-start;
            background: transparent !important;
            border: 0 !important;
            color: var(--ag-ink) !important;
            box-shadow: none !important;
            padding: 0.62rem 0.75rem;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.9rem;
            text-align: left;
            min-height: 42px;
            gap: 0.65rem;
            position: relative;
            opacity: 1 !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
            background: #eef1e7 !important;
            color: var(--ag-leaf-dark) !important;
        }}
        div[data-testid="stElementContainer"]:has(.ag-nav-active-marker) + div[data-testid="stElementContainer"] button {{
            background: var(--ag-leaf-soft) !important;
            color: var(--ag-leaf-dark) !important;
            font-weight: 750 !important;
        }}
        div[data-testid="stElementContainer"]:has(.ag-nav-active-marker) + div[data-testid="stElementContainer"] button::before {{
            content: "";
            position: absolute;
            left: -1rem;
            top: 8px;
            bottom: 8px;
            width: 3px;
            border-radius: 0 3px 3px 0;
            background: var(--ag-leaf);
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button * {{
            color: inherit !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button p {{
            font-size: 0.9rem !important;
            font-weight: 650 !important;
            line-height: 1.15 !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button [data-testid="stIconMaterial"] {{
            width: 28px;
            height: 28px;
            display: inline-grid;
            place-items: center;
            flex-shrink: 0;
            border-radius: 7px;
            background: rgba(47, 95, 63, 0.08);
            color: var(--ag-leaf-dark) !important;
            font-size: 18px !important;
        }}
        div[data-testid="stSidebarCollapseButton"],
        div[data-testid="stSidebarCollapsedControl"],
        div[data-testid="collapsedControl"] {{
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }}
        .ag-nav {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 0;
            margin-bottom: 22px;
        }}
        .ag-nav-link {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            padding: 0.62rem 0.75rem;
            border-radius: 10px;
            color: var(--ag-ink) !important;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 0.9rem;
            position: relative;
            transition: background 0.15s, color 0.15s;
        }}
        .ag-nav-link:hover {{
            background: #eef1e7;
            color: var(--ag-leaf-dark) !important;
        }}
        .ag-nav-link--active {{
            background: var(--ag-leaf-soft);
            color: var(--ag-leaf-dark) !important;
            font-weight: 700;
        }}
        .ag-nav-link--active::before {{
            content: "";
            position: absolute;
            left: -1rem;
            top: 8px;
            bottom: 8px;
            width: 3px;
            border-radius: 0 3px 3px 0;
            background: var(--ag-leaf);
        }}
        .ag-nav-icon {{
            width: 28px;
            height: 28px;
            display: inline-grid;
            place-items: center;
            flex-shrink: 0;
            border-radius: 7px;
            background: rgba(47, 95, 63, 0.08);
            color: var(--ag-leaf-dark);
        }}
        .ag-nav-icon svg {{
            display: block;
            color: inherit;
        }}
        .ag-nav-label {{
            font-size: 0.9rem;
            color: inherit;
        }}
        .ag-compare-summary {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 1.25rem 0 1rem;
        }}
        .ag-compare-stat {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            min-width: 0;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-compare-stat-label {{
            color: var(--ag-leaf);
            font-size: 0.68rem;
            font-weight: 760;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }}
        .ag-compare-stat-value {{
            color: var(--ag-ink);
            font-size: clamp(1.35rem, 2vw, 2.1rem);
            line-height: 1.05;
            font-weight: 700;
            overflow-wrap: anywhere;
        }}
        .ag-compare-table-wrap {{
            overflow-x: auto;
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 12px;
            margin: 0.8rem 0 1.2rem;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-compare-table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 920px;
            font-size: 0.84rem;
        }}
        .ag-compare-table th {{
            color: var(--ag-muted);
            background: #f6f7f1;
            border-bottom: 1px solid var(--ag-line);
            padding: 0.78rem 0.85rem;
            text-align: left;
            font-weight: 750;
            white-space: nowrap;
        }}
        .ag-compare-table td {{
            color: var(--ag-ink);
            border-bottom: 1px solid #ece8dc;
            padding: 0.75rem 0.85rem;
            vertical-align: middle;
            white-space: nowrap;
        }}
        .ag-compare-table tr:last-child td {{
            border-bottom: 0;
        }}
        .ag-compare-table td[data-align="right"],
        .ag-compare-table th[data-align="right"] {{
            text-align: right;
            font-variant-numeric: tabular-nums;
        }}
        .ag-compare-pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.22rem 0.5rem;
            background: var(--ag-leaf-soft);
            color: var(--ag-leaf-dark);
            font-size: 0.74rem;
            font-weight: 750;
        }}
        .ag-compare-cards {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 1rem 0 1.2rem;
        }}
        .ag-compare-card {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            min-width: 0;
        }}
        .ag-compare-card-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.85rem;
        }}
        .ag-compare-card-title {{
            color: var(--ag-ink);
            font-weight: 800;
            font-size: 1rem;
        }}
        .ag-compare-card-sub {{
            color: var(--ag-muted);
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }}
        .ag-compare-card-value {{
            color: var(--ag-leaf-dark);
            font-weight: 800;
            font-size: 1.35rem;
            line-height: 1.1;
            white-space: nowrap;
        }}
        .ag-compare-card-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.55rem;
        }}
        .ag-compare-card-grid div {{
            background: #f7f8f2;
            border: 1px solid #e7e4d8;
            border-radius: 9px;
            padding: 0.58rem 0.65rem;
            min-width: 0;
        }}
        .ag-compare-card-grid span {{
            display: block;
            color: var(--ag-muted);
            font-size: 0.66rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.22rem;
        }}
        .ag-compare-card-grid strong {{
            display: block;
            color: var(--ag-ink);
            font-size: 0.86rem;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }}
        .ag-source-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 1rem 0 1.1rem;
        }}
        .ag-source-card {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 12px;
            padding: 1rem 1.05rem;
            min-width: 0;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-source-card-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.7rem;
        }}
        .ag-source-title {{
            color: var(--ag-ink);
            font-weight: 800;
            font-size: 0.98rem;
        }}
        .ag-source-badge {{
            border-radius: 999px;
            padding: 0.18rem 0.48rem;
            background: var(--ag-leaf-soft);
            color: var(--ag-leaf-dark);
            font-size: 0.68rem;
            font-weight: 800;
            white-space: nowrap;
        }}
        .ag-source-role {{
            color: var(--ag-muted);
            font-size: 0.8rem;
            line-height: 1.35;
            min-height: 2.2rem;
        }}
        .ag-source-metrics {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.45rem;
            margin-top: 0.85rem;
        }}
        .ag-source-metrics div {{
            background: #f7f8f2;
            border: 1px solid #e7e4d8;
            border-radius: 9px;
            padding: 0.5rem 0.55rem;
            min-width: 0;
        }}
        .ag-source-metrics span {{
            display: block;
            color: var(--ag-muted);
            font-size: 0.63rem;
            font-weight: 760;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.16rem;
        }}
        .ag-source-metrics strong {{
            color: var(--ag-ink);
            display: block;
            font-size: 0.82rem;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }}
        div[data-testid="stSlider"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stSlider"] label *,
        div[data-testid="stNumberInput"] label * {{
            color: var(--ag-ink) !important;
            font-weight: 600;
        }}
        .block-container {{
            padding-top: 1.8rem;
            max-width: 1180px;
        }}
        h1, h2, h3 {{
            color: var(--ag-ink);
        }}
        h1 {{
            font-family: var(--ag-serif);
            font-size: 3rem !important;
            line-height: 1.02 !important;
            font-weight: 400 !important;
            letter-spacing: -0.02em;
        }}
        h2 {{
            font-family: var(--ag-serif);
            font-size: 2rem !important;
            font-weight: 400 !important;
            letter-spacing: -0.01em;
        }}
        .ag-card {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 14px;
            padding: 1.35rem 1.45rem;
            min-height: 132px;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-history-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin: 1.45rem 0 2rem;
            max-width: 980px;
        }}
        .ag-history-card {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 14px;
            padding: 1.45rem 1.55rem;
            min-height: 240px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-history-card .ag-kicker {{
            margin-bottom: 0.35rem;
        }}
        .ag-history-card .ag-stat-value {{
            font-size: 2rem;
            margin-bottom: 0.55rem;
        }}
        .ag-history-card .ag-muted {{
            line-height: 1.55;
            margin: 0;
        }}
        .ag-info-card {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 14px;
            padding: 1.25rem 1.35rem;
            margin: 1rem 0 1.15rem;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-info-card h3 {{
            font-family: var(--ag-ui);
            font-size: 1.25rem !important;
            line-height: 1.2 !important;
            font-weight: 700 !important;
            letter-spacing: 0;
            color: var(--ag-ink);
            margin: 0.2rem 0 0.9rem;
        }}
        .ag-metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
        }}
        .ag-metric-grid--five {{
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }}
        .ag-metric-grid--six {{
            grid-template-columns: repeat(6, minmax(0, 1fr));
        }}
        .ag-metric-item {{
            background: #f7f8f2;
            border: 1px solid #e7e4d8;
            border-radius: 10px;
            padding: 0.8rem 0.85rem;
            min-width: 0;
        }}
        .ag-metric-label {{
            font-size: 0.66rem;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            color: var(--ag-leaf);
            font-weight: 750;
            margin-bottom: 0.35rem;
        }}
        .ag-metric-value {{
            color: var(--ag-ink);
            font-size: 0.94rem;
            line-height: 1.3;
            font-weight: 650;
            overflow-wrap: anywhere;
        }}
        .ag-weather-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.9rem;
            padding: 0.75rem 0.85rem;
            border-radius: 10px;
            background: #f3f5ee;
            color: var(--ag-muted);
            font-size: 0.9rem;
            line-height: 1.45;
        }}
        .ag-weather-strip > span {{
            display: inline-flex;
            gap: 0.25rem;
        }}
        .ag-weather-strip strong {{
            color: var(--ag-ink);
            font-weight: 650;
        }}
        .ag-card-dark {{
            background: linear-gradient(155deg, var(--ag-leaf), var(--ag-leaf-dark));
            color: #f3f8ef;
            border-radius: 14px;
            padding: 1.35rem 1.45rem;
            min-height: 168px;
            box-shadow: 0 10px 24px -18px rgba(31, 63, 45, 0.55);
        }}
        .ag-card-dark h3, .ag-card-dark p {{
            color: #f3f8ef;
        }}
        .ag-muted {{
            color: var(--ag-muted);
        }}
        .ag-hero {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 20px;
            padding: 1.7rem;
            min-height: 210px;
            box-shadow: 0 4px 16px -12px rgba(31, 63, 45, 0.18);
        }}
        .ag-recommendation {{
            background:
                radial-gradient(ellipse 90% 70% at 100% 0%, rgba(143, 184, 132, 0.45), transparent 60%),
                linear-gradient(160deg, #e8f2e8, #ddebdc);
            border-radius: 20px;
            padding: 1.7rem 1.9rem;
            border: 1px solid #c7dec5;
            box-shadow: 0 8px 24px -18px rgba(31, 63, 45, 0.38);
        }}
        header[data-testid="stHeader"] {{
            background: var(--ag-surface);
            border-bottom: 1px solid var(--ag-line);
        }}
        div[data-testid="stMetricValue"] {{
            color: {TEXT};
        }}
        div[data-baseweb="input"] {{
            background: var(--ag-surface) !important;
            border: 1px solid var(--ag-line);
            border-radius: 10px;
        }}
        div[data-baseweb="input"] input {{
            background: var(--ag-surface) !important;
            color: var(--ag-ink) !important;
            font-family: var(--ag-mono);
        }}
        div[data-testid="stButton"] button,
        button[kind="primary"] {{
            background: var(--ag-leaf) !important;
            border-color: var(--ag-leaf) !important;
            color: white !important;
            border-radius: 10px;
            font-weight: 600;
        }}
        div[data-testid="stButton"] button *,
        button[kind="primary"] *,
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stDownloadButton"] button * {{
            color: white !important;
        }}
        div[data-testid="stDownloadButton"] button {{
            background: var(--ag-leaf) !important;
            border-color: var(--ag-leaf) !important;
            border-radius: 10px;
        }}
        .ag-brand {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
            padding: 6px 0 14px;
            color: var(--ag-ink) !important;
            text-decoration: none !important;
            border-radius: 12px;
            text-align: center;
        }}
        section[data-testid="stSidebar"] hr {{
            margin: 0.45rem 0 2.2rem;
        }}
        .ag-logo {{
            width: 52px;
            height: 52px;
            border-radius: 14px;
            display: grid;
            place-items: center;
            background: linear-gradient(155deg, var(--ag-leaf), var(--ag-leaf-dark));
            flex-shrink: 0;
        }}
        .ag-brand-name {{
            font-family: var(--ag-serif);
            font-size: 27px;
            line-height: 1;
            color: var(--ag-ink);
        }}
        .ag-brand-tag {{
            font-size: 10px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--ag-muted);
            margin-top: 6px;
        }}
        .ag-sidebar-footer {{
            color: var(--ag-muted);
            font-size: 0.78rem;
            line-height: 1.5;
            padding-top: 1rem;
            margin-top: auto;
            border-top: 1px solid var(--ag-line);
        }}
        .ag-user {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 6px 10px 6px 6px;
            background: #eef5eb;
            color: var(--ag-ink);
            font-weight: 600;
            font-size: 13px;
        }}
        .ag-avatar {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #dcebd8;
            display: grid;
            place-items: center;
            color: var(--ag-leaf-dark);
            font-size: 12px;
            font-family: var(--ag-mono);
        }}
        .ag-kicker {{
            font-size: 11px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--ag-leaf);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        h1 em {{
            font-style: italic;
            color: var(--ag-leaf-dark);
        }}
        .ag-home-subtitle {{
            font-size: 1rem;
            color: var(--ag-muted);
            line-height: 1.65;
            max-width: 540px;
            margin: 1.1rem 0 0;
        }}
        .ag-status-row {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            margin-top: 1.5rem;
            padding-top: 1.2rem;
            border-top: 1px solid var(--ag-line);
        }}
        .ag-status-item {{
            font-size: 0.82rem;
            color: var(--ag-muted);
            line-height: 1.4;
        }}
        .ag-status-dot {{
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: var(--ag-muted);
            opacity: 0.4;
            margin: 0 12px;
            flex-shrink: 0;
            display: inline-block;
        }}
        .ag-stat-value {{
            font-family: var(--ag-serif);
            font-size: 2.2rem;
            line-height: 1;
            color: var(--ag-ink);
        }}
        .ag-gs-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 14px;
            margin: 10px 0 28px;
        }}
        .ag-gs-card {{
            border-radius: 20px;
            padding: 1.45rem 1.5rem;
            border: 1px solid var(--ag-line);
            text-decoration: none !important;
            display: flex;
            flex-direction: column;
            gap: 0;
            background: var(--ag-surface);
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
            transition: box-shadow 0.15s, transform 0.15s;
            cursor: pointer;
            min-height: 200px;
        }}
        .ag-gs-card:hover {{
            box-shadow: 0 6px 20px -10px rgba(31, 63, 45, 0.18);
            transform: translateY(-1px);
        }}
        .ag-gs-card--dark {{
            background: linear-gradient(155deg, #2f5f3f 0%, #1a3528 100%);
            border-color: transparent;
        }}
        .ag-gs-card--dark .ag-gs-title,
        .ag-gs-card--dark .ag-gs-body,
        .ag-gs-card--dark .ag-gs-arrow {{
            color: #f3f8ef !important;
        }}
        .ag-gs-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }}
        .ag-gs-icon {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.15);
            display: grid;
            place-items: center;
            color: #f3f8ef;
        }}
        .ag-gs-icon--light {{
            background: var(--ag-leaf-soft);
            color: var(--ag-leaf-dark);
        }}
        .ag-gs-arrow {{
            font-size: 18px;
            color: var(--ag-muted);
            line-height: 1;
        }}
        .ag-gs-title {{
            font-family: var(--ag-serif);
            font-size: 1.45rem;
            font-weight: 400;
            color: var(--ag-ink);
            margin: 0 0 0.4rem;
            line-height: 1.1;
        }}
        .ag-gs-body {{
            font-size: 0.87rem;
            color: var(--ag-muted);
            line-height: 1.5;
            margin: 0;
        }}
        .ag-glance-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 10px 0 24px;
        }}
        .ag-glance-card {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 16px;
            padding: 1.25rem 1.35rem;
            display: flex;
            align-items: flex-start;
            gap: 14px;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-glance-icon {{
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: var(--ag-leaf-soft);
            display: grid;
            place-items: center;
            color: var(--ag-leaf-dark);
            flex-shrink: 0;
            margin-top: 2px;
        }}
        .ag-glance-label {{
            font-size: 10px;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--ag-muted);
            margin-bottom: 4px;
        }}
        .ag-glance-value {{
            font-family: var(--ag-serif);
            font-size: 2rem;
            line-height: 1.05;
            color: var(--ag-ink);
        }}
        .ag-glance-unit {{
            font-family: var(--ag-ui);
            font-size: 13px;
            margin-left: 3px;
            color: var(--ag-ink);
            font-weight: 400;
        }}
        .ag-glance-sub {{
            font-size: 12.5px;
            color: var(--ag-muted);
            margin-top: 3px;
        }}
        .ag-section-label {{
            font-size: 11px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--ag-muted);
            margin: 2rem 0 0;
        }}
        .ag-source-note {{
            border-top: 1px solid var(--ag-line);
            margin-top: 1.1rem;
            padding-top: 0.85rem;
            color: var(--ag-muted);
            font-size: 0.82rem;
        }}
        .ag-section-band {{
            background: rgba(255, 254, 250, 0.7);
            border: 1px solid var(--ag-line);
            border-radius: 16px;
            padding: 1rem 1.1rem 0.45rem;
            margin-bottom: 1rem;
        }}
        .ag-start-title {{
            font-family: var(--ag-ui);
            font-size: 2.85rem;
            line-height: 1;
            font-weight: 700;
            color: #0f172a;
            margin: 0.55rem 0 1.55rem;
            letter-spacing: 0;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) {{
            background: #ffffff;
            border: 1px solid #dfe4ea;
            border-radius: 16px;
            padding: 1.55rem 2rem 1.35rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stVerticalBlock"] {{
            gap: 0.45rem;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stSelectbox"],
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stTextInput"],
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stSlider"] {{
            margin-bottom: 0.08rem;
        }}
        .ag-sim-card-marker {{
            display: none;
        }}
        .ag-form-caption {{
            color: #667085;
            text-align: center;
            font-size: 0.95rem;
            margin-top: 1.55rem;
        }}
        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stSlider"] label {{
            color: #344054 !important;
            font-size: 0.86rem !important;
            font-weight: 650 !important;
            padding-bottom: 0.08rem;
        }}
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stTextInput"] [data-baseweb="input"],
        div[data-testid="stNumberInput"] [data-baseweb="input"] {{
            min-height: 44px;
            border: 1px solid #d0d5dd !important;
            border-radius: 9px !important;
            background: #ffffff !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker)
        div[data-testid="stElementContainer"]:has(div[data-testid="stTextInput"] input:focus:not(:disabled)) {{
            background: transparent;
            border-left: 0;
            border-radius: 0;
            padding: 0;
            margin: 0;
            box-shadow: none;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker)
        div[data-testid="stTextInput"]:focus-within:not(:has(input:disabled)) label {{
            color: var(--ag-leaf-dark) !important;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker)
        div[data-testid="stTextInput"]:focus-within:not(:has(input:disabled)) [data-baseweb="input"] {{
            border: 3px solid var(--ag-leaf) !important;
            background: #ffffff !important;
            box-shadow: 0 2px 8px rgba(31, 63, 45, 0.08) !important;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker)
        div[data-testid="stTextInput"]:focus-within:not(:has(input:disabled)) input {{
            background: #ffffff !important;
            caret-color: var(--ag-leaf) !important;
        }}
        div[data-testid="stSelectbox"] [data-baseweb="select"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stSelectbox"] [data-baseweb="select"] * {{
            cursor: pointer !important;
        }}
        div[data-testid="stTextInput"] [data-baseweb="input"],
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] [data-baseweb="input"],
        div[data-testid="stNumberInput"] input {{
            cursor: text !important;
        }}
        div[data-testid="stSelectbox"] [data-baseweb="select"] * {{
            color: #667085 !important;
        }}
        div[data-testid="stSelectbox"] [data-baseweb="select"] svg {{
            color: #475467 !important;
        }}
        div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input {{
            font-size: 1rem !important;
        }}
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input {{
            color: #101828 !important;
        }}
        div[data-testid="stTextInput"] input::placeholder {{
            color: #667085 !important;
            opacity: 1 !important;
        }}
        div[data-testid="stTextInput"] input:disabled {{
            background: #f2f4f7 !important;
            color: #667085 !important;
            -webkit-text-fill-color: #667085 !important;
            cursor: not-allowed !important;
        }}
        div[data-testid="stSlider"] [data-testid="stTickBar"] {{
            color: #667085 !important;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stElementContainer"]:has(.ag-run-button-wrap) + div[data-testid="stElementContainer"] {{
            width: 100% !important;
            max-width: 100% !important;
            margin-top: 0.8rem;
            margin-left: 0 !important;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stElementContainer"]:has(.ag-run-button-wrap) + div[data-testid="stElementContainer"] div[data-testid="stButton"],
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stElementContainer"]:has(.ag-run-button-wrap) + div[data-testid="stElementContainer"] button {{
            width: 100% !important;
            max-width: 100% !important;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) div[data-testid="stElementContainer"]:has(.ag-run-button-wrap) + div[data-testid="stElementContainer"] button {{
            min-height: 44px;
            background: var(--ag-leaf) !important;
            border-color: var(--ag-leaf) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-size: 0.9rem !important;
            font-weight: 650 !important;
            padding: 0.55rem 1.05rem !important;
            margin-top: 0;
        }}
        .ag-pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.25rem 0.55rem;
            background: var(--ag-leaf-soft);
            color: var(--ag-leaf-dark);
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .ag-risk-row {{
            display: grid;
            grid-template-columns: minmax(130px, 1fr) 170px 70px;
            gap: 12px;
            align-items: center;
            margin: 0.55rem 0;
            color: var(--ag-ink);
            font-size: 0.9rem;
        }}
        .ag-bar {{
            height: 10px;
            background: #e7e3d8;
            border-radius: 999px;
            overflow: hidden;
        }}
        .ag-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--ag-leaf), #7fa36b);
            border-radius: 999px;
        }}
        .ag-page-head {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        div[data-testid="stVerticalBlock"]:has(.ag-header-action-marker)
        div[data-testid="stButton"] {{
            margin-top: 2.35rem;
        }}
        .ag-page-head h1 {{
            margin-bottom: 0.2rem;
        }}
        .ag-consensus {{
            position: relative;
            background:
                radial-gradient(ellipse 80% 100% at 100% 100%, rgba(167, 204, 151, 0.44), transparent 60%),
                linear-gradient(155deg, var(--ag-leaf), var(--ag-leaf-dark));
            color: #f3f8ef;
            border-radius: 20px;
            padding: 1.9rem 2.1rem;
            display: grid;
            grid-template-columns: 1fr 170px;
            gap: 1.5rem;
            align-items: stretch;
            overflow: hidden;
            box-shadow: 0 14px 36px -18px rgba(31, 63, 45, 0.48);
            margin-bottom: 1.35rem;
        }}
        .ag-consensus::before {{
            content: "";
            position: absolute;
            inset: 0;
            background-image:
                repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px),
                repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 64px);
            pointer-events: none;
            mask-image: radial-gradient(ellipse 110% 100% at 0% 0%, black, transparent 70%);
        }}
        .ag-consensus-left,
        .ag-consensus-right {{
            position: relative;
        }}
        .ag-consensus-eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #e7f4df;
            font-weight: 700;
            padding: 0.35rem 0.7rem;
            background: rgba(255,255,255,0.10);
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.13);
        }}
        .ag-consensus-title {{
            font-family: var(--ag-serif);
            font-size: 2.65rem;
            line-height: 1.04;
            color: #f3f8ef;
            margin: 0.8rem 0 0.65rem;
            font-weight: 400;
        }}
        .ag-consensus-title em {{
            color: #dff0d4;
            font-style: italic;
        }}
        .ag-consensus-sub {{
            color: #dbeada;
            font-size: 0.95rem;
            line-height: 1.55;
            max-width: 68ch;
            margin: 0;
        }}
        .ag-consensus-meta {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            border-top: 1px solid rgba(255,255,255,0.12);
            margin-top: 1.1rem;
            padding-top: 1rem;
        }}
        .ag-consensus-meta-label {{
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #b9d8b7;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}
        .ag-consensus-meta-value {{
            color: #f3f8ef;
            font-size: 0.92rem;
            font-weight: 600;
        }}
        .ag-consensus-right {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
        }}
        .ag-consensus-crest {{
            width: 104px;
            height: 104px;
            border-radius: 999px;
            background: radial-gradient(circle at 30% 30%, #eef8e8, #b6d6a9);
            color: var(--ag-leaf-dark);
            display: grid;
            place-items: center;
            font-size: 2.2rem;
            box-shadow:
                0 0 0 8px rgba(255,255,255,0.06),
                0 0 0 18px rgba(255,255,255,0.04),
                0 10px 30px -10px rgba(14, 45, 26, 0.55);
        }}
        .ag-consensus-chip {{
            font-size: 0.65rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #f3f8ef;
            background: rgba(255,255,255,0.11);
            border: 1px solid rgba(255,255,255,0.16);
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            font-weight: 700;
        }}
        .ag-criteria-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1.2rem;
            margin-bottom: 1.25rem;
        }}
        .ag-criterion {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 14px;
            padding: 1.45rem;
            box-shadow: 0 1px 2px rgba(31, 63, 45, 0.04);
        }}
        .ag-criterion-head {{
            display: grid;
            grid-template-columns: 48px 1fr;
            gap: 0.9rem;
            align-items: flex-start;
            margin-bottom: 1rem;
        }}
        .ag-criterion-badge {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--ag-leaf-soft);
            border: 1px solid #cfe3ca;
            color: var(--ag-leaf-dark);
            display: grid;
            place-items: center;
            font-family: var(--ag-serif);
            font-size: 1.35rem;
            font-style: italic;
        }}
        .ag-criterion-title {{
            font-family: var(--ag-serif);
            font-size: 1.65rem;
            line-height: 1.1;
            color: var(--ag-ink);
            margin-bottom: 0.25rem;
        }}
        .ag-criterion-sub {{
            color: var(--ag-muted);
            font-size: 0.84rem;
            line-height: 1.5;
        }}
        .ag-criterion-pick {{
            background: var(--ag-leaf-soft);
            border: 1px solid #cfe3ca;
            border-radius: 10px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.95rem;
        }}
        .ag-criterion-eyebrow {{
            font-size: 0.66rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--ag-leaf);
            font-weight: 800;
        }}
        .ag-criterion-alt {{
            display: flex;
            align-items: baseline;
            gap: 0.75rem;
            margin-top: 0.35rem;
        }}
        .ag-criterion-alt-id {{
            font-family: var(--ag-mono);
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--ag-leaf);
            background: var(--ag-surface);
            border: 1px solid #bfd9bb;
            padding: 0.12rem 0.5rem;
            border-radius: 6px;
        }}
        .ag-criterion-alt-name {{
            font-family: var(--ag-serif);
            font-size: 1.85rem;
            line-height: 1;
            color: var(--ag-ink);
        }}
        .ag-criterion-metric {{
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-top: 0.55rem;
        }}
        .ag-criterion-metric-val {{
            font-family: var(--ag-mono);
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--ag-leaf-dark);
        }}
        .ag-criterion-metric-unit {{
            color: var(--ag-muted);
            font-size: 0.78rem;
        }}
        .ag-criterion-formula {{
            font-family: var(--ag-mono);
            color: var(--ag-muted);
            border-top: 1px dashed #bfd9bb;
            padding-top: 0.55rem;
            margin-top: 0.55rem;
            font-size: 0.72rem;
        }}
        .ag-criterion details {{
            border: 1px solid var(--ag-line);
            border-radius: 10px;
            background: #fffefa;
            overflow: hidden;
        }}
        .ag-criterion summary {{
            cursor: pointer;
            padding: 0.75rem 0.9rem;
            font-weight: 700;
            color: var(--ag-ink);
            list-style: none;
        }}
        .ag-criterion summary::-webkit-details-marker {{
            display: none;
        }}
        .ag-criterion-toggle {{
            border: 1px solid var(--ag-line);
            border-radius: 10px 10px 0 0;
            background: #fffefa;
            padding: 0.75rem 0.9rem;
            font-weight: 700;
            color: var(--ag-ink);
            font-size: 0.86rem;
        }}
        .ag-criterion-detail {{
            padding: 0 0.9rem 0.9rem;
            border: 1px solid var(--ag-line);
            border-top: 0;
            border-radius: 0 0 10px 10px;
            background: #fffefa;
        }}
        .ag-dmatrix {{
            display: flex;
            flex-direction: column;
            border: 1px solid var(--ag-line);
            border-radius: 10px;
            overflow: hidden;
            background: var(--ag-surface);
        }}
        .ag-dmatrix-row,
        .ag-dmatrix-head {{
            display: grid;
            grid-template-columns: 1.45fr 1fr 1fr 1fr 1fr;
            align-items: stretch;
        }}
        .ag-dmatrix-head {{
            background: #f1eee4;
        }}
        .ag-dmatrix-cell {{
            padding: 0.62rem 0.65rem;
            border-right: 1px solid var(--ag-line);
            border-bottom: 1px solid var(--ag-line);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.78rem;
            color: var(--ag-ink);
        }}
        .ag-dmatrix-cell:last-child {{
            border-right: 0;
        }}
        .ag-dmatrix-row:last-child .ag-dmatrix-cell {{
            border-bottom: 0;
        }}
        .ag-dmatrix-label {{
            justify-content: flex-start;
            gap: 0.45rem;
            font-family: var(--ag-ui);
        }}
        .ag-dmatrix-alt-id {{
            font-family: var(--ag-mono);
            font-size: 0.68rem;
            color: var(--ag-muted);
            background: #f1eee4;
            padding: 0.08rem 0.36rem;
            border-radius: 4px;
            font-weight: 700;
        }}
        .ag-dmatrix-head .ag-dmatrix-cell {{
            font-weight: 800;
            font-size: 0.68rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--ag-muted);
        }}
        .ag-dmatrix-result {{
            background: rgba(232, 242, 232, 0.65);
            color: var(--ag-leaf-dark);
            font-family: var(--ag-mono);
            font-weight: 800;
        }}
        .ag-dmatrix-win {{
            background: rgba(232, 242, 232, 0.8);
        }}
        .ag-dmatrix-win .ag-dmatrix-alt-id {{
            background: var(--ag-leaf);
            color: #f3f8ef;
        }}
        .ag-dmatrix-min {{
            color: var(--ag-clay);
            font-weight: 800;
        }}
        .ag-criterion-note {{
            margin-top: 0.75rem;
            padding: 0.75rem 0.85rem;
            background: #f3f1e8;
            border-left: 2px solid var(--ag-leaf);
            border-radius: 8px;
            color: var(--ag-muted);
            font-size: 0.78rem;
            line-height: 1.5;
        }}
        .ag-savebar {{
            background: var(--ag-surface);
            border: 1px solid var(--ag-line);
            border-radius: 14px;
            padding: 1.2rem 1.3rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.1rem;
            margin-top: 1.2rem;
        }}
        .ag-savebar-source {{
            color: var(--ag-muted);
            font-size: 0.78rem;
            margin-top: 0.35rem;
            line-height: 1.5;
        }}
        .ag-save-toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 100000;
            width: min(360px, calc(100vw - 32px));
            background: var(--ag-surface);
            border: 1px solid rgba(47, 95, 63, 0.16);
            border-radius: 14px;
            box-shadow:
                0 20px 46px -24px rgba(31, 63, 45, 0.65),
                0 1px 0 rgba(255, 255, 255, 0.85) inset;
            padding: 0.9rem 1rem;
            color: var(--ag-ink);
            display: grid;
            grid-template-columns: 38px 1fr;
            gap: 0.8rem;
            align-items: center;
            animation:
                ag-save-toast-in 220ms ease-out,
                ag-save-toast-out 420ms ease-in 4.1s forwards;
            pointer-events: none;
        }}
        .ag-save-toast-icon {{
            width: 38px;
            height: 38px;
            border-radius: 999px;
            background: var(--ag-leaf-soft);
            border: 1px solid rgba(47, 95, 63, 0.18);
            color: var(--ag-leaf-dark);
            display: grid;
            place-items: center;
            font-size: 1rem;
            font-weight: 800;
        }}
        .ag-save-toast-label {{
            color: var(--ag-muted);
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            line-height: 1.1;
            margin-bottom: 0.22rem;
            text-transform: uppercase;
        }}
        .ag-save-toast-title {{
            color: var(--ag-ink);
            font-size: 0.98rem;
            font-weight: 780;
            line-height: 1.3;
        }}
        .ag-save-toast-body {{
            color: var(--ag-muted);
            font-size: 0.82rem;
            line-height: 1.45;
            margin-top: 0.2rem;
        }}
        .ag-save-toast-body strong {{
            color: var(--ag-leaf-dark);
            font-weight: 760;
        }}
        @keyframes ag-save-toast-in {{
            from {{
                opacity: 0;
                transform: translate(18px, 10px);
            }}
            to {{
                opacity: 1;
                transform: translate(0, 0);
            }}
        }}
        @keyframes ag-save-toast-out {{
            to {{
                opacity: 0;
                transform: translate(18px, 10px);
            }}
        }}
        @media (max-width: 1100px) {{
            .ag-consensus,
            .ag-criteria-grid {{
                grid-template-columns: 1fr;
            }}
            .ag-consensus-right {{
                flex-direction: row;
                justify-content: flex-start;
            }}
            .ag-consensus-meta {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .ag-glance-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .ag-history-grid {{
                max-width: none;
            }}
            .ag-metric-grid,
            .ag-metric-grid--five,
            .ag-metric-grid--six {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .ag-compare-summary,
            .ag-compare-cards,
            .ag-source-grid {{
                grid-template-columns: 1fr;
            }}
            .ag-compare-card-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .ag-save-toast {{
                bottom: 16px;
                right: 16px;
                left: 16px;
                width: auto;
            }}
        }}
        @media (max-width: 700px) {{
            .block-container {{
                padding: 0.75rem 0.9rem 2rem;
                max-width: 100%;
            }}
            .ag-mobile-nav-open {{
                display: block !important;
                position: fixed;
                inset: 0;
                z-index: 99980;
                background: rgba(15, 23, 42, 0.34);
                backdrop-filter: blur(2px);
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) {{
                display: block !important;
                height: 0;
                margin: 0;
                padding: 0;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] {{
                display: flex !important;
                flex-direction: row !important;
                align-items: center;
                gap: 0.75rem;
                position: sticky;
                top: 0;
                z-index: 100000;
                margin: -0.75rem -0.9rem 1rem;
                padding: 0.65rem 0.9rem;
                background: rgba(255, 254, 250, 0.96);
                border-bottom: 1px solid var(--ag-line);
                backdrop-filter: blur(12px);
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] > div:first-child {{
                width: auto !important;
                flex: 0 0 auto !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] > div:last-child {{
                display: none !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] {{
                width: auto !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {{
                width: 44px !important;
                min-width: 44px !important;
                height: 44px !important;
                min-height: 44px !important;
                padding: 0 !important;
                border-radius: 12px !important;
                display: inline-flex;
                justify-content: center;
                align-items: center;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button p {{
                display: none;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-header-marker) + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button [data-testid="stIconMaterial"] {{
                margin: 0 !important;
                font-size: 22px !important;
            }}
            .ag-mobile-brand {{
                display: none !important;
            }}
            .ag-mobile-logo {{
                width: 40px;
                height: 40px;
                border-radius: 11px;
                display: grid;
                place-items: center;
                flex-shrink: 0;
                background: linear-gradient(155deg, var(--ag-leaf), var(--ag-leaf-dark));
            }}
            .ag-mobile-brand-name {{
                font-family: var(--ag-serif);
                font-size: 1.55rem;
                line-height: 1;
                color: var(--ag-ink);
            }}
            .ag-mobile-brand-tag {{
                font-size: 0.58rem;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: var(--ag-muted);
                margin-top: 0.18rem;
                white-space: nowrap;
            }}
            section[data-testid="stSidebar"] {{
                display: none !important;
            }}
            .ag-mobile-drawer {{
                display: flex !important;
                position: fixed;
                inset: 0 auto 0 0;
                z-index: 100010;
                width: 80vw;
                max-width: 360px;
                min-width: 280px;
                height: 100dvh;
                box-sizing: border-box;
                padding: 2rem 0.9rem 1rem;
                flex-direction: column;
                background: #fffefa;
                border-right: 1px solid var(--ag-line);
                border-radius: 0 22px 22px 0;
                box-shadow: 22px 0 54px -30px rgba(15, 23, 42, 0.72);
                animation: ag-mobile-drawer-in 180ms ease-out;
            }}
            @keyframes ag-mobile-drawer-in {{
                from {{
                    transform: translateX(-100%);
                }}
                to {{
                    transform: translateX(0);
                }}
            }}
            .ag-mobile-profile {{
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                gap: 0.68rem;
                padding: 0.15rem 0.2rem 1.65rem;
            }}
            .ag-mobile-profile-logo {{
                width: 58px;
                height: 58px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                background: linear-gradient(155deg, var(--ag-leaf), var(--ag-leaf-dark));
                box-shadow: 0 8px 18px -12px rgba(31, 63, 45, 0.65);
            }}
            .ag-mobile-profile-name {{
                color: var(--ag-ink);
                font-size: 1.22rem;
                line-height: 1;
                font-weight: 800;
            }}
            .ag-mobile-profile-sub {{
                color: var(--ag-muted);
                font-size: 0.72rem;
                margin-top: 0.2rem;
            }}
            .ag-mobile-drawer-nav {{
                display: flex;
                flex-direction: column;
                gap: 0.3rem;
            }}
            .ag-mobile-drawer-link {{
                display: flex;
                align-items: center;
                gap: 0.6rem;
                min-height: 42px;
                padding: 0.48rem 0.5rem;
                border-radius: 10px;
                color: var(--ag-ink) !important;
                text-decoration: none !important;
                font-size: 0.86rem;
                font-weight: 700;
            }}
            .ag-mobile-drawer-link:hover,
            .ag-mobile-drawer-link--active {{
                background: var(--ag-leaf-soft);
                color: var(--ag-leaf-dark) !important;
            }}
            .ag-mobile-drawer-link svg {{
                width: 18px;
                height: 18px;
                color: currentColor;
                flex-shrink: 0;
            }}
            .ag-mobile-drawer-close {{
                margin-top: auto;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 42px;
                border-radius: 999px;
                background: #f2f1ef;
                color: var(--ag-ink) !important;
                text-decoration: none !important;
                font-size: 0.78rem;
                font-weight: 800;
            }}
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebarContent"],
            div[data-testid="stSidebarUserContent"],
            div[data-testid="stSidebarUserContent"] div[data-testid="stVerticalBlock"]:has(.ag-sidebar-footer) {{
                height: 100%;
                min-height: 0;
                overflow-y: auto !important;
            }}
            div[data-testid="stSidebarUserContent"] {{
                padding: 2rem 0.9rem 1rem;
            }}
            section[data-testid="stSidebar"] .ag-brand {{
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items: flex-start;
                gap: 0.65rem;
                text-align: left;
                padding: 0.2rem 0.15rem 1.35rem;
            }}
            section[data-testid="stSidebar"] .ag-logo {{
                width: 56px;
                height: 56px;
                border-radius: 50%;
                box-shadow: 0 8px 18px -12px rgba(31, 63, 45, 0.65);
            }}
            section[data-testid="stSidebar"] .ag-brand-name {{
                font-family: var(--ag-ui);
                font-size: 1.28rem;
                font-weight: 800;
            }}
            section[data-testid="stSidebar"] .ag-brand-tag {{
                font-size: 0.72rem;
                letter-spacing: 0;
                text-transform: none;
                margin-top: 0.15rem;
            }}
            .ag-mobile-drawer-title {{
                display: block !important;
                color: var(--ag-muted);
                font-size: 0.68rem;
                font-weight: 800;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                padding: 0.15rem 0.25rem 0.8rem;
            }}
            .ag-sidebar-footer {{
                display: none;
            }}
            section[data-testid="stSidebar"] hr {{
                display: none;
            }}
            .ag-nav {{
                gap: 0.35rem;
                margin: 0;
            }}
            section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
                min-height: 44px;
                padding: 0.55rem 0.45rem;
                border: 1px solid transparent !important;
                border-radius: 9px;
                font-size: 0.86rem;
                margin-bottom: 0.15rem;
                gap: 0.5rem;
            }}
            section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
                border-color: #dbe7d7 !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-nav-active-marker) + div[data-testid="stElementContainer"] button {{
                border-color: #cfe3ca !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-nav-active-marker) + div[data-testid="stElementContainer"] button::before {{
                display: none;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker) {{
                display: block !important;
                margin-top: auto !important;
                padding-top: 2rem;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker) + div[data-testid="stElementContainer"] {{
                display: block !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker) + div[data-testid="stElementContainer"] button {{
                justify-content: center !important;
                min-height: 42px;
                border-radius: 999px !important;
                background: #f2f1ef !important;
                color: var(--ag-ink) !important;
                font-size: 0.78rem;
                font-weight: 700;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker) + div[data-testid="stElementContainer"] button:hover {{
                background: #e8e6e1 !important;
            }}
            div[data-testid="stElementContainer"]:has(.ag-mobile-close-marker) + div[data-testid="stElementContainer"] button::before {{
                display: none;
            }}
            section[data-testid="stSidebar"] div[data-testid="stButton"] button:disabled::before {{
                left: 0.2rem;
                top: 10px;
                bottom: 10px;
                width: 4px;
                border-radius: 0 4px 4px 0;
            }}
            section[data-testid="stSidebar"] div[data-testid="stButton"] button [data-testid="stIconMaterial"],
            .ag-nav-icon {{
                width: 30px;
                height: 30px;
                border-radius: 8px;
            }}
            h1 {{
                font-size: 2.25rem !important;
                line-height: 1.08 !important;
            }}
            h2 {{
                font-size: 1.65rem !important;
            }}
            .ag-start-title {{
                font-size: 2rem;
                margin: 0.35rem 0 1rem;
            }}
            .ag-gs-grid,
            .ag-glance-grid,
            .ag-history-grid,
            .ag-source-grid,
            .ag-compare-summary,
            .ag-compare-cards,
            .ag-metric-grid,
            .ag-metric-grid--five,
            .ag-metric-grid--six,
            .ag-consensus-meta,
            .ag-compare-card-grid,
            .ag-source-metrics {{
                grid-template-columns: 1fr;
            }}
            div[data-testid="stHorizontalBlock"] {{
                flex-direction: column;
            }}
            div[data-testid="stHorizontalBlock"] > div {{
                width: 100% !important;
                flex: 1 1 100% !important;
            }}
            .ag-card,
            .ag-info-card,
            .ag-history-card,
            .ag-source-card,
            .ag-compare-card,
            .ag-criterion,
            div[data-testid="stVerticalBlock"]:has(.ag-sim-card-marker) {{
                border-radius: 12px;
                padding: 1rem;
                min-height: 0;
            }}
            .ag-gs-card {{
                border-radius: 14px;
                min-height: 0;
                padding: 1.05rem;
            }}
            .ag-glance-card {{
                border-radius: 12px;
                padding: 1rem;
            }}
            .ag-page-head,
            .ag-compare-card-head,
            .ag-source-card-head,
            .ag-savebar {{
                flex-direction: column;
                align-items: stretch;
            }}
            div[data-testid="stVerticalBlock"]:has(.ag-header-action-marker)
            div[data-testid="stButton"] {{
                margin-top: 0;
            }}
            .ag-consensus {{
                border-radius: 14px;
                padding: 1.15rem;
                gap: 1rem;
            }}
            .ag-consensus-title {{
                font-size: 2rem;
                overflow-wrap: anywhere;
            }}
            .ag-consensus-right {{
                display: none;
            }}
            .ag-weather-strip {{
                display: grid;
                grid-template-columns: 1fr;
                font-size: 0.84rem;
            }}
            .ag-weather-strip > span {{
                display: block;
            }}
            .ag-criterion-head {{
                grid-template-columns: 38px 1fr;
                gap: 0.7rem;
            }}
            .ag-criterion-badge {{
                width: 38px;
                height: 38px;
                border-radius: 10px;
                font-size: 1.1rem;
            }}
            .ag-criterion-title {{
                font-size: 1.35rem;
            }}
            .ag-criterion-alt,
            .ag-criterion-metric {{
                align-items: flex-start;
                flex-direction: column;
                gap: 0.35rem;
            }}
            .ag-criterion-alt-name {{
                font-size: 1.45rem;
            }}
            .ag-criterion-formula,
            .ag-dmatrix {{
                overflow-x: auto;
            }}
            .ag-dmatrix-row,
            .ag-dmatrix-head {{
                min-width: 620px;
            }}
            .ag-compare-table {{
                min-width: 760px;
            }}
            .ag-risk-row {{
                grid-template-columns: 1fr;
                gap: 0.45rem;
            }}
            .ag-bar {{
                width: 100%;
            }}
            .ag-form-caption {{
                font-size: 0.85rem;
                margin-top: 1rem;
            }}
            div[data-testid="stButton"] button,
            div[data-testid="stDownloadButton"] button {{
                min-height: 44px;
                white-space: normal;
            }}
            .ag-save-toast {{
                bottom: 12px;
                right: 12px;
                left: 12px;
                width: auto;
                grid-template-columns: 32px 1fr;
                padding: 0.8rem;
            }}
            .ag-save-toast-icon {{
                width: 32px;
                height: 32px;
            }}
        }}
        div[data-baseweb="select"] > div {{
            background: var(--ag-surface) !important;
            border-color: var(--ag-line) !important;
            border-radius: 10px !important;
            color: var(--ag-ink) !important;
        }}
        div[data-testid="stSelectbox"] label,
        div[data-testid="stSelectbox"] label *,
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextInput"] label * {{
            color: var(--ag-ink) !important;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _agrovision_logo_svg(size: int = 26) -> str:
    """Return the AgroVision leaf logo SVG."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none"'
        ' stroke="#f3f8ef" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M7 20h10"/>'
        '<path d="M10 20c5.5-2.5.8-6.4 3-10"/>'
        '<path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-2-3.4.8.1 2.9-.6 4.5 0z"/>'
        '<path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.4-3.7-.8.1-2.8-.5-4.6 1.1z"/>'
        '</svg>'
    )


def _render_mobile_header() -> None:
    """Render the mobile-only top bar that opens the navigation drawer."""
    mobile_nav_open = bool(st.session_state.get("mobile_nav_open", False))
    if mobile_nav_open:
        st.markdown('<span class="ag-mobile-nav-open"></span>', unsafe_allow_html=True)

    st.markdown('<span class="ag-mobile-header-marker"></span>', unsafe_allow_html=True)
    menu_col, _spacer_col = st.columns([0.14, 0.86])
    with menu_col:
        if st.button(
            "Close" if mobile_nav_open else "Menu",
            key="mobile_nav_toggle",
            icon=":material/close:" if mobile_nav_open else ":material/menu:",
        ):
            st.session_state["mobile_nav_open"] = not mobile_nav_open
            st.rerun()


def _render_mobile_drawer() -> None:
    """Render the mobile drawer independently from Streamlit's native sidebar."""
    if not st.session_state.get("mobile_nav_open", False):
        return

    current_page = st.session_state.get("active_page", "Home")
    nav_items = (
        (
            "Home",
            "Home",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="m3 9 9-7 9 7"/><path d="M9 22V12h6v10"/>'
            '<path d="M21 9v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9"/></svg>',
        ),
        (
            "Start Simulation",
            "Start Simulation",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>',
        ),
        (
            "Historical Insights",
            "Historical Insights",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
        ),
        (
            "Compare Simulations",
            "Compare Simulations",
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>',
        ),
    )
    links = []
    for page, label, icon in nav_items:
        active_class = " ag-mobile-drawer-link--active" if page == current_page else ""
        links.append(
            f'<a class="ag-mobile-drawer-link{active_class}" '
            f'href="?page={quote(page)}&menu=closed">{icon}<span>{escape(label)}</span></a>'
        )

    st.markdown(
        f"""
        <nav class="ag-mobile-drawer" aria-label="Mobile navigation">
            <div class="ag-mobile-profile">
                <div class="ag-mobile-profile-logo">{_agrovision_logo_svg(28)}</div>
                <div>
                    <div class="ag-mobile-profile-name">AgroVision</div>
                    <div class="ag-mobile-profile-sub">Precision Planting</div>
                </div>
            </div>
            <div class="ag-mobile-drawer-nav">
                {''.join(links)}
            </div>
            <a class="ag-mobile-drawer-close" href="?page={quote(str(current_page))}&menu=closed">
                Close menu
            </a>
        </nav>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    """Render the left navigation and update the selected app section."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="ag-brand" aria-label="AgroVision Home">
                <div class="ag-logo">{_agrovision_logo_svg()}</div>
                <div>
                    <div class="ag-brand-name">AgroVision</div>
                    <div class="ag-brand-tag">Precision Planting</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown(
            '<div class="ag-mobile-drawer-title">Navigation</div>',
            unsafe_allow_html=True,
        )

        _icon_home = (
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="m3 9 9-7 9 7"/>'
            '<path d="M9 22V12h6v10"/>'
            '<path d="M21 9v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9"/>'
            '</svg>'
        )
        _icon_sim = (
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="10"/>'
            '<polygon points="10 8 16 12 10 16 10 8"/></svg>'
        )
        _icon_history = (
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'
            '</svg>'
        )
        _icon_compare = (
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M18 20V10"/>'
            '<path d="M12 20V4"/>'
            '<path d="M6 20v-6"/>'
            '</svg>'
        )
        nav_items = (
            ("Home", _icon_home, ":material/home:", "Home"),
            ("Start Simulation", _icon_sim, ":material/play_circle:", "Start Simulation"),
            (
                "Historical Insights",
                _icon_history,
                ":material/monitoring:",
                "Historical Insights",
            ),
            (
                "Compare Simulations",
                _icon_compare,
                ":material/bar_chart:",
                "Compare Simulations",
            ),
        )
        current_page = st.session_state.get("active_page", "Home")

        st.markdown('<div class="ag-nav">', unsafe_allow_html=True)
        for page, _icon, material_icon, label in nav_items:
            if current_page == page:
                st.markdown(
                    '<span class="ag-nav-active-marker"></span>',
                    unsafe_allow_html=True,
                )
            if st.button(
                label,
                key=f"nav_{page}",
                icon=material_icon,
                use_container_width=True,
            ):
                st.session_state["active_page"] = page
                st.session_state["mobile_nav_open"] = False
                st.query_params["page"] = page
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<span class="ag-mobile-close-marker"></span>',
            unsafe_allow_html=True,
        )
        if st.button("Close menu", key="mobile_nav_close", use_container_width=True):
            st.session_state["mobile_nav_open"] = False
            st.rerun()


def _render_home_page() -> None:
    """Render the landing dashboard from the prototype."""
    _kicker_leaf = (
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/>'
        '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>'
    )

    status_items = [
        "Open-Meteo forecast",
        "Internal station database",
        "Soybean and corn model",
    ]
    dot = '<span class="ag-status-dot"></span>'
    status_html = dot.join(
        f'<span class="ag-status-item">{escape(item)}</span>'
        for item in status_items
    )
    st.markdown(
        f'<div class="ag-kicker">{_kicker_leaf}{escape(HOME_CONTEXT["season"])}</div>'
        f'<h1 style="margin-top:0.5rem;margin-bottom:0;max-width:900px;">Agricultural <em>decision support</em> simulator.</h1>'
        f'<p class="ag-home-subtitle" style="max-width:760px;">{escape(HOME_CONTEXT["subtitle"])}</p>'
        f'<div class="ag-status-row">{status_html}</div>',
        unsafe_allow_html=True,
    )

    _icon_play = (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>'
    )
    _icon_trend = (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
        '<polyline points="17 6 23 6 23 12"/></svg>'
    )
    card_icons = {
        "Start Simulation": _icon_play,
        "Historical Insights": _icon_trend,
    }

    gs_html_parts = []
    for card in QUICK_ACCESS_CARDS:
        title = card["title"]
        body = card["body"]
        target = card["target"]
        icon = card_icons.get(title, _icon_trend)
        dark = bool(card["is_primary"])
        card_cls = "ag-gs-card ag-gs-card--dark" if dark else "ag-gs-card"
        icon_cls = "ag-gs-icon" if dark else "ag-gs-icon ag-gs-icon--light"
        href = f"?page={quote(target)}"
        gs_html_parts.append(
            f'<a class="{card_cls}" href="{href}" target="_self">'
            f'  <div class="ag-gs-card-top">'
            f'    <span class="{icon_cls}">{icon}</span>'
            f'    <span class="ag-gs-arrow">→</span>'
            f'  </div>'
            f'  <p class="ag-gs-title">{title}</p>'
            f'  <p class="ag-gs-body">{body}</p>'
            f'</a>'
        )

    st.markdown('<p class="ag-section-label">Get started</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ag-gs-grid">{"".join(gs_html_parts)}</div>',
        unsafe_allow_html=True,
    )

    _icon_leaf = (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8'
        ' 0 5.5-4.78 10-10 10z"/>'
        '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>'
    )
    _icon_users = (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
    )
    _icon_cal = (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/></svg>'
    )

    glance_icons = [_icon_leaf, _icon_leaf, _icon_users, _icon_users]

    glance_parts = []
    at_a_glance = get_at_a_glance()
    for icon, item in zip(glance_icons, at_a_glance):
        label = item["label"]
        value = item["value"]
        unit = item["unit"]
        sub = item["subtext"]
        unit_html = f' <span class="ag-glance-unit">{unit}</span>' if unit else ""
        glance_parts.append(
            f'<div class="ag-glance-card">'
            f'  <div class="ag-glance-icon">{icon}</div>'
            f'  <div>'
            f'    <div class="ag-glance-label">{label}</div>'
            f'    <div class="ag-glance-value">{value}{unit_html}</div>'
            f'    <div class="ag-glance-sub">{sub}</div>'
            f'  </div>'
            f'</div>'
        )

    st.markdown('<p class="ag-section-label">At a glance</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ag-glance-grid">{"".join(glance_parts)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="ag-source-note">
            {get_data_source_note()}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_historical_insights_page() -> None:
    """Render a compact context page for historical agricultural signals."""
    st.markdown('<div class="ag-kicker">Historical context</div>', unsafe_allow_html=True)
    st.title("Historical insights.")
    st.caption(
        "A dataset-backed view calculated from Bayer internal planting and harvest records."
    )

    historical_insights = get_historical_insights()
    insight_cards = []
    for insight in historical_insights:
        insight_cards.append(
            '<div class="ag-history-card">'
            f'<div class="ag-kicker">{escape(insight["title"])}</div>'
            f'<div class="ag-stat-value">{escape(insight["value"])}</div>'
            f'<p class="ag-muted">{escape(insight["description"])}</p>'
            '</div>'
        )
    st.markdown(
        f'<div class="ag-history-grid">{"".join(insight_cards)}</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    st.subheader("How this informs the simulator")
    st.write(get_historical_insights_explanation())

    st.markdown(
        f"""
        <div class="ag-source-note">
            {get_data_source_note()}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_start_simulation_page() -> None:
    """Render the guided simulation form."""
    st.markdown('<div class="ag-start-title">Start Simulation</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<span class="ag-sim-card-marker"></span>', unsafe_allow_html=True)
        field_context = _render_context_inputs()
        st.session_state["field_context"] = field_context

        st.markdown('<div class="ag-run-button-wrap"></div>', unsafe_allow_html=True)
        action_col_a, action_col_b = st.columns(2)
        with action_col_a:
            run_decision_tree = st.button(
                "Simulate - Decision Tree",
                type="primary",
                use_container_width=True,
            )
        with action_col_b:
            run_payoff_matrix = st.button(
                "Simulate - Payoff Matrix",
                use_container_width=True,
            )

        if run_decision_tree or run_payoff_matrix:
            simulation_method = (
                DECISION_TREE_METHOD if run_decision_tree else PAYOFF_MATRIX_METHOD
            )
            input_errors = field_context.get("_input_errors", [])
            if input_errors:
                st.error("Please correct the numeric inputs before running the simulation.")
                for error in input_errors:
                    st.caption(f"- {error}")
                return

            location = build_farm_weather_location(
                latitude=float(field_context["farm_latitude"]),
                longitude=float(field_context["farm_longitude"]),
                label=(
                    f"Farm location ({field_context['farm_latitude']:.4f}, "
                    f"{field_context['farm_longitude']:.4f})"
                ),
            )
            field_context = {
                **field_context,
                "weather_location": location.label,
                "weather_latitude": location.latitude,
                "weather_longitude": location.longitude,
            }
            st.session_state["field_context"] = field_context

            with st.spinner(
                f"Fetching Open-Meteo forecast and running {simulation_method} simulation..."
            ):
                try:
                    forecast = fetch_open_meteo_forecast(location)
                except Exception as exc:
                    st.error(f"Open-Meteo forecast could not be loaded: {exc}")
                    return

                station_summary = load_station_weather_summary()
                station_observation = (
                    station_summary.to_model_input()
                    if station_summary is not None
                    else None
                )
                simulation_builder = (
                    build_decision_tree_simulation
                    if simulation_method == DECISION_TREE_METHOD
                    else build_payoff_matrix_simulation
                )
                simulation = simulation_builder(
                    field_context,
                    forecast,
                    station_observation=station_observation,
                )
                st.session_state["probabilities"] = simulation.probabilities
                st.session_state["payoff_matrix"] = simulation.payoff_matrix
                st.session_state["weather_evidence"] = simulation.weather_evidence
                st.session_state["productivity_simulation"] = simulation
                st.session_state["simulation_method"] = simulation.simulation_method
            st.session_state["active_page"] = "Recommendation Summary"
            st.query_params["page"] = "Recommendation Summary"
            st.rerun()

        st.markdown(
            """
            <div class="ag-form-caption">
                Climatic conditions are derived from Open-Meteo API and the internal station database.
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_context_inputs() -> dict[str, object]:
    """Render agricultural and operational context inputs from the prototype."""
    defaults = st.session_state.get("field_context", {})
    input_errors: list[str] = []

    col_a, col_b = st.columns(2)
    with col_a:
        farm_latitude = _validated_numeric_text_input(
            "1\\. Farm Latitude",
            key="farm_latitude_input",
            default_value=float(defaults.get("farm_latitude", -13.5277)),
            minimum=-90.0,
            maximum=90.0,
            decimals=4,
            placeholder="-13.5277",
            help_text="Latitude used by Open-Meteo to fetch farm-level weather.",
            errors=input_errors,
        )
        farm_longitude = _validated_numeric_text_input(
            "2\\. Farm Longitude",
            key="farm_longitude_input",
            default_value=float(defaults.get("farm_longitude", -56.0469)),
            minimum=-180.0,
            maximum=180.0,
            decimals=4,
            placeholder="-56.0469",
            help_text="Longitude used by Open-Meteo to fetch farm-level weather.",
            errors=input_errors,
        )
        seed_type = st.selectbox(
            "3\\. Seed Type",
            SEED_TYPE_OPTIONS,
            index=_option_index(list(SEED_TYPE_OPTIONS), defaults.get("seed_type", "soybean")),
        )

    with col_b:
        soil_ph = _validated_numeric_text_input(
            "4\\. Soil pH",
            key="soil_ph_input",
            default_value=float(defaults.get("soil_ph", 6.2)),
            minimum=3.5,
            maximum=8.5,
            decimals=1,
            placeholder="6.2",
            help_text="Accepted range: 3.5 to 8.5.",
            errors=input_errors,
        )
        planting_window = st.selectbox(
            "5\\. Planting Window",
            PLANTING_WINDOW_OPTIONS,
            index=_option_index(
                list(PLANTING_WINDOW_OPTIONS),
                defaults.get("planting_window", "Ideal"),
            ),
        )
        st.text_input(
            "6\\. Climatic Conditions",
            value="Open-Meteo API + Internal Station Database",
            disabled=True,
        )

    if input_errors:
        st.error("Some numeric inputs need attention.")
        for error in input_errors:
            st.caption(f"- {error}")

    return {
        "farm_latitude": farm_latitude,
        "farm_longitude": farm_longitude,
        "seed_type": seed_type,
        "soil_ph": soil_ph,
        "planting_window": planting_window,
        "_input_errors": input_errors,
    }


def _validated_numeric_text_input(
    label: str,
    *,
    key: str,
    default_value: float,
    minimum: float,
    maximum: float,
    decimals: int,
    placeholder: str,
    help_text: str,
    errors: list[str],
) -> float:
    """Render a plain numeric input without +/- controls."""
    raw_value = st.text_input(
        label,
        value=f"{default_value:.{decimals}f}",
        key=key,
        placeholder=placeholder,
        help=help_text,
    )
    normalized = str(raw_value).strip().replace(",", ".")
    try:
        parsed = float(normalized)
    except ValueError:
        errors.append(f"{label.replace('\\\\.', '.')} must be a number.")
        return default_value

    if not minimum <= parsed <= maximum:
        errors.append(
            f"{label.replace('\\\\.', '.')} must be between {minimum:g} and {maximum:g}."
        )
        return parsed

    return round(parsed, decimals)


def _render_compare_strategies_page() -> None:
    """Render visual comparison of the configured strategies."""
    st.title("Compare Strategies")
    st.caption("Based on the current simulation inputs")

    payoff_matrix = _get_payoff_matrix()
    probabilities = _get_probabilities()
    summary = build_decision_summary(payoff_matrix, probabilities)

    expected_df = _scores_to_dataframe(summary.expected_value.scores, "Expected Value")
    minimax_df = _scores_to_dataframe(summary.minimax.scores, "Maximum Regret")

    card_cols = st.columns(3)
    for column, alternative in zip(card_cols, payoff_matrix):
        with column:
            ev_score = summary.expected_value.scores[alternative]
            maximum_regret = summary.minimax.scores[alternative]
            is_recommended = alternative == summary.final_recommendation
            confidence = _strategy_confidence(alternative, summary)
            risk_level = _strategy_risk_level(alternative, payoff_matrix)
            st.markdown(
                f"""
                <div class="ag-card">
                    <strong>{_strategy_label(alternative)}</strong>
                    <p class="ag-muted">{_strategy_description(alternative)}</p>
                    <h2>{ev_score:.1f} bags/ha</h2>
                    <p>Maximum regret: <strong>{maximum_regret:.1f}</strong></p>
                    <p>Risk level: <strong>{risk_level}</strong></p>
                    <p>Confidence: <strong>{confidence}%</strong></p>
                    <span class="ag-pill">{'Recommended' if is_recommended else 'Alternative'}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("Expected Value")
        fig = px.bar(
            expected_df,
            x="Alternative",
            y="Expected Value",
            color="Alternative",
            color_discrete_sequence=["#6b7280", "#9ca3af", "#d1d5db"],
            template="plotly_white",
        )
        fig.update_xaxes(tickangle=0)
        fig.update_yaxes(gridcolor=BORDER)
        fig.update_layout(
            showlegend=False,
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            font_color=TEXT,
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

    with chart_cols[1]:
        st.subheader("Minimax Regret")
        fig = px.bar(
            minimax_df,
            x="Alternative",
            y="Maximum Regret",
            color="Alternative",
            color_discrete_sequence=["#6b7280", "#9ca3af", "#d1d5db"],
            template="plotly_white",
        )
        fig.update_xaxes(tickangle=0)
        fig.update_yaxes(gridcolor=BORDER)
        fig.update_layout(
            showlegend=False,
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            font_color=TEXT,
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

    st.subheader("Payoff Matrix")
    st.dataframe(_payoff_matrix_dataframe(payoff_matrix), use_container_width=True)

    st.subheader("Risk and Confidence Indicators")
    for alternative in payoff_matrix:
        confidence = _strategy_confidence(alternative, summary)
        risk_level = _strategy_risk_level(alternative, payoff_matrix)
        st.markdown(
            f"""
            <div class="ag-risk-row">
                <strong>{_strategy_label(alternative)}</strong>
                <div class="ag-bar"><div class="ag-bar-fill" style="width: {confidence}%;"></div></div>
                <span>{risk_level}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="ag-source-note">
            Comparison metrics are generated from the configured expected
            productivity matrix, scenario probabilities, and Sprint 03 decision
            criteria. Minimax regret is a going-beyond comparison where lower
            values indicate less downside exposure.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_recommendation_page() -> None:
    """Render the final recommendation and supporting calculation."""
    productivity_simulation = st.session_state.get("productivity_simulation")
    if productivity_simulation:
        _render_productivity_recommendation_page(productivity_simulation)
        return

    _render_empty_recommendation_page()


def _render_empty_recommendation_page() -> None:
    """Render a scoped empty state when no productivity run exists yet."""
    st.markdown(
        """
        <div class="ag-page-head">
            <div>
                <div class="ag-kicker">Weather-driven productivity forecast</div>
                <h1>Recommendation <em style="font-style: italic; color: var(--ag-leaf);">summary</em>.</h1>
                <p class="ag-muted" style="max-width: 70ch;">
                    Run a simulation first so AgroVision can fetch Open-Meteo
                    climatic conditions and estimate productivity from the selected
                    seed type, soil pH, and planting window.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ag-card">
            <div class="ag-kicker">No productivity forecast yet</div>
            <h3>Start with the farm inputs</h3>
            <p class="ag-muted">
                The required inputs are farm location, seed type, soil pH, and
                planting window. Climatic conditions are selected automatically
                from Open-Meteo API and the internal station database after the run.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Start Simulation", type="primary"):
        st.session_state["active_page"] = "Start Simulation"
        st.query_params["page"] = "Start Simulation"
        st.rerun()


def _render_productivity_recommendation_page(simulation) -> None:
    """Render the scoped productivity forecast and recommendation summary."""
    field_context = st.session_state.get("field_context", {})
    saved_toast = None
    simulation_method = getattr(simulation, "simulation_method", DECISION_TREE_METHOD)

    header_col, save_col = st.columns([0.72, 0.28])
    with header_col:
        st.markdown(
            f"""
            <div class="ag-page-head">
                <div>
                    <div class="ag-kicker">{escape(simulation_method)} simulation</div>
                    <h1>Recommendation <em style="font-style: italic; color: var(--ag-leaf);">summary</em>.</h1>
                    <p class="ag-muted" style="max-width: 70ch;">
                        {escape(_simulation_method_description(simulation_method))}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with save_col:
        st.markdown('<div class="ag-header-action-marker"></div>', unsafe_allow_html=True)
        if st.button("Save Simulation", use_container_width=True):
            saved_snapshot = _save_simulation_snapshot(simulation, field_context)
            saved_toast = _save_simulation_toast_html(saved_snapshot)

    if saved_toast:
        st.markdown(saved_toast, unsafe_allow_html=True)

    if simulation_method == PAYOFF_MATRIX_METHOD:
        _render_payoff_matrix_recommendation_sections(simulation, field_context)
        return

    st.markdown(
        _productivity_summary_html(simulation, field_context),
        unsafe_allow_html=True,
    )
    st.markdown(
        _data_sources_html(simulation),
        unsafe_allow_html=True,
    )
    st.markdown(
        _weather_evidence_html(simulation.weather_evidence, field_context),
        unsafe_allow_html=True,
    )
    st.markdown(
        _productivity_factors_html(simulation.productivity_factors),
        unsafe_allow_html=True,
    )

    st.download_button(
        "Export PDF",
        data=_build_productivity_summary_pdf(simulation, field_context),
        file_name="agrovision_recommendation_summary.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.markdown(
        """
        <div class="ag-source-note">
            Climatic conditions come from the Open-Meteo forecast for the selected
            farm coordinates. The local station database adds recent observed
            weather as a calibration layer when available. Productivity is also
            adjusted by crop baseline, soil pH, and planting window.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _simulation_method_description(simulation_method: str) -> str:
    if simulation_method == PAYOFF_MATRIX_METHOD:
        return (
            "The Payoff Matrix engine compares seed density strategies with "
            "Expected Value and Minimax using forecast-derived scenario probabilities."
        )
    return (
        "The Decision Tree engine estimates productivity from farm location, seed "
        "type, soil pH, planting window, Open-Meteo climate signals, and station data."
    )


def _render_payoff_matrix_recommendation_sections(
    simulation,
    field_context: dict[str, object],
) -> None:
    """Render Payoff Matrix-specific recommendation output."""
    summary = simulation.decision_summary or build_decision_summary(
        simulation.payoff_matrix,
        simulation.probabilities,
    )

    st.markdown(
        _recommendation_consensus_html(summary, simulation.payoff_matrix),
        unsafe_allow_html=True,
    )
    st.markdown(
        _weather_evidence_html(simulation.weather_evidence, field_context),
        unsafe_allow_html=True,
    )

    criterion_cols = st.columns(2)
    with criterion_cols[0]:
        st.markdown(
            _criterion_card_html(
                "Expected Value",
                "ev",
                summary,
                simulation.payoff_matrix,
                simulation.probabilities,
            ),
            unsafe_allow_html=True,
        )
    with criterion_cols[1]:
        st.markdown(
            _criterion_card_html(
                "Minimax Regret",
                "minimax",
                summary,
                simulation.payoff_matrix,
                simulation.probabilities,
            ),
            unsafe_allow_html=True,
        )

    st.markdown(_findings_card_html(summary), unsafe_allow_html=True)
    st.subheader("Payoff Matrix")
    st.dataframe(_payoff_matrix_dataframe(simulation.payoff_matrix), use_container_width=True)

    st.download_button(
        "Export Summary",
        data=_build_simulation_download_text(simulation, field_context),
        file_name="agrovision_payoff_matrix_summary.txt",
        mime="text/plain",
        use_container_width=True,
    )


def _save_simulation_toast_html(saved_snapshot: dict[str, object]) -> str:
    """Return the save confirmation toast."""
    label = str(saved_snapshot.get("label", "Simulation #1"))
    save_number = label.replace("Simulation ", "").strip() or "#1"
    return dedent(f"""
        <div class="ag-save-toast" role="status" aria-live="polite">
            <div class="ag-save-toast-icon">✓</div>
            <div>
                <div class="ag-save-toast-label">Simulation saved</div>
                <div class="ag-save-toast-title">Your {escape(save_number)} simulation is saved.</div>
                <div class="ag-save-toast-body">
                    To compare it with another run, go to <strong>"Compare Simulations"</strong>.
                </div>
            </div>
        </div>
    """).strip()


def _render_compare_simulations_page() -> None:
    """Render saved simulations from the current Streamlit session."""
    saved_simulations = _get_saved_simulations()

    st.markdown(
        """
        <div class="ag-page-head">
            <div>
                <div class="ag-kicker">Session comparison</div>
                <h1>Compare saved <em style="font-style: italic; color: var(--ag-leaf);">simulations</em>.</h1>
                <p class="ag-muted" style="max-width: 70ch;">
                    Saved runs from the current prototype session, side by side.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not saved_simulations:
        st.markdown(
            """
            <div class="ag-info-card">
                <div class="ag-kicker">No saved simulations</div>
                <h3>Run and save a simulation first.</h3>
                <p class="ag-muted">Saved simulations will appear here until this Streamlit session ends.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start Simulation", type="primary"):
            st.session_state["active_page"] = "Start Simulation"
            st.query_params["page"] = "Start Simulation"
            st.rerun()
        return

    comparison_df = _saved_simulations_dataframe(saved_simulations)
    best_simulation = max(
        saved_simulations,
        key=lambda item: float(item["expected_productivity_bags_ha"]),
    )
    latest_simulation = saved_simulations[-1]

    st.markdown(
        _comparison_summary_html(
            saved_count=len(saved_simulations),
            best_simulation=best_simulation,
            latest_simulation=latest_simulation,
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        _comparison_cards_html(saved_simulations),
        unsafe_allow_html=True,
    )
    st.markdown(
        _comparison_table_html(saved_simulations),
        unsafe_allow_html=True,
    )

    chart_df = comparison_df.rename(
        columns={
            "Simulation": "Simulation",
            "Expected productivity (bags/ha)": "Expected productivity",
        }
    )
    fig = px.bar(
        chart_df,
        x="Simulation",
        y="Expected productivity",
        color="Climate class",
        template="plotly_white",
        color_discrete_sequence=[PRIMARY, CLAY, "#6f7468", "#9ca3af"],
    )
    fig.update_yaxes(gridcolor=BORDER, title="bags/ha")
    fig.update_xaxes(title="")
    fig.update_layout(
        showlegend=True,
        height=340,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font_color=TEXT,
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)

    action_col_a, action_col_b = st.columns([1, 1])
    with action_col_a:
        st.download_button(
            "Download Comparison CSV",
            data=comparison_df.to_csv(index=False),
            file_name="agrovision_session_simulation_comparison.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with action_col_b:
        if st.button("Clear Saved Simulations", use_container_width=True):
            st.session_state["saved_simulations"] = []
            st.rerun()


def _comparison_summary_html(
    *,
    saved_count: int,
    best_simulation: dict[str, object],
    latest_simulation: dict[str, object],
) -> str:
    """Return top-level comparison metrics with app-native styling."""
    best_productivity = float(best_simulation["expected_productivity_bags_ha"])
    return dedent(f"""
    <div class="ag-compare-summary">
        <div class="ag-compare-stat">
            <div class="ag-compare-stat-label">Saved runs</div>
            <div class="ag-compare-stat-value">{saved_count}</div>
        </div>
        <div class="ag-compare-stat">
            <div class="ag-compare-stat-label">Best productivity</div>
            <div class="ag-compare-stat-value">{best_productivity:.2f} bags/ha</div>
        </div>
        <div class="ag-compare-stat">
            <div class="ag-compare-stat-label">Latest run</div>
            <div class="ag-compare-stat-value">{escape(str(latest_simulation["label"]))}</div>
        </div>
    </div>
    """).strip()


def _comparison_cards_html(saved_simulations: list[dict[str, object]]) -> str:
    """Return compact cards for the saved simulation set."""
    cards = []
    for item in saved_simulations:
        simulation_method = item.get("simulation_method", DECISION_TREE_METHOD)
        cards.append(dedent(f"""
        <div class="ag-compare-card">
            <div class="ag-compare-card-head">
                <div>
                    <div class="ag-compare-card-title">{escape(str(item["label"]))}</div>
                    <div class="ag-compare-card-sub">{escape(str(item["saved_at"]))}</div>
                </div>
                <div class="ag-compare-card-value">{float(item["expected_productivity_bags_ha"]):.2f}</div>
            </div>
            <div class="ag-compare-card-grid">
                <div><span>Method</span><strong>{escape(str(simulation_method))}</strong></div>
                <div><span>Seed</span><strong>{escape(str(item["seed_type"]))}</strong></div>
                <div><span>Climate</span><strong>{escape(str(item["climatic_condition"]))}</strong></div>
                <div><span>Coordinates</span><strong>{float(item["farm_latitude"]):.4f}, {float(item["farm_longitude"]):.4f}</strong></div>
                <div><span>Rain</span><strong>{_format_comparison_value(item["total_precipitation_mm"])} mm</strong></div>
                <div><span>Temp</span><strong>{_format_comparison_value(item["average_temperature_c"])} C</strong></div>
                <div><span>Intensity</span><strong>{float(item["weather_intensity_factor"]):.2f}x</strong></div>
            </div>
        </div>
        """).strip())
    return f'<div class="ag-compare-cards">{"".join(cards)}</div>'


def _comparison_table_html(saved_simulations: list[dict[str, object]]) -> str:
    """Return a light, horizontally scrollable comparison table."""
    headers = (
        ("Simulation", "left"),
        ("Method", "left"),
        ("Seed", "left"),
        ("Climate", "left"),
        ("Productivity", "right"),
        ("Lat", "right"),
        ("Long", "right"),
        ("Rain", "right"),
        ("Temp", "right"),
        ("Intensity", "right"),
        ("pH", "right"),
        ("Window", "left"),
    )
    header_html = "".join(
        f'<th data-align="{align}">{escape(label)}</th>' for label, align in headers
    )
    rows = []
    for item in saved_simulations:
        rows.append(dedent(f"""
        <tr>
            <td>{escape(str(item["label"]))}</td>
            <td>{escape(str(item.get("simulation_method", DECISION_TREE_METHOD)))}</td>
            <td>{escape(str(item["seed_type"]))}</td>
            <td><span class="ag-compare-pill">{escape(str(item["climatic_condition"]))}</span></td>
            <td data-align="right">{float(item["expected_productivity_bags_ha"]):.2f} bags/ha</td>
            <td data-align="right">{float(item["farm_latitude"]):.4f}</td>
            <td data-align="right">{float(item["farm_longitude"]):.4f}</td>
            <td data-align="right">{_format_comparison_value(item["total_precipitation_mm"])} mm</td>
            <td data-align="right">{_format_comparison_value(item["average_temperature_c"])} C</td>
            <td data-align="right">{float(item["weather_intensity_factor"]):.2f}x</td>
            <td data-align="right">{float(item["soil_ph"]):.1f}</td>
            <td>{escape(str(item["planting_window"]))}</td>
        </tr>
        """).strip())
    return dedent(f"""
    <div class="ag-compare-table-wrap">
        <table class="ag-compare-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{"".join(rows)}</tbody>
        </table>
    </div>
    """).strip()


def _format_comparison_value(value: object) -> str:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return escape(str(value))


def _save_simulation_snapshot(
    simulation,
    field_context: dict[str, object],
) -> dict[str, object]:
    """Save the current simulation result in session state."""
    saved_simulations = _get_saved_simulations()
    label = f"Simulation #{len(saved_simulations) + 1}"
    weather_evidence = dict(simulation.weather_evidence)
    productivity_factors = dict(simulation.productivity_factors)
    expected_productivity = _display_bags_per_hectare(
        float(simulation.expected_productivity_bags_ha)
    )
    simulation_method = getattr(simulation, "simulation_method", DECISION_TREE_METHOD)
    summary_text = _build_simulation_download_text(simulation, field_context)

    snapshot = {
        "label": label,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "simulation_method": simulation_method,
        "seed_type": _seed_type_label(str(field_context.get("seed_type", "soybean"))),
        "farm_latitude": float(field_context.get("farm_latitude", 0.0) or 0.0),
        "farm_longitude": float(field_context.get("farm_longitude", 0.0) or 0.0),
        "soil_ph": float(field_context.get("soil_ph", 0.0) or 0.0),
        "planting_window": str(field_context.get("planting_window", "")),
        "climatic_condition": str(simulation.climatic_condition),
        "expected_productivity_bags_ha": expected_productivity,
        "average_temperature_c": weather_evidence.get("average_temperature_c", "n/a"),
        "total_precipitation_mm": weather_evidence.get("total_precipitation_mm", "n/a"),
        "max_precipitation_probability_pct": weather_evidence.get(
            "max_precipitation_probability_pct",
            "n/a",
        ),
        "average_et0_mm": weather_evidence.get("average_et0_mm", "n/a"),
        "station_observation_factor": float(
            productivity_factors.get("station_observation_factor", 1.0)
        ),
        "climate_factor": float(productivity_factors.get("climate_factor", 1.0)),
        "weather_intensity_factor": float(
            productivity_factors.get("weather_intensity_factor", 1.0)
        ),
        "soil_ph_factor": float(productivity_factors.get("soil_ph_factor", 1.0)),
        "planting_window_factor": float(
            productivity_factors.get("planting_window_factor", 1.0)
        ),
        "summary_text": summary_text,
    }
    saved_simulations.append(snapshot)
    st.session_state["saved_simulations"] = saved_simulations
    st.session_state["last_saved_summary"] = summary_text
    return snapshot


def _get_saved_simulations() -> list[dict[str, object]]:
    return list(st.session_state.get("saved_simulations", []))


def _saved_simulations_dataframe(
    saved_simulations: list[dict[str, object]],
) -> pd.DataFrame:
    rows = []
    for item in saved_simulations:
        rows.append(
            {
                "Simulation": item["label"],
                "Saved at": item["saved_at"],
                "Method": item.get("simulation_method", DECISION_TREE_METHOD),
                "Seed": item["seed_type"],
                "Latitude": item["farm_latitude"],
                "Longitude": item["farm_longitude"],
                "Soil pH": item["soil_ph"],
                "Planting window": item["planting_window"],
                "Climate class": item["climatic_condition"],
                "Expected productivity (bags/ha)": item[
                    "expected_productivity_bags_ha"
                ],
                "Avg temp (C)": item["average_temperature_c"],
                "Rain total (mm)": item["total_precipitation_mm"],
                "Rain probability (%)": item["max_precipitation_probability_pct"],
                "ET0 avg (mm)": item["average_et0_mm"],
                "Station factor": item["station_observation_factor"],
                "Climate factor": item["climate_factor"],
                "Weather intensity": item["weather_intensity_factor"],
                "Soil factor": item["soil_ph_factor"],
                "Window factor": item["planting_window_factor"],
            }
        )
    return pd.DataFrame(rows)


def _productivity_summary_html(simulation, field_context: dict[str, object]) -> str:
    """Return the scoped recommendation hero for the productivity model."""
    seed_label = _seed_type_label(str(field_context.get("seed_type", "soybean")))
    expected_productivity = _display_bags_per_hectare(
        float(simulation.expected_productivity_bags_ha)
    )
    recommendation_summary = _display_recommendation_summary(
        str(simulation.recommendation_summary),
        raw_productivity=float(simulation.expected_productivity_bags_ha),
        display_productivity=expected_productivity,
    )
    return f"""
    <div class="ag-consensus">
        <div class="ag-consensus-left">
            <div class="ag-consensus-eyebrow">Open-Meteo climate class: {escape(simulation.climatic_condition)}</div>
            <div class="ag-consensus-title">{escape(seed_label)} forecast: <em>{expected_productivity:.2f} bags/ha</em></div>
            <p class="ag-consensus-sub">{escape(recommendation_summary)}</p>
            <div class="ag-consensus-meta">
                <div>
                    <div class="ag-consensus-meta-label">Seed type</div>
                    <div class="ag-consensus-meta-value">{escape(seed_label)}</div>
                </div>
                <div>
                    <div class="ag-consensus-meta-label">Soil pH</div>
                    <div class="ag-consensus-meta-value">{float(field_context.get("soil_ph", 0.0)):.1f}</div>
                </div>
                <div>
                    <div class="ag-consensus-meta-label">Planting window</div>
                    <div class="ag-consensus-meta-value">{escape(str(field_context.get("planting_window", "Ideal")))}</div>
                </div>
                <div>
                    <div class="ag-consensus-meta-label">Expected productivity</div>
                    <div class="ag-consensus-meta-value">{expected_productivity:.2f} bags/ha</div>
                </div>
            </div>
        </div>
        <div class="ag-consensus-right">
            <div class="ag-consensus-crest">✓</div>
            <div class="ag-consensus-chip">Productivity estimate</div>
        </div>
    </div>
    """


def _productivity_factors_html(productivity_factors: dict[str, float]) -> str:
    """Return the simple factor breakdown behind the productivity estimate."""
    base_productivity = _display_bags_per_hectare(
        float(productivity_factors.get("base_productivity", 0.0))
    )
    return dedent(f"""
    <div class="ag-info-card">
        <div class="ag-kicker">How productivity was calculated</div>
        <h3>Model factors</h3>
        <div class="ag-metric-grid ag-metric-grid--six">
            <div class="ag-metric-item">
                <div class="ag-metric-label">Bayer median yield</div>
                <div class="ag-metric-value">{base_productivity:.2f} bags/ha</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Climate factor</div>
                <div class="ag-metric-value">{productivity_factors.get("climate_factor", 1.0):.2f}x</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Weather intensity</div>
                <div class="ag-metric-value">{productivity_factors.get("weather_intensity_factor", 1.0):.2f}x</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Station adjustment</div>
                <div class="ag-metric-value">{productivity_factors.get("station_observation_factor", 1.0):.3f}x</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Soil pH factor</div>
                <div class="ag-metric-value">{productivity_factors.get("soil_ph_factor", 1.0):.2f}x</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Planting window factor</div>
                <div class="ag-metric-value">{productivity_factors.get("planting_window_factor", 1.0):.2f}x</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Bayer records</div>
                <div class="ag-metric-value">{productivity_factors.get("bayer_records", 0):,.0f}</div>
            </div>
        </div>
    </div>
    """).strip()


def _data_sources_html(simulation) -> str:
    """Return a visual explanation of the data sources used in the run."""
    weather_evidence = dict(simulation.weather_evidence)
    productivity_factors = dict(simulation.productivity_factors)
    station = dict(weather_evidence.get("station_observation", {}))
    station_available = bool(station.get("available"))

    station_metrics = (
        _source_metric("Rows", station.get("row_count", "n/a"))
        + _source_metric("Period", _station_period(station))
        + _source_metric(
            "Observed rain",
            _unit_value(station.get("total_precipitation_mm"), "mm"),
        )
        + _source_metric(
            "Station factor",
            f"{float(station.get('station_observation_factor', 1.0)):.3f}x",
        )
        if station_available
        else _source_metric("Status", "Not loaded")
        + _source_metric("Factor", "1.00x")
    )

    return dedent(f"""
    <div class="ag-info-card">
        <div class="ag-kicker">Data lineage</div>
        <h3>Sources used in this productivity estimate</h3>
        <div class="ag-source-grid">
            <div class="ag-source-card">
                <div class="ag-source-card-head">
                    <div class="ag-source-title">Open-Meteo API</div>
                    <div class="ag-source-badge">Forecast</div>
                </div>
                <div class="ag-source-role">Defines the forward-looking climate class and the 7-day weather intensity factor.</div>
                <div class="ag-source-metrics">
                    {_source_metric("Days", weather_evidence.get("forecast_days", "n/a"))}
                    {_source_metric("Climate", weather_evidence.get("classification", "n/a"))}
                    {_source_metric("Rain", _unit_value(weather_evidence.get("total_precipitation_mm"), "mm"))}
                    {_source_metric("Intensity", f"{float(productivity_factors.get("weather_intensity_factor", 1.0)):.2f}x")}
                </div>
            </div>
            <div class="ag-source-card">
                <div class="ag-source-card-head">
                    <div class="ag-source-title">Station database</div>
                    <div class="ag-source-badge">{'Observed' if station_available else 'Optional'}</div>
                </div>
                <div class="ag-source-role">Adds recent local conditions from the station export as a small calibration layer.</div>
                <div class="ag-source-metrics">
                    {station_metrics}
                </div>
            </div>
            <div class="ag-source-card">
                <div class="ag-source-card-head">
                    <div class="ag-source-title">Bayer history + inputs</div>
                    <div class="ag-source-badge">Agronomic</div>
                </div>
                <div class="ag-source-role">Provides crop baseline productivity, pH response, planting window effect, and historical context.</div>
                <div class="ag-source-metrics">
                    {_source_metric("Records", f"{productivity_factors.get("bayer_records", 0):,.0f}")}
                    {_source_metric("Base", f"{_display_bags_per_hectare(float(productivity_factors.get("base_productivity", 0.0))):.2f} bags/ha")}
                    {_source_metric("pH factor", f"{float(productivity_factors.get("soil_ph_factor", 1.0)):.2f}x")}
                    {_source_metric("Window", f"{float(productivity_factors.get("planting_window_factor", 1.0)):.2f}x")}
                </div>
            </div>
        </div>
    </div>
    """).strip()


def _source_metric(label: object, value: object) -> str:
    return (
        f"<div><span>{escape(str(label))}</span>"
        f"<strong>{escape(str(value))}</strong></div>"
    )


def _station_period(station: dict[str, object]) -> str:
    start_time = str(station.get("start_time", "n/a"))
    end_time = str(station.get("end_time", "n/a"))
    if start_time == "n/a" or end_time == "n/a":
        return "n/a"
    return f"{start_time[:10]} to {end_time[:10]}"


def _unit_value(value: object, unit: str) -> str:
    try:
        return f"{float(value):.1f} {unit}"
    except (TypeError, ValueError):
        return "n/a"


def _display_bags_per_hectare(value: float) -> float:
    """Return bags/ha, including for stale session results stored as raw yield."""
    if value > 300:
        return value / 60.0
    return value


def _display_recommendation_summary(
    summary: str,
    *,
    raw_productivity: float,
    display_productivity: float,
) -> str:
    """Normalize old session summaries that used raw average_yield wording."""
    normalized = summary.replace(
        f"{raw_productivity:.2f} average_yield units",
        f"{display_productivity:.2f} bags/ha",
    )
    normalized = normalized.replace("average_yield units", "bags/ha")
    normalized = normalized.replace(" average_yield", " bags/ha")
    return normalized


def _seed_type_label(seed_type: str) -> str:
    """Return the display label for the scoped seed options."""
    return "Corn" if seed_type == "corn" else "Soybean"


def _recommendation_consensus_html(summary, payoff_matrix: PayoffMatrix) -> str:
    """Return the redesigned consensus hero for the recommendation page."""
    final = summary.final_recommendation
    consensus = summary.expected_value.recommendation == summary.minimax.recommendation
    scores = summary.expected_value.scores
    regret_scores = summary.minimax.scores
    values = list(payoff_matrix[final].values())
    status = "Both criteria agree" if consensus else "EV primary - Minimax comparison"
    explanation = (
        f"Expected Value and Minimax both select {_strategy_label(final)}. "
        "This is the most defensible seed density strategy across expected productivity and regret exposure."
        if consensus
        else (
            f"Expected Value selects {_strategy_label(summary.expected_value.recommendation)}, "
            f"while Minimax selects {_strategy_label(summary.minimax.recommendation)}. "
            "Version 1 follows the new scope by using Expected Value as the primary recommendation, "
            "while Minimax remains visible as a risk-aware comparison."
        )
    )

    return f"""
    <div class="ag-consensus">
        <div class="ag-consensus-left">
            <div class="ag-consensus-eyebrow">✦ {escape(status)}</div>
            <div class="ag-consensus-title">Recommended: <em>{escape(_strategy_label(final))}</em></div>
            <p class="ag-consensus-sub">{escape(explanation)}</p>
            <div class="ag-consensus-meta">
                <div>
                    <div class="ag-consensus-meta-label">Seed density strategy</div>
                    <div class="ag-consensus-meta-value">{escape(_strategy_description(final))}</div>
                </div>
                <div>
                    <div class="ag-consensus-meta-label">Expected yield</div>
                    <div class="ag-consensus-meta-value">{scores[final]:.2f} bags/ha</div>
                </div>
                <div>
                    <div class="ag-consensus-meta-label">Max regret</div>
                    <div class="ag-consensus-meta-value">{regret_scores[final]:.2f} bags/ha</div>
                </div>
                <div>
                    <div class="ag-consensus-meta-label">Range</div>
                    <div class="ag-consensus-meta-value">{min(values):.0f} - {max(values):.0f}</div>
                </div>
            </div>
        </div>
        <div class="ag-consensus-right">
            <div class="ag-consensus-crest">✓</div>
            <div class="ag-consensus-chip">{'Consensus pick' if consensus else 'EV primary pick'}</div>
        </div>
    </div>
    """


def _weather_evidence_html(
    weather_evidence: dict[str, object],
    field_context: dict[str, object],
) -> str:
    """Return a compact explanation of the forecast used by the simulation."""
    location = field_context.get(
        "weather_location",
        field_context.get("region", "Selected region"),
    )
    latitude = field_context.get("weather_latitude", "")
    longitude = field_context.get("weather_longitude", "")
    coordinates = (
        f"{float(latitude):.4f}, {float(longitude):.4f}"
        if latitude != "" and longitude != ""
        else "Representative state coordinate"
    )
    limited_note = ""
    if weather_evidence.get("limited_data"):
        limited_note = (
            '<span>Forecast data was incomplete; '
            '<strong>baseline productivity estimate used</strong></span>'
        )
    station = dict(weather_evidence.get("station_observation", {}))
    station_note = ""
    if station.get("available"):
        station_note = (
            f'<span>Local station adjustment: '
            f'<strong>{float(station.get("station_observation_factor", 1.0)):.3f}x</strong></span>'
        )

    return dedent(f"""
    <div class="ag-info-card">
        <div class="ag-kicker">Weather evidence - {escape(str(weather_evidence.get("source", "Open-Meteo")))}</div>
        <h3>Forecast-derived climatic condition</h3>
        <div class="ag-metric-grid">
            <div class="ag-metric-item">
                <div class="ag-metric-label">Lookup point</div>
                <div class="ag-metric-value">{escape(str(location))}</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Coordinates</div>
                <div class="ag-metric-value">{escape(coordinates)}</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Forecast class</div>
                <div class="ag-metric-value">{escape(str(weather_evidence.get("classification", "Unknown")))}</div>
            </div>
            <div class="ag-metric-item">
                <div class="ag-metric-label">Forecast days</div>
                <div class="ag-metric-value">{escape(str(weather_evidence.get("forecast_days", "n/a")))}</div>
            </div>
        </div>
        <div class="ag-weather-strip">
            <span>Average temperature: <strong>{escape(str(weather_evidence.get("average_temperature_c", "n/a")))} °C</strong></span>
            <span>Total precipitation: <strong>{escape(str(weather_evidence.get("total_precipitation_mm", "n/a")))} mm</strong></span>
            <span>Max rain probability: <strong>{escape(str(weather_evidence.get("max_precipitation_probability_pct", "n/a")))}%</strong></span>
            <span>Average ET0: <strong>{escape(str(weather_evidence.get("average_et0_mm", "n/a")))} mm</strong></span>{station_note}{limited_note}
        </div>
    </div>
    """).strip()


def _criterion_card_html(
    title: str,
    kind: str,
    summary,
    payoff_matrix: PayoffMatrix,
    probabilities: ScenarioProbabilities,
) -> str:
    """Return a criterion card with supporting calculation details."""
    is_ev = kind == "ev"
    result = summary.expected_value if is_ev else summary.minimax
    winner = result.recommendation
    score = result.scores[winner]
    alt_id, alt_name = _alternative_parts(winner)
    symbol = "E" if is_ev else "min"
    unit = "bags/ha - expected" if is_ev else "bags/ha - maximum regret"
    subtitle = (
        "Weighted average across all scenarios using forecast-derived probabilities."
        if is_ev
        else "Minimizes the largest regret versus the best strategy in each scenario."
    )
    formula = _criterion_formula(winner, payoff_matrix, probabilities, is_ev)
    matrix = _decision_matrix_html(result, payoff_matrix, probabilities, is_ev)
    note = (
        f"Each expected productivity estimate is weighted by the forecast-derived scenario probability. "
        f"{escape(alt_id)} wins with the highest weighted average."
        if is_ev
        else (
            "The highlighted value is each strategy's largest regret. "
            f"Minimax selects {escape(alt_id)} because its maximum regret is lowest."
        )
    )

    return f"""
    <div class="ag-criterion">
        <div class="ag-criterion-head">
            <div class="ag-criterion-badge">{escape(symbol)}</div>
            <div>
                <div class="ag-criterion-title">{escape(title)}</div>
                <div class="ag-criterion-sub">{escape(subtitle)}</div>
            </div>
        </div>
        <div class="ag-criterion-pick">
            <div class="ag-criterion-eyebrow">Selected alternative</div>
            <div class="ag-criterion-alt">
                <span class="ag-criterion-alt-id">{escape(alt_id)}</span>
                <span class="ag-criterion-alt-name">{escape(alt_name)}</span>
            </div>
            <div class="ag-criterion-metric">
                <span class="ag-criterion-metric-val">{score:.2f}</span>
                <span class="ag-criterion-metric-unit">{escape(unit)}</span>
            </div>
            <div class="ag-criterion-formula">{escape(formula)}</div>
        </div>
        <div class="ag-criterion-toggle">Supporting calculation</div>
        <div class="ag-criterion-detail">
            {matrix}
            <div class="ag-criterion-note">{note}</div>
        </div>
    </div>
    """


def _decision_matrix_html(
    result,
    payoff_matrix: PayoffMatrix,
    probabilities: ScenarioProbabilities,
    is_expected_value: bool,
) -> str:
    """Return a compact HTML decision matrix for one criterion."""
    scenarios = list(probabilities)
    result_label = "Expected Value" if is_expected_value else "Max regret"
    scenario_best_payoffs = {
        scenario: max(payoffs[scenario] for payoffs in payoff_matrix.values())
        for scenario in scenarios
    }
    header_cells = [
        '<div class="ag-dmatrix-cell ag-dmatrix-label">Alternative</div>'
    ]
    for scenario in scenarios:
        probability = f"<br><span style='font-family: var(--ag-mono); color: var(--ag-muted);'>p={probabilities[scenario] * 100:.0f}%</span>"
        header_cells.append(
            f'<div class="ag-dmatrix-cell">{escape(_scenario_label(scenario))}{probability if is_expected_value else ""}</div>'
        )
    header_cells.append(f'<div class="ag-dmatrix-cell ag-dmatrix-result">{escape(result_label)}</div>')

    rows = [f'<div class="ag-dmatrix-head">{"".join(header_cells)}</div>']
    for alternative, scenario_payoffs in payoff_matrix.items():
        is_winner = alternative == result.recommendation
        values = list(scenario_payoffs.values())
        regret_values = [
            scenario_best_payoffs[scenario] - scenario_payoffs[scenario]
            for scenario in scenarios
        ]
        max_regret = max(regret_values)
        alt_id, alt_name = _alternative_parts(alternative)
        cells = [
            '<div class="ag-dmatrix-cell ag-dmatrix-label">'
            f'<span class="ag-dmatrix-alt-id">{escape(alt_id)}</span>'
            f'<span>&nbsp;{escape(alt_name)}</span>'
            '</div>'
        ]
        displayed_values = values if is_expected_value else regret_values
        for value in displayed_values:
            regret_class = " ag-dmatrix-min" if not is_expected_value and value == max_regret else ""
            cells.append(f'<div class="ag-dmatrix-cell{regret_class}">{value:.0f}</div>')
        cells.append(
            f'<div class="ag-dmatrix-cell ag-dmatrix-result">{result.scores[alternative]:.2f}</div>'
        )
        rows.append(
            f'<div class="ag-dmatrix-row{" ag-dmatrix-win" if is_winner else ""}>{"".join(cells)}</div>'
        )

    return f'<div class="ag-dmatrix">{"".join(rows)}</div>'


def _criterion_formula(
    alternative: str,
    payoff_matrix: PayoffMatrix,
    probabilities: ScenarioProbabilities,
    is_expected_value: bool,
) -> str:
    """Return a short formula string for the selected criterion."""
    payoffs = payoff_matrix[alternative]
    if is_expected_value:
        terms = [
            f"{probabilities[scenario]:.2f} x {payoff:.0f}"
            for scenario, payoff in payoffs.items()
        ]
        return "= " + " + ".join(terms)
    scenarios = list(payoffs)
    scenario_best_payoffs = {
        scenario: max(matrix_payoffs[scenario] for matrix_payoffs in payoff_matrix.values())
        for scenario in scenarios
    }
    regrets = [
        scenario_best_payoffs[scenario] - payoffs[scenario]
        for scenario in scenarios
    ]
    return "= max(" + ", ".join(f"{regret:.0f}" for regret in regrets) + ")"


def _findings_card_html(summary) -> str:
    """Return the findings card from the recommendation redesign."""
    consensus = summary.expected_value.recommendation == summary.minimax.recommendation
    final_label = _strategy_label(summary.final_recommendation)
    items = [
        ("Expected Value", "compares strategies using scenario probabilities derived from the forecast."),
        ("Minimax", "compares each strategy's maximum regret against the best outcome available in each scenario."),
        (
            "Final recommendation",
            (
                f"selects {final_label} because both criteria agree."
                if consensus
                else f"selects {final_label} because Expected Value is the primary criterion in Version 1."
            ),
        ),
    ]
    items_html = "".join(
        f"<li><strong>{escape(lead)}</strong> {escape(body)}</li>"
        for lead, body in items
    )
    return f"""
    <div class="ag-card">
        <div class="ag-kicker">How the recommendation was derived</div>
        <h3>Key Findings</h3>
        <ul class="ag-muted" style="line-height: 1.7; margin-bottom: 0;">{items_html}</ul>
    </div>
    """


def _markdown_lines_to_html(text: str) -> str:
    """Convert simple markdown bullet lines into compact HTML."""
    items = []
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith("- "):
            items.append(f"<li>{escape(clean[2:])}</li>")
    return f"<ol>{''.join(items)}</ol>" if items else escape(text)


def _alternative_parts(alternative: str) -> tuple[str, str]:
    """Split an alternative into compact ID and display name."""
    aliases = {
        "Conservative Strategy": ("C", "Conservative"),
        "Adaptive Strategy": ("A", "Adaptive"),
        "Intensive Strategy": ("I", "Intensive"),
    }
    if alternative in aliases:
        return aliases[alternative]
    if " - " not in alternative:
        return alternative, alternative
    return tuple(alternative.split(" - ", maxsplit=1))  # type: ignore[return-value]


def _scenario_label(scenario: str) -> str:
    """Return short scenario label for matrix headers."""
    return scenario.split(" - ", maxsplit=1)[-1]


def _render_probability_inputs(
    suggested_probabilities: ScenarioProbabilities | None = None,
) -> ScenarioProbabilities:
    """Render probability sliders for the three states of the world."""
    st.subheader("Scenario probabilities")
    st.caption("Set how likely each scenario is. The total should equal 1.00.")

    defaults = suggested_probabilities or _get_probabilities()
    cols = st.columns(3)
    probabilities: ScenarioProbabilities = {}

    for column, scenario in zip(cols, defaults):
        with column:
            probabilities[scenario] = st.slider(
                scenario,
                min_value=0.0,
                max_value=1.0,
                value=float(defaults[scenario]),
                step=0.05,
                key=f"probability-{scenario}-{defaults[scenario]:.2f}",
                help="Probability used by Expected Value.",
            )

    return probabilities


def _option_index(options: list[str], selected: object) -> int:
    """Return a safe option index for Streamlit selectbox defaults."""
    try:
        return options.index(str(selected))
    except ValueError:
        return 0


def _render_payoff_inputs() -> PayoffMatrix:
    """Render editable payoff inputs for all alternative-scenario pairs."""
    st.subheader("Expected productivity by scenario")
    st.caption(
        "Values represent estimated productivity in sacks per hectare for each "
        "seed density strategy under each climate scenario."
    )

    current_matrix = _get_payoff_matrix()
    payoff_matrix: PayoffMatrix = {}

    for alternative, scenario_payoffs in current_matrix.items():
        st.markdown(f"**{alternative}**")
        cols = st.columns(3)
        payoff_matrix[alternative] = {}
        for column, (scenario, default_value) in zip(cols, scenario_payoffs.items()):
            with column:
                payoff_matrix[alternative][scenario] = st.number_input(
                    scenario,
                    min_value=0.0,
                    max_value=150.0,
                    value=float(default_value),
                    step=1.0,
                    key=f"payoff-{alternative}-{scenario}",
                    help="Expected productivity used by Expected Value and Minimax.",
                )

    return payoff_matrix


def _get_payoff_matrix() -> PayoffMatrix:
    """Return the active productivity matrix from session state or defaults."""
    current_matrix = st.session_state.get("payoff_matrix")
    if not current_matrix:
        return DEFAULT_PAYOFF_MATRIX
    if set(current_matrix) != set(DEFAULT_PAYOFF_MATRIX):
        return DEFAULT_PAYOFF_MATRIX
    return current_matrix


def _get_probabilities() -> ScenarioProbabilities:
    """Return active scenario probabilities from session state or defaults."""
    return st.session_state.get("probabilities", DEFAULT_SCENARIO_PROBABILITIES)


def _payoff_matrix_dataframe(payoff_matrix: PayoffMatrix) -> pd.DataFrame:
    """Convert productivity matrix dict into a display-friendly dataframe."""
    return pd.DataFrame.from_dict(payoff_matrix, orient="index").rename_axis("Alternative")


def _scores_to_dataframe(scores: dict[str, float], score_label: str) -> pd.DataFrame:
    """Convert criterion scores into a dataframe for charts."""
    return pd.DataFrame(
        {
            "Alternative": [_strategy_label(alternative) for alternative in scores],
            score_label: list(scores.values()),
        }
    )


def _render_trace(trace: dict[str, str]) -> None:
    """Render supporting calculations in an expandable block."""
    with st.expander("Show supporting calculation"):
        for alternative, calculation in trace.items():
            st.markdown(f"**{alternative}**")
            st.code(calculation, language="text")


def _strategy_label(alternative: str) -> str:
    """Return a short strategy label for compact UI elements."""
    labels = {
        "Conservative Strategy": "Conservative",
        "Adaptive Strategy": "Adaptive",
        "Intensive Strategy": "Intensive",
    }
    return labels.get(alternative, alternative.split(" - ", maxsplit=1)[-1])


def _strategy_description(alternative: str) -> str:
    """Return plain-language description for each strategy."""
    descriptions = {
        "Conservative Strategy": "Lower seed density, lower operational risk, and more stable productivity.",
        "Adaptive Strategy": "Balanced seed density that trades off productivity and stability.",
        "Intensive Strategy": "Higher seed density with stronger upside and greater risk exposure.",
    }
    return descriptions[alternative]


def _strategy_risk_level(alternative: str, payoff_matrix: PayoffMatrix) -> str:
    """Classify strategy risk from payoff spread across scenarios."""
    values = list(payoff_matrix[alternative].values())
    spread = max(values) - min(values)
    if spread >= 45:
        return "High"
    if spread >= 25:
        return "Medium"
    return "Low"


def _strategy_confidence(alternative: str, summary) -> int:
    """Return a simple confidence score for comparison visuals."""
    if alternative == summary.minimax.recommendation == summary.expected_value.recommendation:
        return 94
    if alternative == summary.minimax.recommendation:
        return 88
    if alternative == summary.expected_value.recommendation:
        return 82
    return 74


def _suggested_actions(final_recommendation: str) -> str:
    """Return plain-language operational guidance for the selected strategy."""
    if final_recommendation == "Intensive Strategy":
        return (
            "- Use intensive seed density only when climate and soil conditions support higher productivity.\n"
            "- Confirm soil pH and rainfall assumptions before execution.\n"
            "- Monitor downside risk because this strategy is more exposed in unfavorable scenarios."
        )
    if final_recommendation == "Conservative Strategy":
        return (
            "- Use conservative seed density when climate probability or soil pH increases uncertainty.\n"
            "- Prioritize stable performance over peak productivity.\n"
            "- Revisit the unfavorable climate assumptions before final field execution."
        )
    return (
        "- Use adaptive seed density when conditions are mixed and the goal is balanced productivity.\n"
        "- Compare the Expected Value result with the Minimax regret result before execution.\n"
        "- Keep monitoring climate, soil pH, and operational risk before final planting decisions."
    )


def _build_download_text(summary) -> str:
    """Build a simple downloadable text summary."""
    field_context = st.session_state.get("field_context", {})
    context_lines = "\n".join(
        f"{label}: {value}"
        for label, value in field_context.items()
    )
    return (
        "AgroVision Simulation Summary\n"
        f"Final recommendation: {summary.final_recommendation}\n\n"
        "Field context\n"
        f"{context_lines or 'No field context configured.'}\n\n"
        f"Expected Value recommendation: {summary.expected_value.recommendation}\n"
        f"Minimax recommendation: {summary.minimax.recommendation}\n\n"
        f"Explanation: {summary.explanation}\n"
    )


def _build_productivity_download_text(
    simulation,
    field_context: dict[str, object],
) -> str:
    """Build a downloadable text summary for the productivity model."""
    expected_productivity = _display_bags_per_hectare(
        float(simulation.expected_productivity_bags_ha)
    )
    recommendation_summary = _display_recommendation_summary(
        str(simulation.recommendation_summary),
        raw_productivity=float(simulation.expected_productivity_bags_ha),
        display_productivity=expected_productivity,
    )
    weather_evidence = dict(simulation.weather_evidence)
    station = dict(weather_evidence.get("station_observation", {}))
    station_text = (
        f"Local station database: loaded ({station.get('row_count', 'n/a')} rows, "
        f"{station.get('observed_days', 'n/a')} observed days, "
        f"{float(station.get('station_observation_factor', 1.0)):.3f}x factor)"
        if station.get("available")
        else "Local station database: not loaded"
    )
    return (
        "AgroVision Productivity Summary\n"
        f"Seed type: {_seed_type_label(str(field_context.get('seed_type', 'soybean')))}\n"
        f"Farm latitude: {field_context.get('farm_latitude')}\n"
        f"Farm longitude: {field_context.get('farm_longitude')}\n"
        f"Soil pH: {field_context.get('soil_ph')}\n"
        f"Planting window: {field_context.get('planting_window')}\n"
        f"Climatic condition: {simulation.climatic_condition}\n"
        f"Weather source: {weather_evidence.get('source', 'Open-Meteo')}\n"
        f"{station_text}\n"
        f"Expected productivity: {expected_productivity:.2f} bags/ha\n\n"
        f"Recommendation summary: {recommendation_summary}\n"
    )


def _build_simulation_download_text(
    simulation,
    field_context: dict[str, object],
) -> str:
    """Build a text summary for whichever simulation engine produced the result."""
    simulation_method = getattr(simulation, "simulation_method", DECISION_TREE_METHOD)
    if simulation_method != PAYOFF_MATRIX_METHOD:
        return _build_productivity_download_text(simulation, field_context)

    summary = simulation.decision_summary or build_decision_summary(
        simulation.payoff_matrix,
        simulation.probabilities,
    )
    weather_evidence = dict(simulation.weather_evidence)
    probability_lines = "\n".join(
        f"- {scenario}: {probability:.2f}"
        for scenario, probability in simulation.probabilities.items()
    )
    payoff_lines = "\n".join(
        f"- {alternative}: "
        + ", ".join(
            f"{scenario}={payoff:.2f}"
            for scenario, payoff in scenario_payoffs.items()
        )
        for alternative, scenario_payoffs in simulation.payoff_matrix.items()
    )
    return (
        "AgroVision Payoff Matrix Summary\n"
        f"Simulation method: {simulation_method}\n"
        f"Seed type: {_seed_type_label(str(field_context.get('seed_type', 'soybean')))}\n"
        f"Farm latitude: {field_context.get('farm_latitude')}\n"
        f"Farm longitude: {field_context.get('farm_longitude')}\n"
        f"Soil pH: {field_context.get('soil_ph')}\n"
        f"Planting window: {field_context.get('planting_window')}\n"
        f"Climatic condition: {simulation.climatic_condition}\n"
        f"Weather source: {weather_evidence.get('source', 'Open-Meteo')}\n\n"
        "Scenario probabilities\n"
        f"{probability_lines}\n\n"
        "Payoff matrix\n"
        f"{payoff_lines}\n\n"
        f"Final recommendation: {summary.final_recommendation}\n"
        f"Expected Value recommendation: {summary.expected_value.recommendation}\n"
        f"Minimax recommendation: {summary.minimax.recommendation}\n"
        f"Explanation: {summary.explanation}\n"
    )


def _build_productivity_summary_pdf(
    simulation,
    field_context: dict[str, object],
) -> bytes:
    """Build a PDF export that mirrors the recommendation summary view."""
    expected_productivity = _display_bags_per_hectare(
        float(simulation.expected_productivity_bags_ha)
    )
    recommendation_summary = _display_recommendation_summary(
        str(simulation.recommendation_summary),
        raw_productivity=float(simulation.expected_productivity_bags_ha),
        display_productivity=expected_productivity,
    )
    seed_label = _seed_type_label(str(field_context.get("seed_type", "soybean")))
    weather_evidence = dict(simulation.weather_evidence)
    productivity_factors = dict(simulation.productivity_factors)
    station = dict(weather_evidence.get("station_observation", {}))
    station_status = (
        f"Loaded, {station.get('row_count', 'n/a')} rows, "
        f"{float(station.get('station_observation_factor', 1.0)):.3f}x factor"
        if station.get("available")
        else "Not loaded"
    )

    pages: list[list[str]] = [[]]
    page_width = 612
    page_height = 792
    margin = 54
    y = 742.0

    def add_page() -> None:
        nonlocal y
        pages.append([])
        y = 742.0

    def op(command: str) -> None:
        pages[-1].append(command)

    def ensure_space(height: float) -> None:
        if y - height < 56:
            add_page()

    def color(hex_color: str) -> tuple[float, float, float]:
        clean = hex_color.lstrip("#")
        return (
            int(clean[0:2], 16) / 255,
            int(clean[2:4], 16) / 255,
            int(clean[4:6], 16) / 255,
        )

    def rect(x: float, top: float, width: float, height: float, fill: str) -> None:
        r, g, b = color(fill)
        op(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {top - height:.2f} {width:.2f} {height:.2f} re f")

    def text(
        value: object,
        x: float,
        baseline: float,
        *,
        size: int = 10,
        font: str = "F1",
        fill: str = TEXT,
    ) -> None:
        r, g, b = color(fill)
        safe = _pdf_escape(str(value))
        op(
            "BT "
            f"/{font} {size} Tf "
            f"{r:.3f} {g:.3f} {b:.3f} rg "
            f"1 0 0 1 {x:.2f} {baseline:.2f} Tm "
            f"({safe}) Tj ET"
        )

    def wrapped_lines(value: object, width: float, size: int) -> list[str]:
        words = str(value).replace("\n", " ").split()
        if not words:
            return [""]
        max_chars = max(18, int(width / (size * 0.52)))
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def paragraph(
        value: object,
        x: float,
        width: float,
        *,
        size: int = 10,
        line_height: float = 14,
        font: str = "F1",
        fill: str = TEXT,
    ) -> None:
        nonlocal y
        lines = wrapped_lines(value, width, size)
        ensure_space(len(lines) * line_height + 4)
        for line in lines:
            text(line, x, y, size=size, font=font, fill=fill)
            y -= line_height

    def section_title(label: str) -> None:
        nonlocal y
        ensure_space(34)
        y -= 12
        text(label.upper(), margin, y, size=9, font="F2", fill=PRIMARY_DARK)
        y -= 18

    def metric(label: str, value: object, x: float, top: float, width: float) -> None:
        rect(x, top, width, 58, "#f7f8f2")
        text(label.upper(), x + 12, top - 20, size=7, font="F2", fill=MUTED)
        text(value, x + 12, top - 42, size=13, font="F2", fill=TEXT)

    rect(0, page_height, page_width, page_height, BACKGROUND)
    text("AgroVision", margin, y, size=24, font="F2", fill=TEXT)
    text("Recommendation Summary", margin, y - 24, size=14, font="F1", fill=PRIMARY_DARK)
    text(datetime.now().strftime("%Y-%m-%d %H:%M"), page_width - 150, y, size=9, fill=MUTED)
    y -= 62

    rect(margin, y, page_width - margin * 2, 126, PRIMARY_DARK)
    text(
        f"{seed_label} forecast",
        margin + 24,
        y - 30,
        size=13,
        font="F2",
        fill="#f3f8ef",
    )
    text(
        f"{expected_productivity:.2f} bags/ha",
        margin + 24,
        y - 60,
        size=26,
        font="F2",
        fill="#f3f8ef",
    )
    text(
        f"Open-Meteo climate class: {simulation.climatic_condition}",
        margin + 24,
        y - 90,
        size=10,
        fill="#f3f8ef",
    )
    y -= 148

    section_title("Recommendation")
    paragraph(recommendation_summary, margin, page_width - margin * 2, size=11, line_height=16)

    section_title("Field context")
    metric_top = y
    col_w = (page_width - margin * 2 - 18) / 4
    metric("Seed type", seed_label, margin, metric_top, col_w)
    metric("Soil pH", f"{float(field_context.get('soil_ph', 0.0)):.1f}", margin + (col_w + 6), metric_top, col_w)
    metric("Planting window", field_context.get("planting_window", "Ideal"), margin + (col_w + 6) * 2, metric_top, col_w)
    metric("Productivity", f"{expected_productivity:.2f}", margin + (col_w + 6) * 3, metric_top, col_w)
    y -= 78

    section_title("Weather evidence")
    weather_items = (
        ("Source", weather_evidence.get("source", "Open-Meteo")),
        ("Average temperature", _unit_value(weather_evidence.get("average_temperature_c"), "C")),
        ("Total precipitation", _unit_value(weather_evidence.get("total_precipitation_mm"), "mm")),
        ("Rain probability", f"{weather_evidence.get('max_precipitation_probability_pct', 'n/a')}%"),
        ("Station database", station_status),
    )
    for label, value in weather_items:
        paragraph(f"{label}: {value}", margin, page_width - margin * 2, size=10, line_height=14)

    section_title("Model factors")
    factor_items = (
        ("Bayer median yield", f"{_display_bags_per_hectare(float(productivity_factors.get('base_productivity', 0.0))):.2f} bags/ha"),
        ("Climate factor", f"{float(productivity_factors.get('climate_factor', 1.0)):.2f}x"),
        ("Weather intensity", f"{float(productivity_factors.get('weather_intensity_factor', 1.0)):.2f}x"),
        ("Station adjustment", f"{float(productivity_factors.get('station_observation_factor', 1.0)):.3f}x"),
        ("Soil pH factor", f"{float(productivity_factors.get('soil_ph_factor', 1.0)):.2f}x"),
        ("Planting window factor", f"{float(productivity_factors.get('planting_window_factor', 1.0)):.2f}x"),
    )
    for label, value in factor_items:
        paragraph(f"{label}: {value}", margin, page_width - margin * 2, size=10, line_height=14)

    return _pdf_document(pages, page_width=page_width, page_height=page_height)


def _pdf_escape(value: str) -> str:
    """Escape text for a simple PDF string literal."""
    replacements = {
        "✓": "OK",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "’": "'",
    }
    clean = "".join(replacements.get(char, char) for char in value)
    clean = clean.encode("latin-1", errors="replace").decode("latin-1")
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_document(
    pages: list[list[str]],
    *,
    page_width: int,
    page_height: int,
) -> bytes:
    """Return a minimal PDF document from page content streams."""
    objects: list[bytes] = []
    page_count = len(pages)
    catalog_id = 1
    pages_id = 2
    font_regular_id = 3
    font_bold_id = 4
    first_page_id = 5
    first_content_id = first_page_id + page_count

    page_ids = [first_page_id + index for index in range(page_count)]
    content_ids = [first_content_id + index for index in range(page_count)]

    objects.append(f"{catalog_id} 0 obj\n<< /Type /Catalog /Pages {pages_id} 0 R >>\nendobj\n".encode())
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.append(f"{pages_id} 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {page_count} >>\nendobj\n".encode())
    objects.append(f"{font_regular_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode())
    objects.append(f"{font_bold_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n".encode())

    for page_id, content_id in zip(page_ids, content_ids):
        objects.append(
            (
                f"{page_id} 0 obj\n"
                "<< /Type /Page "
                f"/Parent {pages_id} 0 R "
                f"/MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>\n"
                "endobj\n"
            ).encode()
        )

    for content_id, operations in zip(content_ids, pages):
        stream = "\n".join(operations).encode("latin-1", errors="replace")
        objects.append(
            (
                f"{content_id} 0 obj\n"
                f"<< /Length {len(stream)} >>\n"
                "stream\n"
            ).encode()
            + stream
            + b"\nendstream\nendobj\n"
        )

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode()
    )
    return bytes(output)
