"""
app.py
Streamlit dashboard — PayGuard Automated Troubleshooting System.

Run with:
    streamlit run app.py
"""

import os
import pandas as pd
import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PayGuard — ATM Troubleshooter",
    page_icon="🏧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace !important; }

[data-testid="metric-container"] {
    background: #0f1117;
    border: 1px solid #1e2530;
    border-radius: 8px;
    padding: 16px;
}
[data-testid="stSidebar"] {
    background: #0a0d12;
    border-right: 1px solid #1e2530;
}
.section-header {
    border-left: 3px solid #ffd700;
    padding-left: 12px;
    margin: 24px 0 12px 0;
}
.mode-header-green {
    border-left: 4px solid #3ddc84;
    padding-left: 12px;
    background: #3ddc8408;
    border-radius: 0 6px 6px 0;
    margin: 16px 0 8px 0;
    padding-top: 6px;
    padding-bottom: 6px;
}
.mode-header-amber {
    border-left: 4px solid #ffaa00;
    padding-left: 12px;
    background: #ffaa0008;
    border-radius: 0 6px 6px 0;
    margin: 16px 0 8px 0;
    padding-top: 6px;
    padding-bottom: 6px;
}
.mode-header-red {
    border-left: 4px solid #ff4444;
    padding-left: 12px;
    background: #ff444408;
    border-radius: 0 6px 6px 0;
    margin: 16px 0 8px 0;
    padding-top: 6px;
    padding-bottom: 6px;
}
.repeat-warning {
    background: #ff880015;
    border: 1px solid #ff880040;
    border-radius: 6px;
    padding: 10px 14px;
    color: #ffaa44;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)


# ── Module Imports ─────────────────────────────────────────────────────────────
from data_generator import generate_dataset
from pipeline import (
    run_pipeline, ensure_model_trained,
    get_automation_metrics, detect_repeat_atms,
    ML_CONFIDENCE_THRESHOLD,
)
from impact_scorer import impact_label
from feedback_store import save_feedback, load_feedback, get_accuracy_summary
from log_store import load_logs, get_log_summary


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Training ML model…")
def boot_model():
    ensure_model_trained()
    return True


def fmt_inr(val: float) -> str:
    if val >= 1_000_000:
        return f"₹{val/1_000_000:.1f}M"
    elif val >= 1_000:
        return f"₹{val/1_000:.1f}K"
    return f"₹{val:.0f}"


def render_incident_card(row: pd.Series, show_log: bool = True) -> None:
    """Render a single incident expander card with full detail."""
    confidence_str = f" | Conf: {row.get('ml_confidence', 1.0):.0%}" if "ml_confidence" in row else ""
    label = (
        f"{row['atm_id']} — {row['location']} | "
        f"{row['predicted_issue'].replace('_',' ').title()} | "
        f"{impact_label(row['impact_score'])} ₹{row['impact_score']:,.0f}"
        f"{confidence_str}"
    )
    with st.expander(label):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Issue Type:** {row['predicted_issue'].replace('_',' ').title()}")
            st.write(f"**Downtime:** {row['downtime_minutes']} min")
            st.write(f"**Transactions Affected:** {row['transaction_volume']}")
            st.write(f"**Avg Transaction Value:** ₹{row['avg_amount']:,.0f}")
            st.write(f"**Complaints:** {row['complaint_count']}")
            if "ml_confidence" in row:
                conf = row["ml_confidence"]
                conf_color = "🟢" if conf >= 0.8 else ("🟡" if conf >= 0.6 else "🔴")
                st.write(f"**ML Confidence:** {conf_color} {conf:.1%}")
        with c2:
            st.write(f"**Responsible Team:** {row['responsible_team']}")
            st.write(f"**SLA:** {row['sla_minutes']} min")
            st.write(f"**Escalation:** {row['escalation_status']}")
            if row.get("eligibility_reason"):
                st.write(f"**Automation Gate:** {row['eligibility_reason']}")
            st.info(f"**Action:** {row['recommended_action']}")
        if show_log and row.get("automation_log"):
            st.code(row["automation_log"], language=None)


def render_mode_section(
    df: pd.DataFrame,
    mode: str,
    header_html: str,
    avg_time_label: str | None = None,
) -> None:
    """Render a full resolution-mode section: header, KPIs, incident cards."""
    subset = df[df["resolution_mode"] == mode]
    st.markdown(header_html, unsafe_allow_html=True)

    if subset.empty:
        st.info(f"No {mode} incidents in this run.")
        return

    count        = len(subset)
    total_impact = subset["impact_score"].sum()
    avg_impact   = subset["impact_score"].mean()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Incidents", count)
    m2.metric("Total Impact", fmt_inr(total_impact))
    m3.metric("Avg Impact", fmt_inr(avg_impact))

    if avg_time_label and "auto_resolution_time_sec" in subset.columns:
        avg_t = subset[subset["auto_resolution_time_sec"] > 0]["auto_resolution_time_sec"].mean()
        m4.metric(avg_time_label, f"{avg_t:.0f}s" if pd.notna(avg_t) else "—")
    else:
        m4.metric("Issues", subset["predicted_issue"].value_counts().idxmax().replace("_", " ").title())

    st.markdown(f"**{count} incident(s) — sorted by impact (highest first)**")
    for _, row in subset.sort_values("impact_score", ascending=False).iterrows():
        render_incident_card(row, show_log=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏧 PayGuard")
    st.markdown("*ATM Incident Prioritiser*")
    st.divider()

    st.markdown("### ⚙️ Settings")
    confidence_threshold = st.slider(
        "ML Confidence Threshold",
        min_value=0.40, max_value=0.95, value=ML_CONFIDENCE_THRESHOLD, step=0.05,
        help="Predictions below this value are forced to MANUAL_REQUIRED",
    )
    st.caption(f"Current: {confidence_threshold:.0%} — below this → MANUAL_REQUIRED")
    st.divider()

    st.markdown("### 📊 Input Mode")
    mode = st.radio("Choose input", ["Generate Demo Data", "Upload CSV", "Manual Entry"])
    st.divider()

    # Feedback stats
    stats = get_accuracy_summary()
    st.markdown("### 🔁 Feedback")
    if stats["total"] > 0:
        st.metric("Records", stats["total"])
        st.metric("Technician Accuracy", f"{stats['accuracy']}%")
    else:
        st.caption("No feedback yet.")
    st.divider()

    # Historical log summary
    log_stats = get_log_summary()
    st.markdown("### 📁 Log Archive")
    if log_stats["total_logged"] > 0:
        st.metric("Total Logged", log_stats["total_logged"])
        st.metric("Auto-Resolved (hist.)", log_stats["auto_resolved"])
        st.metric("Avg Auto Time", f"{log_stats['avg_auto_time_sec']:.0f}s")
    else:
        st.caption("No logs yet.")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏧 PayGuard — Automated Troubleshooting System")
st.markdown("**Impact-Based Incident Classification & Prioritisation for Digital Payment Failures**")
st.divider()

boot_model()

# ── Data Input ────────────────────────────────────────────────────────────────
raw_df = None

if mode == "Generate Demo Data":
    col1, col2 = st.columns([3, 1])
    with col1:
        n = st.slider("Number of incidents to generate", 10, 200, 50)
    with col2:
        st.write(""); st.write("")
        generate_btn = st.button("⚡ Generate & Analyse", type="primary", use_container_width=True)

    if generate_btn or "demo_df" in st.session_state:
        if generate_btn:
            with st.spinner("Generating incidents…"):
                raw_df = generate_dataset(n)
                st.session_state["demo_df"] = raw_df
        else:
            raw_df = st.session_state["demo_df"]

elif mode == "Upload CSV":
    st.markdown("**Required columns:** `atm_id, location, hour_of_day, transaction_volume, avg_amount, downtime_minutes, complaint_count, error_code`")
    uploaded = st.file_uploader("Upload incident CSV", type=["csv"])
    if uploaded:
        raw_df = pd.read_csv(uploaded)
        st.success(f"Loaded {len(raw_df)} rows.")

elif mode == "Manual Entry":
    st.markdown("#### Enter Single Incident")
    c1, c2, c3 = st.columns(3)
    with c1:
        atm_id   = st.text_input("ATM ID", "ATM-5432")
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
            "E020","E021","E022","E030","E031","E040","E041","E042"
        ])
        run_manual = st.button("🔍 Analyse Incident", type="primary")

    if run_manual:
        raw_df = pd.DataFrame([{
            "atm_id": atm_id, "location": location, "hour_of_day": hour,
            "transaction_volume": volume, "avg_amount": avg_amt,
            "downtime_minutes": downtime, "complaint_count": complaints,
            "error_code": error_code,
        }])


