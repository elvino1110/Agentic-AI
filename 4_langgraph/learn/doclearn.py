from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import os
from IPython.display import Image, display


load_dotenv(override=True)

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm_azure = AzureChatOpenAI(
    api_key=os.environ['OPENAI_API_AZURE_KEY'],
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
    api_version=os.environ['OPENAI_API_VERSION'],
    model = os.environ['OPENAI_AZURE_MODEL'],
)

def chatbot(state: State):
    return {"messages": [llm_azure.invoke(state['messages'])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break