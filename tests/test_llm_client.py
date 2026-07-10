"""Unit tests for the LLM client (src.llm.client)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.llm.client import LLMClient, LLMError, get_llm_client


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Build a mock OpenAI ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = '{"summary": "Test.", "recommendations": []}'
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def client() -> LLMClient:
    """An LLMClient with a test API key."""
    return LLMClient(
        api_key="test-key-123",
        model="llama-3.1-8b-instant",
        temperature=0.3,
        timeout=10,
        max_retries=1,
        provider="groq",
    )


# ── Client initialization ────────────────────────────────────────────────────


class TestClientInit:
    def test_unsupported_provider_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.config
        import src.llm.client
        new_settings = src.config.Settings(
            groq_api_key="test-key-123",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
        )
        monkeypatch.setattr(src.config, "settings", new_settings)
        monkeypatch.setattr(src.llm.client, "settings", new_settings)
        with pytest.raises(LLMError, match="Unsupported provider"):
            _ = LLMClient(api_key=None, provider="openai")

    def test_no_api_key_raises_groq(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.config
        import src.llm.client
        new_settings = src.config.Settings(
            groq_api_key=None,
            llm_provider="groq",
            llm_model="llama-3.1-8b-instant",
        )
        monkeypatch.setattr(src.config, "settings", new_settings)
        monkeypatch.setattr(src.llm.client, "settings", new_settings)
        client = LLMClient(api_key=None, provider="groq")
        with pytest.raises(LLMError, match="No Groq API key"):
            _ = client.client

    def test_lazy_init(self) -> None:
        client = LLMClient(api_key="test-key", provider="groq")
        assert client._client is None
        # Accessing .client triggers init
        _ = client.client
        assert client._client is not None

    def test_custom_model(self) -> None:
        client = LLMClient(api_key="key", model="llama-3.1-8b-instant", provider="groq")
        assert client._model == "llama-3.1-8b-instant"

    def test_custom_temperature(self) -> None:
        client = LLMClient(api_key="key", temperature=0.5, provider="groq")
        assert client._temperature == 0.5






# ── Generate ──────────────────────────────────────────────────────────────────


class TestGenerate:
    def test_successful_response(
        self, client: LLMClient, mock_openai_response: MagicMock,
    ) -> None:
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_openai_response
        client._client = mock_openai
        result = client.generate([{"role": "user", "content": "Hello"}])

        assert isinstance(result, str)
        assert "summary" in result

    def test_empty_content_raises(
        self, client: LLMClient,
    ) -> None:
        choice = MagicMock()
        choice.message.content = None
        response = MagicMock()
        response.choices = [choice]

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = response
        client._client = mock_openai
        with pytest.raises(LLMError, match="empty content"):
            client.generate([{"role": "user", "content": "Hello"}])

    def test_retry_on_failure(
        self, client: LLMClient, mock_openai_response: MagicMock,
    ) -> None:
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = [
            Exception("Transient error"),
            mock_openai_response,
        ]
        client._client = mock_openai
        result = client.generate([{"role": "user", "content": "Hello"}])

        assert isinstance(result, str)
        assert mock_openai.chat.completions.create.call_count == 2

    def test_exhausted_retries_raises(
        self, client: LLMClient,
    ) -> None:
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = Exception("Always fails")
        client._client = mock_openai
        with pytest.raises(LLMError, match="failed after"):
            client.generate([{"role": "user", "content": "Hello"}])

    def test_llm_error_not_retried(
        self, client: LLMClient,
    ) -> None:
        """LLMError (e.g. empty content) should not trigger retry."""
        choice = MagicMock()
        choice.message.content = None
        response = MagicMock()
        response.choices = [choice]

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = response
        client._client = mock_openai
        with pytest.raises(LLMError):
            client.generate([{"role": "user", "content": "Hello"}])
        # Should only be called once — LLMError is not retried
        assert mock_openai.chat.completions.create.call_count == 1


# ── Module-level singleton ────────────────────────────────────────────────────


class TestGetLLMClient:
    def test_returns_client(self) -> None:
        import src.llm.client as llm_module
        llm_module._default_client = None  # Reset
        client = get_llm_client()
        assert isinstance(client, LLMClient)

    def test_singleton(self) -> None:
        import src.llm.client as llm_module
        llm_module._default_client = None  # Reset
        c1 = get_llm_client()
        c2 = get_llm_client()
        assert c1 is c2
        llm_module._default_client = None  # Clean up
