"""Deterministic MOCK_LLM implementation extending CrewAI's BaseLLM.

Task 7 & Submission Guidelines requirements:
1. Extends `crewai.llms.base_llm.BaseLLM` (CrewAI's documented non-litellm extension point).
2. Operates with ZERO network access and ZERO API keys.
3. Pitfall 1 Avoidance:
   CrewAI's ReAct system template contains the literal example "Observation: the result of the action".
   We explicitly parse real model turns/observations and ignore system prompt template examples.
4. Pitfall 2 Avoidance:
   Dispatches tool calls using declared argument schemas (`args_schema`) rather than tool name substrings.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, List, Type

from crewai.llms.base_llm import BaseLLM
from pydantic import BaseModel, Field


class MockLLM(BaseLLM):
    """Deterministic, keyless Mock LLM for CrewAI multi-agent orchestration."""

    model: str = Field(default="mock-llm-v1", description="Model identifier")
    llm_type: str = Field(default="custom", description="LLM provider type")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _extract_conversation_text(self, messages: str | list[Any]) -> str:
        """Flatten message structures into a string."""
        if isinstance(messages, str):
            return messages
        if isinstance(messages, list):
            parts = []
            for m in messages:
                if isinstance(m, dict):
                    parts.append(m.get("content", ""))
                elif hasattr(m, "content"):
                    parts.append(str(m.content))
                else:
                    parts.append(str(m))
            return "\n".join(parts)
        return str(messages)

    def _find_actual_observation(self, conv_text: str) -> str | None:
        """Extract genuine tool execution observation, ignoring template examples.

        Pitfall 1: Avoid matching 'Observation: the result of the action'.
        """
        # Find all occurrences of Observation:
        matches = list(re.finditer(r"Observation:\s*(.+?)(?=\n(?:Thought|Action|Final Answer)|$)", conv_text, re.DOTALL | re.IGNORECASE))
        for m in reversed(matches):
            obs_text = m.group(1).strip()
            # Ignore template placeholder text
            if "the result of the action" in obs_text.lower():
                continue
            if len(obs_text) > 0:
                return obs_text
        return None

    def _dispatch_by_schema(self, tools: list[Any], task_text: str) -> tuple[str, dict[str, Any]] | None:
        """Select tool and construct arguments based strictly on declared schema.

        Pitfall 2: Match args_schema fields, never match tool name strings.
        """
        if not tools:
            return None

        for tool in tools:
            # Check declared args_schema
            schema: Type[BaseModel] | None = getattr(tool, "args_schema", None)
            tool_name = getattr(tool, "name", "tool")

            if schema and hasattr(schema, "model_fields"):
                fields = schema.model_fields
                # Schema requiring record_id (Loan lookup)
                if "record_id" in fields:
                    id_match = re.search(r"CL-\d{5}", task_text, re.IGNORECASE)
                    record_id = id_match.group(0).upper() if id_match else "CL-00001"
                    return tool_name, {"record_id": record_id}

                # Schema requiring query (RAG policy retrieval)
                if "query" in fields:
                    # Clean up prompt text to find query
                    cleaned_query = task_text
                    for prefix in ["Current Task:", "Task:", "Query:", "Question:"]:
                        if prefix in cleaned_query:
                            cleaned_query = cleaned_query.split(prefix)[-1]
                    cleaned_query = cleaned_query.strip().split("\n")[0][:120]
                    return tool_name, {"query": cleaned_query}

        # Fallback if no schema matched
        first_tool = tools[0]
        return getattr(first_tool, "name", "tool"), {}

    def call(
        self,
        messages: str | list[Any],
        tools: list[Any] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any = None,
        from_agent: Any = None,
        response_model: type[BaseModel] | None = None,
    ) -> str | Any:
        """Generate deterministic ReAct turns for CrewAI execution."""
        conv_text = self._extract_conversation_text(messages)
        agent_role = getattr(from_agent, "role", "") if from_agent else ""

        # Step 1: Check if a genuine tool observation exists in the conversation
        observation = self._find_actual_observation(conv_text)

        if observation:
            # Tool has returned an actual result -> Generate Final Answer
            if "Retrieval" in agent_role or "RAG" in agent_role:
                return (
                    "Thought: I have reviewed the retrieved banking policy context.\n"
                    f"Final Answer: Policy Information: {observation}"
                )
            elif "Lookup" in agent_role:
                return (
                    "Thought: I have obtained the verified loan application status and escalation score.\n"
                    f"Final Answer: Loan Application Status: {observation}"
                )
            else:
                return (
                    "Thought: I have processed the tool result.\n"
                    f"Final Answer: {observation}"
                )

        # Step 2: No observation yet -> Decide whether to call a tool or produce an answer
        available_tools = getattr(from_agent, "tools", []) if from_agent else (tools or [])

        if available_tools:
            dispatch = self._dispatch_by_schema(available_tools, conv_text)
            if dispatch:
                tool_name, tool_args = dispatch
                args_json = json.dumps(tool_args)
                return (
                    f"Thought: I need to use the appropriate tool to complete this task.\n"
                    f"Action: {tool_name}\n"
                    f"Action Input: {args_json}"
                )

        # Step 3: No tools required (e.g., Response Composer agent)
        if "Composer" in agent_role or "Response" in agent_role:
            # Check if previous context exists in conversation
            loan_id_match = re.search(r"CL-\d{5}", conv_text)
            loan_id = loan_id_match.group(0) if loan_id_match else "CL-00001"

            if "loan application" in conv_text.lower() or "status" in conv_text.lower():
                return (
                    "Thought: I will synthesize the loan lookup details into a clear member response.\n"
                    f"Final Answer: Based on lending operations records for Application {loan_id}: "
                    "The application status is Under Review with an escalation score within normal bounds. "
                    "No immediate risk escalation is required at this stage."
                )
            else:
                return (
                    "Thought: I will synthesize the retrieved banking policy details into a complete response.\n"
                    "Final Answer: According to Cred's policy guidelines, eligibility and fee calculations "
                    "are strictly governed by the official credit rules and reducing balance calculation formulas."
                )

        # Default fallback
        return (
            "Thought: I have sufficient information to conclude the request.\n"
            "Final Answer: Request successfully processed by the banking support agent."
        )


# Export standard mock_llm instance
mock_llm = MockLLM()

