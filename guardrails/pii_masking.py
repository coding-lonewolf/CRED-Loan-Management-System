"""Input-side PII masking guardrail for the Cred Banking Support Agent.

Task 10 (A) requirements:
- Fixed-format PII fields masked deterministically via regular expressions:
  1. PAN number (5 letters, 4 digits, 1 letter, e.g., 'ABCDE1234F')
  2. Aadhaar number (12 digits, e.g., '1234 5678 9012' or '123456789012')
  3. Bank account number (9 to 18 digits, e.g., '12345678901234')
- Note per guideline: Applicant names and income figures are unformatted free-text
  and acknowledged as out-of-scope for keyless, MOCK_LLM-only masking.
- Must be applied before processing and before writing logs to disk.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

# Exact regex patterns for fixed-format Indian banking identifiers
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
AADHAAR_REGEX = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
# Avoid matching standard 5-digit application numbers (CL-00001) or short codes by enforcing 9-18 digits
ACCOUNT_REGEX = re.compile(r"\b\d{9,18}\b")


def mask_pii(text: str) -> Tuple[str, Dict[str, int]]:
    """Mask fixed-format PII fields in the input string.

    Args:
        text: Raw user prompt or message string.

    Returns:
        tuple of (masked_text, counts_dict) detailing occurrences of redacted PII.
    """
    counts = {
        "pan": 0,
        "aadhaar": 0,
        "bank_account": 0,
    }

    if not text:
        return text, counts

    # 1. Mask PAN numbers
    pan_matches = PAN_REGEX.findall(text)
    if pan_matches:
        counts["pan"] = len(pan_matches)
        text = PAN_REGEX.sub("[PAN_REDACTED]", text)

    # 2. Mask Aadhaar numbers
    aadhaar_matches = AADHAAR_REGEX.findall(text)
    if aadhaar_matches:
        counts["aadhaar"] = len(aadhaar_matches)
        text = AADHAAR_REGEX.sub("[AADHAAR_REDACTED]", text)

    # 3. Mask Bank Account numbers
    account_matches = ACCOUNT_REGEX.findall(text)
    if account_matches:
        counts["bank_account"] = len(account_matches)
        text = ACCOUNT_REGEX.sub("[ACCOUNT_NUMBER_REDACTED]", text)

    return text, counts


def contains_pii(text: str) -> bool:
    """Return True if any supported fixed-format PII pattern is present."""
    if not text:
        return False
    return bool(
        PAN_REGEX.search(text)
        or AADHAAR_REGEX.search(text)
        or ACCOUNT_REGEX.search(text)
    )

