import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    
    llm_provider = os.getenv("LLM_PROVIDER", "groq")
    llm_model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    db_path = os.getenv("CHROMA_DB_PATH", os.path.expanduser("~/.aegisdesk/chroma_db"))
    embed_model = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    top_k = int(os.getenv("TOP_K", "4"))
    
    ticket_webhook_url = os.getenv("TICKET_WEBHOOK_URL", "")
    
    langchain_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY", "")
    langchain_project = os.getenv("LANGCHAIN_PROJECT", "hcltech-aegisdesk")

    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    internal_keywords = [
        keyword.strip().lower()
        for keyword in os.getenv("INTERNAL_KEYWORDS", "hcltech").split(",")
        if keyword.strip()
    ]

    graph_memory_db_path = os.getenv("GRAPH_MEMORY_DB_PATH", os.path.expanduser("~/.aegisdesk/data/graph_memory.db"))
    graph_memory_legacy_path = os.getenv("GRAPH_MEMORY_LEGACY_PATH", os.path.expanduser("~/.aegisdesk/data/graph_memory.pkl"))
    memory_retention_enabled = os.getenv("MEMORY_RETENTION_ENABLED", "true").lower() == "true"
    memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "90"))
    memory_retention_prune_interval_hours = int(os.getenv("MEMORY_RETENTION_PRUNE_INTERVAL_HOURS", "24"))
    memory_context_enabled = os.getenv("MEMORY_CONTEXT_ENABLED", "true").lower() == "true"
    memory_context_max_facts = int(os.getenv("MEMORY_CONTEXT_MAX_FACTS", "20"))
    memory_context_token_budget = int(os.getenv("MEMORY_CONTEXT_TOKEN_BUDGET", "600"))
    memory_context_expansion_depth = int(os.getenv("MEMORY_CONTEXT_EXPANSION_DEPTH", "1"))
    memory_context_max_subqueries = int(os.getenv("MEMORY_CONTEXT_MAX_SUBQUERIES", "4"))

settings = Config()
