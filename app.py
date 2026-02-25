"""
app.py  —  PayGuard Operations Centre
Enterprise-grade Streamlit dashboard for the Automated Payment Troubleshooting System.

Run with:
    streamlit run app.py
"""

import os
import datetime
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PayGuard Operations Centre",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN SYSTEM — CSS
#
#  Aesthetic: Precision-industrial fintech ops centre.
#  Palette  : deep navy base · ice-blue accent · amber/red/green status signals
#  Type     : DM Mono (headers + data numerals) + DM Sans (body)
#  Motif    : controlled density, glowing borders, Bloomberg-meets-security-ops
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── Design tokens ──────────────────────────────────────────────────────── */
:root {
  --bg-base:        #080c14;
  --bg-surface:     #0d1220;
  --bg-raised:      #111827;
  --bg-overlay:     #1a2235;
  --border-subtle:  #1e2d47;
  --border-default: #243450;
  --border-strong:  #2d4166;

  --text-primary:   #e8edf5;
  --text-secondary: #8fa3c0;
  --text-muted:     #4d6380;

  --accent-blue:    #3d8ef0;
  --accent-glow:    rgba(61,142,240,0.10);
  --accent-ice:     #a8c8ff;

  --status-red:          #f05252;
  --status-red-bg:       rgba(240,82,82,0.07);
  --status-red-border:   rgba(240,82,82,0.22);

  --status-amber:        #f0a030;
  --status-amber-bg:     rgba(240,160,48,0.07);
  --status-amber-border: rgba(240,160,48,0.22);

  --status-green:        #34c77b;
  --status-green-bg:     rgba(52,199,123,0.07);
  --status-green-border: rgba(52,199,123,0.22);

  --gold:      #c8a84b;
  --gold-glow: rgba(200,168,75,0.15);

  --font-mono: 'DM Mono', 'Courier New', monospace;
  --font-sans: 'DM Sans', system-ui, sans-serif;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}

/* ── Global ─────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: var(--font-sans) !important;
  background-color: var(--bg-base);
  color: var(--text-primary);
}
.main .block-container {
  padding: 1.25rem 2rem 3rem 2rem !important;
  max-width: 1600px !important;
}
h1, h2, h3, h4, h5 {
  font-family: var(--font-mono) !important;
  letter-spacing: -0.02em;
  color: var(--text-primary) !important;
}
h1 { font-size: 1.5rem  !important; font-weight: 500 !important; }
h2 { font-size: 1.2rem  !important; font-weight: 400 !important; }
h3 { font-size: 1.0rem  !important; font-weight: 400 !important; }
h4 { font-size: 0.85rem !important; font-weight: 400 !important; }
p  { font-size: 0.85rem; color: var(--text-secondary); }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--bg-surface) !important;
  border-right: 1px solid var(--border-subtle) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0.75rem; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label { color: var(--text-secondary) !important; font-size: 0.78rem !important; }
[data-testid="stSidebar"] hr   { border-color: var(--border-subtle) !important; margin: 0.85rem 0; }

/* ── Metric cards ───────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
  background: var(--bg-raised) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem 1.1rem !important;
  position: relative;
  overflow: hidden;
  transition: border-color 0.18s ease;
}
[data-testid="metric-container"]:hover { border-color: var(--border-strong) !important; }
[data-testid="metric-container"]::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-blue) 0%, transparent 100%);
  opacity: 0.55;
}
[data-testid="metric-container"] label {
  font-family: var(--font-mono) !important;
  font-size: 0.62rem !important;
  font-weight: 400 !important;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--font-mono) !important;
  font-size: 1.4rem !important;
  font-weight: 500 !important;
  color: var(--text-primary) !important;
  line-height: 1.15;
}
[data-testid="stMetricDelta"] {
  font-family: var(--font-mono) !important;
  font-size: 0.65rem !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] { border-bottom: 1px solid var(--border-subtle); }
button[data-baseweb="tab"] {
  font-family: var(--font-mono) !important;
  font-size: 0.7rem !important;
  font-weight: 400 !important;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--text-muted) !important;
  background: transparent !important;
  border: none !important;
  padding: 0.7rem 1.1rem !important;
  transition: color 0.12s ease;
}
button[data-baseweb="tab"]:hover { color: var(--text-secondary) !important; }
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--accent-ice) !important;
  border-bottom: 2px solid var(--accent-blue) !important;
}
[data-testid="stTabPanel"] { padding-top: 1.25rem; }

/* ── Buttons ────────────────────────────────────────────────────────────── */
.stButton > button {
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border-default) !important;
  background: var(--bg-raised) !important;
  color: var(--text-secondary) !important;
  transition: all 0.13s ease;
}
.stButton > button:hover {
  border-color: var(--accent-blue) !important;
  color: var(--accent-ice) !important;
  background: var(--accent-glow) !important;
}
.stButton > button[kind="primary"] {
  background: var(--accent-blue) !important;
  border-color: var(--accent-blue) !important;
  color: #fff !important;
}
.stButton > button[kind="primary"]:hover {
  background: #4a9ef8 !important;
}

