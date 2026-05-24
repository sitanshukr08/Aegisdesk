import asyncio
import json
import time
import argparse
import sys
import pandas as pd
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
from tabulate import tabulate
import tiktoken
from langchain_core.callbacks import BaseCallbackHandler
from aegisdesk.core.pipeline import execute_rag_pipeline
from aegisdesk.core.llm_factory import get_llm
import numpy as np

class ResearchCallbackTracker(BaseCallbackHandler):
    def __init__(self):
        self.total_tokens = 0
        self.tool_calls = 0

    def on_llm_end(self, response, **kwargs):
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self.total_tokens += usage.get("total_tokens", 0)

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.tool_calls += 1

class EventLoopMonitor:
    def __init__(self):
        self.is_running = False
        self.total_block_time = 0.0

    async def run(self):
        self.is_running = True
        while self.is_running:
            before = asyncio.get_event_loop().time()
            await asyncio.sleep(0.01)
            after = asyncio.get_event_loop().time()
            block_time = (after - before) - 0.01
            if block_time > 0.005:
                self.total_block_time += block_time

def count_tokens_fallback(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except:
        return len(text.split())

async def run_baseline_query(query: str, tracker: ResearchCallbackTracker):
    llm = get_llm()
    res = await llm.ainvoke(query, config={"callbacks": [tracker]})
    await asyncio.sleep(0.5) 
    return res

async def process_ticket(ticket, session_id, use_baseline=False, fallback_tokens=False):
    max_retries = 10
    for attempt in range(max_retries):
        try:
            tracker = ResearchCallbackTracker()
            t0 = time.perf_counter()
            
            response_text = ""
            actual_agent = "monolithic" if use_baseline else "router_fallback"
            success = True
            
            if use_baseline:
                res = await run_baseline_query(ticket["query"], tracker)
                response_text = res.content
            else:
                async for chunk in execute_rag_pipeline(ticket["query"], "bench_user", session_id, None, None, callbacks=[tracker]):
                    if isinstance(chunk, dict):
                        if chunk.get("type") == "error":
                            if chunk.get("code") == "rate_limit_exceeded":
                                raise Exception("429 RateLimitError internally signaled")
                            else:
                                success = False
                        elif chunk.get("type") == "status" and "Agent completed:" in chunk.get("msg", ""):
                            actual_agent = chunk["msg"].split("Agent completed:")[-1].strip()
                        elif chunk.get("type") == "content":
                            response_text += chunk.get("msg", "")
                            
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000
            
            tokens = tracker.total_tokens
            if fallback_tokens or tokens == 0:
                tokens = count_tokens_fallback(ticket["query"] + response_text)
                
            return {
                "Query": ticket["query"][:30] + "...",
                "Type": ticket["type"],
                "Expected_Agent": ticket["expected_agent"],
                "Actual_Agent": actual_agent,
                "Latency_ms": latency_ms,
                "Tokens": tokens,
                "ToolSteps": tracker.tool_calls,
                "Success": success,
                "RetryCount": attempt
            }
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                await asyncio.sleep(2 + attempt * 2)
            else:
                return {
                    "Query": ticket["query"][:30] + "...",
                    "Type": ticket["type"],
                    "Expected_Agent": ticket["expected_agent"],
                    "Actual_Agent": "error_fallback",
                    "Latency_ms": 0,
                    "Tokens": 0,
                    "ToolSteps": 0,
                    "Success": False,
                    "RetryCount": attempt
                }
    
    return {
        "Query": ticket["query"][:30] + "...",
        "Type": ticket["type"],
        "Expected_Agent": ticket["expected_agent"],
        "Actual_Agent": "rate_limit_failure",
        "Latency_ms": 0,
        "Tokens": 0,
        "ToolSteps": 0,
        "Success": False,
        "RetryCount": max_retries
    }

async def run_batch(tickets, baseline, fallback_tokens):
    monitor = EventLoopMonitor()
    monitor_task = asyncio.create_task(monitor.run())
    
    tasks = []
    start_time = time.time()
    for i, ticket in enumerate(tickets):
        session_id = f"bench_sess_{time.time()}_{i}"
        tasks.append(process_ticket(ticket, session_id, baseline, fallback_tokens))
        
    results = await asyncio.gather(*tasks)
    
    monitor.is_running = False
    await monitor_task
    
    total_time = time.time() - start_time
    
    df = pd.DataFrame(results)
    
    return {
        "N": len(tickets),
        "Total_Wall_Time_s": total_time,
        "Total_Block_Time_s": monitor.total_block_time,
        "Block_Percent": (monitor.total_block_time / total_time) * 100 if total_time > 0 else 0,
        "Avg_Latency_ms": df["Latency_ms"].mean(),
        "Avg_Tokens": df["Tokens"].mean(),
        "Success_Rate": df["Success"].mean() * 100
    }, df

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true", help="Run monolithic baseline instead of AegisDesk Graph")
    parser.add_argument("--runs", type=int, default=3, help="Number of repetitions per N")
    parser.add_argument("--concurrency", type=int, default=None, help="Specific concurrency level")
    args = parser.parse_args()
    
    with open("tests/benchmark_data.json", "r") as f:
        all_tickets = json.load(f)
        
    if args.concurrency:
        concurrency_levels = [args.concurrency]
    else:
        concurrency_levels = [5, 10, 20]
    
    print(f"🚀 Starting Research Benchmark {'(BASELINE)' if args.baseline else '(AEGISDESK)'}")
    
    fallback_tokens = False 
    
    batch_results = []
    all_query_results = []
    
    for n in concurrency_levels:
        tickets = all_tickets[:n]
        print(f"\n--- Running N={n} ({args.runs} runs) ---")
        
        run_stats = []
        for run in range(args.runs):
            print(f"  Run {run+1}/{args.runs}...")
            stats, df = await run_batch(tickets, args.baseline, fallback_tokens)
            run_stats.append(stats)
            df["N"] = n
            df["Run"] = run + 1
            all_query_results.append(df)
            
        avg_stats = {
            "N": n,
            "Wall_Time_s": f"{np.mean([s['Total_Wall_Time_s'] for s in run_stats]):.2f} ± {np.std([s['Total_Wall_Time_s'] for s in run_stats]):.2f}",
            "Block_Time_s": f"{np.mean([s['Total_Block_Time_s'] for s in run_stats]):.2f} ± {np.std([s['Total_Block_Time_s'] for s in run_stats]):.2f}",
            "Block_%": f"{np.mean([s['Block_Percent'] for s in run_stats]):.1f}%",
            "Avg_Latency_ms": f"{np.mean([s['Avg_Latency_ms'] for s in run_stats]):.2f}",
            "Avg_Tokens": f"{np.mean([s['Avg_Tokens'] for s in run_stats]):.2f}",
            "Success_%": f"{np.mean([s['Success_Rate'] for s in run_stats]):.1f}%"
        }
        batch_results.append(avg_stats)
        
    print("\n" + "="*50)
    print("📊 LEVEL 1: BATCH-LEVEL RESULTS (PRIMARY METRIC)")
    batch_df = pd.DataFrame(batch_results)
    
    latex_table = tabulate(
        batch_df,
        headers="keys",
        tablefmt="latex_booktabs",
        showindex=False
    )
    
    print(tabulate(batch_df, headers="keys", tablefmt="grid"))
    
    prefix = "baseline_" if args.baseline else "aegisdesk_"
    with open(f"tests/{prefix}batch_table.tex", "w") as f:
        f.write(latex_table)
        
    final_query_df = pd.concat(all_query_results, ignore_index=True)
    final_query_df.to_csv(f"tests/{prefix}query_results.csv", index=False)
    print(f"\nResults exported to {prefix}batch_table.tex and {prefix}query_results.csv")
    
if __name__ == "__main__":
    asyncio.run(main())
