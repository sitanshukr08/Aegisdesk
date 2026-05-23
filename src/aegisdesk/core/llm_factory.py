from langchain_core.language_models.chat_models import BaseChatModel
from app.config.settings import settings
from src.aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.llm_factory")

class ConfigurationError(Exception):
    """Raised when an LLM provider is misconfigured or missing credentials."""
    pass

def get_llm(temperature: float = 0.0, response_format: dict = None) -> BaseChatModel:
    """
    Factory function that returns the configured LLM provider.
    Ensures vendor agnosticism across the enterprise.
    """
    provider = settings.llm_provider.lower().strip()
    
    kwargs = {"temperature": temperature}
    if response_format:
        kwargs["model_kwargs"] = {"response_format": response_format}
        
    try:
        if provider == "groq":
            from langchain_groq import ChatGroq
            if not settings.groq_api_key:
                raise ConfigurationError("GROQ_API_KEY is missing but provider is set to 'groq'")
            logger.debug(f"Initializing Groq Model: {settings.llm_model}")
            return ChatGroq(
                api_key=settings.groq_api_key,
                model_name=settings.llm_model,
                max_retries=1,
                **kwargs
            )
            
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            openai_key = getattr(settings, "openai_api_key", None)
            if not openai_key:
                raise ConfigurationError("OPENAI_API_KEY is missing but provider is set to 'openai'")
            logger.debug(f"Initializing OpenAI Model: {settings.llm_model}")
            return ChatOpenAI(
                api_key=openai_key,
                model_name=settings.llm_model,
                **kwargs
            )
            
        else:
            raise ConfigurationError(f"Unsupported LLM_PROVIDER: {provider}")
            
    except ImportError as e:
        logger.error(f"Missing dependency for provider '{provider}': {e}")
        raise ConfigurationError(f"Please install the required package for provider '{provider}'")
