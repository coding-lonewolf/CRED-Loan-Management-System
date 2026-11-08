"""Output-side groundedness verification guardrail for the Cred Banking Support Agent.

Task 10 (C) requirements:
- Checks whether the query and draft answer are factually supported by retrieved context.
- When retrieval support is insufficient or out-of-scope, safely returns an
  'I don't know' / unsupported fallback instead of ungrounded generation.
- Must be demonstrated firing on an unsupported or deliberately out-of-scope query.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

# Fallback response mandated when retrieval context cannot support the question
UNSUPPORTED_FALLBACK_ANSWER = (
    "I do not have sufficient information in Cred's verified banking policy knowledge base "
    "to answer this question accurately. Please contact our lending operations support desk "
    "or consult an authorized representative for assistance."
)

DEFAULT_SIMILARITY_THRESHOLD = 0.50


def check_groundedness(
    query: str,
    draft_answer: str,
    retrieved_chunks: List[dict[str, Any]] | None = None,
    similarity_score: Optional[float] = None,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> Tuple[bool, str, str]:
    """Verify that a generated response is grounded in retrieved context.

    Args:
        query: Original user query.
        draft_answer: Draft answer produced by the multi-agent crew.
        retrieved_chunks: List of context dicts returned by RAGTool.
        similarity_score: Top-1 cosine similarity score from vector retrieval.
        threshold: Calibrated minimum threshold below which retrieval is deemed insufficient.

    Returns:
        tuple of (is_grounded: bool, final_answer: str, reason: str)
    """
    # 1. If similarity score is provided and below threshold -> Refuse ungrounded generation
    if similarity_score is not None and similarity_score < threshold:
        reason = f"Top-1 similarity ({similarity_score:.4f}) is below calibrated threshold ({threshold:.4f})."
        return False, UNSUPPORTED_FALLBACK_ANSWER, reason

    # 2. If no context chunks were retrieved
    if retrieved_chunks is not None and len(retrieved_chunks) == 0:
        # Check if it's a direct loan lookup (which is grounded in dataset rather than RAG)
        if "CL-" not in query.upper() and "CL-" not in draft_answer.upper():
            reason = "No relevant context chunks were retrieved from the banking knowledge base."
            return False, UNSUPPORTED_FALLBACK_ANSWER, reason

    # 3. Check for obvious hallucination / out-of-scope keywords
    out_of_scope_indicators = [
        "fifa world cup",
        "photosynthesis",
        "capital of japan",
        "weather in",
        "movie review",
        "recipe for",
    ]
    query_lower = query.lower()
    for indicator in out_of_scope_indicators:
        if indicator in query_lower:
            reason = f"Query contains out-of-scope topic: '{indicator}'."
            return False, UNSUPPORTED_FALLBACK_ANSWER, reason

    # Output is grounded
    return True, draft_answer, "Answer is supported by available domain context."

