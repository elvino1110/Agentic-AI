# Conceptual Code: Hierarchical Research Task
from google.adk.agents import LlmAgent, Agent, Agent
from google.adk.tools import agent_tool
from google.adk.tools.agent_tool import AgentTool
from dotenv import load_dotenv

load_dotenv(override=True)

# Low-level tool-like agents
# web_searcher = LlmAgent(
#     name="WebSearch",
#     description="Performs web searches for facts.",
#     instruction="You are an AI Web Search. Your task is finding the information in Web Search",
#     model="gemini-2.5-pro"
# )
# summarizer = LlmAgent(
#     name="Summarizer",
#     description="Summarizes text.",
#     instruction="You are an AI Summarize information. Your summarization will be consume as a report",
#     model="gemini-2.5-pro"    
# )

# # Mid-level agent combining tools
# research_assistant = LlmAgent(
#     name="ResearchAssistant",
#     model="gemini-2.0-flash",
#     description="Finds and summarizes information on a topic.",
#     tools=[agent_tool.AgentTool(agent=web_searcher), agent_tool.AgentTool(agent=summarizer)]
# )

# # High-level agent delegating research
# report_writer = LlmAgent(
#     name="ReportWriter",
#     model="gemini-2.0-flash",
#     instruction="Write a report on topic X. Use the ResearchAssistant to gather information.",
#     tools=[agent_tool.AgentTool(agent=research_assistant)]
#     # Alternatively, could use LLM Transfer if research_assistant is a sub_agent
# )

# root_agent = report_writer
# User interacts with ReportWriter.
# ReportWriter calls ResearchAssistant tool.
# ResearchAssistant calls WebSearch and Summarizer tools.
# Results flow back up.

# Low Level Agent as Tools