/* ── Form inputs ────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > textarea {
  font-family: var(--font-mono) !important;
  font-size: 0.8rem !important;
  background: var(--bg-raised) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
}
.stSelectbox > div > div > div { color: var(--text-primary) !important; }

/* ── Dataframes ─────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden;
}
[data-testid="stDataFrame"] th {
  background: var(--bg-overlay) !important;
  color: var(--text-muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-family: var(--font-mono) !important;
  font-size: 0.62rem !important;
  border-bottom: 1px solid var(--border-default) !important;
}
[data-testid="stDataFrame"] td {
  font-family: var(--font-mono) !important;
  font-size: 0.76rem !important;
  border-color: var(--border-subtle) !important;
}

/* ── Expanders ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-surface) !important;
  margin-bottom: 5px !important;
  overflow: hidden;
  transition: border-color 0.13s ease;
}
[data-testid="stExpander"]:hover { border-color: var(--border-default) !important; }
[data-testid="stExpander"] summary {
  font-family: var(--font-mono) !important;
  font-size: 0.76rem !important;
  color: var(--text-secondary) !important;
  padding: 0.55rem 0.85rem !important;
}
[data-testid="stExpanderDetails"] {
  background: var(--bg-raised) !important;
  border-top: 1px solid var(--border-subtle) !important;
  padding: 0.9rem !important;
}

/* ── Code blocks ────────────────────────────────────────────────────────── */
.stCode > div, pre {
  background: var(--bg-base) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  color: #7eb8f7 !important;
}

/* ── Misc Streamlit ─────────────────────────────────────────────────────── */
hr { border-color: var(--border-subtle) !important; margin: 1.25rem 0 !important; }
.stCaption, [data-testid="stCaptionContainer"] {
  font-family: var(--font-mono) !important;
  font-size: 0.66rem !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.04em;
}
[data-testid="stRadio"] label {
  font-family: var(--font-mono) !important;
  font-size: 0.76rem !important;
  color: var(--text-secondary) !important;
}
[data-testid="stSpinner"] > div { border-top-color: var(--accent-blue) !important; }
[data-testid="stSlider"] > div > div > div { background: var(--accent-blue) !important; }

/* ══════════════════════════════════════════════════════════════════════════
   CUSTOM COMPONENT CLASSES
   ══════════════════════════════════════════════════════════════════════════ */

/* Header bar */
.pg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.5rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: 1.25rem;
  position: relative;
  overflow: hidden;
}
.pg-header::after {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--accent-blue) 40%, var(--gold) 70%, transparent 100%);
  opacity: 0.45;
}
.pg-logo {
  font-family: var(--font-mono);
  font-size: 1.3rem;
  font-weight: 500;
  color: var(--text-primary);
  letter-spacing: -0.03em;
}
.pg-logo span { color: var(--accent-blue); }
.pg-tagline {
  font-family: var(--font-mono);
  font-size: 0.64rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 3px;
}
.pg-header-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}
.pg-live-dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--status-green);
  box-shadow: 0 0 7px var(--status-green);
  margin-right: 5px;
  animation: blink 2.4s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.35} }
.pg-timestamp {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted);
}
.pg-model-badge {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  color: var(--accent-blue);
  background: var(--accent-glow);
  border: 1px solid rgba(61,142,240,0.2);
  border-radius: 3px;
  padding: 2px 8px;
  letter-spacing: 0.05em;
}

/* Section label */
.pg-section-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.62rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.13em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.4rem;
  margin: 1.5rem 0 0.9rem 0;
}
.pg-section-label::before {
  content: '';
  display: block;
  width: 3px;
  height: 11px;
  background: var(--gold);
  border-radius: 2px;
  flex-shrink: 0;
}

/* Mode panel header */
.pg-mode-header {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 1rem;
  border-radius: var(--radius-md);
  margin: 0.75rem 0;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.03em;
}
.pg-mode-header.red   { background: var(--status-red-bg);   border: 1px solid var(--status-red-border);   color: var(--status-red);   }
.pg-mode-header.amber { background: var(--status-amber-bg); border: 1px solid var(--status-amber-border); color: var(--status-amber); }
.pg-mode-header.green { background: var(--status-green-bg); border: 1px solid var(--status-green-border); color: var(--status-green); }
.pg-mode-count   { font-size: 1.0rem; font-weight: 500; margin-left: auto; }
.pg-mode-impact  { font-size: 0.67rem; opacity: 0.72; }

