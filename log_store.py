"""
log_store.py
Persistent storage for automation execution logs.

Responsibility: ONE job only — append automation results to
data/automation_logs.csv and read them back for reporting.

Schema (fixed, do not modify):
    timestamp
    atm_id
    predicted_issue
    impact_score
    resolution_mode
    eligibility_reason
    auto_resolution_time_sec
    automation_log

Design rules:
  - Auto-creates the file and parent directory on first write
  - Always appends — never overwrites historical records
  - Returns empty DataFrame (correct columns) when file is missing or empty
  - No external dependencies beyond pandas + stdlib
"""

import os
import csv
import datetime
import pandas as pd

LOG_PATH = "data/automation_logs.csv"

LOG_COLUMNS = [
    "timestamp",
    "atm_id",
    "predicted_issue",
    "impact_score",
    "resolution_mode",
    "eligibility_reason",
    "auto_resolution_time_sec",
    "automation_log",
]


# ── Private helpers ───────────────────────────────────────────────────────────

def _ensure_file() -> None:
    """Create log file with header row if it does not yet exist."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
            writer.writeheader()


# ── Public API ────────────────────────────────────────────────────────────────

def append_log(
    atm_id: str,
    predicted_issue: str,
    impact_score: float,
    resolution_mode: str,
    eligibility_reason: str,
    auto_resolution_time_sec: float,
    automation_log: str,
) -> None:
    """
    Append a single automation result record to the CSV.
    Called once per incident after the automation engine finishes.
    """
    _ensure_file()
    record = {
        "timestamp":                  datetime.datetime.now().isoformat(timespec="seconds"),
        "atm_id":                     atm_id,
        "predicted_issue":            predicted_issue,
        "impact_score":               round(float(impact_score), 2),
        "resolution_mode":            resolution_mode,
        "eligibility_reason":         eligibility_reason,
        "auto_resolution_time_sec":   round(float(auto_resolution_time_sec), 1),
        "automation_log":             automation_log,
    }
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        writer.writerow(record)


def append_logs_from_dataframe(df: pd.DataFrame) -> int:
    """
    Bulk-append all rows from a pipeline result DataFrame.
    Expects the following columns to be present:
        atm_id, predicted_issue, impact_score, resolution_mode,
        eligibility_reason (optional), auto_resolution_time_sec, automation_log

    Returns the number of rows written.
    """
    _ensure_file()
    written = 0
    for _, row in df.iterrows():
        append_log(
            atm_id                   = str(row.get("atm_id", "")),
            predicted_issue          = str(row.get("predicted_issue", "")),
            impact_score             = float(row.get("impact_score", 0)),
            resolution_mode          = str(row.get("resolution_mode", "")),
            eligibility_reason       = str(row.get("eligibility_reason", "")),
            auto_resolution_time_sec = float(row.get("auto_resolution_time_sec", 0)),
            automation_log           = str(row.get("automation_log", "")),
        )
        written += 1
    return written


def load_logs() -> pd.DataFrame:
    """
    Load all historical log records.
    Returns a DataFrame with LOG_COLUMNS schema.
    If the file is missing or empty, returns an empty DataFrame with correct columns.
    """
    _ensure_file()
    try:
        df = pd.read_csv(LOG_PATH)
        if df.empty:
            return pd.DataFrame(columns=LOG_COLUMNS)
        # Ensure numeric columns are typed correctly after CSV round-trip
        df["impact_score"]             = pd.to_numeric(df["impact_score"],             errors="coerce").fillna(0)
        df["auto_resolution_time_sec"] = pd.to_numeric(df["auto_resolution_time_sec"], errors="coerce").fillna(0)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=LOG_COLUMNS)


def get_log_summary() -> dict:
    """
    Aggregate stats across ALL historical log records.
    Useful for the sidebar and the persistent-log analytics panel.
    """
    df = load_logs()
    if df.empty:
        return {
            "total_logged":       0,
            "auto_resolved":      0,
            "auto_attempted":     0,
            "manual_required":    0,
            "avg_auto_time_sec":  0.0,
        }

    resolved = (df["resolution_mode"] == "AUTO_RESOLVED").sum()
    attempted = (df["resolution_mode"] == "AUTO_ATTEMPTED").sum()
    manual    = (df["resolution_mode"] == "MANUAL_REQUIRED").sum()

    resolved_times = df.loc[df["resolution_mode"] == "AUTO_RESOLVED", "auto_resolution_time_sec"]
    avg_time = resolved_times.mean() if len(resolved_times) > 0 else 0.0

    return {
        "total_logged":       int(len(df)),
        "auto_resolved":      int(resolved),
        "auto_attempted":     int(attempted),
        "manual_required":    int(manual),
        "avg_auto_time_sec":  round(float(avg_time), 1),
    }


if __name__ == "__main__":
    # Quick smoke test
    append_log(
        atm_id="ATM-TEST",
        predicted_issue="network_failure",
        impact_score=12345.67,
        resolution_mode="AUTO_RESOLVED",
        eligibility_reason="Eligible for automated first-level remediation",
        auto_resolution_time_sec=45.0,
        automation_log="[START] test\n[SUCCESS] done",
    )
    df = load_logs()
    print(f"Rows in log: {len(df)}")
    print(df.tail(3).to_string(index=False))
    print("\nSummary:", get_log_summary())
