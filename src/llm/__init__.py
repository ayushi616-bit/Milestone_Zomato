"""LLM recommendation engine layer."""

from src.llm.client import LLMClient, LLMError, get_llm_client
from src.llm.parser import (
    FORMAT_CORRECTION_HINT,
    LLMParsedResult,
    ParsedRecommendation,
    ResponseParser,
    merge_with_restaurants,
)
from src.llm.prompt_builder import (
    LLM_OUTPUT_SCHEMA,
    build_messages,
    build_system_prompt,
    build_user_prompt,
)

__all__ = [
    "FORMAT_CORRECTION_HINT",
    "LLMClient",
    "LLMError",
    "LLM_OUTPUT_SCHEMA",
    "LLMParsedResult",
    "ParsedRecommendation",
    "ResponseParser",
    "build_messages",
    "build_system_prompt",
    "build_user_prompt",
    "get_llm_client",
    "merge_with_restaurants",
]
