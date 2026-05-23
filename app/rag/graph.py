import os
import sqlite3
from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

from app.rag.pipeline import analyze_intent, expand_query, get_network_answer, get_cloud_answer, get_web_answer, get_general_answer
from app.rag.retriever import get_context
from app.services.webhook_service import create_support_ticket
from app.config.settings import settings
from src.aegisdesk.observability.logger import get_logger
from src.aegisdesk.core.tools import SAFE_TOOLS, DANGEROUS_TOOLS
from src.aegisdesk.core.integration_tools import CLOUD_INTEGRATION_TOOLS
from src.aegisdesk.core.web_tools import WEB_SCRAPING_TOOLS

logger = get_logger("aegisdesk.graph")

SAFE_ALL_TOOLS = SAFE_TOOLS + CLOUD_INTEGRATION_TOOLS + WEB_SCRAPING_TOOLS

# 1. Define the State (Now with persistent 'messages')
class AgentState(TypedDict):
    session_id: str
    user_id: str
    query: str
    messages: Annotated[list, add_messages] # Magic LangGraph reducer
    
    intent_category: Optional[str]
    intent_domain: Optional[str]
    direct_response: Optional[str]
    
    expanded_query: Optional[str]
    context: Optional[str]
    confidence: float
    
    web_answer: Optional[str]
    ticket_id: Optional[str]
    final_answer: Optional[str]

# 2. Define the Nodes
def route_intent_node(state: AgentState):
    logger.debug("[LANGGRAPH] Node: route_intent")
    intent = analyze_intent(state["query"], state.get("messages", []))
    
    update = {
        "intent_category": intent.get("category"),
        "intent_domain": intent.get("domain", "general"),
        "direct_response": intent.get("direct_response"),
        # CRITICAL FIX: Clear out volatile state keys from previous SQLite checkpoints!
        "ticket_id": "",
        "final_answer": "",
        "web_answer": "",
        "context": "",
        "expanded_query": "",
        "confidence": 0.0
    }
    # If the bot answers directly (like a greeting), append it to chat history
    if update["direct_response"]:
        update["messages"] = [("assistant", update["direct_response"])]
        
    return update

async def retrieve_internal_node(state: AgentState):
    logger.debug("[LANGGRAPH] Node: retrieve_internal")
    expanded = expand_query(state["query"], state.get("messages", []))
    ctx, conf = await get_context(state["user_id"], state["query"], expanded)
    return {
        "expanded_query": expanded,
        "context": ctx,
        "confidence": float(conf)
    }

# Removed legacy search_web_node. Web scraping is now handled by node_web_agent.

def node_network_agent(state: AgentState):
    logger.debug("[LANGGRAPH] Node: network_agent")
    ans = get_network_answer(state["query"], state.get("context", ""), state.get("messages", []))
    update = {"messages": [ans]}
    if not getattr(ans, "tool_calls", None): update["final_answer"] = ans.content
    return update

def node_cloud_agent(state: AgentState):
    logger.debug("[LANGGRAPH] Node: cloud_agent")
    ans = get_cloud_answer(state["query"], state.get("context", ""), state.get("messages", []))
    update = {"messages": [ans]}
    if not getattr(ans, "tool_calls", None): update["final_answer"] = ans.content
    return update

def node_web_agent(state: AgentState):
    logger.debug("[LANGGRAPH] Node: web_agent")
    ans = get_web_answer(state["query"], state.get("context", ""), state.get("messages", []))
    update = {"messages": [ans]}
    if not getattr(ans, "tool_calls", None): update["final_answer"] = ans.content
    return update

def node_general_agent(state: AgentState):
    logger.debug("[LANGGRAPH] Node: general_agent")
    ans = get_general_answer(state["query"], state.get("context", ""), state.get("messages", []))
    update = {"messages": [ans]}
    if not getattr(ans, "tool_calls", None): update["final_answer"] = ans.content
    return update

