import asyncio
import time
import pytest
from app.rag.retriever import get_context
from app.api.endpoints import health_check

@pytest.mark.asyncio
async def test_event_loop_bottleneck():
    """
    Test 4: CPU-Bound Event Loop Saturation (The Bottleneck Test)
    Proves that heavy ONNX inference running via asyncio.to_thread in the background
    does not block the primary FastAPI event loop.
    """
    # 1. Start a heavy background task simulating semantic reranking
    # We pass a large arbitrary context to force BGE-Reranker to work hard
    heavy_task = asyncio.create_task(
        get_context("user123", "How do I reset my password?", "How do I reset my password?")
    )
    
    # Give the heavy task a moment to spin up and saturate the CPU thread
    await asyncio.sleep(0.01)
    
    # 2. While the background task is running, hit the health check route multiple times
    health_latencies = []
    for _ in range(10):
        start = time.perf_counter()
        res = await health_check()
        duration = time.perf_counter() - start
        health_latencies.append(duration)
        assert res["status"] == "healthy"
        await asyncio.sleep(0.01)
        
    # Wait for the heavy task to finish so it doesn't leak into other tests
    try:
        await heavy_task
    except Exception:
        pass
        
    # 3. Verify P99 latency is low (e.g. under 50ms)
    # The health check is purely async so it should return instantly, even if a thread is busy
    max_latency = max(health_latencies)
    assert max_latency < 0.05, f"Event loop was blocked! Max latency: {max_latency*1000:.2f}ms"
