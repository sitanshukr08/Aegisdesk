import httpx
from langchain_core.tools import tool
from aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.integrations")

_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    timeout=httpx.Timeout(30.0)
)

@tool
async def reset_okta_password(user_email: str) -> str:
    """Use this to reset an employee's Okta/Active Directory password and email them a temporary link."""
    logger.debug(f"[MOCK API] Sending Okta password reset for {user_email}...")
    # Using mock httpbin to simulate network latency over real HTTP connection pooling
    try:
        await _client.get("https://httpbin.org/delay/1")
    except:
        pass
    return f"Successfully sent a secure password reset link to {user_email} via Okta API."

@tool
async def update_jira_ticket(ticket_id: str, status: str, comment: str = "") -> str:
    """Use this to update the status of a Jira ticket (e.g. 'In Progress', 'Done') and add a comment."""
    logger.debug(f"[MOCK API] Updating Jira Ticket {ticket_id} to status {status}...")
    try:
        await _client.get("https://httpbin.org/delay/1")
    except:
        pass
    msg = f"Jira ticket {ticket_id} updated to '{status}'."
    if comment:
        msg += f" Comment added: '{comment}'"
    return msg

@tool
async def send_slack_message(user_id: str, message: str) -> str:
    """Use this to send a direct message to a user on Slack to notify them of a resolution."""
    logger.debug(f"[MOCK API] Sending Slack message to {user_id}...")
    try:
        await _client.get("https://httpbin.org/delay/0.5")
    except:
        pass
    return f"Slack message successfully delivered to {user_id}."

CLOUD_INTEGRATION_TOOLS = [
    reset_okta_password,
    update_jira_ticket,
    send_slack_message
]

