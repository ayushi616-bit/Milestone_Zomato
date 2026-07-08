"""Deterministic filter engine and candidate builder.

Filters restaurants by user preferences and produces a bounded candidate list
for the LLM.  When strict filtering yields zero results, progressive relaxation
drops filters in order: cuisine → min_rating → budget.

Architecture reference: §7 (Integration and Filtering Layer)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from src.config import settings
from src.data.models import Budget, CostBucket, Restaurant, UserPreferences

logger = logging.getLogger(__name__)


# ── Individual filters ────────────────────────────────────────────────────────


def filter_by_location(
    restaurants: list[Restaurant],
    location: str,
) -> list[Restaurant]:
    """Keep only restaurants whose normalized location matches.

    The comparison is case-insensitive and uses substring matching
    so that area-level queries (e.g. "koramangala") match
    "koramangala 5th block" as well.
    """
    loc = location.lower().strip()
    return [r for r in restaurants if loc in r.location.lower()]


def filter_by_cuisine(
    restaurants: list[Restaurant],
    cuisines: list[str],
) -> list[Restaurant]:
    """Keep restaurants whose cuisine list contains any of the requested cuisines.

    Matching is case-insensitive and partial (e.g. "italian" matches "italian").
    """
    wanted = {c.lower().strip() for c in cuisines if c.strip()}
    if not wanted:
        return restaurants
    return [
        r for r in restaurants
        if any(c.lower() in r_cuisine.lower() for c in wanted for r_cuisine in r.cuisines)
    ]


def filter_by_min_rating(
    restaurants: list[Restaurant],
    min_rating: float,
) -> list[Restaurant]:
    """Keep restaurants with rating >= min_rating."""
    if min_rating <= 0.0:
        return restaurants
    return [r for r in restaurants if r.rating >= min_rating]


def filter_by_budget(
    restaurants: list[Restaurant],
    budget: Budget,
) -> list[Restaurant]:
    """Keep restaurants whose cost bucket matches the user's budget.

    Restaurants with ``CostBucket.UNKNOWN`` are included when the user
    selects ``Budget.LOW`` or ``Budget.MEDIUM`` to avoid over-filtering
    (they might still be relevant).
    """
    target = CostBucket(budget.value)
    return [
        r for r in restaurants
        if r.cost_bucket == target
        or (r.cost_bucket == CostBucket.UNKNOWN and budget in (Budget.LOW, Budget.MEDIUM))
    ]


# ── Filter engine ─────────────────────────────────────────────────────────────


@dataclass
class FilterResult:
    """Result of a filter pass, including logging metadata."""

    candidates: list[Restaurant]
    total_before: int
    stages: dict[str, int]
    relaxed: bool = False
    relaxed_filters: list[str] | None = None


class FilterEngine:
    """Chains location → cuisine → min_rating → budget filters in sequence.

    If strict filtering returns zero results, applies progressive relaxation:
    1. Drop cuisine filter
    2. Lower min_rating to 0
    3. Drop budget filter
    """

    def apply(
        self,
        restaurants: list[Restaurant],
        preferences: UserPreferences,
    ) -> FilterResult:
        """Run the full filter pipeline with optional relaxation."""
        total = len(restaurants)
        stages: dict[str, int] = {"initial": total}

        # ── Strict pass ──────────────────────────────────────────────────
        result = filter_by_location(restaurants, preferences.location)
        stages["after_location"] = len(result)

        cuisine_filtered = filter_by_cuisine(result, preferences.cuisines_list())
        stages["after_cuisine"] = len(cuisine_filtered)

        rating_filtered = filter_by_min_rating(cuisine_filtered, preferences.min_rating)
        stages["after_min_rating"] = len(rating_filtered)

        budget_filtered = filter_by_budget(rating_filtered, preferences.budget)
        stages["after_budget"] = len(budget_filtered)

        if budget_filtered:
            logger.info(
                "Filter pipeline: %d → %d candidates (strict). Stages: %s",
                total, len(budget_filtered), stages,
            )
            return FilterResult(
                candidates=budget_filtered,
                total_before=total,
                stages=stages,
            )

        # ── Progressive relaxation ───────────────────────────────────────
        logger.info("Zero strict results — attempting progressive relaxation.")
        relaxed_filters: list[str] = []

        # Step 1: drop cuisine
        result = filter_by_location(restaurants, preferences.location)
        rating_only = filter_by_min_rating(result, preferences.min_rating)
        budget_only = filter_by_budget(rating_only, preferences.budget)
        if budget_only:
            relaxed_filters.append("cuisine")
            stages["relaxed_after_cuisine_drop"] = len(budget_only)
            logger.info(
                "Relaxation (dropped cuisine): %d candidates.", len(budget_only),
            )
            return FilterResult(
                candidates=budget_only,
                total_before=total,
                stages=stages,
                relaxed=True,
                relaxed_filters=relaxed_filters,
            )

        # Step 2: also drop min_rating
        result = filter_by_location(restaurants, preferences.location)
        budget_only = filter_by_budget(result, preferences.budget)
        if budget_only:
            relaxed_filters.extend(["cuisine", "min_rating"])
            stages["relaxed_after_rating_drop"] = len(budget_only)
            logger.info(
                "Relaxation (dropped cuisine + min_rating): %d candidates.",
                len(budget_only),
            )
            return FilterResult(
                candidates=budget_only,
                total_before=total,
                stages=stages,
                relaxed=True,
                relaxed_filters=relaxed_filters,
            )

        # Step 3: also drop budget
        result = filter_by_location(restaurants, preferences.location)
        if result:
            relaxed_filters.extend(["cuisine", "min_rating", "budget"])
            stages["relaxed_after_budget_drop"] = len(result)
            logger.info(
                "Relaxation (dropped cuisine + min_rating + budget): %d candidates.",
                len(result),
            )
            return FilterResult(
                candidates=result,
                total_before=total,
                stages=stages,
                relaxed=True,
                relaxed_filters=relaxed_filters,
            )

        # Nothing matched at all (location has no restaurants)
        logger.info("No candidates after full relaxation for location=%r.", preferences.location)
        return FilterResult(
            candidates=[],
            total_before=total,
            stages=stages,
            relaxed=True,
            relaxed_filters=["cuisine", "min_rating", "budget"],
        )


# ── Candidate builder ─────────────────────────────────────────────────────────


class CandidateBuilder:
    """Sort, cap, and serialize filtered restaurants into LLM-ready candidates."""

    def __init__(self, cap: int | None = None) -> None:
        self.cap = cap or settings.candidate_cap

    def build(self, restaurants: list[Restaurant]) -> list[Restaurant]:
        """Sort by rating descending and cap at N candidates."""
        sorted_restaurants = sorted(restaurants, key=lambda r: r.rating, reverse=True)
        return sorted_restaurants[: self.cap]

    def serialize(self, candidates: list[Restaurant]) -> list[dict[str, Any]]:
        """Convert candidates to compact JSON-serializable dicts."""
        return [
            {
                "id": r.id,
                "name": r.name,
                "cuisines": r.cuisines,
                "rating": r.rating,
                "cost_bucket": r.cost_bucket.value,
                "cost_for_two": r.cost_for_two,
                "location": r.location,
            }
            for r in candidates
        ]

    def to_json(self, candidates: list[Restaurant]) -> str:
        """Serialize candidates to a JSON string."""
        return json.dumps(self.serialize(candidates), ensure_ascii=False, indent=2)


# ── Convenience functions ─────────────────────────────────────────────────────


_engine = FilterEngine()
_builder = CandidateBuilder()


def apply_filters(
    restaurants: list[Restaurant],
    preferences: UserPreferences,
) -> FilterResult:
    """Apply the filter engine to a list of restaurants.

    Convenience wrapper around ``FilterEngine.apply()``.
    """
    return _engine.apply(restaurants, preferences)


def build_candidates(
    restaurants: list[Restaurant],
) -> list[Restaurant]:
    """Sort and cap filtered restaurants into candidates.

    Convenience wrapper around ``CandidateBuilder.build()``.
    """
    return _builder.build(restaurants)
