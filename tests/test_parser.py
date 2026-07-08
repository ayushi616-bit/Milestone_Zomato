"""Unit tests for the response parser (src.llm.parser)."""

from __future__ import annotations

import json

import pytest

from src.data.models import CostBucket, Recommendation, Restaurant
from src.llm.parser import (
    FORMAT_CORRECTION_HINT,
    LLMParsedResult,
    ResponseParser,
    merge_with_restaurants,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def candidates() -> list[Restaurant]:
    return [
        Restaurant(
            id="r_01", name="Italian Bistro", location="indiranagar",
            cuisines=["italian", "continental"], cost_for_two=800,
            cost_bucket=CostBucket.MEDIUM, rating=4.5, metadata={},
        ),
        Restaurant(
            id="r_02", name="Chinese Wok", location="koramangala",
            cuisines=["chinese", "thai"], cost_for_two=600,
            cost_bucket=CostBucket.MEDIUM, rating=4.2, metadata={},
        ),
        Restaurant(
            id="r_03", name="Budget Curry", location="indiranagar",
            cuisines=["north indian"], cost_for_two=300,
            cost_bucket=CostBucket.LOW, rating=3.8, metadata={},
        ),
    ]


def _valid_llm_response() -> str:
    """A valid LLM JSON response matching the fixture candidates."""
    return json.dumps({
        "summary": "Two great Italian options in Indiranagar.",
        "recommendations": [
            {
                "restaurant_id": "r_01",
                "rank": 1,
                "explanation": "Top-rated Italian spot perfect for families.",
            },
            {
                "restaurant_id": "r_02",
                "rank": 2,
                "explanation": "Good Asian option with moderate pricing.",
            },
        ],
    })


# ── Valid JSON parsing ────────────────────────────────────────────────────────


class TestParseValidJson:
    def test_parses_wellformed_response(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.parse(_valid_llm_response())
        assert isinstance(result, LLMParsedResult)
        assert result.summary == "Two great Italian options in Indiranagar."
        assert len(result.recommendations) == 2

    def test_recommendation_fields(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.parse(_valid_llm_response())
        rec = result.recommendations[0]
        assert rec.restaurant_id == "r_01"
        assert rec.rank == 1
        assert "Italian" in rec.explanation or "italian" in rec.explanation.lower()

    def test_no_discarded_ids(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.parse(_valid_llm_response())
        assert result.discarded_ids == []

    def test_sorted_by_rank(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.parse(_valid_llm_response())
        ranks = [r.rank for r in result.recommendations]
        assert ranks == sorted(ranks)


# ── Hallucination rejection ───────────────────────────────────────────────────


class TestHallucinationRejection:
    def test_rejects_unknown_id(self, candidates: list[Restaurant]) -> None:
        response = json.dumps({
            "summary": "Mixed results.",
            "recommendations": [
                {"restaurant_id": "r_01", "rank": 1, "explanation": "Valid."},
                {"restaurant_id": "r_HALLUCINATED", "rank": 2, "explanation": "Invented."},
                {"restaurant_id": "r_02", "rank": 3, "explanation": "Also valid."},
            ],
        })
        parser = ResponseParser(candidates)
        result = parser.parse(response)
        # Only valid IDs should remain
        ids = [r.restaurant_id for r in result.recommendations]
        assert "r_HALLUCINATED" not in ids
        assert "r_01" in ids
        assert "r_02" in ids

    def test_discarded_ids_tracked(self, candidates: list[Restaurant]) -> None:
        response = json.dumps({
            "summary": "Summary.",
            "recommendations": [
                {"restaurant_id": "r_FAKE1", "rank": 1, "explanation": "Fake."},
                {"restaurant_id": "r_FAKE2", "rank": 2, "explanation": "Fake."},
                {"restaurant_id": "r_01", "rank": 3, "explanation": "Real."},
            ],
        })
        parser = ResponseParser(candidates)
        result = parser.parse(response)
        assert "r_FAKE1" in result.discarded_ids
        assert "r_FAKE2" in result.discarded_ids
        assert len(result.recommendations) == 1

    def test_all_hallucinated(self, candidates: list[Restaurant]) -> None:
        response = json.dumps({
            "summary": "All fake.",
            "recommendations": [
                {"restaurant_id": "r_FAKE", "rank": 1, "explanation": "Fake."},
            ],
        })
        parser = ResponseParser(candidates)
        result = parser.parse(response)
        assert len(result.recommendations) == 0
        assert "r_FAKE" in result.discarded_ids


# ── Malformed JSON handling ──────────────────────────────────────────────────


class TestMalformedJson:
    def test_invalid_json_raises(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        with pytest.raises(ValueError, match="Cannot parse"):
            parser.parse("This is not JSON at all")

    def test_parse_safe_returns_none_on_invalid(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.parse_safe("Not JSON")
        assert result is None

    def test_parse_safe_returns_result_on_valid(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.parse_safe(_valid_llm_response())
        assert result is not None
        assert len(result.recommendations) == 2

    def test_markdown_code_block_extraction(self, candidates: list[Restaurant]) -> None:
        wrapped = f"Here is my response:\n```json\n{_valid_llm_response()}\n```\nThanks!"
        parser = ResponseParser(candidates)
        result = parser.parse(wrapped)
        assert len(result.recommendations) == 2

    def test_non_object_json_raises(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        with pytest.raises(ValueError, match="Expected JSON object"):
            parser.parse("[1, 2, 3]")

    def test_missing_recommendations_key(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        response = json.dumps({"summary": "No recs key."})
        result = parser.parse(response)
        assert result.recommendations == []


# ── Fallback ranking ──────────────────────────────────────────────────────────


class TestFallbackRanking:
    def test_returns_rating_sorted(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates, top_k=5)
        result = parser.fallback_recommendations()
        ratings = [
            next(c.rating for c in candidates if c.id == r.restaurant_id)
            for r in result.recommendations
        ]
        assert ratings == sorted(ratings, reverse=True)

    def test_caps_at_top_k(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates, top_k=2)
        result = parser.fallback_recommendations()
        assert len(result.recommendations) == 2

    def test_has_summary(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.fallback_recommendations()
        assert result.summary
        assert "AI" in result.summary or "rating" in result.summary.lower()

    def test_has_explanations(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        result = parser.fallback_recommendations()
        for rec in result.recommendations:
            assert rec.explanation


# ── Merge with restaurants ────────────────────────────────────────────────────


class TestMergeWithRestaurants:
    def test_merges_correctly(self, candidates: list[Restaurant]) -> None:
        parser = ResponseParser(candidates)
        parsed = parser.parse(_valid_llm_response())
        merged = merge_with_restaurants(parsed, candidates)
        assert len(merged) == 2
        assert all(isinstance(r, Recommendation) for r in merged)
        assert merged[0].restaurant.name == "Italian Bistro"

    def test_drops_unknown_ids(self, candidates: list[Restaurant]) -> None:
        from src.llm.parser import LLMParsedResult, ParsedRecommendation
        parsed = LLMParsedResult(
            summary="Test.",
            recommendations=[
                ParsedRecommendation(restaurant_id="r_01", rank=1, explanation="Good."),
                ParsedRecommendation(restaurant_id="r_MISSING", rank=2, explanation="Gone."),
            ],
        )
        merged = merge_with_restaurants(parsed, candidates)
        assert len(merged) == 1
        assert merged[0].restaurant.id == "r_01"


# ── Format correction hint ────────────────────────────────────────────────────


class TestFormatCorrectionHint:
    def test_hint_is_string(self) -> None:
        assert isinstance(FORMAT_CORRECTION_HINT, str)
        assert len(FORMAT_CORRECTION_HINT) > 10

    def test_hint_mentions_json(self) -> None:
        assert "JSON" in FORMAT_CORRECTION_HINT

    def test_hint_includes_schema_fields(self) -> None:
        assert "restaurant_id" in FORMAT_CORRECTION_HINT
        assert "explanation" in FORMAT_CORRECTION_HINT
