# AegisDesk Architecture

This document maps the core execution flow, memory structures, and architectural boundaries of AegisDesk.

## Swarm Graph (LangGraph)

```mermaid
graph TD
    User([User Request]) --> Router[Zero-Token Router<br/>(MiniLM-L6-v2)]
    
    %% Semantic Routing
    Router -- Confidence > 0.20 --> DomainCheck{Intent Domain}
    Router -- Confidence < 0.20 --> Retrieve[Retrieve Internal<br/>(ChromaDB context)]
    
    %% Intent Domains
    DomainCheck -- network_diagnostics --> NetAgent[Network Agent<br/>(OS Diagnostic Tools)]
    DomainCheck -- cloud_integrations --> CloudAgent[Cloud Agent<br/>(REST API Tools)]
    DomainCheck -- web_scraping --> WebAgent[Web Agent<br/>(Headless Scraper with SSRF protection)]
    DomainCheck -- general --> GenAgent[General IT Agent]
    
    %% Sub-Routing fallback
    Retrieve -- High Confidence --> GenAgent
    Retrieve -- Low Confidence --> WebAgent
    
    %% HITL / Safety boundary
    NetAgent --> Supervisor{Tool Loop Check}
    CloudAgent --> Supervisor
    WebAgent --> Supervisor
    GenAgent --> Supervisor
    
    Supervisor -- Tool Calls < MAX_TOOL_RECURSION --> Tools[Execute Tool Node]
    Tools --> DomainCheck
    
    Supervisor -- Infinite Loop Detected --> Escalate[Escalate Node<br/>(ServiceNow/Jira)]
    Supervisor -- Final Answer Generated --> End([Return Final Answer])
    
    Escalate --> End
```

## Memory Architecture (Semantic Graph)

```mermaid
graph TD
    subgraph SQLite-Vec Database
        Nodes[Entity Nodes<br/>(Users, Devices, Issues)]
        Edges[Relational Edges<br/>(Belongs_to, Associated_with)]
    end
    
    subgraph FastAPI Runtime
        Extract[Extractor<br/>(Entity Extraction)]
        Assemble[Assembler<br/>(Graph Traversal)]
    end
    
    UserQuery --> Extract
    Extract --> Nodes
    Nodes --> Edges
    Edges --> Assemble
    Assemble --> Context(Injected Context)
```

## Zero-Trust Security Boundary
1. **OS Execution**: `subprocess.run` enforces `shell=False`.
2. **SSRF**: `DNSPinnedAdapter` resolves IP once and pins it to the socket layer.
3. **Loop Mitigation**: `MAX_TOOL_RECURSION` halts denial of wallet attacks.
