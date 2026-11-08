"""FastAPI WebSocket endpoint for real-time multi-turn banking chat.

Task 11 requirements:
- Real-time multi-turn chat over WebSocket (@app.websocket).
- Maintains session context across messages in a connection.
- Gracefully handles client disconnects (catches WebSocketDisconnect, keeps the server running).
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from guardrails.pii_masking import mask_pii
from guardrails.prompt_injection import detect_prompt_injection
from structured_logger import structured_logger
from memory.session_memory import (
    resolve_query_with_session_context,
    session_memory_manager,
)
from tools.loan_lookup_tool import check_loan_application_status
from tools.rag_tool import search_knowledge_base

ws_router = APIRouter()


@ws_router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """Handle multi-turn real-time chat with graceful disconnect resilience."""
    await websocket.accept()
    session_id = f"ws_session_{uuid.uuid4().hex[:8]}"

    # Welcome handshake
    await websocket.send_json({
        "sender": "Cred Support Agent",
        "message": "Connected to Cred Banking Support. How may I assist you with your loans or account today?",
        "session_id": session_id,
    })

    try:
        while True:
            # Await message from client
            raw_data = await websocket.receive_text()
            start_time = time.time()
            trace_id = structured_logger.generate_trace_id()

            # Parse input payload
            try:
                payload = json.loads(raw_data)
                user_msg = payload.get("query", "").strip()
                if not user_msg and "message" in payload:
                    user_msg = payload.get("message", "").strip()
            except Exception:
                user_msg = raw_data.strip()

            if not user_msg:
                continue

            # 1. Prompt injection guardrail
            is_injection, reason = detect_prompt_injection(user_msg)
            if is_injection:
                duration_ms = (time.time() - start_time) * 1000
                structured_logger.log_request(
                    trace_id=trace_id,
                    request_type="WebSocket",
                    endpoint="/ws/chat",
                    raw_input=user_msg,
                    query_type="security_threat",
                    status="BLOCKED",
                    duration_ms=duration_ms,
                    session_id=session_id,
                    error_message=reason,
                )
                await websocket.send_json({
                    "sender": "Cred Support Agent",
                    "status": "BLOCKED",
                    "message": "Your message was blocked by security policies: Adversarial pattern detected.",
                    "session_id": session_id,
                })
                continue

            # 2. PII Masking
            sanitized_input, pii_counts = mask_pii(user_msg)

            # 3. Context resolution from session memory
            effective_query, resolved_record_id = resolve_query_with_session_context(sanitized_input, session_id)

            # Route query
            is_loan = bool(resolved_record_id or "CL-" in effective_query.upper())
            query_type = "loan_status" if is_loan else "policy"

            if is_loan:
                rec_id = resolved_record_id or "CL-00001"
                try:
                    record = check_loan_application_status(rec_id)
                    reply = (
                        f"Application {record['record_id']} status is '{record['status']}'. "
                        f"Amount: INR {record['loan_amount_inr']:,}. "
                        f"Escalation Score: {record['escalation_score']} (Threshold: {record['escalation_threshold']})."
                    )
                except KeyError:
                    reply = f"Loan application '{rec_id}' was not found in our records."
            else:
                chunks = search_knowledge_base(effective_query, top_k=1)
                if chunks:
                    reply = f"Policy Reference ({chunks[0].get('document_name', 'policy')}): {chunks[0].get('text', '')[:200]}"
                else:
                    reply = "I do not have sufficient information in our verified banking policy base to answer this question."

            # Save assistant reply to memory
            session_memory_manager.add_ai_message(session_id, reply)

            duration_ms = (time.time() - start_time) * 1000
            structured_logger.log_request(
                trace_id=trace_id,
                request_type="WebSocket",
                endpoint="/ws/chat",
                raw_input=user_msg,
                query_type=query_type,
                status="SUCCESS",
                duration_ms=duration_ms,
                session_id=session_id,
            )

            # Emit reply back to client
            await websocket.send_json({
                "sender": "Cred Support Agent",
                "message": reply,
                "session_id": session_id,
                "query_type": query_type,
                "duration_ms": round(duration_ms, 2),
            })

    except WebSocketDisconnect:
        # Graceful handling of client disconnect without crashing server
        print(f"[WebSocket] Client disconnected gracefully from session: {session_id}")
    except Exception as exc:
        print(f"[WebSocket] Exception in session {session_id}: {exc}")
        try:
            await websocket.close()
        except Exception:
            pass

