import pytest
from app.rag.pipeline import analyze_intent

@pytest.mark.asyncio
async def test_analyze_intent_semantic_matching():
    """Test that the offline router correctly matches intents."""
    # Test network routing
    res1 = await analyze_intent("ping the network gateway", [])
    assert res1["domain"] == "network_diagnostics"
    assert res1["category"] == "it_support"
    
    # Test cloud/identity routing
    res2 = await analyze_intent("My Okta session died", [])
    assert res2["domain"] == "cloud_integrations"
    assert res2["category"] == "it_support"

@pytest.mark.asyncio
async def test_analyze_intent_fallback():
    """Test that unrelated queries fall back to general IT support safely."""
    res = await analyze_intent("What is the recipe for chocolate cake?", [])
    assert res["domain"] == "general"
    assert res["category"] == "it_support"

@pytest.mark.asyncio
async def test_analyze_intent_hardcoded_direct():
    """Test the authorship query delegation."""
    res = await analyze_intent("Who developed AegisDesk?", [])
    assert res["category"] == "it_support"
    assert res["domain"] == "web_scraping"

from unittest.mock import MagicMock, patch
from aegisdesk.core.pipeline import execute_rag_pipeline

@pytest.mark.asyncio
async def test_tool_recursion_limit(monkeypatch):
    """
    Test 3: Tool Recursion Loop Breakage (The Denial of Wallet Test)
    Verify that an agent repeatedly encountering tool errors is forcefully stopped
    when hitting the MAX_TOOL_RECURSION limit.
    """
    # Lower recursion limit for the test
    monkeypatch.setenv("MAX_TOOL_RECURSION", "3")
    
    from langchain_core.runnables import Runnable
    class FakeLLM(Runnable):
        def invoke(self, input, config=None, **kwargs):
            from langchain_core.messages import AIMessage
            return AIMessage(content="", tool_calls=[{"name": "ping_network", "args": {"host": "127.0.0.1"}, "id": "call_retry"}])
        async def ainvoke(self, input, config=None, **kwargs):
            return self.invoke(input, config, **kwargs)
        def bind_tools(self, *args, **kwargs):
            return self
        def with_config(self, *args, **kwargs):
            return self

    with patch("app.rag.pipeline.get_llm", return_value=FakeLLM()):
        
        with patch("aegisdesk.core.tools.run_cmd") as mock_tool:
            # Tool constantly returns transient error, forcing retry
            mock_tool.return_value = "Transient error, please retry."
            
            chunks = []
            async for chunk in execute_rag_pipeline("default_user", "recursion_session", "Ping the network"):
                chunks.append(chunk)

    # Check if the pipeline exited gracefully and output an escalation ticket or final answer
    escalated = False
    for chunk in chunks:
        if chunk.get("type") == "content" and "escalated this issue" in str(chunk.get("msg", "")):
            escalated = True
            
    assert escalated, "Pipeline did not gracefully escalate after hitting the tool recursion limit."

