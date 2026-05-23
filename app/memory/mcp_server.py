from mcp.server.fastmcp import FastMCP

from app.memory.graph_store import graph_db

mcp = FastMCP("AegisDesk Graph Memory")

@mcp.tool()
async def extract_and_store_fact(entity1: str, relation: str, entity2: str) -> str:
    """
    Store a new relationship in the memory graph.
    Example: entity1="aryan", relation="HAS_ISSUE", entity2="bsod_critical_process_died"
    """
    await graph_db.add_fact(entity1, relation, entity2)
    return f"Successfully stored memory: {entity1} {relation} {entity2}"

@mcp.tool()
async def query_user_memory(user_id: str) -> str:
    """
    Retrieve all known historical facts and context about a specific user.
    Use this before answering to understand their past issues, hardware, and access rights.
    """
    facts = await graph_db.query_entity(user_id)
    if not facts:
        return f"No memory found for user: {user_id}"
    
    return "Historical Context:\n" + "\n".join(facts)

if __name__ == "__main__":
    mcp.run(transport='stdio')