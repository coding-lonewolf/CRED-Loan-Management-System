"""CrewAI multi-agent crew orchestration for the Cred Banking Support Agent.

Task 7 requirements:
1. Multi-agent crew with at least 3 agents:
   - Retrieval Agent equipped with RAG tool
   - Lookup Agent equipped with check_loan_application_status tool
   - Response Composer combining outputs into one draft answer
2. Executed via `.kickoff()`.
3. Telemetry strictly disabled (`CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`, `CREWAI_TRACING_ENABLED=false`).
4. Demonstrable tool invocations on:
   - Policy query (e.g. EMI calculation, credit score, fees) -> triggers RAG tool
   - Application query (e.g. status of CL-00001) -> triggers lookup tool
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Enforce zero-network, local telemetry isolation before any CrewAI imports
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["LOCALAPPDATA"] = str(Path(__file__).resolve().parent.parent / ".appdata")

from crewai import Crew, Process, Task

from agents.composer_agent import create_composer_agent
from agents.lookup_agent import create_lookup_agent
from agents.mock_llm import mock_llm
from agents.retrieval_agent import create_retrieval_agent


def build_banking_crew(
    query: str,
    query_type: str = "auto",
    verbose: bool = True,
) -> Crew:
    """Build a specialized CrewAI crew tailored to the incoming query.

    Args:
        query: Customer query string (e.g., 'What is my loan status for CL-00001?'
               or 'How is EMI calculated for reducing balance loans?').
        query_type: 'auto', 'policy', or 'loan_status'.
        verbose: Enable detailed logging during kickoff.

    Returns:
        Configured Crew ready for `.kickoff()`.
    """
    retrieval_agent = create_retrieval_agent(llm=mock_llm, verbose=verbose)
    lookup_agent = create_lookup_agent(llm=mock_llm, verbose=verbose)
    composer_agent = create_composer_agent(llm=mock_llm, verbose=verbose)

    # Detect query type if set to auto
    is_loan_query = (
        query_type == "loan_status"
        or "CL-" in query.upper()
        or "application" in query.lower()
        or "status" in query.lower()
    )

    tasks: list[Task] = []
    active_agents = [retrieval_agent, lookup_agent, composer_agent]

    if is_loan_query:
        # Task 1: Lookup Agent searches application record and computes escalation
        lookup_task = Task(
            description=(
                f"Look up the loan application record and calculate the escalation score for the user inquiry: '{query}'. "
                "Use the check_loan_application_status tool."
            ),
            expected_output=(
                "A verified summary of application status, loan amount in INR, days since creation, "
                "fraud review flag, and calculated escalation score."
            ),
            agent=lookup_agent,
        )
        tasks.append(lookup_task)

        # Task 2: Response Composer drafts the final response
        composer_task = Task(
            description=(
                f"Synthesize the loan application status details for customer query: '{query}'. "
                "Provide a clear, reassuring, and professional response regarding their application status."
            ),
            expected_output=(
                "A polished customer-facing response draft summarizing the application status and next steps."
            ),
            agent=composer_agent,
        )
        tasks.append(composer_task)

    else:
        # Task 1: Retrieval Agent searches banking policies
        retrieval_task = Task(
            description=(
                f"Retrieve relevant banking policy details, terms, rates, or rules from the Cred knowledge base "
                f"for the query: '{query}'. Use the rag_policy_retrieval_tool."
            ),
            expected_output=(
                "Factual policy excerpts, eligibility criteria, or calculation formulas directly answering the inquiry."
            ),
            agent=retrieval_agent,
        )
        tasks.append(retrieval_task)

        # Task 2: Response Composer drafts the final grounded response
        composer_task = Task(
            description=(
                f"Synthesize the retrieved policy information into a helpful, compliant response for: '{query}'. "
                "Ensure all statements are strictly grounded in the retrieved policy text."
            ),
            expected_output=(
                "A clear, grounded, and polite draft answer explaining the policy rules to the member."
            ),
            agent=composer_agent,
        )
        tasks.append(composer_task)

    crew = Crew(
        agents=active_agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
    )
    return crew


def build_full_crew(query: str, verbose: bool = True) -> Crew:
    """Build a comprehensive crew including all 3 agents in sequence.

    Args:
        query: Combined customer request.

    Returns:
        3-agent sequential Crew.
    """
    retrieval_agent = create_retrieval_agent(llm=mock_llm, verbose=verbose)
    lookup_agent = create_lookup_agent(llm=mock_llm, verbose=verbose)
    composer_agent = create_composer_agent(llm=mock_llm, verbose=verbose)

    task_retrieval = Task(
        description=f"Retrieve banking policy context from the knowledge base for: '{query}'.",
        expected_output="Relevant policy guidelines and terms.",
        agent=retrieval_agent,
    )

    task_lookup = Task(
        description=f"Check application details and escalation scores if application ID is present in: '{query}'.",
        expected_output="Loan application record details and escalation score.",
        agent=lookup_agent,
    )

    task_compose = Task(
        description=(
            f"Synthesize all retrieved policy facts and loan application details into a comprehensive "
            f"response draft for the inquiry: '{query}'."
        ),
        expected_output="Final customer-facing draft response.",
        agent=composer_agent,
    )

    return Crew(
        agents=[retrieval_agent, lookup_agent, composer_agent],
        tasks=[task_retrieval, task_lookup, task_compose],
        process=Process.sequential,
        verbose=verbose,
    )


def execute_crew(query: str, verbose: bool = True) -> Any:
    """Convenience execution helper running crew.kickoff()."""
    crew = build_banking_crew(query=query, verbose=verbose)
    return crew.kickoff()