async def escalate_node(state: AgentState):
    logger.debug("[LANGGRAPH] Node: escalate")
    ticket_id = await create_support_ticket(state["session_id"], state["query"], state.get("confidence", 0.0))
    ticket_msg = f"I have escalated this issue to the IT Service Desk. Your ticket reference is {ticket_id}."
    return {
        "ticket_id": ticket_id,
        "messages": [("assistant", ticket_msg)]
    }

# 3. Edges
def route_after_intent(state: AgentState):
    cat = state.get("intent_category")
    if cat in ["greeting", "out_of_scope", "direct_answer"]: return "end"
    if cat == "escalate": return "escalate"
    return "retrieve_internal"

def route_after_retrieval(state: AgentState):
    if state.get("confidence", 0.0) < 0.60: 
        logger.debug("[ROUTING] Low confidence. Escalating to web_agent.")
        return "web_agent"
        
    domain = state.get("intent_domain", "general")
    if domain == "network_diagnostics": return "network_agent"
    elif domain == "cloud_integrations": return "cloud_agent"
    elif domain == "web_scraping": return "web_agent"
    else: return "general_agent"

def route_after_generation(state: AgentState):
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        # Check for Denial of Wallet / Infinite Looping in the current turn only
        current_turn_tools = 0
        for m in reversed(messages):
            m_type = getattr(m, "type", "")
            if m_type in ("human", "user"):
                break
            if m_type == "tool":
                current_turn_tools += 1
                
        max_loops = int(os.getenv("MAX_TOOL_RECURSION", "5"))
        if current_turn_tools >= max_loops:
            logger.warning(f"[SECURITY] Agent hit tool loop limit ({max_loops}). Forcing escalation.")
            return "escalate"
            
        dangerous_names = [t.name for t in DANGEROUS_TOOLS]
        for tc in messages[-1].tool_calls:
            if tc["name"] in dangerous_names:
                return "dangerous_tools"
        return "safe_tools"
        
    ans = state.get("final_answer", "")
    if "cannot find the answer" in ans.lower(): return "escalate"
    return "end"

# 4. Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("route_intent", route_intent_node)
workflow.add_node("retrieve_internal", retrieve_internal_node)
workflow.add_node("network_agent", node_network_agent)
workflow.add_node("cloud_agent", node_cloud_agent)
workflow.add_node("web_agent", node_web_agent)
workflow.add_node("general_agent", node_general_agent)
workflow.add_node("escalate", escalate_node)

# Add the prebuilt ToolNodes (Split Architecture)
workflow.add_node("safe_tools", ToolNode(SAFE_ALL_TOOLS))
workflow.add_node("dangerous_tools", ToolNode(DANGEROUS_TOOLS))

workflow.set_entry_point("route_intent")

workflow.add_conditional_edges("route_intent", route_after_intent, {"end": END, "escalate": "escalate", "retrieve_internal": "retrieve_internal"})
workflow.add_conditional_edges(
    "retrieve_internal", 
    route_after_retrieval, 
    {"network_agent": "network_agent", "cloud_agent": "cloud_agent", "web_agent": "web_agent", "general_agent": "general_agent"}
)

for agent in ["network_agent", "cloud_agent", "web_agent", "general_agent"]:
    workflow.add_conditional_edges(agent, route_after_generation, {"safe_tools": "safe_tools", "dangerous_tools": "dangerous_tools", "end": END, "escalate": "escalate"})

def route_after_tools(state: AgentState):
    domain = state.get("intent_domain", "general")
    if domain == "network_diagnostics": return "network_agent"
    elif domain == "cloud_integrations": return "cloud_agent"
    elif domain == "web_scraping": return "web_agent"
    else: return "general_agent"

workflow.add_conditional_edges("safe_tools", route_after_tools, {"network_agent": "network_agent", "cloud_agent": "cloud_agent", "web_agent": "web_agent", "general_agent": "general_agent"})
workflow.add_conditional_edges("dangerous_tools", route_after_tools, {"network_agent": "network_agent", "cloud_agent": "cloud_agent", "web_agent": "web_agent", "general_agent": "general_agent"})
workflow.add_edge("escalate", END)

# 5. Export the uncompiled workflow!
# We will compile it dynamically in the pipeline so it can share the async thread!