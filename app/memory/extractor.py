import json

from langchain_groq import ChatGroq

from app.config.settings import settings
from app.memory.graph_store import graph_db
from aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.memory")

async def extract_memory_background(user_id: str, text: str):
    """
    Runs asynchronously in the background. 
    Extracts Knowledge Graph triples from user input and saves them securely.
    """
    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key, 
            model_name=settings.llm_model, 
            temperature=0.0,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        sys_msg = f"""You are a Graph Memory Extractor for an IT Support Bot.
        Extract factual relationships from the user's message.
        Always use '{user_id}' as entity1 if the user is talking about themselves.
        
        Use simple, UPPERCASE relations like: HAS_ISSUE, OWNS_DEVICE, ATTEMPTED_FIX, WORKS_IN.
        
        You MUST output a valid JSON object containing a list of 'facts'. 
        Format exactly like this:
        {{
            "facts": [
                {{"entity1": "{user_id}", "relation": "HAS_ISSUE", "entity2": "blue screen of death"}}
            ]
        }}
        If no concrete facts are present, return {{"facts": []}}.
        """
        
        res = await llm.ainvoke([("system", sys_msg), ("human", text)])
        data = json.loads(res.content)
        
        for fact in data.get("facts", []):
            e1 = fact.get("entity1")
            rel = fact.get("relation")
            e2 = fact.get("entity2")
            if e1 and rel and e2:
                await graph_db.add_fact(e1, rel, e2)
                
    except Exception as e:
        logger.error(f"Failed to extract memory facts: {e}", exc_info=True)
