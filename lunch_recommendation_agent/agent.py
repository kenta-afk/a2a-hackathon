"""Main agent entrypoint for ADK CLI."""

# Import the local agent as the root agent for ADK CLI
from lunch_recommendation_agent.local_agent import local_agent

# Export the local agent as the root agent for ADK CLI
root_agent = local_agent
