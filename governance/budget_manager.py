"""Runtime layer per-request token and cost budget manager.

Task 15 requirements:
- Runtime Layer governance control.
- Enforce per-request token/cost budget cap (e.g., 2,000 tokens / $0.05 simulated budget).
- Calculate deterministic token and cost estimation for queries:
    - Token heuristic: ~1 token per 4 characters of input text.
    - System prompt and orchestration overhead: ~400 tokens.
    - RAG retrieval chunk overhead: ~600 tokens.
- Intercept and reject intentionally oversized requests (e.g., >2,000 tokens).
- Maintain an audit log of budget checks, approvals, and rejections.
- Clarification: Under MOCK_LLM, token and cost estimations are deterministic
  architectural simulations for governance validation, not live API billing.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BudgetExceededError(ValueError):
    """Raised when an incoming request exceeds the allocated runtime token or cost budget."""

    def __init__(self, estimated_tokens: int, budget_limit: int, reason: str) -> None:
        message = (
            f"Runtime Governance Budget Exceeded: Request requires ~{estimated_tokens} tokens, "
            f"exceeding the per-request limit of {budget_limit} tokens. {reason}"
        )
        super().__init__(message)
        self.estimated_tokens = estimated_tokens
        self.budget_limit = budget_limit


@dataclass
class BudgetCheckResult:
    """Represents the outcome of a runtime budget inspection."""

    allowed: bool
    estimated_input_tokens: int
    estimated_overhead_tokens: int
    total_estimated_tokens: int
    budget_limit_tokens: int
    estimated_cost_usd: float
    budget_limit_cost_usd: float
    rejection_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_overhead_tokens": self.estimated_overhead_tokens,
            "total_estimated_tokens": self.total_estimated_tokens,
            "budget_limit_tokens": self.budget_limit_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "budget_limit_cost_usd": round(self.budget_limit_cost_usd, 4),
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp,
        }


class BudgetManager:
    """Manages and enforces per-request token and cost runtime budgets."""

    # Default per-request token ceiling
    DEFAULT_MAX_TOKENS: int = 2000
    # Simulated blended pricing per 1,000 tokens ($0.000025/token = $0.05 / 2,000 tokens)
    PRICE_PER_TOKEN_USD: float = 0.000025

    # Standard overhead allocations for banking multi-agent orchestration
    BASE_SYSTEM_OVERHEAD_TOKENS: int = 350
    BASE_RAG_CONTEXT_TOKENS: int = 450

    def __init__(
        self,
        max_tokens_per_request: int = DEFAULT_MAX_TOKENS,
        price_per_token_usd: float = PRICE_PER_TOKEN_USD,
    ) -> None:
        self.max_tokens = max_tokens_per_request
        self.price_per_token = price_per_token_usd
        self.max_cost_usd = max_tokens_per_request * price_per_token_usd
        self.audit_log: List[BudgetCheckResult] = []

    def estimate_tokens(self, text: str) -> int:
        """Deterministic token estimation based on whitespace tokenization and character count.

        Formula: max(words * 1.33, chars / 3.8)
        """
        if not text:
            return 0
        stripped = text.strip()
        word_count = len(stripped.split())
        char_count = len(stripped)
        return int(math.ceil(max(word_count * 1.33, char_count / 3.8)))

    def evaluate_request(
        self,
        query: str,
        expected_rag_context: bool = True,
        system_overhead: Optional[int] = None,
    ) -> BudgetCheckResult:
        """Evaluate an incoming query against per-request runtime limits.

        Args:
            query: The customer query text.
            expected_rag_context: Whether RAG chunks will be retrieved and injected.
            system_overhead: Custom system prompt token overhead if specified.

        Returns:
            BudgetCheckResult indicating approval or rejection.
        """
        input_tokens = self.estimate_tokens(query)

        overhead = system_overhead if system_overhead is not None else self.BASE_SYSTEM_OVERHEAD_TOKENS
        if expected_rag_context:
            overhead += self.BASE_RAG_CONTEXT_TOKENS

        total_tokens = input_tokens + overhead
        estimated_cost = total_tokens * self.price_per_token

        if total_tokens > self.max_tokens:
            reason = (
                f"Query payload is too large ({input_tokens} input tokens + {overhead} overhead tokens = "
                f"{total_tokens} total > {self.max_tokens} limit). Rejection enforced to prevent resource starvation."
            )
            result = BudgetCheckResult(
                allowed=False,
                estimated_input_tokens=input_tokens,
                estimated_overhead_tokens=overhead,
                total_estimated_tokens=total_tokens,
                budget_limit_tokens=self.max_tokens,
                estimated_cost_usd=estimated_cost,
                budget_limit_cost_usd=self.max_cost_usd,
                rejection_reason=reason,
            )
        else:
            result = BudgetCheckResult(
                allowed=True,
                estimated_input_tokens=input_tokens,
                estimated_overhead_tokens=overhead,
                total_estimated_tokens=total_tokens,
                budget_limit_tokens=self.max_tokens,
                estimated_cost_usd=estimated_cost,
                budget_limit_cost_usd=self.max_cost_usd,
                rejection_reason=None,
            )

        self.audit_log.append(result)
        return result

    def enforce_request_budget(
        self,
        query: str,
        expected_rag_context: bool = True,
    ) -> BudgetCheckResult:
        """Validate request budget; raises BudgetExceededError if budget is exceeded.

        Args:
            query: The customer query text.
            expected_rag_context: Whether RAG retrieval is anticipated.

        Returns:
            BudgetCheckResult if permitted.

        Raises:
            BudgetExceededError: If the token ceiling is exceeded.
        """
        result = self.evaluate_request(query, expected_rag_context=expected_rag_context)
        if not result.allowed:
            raise BudgetExceededError(
                estimated_tokens=result.total_estimated_tokens,
                budget_limit=result.budget_limit_tokens,
                reason=result.rejection_reason or "Request exceeds budget ceiling.",
            )
        return result

    def get_audit_summary(self) -> Dict[str, Any]:
        """Return aggregated audit statistics for the runtime budget."""
        total = len(self.audit_log)
        allowed_count = sum(1 for r in self.audit_log if r.allowed)
        rejected_count = total - allowed_count
        return {
            "total_inspections": total,
            "approved_requests": allowed_count,
            "rejected_requests": rejected_count,
            "max_budget_limit_tokens": self.max_tokens,
            "max_cost_limit_usd": self.max_cost_usd,
        }


# Global singleton instance for application runtime
budget_manager = BudgetManager(max_tokens_per_request=2000)

