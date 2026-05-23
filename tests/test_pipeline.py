from app.rag.pipeline import analyze_intent


def test_analyze_intent_semantic_matching():
    """Test that the offline router correctly matches intents."""
    # Test network routing
    res1 = analyze_intent("ping the network gateway", [])
    assert res1["domain"] == "network_diagnostics"
    assert res1["category"] == "it_support"
    
    # Test cloud/identity routing
    res2 = analyze_intent("My Okta session died", [])
    assert res2["domain"] == "cloud_integrations"
    assert res2["category"] == "it_support"

def test_analyze_intent_fallback():
    """Test that unrelated queries fall back to general IT support safely."""
    res = analyze_intent("What is the recipe for chocolate cake?", [])
    assert res["domain"] == "general"
    assert res["category"] == "it_support"

def test_analyze_intent_hardcoded_direct():
    """Test the authorship query delegation."""
    res = analyze_intent("Who developed AegisDesk?", [])
    assert res["category"] == "it_support"
    assert res["domain"] == "web_scraping"
