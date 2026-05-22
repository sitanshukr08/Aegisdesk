from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config.settings import settings
import json
from src.aegisdesk.observability.logger import get_logger
from src.aegisdesk.core.llm_factory import get_llm
from src.aegisdesk.core.tools import IT_SUPPORT_TOOLS
from src.aegisdesk.core.integration_tools import CLOUD_INTEGRATION_TOOLS
from src.aegisdesk.core.web_tools import WEB_SCRAPING_TOOLS

logger = get_logger("aegisdesk.pipeline")

def analyze_intent(query: str, history: list) -> dict:
    """Classifies the query using short-term memory to prevent blocking follow-ups."""
    try:
        recent = history[-4:] if history else []
        history_text = "\n".join([f"{m.type}: {m.content}" for m in recent]) if recent else "No history."
        logger.debug(f"Router history context length: {len(recent)} messages")

        llm = get_llm(temperature=0.0, response_format={"type": "json_object"})
        sys_msg = f"""You are a classification router. 
        Recent Context: {history_text}
        
        Classify the user's latest input.
        Categories:
        - "greeting": "hi", "hello", "thanks"
        - "direct_answer": Questions that can be fully answered using the Recent Context. ALSO, if asked "who made aegisdesk" or "who developed you", ALWAYS output "AegisDesk was developed by Sitanshu Kumar".
        - "out_of_scope": Completely unrelated general knowledge.
        - "escalate": User is angry or asking for a human.
        - "it_support": IT issues, troubleshooting, HR portals.
        
        If category is "it_support", you MUST also classify the `domain` as one of:
        - "network_diagnostics": ping, ipconfig, local windows commands
        - "cloud_integrations": okta, jira, slack, resetting passwords, tickets
        - "web_scraping": scraping HR portals, reading external documentation
        - "general": general IT questions
        
        If category is "greeting", "direct_answer", or "out_of_scope", you MUST provide a friendly response in `direct_response`.
        
        You MUST output a valid JSON object. Format MUST be exactly: {{"category": "category_name", "domain": "domain_name or null", "direct_response": "response string or null"}}"""
        
        res = llm.invoke([("system", sys_msg), ("human", query)])
        logger.debug(f"Router Decision: {res.content}")
        return json.loads(res.content)
    except Exception as e:
        logger.error(f"Intent Routing Failed: {e}", exc_info=True)
        return {"category": "it_support", "direct_response": None}
    
def expand_query(query: str, history: list) -> str:
    """Uses chat history to create a context-aware standalone English search query."""
    try:
        recent = history[-4:] if history else []
        history_text = "\n".join([f"{m.type}: {m.content}" for m in recent]) if recent else "No history."
        
        llm = get_llm(temperature=0.0)
        sys_msg = f"""You are an IT query optimizer. 
        Recent chat history:
        {history_text}
        
        Based on the history, translate and expand the user's latest Hinglish/informal query into a standalone, concise English IT search query. 
        Output ONLY the expanded English query."""
        
        res = llm.invoke([("system", sys_msg), ("human", query)])
        return res.content.strip()
    except Exception:
        return query

def get_network_answer(query: str, context: str, history: list):
    """Network Diagnostic Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0).bind_tools(IT_SUPPORT_TOOLS)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk Network Diagnostics Agent. You have tools to run Windows OS commands. Keep your answers brief."),
            MessagesPlaceholder(variable_name="history")
        ])
        return (prompt | llm).invoke({"history": history})
    except Exception as e:
        return _handle_agent_error(e)

def get_cloud_answer(query: str, context: str, history: list):
    """Cloud Integrations Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0).bind_tools(CLOUD_INTEGRATION_TOOLS)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk Cloud Operations Agent. You manage Jira, Slack, and Okta via APIs. Keep your answers brief."),
            MessagesPlaceholder(variable_name="history")
        ])
        return (prompt | llm).invoke({"history": history})
    except Exception as e:
        return _handle_agent_error(e)

def get_web_answer(query: str, context: str, history: list):
    """Web Scraping Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0).bind_tools(WEB_SCRAPING_TOOLS)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk Web Research Agent. Use your web scraper to read internal wikis or external links to solve the user's problem."),
            MessagesPlaceholder(variable_name="history")
        ])
        return (prompt | llm).invoke({"history": history})
    except Exception as e:
        return _handle_agent_error(e)

def get_general_answer(query: str, context: str, history: list):
    """General Knowledge Sub-Agent (No Tools)"""
    try:
        llm = get_llm(temperature=0.0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk IT Assistant. Answer using this context: {context}"),
            MessagesPlaceholder(variable_name="history")
        ])
        return (prompt | llm).invoke({"context": context, "history": history})
    except Exception as e:
        return _handle_agent_error(e)

def _handle_agent_error(e: Exception):
    logger.error(f"Agent generation failed: {e}", exc_info=True)
    from langchain_core.messages import AIMessage
    return AIMessage(content=f"System Error: {str(e)}")