"""Pipeline coordinater for the restaurant recommendation system.

Sequences: validate -> filter -> (empty check) -> prompt -> LLM -> parse -> format.

Architecture reference: §4.2 (Application Layer (Orchestrator))
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from src.config import settings
from src.data.models import Budget, UserPreferences
from src.data.store import get_restaurants
from src.filters.filter_engine import apply_filters, build_candidates
from src.llm.client import get_llm_client
from src.llm.parser import ResponseParser, merge_with_restaurants, FORMAT_CORRECTION_HINT
from src.llm.prompt_builder import build_messages
from src.presentation.formatter import DisplayRecommendation, format_recommendations
from src.validators import validate_preferences

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecommendationResponse:
    """Result returned by the orchestrator recommendation pipeline."""

    summary: str
    recommendations: list[DisplayRecommendation]
    provider: str
    model: str
    latency_ms: float
    relaxed: bool
    relaxed_filters: list[str]


def recommend(
    location: str,
    budget: str | Budget,
    cuisine: str | list[str],
    min_rating: float | str | int,
    additional_preferences: str | None = None,
    top_k: int | None = None,
) -> RecommendationResponse:
    """Coordinate the end-to-end recommendation pipeline.

    Args:
        location: Target city/area name.
        budget: Budget tier ("low", "medium", "high").
        cuisine: Cuisine preference.
        min_rating: Minimum rating value.
        additional_preferences: Optional free-text preferences.
        top_k: Optional number of recommendations to request.

    Returns:
        A structured ``RecommendationResponse``.
    """
    t_start = time.time()

    # 1. Validate preferences
    preferences = validate_preferences(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional_preferences,
    )

    # 2. Load dataset
    restaurants = get_restaurants()

    # 3. Filter candidates
    filter_result = apply_filters(restaurants, preferences)

    # 4. Handle empty candidates
    if not filter_result.candidates:
        return RecommendationResponse(
            summary=(
                "No restaurants matching your criteria were found, even after relaxation. "
                "Try broadening your location or cuisine preferences."
            ),
            recommendations=[],
            provider=settings.llm_provider,
            model=settings.llm_model,
            latency_ms=0.0,
            relaxed=filter_result.relaxed,
            relaxed_filters=filter_result.relaxed_filters or [],
        )

    # 5. Build candidates (sort and cap)
    candidates = build_candidates(filter_result.candidates)

    # 6. Build prompt
    messages = build_messages(preferences, candidates, top_k=top_k)

    # 7. LLM Client
    client = get_llm_client()
    parser = ResponseParser(candidates, top_k=top_k)

    raw_response = ""
    parsed_result = None
    t0 = time.time()

    try:
        # 8. First LLM generation attempt
        raw_response = client.generate(messages)
        parsed_result = parser.parse_safe(raw_response)

        # 9. Format correction retry on parse failure
        if parsed_result is None:
            logger.warning("First LLM response failed to parse. Retrying with format hint...")
            retry_messages = list(messages)
            retry_messages.extend([
                {"role": "assistant", "content": raw_response},
                {"role": "user", "content": FORMAT_CORRECTION_HINT},
            ])
            raw_response = client.generate(retry_messages)
            parsed_result = parser.parse_safe(raw_response)

    except Exception as exc:
        logger.error("Error during LLM generation: %s", exc)

    latency_ms = (time.time() - t0) * 1000

    # 10. Fallback on total failure
    if parsed_result is None:
        logger.warning("LLM generation/parsing failed completely. Falling back to rating-based sorting.")
        parsed_result = parser.fallback_recommendations()

    # 11. Merge with full restaurant details
    domain_recs = merge_with_restaurants(parsed_result, candidates)

    # 12. Format results for display
    display_recs = format_recommendations(domain_recs)

    return RecommendationResponse(
        summary=parsed_result.summary,
        recommendations=display_recs,
        provider=settings.llm_provider,
        model=settings.llm_model,
        latency_ms=latency_ms,
        relaxed=filter_result.relaxed,
        relaxed_filters=filter_result.relaxed_filters or [],
    )
