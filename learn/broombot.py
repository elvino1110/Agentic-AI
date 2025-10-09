from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langgraph.types import Literal
from pydantic import BaseModel, Field
from IPython.display import Image, display
import gradio as gr
import uuid
from dotenv import load_dotenv
import os
load_dotenv(override=True)
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    route: Optional[Literal["sales_agent", "repair_agent", "END"]]  # Make it optional
    conversation_complete: bool  # Add flag to track completion

llm = AzureChatOpenAI(
    api_key=os.environ['OPENAI_API_AZURE_KEY'],
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
    api_version=os.environ['OPENAI_API_VERSION'],
    model=os.environ['OPENAI_AZURE_MODEL'],
)

class CustomerServiceResult(BaseModel):
    route: Literal["sales_agent", "repair_agent", "END"] = Field(
        ..., description="The route to take based on the user's request. Options are 'sales_agent', 'repair_agent', or 'END'."
    )
    answer: str = Field(
        ..., description="The response to the user when user not ask about repair or buy motorcycle."
    )

customer_service_llm = llm.with_structured_output(CustomerServiceResult)

def customer_service(state: State) -> Dict[str, Any]:
    """Customer service node - routes requests or provides general answers"""
    print("=== CUSTOMER SERVICE NODE ===")
    print("Current state:", state)
    
    # Check if we're coming back from a specialist agent
    if len(state['messages']) > 1 and hasattr(state['messages'][-1], 'content'):
        last_message = state['messages'][-1]
        # If last message is from AI (specialist), we should end the conversation
        if isinstance(last_message, AIMessage):
            print("Detected specialist response, ending conversation")
            return {
                "messages": state['messages'],
                "route": "END",
                "conversation_complete": True
            }
    
    system_message = """You are a customer service agent for Broom Bot Inc, a motorcycle company that can sell motorcycle or repair motorcycle.
    
    You will guide the customer to either buy a motorcycle or repair a motorcycle.
    
    ROUTING RULES:
    - If user wants to buy a motorcycle, ask about new models, or any question related to motorcycle purchasing/models → route to "sales_agent"
    - If user wants to repair a motorcycle, ask about motor problems, maintenance, or any repair-related issues → route to "repair_agent"  
    - If user asks general questions not related to buying or repairing motorcycles → answer directly and route to "END"
    
    IMPORTANT: Only route to specialists for the INITIAL request. Do not route follow-up questions.
    """
    
    # Get only the user messages for routing decision
    user_messages = [msg for msg in state['messages'] if isinstance(msg, HumanMessage)]
    
    customer_service_messages = [
        SystemMessage(content=system_message),
        *user_messages  # Only include user messages for routing
    ]
    
    print("Messages sent to customer service LLM:", customer_service_messages)
    
    try:
        customer_service_result = customer_service_llm.invoke(customer_service_messages)
        print("Customer service result:", customer_service_result)
        
        # If routing to END, include the answer in messages
        if customer_service_result.route == "END":
            new_messages = state['messages'] + [AIMessage(content=customer_service_result.answer)]
            conversation_complete = True
        else:
            # If routing to specialist, don't add message yet
            new_messages = state['messages']
            conversation_complete = False
        
        new_state = {
            "messages": new_messages,
            "route": customer_service_result.route,
            "conversation_complete": conversation_complete
        }
        
        print("New state from customer service:", new_state)
        return new_state
        
    except Exception as e:
        print(f"Error in customer service: {e}")
        return {
            "messages": state['messages'] + [AIMessage(content="I apologize, but I'm having trouble processing your request. Please try again.")],
            "route": "END",
            "conversation_complete": True
        }

def route_based_on_evaluation(state: State) -> str:
    """Routing function for conditional edges"""
    print("=== ROUTING DECISION ===")
    print(f"Route: {state.get('route', 'None')}")
    print(f"Conversation complete: {state.get('conversation_complete', False)}")
    
    route = state.get('route', 'END')
    print(f"Routing to: {route}")
    return route

