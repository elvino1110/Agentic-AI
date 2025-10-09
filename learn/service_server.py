from mcp.server.fastmcp import FastMCP
from data_embed import search_data

mcp = FastMCP("service_server")

@mcp.tool()
async def motor_problem(problem_description: str) -> str:
    """Given a description of a motor problem, return a diagnosis and recommended repair steps.

    Args:
        problem_description: A description of the motor problem. For example, "The motor is making a grinding noise when starting."
    """
    context = search_data(problem_description)    
    print("sucessfully searched data")
    return f"Based on the problem description '{problem_description}', the following information may be relevant:\n\n" + "\n\n".join([doc.page_content for doc in context])


if __name__ == "__main__":
    mcp.run(transport='stdio')