/* Incident detail grid */
.pg-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem 1.25rem;
  margin-bottom: 0.65rem;
}
.pg-detail-row  { font-family: var(--font-mono); font-size: 0.73rem; display: flex; gap: 0.4rem; align-items: baseline; }
.pg-detail-key  { color: var(--text-muted); font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.07em; white-space: nowrap; flex-shrink: 0; }
.pg-detail-val  { color: var(--text-primary); }

/* Confidence pill */
.conf-pill { font-family: var(--font-mono); font-size: 0.63rem; padding: 1px 6px; border-radius: 3px; display: inline-block; }
.conf-high { color: var(--status-green); background: var(--status-green-bg); border: 1px solid var(--status-green-border); }
.conf-med  { color: var(--status-amber); background: var(--status-amber-bg); border: 1px solid var(--status-amber-border); }
.conf-low  { color: var(--status-red);   background: var(--status-red-bg);   border: 1px solid var(--status-red-border);   }

/* Action box */
.pg-action-box {
  background: var(--bg-overlay);
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--accent-blue);
  border-radius: var(--radius-sm);
  padding: 0.55rem 0.8rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--accent-ice);
  line-height: 1.5;
  margin-top: 0.5rem;
}

/* Sidebar branding */
.pg-sidebar-logo {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  padding: 0.35rem 0 0.2rem 0;
}
.pg-sidebar-logo span { color: var(--accent-blue); }
.pg-sidebar-tagline {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.11em;
  margin-bottom: 0.4rem;
}
.pg-sidebar-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-mono);
  font-size: 0.68rem;
}
.pg-sidebar-stat-key { color: var(--text-muted); }
.pg-sidebar-stat-val { color: var(--text-primary); font-weight: 500; }

/* Section headers in sidebar */
.pg-sb-section {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.11em;
  color: var(--text-muted);
  margin: 0.9rem 0 0.45rem 0;
}

/* Empty / idle state */
.pg-empty-state {
  text-align: center;
  padding: 3rem 1rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-muted);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-md);
  line-height: 1.8;
}
.pg-empty-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

