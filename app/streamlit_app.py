from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import psycopg
import pydeck as pdk
import streamlit as st
from psycopg.rows import dict_row

# ── Region presets ────────────────────────────────────────────────────────────

REGIONS: dict[str, dict] = {
    "World":         dict(north=85,  south=-85, west=-180, east=180,  lat=20,  lon=0,    zoom=1),
    "North America": dict(north=75,  south=15,  west=-170, east=-50,  lat=45,  lon=-100, zoom=2),
    "Europe":        dict(north=72,  south=35,  west=-15,  east=45,   lat=54,  lon=15,   zoom=3),
    "Asia Pacific":  dict(north=60,  south=-10, west=60,   east=180,  lat=25,  lon=120,  zoom=2),
    "Middle East":   dict(north=45,  south=10,  west=25,   east=65,   lat=27,  lon=45,   zoom=3),
    "Africa":        dict(north=40,  south=-40, west=-20,  east=55,   lat=0,   lon=20,   zoom=2),
    "South America": dict(north=15,  south=-60, west=-85,  east=-30,  lat=-20, lon=-60,  zoom=2),
}

_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://vessel:vessel@localhost:5432/vessel_track",
)

# ── Data queries ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_aircraft(north: float, south: float, west: float, east: float) -> pd.DataFrame:
    try:
        with psycopg.connect(_DB_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT flight_id, callsign, aircraft_type, registration,
                           lat, lon, altitude, speed, heading, on_ground, last_seen
                    FROM aircraft_positions
                    WHERE captured_at = (SELECT MAX(captured_at) FROM aircraft_positions)
                      AND lat BETWEEN %s AND %s
                      AND lon BETWEEN %s AND %s
                    """,
                    (south, north, west, east),
                )
                rows = cur.fetchall()
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=5)
def load_aircraft_types(north: float, south: float, west: float, east: float) -> list[str]:
    try:
        with psycopg.connect(_DB_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT aircraft_type
                    FROM aircraft_positions
                    WHERE captured_at = (SELECT MAX(captured_at) FROM aircraft_positions)
                      AND lat BETWEEN %s AND %s
                      AND lon BETWEEN %s AND %s
                      AND aircraft_type IS NOT NULL
                    ORDER BY aircraft_type
                    """,
                    (south, north, west, east),
                )
                return [r["aircraft_type"] for r in cur.fetchall()]
    except Exception:
        return []

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Air Traffic",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────

st.session_state.setdefault("region", "World")
st.session_state.setdefault("callsign_filter", "")
st.session_state.setdefault("type_filter", [])

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✈ Air Traffic")
    st.caption("Live ADS-B · FlightRadar24")
    st.divider()

    st.selectbox("Region", list(REGIONS.keys()), key="region")
    region = REGIONS[st.session_state["region"]]

    st.divider()
    st.subheader("Filters")

    st.text_input(
        "Callsign contains",
        key="callsign_filter",
        placeholder="e.g. BAW",
    )

    available_types = load_aircraft_types(
        region["north"], region["south"], region["west"], region["east"]
    )
    # Drop stale selections that no longer exist in the current snapshot
    valid = [t for t in st.session_state["type_filter"] if t in available_types]
    if valid != st.session_state["type_filter"]:
        st.session_state["type_filter"] = valid

    st.multiselect(
        "Aircraft type",
        options=available_types,
        key="type_filter",
        placeholder="All types",
    )
    if not available_types:
        st.caption("No enriched types in this region yet.")

    st.divider()
    st.caption("Refreshes every 5 s")

# ── Auto-refreshing traffic fragment ─────────────────────────────────────────

@st.fragment(run_every="5s")
def render_traffic() -> None:
    region = REGIONS[st.session_state["region"]]
    callsign_f = st.session_state.get("callsign_filter", "").strip().upper()
    type_f: list[str] = st.session_state.get("type_filter", [])

    df = load_aircraft(
        region["north"], region["south"], region["west"], region["east"]
    )

    if df.empty:
        st.info(
            "Waiting for the first scrape cycle to complete — "
            "this takes about 10 seconds after `make dashboard`.",
            icon="⏳",
        )
        return

    if callsign_f:
        df = df[df["callsign"].fillna("").str.contains(callsign_f)]
    if type_f:
        df = df[df["aircraft_type"].isin(type_f)]

    # ── Metrics ───────────────────────────────────────────────────────────────
    airborne  = int((~df["on_ground"].fillna(False)).sum())
    on_ground = int(df["on_ground"].fillna(False).sum())

    with st.container(horizontal=True):
        st.metric("Aircraft visible", len(df), border=True)
        st.metric("Airborne", airborne, border=True)
        st.metric("On ground", on_ground, border=True)

    # ── Map ───────────────────────────────────────────────────────────────────
    map_df = df.dropna(subset=["lat", "lon"]).copy()
    map_df["color"] = map_df["on_ground"].apply(
        lambda g: [255, 140, 0, 210] if g else [0, 200, 255, 160]
    )
    map_df["alt_str"]  = map_df["altitude"].fillna("—").astype(str)
    map_df["spd_str"]  = map_df["speed"].fillna("—").astype(str)
    map_df["hdg_str"]  = map_df["heading"].fillna("—").astype(str)
    map_df["type_str"] = map_df["aircraft_type"].fillna("unknown")

    layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=6000,
        radius_min_pixels=3,
        radius_max_pixels=10,
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(
        latitude=region["lat"],
        longitude=region["lon"],
        zoom=region["zoom"],
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{callsign}</b><br/>"
            "Alt: {alt_str} ft &nbsp;|&nbsp; Spd: {spd_str} kts<br/>"
            "Hdg: {hdg_str}° &nbsp;|&nbsp; Type: {type_str}"
        ),
        "style": {
            "background": "#2E3440",
            "color": "#ECEFF4",
            "font-size": "12px",
            "padding": "6px 10px",
            "border-radius": "4px",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            tooltip=tooltip,
            map_provider="carto",
            map_style=pdk.map_styles.DARK,
        ),
        width="stretch",
        height=560,
    )

    st.caption(
        f"🔵 Airborne &nbsp; 🟠 On ground &nbsp;·&nbsp; "
        f"Snapshot: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    )

    # ── Aircraft list ─────────────────────────────────────────────────────────
    with st.expander(f"Aircraft list ({len(df)})", expanded=True):
        display = ["callsign", "aircraft_type", "registration",
                   "altitude", "speed", "heading", "on_ground", "lat", "lon"]
        display = [c for c in display if c in df.columns]
        st.dataframe(
            df[display].sort_values("callsign").reset_index(drop=True),
            hide_index=True,
            width="stretch",
            column_config={
                "callsign":      st.column_config.TextColumn("Callsign"),
                "aircraft_type": st.column_config.TextColumn("Type"),
                "registration":  st.column_config.TextColumn("Reg"),
                "altitude":      st.column_config.NumberColumn("Alt (ft)",  format="%d"),
                "speed":         st.column_config.NumberColumn("Spd (kts)", format="%d"),
                "heading":       st.column_config.NumberColumn("Hdg (°)",   format="%d"),
                "on_ground":     st.column_config.CheckboxColumn("On Ground"),
                "lat":           st.column_config.NumberColumn("Lat", format="%.4f"),
                "lon":           st.column_config.NumberColumn("Lon", format="%.4f"),
            },
        )


render_traffic()
