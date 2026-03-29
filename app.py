import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AquaWatch · Water Quality Monitor",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Firebase config ───────────────────────────────────────────────────────────
FIREBASE_URL = (
    "https://flood-alert--2-default-rtdb.asia-southeast1.firebasedatabase.app"
    "/WaterQuality/LiveData.json"
)

# ── Thresholds ────────────────────────────────────────────────────────────────
THRESHOLDS = {
    "ph":          {"min": 6.5,  "max": 8.5,  "unit": "",     "label": "pH Level",      "icon": "⚗️"},
    "tds":         {"min": 0,    "max": 500,   "unit": "ppm",  "label": "TDS",           "icon": "🧂"},
    "temperature": {"min": 10,   "max": 30,    "unit": "°C",   "label": "Temperature",   "icon": "🌡️"},
    "turbidity":   {"min": 0,    "max": 4,     "unit": "NTU",  "label": "Turbidity",     "icon": "🌊"},
}

GAUGE_RANGES = {
    "ph":          (0, 14),
    "tds":         (0, 1500),
    "temperature": (0, 50),
    "turbidity":   (0, 1500),
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700&display=swap');

/* ── Root variables ── */
:root {
    --bg-deep:    #040d1a;
    --bg-card:    #071428;
    --bg-panel:   #0a1e38;
    --accent-1:   #00d4ff;
    --accent-2:   #00ff88;
    --accent-warn:#ffb300;
    --accent-danger:#ff3b5c;
    --text-hi:    #e8f4ff;
    --text-mid:   #7ba8cc;
    --text-lo:    #3a6080;
    --border:     rgba(0,212,255,0.15);
    --glow-1:     rgba(0,212,255,0.25);
    --glow-2:     rgba(0,255,136,0.2);
}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-deep) !important;
    font-family: 'Exo 2', sans-serif;
    color: var(--text-hi);
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none; }
.stApp { background: var(--bg-deep) !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--accent-1); border-radius: 2px; }

/* ── Header ── */
.aq-header {
    background: linear-gradient(135deg, #040d1a 0%, #071e3d 60%, #040d1a 100%);
    border-bottom: 1px solid var(--border);
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    margin: -1rem -1rem 0 -1rem;
}
.aq-header::before {
    content: '';
    position: absolute;
    top: -60px; left: 30%;
    width: 40%; height: 120px;
    background: radial-gradient(ellipse, rgba(0,212,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.aq-logo {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 3px;
    color: var(--accent-1);
    text-transform: uppercase;
}
.aq-logo span { color: var(--text-hi); }
.aq-subtitle {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-mid);
    letter-spacing: 2px;
    margin-top: 2px;
}
.aq-live-badge {
    display: flex; align-items: center; gap: 8px;
    background: rgba(0,255,136,0.08);
    border: 1px solid rgba(0,255,136,0.3);
    border-radius: 20px;
    padding: 6px 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent-2);
    letter-spacing: 1px;
}
.pulse-dot {
    width: 8px; height: 8px;
    background: var(--accent-2);
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 6px var(--accent-2);
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.7); }
}

/* ── Status bar ── */
.aq-status-bar {
    display: flex; align-items: center; gap: 24px;
    padding: 10px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 1.2rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-mid);
}
.aq-status-bar .ts { color: var(--accent-1); }
.aq-status-bar .sep { color: var(--text-lo); }

/* ── Alert banner ── */
.alert-safe {
    background: linear-gradient(90deg, rgba(0,255,136,0.08), transparent);
    border-left: 3px solid var(--accent-2);
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent-2);
    margin-bottom: 1rem;
}
.alert-warn {
    background: linear-gradient(90deg, rgba(255,179,0,0.1), transparent);
    border-left: 3px solid var(--accent-warn);
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent-warn);
    margin-bottom: 1rem;
}
.alert-danger {
    background: linear-gradient(90deg, rgba(255,59,92,0.12), transparent);
    border-left: 3px solid var(--accent-danger);
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent-danger);
    margin-bottom: 1rem;
    animation: blink-border 1.2s ease-in-out infinite alternate;
}
@keyframes blink-border { from { opacity: 1; } to { opacity: 0.5; } }

