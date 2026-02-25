import pandas as pd
import numpy as np

np.random.seed(42)

n = 1500

issue_types = [
    "Cash Depletion",
    "Network Timeout",
    "Switch Failure",
    "Bank Decline",
    "Fraud Suspicion"
]

data = pd.DataFrame({
    "atm_id": np.random.choice([f"ATM_{i}" for i in range(50)], n),
    "location": np.random.choice(["Chennai", "Bangalore", "Mumbai", "Delhi"], n),
    "hour_of_day": np.random.randint(0, 24, n),
    "transaction_volume": np.random.randint(20, 300, n),
    "avg_amount": np.random.randint(100, 5000, n),
    "downtime_minutes": np.random.randint(5, 180, n),
    "complaint_count": np.random.randint(0, 20, n),
    "error_code": np.random.randint(100, 600, n),
    "issue_type": np.random.choice(issue_types, n)
})

data.to_csv("payment_incidents.csv", index=False)

print("Dataset created successfully")