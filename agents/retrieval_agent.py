"""Retrieval Agent definition for the Cred Banking Crew.

Task 7 requirement:
- Retrieval Agent equipped with the RAG retrieval tool.
- Retrieves authoritative policy information from the knowledge base.
"""

from crewai import Agent

from agents.mock_llm import mock_llm
from tools.rag_tool import rag_tool


def create_retrieval_agent(llm=None, verbose: bool = True) -> Agent:
    """Create and return the Retrieval Agent."""
    return Agent(
        role="Retrieval Agent",
        goal="Retrieve authoritative banking policy information, interest rates, KYC rules, and fee structures from the Cred knowledge base.",
        backstory=(
            "You are a dedicated banking policy specialist at Cred. Your role is to carefully "
            "search the institutional knowledge base and provide factual, grounded policy excerpts "
            "to answer member inquiries."
        ),
        tools=[rag_tool],
        llm=llm or mock_llm,
        verbose=verbose,
        allow_delegation=False,
    )


retrieval_agent = create_retrieval_agent()

