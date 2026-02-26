"""
data_generator.py
Generates synthetic payment failure data for training/demo.
"""

import numpy as np
import pandas as pd
import random

LOCATIONS = [
    "Mumbai Central", "Delhi Airport", "Chennai Mall",
    "Bangalore Station", "Hyderabad Hub", "Pune Market",
    "Kolkata Port", "Ahmedabad Bazaar"
]

ERROR_CODES = {
    "network_failure":   ["E001", "E002", "E003"],
    "card_declined":     ["E010", "E011", "E012"],
    "hardware_fault":    ["E020", "E021", "E022"],
    "cash_out":          ["E030", "E031"],
    "auth_timeout":      ["E040", "E041", "E042"],
}

ISSUE_TYPES = list(ERROR_CODES.keys())


def generate_row(issue_type: str) -> dict:
    """Generate a single synthetic record for a given issue type."""
    hour = random.randint(0, 23)
    
    # Pattern-based synthetic logic per issue type
    if issue_type == "network_failure":
        volume     = random.randint(10, 80)
        avg_amt    = random.uniform(500, 3000)
        downtime   = random.randint(15, 120)
        complaints = random.randint(3, 20)
    elif issue_type == "card_declined":
        volume     = random.randint(50, 200)
        avg_amt    = random.uniform(200, 1500)
        downtime   = random.randint(0, 10)
        complaints = random.randint(5, 30)
    elif issue_type == "hardware_fault":
        volume     = random.randint(5, 50)
        avg_amt    = random.uniform(1000, 5000)
        downtime   = random.randint(60, 480)
        complaints = random.randint(10, 40)
    elif issue_type == "cash_out":
        volume     = random.randint(80, 300)
        avg_amt    = random.uniform(2000, 8000)
        downtime   = random.randint(30, 240)
        complaints = random.randint(15, 60)
    else:  # auth_timeout
        volume     = random.randint(20, 100)
        avg_amt    = random.uniform(300, 2000)
        downtime   = random.randint(5, 45)
        complaints = random.randint(2, 15)

    error_code = random.choice(ERROR_CODES[issue_type])

    return {
        "atm_id":            f"ATM-{random.randint(1000, 9999)}",
        "location":          random.choice(LOCATIONS),
        "hour_of_day":       hour,
        "transaction_volume": volume,
        "avg_amount":        round(avg_amt, 2),
        "downtime_minutes":  downtime,
        "complaint_count":   complaints,
        "error_code":        error_code,
        "issue_type":        issue_type,
    }


def generate_dataset(n_samples: int = 1000, seed: int | None = 42) -> pd.DataFrame:
    """
    Generate a balanced synthetic dataset.

    Args:
        n_samples: Number of records to generate.
        seed:      RNG seed for reproducibility.
                   Pass 42   (default) for Stable Demo Mode — identical output every run.
                   Pass None           for Live Simulation Mode — different output each run.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    # If seed is None the global RNG state is used as-is (true randomness).

    rows = []
    per_class = n_samples // len(ISSUE_TYPES)
    for issue in ISSUE_TYPES:
        for _ in range(per_class):
            rows.append(generate_row(issue))

    # Fill remainder
    for i in range(n_samples - len(rows)):
        rows.append(generate_row(ISSUE_TYPES[i % len(ISSUE_TYPES)]))

    random.shuffle(rows)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_dataset(1000)
    df.to_csv("data/training_data.csv", index=False)
    print(f"Generated {len(df)} rows | Columns: {list(df.columns)}")
    print(df["issue_type"].value_counts())
