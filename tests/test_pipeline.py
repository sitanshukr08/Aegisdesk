import pytest
from app.rag.pipeline import analyze_intent, get_answer
from unittest.mock import patch

def test_analyze_intent_fallback():
    """
    EDGE CASE: LLM API goes down during routing.
    If the LLM fails to classify the intent, the system MUST NOT crash.
    It should log the error and default to 'it_support' so the pipeline continues to search.
    """
    with patch("app.rag.pipeline.get_llm") as mock_get_llm:
        mock_get_llm.return_value.invoke.side_effect = Exception("503 Service Unavailable")
        
        result = analyze_intent("I am locked out of my laptop", [])
        
        assert result["category"] == "it_support"
        assert result["direct_response"] is None

def test_analyze_intent_malformed_json():
    """
    EDGE CASE: LLM hallucinates and returns invalid JSON.
    The system MUST catch the JSONDecodeError and safely default to 'it_support'.
    """
    with patch("app.rag.pipeline.get_llm") as mock_get_llm:
        # Mocking an object with a .content attribute
        class MockResponse:
            content = "This is not valid JSON! Here is your answer."
            
        mock_get_llm.return_value.invoke.return_value = MockResponse()
        
        result = analyze_intent("Help me", [])
        
        assert result["category"] == "it_support"

def test_get_answer_fallback():
    """
    EDGE CASE: LLM API rate limits during final generation.
    It MUST NOT crash the LangGraph. It should return a clean error string.
    """
    with patch("langchain_core.runnables.base.RunnableSequence.invoke") as mock_invoke:
        mock_invoke.side_effect = Exception("429 Too Many Requests")
        
        result = get_answer("query", "context", [])
        
        assert "System Error: 429 Too Many Requests" in result
