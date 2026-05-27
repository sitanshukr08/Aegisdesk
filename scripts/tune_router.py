import asyncio
import os

from aegisdesk.app.rag.pipeline import async_get_router

test_cases = [
    # Network -> static_route_1
    ("Can you ping 192.168.1.1?", "static_route_1"),
    ("Are port 80 and 443 open on google.com?", "static_route_1"),
    ("Run a traceroute to internal-git.hcl.com", "static_route_1"),
    ("Check the listening TCP ports on this machine", "static_route_1"),
    ("What is my current IP address?", "static_route_1"),
    ("Execute an nmap scan on the local subnet", "static_route_1"),
    ("Why is the corporate gateway dropping packets?", "static_route_1"),
    ("Check DNS resolution for the auth server", "static_route_1"),
    ("Show me the active network interfaces", "static_route_1"),
    ("Is the proxy blocking traffic to github?", "static_route_1"),
    
    # Cloud/Software -> static_route_2
    ("Create an AWS EC2 instance in us-east-1", "static_route_2"),
    ("Reset my Okta password", "static_route_2"),
    ("Unlock my Jira account", "static_route_2"),
    ("Provision a new Azure SQL database", "static_route_2"),
    ("Restart the Kubernetes pod for the payment service", "static_route_2"),
    ("Add me to the github enterprise organization", "static_route_2"),
    ("Delete the old S3 bucket", "static_route_2"),
    ("Give me admin access to the production cluster", "static_route_2"),
    ("Scale the web deployment to 5 replicas", "static_route_2"),
    ("List all EC2 instances running in dev", "static_route_2"),
    
    # Web/Scraping -> static_route_3
    ("Read the HR policy from https://hr.internal.com/policy", "static_route_3"),
    ("Who created AegisDesk?", "static_route_3"),
    ("Who is the author of AegisDesk?", "static_route_3"),
    ("Search the internet for the latest python version", "static_route_3"),
    ("Scrape the wikipedia page for Active Directory", "static_route_3"),
    ("What does the news say about Microsoft?", "static_route_3"),
    ("Check the status page at https://status.github.com", "static_route_3"),
    ("Can you extract text from this internal wiki link?", "static_route_3"),
    ("Look up the recent CVEs for OpenSSL on the web", "static_route_3"),
    ("Read the docs from https://docs.python.org", "static_route_3"),
    
    # General/RAG -> None
    ("How do I setup the BigFix VPN?", "None"),
    ("What is the process to get a new laptop?", "None"),
    ("When do passwords expire?", "None"),
    ("I got locked out of my AD account, what do I do?", "static_route_2"),
    ("How many leaves do I get?", "None"),
    ("What is the holiday calendar for this year?", "None"),
    ("Can I install Docker on my laptop?", "None"),
    ("What do I do if I lose my ID card?", "None"),
    ("How do I get temporary admin rights?", "None"),
    ("What is the IT helpdesk phone number?", "None"),
    
    # Out of Scope / Fallback -> None
    ("Write a poem about a robot", "None"),
    ("What is the recipe for chocolate cake?", "None"),
    ("Translate this sentence to French", "None"),
    ("Who won the superbowl in 2020?", "None"),
    ("Write a python script to sort an array", "None"),
    ("Tell me a funny joke", "None"),
    ("What is the meaning of life?", "None"),
    ("Solve this math problem: 2+2", "None"),
    ("Summarize the plot of the matrix", "None"),
    ("Can you give me medical advice?", "None"),

    # Greetings -> static_route_0
    ("Hi there", "static_route_0"),
    ("Hello AegisDesk", "static_route_0"),
    ("Good morning", "static_route_0"),
    ("Thanks bye", "static_route_0"),
]

async def tune():
    print("Initializing router...")
    router = await async_get_router()
    
    samples = [tc[0] for tc in test_cases]
    labels = [tc[1] for tc in test_cases]
    
    print("Fitting thresholds...")
    router.fit_thresholds(samples, labels)
    
    print("New thresholds:")
    for name, route in router._route_map.items():
        print(f"  {name}: {route.threshold}")
        
    await router.stop()

if __name__ == "__main__":
    asyncio.run(tune())
