"""Unit tests for the prompt builder (src.llm.prompt_builder)."""

from __future__ import annotations

import json

import pytest

from src.data.models import Budget, CostBucket, Restaurant, UserPreferences
from src.llm.prompt_builder import (
    LLM_OUTPUT_SCHEMA,
    build_messages,
    build_system_prompt,
    build_user_prompt,
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


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="indiranagar",
        budget=Budget.MEDIUM,
        cuisine="italian",
        min_rating=3.5,
        additional_preferences="family-friendly",
    )


# ── System prompt ─────────────────────────────────────────────────────────────


class TestBuildSystemPrompt:
    def test_contains_top_k(self) -> None:
        prompt = build_system_prompt(top_k=5)
        assert "5" in prompt

    def test_default_top_k(self) -> None:
        prompt = build_system_prompt()
        assert "5" in prompt  # settings.top_k_recommendations is 5

    def test_mentions_no_invention(self) -> None:
        prompt = build_system_prompt()
        assert "ONLY" in prompt or "Do not invent" in prompt

    def test_mentions_json_output(self) -> None:
        prompt = build_system_prompt()
        assert "JSON" in prompt


# ── User prompt ───────────────────────────────────────────────────────────────


class TestBuildUserPrompt:
    def test_includes_all_preferences(
        self, preferences: UserPreferences, candidates: list[Restaurant],
    ) -> None:
        prompt = build_user_prompt(preferences, candidates)
        assert "indiranagar" in prompt
        assert "medium" in prompt
        assert "italian" in prompt
        assert "3.5" in prompt
        assert "family-friendly" in prompt

    def test_includes_candidate_list(
        self, preferences: UserPreferences, candidates: list[Restaurant],
    ) -> None:
        prompt = build_user_prompt(preferences, candidates)
        assert "r_01" in prompt
        assert "r_02" in prompt
        assert "r_03" in prompt
        assert "Italian Bistro" in prompt

    def test_includes_schema(
        self, preferences: UserPreferences, candidates: list[Restaurant],
    ) -> None:
        prompt = build_user_prompt(preferences, candidates)
        assert "restaurant_id" in prompt
        assert "explanation" in prompt
        assert "summary" in prompt

    def test_no_additional_shows_none(
        self, candidates: list[Restaurant],
    ) -> None:
        prefs = UserPreferences(
            location="bangalore", budget=Budget.LOW,
            cuisine="indian", min_rating=3.0,
        )
        prompt = build_user_prompt(prefs, candidates)
        assert "none" in prompt

    def test_multi_cuisine_display(
        self, candidates: list[Restaurant],
    ) -> None:
        prefs = UserPreferences(
            location="bangalore", budget=Budget.MEDIUM,
            cuisine=["italian", "chinese"], min_rating=3.0,
        )
        prompt = build_user_prompt(prefs, candidates)
        assert "italian" in prompt
        assert "chinese" in prompt


# ── Build messages ────────────────────────────────────────────────────────────


class TestBuildMessages:
    def test_returns_two_messages(
        self, preferences: UserPreferences, candidates: list[Restaurant],
    ) -> None:
        messages = build_messages(preferences, candidates)
        assert len(messages) == 2

    def test_system_message_first(
        self, preferences: UserPreferences, candidates: list[Restaurant],
    ) -> None:
        messages = build_messages(preferences, candidates)
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_message_content_non_empty(
        self, preferences: UserPreferences, candidates: list[Restaurant],
    ) -> None:
        messages = build_messages(preferences, candidates)
        for msg in messages:
            assert msg["content"]
            assert isinstance(msg["content"], str)


# ── Schema validation ─────────────────────────────────────────────────────────


class TestOutputSchema:
    def test_schema_is_valid_json(self) -> None:
        # Should serialize without errors
        json_str = json.dumps(LLM_OUTPUT_SCHEMA)
        parsed = json.loads(json_str)
        assert parsed["type"] == "object"

    def test_schema_has_required_fields(self) -> None:
        assert "summary" in LLM_OUTPUT_SCHEMA["properties"]
        assert "recommendations" in LLM_OUTPUT_SCHEMA["properties"]

    def test_recommendation_item_schema(self) -> None:
        item_schema = LLM_OUTPUT_SCHEMA["properties"]["recommendations"]["items"]
        props = item_schema["properties"]
        assert "restaurant_id" in props
        assert "rank" in props
        assert "explanation" in props
