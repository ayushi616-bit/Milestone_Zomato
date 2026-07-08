"""Parse and validate LLM responses for the recommendation engine.

Responsibilities:
- Parse raw LLM text as JSON
- Validate restaurant IDs against the candidate set (hallucination rejection)
- Retry with format correction hint on malformed JSON
- Fallback to rating-sorted top-K when LLM fails entirely

Architecture reference: §8.3 (Grounding and Hallucination Mitigation)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.config import settings
from src.data.models import Recommendation, Restaurant

logger = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class LLMParsedResult:
    """Parsed LLM response after validation."""

    summary: str
    recommendations: list[ParsedRecommendation]
    discarded_ids: list[str] = field(default_factory=list)


@dataclass
class ParsedRecommendation:
    """A single parsed recommendation from the LLM output."""

    restaurant_id: str
    rank: int
    explanation: str


# ── Parser ────────────────────────────────────────────────────────────────────


class ResponseParser:
    """Parse LLM responses and validate against the candidate set.

    Args:
        candidates: The list of candidate restaurants sent to the LLM.
        top_k: Maximum number of recommendations to return.
    """

    def __init__(
        self,
        candidates: list[Restaurant],
        top_k: int | None = None,
    ) -> None:
        self._candidates = candidates
        self._candidate_ids = {r.id for r in candidates}
        self._candidate_map = {r.id: r for r in candidates}
        self._top_k = top_k or settings.top_k_recommendations

    def parse(self, raw_text: str) -> LLMParsedResult:
        """Parse raw LLM response text into a validated result.

        Args:
            raw_text: The raw text output from the LLM.

        Returns:
            A validated ``LLMParsedResult``.

        Raises:
            ValueError: If the JSON cannot be parsed even after cleanup.
        """
        data = self._extract_json(raw_text)
        return self._validate(data)

    def parse_safe(self, raw_text: str) -> LLMParsedResult | None:
        """Like ``parse()`` but returns ``None`` on failure instead of raising.

        Useful for triggering retry logic in the caller.
        """
        try:
            return self.parse(raw_text)
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Failed to parse LLM response: %s", exc)
            return None

    def fallback_recommendations(self) -> LLMParsedResult:
        """Generate fallback recommendations sorted by rating (no LLM).

        Used when the LLM is unavailable. Returns top-K candidates sorted
        by rating descending, with generic explanations.
        """
        sorted_candidates = sorted(
            self._candidates, key=lambda r: r.rating, reverse=True,
        )[: self._top_k]

        recs: list[ParsedRecommendation] = []
        for rank, restaurant in enumerate(sorted_candidates, 1):
            cuisines = ", ".join(restaurant.cuisines[:3])
            recs.append(
                ParsedRecommendation(
                    restaurant_id=restaurant.id,
                    rank=rank,
                    explanation=(
                        f"Highly rated {cuisines} restaurant in {restaurant.location} "
                        f"with a {restaurant.rating:.1f}★ rating."
                    ),
                )
            )

        return LLMParsedResult(
            summary=(
                f"Here are the top {len(recs)} restaurants based on ratings "
                f"(AI explanations unavailable)."
            ),
            recommendations=recs,
        )

    # ── Internal methods ──────────────────────────────────────────────────

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        """Extract JSON from the LLM response text.

        Handles cases where the LLM wraps JSON in markdown code blocks.
        """
        text = raw_text.strip()

        # Try to extract from markdown code blocks
        code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Cannot parse LLM response as JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}.")

        return data

    def _validate(self, data: dict[str, Any]) -> LLMParsedResult:
        """Validate parsed JSON against the candidate set."""
        summary = str(data.get("summary", ""))
        raw_recs = data.get("recommendations", [])

        if not isinstance(raw_recs, list):
            raise ValueError("'recommendations' must be a list.")

        valid_ids = self._candidate_ids
        recommendations: list[ParsedRecommendation] = []
        discarded: list[str] = []

        for item in raw_recs:
            if not isinstance(item, dict):
                logger.warning("Skipping non-dict recommendation item: %s", item)
                continue

            rid = item.get("restaurant_id", "")
            rank = item.get("rank", 0)
            explanation = str(item.get("explanation", ""))

            # Hallucination check: ID must be in the candidate set
            if rid not in valid_ids:
                discarded.append(rid)
                logger.info("Discarded hallucinated restaurant ID: %s", rid)
                continue

            # Validate rank is a positive integer
            try:
                rank_int = int(rank)
                if rank_int < 1:
                    rank_int = len(recommendations) + 1
            except (TypeError, ValueError):
                rank_int = len(recommendations) + 1

            recommendations.append(
                ParsedRecommendation(
                    restaurant_id=rid,
                    rank=rank_int,
                    explanation=explanation,
                )
            )

        # Sort by rank and cap at top_k
        recommendations.sort(key=lambda r: r.rank)
        recommendations = recommendations[: self._top_k]

        if discarded:
            logger.info(
                "Discarded %d hallucinated IDs out of %d total recommendations.",
                len(discarded), len(raw_recs),
            )

        return LLMParsedResult(
            summary=summary,
            recommendations=recommendations,
            discarded_ids=discarded,
        )


# ── Convenience: merge parsed results with Restaurant objects ─────────────────


def merge_with_restaurants(
    parsed: LLMParsedResult,
    candidates: list[Restaurant],
) -> list[Recommendation]:
    """Merge parsed LLM output with candidate restaurant objects.

    Returns a list of ``Recommendation`` domain objects, dropping any
    parsed recommendations whose restaurant ID is no longer found.
    """
    restaurant_map = {r.id: r for r in candidates}
    results: list[Recommendation] = []

    for pr in parsed.recommendations:
        restaurant = restaurant_map.get(pr.restaurant_id)
        if restaurant is None:
            continue
        results.append(
            Recommendation(
                restaurant=restaurant,
                rank=pr.rank,
                explanation=pr.explanation,
            )
        )

    return results


# ── Retry hint for malformed JSON ────────────────────────────────────────────

FORMAT_CORRECTION_HINT = (
    "Your previous response was not valid JSON. Please output ONLY valid JSON "
    "matching this schema: {\"summary\": \"...\", \"recommendations\": [{\"restaurant_id\": \"...\", "
    "\"rank\": 1, \"explanation\": \"...\"}]}. No markdown, no commentary outside the JSON."
)
