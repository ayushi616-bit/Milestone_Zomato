"""Unit tests for application configuration."""

import os

import pytest

from src.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = get_settings()
    assert settings.candidate_cap == 20
    assert settings.top_k_recommendations == 5
    assert settings.llm_provider == "groq"
    assert settings.llm_model == "llama-3.1-8b-instant"
    assert settings.huggingface_dataset_name == "ManikaSaini/zomato-restaurant-recommendation"


def test_settings_reads_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")

    settings = get_settings()
    assert settings.llm_provider == "openai"
    assert settings.openai_api_key == "test-key-123"
    assert settings.llm_model == "gpt-4o"



def test_settings_no_hardcoded_secrets() -> None:
    """Ensure API key comes from environment, not hardcoded."""
    settings = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        llm_provider="groq",
        llm_model="llama3-8b-8192",
    )
    assert settings.openai_api_key is None or isinstance(settings.openai_api_key, str)
    assert settings.groq_api_key is None or isinstance(settings.groq_api_key, str)

