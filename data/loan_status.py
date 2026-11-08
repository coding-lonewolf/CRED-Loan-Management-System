"""Loan application status lookup and escalation scoring.

Expected layout:
    dataset.py
    loan_applications.json
    loan_status.py

Scoring formula:
    recency_signal = days_since_created / 30
    escalation_score = 0.70 * int(flagged_for_fraud_review) + 0.30 * recency_signal

For the supplied 60-record dataset, the linearly interpolated 80th percentile
of days_since_created is 24.4 days. The corresponding score threshold for an
unflagged record is 0.30 * (24.4 / 30) = 0.244.
"""

import json
from functools import lru_cache
from pathlib import Path

MAX_DAYS = 30
FRAUD_WEIGHT = 0.70
RECENCY_WEIGHT = 0.30
ESCALATION_THRESHOLD = 0.244

DATA_FILE = Path(__file__).resolve().with_name("loan_applications.json")


@lru_cache(maxsize=1)
def _load_applications() -> dict[str, dict]:
    """Load the sample data once and index it by record_id."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    return {record["record_id"]: record for record in records}


def check_loan_application_status(record_id: str) -> dict:
    """Return status, loan amount, and a 0-to-1 escalation score.

    Raises:
        KeyError: if record_id is not present in loan_applications.json.
    """
    applications = _load_applications()

    if record_id not in applications:
        raise KeyError(f"Loan application not found: {record_id}")

    record = applications[record_id]

    fraud_signal = int(record["flagged_for_fraud_review"])
    recency_signal = record["days_since_created"] / MAX_DAYS

    score = (
        FRAUD_WEIGHT * fraud_signal
        + RECENCY_WEIGHT * recency_signal
    )
    score = max(0.0, min(1.0, score))

    return {
        "status": record["status"],
        "loan_amount_inr": record["loan_amount_inr"],
        "escalation_score": round(score, 4),
    }


if __name__ == "__main__":
    print(check_loan_application_status("CL-00001"))
