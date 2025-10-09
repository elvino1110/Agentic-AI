from google.adk.agents import LlmAgent
from dotenv import load_dotenv
load_dotenv(override=True)
# Children Agent

# 1. Planning Agent
planning_agent = LlmAgent(
    name="planning_agent",
    instruction=(
        "You are a planning agent that help user change their question into the plant that must to do"
        "You can use the search_plan_tool to get the information about the similarity planning and make it based on the question of user"
    ),
    description="Search the planning from the vector database and change the user question into the planning",
    model="gemini-2.5-pro"
)
# 2. Analayst Agent

analyst_agent = LlmAgent(
    name="analyst_agent",
    instruction=(
        "You are analyst agent that help user to analyze data and give the summary back to the user through the supervisor agent"
        "You must get the planning from the Planner Agent and execute what should you do and you never run before the planner agent done"
        "Use the engineer agent tool to get the data and analyze it"
    ),
    description="Analyst Agent is used to give summary from the data and execute the plan from the planning agent",
    model="gemini-2.5-pro"
)

# Supervisor Agent

root_agent = LlmAgent(
    name="supervisor_agent",
    instruction=(
        "You are supervisor agent that direct user question into several agents"
        "First step you must create the planning from user question with the Planning Agent"
        "After the planning is avaliable, directly go to the Analyst Agent to execute what must the agent do from the planning and analyze the data"
    ),
    description="You are supervisor agent that direct user question into the planning agent and analyst agent to solve the user question",
    model="gemini-2.5-pro",
    sub_agents=[planning_agent, analyst_agent]
)