/* Chart card wrapper */
.pg-chart-card {
  background: var(--bg-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 0.9rem 1rem;
}
.pg-chart-title {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 0.65rem;
}

/* Feedback form card */
.pg-form-card {
  background: var(--bg-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 1rem 1.1rem;
  margin-bottom: 0.5rem;
}
.pg-form-label { font-family: var(--font-mono); font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 2px; }
.pg-form-value { font-family: var(--font-mono); font-size: 0.82rem; color: var(--text-primary); margin-bottom: 0.55rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  BACKEND IMPORTS  (zero changes to any backend module)
# ─────────────────────────────────────────────────────────────────────────────
from data_generator import generate_dataset
from pipeline import (
    run_pipeline, ensure_model_trained,
    get_automation_metrics, detect_repeat_atms,
    ML_CONFIDENCE_THRESHOLD,
)
from impact_scorer import impact_label
from feedback_store import save_feedback, load_feedback, get_accuracy_summary
from log_store import load_logs, get_log_summary


# ─────────────────────────────────────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Initialising ML model…")
def boot_model():
    ensure_model_trained()
    return True


def fmt_inr(val: float) -> str:
    if val >= 1_000_000:
        return f"₹{val/1_000_000:.2f}M"
    elif val >= 1_000:
        return f"₹{val/1_000:.1f}K"
    return f"₹{val:.0f}"


def conf_pill_html(conf: float) -> str:
    cls = "conf-high" if conf >= 0.8 else ("conf-med" if conf >= 0.6 else "conf-low")
    return f'<span class="conf-pill {cls}">{conf:.0%}</span>'


def section_label(icon: str, text: str) -> None:
    st.markdown(
        f'<div class="pg-section-label">{icon}&nbsp; {text}</div>',
        unsafe_allow_html=True,
    )


def render_incident_card(row: pd.Series) -> None:
    """Fully styled incident detail expander card."""
    conf   = row.get("ml_confidence", 1.0)
    impact = row["impact_score"]
    sev    = impact_label(impact)

    title = (
        f"{row['atm_id']}  ·  {row['location']}  ·  "
        f"{row['predicted_issue'].replace('_',' ').title()}  ·  "
        f"{sev}  ₹{impact:,.0f}"
    )

    with st.expander(title, expanded=False):
        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown(
                f"""
                <div class="pg-detail-grid">
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Issue</span>
                    <span class="pg-detail-val">{row['predicted_issue'].replace('_',' ').title()}</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Downtime</span>
                    <span class="pg-detail-val">{row['downtime_minutes']} min</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Volume</span>
                    <span class="pg-detail-val">{row['transaction_volume']:,} txns</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Avg Value</span>
                    <span class="pg-detail-val">₹{row['avg_amount']:,.0f}</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Complaints</span>
                    <span class="pg-detail-val">{row['complaint_count']}</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Confidence</span>
                    <span class="pg-detail-val">{conf_pill_html(conf)}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right_col:
            gate = row.get("eligibility_reason", "")
            st.markdown(
                f"""
                <div class="pg-detail-grid">
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Team</span>
                    <span class="pg-detail-val">{row['responsible_team']}</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">SLA</span>
                    <span class="pg-detail-val">{row['sla_minutes']} min</span>
                  </div>
                  <div class="pg-detail-row">
                    <span class="pg-detail-key">Escalation</span>
                    <span class="pg-detail-val" style="font-size:0.68rem">{row['escalation_status']}</span>
                  </div>
                  {f'<div class="pg-detail-row"><span class="pg-detail-key">Auto Gate</span><span class="pg-detail-val" style="color:var(--text-secondary);font-size:0.68rem">{gate}</span></div>' if gate else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Recommended action
        st.markdown(
            f'<div class="pg-action-box">⚡&nbsp; {row["recommended_action"]}</div>',
            unsafe_allow_html=True,
        )

        # Automation log
        if row.get("automation_log"):
            st.code(row["automation_log"], language=None)


def render_mode_panel(
    df: pd.DataFrame,
    mode: str,
    color: str,
    icon: str,
    title: str,
    avg_time_label: str | None = None,
) -> None:
    """Full resolution-mode panel: coloured header, mini KPIs, incident cards."""
    subset       = df[df["resolution_mode"] == mode]
    count        = len(subset)
    total_impact = subset["impact_score"].sum() if count else 0
    avg_impact   = subset["impact_score"].mean() if count else 0

    avg_t_str = "—"
    if avg_time_label and count and "auto_resolution_time_sec" in subset.columns:
        vals = subset[subset["auto_resolution_time_sec"] > 0]["auto_resolution_time_sec"]
        if len(vals):
            avg_t_str = f"{vals.mean():.0f}s"

    st.markdown(
        f"""<div class="pg-mode-header {color}">
              <span style="font-size:1.05rem">{icon}</span>
              <span style="font-weight:500;letter-spacing:0.03em">{title}</span>
              <span class="pg-mode-count">{count}</span>
              <span class="pg-mode-impact">₹{total_impact:,.0f} total exposure</span>
            </div>""",
        unsafe_allow_html=True,
    )

    if count == 0:
        st.markdown(
            '<div class="pg-empty-state" style="padding:1.5rem">'
            '<span class="pg-empty-icon" style="font-size:1.2rem">✓</span>'
            'No incidents in this category for this run.</div>',
            unsafe_allow_html=True,
        )
        return

    mk1, mk2, mk3, mk4 = st.columns(4)
    mk1.metric("Incidents",       count)
    mk2.metric("Total Exposure",  fmt_inr(total_impact))
    mk3.metric("Avg Exposure",    fmt_inr(avg_impact))
    if avg_time_label:
        mk4.metric(avg_time_label, avg_t_str)
    else:
        top = subset["predicted_issue"].value_counts().idxmax().replace("_"," ").title()
        mk4.metric("Top Issue", top)

    st.markdown(
        f'<div style="font-family:var(--font-mono);font-size:0.65rem;'
        f'color:var(--text-muted);margin:0.5rem 0 0.35rem 0;">'
        f'{count} incident(s) — sorted by financial exposure, highest first</div>',
        unsafe_allow_html=True,
    )
    for _, row in subset.sort_values("impact_score", ascending=False).iterrows():
        render_incident_card(row)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="pg-sidebar-logo">Pay<span>Guard</span></div>'
        '<div class="pg-sidebar-tagline">Operations Centre · v2.0</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<div class="pg-sb-section">⚙ Configuration</div>', unsafe_allow_html=True)
    confidence_threshold = st.slider(
        "ML Confidence Floor",
        min_value=0.40, max_value=0.95,
        value=ML_CONFIDENCE_THRESHOLD, step=0.05,
        help="Predictions below this threshold are forced to MANUAL_REQUIRED",
    )
    st.caption(f"Below {confidence_threshold:.0%} → MANUAL_REQUIRED")

    st.divider()
    st.markdown('<div class="pg-sb-section">◈ Data Source</div>', unsafe_allow_html=True)
    mode = st.radio(
        "input_mode",
        ["Generate Demo Data", "Upload CSV", "Manual Entry"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown('<div class="pg-sb-section">◈ System Telemetry</div>', unsafe_allow_html=True)
    stats    = get_accuracy_summary()
    log_stat = get_log_summary()

    def _sb_stat(k, v):
        st.markdown(
            f'<div class="pg-sidebar-stat">'
            f'<span class="pg-sidebar-stat-key">{k}</span>'
            f'<span class="pg-sidebar-stat-val">{v}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _sb_stat("Log archive",          f"{log_stat['total_logged']:,} records")
    _sb_stat("Auto-resolved (all)",  f"{log_stat['auto_resolved']:,}")
    _sb_stat("Avg auto-resolve",     f"{log_stat['avg_auto_time_sec']:.0f}s")
    _sb_stat("Feedback records",     f"{stats['total']:,}")
    if stats["total"] > 0:
        _sb_stat("Technician accuracy", f"{stats['accuracy']}%")

    st.divider()
    st.markdown(
        '<div style="font-family:var(--font-mono);font-size:0.58rem;'
        'color:var(--text-muted);line-height:1.7;padding:0.25rem 0;">'
        'RandomForest · Rule Engine<br>'
        'Automation Layer · Feedback Loop<br>'
        'Fully Offline · No Cloud APIs'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER BAR
# ─────────────────────────────────────────────────────────────────────────────
boot_model()
now_str = datetime.datetime.now().strftime("%d %b %Y  %H:%M")

st.markdown(
    f"""
    <div class="pg-header">
      <div>
        <div class="pg-logo">Pay<span>Guard</span>&nbsp;OPS</div>
        <div class="pg-tagline">Automated Payment Incident Intelligence Platform</div>
      </div>
      <div class="pg-header-right">
        <div class="pg-timestamp">
          <span class="pg-live-dot"></span>LIVE &nbsp;·&nbsp; {now_str}
        </div>
        <div class="pg-model-badge">RandomForest · 5-Layer Pipeline</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
#  DATA INPUT
# ─────────────────────────────────────────────────────────────────────────────
raw_df = None

if mode == "Generate Demo Data":
    inp_col, btn_col = st.columns([5, 1])
    with inp_col:
        n = st.slider("Incident batch size", 10, 200, 50,
                      help="Number of synthetic ATM incidents to generate")
    with btn_col:
        st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        generate_btn = st.button("⚡ Run Analysis", type="primary", use_container_width=True)

    if generate_btn or "demo_df" in st.session_state:
        if generate_btn:
            with st.spinner("Generating batch and running 5-layer pipeline…"):
                raw_df = generate_dataset(n)
                st.session_state["demo_df"] = raw_df
        else:
            raw_df = st.session_state["demo_df"]

elif mode == "Upload CSV":
    st.caption("Required columns: atm_id · location · hour_of_day · transaction_volume · avg_amount · downtime_minutes · complaint_count · error_code")
    uploaded = st.file_uploader("Drop CSV file here", type=["csv"], label_visibility="collapsed")
    if uploaded:
        raw_df = pd.read_csv(uploaded)
        st.success(f"Loaded {len(raw_df):,} rows from {uploaded.name}")

elif mode == "Manual Entry":
    section_label("✏", "Single Incident Entry")
    c1, c2, c3 = st.columns(3)
    with c1:
        atm_id   = st.text_input("ATM ID",   "ATM-5432")
        location = st.text_input("Location", "Mumbai Central")
        hour     = st.slider("Hour of Day", 0, 23, 14)
    with c2:
        volume   = st.number_input("Transaction Volume", 1, 500, 80)
        avg_amt  = st.number_input("Avg Amount (₹)", 100.0, 10000.0, 2500.0)
        downtime = st.number_input("Downtime (minutes)", 0, 600, 90)
    with c3:
        complaints = st.number_input("Complaint Count", 0, 100, 15)
        error_code = st.selectbox("Error Code", [
            "E001","E002","E003","E010","E011","E012",
            "E020","E021","E022","E030","E031","E040","E041","E042",
        ])
        st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
        run_manual = st.button("🔍 Analyse Incident", type="primary", use_container_width=True)

    if run_manual:
        raw_df = pd.DataFrame([{
            "atm_id": atm_id, "location": location, "hour_of_day": hour,
            "transaction_volume": volume, "avg_amount": avg_amt,
            "downtime_minutes": downtime, "complaint_count": complaints,
            "error_code": error_code,
        }])


# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS  — tab-based layout
# ─────────────────────────────────────────────────────────────────────────────
if raw_df is not None:
    with st.spinner("Running pipeline: classify → score → escalate → automate → persist…"):
        result_df   = run_pipeline(raw_df, confidence_threshold=confidence_threshold)
    st.session_state["result_df"] = result_df

    auto_metrics  = get_automation_metrics(result_df)
    repeat_df     = detect_repeat_atms(result_df)
    total         = len(result_df)
    escalated_n   = result_df["escalation_status"].str.contains("ESCALATED").sum()
    total_impact  = result_df["impact_score"].sum()
    top_issue     = result_df["predicted_issue"].value_counts().idxmax()
    avg_downtime  = result_df["downtime_minutes"].mean()

    TAB_OV, TAB_MR, TAB_AA, TAB_AR, TAB_LG, TAB_FB = st.tabs([
        "📊  Overview",
        "🔴  Manual Required",
        "🟡  Auto Attempted",
        "🟢  Auto Resolved",
        "📁  Log Archive",
        "🔁  Feedback",
    ])

    # ═════════════════════════════════════════════════════════════════════════
    #  OVERVIEW TAB
    # ═════════════════════════════════════════════════════════════════════════
    with TAB_OV:

        section_label("◈", "Run Summary")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Incidents",  total)
        k2.metric("Escalated",        escalated_n,
                  delta=f"{escalated_n/total:.0%} of batch",
                  delta_color="inverse")
        k3.metric("Total Exposure",   fmt_inr(total_impact))
        k4.metric("Dominant Issue",   top_issue.replace("_"," ").title())
        k5.metric("Avg Downtime",     f"{avg_downtime:.0f} min")

        section_label("🤖", "Automation Engine")
        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Auto-Resolved",
                  auto_metrics.get("auto_resolved_count", 0),
                  delta=f"{auto_metrics.get('auto_resolved_pct',0)}%",
                  delta_color="normal")
        a2.metric("Auto-Attempted",
                  auto_metrics.get("auto_attempted_count", 0),
                  delta=f"{auto_metrics.get('auto_attempted_pct',0)}% partial",
                  delta_color="off")
        a3.metric("Manual Required",
                  auto_metrics.get("manual_required_count", 0),
                  delta=f"{auto_metrics.get('manual_required_pct',0)}%",
                  delta_color="inverse")
        a4.metric("Avg Auto-Resolve", f"{auto_metrics.get('avg_auto_time_sec',0):.0f}s")
        a5.metric("Manual Saved",     f"{auto_metrics.get('manual_reduction_pct',0):.1f}%",
                  delta="vs 100% baseline", delta_color="normal")

        section_label("◈", "Operational Intelligence")
        b1, b2, b3, b4 = st.columns(4)
        saved_min = auto_metrics.get("downtime_saved_minutes", 0)
        b1.metric("Downtime Saved",
                  f"{saved_min:,} min",
                  delta=f"{saved_min/60:.1f} hrs",
                  delta_color="normal",
                  help="AUTO_RESOLVED count × 120 min manual baseline")
        b2.metric("Revenue Contained",
                  fmt_inr(auto_metrics.get("revenue_auto_contained", 0)),
                  help="Sum of impact_score for AUTO_RESOLVED incidents")
        b3.metric("Repeat ATMs",
                  auto_metrics.get("repeat_atm_count", 0),
                  delta="Flagged for review" if auto_metrics.get("repeat_atm_count",0) > 0 else "Clear",
                  delta_color="inverse" if auto_metrics.get("repeat_atm_count",0) > 0 else "off")
        b4.metric("Low-Confidence Flags",
                  auto_metrics.get("low_confidence_count", 0),
                  delta="Sent to manual" if auto_metrics.get("low_confidence_count",0) > 0 else "None",
                  delta_color="inverse" if auto_metrics.get("low_confidence_count",0) > 0 else "off",
                  help=f"Predictions below {confidence_threshold:.0%} threshold")

        # Repeat ATM table
        if not repeat_df.empty:
            section_label("⚠", "Repeat ATM Incidents Detected")
            repeat_rows = []
            for _, r in repeat_df.iterrows():
                atm_rows = result_df[result_df["atm_id"] == r["atm_id"]]
                repeat_rows.append({
                    "ATM ID":       r["atm_id"],
                    "# Incidents":  r["incident_count"],
                    "Issue Types":  ", ".join(atm_rows["predicted_issue"].str.replace("_"," ").str.title().unique()),
                    "Modes":        ", ".join(atm_rows["resolution_mode"].unique()),
                    "Total Impact": fmt_inr(atm_rows["impact_score"].sum()),
                })
            st.dataframe(pd.DataFrame(repeat_rows), use_container_width=True, hide_index=True)

        # Charts
        section_label("◈", "Distribution Analytics")
        ch1, ch2, ch3 = st.columns(3)

        with ch1:
            st.markdown('<div class="pg-chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="pg-chart-title">Incidents by Issue Type</div>', unsafe_allow_html=True)
            ic = result_df["predicted_issue"].value_counts().reset_index()
            ic.columns = ["Issue", "Count"]
            st.bar_chart(ic.set_index("Issue"), height=195, color="#3d8ef0")
            st.markdown('</div>', unsafe_allow_html=True)

        with ch2:
            st.markdown('<div class="pg-chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="pg-chart-title">Financial Exposure by Issue Type (₹)</div>', unsafe_allow_html=True)
            imp = (result_df.groupby("predicted_issue")["impact_score"]
                   .sum().sort_values(ascending=False).reset_index())
            imp.columns = ["Issue", "Impact"]
            st.bar_chart(imp.set_index("Issue"), height=195, color="#c8a84b")
            st.markdown('</div>', unsafe_allow_html=True)

        with ch3:
            st.markdown('<div class="pg-chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="pg-chart-title">Resolution Mode Split</div>', unsafe_allow_html=True)
            mode_order = {"MANUAL_REQUIRED": 0, "AUTO_ATTEMPTED": 1, "AUTO_RESOLVED": 2}
            mc = result_df["resolution_mode"].value_counts().reset_index()
            mc.columns = ["Mode", "Count"]
            mc["_o"] = mc["Mode"].map(mode_order).fillna(3)
            mc = mc.sort_values("_o").drop(columns=["_o"])
            st.bar_chart(mc.set_index("Mode"), height=195, color="#34c77b")
            st.markdown('</div>', unsafe_allow_html=True)

        # Export
        section_label("⬇", "Export")
        dl_cols = [
            "atm_id", "location", "predicted_issue", "ml_confidence",
            "impact_score", "downtime_minutes", "resolution_mode",
            "recommended_action", "responsible_team", "sla_minutes",
            "escalation_status", "eligibility_reason", "automation_log",
        ]
        csv_out = result_df[[c for c in dl_cols if c in result_df.columns]].to_csv(index=False)
        st.download_button(
            "⬇  Download Full Results (CSV)",
            csv_out, file_name="payguard_results.csv", mime="text/csv",
        )

    # ═════════════════════════════════════════════════════════════════════════
    #  MANUAL REQUIRED TAB
    # ═════════════════════════════════════════════════════════════════════════
    with TAB_MR:
        st.caption("Incidents that require immediate human intervention — escalated, high-impact, or ineligible for automation.")
        render_mode_panel(
            result_df, "MANUAL_REQUIRED",
            color="red", icon="🔴",
            title="MANUAL REQUIRED — Human Intervention Needed",
        )

    # ═════════════════════════════════════════════════════════════════════════
    #  AUTO ATTEMPTED TAB
    # ═════════════════════════════════════════════════════════════════════════
    with TAB_AA:
        st.caption("Automation was triggered and executed but did not fully resolve the issue. Routed to the responsible team with full diagnostic context.")
        render_mode_panel(
            result_df, "AUTO_ATTEMPTED",
            color="amber", icon="🟡",
            title="AUTO ATTEMPTED — Partial Automation, Human Handoff",
            avg_time_label="Avg Attempt Time",
        )

    # ═════════════════════════════════════════════════════════════════════════
    #  AUTO RESOLVED TAB
    # ═════════════════════════════════════════════════════════════════════════
    with TAB_AR:
        st.caption("Fully automated remediation. Closed by the automation engine. No human intervention required.")
        render_mode_panel(
            result_df, "AUTO_RESOLVED",
            color="green", icon="🟢",
            title="AUTO RESOLVED — System Remediated Successfully",
            avg_time_label="Avg Resolve Time",
        )

    # ═════════════════════════════════════════════════════════════════════════
    #  LOG ARCHIVE TAB
    # ═════════════════════════════════════════════════════════════════════════
    with TAB_LG:
        section_label("📁", "Persistent Automation Log Archive")
        log_df = load_logs()

        if log_df.empty:
            st.markdown(
                '<div class="pg-empty-state"><span class="pg-empty-icon">📭</span>'
                'No log records yet. Run an analysis to populate the archive.</div>',
                unsafe_allow_html=True,
            )
        else:
            lk1, lk2, lk3, lk4 = st.columns(4)
            lk1.metric("Total Records",   f"{len(log_df):,}")
            lk2.metric("Auto-Resolved",   f"{(log_df['resolution_mode']=='AUTO_RESOLVED').sum():,}")
            lk3.metric("Auto-Attempted",  f"{(log_df['resolution_mode']=='AUTO_ATTEMPTED').sum():,}")
            lk4.metric("Manual Required", f"{(log_df['resolution_mode']=='MANUAL_REQUIRED').sum():,}")

            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
            fc, _ = st.columns([2, 3])
            with fc:
                filter_mode = st.selectbox(
                    "Filter by mode",
                    ["All", "AUTO_RESOLVED", "AUTO_ATTEMPTED", "MANUAL_REQUIRED"],
                    key="log_filter",
                )
            view_df = log_df if filter_mode == "All" else log_df[log_df["resolution_mode"] == filter_mode]
            disp = view_df[[
                "timestamp", "atm_id", "predicted_issue", "impact_score",
                "resolution_mode", "auto_resolution_time_sec", "eligibility_reason",
            ]].copy()
            disp["impact_score"] = disp["impact_score"].apply(lambda x: f"₹{x:,.0f}")
            disp = disp.rename(columns={
                "timestamp": "Timestamp", "atm_id": "ATM ID",
                "predicted_issue": "Issue", "impact_score": "Impact",
                "resolution_mode": "Mode",
                "auto_resolution_time_sec": "Auto Time (s)",
                "eligibility_reason": "Automation Gate",
            })
            st.dataframe(disp.tail(50), use_container_width=True, hide_index=True, height=400)
            st.download_button(
                "⬇  Download Full Log Archive (CSV)",
                log_df.to_csv(index=False),
                file_name="payguard_automation_logs.csv", mime="text/csv",
            )

    # ═════════════════════════════════════════════════════════════════════════
    #  FEEDBACK TAB
    # ═════════════════════════════════════════════════════════════════════════
    with TAB_FB:
        section_label("🔁", "Technician Feedback Loop")
        st.caption("Submit corrections to improve model accuracy over time. Feedback is written to data/feedback.csv.")

        result_df_saved = st.session_state.get("result_df", None)

        if result_df_saved is None:
            st.markdown(
                '<div class="pg-empty-state"><span class="pg-empty-icon">📋</span>'
                'Run an analysis first to enable feedback submission.</div>',
                unsafe_allow_html=True,
            )
        else:
            feedback_candidates = result_df_saved[
                result_df_saved["resolution_mode"].isin(["MANUAL_REQUIRED", "AUTO_ATTEMPTED"])
            ]
            if feedback_candidates.empty:
                feedback_candidates = result_df_saved

            fb_col1, fb_col2 = st.columns(2)

            with fb_col1:
                section_label("◈", "Select Incident")
                fb_atm  = st.selectbox("ATM ID", feedback_candidates["atm_id"].tolist(), key="fb_atm_select")
                matched = feedback_candidates[feedback_candidates["atm_id"] == fb_atm].iloc[0]
                st.markdown(
                    f"""
                    <div class="pg-form-card">
                      <div class="pg-form-label">Predicted Issue</div>
                      <div class="pg-form-value">{matched['predicted_issue'].replace('_',' ').title()}</div>
                      <div class="pg-form-label">Resolution Mode</div>
                      <div class="pg-form-value">{matched['resolution_mode']}</div>
                      <div class="pg-form-label">ML Confidence</div>
                      <div class="pg-form-value">{matched.get('ml_confidence', 1.0):.1%}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with fb_col2:
                section_label("◈", "Technician Assessment")
                ISSUE_TYPES = ["network_failure","card_declined","hardware_fault","cash_out","auth_timeout"]
                fb_actual   = st.selectbox(
                    "Actual Issue Diagnosed", ISSUE_TYPES,
                    index=ISSUE_TYPES.index(matched["predicted_issue"])
                          if matched["predicted_issue"] in ISSUE_TYPES else 0,
                    key="fb_actual",
                )
                fb_helpful  = st.radio(
                    "Was recommended action helpful?",
                    ["yes","partial","no"], horizontal=True, key="fb_helpful",
                )
                fb_res_time = st.number_input("Resolution Time (min)", 0, 600, 30, key="fb_res")
                fb_notes    = st.text_area("Notes (optional)", key="fb_notes", height=80)
                if st.button("✅  Submit Feedback", type="primary"):
                    save_feedback(
                        atm_id=fb_atm,
                        predicted_issue=matched["predicted_issue"],
                        technician_actual_issue=fb_actual,
                        action_helpful=fb_helpful,
                        technician_notes=fb_notes,
                        resolution_time_minutes=fb_res_time,
                    )
                    st.success("Feedback recorded successfully.")
                    st.rerun()

        feedback_df = load_feedback()
        if not feedback_df.empty:
            section_label("◈", "Feedback History (last 20)")
            st.dataframe(feedback_df.tail(20), use_container_width=True, hide_index=True, height=280)

# ─────────────────────────────────────────────────────────────────────────────
#  IDLE STATE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown(
        """
        <div class="pg-empty-state" style="margin-top:1.5rem; padding:4rem 2rem;">
          <span class="pg-empty-icon">🛡️</span>
          <div style="font-size:0.88rem;color:var(--text-secondary);margin-bottom:0.4rem;font-family:var(--font-mono);">
            PayGuard Operations Centre
          </div>
          <div>Select a data source in the sidebar and click <strong>Run Analysis</strong> to begin.</div>
          <div style="margin-top:0.85rem;font-size:0.62rem;color:var(--text-muted);letter-spacing:0.06em;">
            CLASSIFY &nbsp;·&nbsp; SCORE &nbsp;·&nbsp; ESCALATE &nbsp;·&nbsp; AUTOMATE &nbsp;·&nbsp; LOG
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