/* ── Metric card ── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 18px 10px 18px;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.3s;
}
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-1), transparent);
    opacity: 0.6;
}
.metric-card.warn::after  { background: linear-gradient(90deg, transparent, var(--accent-warn), transparent); }
.metric-card.danger::after { background: linear-gradient(90deg, transparent, var(--accent-danger), transparent); animation: blink-border 0.8s infinite; }

.mc-icon {
    font-size: 1.4rem;
    margin-bottom: 4px;
}
.mc-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 2px;
    color: var(--text-mid);
    text-transform: uppercase;
    margin-bottom: 4px;
}
.mc-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
    color: var(--accent-1);
}
.mc-value.warn   { color: var(--accent-warn); }
.mc-value.danger { color: var(--accent-danger); }
.mc-unit {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-mid);
    margin-left: 4px;
}
.mc-status {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 1px;
    margin-top: 8px;
}
.mc-status.safe   { background: rgba(0,255,136,0.1);  color: var(--accent-2);     border: 1px solid rgba(0,255,136,0.3); }
.mc-status.warn   { background: rgba(255,179,0,0.1);  color: var(--accent-warn);  border: 1px solid rgba(255,179,0,0.3); }
.mc-status.danger { background: rgba(255,59,92,0.12); color: var(--accent-danger);border: 1px solid rgba(255,59,92,0.3); }

/* ── Section title ── */
.sec-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-mid);
    border-left: 3px solid var(--accent-1);
    padding-left: 10px;
    margin: 1.4rem 0 0.8rem 0;
}

/* ── Chart container ── */
.chart-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 8px 4px;
}

/* ── Footer ── */
.aq-footer {
    text-align: center;
    padding: 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-lo);
    letter-spacing: 1px;
    border-top: 1px solid var(--border);
    margin-top: 1.5rem;
}

