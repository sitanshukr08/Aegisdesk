import time
import json
from app.rag.pipeline import analyze_intent

def run_benchmark():
    test_cases = [
        # Network
        ("Can you ping 192.168.1.1?", "it_support", "network_diagnostics"),
        ("Are port 80 and 443 open on google.com?", "it_support", "network_diagnostics"),
        ("Run a traceroute to internal-git.hcl.com", "it_support", "network_diagnostics"),
        ("Check the listening TCP ports on this machine", "it_support", "network_diagnostics"),
        ("What is my current IP address?", "it_support", "network_diagnostics"),
        ("Execute an nmap scan on the local subnet", "it_support", "network_diagnostics"),
        ("Why is the corporate gateway dropping packets?", "it_support", "network_diagnostics"),
        ("Check DNS resolution for the auth server", "it_support", "network_diagnostics"),
        ("Show me the active network interfaces", "it_support", "network_diagnostics"),
        ("Is the proxy blocking traffic to github?", "it_support", "network_diagnostics"),
        
        # Cloud/Software
        ("Create an AWS EC2 instance in us-east-1", "it_support", "cloud_integrations"),
        ("Reset my Okta password", "it_support", "cloud_integrations"),
        ("Unlock my Jira account", "it_support", "cloud_integrations"),
        ("Provision a new Azure SQL database", "it_support", "cloud_integrations"),
        ("Restart the Kubernetes pod for the payment service", "it_support", "cloud_integrations"),
        ("Add me to the github enterprise organization", "it_support", "cloud_integrations"),
        ("Delete the old S3 bucket", "it_support", "cloud_integrations"),
        ("Give me admin access to the production cluster", "it_support", "cloud_integrations"),
        ("Scale the web deployment to 5 replicas", "it_support", "cloud_integrations"),
        ("List all EC2 instances running in dev", "it_support", "cloud_integrations"),
        
        # Web/Scraping
        ("Read the HR policy from https://hr.internal.com/policy", "it_support", "web_scraping"),
        ("Who created AegisDesk?", "it_support", "web_scraping"),
        ("Who is the author of AegisDesk?", "it_support", "web_scraping"),
        ("Search the internet for the latest python version", "it_support", "web_scraping"),
        ("Scrape the wikipedia page for Active Directory", "it_support", "web_scraping"),
        ("What does the news say about Microsoft?", "it_support", "web_scraping"),
        ("Check the status page at https://status.github.com", "it_support", "web_scraping"),
        ("Can you extract text from this internal wiki link?", "it_support", "web_scraping"),
        ("Look up the recent CVEs for OpenSSL on the web", "it_support", "web_scraping"),
        ("Read the docs from https://docs.python.org", "it_support", "web_scraping"),
        
        # General/RAG
        ("How do I setup the BigFix VPN?", "it_support", "general"),
        ("What is the process to get a new laptop?", "it_support", "general"),
        ("When do passwords expire?", "it_support", "general"),
        ("I got locked out of my AD account, what do I do?", "it_support", "cloud_integrations"),
        ("How many leaves do I get?", "it_support", "general"),
        ("What is the holiday calendar for this year?", "it_support", "general"),
        ("Can I install Docker on my laptop?", "it_support", "general"),
        ("What do I do if I lose my ID card?", "it_support", "general"),
        ("How do I get temporary admin rights?", "it_support", "general"),
        ("What is the IT helpdesk phone number?", "it_support", "general"),
        
        # Out of Scope / Fallback
        ("Write a poem about a robot", "it_support", "general"),
        ("What is the recipe for chocolate cake?", "it_support", "general"),
        ("Translate this sentence to French", "it_support", "general"),
        ("Who won the superbowl in 2020?", "it_support", "general"),
        ("Write a python script to sort an array", "it_support", "general"),
        ("Tell me a funny joke", "it_support", "general"),
        ("What is the meaning of life?", "it_support", "general"),
        ("Solve this math problem: 2+2", "it_support", "general"),
        ("Summarize the plot of the matrix", "it_support", "general"),
        ("Can you give me medical advice?", "it_support", "general")
    ]
    
    correct = 0
    total = len(test_cases)
    start_time = time.time()
    
    # Warmup the ONNX model to avoid cold start penalty
    analyze_intent("Warmup query", [])
    
    print("🚀 Starting AegisDesk Semantic Router Benchmark...")
    print("=" * 60)
    
    query_times = []
    
    for query, expected_category, expected_domain in test_cases:
        t0 = time.perf_counter()
        res = analyze_intent(query, [])
        t1 = time.perf_counter()
        
        latency = (t1 - t0) * 1000
        query_times.append(latency)
        
        cat = res.get("category")
        dom = res.get("domain")
        
        is_correct = (cat == expected_category) and (dom == expected_domain)
        if is_correct:
            correct += 1
            status = "✅ PASS"
        else:
            status = f"❌ FAIL (Got: {cat}/{dom})"
            
        print(f"[{latency:.2f}ms] {status} | Query: '{query}'")

    total_time = time.time() - start_time
    avg_latency = sum(query_times) / len(query_times)
    accuracy = (correct / total) * 100
    
    print("=" * 60)
    print(f"📊 Benchmark Results:")
    print(f"Total Queries : {total}")
    print(f"Total Time    : {total_time:.2f}s")
    print(f"Avg Latency   : {avg_latency:.2f} ms per query")
    print(f"Accuracy      : {accuracy:.1f}% ({correct}/{total})")
    print(f"Token Cost    : $0.00 (100% Local Inference)")

if __name__ == "__main__":
    run_benchmark()
