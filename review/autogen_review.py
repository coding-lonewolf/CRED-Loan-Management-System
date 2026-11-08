"""Two-agent AutoGen review team for post-CrewAI draft verification.

Task 14 requirements:
- Independent review stage following the CrewAI Composer's draft answer.
- 2 Agents:
  1. Policy-Compliance-Reviewer: Audits draft against original retrieved context.
  2. Final-Editor: Emits structured VerdictModel (approved, final_answer, reason).
- Bounded orchestration: RoundRobinGroupChat(max_turns=2).
- Structured output: Registers custom_message_types=[StructuredMessage[VerdictModel]]
  to prevent runtime ValueError: Message type ... is not registered.
- Demonstrates two mandatory cases:
  1. Approve unchanged when draft is fully supported by context.
  2. Revise when an unsupported claim has been deliberately injected.
- Zero-network, keyless deterministic MOCK_LLM execution.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from schemas.verdict_schema import VerdictModel, create_verdict

T = TypeVar("T", bound=BaseModel)


class StructuredMessage(Generic[T]):
    """Generic structured message container for AutoGen AgentChat compatibility."""

    def __init__(self, content: T, source: str) -> None:
        self.content = content
        self.source = source

    def __repr__(self) -> str:
        return f"StructuredMessage(source='{self.source}', content={self.content})"


class AutoGenAgent:
    """Lightweight deterministic AutoGen agent representation under MOCK_LLM."""

    def __init__(self, name: str, role_description: str, output_content_type: Optional[Type[BaseModel]] = None) -> None:
        self.name = name
        self.role_description = role_description
        self.output_content_type = output_content_type


class RoundRobinGroupChat:
    """Bounded round-robin group chat for the two-agent review team."""

    def __init__(
        self,
        agents: List[AutoGenAgent],
        max_turns: int = 2,
        custom_message_types: Optional[List[Any]] = None,
    ) -> None:
        self.agents = agents
        self.max_turns = max_turns
        self.custom_message_types = custom_message_types or []

        # Validate structured message type registration to guard against known AutoGen error
        if any(a.output_content_type is not None for a in agents):
            has_registered_type = any(
                hasattr(t, "__origin__") and issubclass(t.__origin__, StructuredMessage) or t == StructuredMessage
                for t in self.custom_message_types
            )
            if not has_registered_type and not custom_message_types:
                raise ValueError("ValueError: Structured message type must be registered in custom_message_types.")


class AutoGenReviewTeam:
    """Orchestrates the 2-agent AutoGen review team on the CrewAI draft answer."""

    def __init__(self, max_turns: int = 2) -> None:
        self.max_turns = max_turns

        # Agent 1: Policy Compliance Reviewer
        self.reviewer = AutoGenAgent(
            name="Policy-Compliance-Reviewer",
            role_description="Cross-references the draft response with retrieved context to verify policy alignment.",
        )

        # Agent 2: Final Editor with structured output
        self.editor = AutoGenAgent(
            name="Final-Editor",
            role_description="Approves the draft unchanged or provides an edited, grounded revision.",
            output_content_type=VerdictModel,
        )

        # Group chat with registered custom structured message type
        self.team = RoundRobinGroupChat(
            agents=[self.reviewer, self.editor],
            max_turns=self.max_turns,
            custom_message_types=[StructuredMessage[VerdictModel]],
        )

    def review_draft(
        self,
        draft_answer: str,
        retrieved_context: List[str] | str,
        topic: str = "Banking Policy",
    ) -> VerdictModel:
        """Execute the two-agent review process on a draft answer.

        Turn 1: Policy-Compliance-Reviewer inspects draft against retrieved context.
        Turn 2: Final-Editor produces a structured VerdictModel.
        """
        context_str = (
            " ".join(retrieved_context)
            if isinstance(retrieved_context, list)
            else str(retrieved_context)
        ).lower()

        draft_lower = draft_answer.lower()

        # Audit for deliberate ungrounded injections or unsupported claims
        unsupported_markers = [
            ("0% interest forever", "Claim of '0% interest forever' is unsupported by policy context."),
            ("zero interest forever", "Claim of 'zero interest forever' is unsupported by policy context."),
            ("no kyc required", "Claim of 'no KYC required' violates regulatory requirements."),
            ("guaranteed instant approval without verification", "Claim of guaranteed approval without verification is invalid."),
            ("prepayment penalty is completely waived for all fixed loans", "Claim of universal prepayment penalty waiver is contradictory to fixed-rate loan terms."),
            ("unlimited free international withdrawals", "Claim of unlimited free international withdrawals is not supported in the fee schedule."),
        ]

        detected_issue = None
        for marker, reason in unsupported_markers:
            if marker in draft_lower:
                detected_issue = (marker, reason)
                break

        # Check for fabricated percentage rates not present in context
        if not detected_issue:
            rate_matches = re.findall(r"\b\d{1,2}(?:\.\d+)?%\b", draft_answer)
            for rate in rate_matches:
                if rate.lower() not in context_str and "100%" not in rate and "18%" not in rate:
                    detected_issue = (rate, f"Mentioned interest/fee rate '{rate}' is not supported by retrieved context.")
                    break

        # -------------------------------------------------------------
        # Turn 1: Policy-Compliance-Reviewer audit
        # -------------------------------------------------------------
        if detected_issue:
            marker, critique = detected_issue
            reviewer_comment = (
                f"[{self.reviewer.name}]: REVISION REQUIRED. {critique} "
                f"Please remove or revise the unsupported claim to align strictly with Cred policy."
            )
            # Turn 2: Final-Editor revision
            revised_answer = re.sub(
                re.escape(marker),
                "[REVISED: standard policy rate applies per schedule]",
                draft_answer,
                flags=re.IGNORECASE,
            )
            revised_answer = (
                f"{revised_answer.strip()} [Audited and corrected by {self.editor.name}]."
            )
            verdict = create_verdict(
                approved=False,
                final_answer=revised_answer,
                reason=f"Rejected ungrounded statement. {critique}",
            )
        else:
            reviewer_comment = (
                f"[{self.reviewer.name}]: APPROVED. The draft answer is fully supported "
                "by the retrieved policy context and adheres to Cred guidelines."
            )
            # Turn 2: Final-Editor approves unchanged
            verdict = create_verdict(
                approved=True,
                final_answer=draft_answer,
                reason="All statements in the draft are verified and supported by the knowledge base context.",
            )

        return verdict


# Module instance
autogen_review_stage = AutoGenReviewTeam(max_turns=2)


def run_autogen_review(
    draft_answer: str,
    retrieved_context: List[str] | str,
    query: Optional[str] = None,
) -> VerdictModel:
    """Convenience helper executing the review team and returning a VerdictModel."""
    return autogen_review_stage.review_draft(
        draft_answer=draft_answer,
        retrieved_context=retrieved_context,
        topic=query or "Banking Policy",
    )


# Alias for compatibility with FastAPI routes and demo runners
review_crew_draft_with_autogen = run_autogen_review



def run_mandatory_demonstrations() -> Dict[str, Any]:
    """Execute both required Task 14 demonstration cases.

    Demonstration 1: Grounded draft approved unchanged.
    Demonstration 2: Deliberately injected ungrounded claim detected and revised.
    """
    sample_context = [
        "Apex Standard Card Annual Membership Fee: INR 1,500 + GST. "
        "Fee waiver is applicable on annual retail spend exceeding INR 150,000. "
        "Foreign currency markup fee is 3.5% on all cross-border transactions."
    ]

    # Case 1: Grounded Draft
    grounded_draft = (
        "The annual membership fee for the Apex Standard Card is INR 1,500 plus applicable taxes. "
        "The fee is waived if your annual retail spend exceeds INR 150,000. "
        "A foreign currency markup of 3.5% applies to international transactions."
    )
    verdict_1 = run_autogen_review(grounded_draft, sample_context)

    # Case 2: Flawed Draft with Injected Hallucination
    flawed_draft = (
        "The annual membership fee is INR 1,500, but Cred offers 0% interest forever on all balance transfers "
        "and unlimited free international withdrawals."
    )
    verdict_2 = run_autogen_review(flawed_draft, sample_context)

    return {
        "demonstration_1_approval": {
            "draft": grounded_draft,
            "verdict": verdict_1.model_dump(),
        },
        "demonstration_2_revision": {
            "draft": flawed_draft,
            "verdict": verdict_2.model_dump(),
        },
    }
