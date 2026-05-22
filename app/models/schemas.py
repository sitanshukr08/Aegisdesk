from pydantic import BaseModel, Field
import uuid
from typing import Optional

class QueryReq(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session ID for conversational memory")

class QueryRes(BaseModel):
    session_id: str
    original_query: str
    normalized_query: str
    answer: str
    confidence: float
    escalate: bool
    ticket_id: Optional[str] = None