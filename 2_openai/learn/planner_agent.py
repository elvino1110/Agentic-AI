from pydantic import BaseModel
from agents import Agent

HOW_MANY_INSTRUCTIONS = 5

INSTRUCTIONS = f"You are a helpful assistant. Given query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_INSTRUCTIONS} terms to query for."

class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important to the query."

    query: str
    "The search term to use in a web search."

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]
    """A list of web searches to perform to best answer the query."""
    

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan
)