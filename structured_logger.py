"""Structured JSON-Lines logging for the Cred Banking Support Agent.

Task 12 requirements:
- Writes exactly one JSON object per request line (ELK-style structured logging).
- Records trace ID, ISO 8601 timestamp, request type, processing duration in ms, and status.
- Strict PII Guardrail: Fixed-format PII fields (PAN, Aadhaar, Bank Account) are ALWAYS
  masked BEFORE being written to disk so raw customer secrets never reach log storage.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from guardrails.pii_masking import mask_pii

LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOGS_DIR / "application.jsonl"

_log_lock = threading.Lock()


class StructuredLogger:
    """Thread-safe structured JSON-Lines logger enforcing pre-write PII sanitization."""

    def __init__(self, log_path: Path = LOG_FILE) -> None:
        self.log_path = log_path
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_trace_id(self) -> str:
        """Create a unique correlation trace ID."""
        return f"trace_{uuid.uuid4().hex[:16]}"

    def log_request(
        self,
        trace_id: str,
        request_type: str,
        endpoint: str,
        raw_input: str,
        query_type: str,
        status: str,
        duration_ms: float,
        session_id: Optional[str] = None,
        error_message: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Sanitize raw inputs and write a structured JSONL entry to disk."""
        # 1. Strictly apply PII masking before persisting to disk
        sanitized_text, pii_counts = mask_pii(raw_input)

        entry: Dict[str, Any] = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_type": request_type,
            "endpoint": endpoint,
            "query_type": query_type,
            "status": status,
            "request_duration_ms": round(duration_ms, 2),
            "session_id": session_id or "unassigned",
            "sanitized_input": sanitized_text,
            "pii_detected": pii_counts,
        }

        if error_message:
            entry["error"] = error_message

        if extra_metadata:
            entry["metadata"] = extra_metadata

        line = json.dumps(entry, ensure_ascii=False)

        # Thread-safe write to JSONL file
        with _log_lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        return entry


# Singleton logger instance
structured_logger = StructuredLogger()

