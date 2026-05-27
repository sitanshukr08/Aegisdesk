
import asyncio

import asyncio

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from aegisdesk.core.integration_tools import CLOUD_INTEGRATION_TOOLS
from aegisdesk.core.llm_factory import get_llm
from aegisdesk.core.tools import IT_SUPPORT_TOOLS
from aegisdesk.core.web_tools import WEB_SCRAPING_TOOLS
from aegisdesk.observability.logger import get_logger

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

from synaptoroute.router import AdaptiveRouter
from synaptoroute.encoder import Encoder
from synaptoroute.storage import SQLiteStorage
from synaptoroute.models import Route

_ROUTER: AdaptiveRouter | None = None
_ROUTER_LOCK = asyncio.Lock()

async def async_get_router() -> AdaptiveRouter:
    global _ROUTER
    
    if _ROUTER is None:
        async with _ROUTER_LOCK:
            if _ROUTER is None:
                logger.info("Initializing SynaptoRoute for semantic routing...")
                
                # Setup Encoder and Storage
                encoder = Encoder(model_name="BAAI/bge-small-en-v1.5")
                import os
                os.makedirs("data", exist_ok=True)
                storage = SQLiteStorage("data/synaptoroute.sqlite")
                
                router = AdaptiveRouter(encoder, storage)
                
                # Load static intents into router
                for idx, item in enumerate(INTENT_CLASSES):
                    route = Route(
                        name=f"static_route_{idx}",
                        utterances=[item["keywords"]],
                        threshold=0.45,
                        metadata={"category": item["category"], "domain": item["domain"]}
                    )
                    router.add_route(route)
                    
                # Load dynamic few-shot examples from DB
                try:
                    from aegisdesk.app.memory.graph_store import graph_db
                    examples = await graph_db.get_routing_examples()
                    
                    # Group examples by category/domain to create consolidated routes
                    dynamic_routes = {}
                    for ex in examples:
                        cat = ex["category"]
                        dom = ex["domain"]
                        key = f"dynamic_{cat}_{dom}"
                        if key not in dynamic_routes:
                            dynamic_routes[key] = {"utterances": [], "meta": {"category": cat, "domain": dom}}
                        dynamic_routes[key]["utterances"].append(ex["query"])
                        
                    for key, data in dynamic_routes.items():
                        route = Route(
                            name=key,
                            utterances=data["utterances"],
                            threshold=0.45,
                            metadata=data["meta"]
                        )
                        router.add_route(route)
                except Exception as e:
                    logger.error(f"Failed to load dynamic routing examples: {e}")
                
                await router.start()
                _ROUTER = router
                
    return _ROUTER

async def shutdown_router():
    global _ROUTER
    if _ROUTER is not None:
        await _ROUTER.stop()

async def analyze_intent(query: str, history: list) -> dict:
    """Classifies the query offline using SynaptoRoute."""
    try:
        # Hardcoded direct answers
        q_lower = query.lower()
        if "who" in q_lower and ("aegisdesk" in q_lower or "made" in q_lower or "developed" in q_lower or "created" in q_lower or "author" in q_lower):
            return {"category": "it_support", "domain": "web_scraping", "direct_response": None}
            
        # Semantic Routing using SynaptoRoute
        router = await async_get_router()
        match = await router.aquery(q_lower)
        
        # Fallback if query doesn't match any known vectors strongly
        if not match:
            return {"category": "it_support", "domain": "general", "direct_response": None}
            
        direct_resp = None
        if match.metadata and match.metadata.get("category") == "greeting":
            try:
                from aegisdesk.core.llm_factory import get_llm
                llm = get_llm(temperature=0.7, tier="synthesis")
                res = await llm.ainvoke([
                    ("system", "You are AegisDesk, an elite autonomous IT assistant. The user is chatting or asking what you do. Respond naturally and briefly explain your capabilities (resolving IT tickets, network diagnostics, etc). Keep it to 1-2 short sentences. Do not be overly robotic."),
                    ("human", query)
                ])
                direct_resp = res.content
            except Exception:
                direct_resp = "Hello! I am AegisDesk, your autonomous IT assistant. How can I help you today?"
        
        return {
            "category": match.metadata.get("category", "it_support"), 
            "domain": match.metadata.get("domain", "general"), 
            "direct_response": direct_resp
        }
        
    except Exception as e:
        logger.error(f"Offline Intent Routing Failed: {e}", exc_info=True)
        return {"category": "it_support", "domain": "general", "direct_response": None}
    
async def expand_query(query: str, history: list) -> str:
    """Uses chat history to create a context-aware standalone English search query."""
    try:
        recent = history[-4:] if history else []
        history_text = "\n".join([f"{m.type}: {m.content}" for m in recent]) if recent else "No history."
        
        llm = get_llm(temperature=0.0, tier="fast")
        sys_msg = f"""You are an IT query optimizer. 
        Recent chat history:
        {history_text}
        
        Based on the history, translate and expand the user's latest Hinglish/informal query into a standalone, concise English IT search query. 
        Output ONLY the expanded English query."""
        
        res = await llm.ainvoke([("system", sys_msg), ("human", query)])
        return res.content.strip()
    except Exception:
        return query

async def get_network_answer(query: str, context: str, history: list):
    """Network Diagnostic Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0, tier="fast").bind_tools(IT_SUPPORT_TOOLS)
        sys_msg = f"""You are the AegisDesk Network Diagnostics Agent. You have tools to run Windows OS commands. Keep your answers brief. Use the native tool_calls API directly. Do not describe what you are about to do. If the history contains a ToolMessage with the command output, you MUST provide the final answer to the user based on that output. DO NOT call the exact same tool again.
        
Knowledge Base Context (use if relevant):
{context}"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_msg),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"history": history})
    except Exception as e:
        return _handle_agent_error(e)

async def get_cloud_answer(query: str, context: str, history: list):
    """Cloud Integrations Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0, tier="fast").bind_tools(CLOUD_INTEGRATION_TOOLS)
        sys_msg = f"""You are the AegisDesk Cloud Operations Agent. You manage Jira, Slack, and Okta via APIs. Keep your answers brief. Use the native tool_calls API directly. Do not describe what you are about to do. When invoking a tool, you MUST use the native JSON tool call format. DO NOT use XML <function> tags.
        
Knowledge Base Context (use if relevant):
{context}"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_msg),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"history": history})
    except Exception as e:
        return _handle_agent_error(e)

async def get_web_answer(query: str, context: str, history: list):
    """Web Scraping Sub-Agent"""
    try:
        llm = get_llm(temperature=0.0, tier="fast").bind_tools(WEB_SCRAPING_TOOLS)
        sys_msg = f"""You are the AegisDesk Web Research Agent. Use your search tools to search the internet or scrape webpages to solve the user's problem. Use the native tool_calls API directly. Do not describe what you are about to do. When invoking a tool, you MUST use the native JSON tool call format. DO NOT use XML <function> tags.
        
Knowledge Base Context (use if relevant):
{context}"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_msg),
            MessagesPlaceholder(variable_name="history")
        ])
        return await _with_retries(prompt | llm, {"history": history})
    except Exception as e:
        return _handle_agent_error(e)

async def get_general_answer(query: str, context: str, history: list):
    """General Knowledge Sub-Agent (No Tools)"""
    try:
        llm = get_llm(temperature=0.0, tier="synthesis")
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

