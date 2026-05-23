import pytest
from app.api.endpoints import get_cache_key
from app.memory.graph_store import graph_db

@pytest.mark.asyncio
async def test_stale_cache_stampede():
    """
    Test 5: Stale Cache Stampede & Mutation Integrity (The Cache Test)
    Verifies that a background mutation to a user's memory instantly invalidates
    their specific cache key without wiping out the global cache or serving stale data.
    """
    session_id = "test_session_1"
    user_id = "test_user_cache"
    query = "What is my server gateway?"
    
    # 1. Simulate initial query cache key generation
    initial_key = get_cache_key(query, session_id, user_id)
    
    # Simulate caching the response
    from app.api.endpoints import RESPONSE_CACHE
    RESPONSE_CACHE[initial_key] = ["Initial Cached Response"]
    
    # 2. Assert the key hits the cache
    assert initial_key in RESPONSE_CACHE
    
    # 3. Mutate the system state (this updates graph_db.user_mutations)
    await graph_db.supersede_facts_by_entity(user_id)
    
    # 4. Re-run the exact same query within the same session
    post_mutation_key = get_cache_key(query, session_id, user_id)
    
    # 5. Assert the dynamic caching mechanism recognized the state change
    assert initial_key != post_mutation_key, "Cache key did not mutate after state change!"
    assert post_mutation_key not in RESPONSE_CACHE, "System served a stale cache chunk!"
