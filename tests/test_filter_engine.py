"""Unit tests for the filter engine (src.filters.filter_engine)."""

from __future__ import annotations

import json

import pytest

from src.data.models import Budget, CostBucket, Restaurant, UserPreferences
from src.filters.filter_engine import (
    CandidateBuilder,
    FilterEngine,
    apply_filters,
    build_candidates,
    filter_by_budget,
    filter_by_cuisine,
    filter_by_location,
    filter_by_min_rating,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def restaurants() -> list[Restaurant]:
    """Diverse set of restaurants for filter testing."""
    return [
        Restaurant(
            id="r_01", name="Italian Bistro", location="indiranagar",
            cuisines=["italian", "continental"], cost_for_two=800,
            cost_bucket=CostBucket.MEDIUM, rating=4.5, metadata={},
        ),
        Restaurant(
            id="r_02", name="Chinese Wok", location="koramangala 5th block",
            cuisines=["chinese", "thai"], cost_for_two=600,
            cost_bucket=CostBucket.MEDIUM, rating=4.2, metadata={},
        ),
        Restaurant(
            id="r_03", name="Budget Curry", location="indiranagar",
            cuisines=["north indian", "biryani"], cost_for_two=300,
            cost_bucket=CostBucket.LOW, rating=3.8, metadata={},
        ),
        Restaurant(
            id="r_04", name="Fancy Dining", location="mg road",
            cuisines=["italian", "french"], cost_for_two=2500,
            cost_bucket=CostBucket.HIGH, rating=4.8, metadata={},
        ),
        Restaurant(
            id="r_05", name="Street Food", location="indiranagar",
            cuisines=["indian", "fast food"], cost_for_two=200,
            cost_bucket=CostBucket.LOW, rating=4.0, metadata={},
        ),
        Restaurant(
            id="r_06", name="Unknown Cost Cafe", location="indiranagar",
            cuisines=["cafe", "continental"], cost_for_two=None,
            cost_bucket=CostBucket.UNKNOWN, rating=4.1, metadata={},
        ),
    ]


def _prefs(**overrides) -> UserPreferences:
    """Build test preferences with sensible defaults."""
    defaults = dict(
        location="indiranagar", budget=Budget.MEDIUM,
        cuisine="italian", min_rating=3.5,
    )
    defaults.update(overrides)
    return UserPreferences(**defaults)


# ── Individual filter tests ───────────────────────────────────────────────────


class TestFilterByLocation:
    def test_exact_match(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_location(restaurants, "indiranagar")
        names = {r.name for r in result}
        assert "Italian Bistro" in names
        assert "Budget Curry" in names
        assert "Chinese Wok" not in names

    def test_partial_match(self, restaurants: list[Restaurant]) -> None:
        """'koramangala' should match 'koramangala 5th block'."""
        result = filter_by_location(restaurants, "koramangala")
        assert len(result) == 1
        assert result[0].name == "Chinese Wok"

    def test_case_insensitive(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_location(restaurants, "INDIRANAGAR")
        assert len(result) >= 1

    def test_no_match(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_location(restaurants, "whitefield")
        assert len(result) == 0


class TestFilterByCuisine:
    def test_single_cuisine(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_cuisine(restaurants, ["italian"])
        names = {r.name for r in result}
        assert "Italian Bistro" in names
        assert "Fancy Dining" in names  # has italian

    def test_multiple_cuisines(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_cuisine(restaurants, ["chinese", "north indian"])
        names = {r.name for r in result}
        assert "Chinese Wok" in names
        assert "Budget Curry" in names

    def test_partial_match_italian(self, restaurants: list[Restaurant]) -> None:
        """'Italian' should match restaurants with 'italian' in their cuisine list."""
        result = filter_by_cuisine(restaurants, ["Italian"])
        assert any(r.name == "Italian Bistro" for r in result)

    def test_empty_cuisine_returns_all(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_cuisine(restaurants, [])
        assert len(result) == len(restaurants)

    def test_no_match(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_cuisine(restaurants, ["japanese"])
        assert len(result) == 0


class TestFilterByMinRating:
    def test_filters_below_threshold(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_min_rating(restaurants, 4.0)
        for r in result:
            assert r.rating >= 4.0

    def test_zero_returns_all(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_min_rating(restaurants, 0.0)
        assert len(result) == len(restaurants)

    def test_high_threshold(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_min_rating(restaurants, 4.7)
        assert len(result) == 1
        assert result[0].name == "Fancy Dining"


class TestFilterByBudget:
    def test_medium_budget(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_budget(restaurants, Budget.MEDIUM)
        for r in result:
            assert r.cost_bucket in (CostBucket.MEDIUM, CostBucket.UNKNOWN)

    def test_low_budget_includes_unknown(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_budget(restaurants, Budget.LOW)
        buckets = {r.cost_bucket for r in result}
        assert CostBucket.LOW in buckets
        # UNKNOWN is included for LOW/MEDIUM
        assert CostBucket.UNKNOWN in buckets

    def test_high_budget_excludes_low(self, restaurants: list[Restaurant]) -> None:
        result = filter_by_budget(restaurants, Budget.HIGH)
        for r in result:
            assert r.cost_bucket == CostBucket.HIGH


# ── Filter engine (integration) ───────────────────────────────────────────────


class TestFilterEngine:
    def test_strict_pass(self, restaurants: list[Restaurant]) -> None:
        engine = FilterEngine()
        prefs = _prefs(location="indiranagar", budget=Budget.MEDIUM, cuisine="italian", min_rating=3.5)
        result = engine.apply(restaurants, prefs)
        assert len(result.candidates) >= 1
        assert not result.relaxed
        assert result.stages["initial"] == 6

    def test_relaxation_drops_cuisine(self, restaurants: list[Restaurant]) -> None:
        """When no italian+medium+indiranagar match, cuisine is dropped."""
        engine = FilterEngine()
        prefs = _prefs(location="indiranagar", budget=Budget.LOW, cuisine="japanese", min_rating=3.5)
        result = engine.apply(restaurants, prefs)
        # Should find results after dropping cuisine
        assert len(result.candidates) >= 1
        assert result.relaxed
        assert "cuisine" in (result.relaxed_filters or [])

    def test_full_relaxation_location_only(self, restaurants: list[Restaurant]) -> None:
        """When only location matches, all other filters are dropped."""
        engine = FilterEngine()
        prefs = _prefs(
            location="indiranagar", budget=Budget.HIGH,
            cuisine="japanese", min_rating=4.9,
        )
        result = engine.apply(restaurants, prefs)
        # indiranagar has no high-budget japanese with 4.9 rating
        # After full relaxation, we get all indiranagar restaurants
        assert result.relaxed
        assert len(result.candidates) >= 1  # at least location matches

    def test_zero_results_unknown_location(self, restaurants: list[Restaurant]) -> None:
        """When location has no matches, result is empty even after relaxation."""
        engine = FilterEngine()
        prefs = _prefs(location="whitefield", budget=Budget.MEDIUM, cuisine="italian", min_rating=3.0)
        result = engine.apply(restaurants, prefs)
        assert len(result.candidates) == 0
        assert result.relaxed

    def test_stages_logged(self, restaurants: list[Restaurant]) -> None:
        engine = FilterEngine()
        prefs = _prefs()
        result = engine.apply(restaurants, prefs)
        assert "initial" in result.stages
        assert "after_location" in result.stages


# ── Candidate builder ─────────────────────────────────────────────────────────


class TestCandidateBuilder:
    def test_sorted_by_rating_desc(self, restaurants: list[Restaurant]) -> None:
        builder = CandidateBuilder(cap=10)
        result = builder.build(restaurants)
        ratings = [r.rating for r in result]
        assert ratings == sorted(ratings, reverse=True)

    def test_cap_limits_output(self, restaurants: list[Restaurant]) -> None:
        builder = CandidateBuilder(cap=3)
        result = builder.build(restaurants)
        assert len(result) == 3

    def test_cap_default_from_settings(self, restaurants: list[Restaurant]) -> None:
        builder = CandidateBuilder()  # uses settings.candidate_cap (20)
        result = builder.build(restaurants)
        assert len(result) <= 20

    def test_serialize_keys(self, restaurants: list[Restaurant]) -> None:
        builder = CandidateBuilder(cap=2)
        candidates = builder.build(restaurants)
        serialized = builder.serialize(candidates)
        assert len(serialized) == 2
        expected_keys = {"id", "name", "cuisines", "rating", "cost_bucket", "cost_for_two", "location"}
        for item in serialized:
            assert set(item.keys()) == expected_keys

    def test_to_json_is_valid(self, restaurants: list[Restaurant]) -> None:
        builder = CandidateBuilder(cap=2)
        candidates = builder.build(restaurants)
        json_str = builder.to_json(candidates)
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 2


# ── Convenience functions ──────────────────────────────────────────────────────


class TestConvenienceFunctions:
    def test_apply_filters(self, restaurants: list[Restaurant]) -> None:
        prefs = _prefs()
        result = apply_filters(restaurants, prefs)
        assert isinstance(result.candidates, list)

    def test_build_candidates(self, restaurants: list[Restaurant]) -> None:
        result = build_candidates(restaurants)
        assert len(result) <= 20
        ratings = [r.rating for r in result]
        assert ratings == sorted(ratings, reverse=True)
