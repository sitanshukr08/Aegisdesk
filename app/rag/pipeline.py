
import asyncio

import numpy as np
from fastembed import TextEmbedding
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.aegisdesk.core.integration_tools import CLOUD_INTEGRATION_TOOLS
from src.aegisdesk.core.llm_factory import get_llm
from src.aegisdesk.core.tools import IT_SUPPORT_TOOLS
from src.aegisdesk.core.web_tools import WEB_SCRAPING_TOOLS
from src.aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.pipeline")

# Offline Intent Vocabulary (Zero-Token Routing)
INTENT_CLASSES = [
    {
        "category": "greeting", 
        "domain": None, 
        "keywords": "hi hello thanks hey greetings good morning afternoon good evening what's up how are you bye cya"
    },
    {
        "category": "it_support", 
        "domain": "network_diagnostics", 
        "keywords": "ping ipconfig network internet slow wifi connection vpn disconnected ethernet latency routing broken pipe gateway dns traceroute nmap packet loss subnet mask ip address port closed tcp udp proxy firewall system process task running kill close cpu memory ram speed performance check spotify taskkill"
    },
    {
        "category": "it_support", 
        "domain": "cloud_integrations", 
        "keywords": "okta jira slack reset password unlock account ticket aws azure active directory sso login token expired ec2 s3 kubernetes pod docker rancher intellij eclipse bitlocker ad profile update rdp ssh keys cloud database sql mfa authenticator cyberark"
    },
    {
        "category": "it_support", 
        "domain": "web_scraping", 
        "keywords": "scrape read wiki documentation hr portal benefits policy external website url page search internet wikipedia latest news status cve lookup extract text web article manual guide"
    },
]

_ROUTER_MODEL: TextEmbedding | None = None
_INTENT_VECTORS: np.ndarray | None = None
_ROUTER_META: list[dict] | None = None

def get_router():
    # Deprecated sync wrapper, use async_get_router
    pass

_ROUTER_LOCKS = {}

def _load_intents_db():
    corpus = []
    meta = []
    for item in INTENT_CLASSES:
        corpus.append(item["keywords"])
        meta.append({"category": item["category"], "domain": item["domain"]})
    return corpus, meta

async def async_get_router() -> tuple[TextEmbedding, np.ndarray, list[dict]]:
    global _ROUTER_MODEL, _INTENT_VECTORS, _ROUTER_META, _ROUTER_LOCKS
    loop = asyncio.get_running_loop()
    if loop not in _ROUTER_LOCKS:
        _ROUTER_LOCKS[loop] = asyncio.Lock()
        
    if _ROUTER_META is None:
        async with _ROUTER_LOCKS[loop]:
            if _ROUTER_META is None:
                logger.info("Loading FastEmbed model for semantic routing...")
                model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                
                # Base static corpus
                corpus, meta = _load_intents_db()
                    
                # Dynamic few-shot examples from DB
                try:
                    from app.memory.graph_store import graph_db
                    examples = await graph_db.get_routing_examples()
                    for ex in examples:
                        corpus.append(ex["query"])
                        meta.append({"category": ex["category"], "domain": ex["domain"]})
                except Exception as e:
                    logger.error(f"Failed to load dynamic routing examples: {e}")
                    
                _ROUTER_MODEL = model
                _INTENT_VECTORS = np.array(list(_ROUTER_MODEL.embed(corpus)))
                _ROUTER_META = meta
    return _ROUTER_MODEL, _INTENT_VECTORS, _ROUTER_META

