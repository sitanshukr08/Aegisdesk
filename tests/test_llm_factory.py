import pytest

from app.config.settings import settings
from src.aegisdesk.core.llm_factory import ConfigurationError, get_llm


def test_llm_factory_groq_success(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "fake_key")
    llm = get_llm()
    assert llm.__class__.__name__ == "ChatGroq"

def test_llm_factory_openai_success(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "fake_key")
    llm = get_llm()
    assert llm.__class__.__name__ == "ChatOpenAI"

def test_llm_factory_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "")
    with pytest.raises(ConfigurationError, match="GROQ_API_KEY is missing"):
        get_llm()

def test_llm_factory_unsupported_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "huggingface_local")
    with pytest.raises(ConfigurationError, match="Unsupported LLM_PROVIDER"):
        get_llm()
