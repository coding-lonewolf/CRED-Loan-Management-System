"""Pydantic request and response models for FastAPI endpoints.

Task 11 requirements:
- Request/Response validation models for POST /ask and POST /add-document.
- WebSocket message models.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field

from schemas.response_schema import BankingResponse


class AskRequest(BaseModel):
    """Request payload for POST /ask."""
    query: str = Field(
        ...,
        min_length=2,
        description="The customer's question or loan status query.",
        examples=["What is the annual membership fee for the credit card?"],
    )
    session_id: Optional[str] = Field(
        default="default_session",
        description="Session identifier for maintaining multi-turn conversation context.",
        examples=["session_user_123"],
    )


class AskResponse(BaseModel):
    """Response payload for POST /ask."""
    trace_id: str = Field(..., description="Unique request correlation ID.")
    session_id: str = Field(..., description="Active session ID.")
    query: str = Field(..., description="Original user query.")
    sanitized_query: str = Field(..., description="Query with PII masked.")
    response: BankingResponse = Field(..., description="Structured multi-agent banking answer.")
    duration_ms: float = Field(..., description="Total processing time in milliseconds.")
    status: str = Field(default="SUCCESS", description="Execution status.")


class AddDocumentRequest(BaseModel):
    """Request payload for POST /add-document."""
    title: str = Field(
        ...,
        min_length=3,
        description="Title or topic of the banking policy document.",
        examples=["overdraft_protection_policy"],
    )
    content: str = Field(
        ...,
        min_length=10,
        description="Full markdown content of the policy document (minimum 2 sentences).",
    )
    category: Optional[str] = Field(
        default="General Policy",
        description="Banking category for the document.",
    )


class AddDocumentResponse(BaseModel):
    """Response payload for POST /add-document."""
    status: str = Field(..., description="Status of ingestion: 'SUCCESS' or 'FAILED'.")
    document_name: str = Field(..., description="Saved markdown file name.")
    message: str = Field(..., description="Detailed result message.")
    characters_indexed: int = Field(..., description="Number of characters saved to knowledge base.")


class ChatMessagePayload(BaseModel):
    """Payload for WebSocket multi-turn chat messages."""
    query: str = Field(..., description="User message.")
    session_id: Optional[str] = Field(default="ws_session", description="Session ID.")

