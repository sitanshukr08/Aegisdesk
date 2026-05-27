from langchain_core.language_models.chat_models import BaseChatModel

from aegisdesk.app.config.settings import settings
from aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.llm_factory")

class ConfigurationError(Exception):
    """Raised when an LLM provider is misconfigured or missing credentials."""
    pass

from typing import Literal

def get_llm(temperature: float = 0.0, response_format: dict = None, tier: Literal["fast", "synthesis", "default"] = "default") -> BaseChatModel:
    """
    Factory function that returns the configured LLM provider with failover.
    Ensures vendor agnosticism across the enterprise.
    """
    kwargs = {"temperature": temperature}
    if response_format:
        kwargs["model_kwargs"] = {"response_format": response_format}
        
    providers = []
    
    # Model selection based on tier
    groq_model = settings.llm_model
    openai_model = getattr(settings, "openai_model", "gpt-4o-mini")
    
    if tier == "fast":
        groq_model = "llama-3.1-8b-instant"
    elif tier == "synthesis":
        groq_model = "llama-3.1-70b-versatile"
        openai_model = "gpt-4o"
    
    # 1. Gemini (Primary for Benchmark)
    if getattr(settings, "gemini_api_key", None):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            providers.append(ChatGoogleGenerativeAI(
                api_key=settings.gemini_api_key,
                model=getattr(settings, "google_model", "gemini-2.0-flash"),
                max_retries=0,
                **kwargs
            ))
        except ImportError:
            pass

    # 2. Groq (Secondary)
    if getattr(settings, "groq_api_key", None):
        try:
            from langchain_groq import ChatGroq
            providers.append(ChatGroq(
                api_key=settings.groq_api_key,
                model_name=groq_model,
                max_retries=0, # Let LangChain fallback handle retries immediately
                **kwargs
            ))
        except ImportError:
            pass

    # 3. OpenAI (Tertiary)
    if getattr(settings, "openai_api_key", None):
        try:
            from langchain_openai import ChatOpenAI
            providers.append(ChatOpenAI(
                api_key=settings.openai_api_key,
                model_name=openai_model,
                max_retries=0,
                **kwargs
            ))
        except ImportError:
            pass

    if not providers:
        raise ConfigurationError("No valid LLM providers configured with API keys.")
        
    primary_llm = providers[0]
    if len(providers) > 1:
        # Import exception classes for safe fallback routing
        exceptions = []
        try:
            import groq
            exceptions.append(groq.RateLimitError)
            exceptions.append(groq.InternalServerError)
        except ImportError:
            pass
        try:
            import openai
            exceptions.append(openai.RateLimitError)
            exceptions.append(openai.InternalServerError)
        except ImportError:
            pass
        try:
            from google.api_core.exceptions import ResourceExhausted, InternalServerError
            exceptions.append(ResourceExhausted)
            exceptions.append(InternalServerError)
        except ImportError:
            pass
            
        if not exceptions:
            exceptions = (Exception,) # Fallback to base Exception if clients missing
            
        return primary_llm.with_fallbacks(
            providers[1:],
            exceptions_to_handle=tuple(exceptions)
        )
    return primary_llm


