from app.api.endpoints import get_cache_key


def test_cache_key_generation():
    key1 = get_cache_key("How do I connect to VPN?", "aryan")
    key2 = get_cache_key("how do I connect to vpn?   ", "aryan")
    key3 = get_cache_key("How do I connect to VPN?", "admin")
    
    # Test 1: Cache keys must be case-insensitive and ignore trailing spaces
    assert key1 == key2
    
    # Test 2: User Isolation - The exact same query from different users MUST generate different cache keys
    assert key1 != key3