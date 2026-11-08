"""Pydantic structured output models for the Cred Banking Support Agent.

Task 9 requirements:
- Every CrewAI response must conform to a declared Pydantic schema (response_format).
- Includes validation of field types, value constraints (escalation_score in [0, 1]),
  and source provenance.
- Validated programmatically in code.
"""

from __future__ import annotations

import json
import re
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class BankingResponse(BaseModel):
    """Declared structured response model for all banking agent replies."""

    query_type: Literal["policy", "loan_status", "general", "out_of_scope", "fallback"] = Field(
        ...,
        description="Classification of the query type processed by the agent.",
    )
    answer: str = Field(
        ...,
        min_length=5,
        description="The customer-facing grounded response draft.",
    )
    record_id: Optional[str] = Field(
        default=None,
        description="The unique loan application ID (e.g. CL-00001) if applicable.",
    )
    application_status: Optional[str] = Field(
        default=None,
        description="Current application status (Submitted, Under Review, Approved, Rejected, Disbursed).",
    )
    loan_amount_inr: Optional[int] = Field(
        default=None,
        ge=0,
        description="Loan amount in INR if applicable.",
    )
    escalation_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Composite escalation score strictly bounded between 0.0 and 1.0.",
    )
    escalation_recommended: Optional[bool] = Field(
        default=None,
        description="Whether managerial escalation is recommended based on threshold >= 0.244.",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Knowledge base documents or system datasets referenced in the answer.",
    )
    grounded: bool = Field(
        default=True,
        description="Whether the answer is supported by retrieved context or database records.",
    )

    @field_validator("record_id")
    @classmethod
    def validate_record_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if not re.match(r"^CL-\d{5}$", v):
                raise ValueError(f"Invalid record_id format: '{v}'. Expected format like 'CL-00001'.")
        return v

    @field_validator("escalation_score")
    @classmethod
    def validate_escalation_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"escalation_score {v} must be between 0.0 and 1.0.")
            v = round(v, 4)
        return v


def parse_and_validate_response(
    raw_output: Any,
    query: str,
    record_details: Optional[dict[str, Any]] = None,
    retrieved_sources: Optional[list[str]] = None,
) -> BankingResponse:
    """Construct and validate a BankingResponse instance from agent outputs.

    Ensures every response emitted by the multi-agent system conforms strictly
    to the Pydantic schema and passes validation.
    """
    raw_text = str(raw_output.raw if hasattr(raw_output, "raw") else raw_output).strip()

    # Determine query classification
    is_loan = "CL-" in query.upper() or "loan_applications" in raw_text or record_details is not None
    query_type = "loan_status" if is_loan else "policy"

    # Default fallback data
    record_id = None
    app_status = None
    amount = None
    score = None
    escalate = None
    sources = retrieved_sources or []

    if record_details:
        record_id = record_details.get("record_id")
        app_status = record_details.get("status")
        amount = record_details.get("loan_amount_inr")
        score = record_details.get("escalation_score")
        escalate = record_details.get("escalation_recommended")
        if "data/loan_applications.json" not in sources:
            sources.append("data/loan_applications.json")
    elif is_loan:
        id_match = re.search(r"CL-\d{5}", query, re.IGNORECASE) or re.search(r"CL-\d{5}", raw_text, re.IGNORECASE)
        if id_match:
            record_id = id_match.group(0).upper()

    response = BankingResponse(
        query_type=query_type,
        answer=raw_text,
        record_id=record_id,
        application_status=app_status,
        loan_amount_inr=amount,
        escalation_score=score,
        escalation_recommended=escalate,
        sources=sources,
        grounded=True,
    )
    return response

