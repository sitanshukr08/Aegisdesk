from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config.settings import settings
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.aegisdesk.observability.logger import get_logger
from src.aegisdesk.core.llm_factory import get_llm
from src.aegisdesk.core.tools import IT_SUPPORT_TOOLS
from src.aegisdesk.core.integration_tools import CLOUD_INTEGRATION_TOOLS
from src.aegisdesk.core.web_tools import WEB_SCRAPING_TOOLS

logger = get_logger("aegisdesk.pipeline")

# Offline Intent Vocabulary (Zero-Token Routing)
INTENT_CLASSES = [
    {"category": "greeting", "domain": None, "keywords": "hi hello thanks hey greetings good morning afternoon"},
    {"category": "it_support", "domain": "network_diagnostics", "keywords": "ping ipconfig network internet slow wifi connection vpn disconnected ethernet latency routing"},
    {"category": "it_support", "domain": "cloud_integrations", "keywords": "okta jira slack reset password unlock account ticket aws azure active directory sso login"},
    {"category": "it_support", "domain": "web_scraping", "keywords": "scrape read wiki documentation hr portal benefits policy external website url page"},
]

vectorizer = TfidfVectorizer()
corpus = [item["keywords"] for item in INTENT_CLASSES]
tfidf_matrix = vectorizer.fit_transform(corpus)

def analyze_intent(query: str, history: list) -> dict:
    """Classifies the query offline using TF-IDF and Cosine Similarity (Zero-Token)."""
    try:
        # Hardcoded direct answers
        q_lower = query.lower()
        if "who" in q_lower and ("aegisdesk" in q_lower or "made" in q_lower or "developed" in q_lower):
            return {"category": "direct_answer", "domain": None, "direct_response": "AegisDesk was developed by Sitanshu Kumar."}
            
        # Offline Semantic Routing
        query_vec = vectorizer.transform([q_lower])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        best_match_idx = int(np.argmax(similarities))
        
        # Fallback if query doesn't match any known vectors strongly
        if similarities[best_match_idx] < 0.15:
            return {"category": "it_support", "domain": "general", "direct_response": None}
            
        match = INTENT_CLASSES[best_match_idx]
        
        direct_resp = None
        if match["category"] == "greeting":
            direct_resp = "Hello! I am AegisDesk, your autonomous IT assistant. How can I help you today?"
            
        return {"category": match["category"], "domain": match["domain"], "direct_response": direct_resp}
        
    except Exception as e:
        logger.error(f"Offline Intent Routing Failed: {e}", exc_info=True)
        return {"category": "it_support", "domain": "general", "direct_response": None}
    
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