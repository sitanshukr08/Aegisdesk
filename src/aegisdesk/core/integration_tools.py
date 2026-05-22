from langchain_core.tools import tool
from src.aegisdesk.observability.logger import get_logger
import time

logger = get_logger("aegisdesk.integrations")

@tool
def reset_okta_password(user_email: str) -> str:
    """Use this to reset an employee's Okta/Active Directory password and email them a temporary link."""
    logger.debug(f"[MOCK API] Sending Okta password reset for {user_email}...")
    time.sleep(1) # Simulate network latency
    return f"Successfully sent a secure password reset link to {user_email} via Okta API."

@tool
def update_jira_ticket(ticket_id: str, status: str, comment: str = "") -> str:
    """Use this to update the status of a Jira ticket (e.g. 'In Progress', 'Done') and add a comment."""
    logger.debug(f"[MOCK API] Updating Jira Ticket {ticket_id} to status {status}...")
    time.sleep(1)
    msg = f"Jira ticket {ticket_id} updated to '{status}'."
    if comment:
        msg += f" Comment added: '{comment}'"
    return msg

@tool
def send_slack_message(user_id: str, message: str) -> str:
    """Use this to send a direct message to a user on Slack to notify them of a resolution."""
    logger.debug(f"[MOCK API] Sending Slack message to {user_id}...")
    time.sleep(0.5)
    return f"Slack message successfully delivered to {user_id}."

CLOUD_INTEGRATION_TOOLS = [
    reset_okta_password,
    update_jira_ticket,
    send_slack_message
]
