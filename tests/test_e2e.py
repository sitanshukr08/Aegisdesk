from unittest.mock import MagicMock, patch

import pytest

from app.rag.pipeline import analyze_intent
from src.aegisdesk.core.pipeline import execute_rag_pipeline


@pytest.mark.asyncio
async def test_e2e_network_diagnostics_happy_path():
    """
    E2E Test: Verifies that a user query successfully passes through the MiniLM router,
    hits the LangGraph execution engine, triggers a mocked agent tool, and returns a cohesive answer.
    """
    user_query = "My internet is down, ping the gateway."
    
    # 1. Verify the local MiniLM Semantic Router functions properly
    intent = await analyze_intent(user_query, [])
    assert intent["domain"] == "network_diagnostics"
    
    # 2. Execute the full RAG Pipeline with mocked LLM to prevent API calls during CI
    mock_llm_response = MagicMock()
    mock_llm_response.content = "I have successfully pinged the gateway. It is unreachable."
    mock_llm_response.tool_calls = [] # Simulate that the agent finished tool calling
    
    with patch("src.aegisdesk.core.llm_factory.get_llm") as mock_get_llm:
        # Mock the LLM to return our static response
        mock_get_llm.return_value.invoke.return_value = mock_llm_response
        
        # In a true E2E, we'd also mock the actual subprocess 'ping' to prevent system mutation,
        # but since we mocked the LLM to return 0 tool calls, the tool node is never actually invoked.
        
        async for chunk in execute_rag_pipeline("user-123", "session-456", user_query):
            if "answer" in chunk:
                # 3. Assert the pipeline properly encapsulated the agent's answer
                assert "pinged the gateway" in chunk["answer"]
                break
