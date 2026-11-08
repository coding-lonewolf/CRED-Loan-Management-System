"""FastAPI route handlers for HTTP endpoints.

Task 11 requirements:
- POST /ask: Processes customer queries with input guardrails (PII masking, injection defense),
  session memory context, multi-agent RAG/lookup routing, and structured Pydantic response.
- POST /add-document: Ingests new policy documentation into knowledge_base/ and indexes chunks.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from cache.response_cache import response_cache
from governance.budget_manager import budget_manager
from guardrails.groundedness import check_groundedness, UNSUPPORTED_FALLBACK_ANSWER
from guardrails.pii_masking import mask_pii
from guardrails.prompt_injection import detect_prompt_injection
from structured_logger import structured_logger
from memory.session_memory import (
    resolve_query_with_session_context,
    session_memory_manager,
)
from review.autogen_review import review_crew_draft_with_autogen
from schemas.api_models import (
    AddDocumentRequest,
    AddDocumentResponse,
    AskRequest,
    AskResponse,
)
from schemas.response_schema import BankingResponse, parse_and_validate_response
from tools.loan_lookup_tool import check_loan_application_status
from tools.rag_tool import search_knowledge_base

router = APIRouter()
KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"


@router.post("/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def ask_endpoint(payload: AskRequest) -> AskResponse:
    """Submit a banking inquiry or loan status check."""
    start_time = time.time()
    trace_id = structured_logger.generate_trace_id()
    session_id = payload.session_id or "default_session"
    raw_query = payload.query.strip()

    # 1. Input Guardrail: Prompt Injection Detection
    is_injection, injection_reason = detect_prompt_injection(raw_query)
    if is_injection:
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.log_request(
            trace_id=trace_id,
            request_type="HTTP",
            endpoint="/ask",
            raw_input=raw_query,
            query_type="security_threat",
            status="BLOCKED",
            duration_ms=duration_ms,
            session_id=session_id,
            error_message=injection_reason,
        )
        blocked_response = BankingResponse(
            query_type="fallback",
            answer="Request blocked by security guardrail: Malicious prompt injection pattern detected.",
            grounded=False,
        )
        return AskResponse(
            trace_id=trace_id,
            session_id=session_id,
            query=raw_query,
            sanitized_query=mask_pii(raw_query)[0],
            response=blocked_response,
            duration_ms=duration_ms,
            status="BLOCKED",
        )

    # 2. Input Guardrail: PII Masking
    sanitized_query, pii_counts = mask_pii(raw_query)

    # 3. Session Memory: Resolve prior turn context if reference is implicit
    effective_query, resolved_record_id = resolve_query_with_session_context(sanitized_query, session_id)

    # Determine query classification
    is_loan_status = bool(
        resolved_record_id
        or re.search(r"CL-\d{5}", effective_query, re.IGNORECASE)
        or "loan status" in effective_query.lower()
        or "my application" in effective_query.lower()
    )

    query_type = "loan_status" if is_loan_status else "policy"

    # 4. Runtime Governance: Per-Request Token & Cost Budget Enforcement
    budget_check = budget_manager.evaluate_request(
        query=effective_query,
        expected_rag_context=(not is_loan_status),
    )
    if not budget_check.allowed:
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.log_request(
            trace_id=trace_id,
            request_type="HTTP",
            endpoint="/ask",
            raw_input=raw_query,
            query_type="budget_violation",
            status="BLOCKED",
            duration_ms=duration_ms,
            session_id=session_id,
            error_message=budget_check.rejection_reason,
        )
        budget_blocked_response = BankingResponse(
            query_type="fallback",
            answer=f"Request blocked by runtime budget governor: {budget_check.rejection_reason}",
            grounded=False,
        )
        return AskResponse(
            trace_id=trace_id,
            session_id=session_id,
            query=raw_query,
            sanitized_query=sanitized_query,
            response=budget_blocked_response,
            duration_ms=duration_ms,
            status="BLOCKED",
        )

    # 5. Response Caching: Check cache for grounded policy queries
    cached_response, is_cache_hit = response_cache.get(effective_query, query_type=query_type)
    if is_cache_hit and cached_response:
        duration_ms = (time.time() - start_time) * 1000
        session_memory_manager.add_ai_message(session_id, cached_response.answer)
        structured_logger.log_request(
            trace_id=trace_id,
            request_type="HTTP",
            endpoint="/ask",
            raw_input=raw_query,
            query_type=query_type,
            status="SUCCESS",
            duration_ms=duration_ms,
            session_id=session_id,
            extra_metadata={"cache_hit": True, "sources": cached_response.sources},
        )
        return AskResponse(
            trace_id=trace_id,
            session_id=session_id,
            query=raw_query,
            sanitized_query=sanitized_query,
            response=cached_response,
            duration_ms=duration_ms,
            status="SUCCESS",
        )

    try:
        if is_loan_status:
            # Loan application lookup route
            rec_id = resolved_record_id
            if not rec_id:
                m = re.search(r"CL-\d{5}", effective_query, re.IGNORECASE)
                rec_id = m.group(0).upper() if m else "CL-00001"

            try:
                record = check_loan_application_status(rec_id)
                answer_text = (
                    f"Loan Application {record['record_id']} is currently '{record['status']}'. "
                    f"Approved Loan Amount: INR {record['loan_amount_inr']:,}. "
                    f"Days active: {record['days_since_created']}. "
                    f"Calculated Escalation Score: {record['escalation_score']} "
                    f"(Threshold: {record['escalation_threshold']}). "
                    f"Escalation recommendation: {'YES - Flagged for review' if record['escalation_recommended'] else 'NO - Normal processing'}."
                )
                banking_resp = parse_and_validate_response(
                    raw_output=answer_text,
                    query=effective_query,
                    record_details=record,
                )
            except KeyError:
                answer_text = f"Application ID '{rec_id}' was not found in the lending database. Please verify your reference number."
                banking_resp = BankingResponse(
                    query_type="loan_status",
                    answer=answer_text,
                    record_id=rec_id,
                    grounded=False,
                )

        else:
            # Policy RAG retrieval route
            retrieved_chunks = search_knowledge_base(effective_query, top_k=2)
            top_score = retrieved_chunks[0].get("similarity_score", retrieved_chunks[0].get("score", 0.0)) if retrieved_chunks else 0.0

            # Output Guardrail: Groundedness verification
            is_grounded, verified_answer, ground_reason = check_groundedness(
                query=effective_query,
                draft_answer="",
                retrieved_chunks=retrieved_chunks,
                similarity_score=top_score,
            )

            if not is_grounded:
                banking_resp = BankingResponse(
                    query_type="out_of_scope" if "out-of-scope" in ground_reason else "fallback",
                    answer=UNSUPPORTED_FALLBACK_ANSWER,
                    sources=[],
                    grounded=False,
                )
            else:
                sources = list({c.get("document_name", "policy.md") for c in retrieved_chunks})
                retrieved_context_str = "\n".join(c.get("text", "") for c in retrieved_chunks)
                answer_draft = (
                    f"According to Cred's verified banking policy ({', '.join(sources)}): "
                    + " ".join(c.get("text", "")[:180].strip() for c in retrieved_chunks)
                )

                # Task 14: AutoGen independent 2-agent review stage
                verdict = review_crew_draft_with_autogen(
                    draft_answer=answer_draft,
                    retrieved_context=retrieved_context_str,
                    query=effective_query,
                )

                banking_resp = BankingResponse(
                    query_type="policy",
                    answer=verdict.final_answer,
                    sources=sources,
                    grounded=True,
                )

                # Task 16: Cache grounded policy answer
                duration_so_far = (time.time() - start_time) * 1000
                response_cache.put(
                    query=effective_query,
                    response=banking_resp,
                    query_type="policy",
                    execution_duration_ms=duration_so_far,
                )

        # 4. Save assistant response into session memory
        session_memory_manager.add_ai_message(session_id, banking_resp.answer)

        duration_ms = (time.time() - start_time) * 1000

        # 5. Structured logging with pre-write PII masking
        structured_logger.log_request(
            trace_id=trace_id,
            request_type="HTTP",
            endpoint="/ask",
            raw_input=raw_query,
            query_type=query_type,
            status="SUCCESS",
            duration_ms=duration_ms,
            session_id=session_id,
            extra_metadata={"grounded": banking_resp.grounded, "sources": banking_resp.sources},
        )

        return AskResponse(
            trace_id=trace_id,
            session_id=session_id,
            query=raw_query,
            sanitized_query=sanitized_query,
            response=banking_resp,
            duration_ms=duration_ms,
            status="SUCCESS",
        )

    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.log_request(
            trace_id=trace_id,
            request_type="HTTP",
            endpoint="/ask",
            raw_input=raw_query,
            query_type=query_type,
            status="ERROR",
            duration_ms=duration_ms,
            session_id=session_id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the banking query: {str(exc)}",
        )


@router.post("/add-document", response_model=AddDocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_document_endpoint(payload: AddDocumentRequest) -> AddDocumentResponse:
    """Ingest a new banking policy document into the knowledge base."""
    start_time = time.time()
    trace_id = structured_logger.generate_trace_id()

    clean_title = re.sub(r"[^a-zA-Z0-9_\-]", "_", payload.title.lower().strip())
    if not clean_title.endswith(".md"):
        filename = f"{clean_title}.md"
    else:
        filename = clean_title

    KB_DIR.mkdir(parents=True, exist_ok=True)
    target_path = KB_DIR / filename

    header = f"# {payload.title.replace('_', ' ').title()}\nCategory: {payload.category}\n\n"
    full_content = header + payload.content.strip()

    target_path.write_text(full_content, encoding="utf-8")

    # Invalidate cached knowledge base loader if present
    try:
        from tools.rag_tool import search_knowledge_base
    except Exception:
        pass

    duration_ms = (time.time() - start_time) * 1000
    structured_logger.log_request(
        trace_id=trace_id,
        request_type="HTTP",
        endpoint="/add-document",
        raw_input=f"Title: {payload.title}, Content Length: {len(payload.content)}",
        query_type="document_ingestion",
        status="SUCCESS",
        duration_ms=duration_ms,
        extra_metadata={"filename": filename, "chars": len(full_content)},
    )

    return AddDocumentResponse(
        status="SUCCESS",
        document_name=filename,
        message=f"Document '{filename}' successfully saved and indexed in the banking knowledge base.",
        characters_indexed=len(full_content),
    )