# ── Pipeline + Results ────────────────────────────────────────────────────────
if raw_df is not None:
    with st.spinner("Running pipeline (classify → score → action → automate → log)…"):
        result_df = run_pipeline(raw_df, confidence_threshold=confidence_threshold)

    st.session_state["result_df"] = result_df
    auto_metrics = get_automation_metrics(result_df)
    repeat_df    = detect_repeat_atms(result_df)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Core KPIs
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header"><h3>📈 Run Summary</h3></div>', unsafe_allow_html=True)

    total_incidents = len(result_df)
    escalated       = result_df["escalation_status"].str.contains("ESCALATED").sum()
    total_impact    = result_df["impact_score"].sum()
    top_issue       = result_df["predicted_issue"].value_counts().idxmax()
    avg_downtime    = result_df["downtime_minutes"].mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("📋 Incidents",     total_incidents)
    k2.metric("🚨 Escalated",     escalated,
              delta=f"{escalated/total_incidents:.0%}", delta_color="inverse")
    k3.metric("💸 Total Impact",  fmt_inr(total_impact))
    k4.metric("🔝 Top Issue",     top_issue.replace("_", " ").title())
    k5.metric("⏱ Avg Downtime",   f"{avg_downtime:.0f} min")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Automation KPIs (core + advanced)
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header"><h3>🤖 Automation Performance</h3></div>', unsafe_allow_html=True)

    # Row A — resolution counts
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("✅ Auto-Resolved",  auto_metrics.get("auto_resolved_count", 0),
              delta=f"{auto_metrics.get('auto_resolved_pct', 0)}%", delta_color="normal")
    a2.metric("⚠️ Auto-Attempted", auto_metrics.get("auto_attempted_count", 0),
              delta=f"{auto_metrics.get('auto_attempted_pct', 0)}% partial", delta_color="off")
    a3.metric("👷 Manual Required", auto_metrics.get("manual_required_count", 0),
              delta=f"{auto_metrics.get('manual_required_pct', 0)}%", delta_color="inverse")
    a4.metric("⚡ Avg Auto Time",  f"{auto_metrics.get('avg_auto_time_sec', 0):.0f}s")
    a5.metric("📉 Manual Reduced", f"{auto_metrics.get('manual_reduction_pct', 0):.1f}%",
              delta="vs 100% baseline", delta_color="normal")

    st.markdown("---")

    # Row B — advanced operational metrics
    b1, b2, b3, b4 = st.columns(4)
    b1.metric(
        "⏳ Downtime Saved",
        f"{auto_metrics.get('downtime_saved_minutes', 0):,} min",
        delta=f"{auto_metrics.get('downtime_saved_minutes', 0) / 60:.1f} hrs",
        delta_color="normal",
        help="AUTO_RESOLVED count × 120min manual baseline per incident",
    )
    b2.metric(
        "💰 Revenue Contained",
        fmt_inr(auto_metrics.get("revenue_auto_contained", 0)),
        help="Sum of impact_score for all AUTO_RESOLVED incidents",
    )
    b3.metric(
        "🔁 Repeat ATMs Detected",
        auto_metrics.get("repeat_atm_count", 0),
        delta="Flagged for review" if auto_metrics.get("repeat_atm_count", 0) > 0 else "None",
        delta_color="inverse" if auto_metrics.get("repeat_atm_count", 0) > 0 else "off",
        help="ATMs appearing more than once in this run",
    )
    b4.metric(
        "🤔 Low-Confidence Flags",
        auto_metrics.get("low_confidence_count", 0),
        delta=f"Forced to MANUAL" if auto_metrics.get("low_confidence_count", 0) > 0 else "None",
        delta_color="inverse" if auto_metrics.get("low_confidence_count", 0) > 0 else "off",
        help=f"Predictions below {confidence_threshold:.0%} confidence threshold",
    )

    # ── Repeat ATM Warning Panel ──────────────────────────────────────────────
    if not repeat_df.empty:
        st.markdown('<div class="section-header"><h3>⚠️ Repeat ATM Incidents Detected</h3></div>', unsafe_allow_html=True)
        repeat_rows = []
        for _, r in repeat_df.iterrows():
            atm_rows = result_df[result_df["atm_id"] == r["atm_id"]]
            issues   = ", ".join(atm_rows["predicted_issue"].str.replace("_", " ").str.title().unique())
            modes    = ", ".join(atm_rows["resolution_mode"].unique())
            repeat_rows.append({
                "ATM ID":        r["atm_id"],
                "# Incidents":   r["incident_count"],
                "Issue Types":   issues,
                "Modes":         modes,
                "Total Impact":  fmt_inr(atm_rows["impact_score"].sum()),
            })
        st.dataframe(pd.DataFrame(repeat_rows), use_container_width=True, hide_index=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header"><h3>🔍 Issue & Impact Breakdown</h3></div>', unsafe_allow_html=True)
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.caption("Incidents by Issue Type")
        ic = result_df["predicted_issue"].value_counts().reset_index()
        ic.columns = ["Issue", "Count"]
        st.bar_chart(ic.set_index("Issue"))
    with ch2:
        st.caption("Impact by Issue Type (₹)")
        imp = result_df.groupby("predicted_issue")["impact_score"].sum().sort_values(ascending=False).reset_index()
        imp.columns = ["Issue", "Impact"]
        st.bar_chart(imp.set_index("Issue"))
    with ch3:
        st.caption("Resolution Mode Distribution")
        mode_order = {"MANUAL_REQUIRED": 0, "AUTO_ATTEMPTED": 1, "AUTO_RESOLVED": 2}
        mc = result_df["resolution_mode"].value_counts().reset_index()
        mc.columns = ["Mode", "Count"]
        mc["_o"] = mc["Mode"].map(mode_order).fillna(3)
        mc = mc.sort_values("_o").drop(columns=["_o"])
        st.bar_chart(mc.set_index("Mode"))

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Three separated resolution-mode panels
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header"><h3>🗂 Incidents by Resolution Mode</h3></div>', unsafe_allow_html=True)
    st.caption("Each section shows only incidents of that resolution type, sorted by impact. Expand any row for full detail and automation log.")

    # ── 3a. MANUAL_REQUIRED ───────────────────────────────────────────────────
    render_mode_section(
        result_df, "MANUAL_REQUIRED",
        header_html='<div class="mode-header-red"><h4>👷 MANUAL_REQUIRED — Immediate Human Action Needed</h4></div>',
        avg_time_label=None,
    )

    # ── 3b. AUTO_ATTEMPTED ────────────────────────────────────────────────────
    render_mode_section(
        result_df, "AUTO_ATTEMPTED",
        header_html='<div class="mode-header-amber"><h4>⚠️ AUTO_ATTEMPTED — Automation Ran But Issue Persists</h4></div>',
        avg_time_label="Avg Attempt Time",
    )

    # ── 3c. AUTO_RESOLVED ─────────────────────────────────────────────────────
    render_mode_section(
        result_df, "AUTO_RESOLVED",
        header_html='<div class="mode-header-green"><h4>✅ AUTO_RESOLVED — System Fixed It, No Human Needed</h4></div>',
        avg_time_label="Avg Resolve Time",
    )

    # ── Download ──────────────────────────────────────────────────────────────
    st.divider()
    dl_cols = [
        "atm_id", "location", "predicted_issue", "ml_confidence",
        "impact_score", "downtime_minutes", "resolution_mode",
        "recommended_action", "responsible_team", "sla_minutes",
        "escalation_status", "eligibility_reason", "automation_log",
    ]
    csv_out = result_df[[c for c in dl_cols if c in result_df.columns]].to_csv(index=False)
    st.download_button("⬇️ Download Full Results CSV", csv_out,
                       file_name="payguard_results.csv", mime="text/csv")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Persistent Log Archive
# ═════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<div class="section-header"><h3>📁 Persistent Automation Log Archive</h3></div>', unsafe_allow_html=True)

with st.expander("View Historical Logs (data/automation_logs.csv)", expanded=False):
    log_df = load_logs()
    if log_df.empty:
        st.info("No logs yet. Run an analysis to populate the archive.")
    else:
        st.caption(f"{len(log_df)} total records in archive")
        filter_mode = st.selectbox(
            "Filter by resolution mode",
            ["All", "AUTO_RESOLVED", "AUTO_ATTEMPTED", "MANUAL_REQUIRED"],
            key="log_filter",
        )
        view_df = log_df if filter_mode == "All" else log_df[log_df["resolution_mode"] == filter_mode]

        display_log = view_df[[
            "timestamp", "atm_id", "predicted_issue",
            "impact_score", "resolution_mode", "auto_resolution_time_sec",
            "eligibility_reason",
        ]].copy()
        display_log["impact_score"] = display_log["impact_score"].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(display_log.tail(50), use_container_width=True, hide_index=True)

        csv_logs = log_df.to_csv(index=False)
        st.download_button("⬇️ Download Full Log Archive", csv_logs,
                           file_name="payguard_automation_logs.csv", mime="text/csv")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Technician Feedback Loop
# ═════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<div class="section-header"><h3>🔁 Technician Feedback Loop</h3></div>', unsafe_allow_html=True)

result_df_saved = st.session_state.get("result_df", None)

with st.expander("Submit Technician Feedback", expanded=False):
    if result_df_saved is None:
        st.info("Run an analysis first to enable feedback.")
    else:
        # Only show MANUAL_REQUIRED and AUTO_ATTEMPTED in feedback — AUTO_RESOLVED doesn't need it
        feedback_candidates = result_df_saved[
            result_df_saved["resolution_mode"].isin(["MANUAL_REQUIRED", "AUTO_ATTEMPTED"])
        ]
        if feedback_candidates.empty:
            feedback_candidates = result_df_saved

        atm_options = feedback_candidates["atm_id"].tolist()
        fb_atm = st.selectbox("Select ATM ID", atm_options, key="fb_atm_select")
        matched = feedback_candidates[feedback_candidates["atm_id"] == fb_atm].iloc[0]

        fcol1, fcol2 = st.columns(2)
        with fcol1:
            st.write(f"**Predicted Issue:** {matched['predicted_issue'].replace('_',' ').title()}")
            st.write(f"**Resolution Mode:** {matched['resolution_mode']}")
            if "ml_confidence" in matched:
                st.write(f"**ML Confidence:** {matched['ml_confidence']:.1%}")

        with fcol2:
            ISSUE_TYPES = ["network_failure","card_declined","hardware_fault","cash_out","auth_timeout"]
            fb_actual   = st.selectbox(
                "Actual Issue (technician diagnosis)", ISSUE_TYPES,
                index=ISSUE_TYPES.index(matched["predicted_issue"])
                      if matched["predicted_issue"] in ISSUE_TYPES else 0,
                key="fb_actual",
            )
            fb_helpful  = st.radio("Was the recommended action helpful?",
                                   ["yes","partial","no"], horizontal=True, key="fb_helpful")

        fb_notes    = st.text_area("Notes (optional)", key="fb_notes")
        fb_res_time = st.number_input("Resolution Time (minutes)", 0, 600, 30, key="fb_res")

        if st.button("✅ Submit Feedback"):
            save_feedback(
                atm_id=fb_atm,
                predicted_issue=matched["predicted_issue"],
                technician_actual_issue=fb_actual,
                action_helpful=fb_helpful,
                technician_notes=fb_notes,
                resolution_time_minutes=fb_res_time,
            )
            st.success("Feedback saved!")
            st.rerun()

feedback_df = load_feedback()
if not feedback_df.empty:
    st.markdown("#### 📝 Feedback History (last 20)")
    st.dataframe(feedback_df.tail(20), use_container_width=True, hide_index=True)