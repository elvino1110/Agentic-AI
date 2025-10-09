from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
import os


abspath = os.path.dirname(os.path.abspath(__file__))
path_server = os.path.join(abspath, "service_server.py")

server_params = StdioServerParameters(
    command="uv",
    # Make sure to update to the full absolute path to your math_server.py file
    args=["run", path_server],
)
async def tools_service():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)
            # print("tools", tools)
            return tools


