"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime settings and constants."""

    # LLM provider
    groq_api_key: str | None
    llm_provider: str  # "openai" or "groq"
    llm_model: str

    # Pipeline constants
    candidate_cap: int = 20
    top_k_recommendations: int = 5

    # LLM behavior
    llm_temperature: float = 0.3
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 1

    # Input limits
    max_additional_preferences_chars: int = 500

    # Dataset
    huggingface_dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"

    # Cost bucket thresholds (INR for two)
    cost_low_max: int = 500
    cost_medium_max: int = 1500


def get_settings() -> Settings:
    """Build settings from environment variables with sensible defaults."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()
    
    # Sensible defaults based on provider
    default_model = "llama-3.1-8b-instant" if provider == "groq" else "gpt-4o-mini"
    
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        llm_provider=provider,
        llm_model=os.getenv("LLM_MODEL", default_model),
    )


# Module-level singleton for convenience
settings = get_settings()

