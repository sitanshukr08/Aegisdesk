import pytest
from app.api.endpoints import get_cache_key
from app.services.web_agent import needs_actionable_answer, answer_is_actionable

def test_cache_key_generation():
    key1 = get_cache_key("How do I connect to VPN?", "aryan")
    key2 = get_cache_key("how do I connect to vpn?   ", "aryan")
    key3 = get_cache_key("How do I connect to VPN?", "admin")
    
    # Test 1: Cache keys must be case-insensitive and ignore trailing spaces
    assert key1 == key2
    
    # Test 2: User Isolation - The exact same query from different users MUST generate different cache keys
    assert key1 != key3

def test_action_triggers():
    # Test 3: The system must correctly identify when a user needs a step-by-step guide
    assert needs_actionable_answer("How to reset my password?") == True
    assert needs_actionable_answer("What is HCLTech?") == False
    
def test_action_signals():
    # Test 4: The system must correctly identify if a web search result contains actionable steps
    assert answer_is_actionable("First, click on settings and reboot.") == True
    assert answer_is_actionable("The VPN was invented in 1996.") == False