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
    Now supports HITL (Human-in-the-Loop) tool interrupts.
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
        
        # Open an Async SQLite connection specifically for this session!
        async with AsyncSqliteSaver.from_conn_string("data/checkpoints.sqlite") as memory:
            # Compile the graph with memory attached to this async thread, and pause before tools run
            app_graph = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
            
            if user_approval is True:
                # Resume exactly where it left off
                stream = app_graph.astream(None, config=config)
            elif user_approval is False:
                # User denied the tool. Fake a tool response so the LLM knows it was denied.
                from langchain_core.messages import ToolMessage
                state = await app_graph.aget_state(config)
                last_msg = state.values["messages"][-1]
                tool_call = last_msg.tool_calls[0]
                denial_msg = ToolMessage(content="User DENIED permission to run this tool. Do not try again. Suggest a manual workaround.", tool_call_id=tool_call["id"])
                
                # Update state as if the tool node ran
                await app_graph.aupdate_state(config, {"messages": [denial_msg]}, as_node="tools")
                stream = app_graph.astream(None, config=config)
            else:
                # Standard first run
                stream = app_graph.astream(initial_state, config=config)
            
            # Stream the Agent's Node Transitions
            async for output in stream:
                for node_name, state_update in output.items():
                    yield {"type": "status", "msg": f"Agent completed: {node_name}"}
                    
                    if final_state is None:
                        final_state = state_update.copy()
                    else:
                        final_state.update(state_update)

            # Check if the graph has paused due to an interrupt
            state = await app_graph.aget_state(config)
            if state.next and state.next[0] == 'tools':
                last_msg = state.values["messages"][-1]
                tool_call = last_msg.tool_calls[0]
                yield {
                    "type": "interrupt", 
                    "tool_name": tool_call["name"], 
                    "tool_args": tool_call["args"],
                    "msg": f"AegisDesk wants to run `{tool_call['name']}` with args `{tool_call['args']}`.\nDo you approve?"
                }
                return
        
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