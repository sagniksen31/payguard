"""
classifier.py
Layer 1: Classification of payment failure types.
Uses RandomForest on structured features.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

MODEL_PATH = "model/classifier.pkl"
ENCODER_PATH = "model/label_encoder.pkl"

# Features used for training (no target, no IDs)
FEATURE_COLS = [
    "hour_of_day",
    "transaction_volume",
    "avg_amount",
    "downtime_minutes",
    "complaint_count",
    "error_code_encoded",
]


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add encoded error_code column."""
    df = df.copy()
    # Simple ordinal encoding for error_code
    unique_codes = sorted(df["error_code"].unique())
    code_map = {code: idx for idx, code in enumerate(unique_codes)}
    df["error_code_encoded"] = df["error_code"].map(code_map).fillna(-1).astype(int)
    return df, code_map


def train(df: pd.DataFrame) -> dict:
    """Train the RandomForest classifier and persist it."""
    os.makedirs("model", exist_ok=True)

    df, code_map = encode_features(df)

    le = LabelEncoder()
    y = le.fit_transform(df["issue_type"])
    X = df[FEATURE_COLS].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=le.classes_)

    # Persist
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "code_map": code_map}, f)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(le, f)

    print(f"Training complete | Accuracy: {acc:.3f}")
    print(report)
    return {"accuracy": acc, "report": report, "classes": list(le.classes_)}


def load_model():
    """Load persisted model artifacts."""
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    with open(ENCODER_PATH, "rb") as f:
        le = pickle.load(f)
    return bundle["model"], bundle["code_map"], le


def predict_single(row: dict) -> str:
    """Predict issue type for a single incident dict."""
    clf, code_map, le = load_model()
    code_enc = code_map.get(row.get("error_code", ""), -1)
    features = np.array([[
        row["hour_of_day"],
        row["transaction_volume"],
        row["avg_amount"],
        row["downtime_minutes"],
        row["complaint_count"],
        code_enc,
    ]])
    pred_idx = clf.predict(features)[0]
    return le.inverse_transform([pred_idx])[0]


def predict_batch(df: pd.DataFrame) -> pd.Series:
    """Predict issue types for a DataFrame."""
    clf, code_map, le = load_model()
    df2 = df.copy()
    df2["error_code_encoded"] = df2["error_code"].map(code_map).fillna(-1).astype(int)
    X = df2[FEATURE_COLS].values
    preds = clf.predict(X)
    return pd.Series(le.inverse_transform(preds), index=df.index, name="predicted_issue")


def predict_batch_with_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict issue types AND return the model's max-class confidence score.

    Returns a DataFrame with two columns:
        predicted_issue : string label  (e.g. "network_failure")
        ml_confidence   : float 0.0–1.0 (highest class probability from predict_proba)

    Rows where ml_confidence < ML_CONFIDENCE_THRESHOLD (defined in pipeline.py)
    are considered uncertain and will be forced to MANUAL_REQUIRED by the
    automation engine, regardless of impact/downtime eligibility.
    """
    clf, code_map, le = load_model()
    df2 = df.copy()
    df2["error_code_encoded"] = df2["error_code"].map(code_map).fillna(-1).astype(int)
    X = df2[FEATURE_COLS].values

    preds      = clf.predict(X)
    proba      = clf.predict_proba(X)    # shape: (n_rows, n_classes)
    confidence = proba.max(axis=1)       # highest class probability per row

    return pd.DataFrame(
        {
            "predicted_issue": le.inverse_transform(preds),
            "ml_confidence":   np.round(confidence, 4),
        },
        index=df.index,
    )


if __name__ == "__main__":
    from data_generator import generate_dataset
    df = generate_dataset(1000)
    train(df)