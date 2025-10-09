import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
client = MultiServerMCPClient(
    {
        "service_tool": {
            "command": "uv",
            "args": ["run", "service_server.py"], 
            "transport": "stdio",
        }
    }
)


async def get_service_tools():
    tools = await client.get_tools()
    return tools
