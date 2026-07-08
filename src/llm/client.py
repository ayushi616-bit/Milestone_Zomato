"""LLM client wrapper for the recommendation engine.

Provides a thin wrapper around the OpenAI chat completions API with:
- Configurable model, temperature, and timeout
- Retry logic on transient failures
- Structured message passing

Architecture reference: §8.2 (LLM Integration Architecture)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM call fails after all retries."""


class LLMClient:
    """Wrapper around the OpenAI and Groq chat completions API.

    Args:
        api_key: LLM API key. Defaults to ``settings.groq_api_key`` or ``settings.openai_api_key``.
        model: Model name. Defaults to ``settings.llm_model``.
        temperature: Sampling temperature. Defaults to ``settings.llm_temperature``.
        timeout: Request timeout in seconds. Defaults to ``settings.llm_timeout_seconds``.
        max_retries: Number of retries on failure. Defaults to ``settings.llm_max_retries``.
        provider: Provider name ("openai" or "groq"). Defaults to ``settings.llm_provider``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        provider: str | None = None,
    ) -> None:
        self._provider = (provider or settings.llm_provider).lower().strip()
        
        if self._provider == "groq":
            self._api_key = api_key or settings.groq_api_key
        else:
            self._api_key = api_key or settings.openai_api_key
            
        self._model = model or settings.llm_model
        self._temperature = temperature if temperature is not None else settings.llm_temperature
        self._timeout = timeout or settings.llm_timeout_seconds
        self._max_retries = max_retries if max_retries is not None else settings.llm_max_retries
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """Lazy-initialize the client."""
        if self._client is None:
            if not self._api_key:
                if self._provider == "groq":
                    raise LLMError(
                        "No Groq API key configured. Set GROQ_API_KEY in your .env file."
                    )
                else:
                    raise LLMError(
                        "No OpenAI API key configured. Set OPENAI_API_KEY in your .env file."
                    )
            
            if self._provider == "groq":
                self._client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=self._api_key,
                    timeout=self._timeout,
                )
            else:
                self._client = OpenAI(
                    api_key=self._api_key,
                    timeout=self._timeout,
                )
        return self._client

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Send messages to the LLM and return the response text.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` message dicts.

        Returns:
            The assistant's response text.

        Raises:
            LLMError: If the API call fails after all retries.
        """
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 2):  # +1 for the initial attempt
            try:
                t0 = time.time()
                response = self.client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=self._temperature,
                )
                latency_ms = (time.time() - t0) * 1000
                logger.info(
                    "LLM call succeeded (attempt %d, provider=%s, model=%s, latency=%.0fms).",
                    attempt, self._provider, self._model, latency_ms,
                )

                # Extract content
                content = response.choices[0].message.content
                if content is None:
                    raise LLMError("LLM returned empty content.")
                return content.strip()

            except LLMError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s",
                    attempt, self._max_retries + 1, exc,
                )
                if attempt <= self._max_retries:
                    time.sleep(0.5 * attempt)  # simple backoff

        raise LLMError(
            f"LLM call failed after {self._max_retries + 1} attempts: {last_error}"
        ) from last_error


# Module-level default client (lazy — only initialized on first use)
_default_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Return the default LLM client singleton."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client

