from aegisdesk.app.services.web_agent import run_web_research

from aegisdesk.app.config.settings import settings
from aegisdesk.app.rag.pipeline import analyze_intent, expand_query, get_answer
from aegisdesk.app.rag.retriever import get_context
from aegisdesk.app.services.webhook_service import create_support_ticket
from aegisdesk.app.utils.preprocessing import clean_text


def is_internal_query(query: str) -> bool:
    if not settings.internal_keywords:
        return False
    normalized_query = query.lower()
    return any(keyword in normalized_query for keyword in settings.internal_keywords)

async def process_user_query(session_id: str, user_id: str, raw_q: str):
    clean_q = clean_text(raw_q)
    
    meta = {
        "session_id": session_id,
        "user_id": user_id,
        "original_query": raw_q,
        "normalized_query": clean_q,
        "confidence": 0.0,
        "escalate": False,
        "ticket_id": None
    }
    
    if not clean_q:
        yield {"chunk": "Please provide a valid question.", "meta": meta}
        return
    
    intent = await analyze_intent(session_id, clean_q)
    print(f"\n[ROUTER] Classified as: {intent.get('category')}")
    
    if intent.get("category") in ["greeting", "out_of_scope"]:
        meta["confidence"] = 1.0
        yield {"chunk": intent.get("direct_response") or "I am an IT Support bot. I cannot assist with this request.", "meta": meta}
        return

    if intent.get("category") == "escalate":
        meta["escalate"] = True
        meta["confidence"] = 1.0
        meta["ticket_id"] = await create_support_ticket(session_id, raw_q, 1.0)
        yield {"chunk": f"I apologize for the frustration. I am escalating your case to a human agent immediately. Your ticket reference is {meta['ticket_id']}.", "meta": meta}
        return

    expanded_q = await expand_query(session_id, clean_q)
    print(f"[EXPANDER] Expanded: {expanded_q}")
    
    ctx, conf = get_context(user_id, clean_q, expanded_q)
    meta["confidence"] = round(conf, 4)

    if not ctx or conf < 0.60:
        if is_internal_query(clean_q):
            meta["escalate"] = True
            meta["ticket_id"] = await create_support_ticket(session_id, raw_q, conf)
            yield {"chunk": f"I couldn't find this in the internal knowledge base and it appears to be an internal system. I have escalated this issue to the IT Service Desk. Your ticket reference is {meta['ticket_id']}.", "meta": meta}
            return
        yield {"chunk": "\n*Searching the live internet for a solution...*\n\n", "meta": meta}
        
        web_answer = await run_web_research(expanded_q)
        
        if web_answer:
            yield {"chunk": web_answer, "meta": meta}
            return
        else:
            meta["escalate"] = True
            meta["ticket_id"] = await create_support_ticket(session_id, raw_q, conf)
            yield {"chunk": f"I couldn't find a solution locally or on the web.\n\nI have escalated this issue to the IT Service Desk. Your ticket reference is {meta['ticket_id']}.", "meta": meta}
            return

    full_answer = get_answer(clean_q, ctx, [])
    yield {"chunk": full_answer, "meta": meta}
        
    if "cannot find the answer" in full_answer.lower():
        meta["escalate"] = True
        meta["ticket_id"] = await create_support_ticket(session_id, raw_q, conf)
        yield {"chunk": f"\n\nI have escalated this issue to the IT Service Desk. Your ticket reference is {meta['ticket_id']}.", "meta": meta}

