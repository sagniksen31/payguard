"""
action_engine.py
Layer 3 & 4: Rule-based action recommendations + escalation logic.

Actions are deterministic rules based on predicted issue type.
Escalation is triggered by impact score or downtime thresholds.
"""

# ── Thresholds ────────────────────────────────────────────────────────────────
ESCALATION_IMPACT_THRESHOLD   = 100_000   # ₹1 lakh
ESCALATION_DOWNTIME_THRESHOLD = 120       # 2 hours

# ── Action Rules ─────────────────────────────────────────────────────────────
ACTION_MAP = {
    "network_failure": {
        "action": "Restart network interface; verify ISP connectivity; check firewall rules.",
        "sla_minutes": 30,
        "team": "Network Operations",
    },
    "card_declined": {
        "action": "Check card processor gateway status; review decline reason codes; contact issuing bank if batch failure.",
        "sla_minutes": 15,
        "team": "Payments Team",
    },
    "hardware_fault": {
        "action": "Dispatch field technician immediately; run hardware diagnostics; check card reader & dispensing mechanism.",
        "sla_minutes": 60,
        "team": "Field Maintenance",
    },
    "cash_out": {
        "action": "Schedule emergency cash replenishment; notify branch manager; temporarily disable cash withdrawal.",
        "sla_minutes": 45,
        "team": "Cash Management",
    },
    "auth_timeout": {
        "action": "Check authentication server latency; review API timeout configs; increase retry window.",
        "sla_minutes": 20,
        "team": "Backend Engineering",
    },
}

FALLBACK_ACTION = {
    "action": "Log incident; assign to L1 support for triage.",
    "sla_minutes": 30,
    "team": "L1 Support",
}


def get_recommended_action(predicted_issue: str) -> dict:
    """Return action details for a predicted issue type."""
    return ACTION_MAP.get(predicted_issue, FALLBACK_ACTION)


def should_escalate(impact_score: float, downtime_minutes: float) -> bool:
    """Return True if incident meets escalation criteria."""
    return (
        impact_score >= ESCALATION_IMPACT_THRESHOLD
        or downtime_minutes >= ESCALATION_DOWNTIME_THRESHOLD
    )


def escalation_status(impact_score: float, downtime_minutes: float) -> str:
    """Return a human-readable escalation status string."""
    if should_escalate(impact_score, downtime_minutes):
        reasons = []
        if impact_score >= ESCALATION_IMPACT_THRESHOLD:
            reasons.append(f"Impact ₹{impact_score:,.0f} exceeds threshold")
        if downtime_minutes >= ESCALATION_DOWNTIME_THRESHOLD:
            reasons.append(f"Downtime {downtime_minutes}m exceeds threshold")
        return "🚨 ESCALATED — " + "; ".join(reasons)
    return "✅ Normal — Monitor"


def process_incident(row: dict) -> dict:
    """
    Full pipeline for a single incident dict.
    Expects keys: atm_id, location, predicted_issue, impact_score, downtime_minutes
    Returns enriched dict with action + escalation fields.
    """
    predicted = row.get("predicted_issue", "unknown")
    impact    = row.get("impact_score", 0)
    downtime  = row.get("downtime_minutes", 0)

    action_info = get_recommended_action(predicted)

    return {
        **row,
        "recommended_action": action_info["action"],
        "sla_minutes":        action_info["sla_minutes"],
        "responsible_team":   action_info["team"],
        "escalation_status":  escalation_status(impact, downtime),
    }


def process_dataframe(df):
    """Apply full action + escalation logic to a DataFrame."""
    import pandas as pd
    df = df.copy()

    df["recommended_action"] = df["predicted_issue"].apply(
        lambda x: get_recommended_action(x)["action"]
    )
    df["sla_minutes"] = df["predicted_issue"].apply(
        lambda x: get_recommended_action(x)["sla_minutes"]
    )
    df["responsible_team"] = df["predicted_issue"].apply(
        lambda x: get_recommended_action(x)["team"]
    )
    df["escalation_status"] = df.apply(
        lambda r: escalation_status(r["impact_score"], r["downtime_minutes"]), axis=1
    )
    return df
