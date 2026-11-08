"""Pydantic schema for the AutoGen review team verdict.

Task 14 requirements:
- VerdictModel with fields:
  1. approved: bool (True if draft answer is grounded and compliant)
  2. final_answer: str (the approved original draft or revised answer)
  3. reason: str (explanation for approval or revision)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VerdictModel(BaseModel):
    """Pydantic model representing the review team's final decision."""

    approved: bool = Field(
        ...,
        description="Whether the draft answer was approved unchanged (True) or revised (False).",
    )
    final_answer: str = Field(
        ...,
        min_length=5,
        description="The final customer response (either unchanged draft or corrected text).",
    )
    reason: str = Field(
        ...,
        description="Justification detailing why the draft was approved or which claim was revised.",
    )


def create_verdict(approved: bool, final_answer: str, reason: str) -> VerdictModel:
    """Helper factory for generating validated VerdictModel instances."""
    return VerdictModel(
        approved=approved,
        final_answer=final_answer.strip(),
        reason=reason.strip(),
    )

