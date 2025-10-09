from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from service_client import get_service_tools
from dotenv import load_dotenv
load_dotenv(override=True)
import os
import asyncio

llm = AzureChatOpenAI(
    api_key=os.environ['OPENAI_API_AZURE_KEY'],
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
    api_version=os.environ['OPENAI_API_VERSION'],
    model = os.environ['OPENAI_AZURE_MODEL'],
)
def product_motor(motor_name: str):
    """Search a motor product"""
    return f"Successfully search a product motor named {motor_name}. The motor is available with price 20.000.000 IDR"

service_tools = asyncio.run(get_service_tools())

system_message_sales_agent = """You are a sales agent for Broom Bot Inc, a motorcycle company that specializes in selling motorcycles.

    Your expertise includes:
    - Recommending motorcycle models based on customer needs
    - Providing pricing information and financing options
    - Explaining motorcycle specifications and features
    - Arranging test rides and demonstrations
    - Processing sales inquiries and orders

    Available motorcycle categories:
    - Sport bikes: High performance, racing-oriented
    - Cruisers: Comfortable, touring-focused  
    - Adventure bikes: Versatile, on/off-road capability
    - Standard bikes: Balanced, everyday riding

    Provide helpful, informative responses about motorcycle sales and models. Be professional and enthusiastic about helping customers find their perfect motorcycle.
    You only help with motorcycle sales, do not help with motorcycle problem.
    Use the tool 'product_motor' to search for motorcycle products based on customer requests.

    After providing your response, the conversation will be complete unless the user has follow-up questions."""


sales_agent = create_react_agent(
    model=llm,
    tools=[product_motor],
    prompt=system_message_sales_agent,
    name="sales_agent"
)
system_message_service_agent = """You are a repair agent for Broom Bot Inc, a motorcycle company that specializes in motorcycle repairs and maintenance.

    Your expertise includes:
    - Diagnosing motorcycle problems
    - Providing repair solutions and maintenance advice
    - Scheduling service appointments
    - Explaining repair procedures and costs
    - Troubleshooting mechanical and electrical issues

    Provide helpful, detailed responses about motorcycle repair and maintenance. Be professional and knowledgeable.
    You only help with motorcycle problem, do not help with motorcycle sales.
    
    After providing your response, the conversation will be complete unless the user has follow-up questions."""

service_agent = create_react_agent(
    model=llm,
    tools=service_tools,
    prompt=system_message_service_agent,
    name="service_agent"
)

supervisor = create_supervisor(
    agents=[sales_agent, service_agent],
    model=llm,
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a sales agent. Assign to help user find their motorcycle that they want to buy\n"
        "- a service agent. Assign to help user find the solotion of their motor problem\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself.\n"
        "Combine the result from the agent that you call to give the final response to the user."
    )
).compile()

    