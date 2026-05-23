"""
Core Orchestration Pipeline.
Now powered by LangGraph Agentic Workflows & Async SQLite Persistent Memory.
"""
import os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.rag.graph import workflow
from src.aegisdesk.observability.metrics import recorder
from app.services.vision_service import analyze_screenshot

async def execute_rag_pipeline(query: str, user_id: str, session_id: str, image_path: str = None, user_approval: bool = None):
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
    
    config = {"configurable": {"thread_id": session_id}}
    os.makedirs("data", exist_ok=True)
    
    try:
        final_state = None
        
        async with AsyncSqliteSaver.from_conn_string("data/checkpoints.sqlite") as memory:
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
            yield {"type": "content", "msg": final_state["final_answer"]}
            
        else:
            yield {"type": "content", "msg": "I am unable to process your request at this time."}
            
    except Exception as e:
        yield {"type": "content", "msg": f"\nSystem Error: {str(e)}"}
    finally:
        recorder.stop_timer("langgraph_execution_time")
        recorder.record_custom("status", "success")
        recorder.flush(query)