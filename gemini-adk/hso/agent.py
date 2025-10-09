from google.adk.agents import LlmAgent, SequentialAgent
from .embed_data import QdrantEmbedGemini
from dotenv import load_dotenv
load_dotenv(override=True)
# Children Agent

# 1. Planning Agent

# Tools RAG
def get_planning_rag(question: str) -> str:
    """Retrieve data from vector database based on the user question

        Args:
        question (str): The question from user

        Returns
        str: The result of similiartiy search from the vector database about the planning
    """
    planning_qdrant = QdrantEmbedGemini("planning_data")
    result = planning_qdrant.search(question)
    text = ""
    for res in result:
        text += res.page_content
    return text

planning_agent = LlmAgent(
    name="planning_agent",
    instruction=(
        "You are a planning agent that help user change their question into the plant that must to do"
    ),
    description="Search the planning from the vector database and change the user question into the planning",
    tools=[get_planning_rag],
    model="gemini-2.5-pro",
    output_key="planning"
)
# 2. Analayst Agent

analyst_agent = LlmAgent(
    name="analyst_agent",
    instruction=(
        "You are analyst agent that help user to analyze data and give the summary back to the user through the supervisor agent"
        "You must get the planning from the Planner Agent and execute what should you do and you never run before the planner agent done"
        "This is the planning that already build by planner agent {planning}"
    ),
    description="Analyst Agent is used to give summary from the data and execute the plan from the planning agent",
    model="gemini-2.5-pro"
)
engineering_agent = LlmAgent(
    name="engineering_agent",
    instruction=(
        "You are an engineering agent that help user to generate the sql query from the analyst plan result"
    ),
    description="Engineering agent is used to generate sql query based on the analyst plan",
    model="gemini-2.5-pro",
)
# Supervisor Agent

supervisor_agent = SequentialAgent(
    name="supervisor_agent",
    description="You are supervisor agent that direct user question into the planning agent and analyst agent to solve the user question",
    sub_agents=[planning_agent, analyst_agent, engineering_agent]
)

root_agent = supervisor_agent