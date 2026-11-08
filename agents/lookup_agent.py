"""Lookup Agent definition for the Cred Banking Crew.

Task 7 requirement:
- Lookup Agent equipped with the check_loan_application_status tool.
- Retrieves loan application details and calculated escalation scores.
"""

from crewai import Agent

from agents.mock_llm import mock_llm
from tools.loan_lookup_tool import loan_lookup_tool


def create_lookup_agent(llm=None, verbose: bool = True) -> Agent:
    """Create and return the Lookup Agent."""
    return Agent(
        role="Lookup Agent",
        goal="Look up specific loan application records by application ID and compute escalation and fraud scores.",
        backstory=(
            "You are a lending operations officer at Cred. You have direct authorization to inspect "
            "loan application records, determine verification statuses, and compute risk escalation scores "
            "for human supervisors."
        ),
        tools=[loan_lookup_tool],
        llm=llm or mock_llm,
        verbose=verbose,
        allow_delegation=False,
    )


lookup_agent = create_lookup_agent()

