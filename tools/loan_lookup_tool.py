"""Loan application status lookup and escalation scoring tool for CrewAI.

Task 6 & Task 7 requirements:
- Deterministic lookup using dataset records (data/loan_applications.json).
- Computes designed escalation_score in [0, 1] combining flagged_for_fraud_review (0.70)
  and normalized recency signal days_since_created / 30 (0.30).
- Escalation threshold: 0.244 (justified by 80th percentile of days_since_created = 24.4 days).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Type

# Set zero-telemetry and redirect LOCALAPPDATA to prevent WinError 5 in sandboxes
_ROOT = Path(__file__).resolve().parent.parent
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CI"] = "true"
os.environ["LOCALAPPDATA"] = str(_ROOT / ".appdata")

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "loan_applications.json"
MAX_DAYS = 30
FRAUD_WEIGHT = 0.70
RECENCY_WEIGHT = 0.30
ESCALATION_THRESHOLD = 0.244


@lru_cache(maxsize=1)
def _load_applications() -> dict[str, dict[str, Any]]:
    """Load loan applications dataset and index by record_id."""
    if not DATA_FILE.exists():
        # Fallback to generating if file not yet present
        try:
            from dataset import generate_loan_applications
            records = generate_loan_applications()
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")
        except Exception:
            records = []
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

    return {r["record_id"]: r for r in records}


def check_loan_application_status(record_id: str) -> dict[str, Any]:
    """Return loan application status, amount in INR, and escalation score.

    Args:
        record_id: Unique application identifier (e.g., 'CL-00001').

    Returns:
        Dictionary containing record details and calculated escalation score.
    """
    clean_id = record_id.strip().upper()
    apps = _load_applications()

    if clean_id not in apps:
        raise KeyError(f"Loan application not found: {record_id}")

    record = apps[clean_id]
    fraud_signal = int(record["flagged_for_fraud_review"])
    recency_signal = record["days_since_created"] / MAX_DAYS

    score = (FRAUD_WEIGHT * fraud_signal) + (RECENCY_WEIGHT * recency_signal)
    escalation_score = round(max(0.0, min(1.0, score)), 4)
    escalate = escalation_score >= ESCALATION_THRESHOLD

    return {
        "record_id": record["record_id"],
        "category": record["category"],
        "status": record["status"],
        "loan_amount_inr": record["loan_amount_inr"],
        "days_since_created": record["days_since_created"],
        "flagged_for_fraud_review": record["flagged_for_fraud_review"],
        "escalation_score": escalation_score,
        "escalation_recommended": escalate,
        "escalation_threshold": ESCALATION_THRESHOLD,
    }


class LoanLookupInput(BaseModel):
    """Input schema for loan application status lookup."""
    record_id: str = Field(
        ...,
        description="The unique loan application ID, e.g., 'CL-00001'.",
    )


class LoanLookupTool(BaseTool):
    """CrewAI tool for checking loan application status."""

    name: str = "check_loan_application_status"
    description: str = (
        "Look up loan application status, amount, and fraud/recency escalation score "
        "by record_id (e.g. 'CL-00001'). Always use this tool for customer application queries."
    )
    args_schema: Type[BaseModel] = LoanLookupInput

    def _run(self, record_id: str) -> str:
        try:
            result = check_loan_application_status(record_id)
            return json.dumps(result, indent=2)
        except KeyError as err:
            return json.dumps({"error": str(err), "record_id": record_id})
        except Exception as err:
            return json.dumps({"error": f"Unexpected error during lookup: {err}"})


# Module export instance
loan_lookup_tool = LoanLookupTool()

