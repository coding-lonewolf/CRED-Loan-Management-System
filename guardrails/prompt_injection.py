"""Input-side prompt-injection detection guardrail for the Cred Banking Support Agent.

Task 10 (B) requirements:
- Deterministic heuristic and pattern-based detection of adversarial prompt injection,
  system instruction overrides, roleplay escapes, and data leakage attempts.
- Safely rejects or blocks the request prior to multi-agent invocation.
- Must be demonstrated firing on a deliberate test case.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# Suspicious instruction patterns targeting agent persona or system prompt overrides
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+(instructions|rules)", re.IGNORECASE),
    re.compile(r"(forget|bypass|override)\s+(your\s+)?(system\s+)?(prompt|rules|instructions)", re.IGNORECASE),
    re.compile(r"(reveal|print|show|dump)\s+(your\s+)?(initial|system|underlying)\s+(prompt|instructions)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan\s+mode|jailbroken|unrestricted)", re.IGNORECASE),
    re.compile(r"(system\s+prompt\s+override|instruction\s+injection|jailbreak)", re.IGNORECASE),
    re.compile(r"(system|admin)\s*:\s*(ignore|override|execute)", re.IGNORECASE),
    re.compile(r"pretend\s+(you\s+have\s+no\s+rules|you\s+are\s+not\s+a\s+banking\s+agent)", re.IGNORECASE),
]


def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Scan incoming user prompt for adversarial prompt injection patterns.

    Args:
        text: Raw user query or message string.

    Returns:
        tuple of (is_injection: bool, matched_reason: Optional[str])
    """
    if not text:
        return False, None

    normalized = " ".join(text.split())

    for pattern in INJECTION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            reason = f"Adversarial instruction pattern detected: '{match.group(0)}'"
            return True, reason

    return False, None


def validate_input_safety(text: str) -> Tuple[bool, str]:
    """Validate query safety before agent invocation.

    Returns:
        tuple of (is_safe: bool, message: str)
    """
    is_injection, reason = detect_prompt_injection(text)
    if is_injection:
        return False, f"Request blocked by safety guardrail: {reason}"
    return True, "Input cleared safety checks."

