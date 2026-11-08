"""Session-based conversation memory for the Cred Banking Support Agent.

Task 8 requirements:
- In-process conversation memory using LangChain's InMemoryChatMessageHistory.
- Maintains conversation history across turns within one process run for a given session ID.
- Demonstrates context carry-over across turns (e.g. recalling application ID CL-00001).
- Demonstrates fresh-session reset (a new session ID starts with completely empty context).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class SessionMemoryManager:
    """Manages in-process multi-turn conversation memory keyed by session_id."""

    def __init__(self) -> None:
        self._store: Dict[str, InMemoryChatMessageHistory] = {}

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """Retrieve or initialize the message history for a given session."""
        if not session_id:
            session_id = "default_session"
        if session_id not in self._store:
            self._store[session_id] = InMemoryChatMessageHistory()
        return self._store[session_id]

    def add_user_message(self, session_id: str, message: str) -> None:
        """Record a user query into the session history."""
        history = self.get_session_history(session_id)
        history.add_user_message(message)

    def add_ai_message(self, session_id: str, message: str) -> None:
        """Record an assistant response into the session history."""
        history = self.get_session_history(session_id)
        history.add_ai_message(message)

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Return all messages for the given session."""
        return self.get_session_history(session_id).messages

    def get_history_summary(self, session_id: str) -> str:
        """Format the dialogue history into a plain text summary for prompt injection."""
        messages = self.get_messages(session_id)
        if not messages:
            return ""
        formatted = []
        for msg in messages:
            speaker = "Customer" if isinstance(msg, HumanMessage) else "Support Agent"
            formatted.append(f"{speaker}: {msg.content}")
        return "\n".join(formatted)

    def extract_prior_record_id(self, session_id: str) -> str | None:
        """Scan prior dialogue turns to extract previously mentioned loan application ID (CL-XXXXX)."""
        messages = self.get_messages(session_id)
        for msg in reversed(messages):
            match = re.search(r"CL-\d{5}", str(msg.content), re.IGNORECASE)
            if match:
                return match.group(0).upper()
        return None

    def clear_session(self, session_id: str) -> None:
        """Clear conversation memory for a session (used to demonstrate fresh session reset)."""
        if session_id in self._store:
            self._store[session_id].clear()
            del self._store[session_id]

    def has_session(self, session_id: str) -> bool:
        """Check if a session exists with messages."""
        return session_id in self._store and len(self._store[session_id].messages) > 0


# Global singleton instance for in-process memory
session_memory_manager = SessionMemoryManager()


def resolve_query_with_session_context(query: str, session_id: str) -> tuple[str, str | None]:
    """Enrich the incoming query with prior session memory if application ID is omitted.

    Returns:
        tuple of (effective_query, extracted_record_id)
    """
    # Check if query already has record_id
    id_match = re.search(r"CL-\d{5}", query, re.IGNORECASE)
    if id_match:
        record_id = id_match.group(0).upper()
        session_memory_manager.add_user_message(session_id, query)
        return query, record_id

    # Check prior history if record_id omitted
    prior_id = session_memory_manager.extract_prior_record_id(session_id)
    if prior_id and ("status" in query.lower() or "application" in query.lower() or "it" in query.lower()):
        enriched_query = f"{query} (Context from prior turn: Application {prior_id})"
        session_memory_manager.add_user_message(session_id, query)
        return enriched_query, prior_id

    session_memory_manager.add_user_message(session_id, query)
    return query, None

