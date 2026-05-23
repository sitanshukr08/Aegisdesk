import json
import logging
import uuid
from pathlib import Path

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

async def create_support_ticket(session_id: str, query: str, context_score: float) -> str:
    """
    Simulates creating an IT support ticket in a system like ServiceNow or Jira.
    Fires an async webhook if the URL is configured, and logs it locally for the CLI.
    """
    ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    
    payload = {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "issue_description": query,
        "bot_confidence_score": context_score,
        "status": "Open",
        "assignment_group": "L1_Service_Desk"
    }
    
    # Save to local disk for the CLI to read
    Path("data").mkdir(exist_ok=True)
    with open("data/tickets.jsonl", "a") as f:
        f.write(json.dumps(payload) + "\n")

    if not settings.ticket_webhook_url:
        logger.warning(f"Webhook URL not set. Simulated Ticket Created: {ticket_id}")
        return ticket_id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(settings.ticket_webhook_url, json=payload, timeout=5.0)
            resp.raise_for_status()
            logger.info(f"Successfully created ticket {ticket_id} via webhook.")
    except Exception as e:
        logger.error(f"Failed to trigger escalation webhook: {str(e)}")
        
    return ticket_id