async def analyze_intent(query: str, history: list) -> dict:
    """Classifies the query offline using SentenceTransformer (Zero-Token)."""
    try:
        # Hardcoded direct answers
        q_lower = query.lower()
        if "who" in q_lower and ("aegisdesk" in q_lower or "made" in q_lower or "developed" in q_lower or "created" in q_lower or "author" in q_lower):
            return {"category": "it_support", "domain": "web_scraping", "direct_response": None}
            
        # Semantic Routing using Singleton Model
        model, intent_vectors, router_meta = await async_get_router()
        query_vec = np.array(list(model.embed([q_lower])))
        
        # Calculate cosine similarity manually since vectors are normalized by default
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_vec, intent_vectors).flatten()
        best_match_idx = int(np.argmax(similarities))
        
        # Fallback if query doesn't match any known vectors strongly
        if similarities[best_match_idx] < 0.45:
            return {"category": "it_support", "domain": "general", "direct_response": None}
            
        match = router_meta[best_match_idx]
        
        direct_resp = None
        if match["category"] == "greeting":
            try:
                from src.aegisdesk.core.llm_factory import get_llm
                llm = get_llm(temperature=0.7)
                res = llm.invoke([
                    ("system", "You are AegisDesk, an elite autonomous IT assistant. The user is chatting or asking what you do. Respond naturally and briefly explain your capabilities (resolving IT tickets, network diagnostics, etc). Keep it to 1-2 short sentences. Do not be overly robotic."),
                    ("human", query)
                ])
                direct_resp = res.content
            except Exception:
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

async def get_network_answer(query: str, context: str, history: list):
    """Network Diagnostic Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0).bind_tools(IT_SUPPORT_TOOLS)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk Network Diagnostics Agent. You have tools to run Windows OS commands. Keep your answers brief. Use the native tool_calls API directly. Do not describe what you are about to do. If the history contains a ToolMessage with the command output, you MUST provide the final answer to the user based on that output. DO NOT call the exact same tool again."),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"history": history})
    except Exception as e:
        return _handle_agent_error(e)

async def get_cloud_answer(query: str, context: str, history: list):
    """Cloud Integrations Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0).bind_tools(CLOUD_INTEGRATION_TOOLS)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk Cloud Operations Agent. You manage Jira, Slack, and Okta via APIs. Keep your answers brief. Use the native tool_calls API directly. Do not describe what you are about to do. When invoking a tool, you MUST use the native JSON tool call format. DO NOT use XML <function> tags."),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"history": history})
    except Exception as e:
        return _handle_agent_error(e)

async def get_web_answer(query: str, context: str, history: list):
    """Web Scraping Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0).bind_tools(WEB_SCRAPING_TOOLS)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AegisDesk Web Research Agent. Use your search tools to search the internet or scrape webpages to solve the user's problem. Use the native tool_calls API directly. Do not describe what you are about to do. When invoking a tool, you MUST use the native JSON tool call format. DO NOT use XML <function> tags."),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"history": history})
    except Exception as e:
        return _handle_agent_error(e)

async def get_general_answer(query: str, context: str, history: list):
    """General Knowledge Sub-Agent (No Tools)"""
    try:
        llm = get_llm(temperature=0.0)
        sys_msg = """You are the AegisDesk IT Assistant. 
You must answer the user's query strictly using ONLY the provided context.
If the context does not contain the answer or is irrelevant, explicitly state that you do not have that information in your knowledge base. Do not hallucinate or use outside knowledge.

Context:
{context}"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_msg),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"context": context, "history": history})
    except Exception as e:
        return _handle_agent_error(e)

def _handle_agent_error(e: Exception):
    logger.exception("Agent generation failed")
    from langchain_core.messages import AIMessage
    
    try:
        import groq
        if isinstance(e, groq.RateLimitError):
            return AIMessage(content="Service is currently experiencing high traffic. Please try again in a moment.")
        elif isinstance(e, groq.AuthenticationError):
            return AIMessage(content="An internal authentication error occurred. Please check system credentials.")
    except ImportError:
        pass
        
    return AIMessage(content="An internal service error occurred. The incident has been logged.")

async def _with_retries(runnable, inputs, max_attempts=3):
    import groq
    for attempt in range(max_attempts):
        try:
            return await runnable.ainvoke(inputs)
        except groq.RateLimitError as e:
            if attempt == max_attempts - 1:
                raise e
            logger.warning(f"RateLimitError encountered. Retrying in {2 ** attempt}s...")
            await asyncio.sleep(2 ** attempt)