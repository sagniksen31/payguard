"""
impact_scorer.py
Layer 2: Business impact calculation.

Formula:
  impact_score = (transaction_volume × avg_amount × downtime_minutes / 60)
                 × (1 + complaint_count × COMPLAINT_WEIGHT)

Result is a float representing estimated financial exposure (₹).
"""

COMPLAINT_WEIGHT = 0.05   # Each complaint adds 5% to the impact multiplier
DOWNTIME_DIVISOR = 60.0   # Convert minutes → hours for revenue loss


def calculate_impact(
    transaction_volume: float,
    avg_amount: float,
    downtime_minutes: float,
    complaint_count: int,
) -> float:
    """
    Calculate business impact score.

    Returns:
        impact_score (float): Estimated financial exposure in ₹
    """
    if downtime_minutes <= 0:
        downtime_minutes = 1  # Minimum 1 minute exposure

    base_loss = transaction_volume * avg_amount * (downtime_minutes / DOWNTIME_DIVISOR)
    complaint_multiplier = 1.0 + (complaint_count * COMPLAINT_WEIGHT)
    impact_score = base_loss * complaint_multiplier
    return round(impact_score, 2)


def score_dataframe(df):
    """Add impact_score column to a DataFrame in-place."""
    import pandas as pd
    df = df.copy()
    df["impact_score"] = df.apply(
        lambda r: calculate_impact(
            r["transaction_volume"],
            r["avg_amount"],
            r["downtime_minutes"],
            r["complaint_count"],
        ),
        axis=1,
    )
    return df


def impact_label(score: float) -> str:
    """Human-readable severity label."""
    if score >= 500_000:
        return "🔴 CRITICAL"
    elif score >= 100_000:
        return "🟠 HIGH"
    elif score >= 20_000:
        return "🟡 MEDIUM"
    else:
        return "🟢 LOW"


if __name__ == "__main__":
    score = calculate_impact(150, 2000, 90, 25)
    print(f"Impact Score: ₹{score:,.0f}  |  {impact_label(score)}")