/* ── Plotly tweaks ── */
.js-plotly-plot .plotly .modebar { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_data():
    try:
        r = requests.get(FIREBASE_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def get_status(key, value):
    t = THRESHOLDS[key]
    if value < t["min"] or value > t["max"]:
        # how far out of range?
        margin = max(abs(value - t["min"]), abs(value - t["max"]))
        safe_range = t["max"] - t["min"]
        if margin > safe_range * 0.5:
            return "danger"
        return "warn"
    return "safe"


def status_label(s):
    return {"safe": "● NORMAL", "warn": "▲ WARNING", "danger": "✖ CRITICAL"}[s]


def make_gauge(key, value, status):
    cfg = THRESHOLDS[key]
    lo, hi = GAUGE_RANGES[key]
    color_map = {"safe": "#00ff88", "warn": "#ffb300", "danger": "#ff3b5c"}
    bar_color = color_map[status]

    safe_lo = max(lo, cfg["min"])
    safe_hi = min(hi, cfg["max"])

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 3),
        number={
            "font": {"family": "Rajdhani, sans-serif", "size": 30, "color": bar_color},
            "suffix": f" {cfg['unit']}",
        },
        gauge={
            "axis": {
                "range": [lo, hi],
                "tickfont": {"family": "Share Tech Mono", "size": 9, "color": "#3a6080"},
                "tickcolor": "#3a6080",
                "dtick": (hi - lo) / 5,
            },
            "bar": {"color": bar_color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(0,212,255,0.15)",
            "steps": [
                {"range": [lo, safe_lo],  "color": "rgba(255,59,92,0.15)"},
                {"range": [safe_lo, safe_hi], "color": "rgba(0,255,136,0.1)"},
                {"range": [safe_hi, hi],  "color": "rgba(255,59,92,0.15)"},
            ],
            "threshold": {
                "line": {"color": bar_color, "width": 2},
                "thickness": 0.75,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        height=190,
        margin=dict(t=20, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#7ba8cc",
    )
    return fig


def make_trend(key, history_df):
    cfg = THRESHOLDS[key]
    color = "#00d4ff"
    fill_color = "rgba(0,212,255,0.07)"

    fig = go.Figure()
    if not history_df.empty and key in history_df.columns:
        xs = history_df["ts"]
        ys = history_df[key]

        # Safe-band
        fig.add_hrect(
            y0=cfg["min"], y1=cfg["max"],
            fillcolor="rgba(0,255,136,0.05)",
            line_width=0,
        )
        fig.add_hline(y=cfg["min"], line=dict(color="rgba(0,255,136,0.3)", width=1, dash="dot"))
        fig.add_hline(y=cfg["max"], line=dict(color="rgba(0,255,136,0.3)", width=1, dash="dot"))

        # Fill under line
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            fill="tozeroy",
            fillcolor=fill_color,
            line=dict(color=color, width=2, shape="spline"),
            hovertemplate=f"<b>{cfg['label']}</b><br>%{{y:.3f}} {cfg['unit']}<extra></extra>",
        ))

    fig.update_layout(
        height=180,
        margin=dict(t=10, b=30, l=40, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(family="Share Tech Mono", size=8, color="#3a6080"),
            tickformat="%H:%M:%S",
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(0,212,255,0.06)", zeroline=False,
            tickfont=dict(family="Share Tech Mono", size=8, color="#3a6080"),
        ),
        showlegend=False,
    )
    return fig


# ── Session state init ────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None
if "fetch_count" not in st.session_state:
    st.session_state.fetch_count = 0

# ── Fetch ─────────────────────────────────────────────────────────────────────
raw = fetch_data()
now = datetime.now()

if raw:
    row = {
        "ts":          now,
        "ph":          float(raw.get("ph", 0)),
        "tds":         float(raw.get("tds", 0)),
        "temperature": float(raw.get("temperature", 0)),
        "turbidity":   float(raw.get("turbidity", 0)),
    }
    st.session_state.history.append(row)
    # Keep last 120 points (~10 min at 5 s interval)
    st.session_state.history = st.session_state.history[-120:]
    st.session_state.last_fetch = now
    st.session_state.fetch_count += 1

history_df = pd.DataFrame(st.session_state.history) if st.session_state.history else pd.DataFrame()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="aq-header">
  <div>
    <div class="aq-logo">Aqua<span>Watch</span></div>
    <div class="aq-subtitle">REAL-TIME WATER QUALITY INTELLIGENCE PLATFORM</div>
  </div>
  <div class="aq-live-badge">
    <div class="pulse-dot"></div> LIVE MONITORING
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# ── Status bar ────────────────────────────────────────────────────────────────
fetch_info = f"Firebase · Asia-Southeast1"
ts_str = now.strftime("%Y-%m-%d  %H:%M:%S") if raw else "—"
count_str = f"POLL #{st.session_state.fetch_count}"
st.markdown(f"""
<div class="aq-status-bar">
  <span>📡 {fetch_info}</span>
  <span class="sep">|</span>
  <span>🕒 <span class="ts">{ts_str}</span></span>
  <span class="sep">|</span>
  <span>{count_str}</span>
  <span class="sep">|</span>
  <span>⏱ AUTO-REFRESH: 5 s</span>
</div>
""", unsafe_allow_html=True)

# ── Connection error ──────────────────────────────────────────────────────────
if not raw:
    st.markdown('<div class="alert-danger">⚠ FIREBASE UNREACHABLE — check your network or database URL</div>',
                unsafe_allow_html=True)
    st.stop()

# ── Compute statuses ──────────────────────────────────────────────────────────
values = {k: row[k] for k in ["ph", "tds", "temperature", "turbidity"]}
statuses = {k: get_status(k, v) for k, v in values.items()}

worst = "safe"
if any(s == "danger" for s in statuses.values()):
    worst = "danger"
elif any(s == "warn" for s in statuses.values()):
    worst = "warn"

bad_params = [THRESHOLDS[k]["label"] for k, s in statuses.items() if s != "safe"]

# ── Alert banner ──────────────────────────────────────────────────────────────
if worst == "safe":
    st.markdown(
        '✅ &nbsp; ALL PARAMETERS WITHIN SAFE LIMITS — Water quality is GOOD',
        unsafe_allow_html=False,
    )
    st.markdown('<div class="alert-safe">✅ &nbsp; ALL PARAMETERS WITHIN SAFE LIMITS — Water quality is GOOD</div>',
                unsafe_allow_html=True)
elif worst == "warn":
    params_str = ", ".join(bad_params)
    st.markdown(f'<div class="alert-warn">▲ &nbsp; WARNING: {params_str} out of recommended range. Monitor closely.</div>',
                unsafe_allow_html=True)
else:
    params_str = ", ".join(bad_params)
    st.markdown(f'<div class="alert-danger">✖ &nbsp; CRITICAL ALERT: {params_str} at dangerous levels! Immediate action required.</div>',
                unsafe_allow_html=True)

# ── Metric cards ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">LIVE SENSOR READINGS</div>', unsafe_allow_html=True)

keys_order = ["ph", "tds", "temperature", "turbidity"]
cols = st.columns(4, gap="small")

for col, key in zip(cols, keys_order):
    cfg = THRESHOLDS[key]
    val = values[key]
    s   = statuses[key]
    card_class = f"metric-card {s if s != 'safe' else ''}"
    val_class  = s if s != "safe" else ""

    with col:
        st.markdown(f"""
        <div class="{card_class}">
          <div class="mc-icon">{cfg['icon']}</div>
          <div class="mc-label">{cfg['label']}</div>
          <div>
            <span class="mc-value {val_class}">{val:.3f}</span>
            <span class="mc-unit">{cfg['unit']}</span>
          </div>
          <div><span class="mc-status {s}">{status_label(s)}</span></div>
        </div>
        """, unsafe_allow_html=True)

# ── Gauge charts ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">SENSOR GAUGES</div>', unsafe_allow_html=True)
g_cols = st.columns(4, gap="small")
for col, key in zip(g_cols, keys_order):
    with col:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            make_gauge(key, values[key], statuses[key]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ── Trend charts ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">HISTORICAL TRENDS  <span style="font-size:0.6rem;color:#3a6080">(last 120 readings)</span></div>',
            unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2, gap="small")
r2c1, r2c2 = st.columns(2, gap="small")
trend_pairs = [
    (r1c1, "ph"),
    (r1c2, "temperature"),
    (r2c1, "tds"),
    (r2c2, "turbidity"),
]

for col, key in trend_pairs:
    cfg = THRESHOLDS[key]
    with col:
        st.markdown(
            f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.68rem;color:#3a6080;letter-spacing:1px;padding:4px 8px">'
            f'{cfg["icon"]} {cfg["label"].upper()}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            make_trend(key, history_df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ── Threshold reference table ─────────────────────────────────────────────────
with st.expander("📋  Safe Range Reference", expanded=False):
    ref_data = {
        "Parameter": [THRESHOLDS[k]["label"] for k in keys_order],
        "Current Value": [f"{values[k]:.3f} {THRESHOLDS[k]['unit']}" for k in keys_order],
        "Safe Min": [str(THRESHOLDS[k]["min"]) for k in keys_order],
        "Safe Max": [str(THRESHOLDS[k]["max"]) for k in keys_order],
        "Status": [status_label(statuses[k]) for k in keys_order],
    }
    ref_df = pd.DataFrame(ref_data)
    st.dataframe(ref_df, use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="aq-footer">
  AQUAWATCH MONITORING SYSTEM &nbsp;·&nbsp; FIREBASE RTDB &nbsp;·&nbsp;
  NODE: ASIA-SOUTHEAST1 &nbsp;·&nbsp; REFRESH CYCLE: 5 s
</div>
""", unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
time.sleep(5)
st.rerun()