def repair_agent(state: State) -> Dict[str, Any]:
    """Repair agent - handles motorcycle repair requests"""
    print("=== REPAIR AGENT NODE ===")
    print("Current messages:", state["messages"])
    
    # Get the user's original request
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    if not user_messages:
        return {
            "messages": state["messages"] + [AIMessage(content="I didn't receive your repair request. Please describe your motorcycle problem.")],
            "route": "END",
            "conversation_complete": True
        }
    
    latest_user_message = user_messages[-1].content
    print("Latest user message:", latest_user_message)

    system_message = """You are a repair agent for Broom Bot Inc, a motorcycle company that specializes in motorcycle repairs and maintenance.

    Your expertise includes:
    - Diagnosing motorcycle problems
    - Providing repair solutions and maintenance advice
    - Scheduling service appointments
    - Explaining repair procedures and costs
    - Troubleshooting mechanical and electrical issues

    Provide helpful, detailed responses about motorcycle repair and maintenance. Be professional and knowledgeable.
    
    After providing your response, the conversation will be complete unless the user has follow-up questions."""

    repair_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=latest_user_message)
    ]

    try:
        result = llm.invoke(repair_messages)
        print("Repair agent result:", result)
        
        return {
            "messages": state["messages"] + [result],
            "route": "END",
            "conversation_complete": True
        }
    except Exception as e:
        print(f"Error in repair agent: {e}")
        return {
            "messages": state["messages"] + [AIMessage(content="I apologize, but I'm having trouble processing your repair request. Please contact our service department directly.")],
            "route": "END",
            "conversation_complete": True
        }

def sales_agent(state: State) -> Dict[str, Any]:
    """Sales agent - handles motorcycle sales requests"""
    print("=== SALES AGENT NODE ===")
    print("Current messages:", state["messages"])
    
    # Get the user's original request
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    if not user_messages:
        return {
            "messages": state["messages"] + [AIMessage(content="I didn't receive your sales inquiry. Please let me know what motorcycle you're interested in.")],
            "route": "END", 
            "conversation_complete": True
        }
    
    latest_user_message = user_messages[-1].content
    print("Latest user message:", latest_user_message)

    system_message = """You are a sales agent for Broom Bot Inc, a motorcycle company that specializes in selling motorcycles.

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
    
    After providing your response, the conversation will be complete unless the user has follow-up questions."""

    sales_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=latest_user_message)
    ]

    try:
        result = llm.invoke(sales_messages)
        print("Sales agent result:", result)
        
        return {
            "messages": state["messages"] + [result],
            "route": "END",
            "conversation_complete": True
        }
    except Exception as e:
        print(f"Error in sales agent: {e}")
        return {
            "messages": state["messages"] + [AIMessage(content="I apologize, but I'm having trouble processing your sales inquiry. Please contact our sales department directly.")],
            "route": "END",
            "conversation_complete": True
        }

# Build the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("customer_service", customer_service)
graph_builder.add_node("repair_agent", repair_agent)
graph_builder.add_node("sales_agent", sales_agent)

# Add edges - FIXED STRUCTURE
graph_builder.add_edge(START, "customer_service")

# Conditional edges from customer service
graph_builder.add_conditional_edges(
    "customer_service", 
    route_based_on_evaluation, 
    {
        "sales_agent": "sales_agent", 
        "repair_agent": "repair_agent", 
        "END": END
    }
)

# Both specialist agents go directly to END (no loop back)
graph_builder.add_edge("repair_agent", END)
graph_builder.add_edge("sales_agent", END)

# Compile the graph
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Test function
def test_graph():
    """Test the multi-agent system"""
    print("🏍️ Testing Multi-Agent Motorcycle System")
    print("=" * 50)
    
    test_cases = [
        "I want to buy a new motorcycle",
        "My motorcycle won't start",  
        "What's the weather like today?",
        "Tell me about sport bikes",
        "My brakes are making noise"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_input}")
        
        # Create unique thread for each test
        thread_id = f"test-{i}-{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Run the graph
            result = graph.invoke(
                {"messages": [HumanMessage(content=test_input)], "route": None, "conversation_complete": False},
                config=config
            )
            
            # Get the final response
            if result["messages"]:
                final_message = result["messages"][-1]
                if hasattr(final_message, 'content'):
                    print(f"Response: {final_message.content}")
                else:
                    print(f"Response: {final_message}")
            else:
                print("No response received")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 30)

# Interactive function for Gradio or direct use
def chat_with_system(message: str, thread_id: str = None) -> str:
    """Chat with the multi-agent system"""
    if thread_id is None:
        thread_id = f"chat-{uuid.uuid4()}"
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=message)], "route": None, "conversation_complete": False},
            config=config
        )
        
        if result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                return final_message.content
            else:
                return str(final_message)
        else:
            return "I apologize, but I couldn't process your request."
            
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    # Run tests
    test_graph()
    
    # Interactive mode
    print("\n🔄 Interactive Mode (type 'quit' to exit):")
    thread_id = f"interactive-{uuid.uuid4()}"
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Thank you for using Broom Bot Inc!")
            break
        
        if user_input:
            response = chat_with_system(user_input, thread_id)
            print(f"🤖 Broom Bot: {response}")