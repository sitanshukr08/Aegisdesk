"""
Core Orchestration Pipeline.
Now powered by LangGraph Agentic Workflows & Async SQLite Persistent Memory.
"""
import os

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from aegisdesk.app.rag.graph import workflow
from aegisdesk.app.services.vision_service import analyze_screenshot
from aegisdesk.observability.metrics import recorder

import asyncio
import time
from collections import deque

# Global Throttle: Never execute more than 10 LangGraph pipelines simultaneously
PIPELINE_THROTTLE = asyncio.Semaphore(10)

# Sliding Window RPM Limiter: Gemini Free Tier allows 60 RPM.
# Since AegisDesk generates ~3 LLM calls per pipeline, we allow max 19 pipelines per 60 seconds.
MAX_PIPELINES_PER_MINUTE = 19
pipeline_timestamps = deque(maxlen=MAX_PIPELINES_PER_MINUTE)

async def execute_rag_pipeline(query: str, user_id: str, session_id: str, image_path: str = None, user_approval: bool = None, callbacks: list = None):
    """
    Core orchestrator that runs the LangGraph State Machine.
    Supports Tier 3 Selective HITL (Interrupts only for dangerous_tools).
    """
    recorder.start_timer("langgraph_execution_time")
    
    if image_path:
        yield {"type": "status", "msg": f"Analyzing image {os.path.basename(image_path)}"}
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            vision_context = analyze_screenshot(image_bytes, query)
            query = f"User Query: {query}\n\n[Vision Model Analysis of attached screenshot]: {vision_context}"
        except Exception as e:
            yield {"type": "content", "msg": f"\n[bold red]Vision Error:[/bold red] Failed to process image - {e}\n"}
            return

    initial_state = {
        "session_id": session_id,
        "user_id": user_id,
        "query": query,
        "messages": [("user", query)], 
        "confidence": 0.0
    }
    
    # 1. Check Semantic Cache
    try:
        from aegisdesk.app.db.vector_store import get_cache_db
        import time
        cache_db = get_cache_db()
        cache_threshold = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.95"))
        
        # asimilarity_search_with_relevance_scores gives (doc, score) where score is [0, 1]
        cached = await cache_db.asimilarity_search_with_relevance_scores(query, k=1)
        if cached and cached[0][1] >= cache_threshold:
            doc, score = cached[0]
            if time.time() - doc.metadata.get("timestamp", 0) < 3600:
                yield {"type": "content", "msg": doc.metadata["response"]}
                recorder.stop_timer("langgraph_execution_time")
                recorder.record_custom("status", "cache_hit")
                recorder.flush(query)
                return
    except Exception as e:
        from aegisdesk.observability.logger import get_logger
        get_logger("aegisdesk.pipeline").warning(f"Semantic Cache Error: {e}")

    # 2. Tier 3: Concurrency Throttle & RPM Sliding Window
    if PIPELINE_THROTTLE.locked() or len(pipeline_timestamps) == MAX_PIPELINES_PER_MINUTE:
        yield {"type": "status", "msg": "High traffic. Ticket placed in queue..."}
    
    async with PIPELINE_THROTTLE:
        # Enforce the 60-second sliding window limit
        while True:
            if len(pipeline_timestamps) < MAX_PIPELINES_PER_MINUTE:
                break
            oldest_time = pipeline_timestamps[0]
            if time.time() - oldest_time > 61.0:
                break
            await asyncio.sleep(1)
            
        pipeline_timestamps.append(time.time())
        
        config = {"configurable": {"thread_id": session_id}, "callbacks": callbacks or []}
        os.makedirs("data", exist_ok=True)
        
        try:
            final_state = None
            
            import aiosqlite
            async with aiosqlite.connect("data/checkpoints.sqlite", timeout=30, check_same_thread=False) as conn:
                await conn.execute("PRAGMA journal_mode=WAL")
                memory = AsyncSqliteSaver(conn)
                # Compile the graph with Tier 3 Selective Interrupts
                app_graph = workflow.compile(checkpointer=memory, interrupt_before=["dangerous_tools"])
                
                if user_approval is not None:
                    if user_approval:
                        stream = app_graph.astream(None, config=config)
                    else:
                        yield {"type": "content", "msg": "\n[bold red]Action Cancelled by User.[/bold red]"}
                        return
                else:
                    stream = app_graph.astream(initial_state, config=config)
                
                # Stream the Agent's Node Transitions
                async for output in stream:
                    for node_name, state_update in output.items():
                        # Extract the LLM's explanation and tool intentions for transparency!
                        if "messages" in state_update and state_update["messages"]:
                            last_msg = state_update["messages"][-1]
                            # If the agent output a natural language explanation, print it
                            if getattr(last_msg, "content", "") and getattr(last_msg, "type", "") == "ai":
                                yield {"type": "content", "msg": f"\n[dim italic]🤖 {last_msg.content}[/dim italic]\n"}
                            # If it is about to run a tool, update the spinner status
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                tool_names = [tc["name"] for tc in last_msg.tool_calls]
                                yield {"type": "status", "msg": f"Executing: {', '.join(tool_names)}..."}
                                continue
                                
                        yield {"type": "status", "msg": f"Agent completed: {node_name}"}
    
                state = await app_graph.aget_state(config)
                
                if state.next and "dangerous_tools" in state.next:
                    # Graph paused before dangerous tools!
                    last_msg = state.values.get("messages", [])[-1]
                    tool_names = [tc["name"] for tc in last_msg.tool_calls] if hasattr(last_msg, "tool_calls") else ["Unknown"]
                    yield {"type": "interrupt", "msg": f"AegisDesk wants to execute dangerous command(s): {', '.join(tool_names)}.\nDo you approve?"}
                    return
                    
                final_state = state.values
            
            if final_state is None:
                yield {"type": "content", "msg": "I am unable to process your request at this time."}
                return
    
            if final_state.get("direct_response"):
                yield {"type": "content", "msg": final_state["direct_response"]}
                
            elif final_state.get("ticket_id"):
                if final_state.get("final_answer"):
                    yield {"type": "content", "msg": final_state["final_answer"]}
                yield {"type": "content", "msg": f"\n\n🎫 I have escalated this issue to the IT Service Desk. Your ticket reference is {final_state['ticket_id']}."}
                
            elif final_state.get("web_answer"):
                yield {"type": "content", "msg": final_state["web_answer"]}
                
            elif final_state.get("final_answer"):
                msg = final_state["final_answer"]
                yield {"type": "content", "msg": msg}
                
                # Write to Semantic Cache
                try:
                    import time
                    from aegisdesk.app.db.vector_store import get_cache_db
                    cache_db = get_cache_db()
                    await cache_db.aadd_texts(
                        texts=[query], 
                        metadatas=[{"response": msg, "timestamp": time.time()}]
                    )
                except Exception as e:
                    logger.warning(f"Semantic Cache Write Error: {e}")
                
            else:
                yield {"type": "content", "msg": "I am unable to process your request at this time."}
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                yield {"type": "error", "code": "rate_limit_exceeded", "msg": "Service temporarily unavailable."}
            else:
                yield {"type": "error", "code": "system_error", "msg": f"System Error: {str(e)}"}
        finally:
            recorder.stop_timer("langgraph_execution_time")
            recorder.record_custom("status", "success")
            recorder.flush(query)

