"""Response Composer Agent definition for the Cred Banking Crew.

Task 7 requirement:
- Combines agent outputs into one final draft answer.
- No mandatory tool.
"""

from crewai import Agent

from agents.mock_llm import mock_llm


def create_composer_agent(llm=None, verbose: bool = True) -> Agent:
    """Create and return the Response Composer Agent."""
    return Agent(
        role="Response Composer",
        goal="Synthesize policy facts, loan records, and escalation metrics into a clear, grounded, and polite draft answer for the member.",
        backstory=(
            "You are a senior member communications editor at Cred. Your responsibility is to combine "
            "technical policy retrievals and loan operational data into a clear, unified, and compliant "
            "customer response before supervisory review."
        ),
        tools=[],
        llm=llm or mock_llm,
        verbose=verbose,
        allow_delegation=False,
    )


composer_agent = create_composer_agent()

