"""
pipeline.py
Orchestrates all layers end-to-end.

Layer execution order:
    1  classifier        → predicted_issue  +  ml_confidence
    2  impact_scorer     → impact_score
    3  action_engine     → recommended_action, sla_minutes, responsible_team
    4  action_engine     → escalation_status
    5  automation_engine → resolution_mode, automation_log,
                           auto_resolution_time_sec, eligibility_reason
    6  log_store         → append results to data/automation_logs.csv

Constants:
    ML_CONFIDENCE_THRESHOLD  — predictions below this are forced to MANUAL_REQUIRED
                                Can be overridden by passing confidence_threshold
                                to run_pipeline().

Usage:
    from pipeline import run_pipeline, run_single, get_automation_metrics
"""

import os
import pandas as pd

from data_generator import generate_dataset
from classifier import train, predict_batch_with_confidence
from impact_scorer import score_dataframe
from action_engine import process_dataframe
from automation_engine import automate_dataframe, compute_automation_metrics
from log_store import append_logs_from_dataframe

MODEL_PATH = "model/classifier.pkl"

# Predictions below this confidence are too uncertain for automation
ML_CONFIDENCE_THRESHOLD = 0.60

# ── Execution mode constants ──────────────────────────────────────────────────
# Use these strings everywhere — no magic literals scattered through the codebase.
STABLE_DEMO = "Stable Demo Mode"
LIVE_SIM    = "Live Simulation Mode"


def ensure_model_trained(execution_mode: str = STABLE_DEMO) -> None:
    """
    Guarantee a trained model is ready before the pipeline runs.

    Stable Demo Mode:
        Load from disk if it exists (fast, deterministic).
        If no file exists, train once with seed=42 and persist.

    Live Simulation Mode:
        Always retrain from scratch with random_state=None.
        The saved model file is intentionally ignored so each run
        produces a freshly trained, non-deterministic model.
    """
    if execution_mode == LIVE_SIM:
        # Force a fresh random retrain every run — discard any saved artefact.
        print("Live Simulation Mode — retraining model with random_state=None …")
        df = generate_dataset(1000, seed=None)     # unseeded data
        os.makedirs("data", exist_ok=True)
        result = train(df, random_state=None)      # unseeded forest
        print(f"Model retrained | Accuracy: {result['accuracy']:.1%}")
    else:
        # Stable Demo: load from disk or train once with fixed seed.
        if not os.path.exists(MODEL_PATH):
            print("No model found — training on fresh synthetic data …")
            df = generate_dataset(1000, seed=42)
            os.makedirs("data", exist_ok=True)
            df.to_csv("data/training_data.csv", index=False)
            result = train(df, random_state=42)
            print(f"Model trained | Accuracy: {result['accuracy']:.1%}")
        else:
            print("Stable Demo Mode — model loaded from disk.")


def run_pipeline(
    df: pd.DataFrame,
    confidence_threshold: float = ML_CONFIDENCE_THRESHOLD,
    persist_logs: bool = True,
    execution_mode: str = STABLE_DEMO,
) -> pd.DataFrame:
    """
    Full 6-layer pipeline on a DataFrame of raw incidents.

    Input columns required:
        atm_id, location, hour_of_day, transaction_volume,
        avg_amount, downtime_minutes, complaint_count, error_code

    Output columns:
        atm_id, location, predicted_issue, ml_confidence,
        impact_score, recommended_action, escalation_status,
        sla_minutes, responsible_team,
        resolution_mode, automation_log,
        auto_resolution_time_sec, eligibility_reason

    Args:
        df                   : raw incident DataFrame
        confidence_threshold : ML confidence below which → MANUAL_REQUIRED
        persist_logs         : if True, appends results to data/automation_logs.csv
        execution_mode       : STABLE_DEMO (default) or LIVE_SIM.
                               Controls seeding of model training, data generation,
                               and per-row automation outcomes.
    """
    # Model is guaranteed ready by boot_model() called at app startup.
    # No retrain here — avoids double-training in Live Sim mode.

    # Layer 1: Classification + confidence scores
    df = df.copy()
    classification = predict_batch_with_confidence(df)
    df["predicted_issue"] = classification["predicted_issue"]
    df["ml_confidence"]   = classification["ml_confidence"]

    # Layer 2: Impact Scoring
    df = score_dataframe(df)

    # Layers 3 & 4: Action Recommendation + Escalation
    df = process_dataframe(df)

    # Layer 5: Automation Engine
    # deterministic=True  → per-row seed = row index (Stable Demo)
    # deterministic=False → seed=None, outcomes vary per run (Live Sim)
    df = automate_dataframe(
        df,
        ml_confidence_threshold=confidence_threshold,
        deterministic=(execution_mode == STABLE_DEMO),
    )

    # Layer 6: Persist logs
    if persist_logs:
        append_logs_from_dataframe(df)

    # Sort: MANUAL_REQUIRED (highest impact) first, AUTO_RESOLVED last
    resolution_order = {"MANUAL_REQUIRED": 0, "AUTO_ATTEMPTED": 1, "AUTO_RESOLVED": 2}
    df["_sort_mode"] = df["resolution_mode"].map(resolution_order).fillna(0)
    df = (
        df.sort_values(["_sort_mode", "impact_score"], ascending=[True, False])
          .drop(columns=["_sort_mode"])
          .reset_index(drop=True)
    )

    return df


def get_automation_metrics(df: pd.DataFrame) -> dict:
    """Convenience wrapper — returns all automation KPIs for the dashboard."""
    return compute_automation_metrics(df)


def detect_repeat_atms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag ATM IDs that appear more than once in the current run.
    Returns a DataFrame of repeat ATMs with their incident counts.
    Used by the dashboard for the repeat-incident warning panel.
    """
    counts = df["atm_id"].value_counts().reset_index()
    counts.columns = ["atm_id", "incident_count"]
    return counts[counts["incident_count"] > 1].sort_values(
        "incident_count", ascending=False
    ).reset_index(drop=True)


def run_single(incident: dict) -> dict:
    """
    Full pipeline for a single incident dict.
    Returns enriched output dict.
    """
    df_in  = pd.DataFrame([incident])
    df_out = run_pipeline(df_in)
    return df_out.iloc[0].to_dict()


OUTPUT_COLS = [
    "atm_id", "location", "predicted_issue", "ml_confidence",
    "impact_score", "recommended_action", "escalation_status",
    "sla_minutes", "responsible_team",
    "resolution_mode", "automation_log", "eligibility_reason",
]


if __name__ == "__main__":
    from data_generator import generate_dataset
    sample = generate_dataset(30)
    result = run_pipeline(sample)
    print(result[OUTPUT_COLS].head(10).to_string(index=False))
    print("\n── Automation Metrics ──")
    metrics = get_automation_metrics(result)
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("\n── Repeat ATMs ──")
    print(detect_repeat_atms(result))
