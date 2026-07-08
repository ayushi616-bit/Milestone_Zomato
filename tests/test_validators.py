"""Unit tests for the input validator (src.validators)."""

from __future__ import annotations

import pytest

from src.data.models import Budget, UserPreferences
from src.validators import ValidationError, validate_preferences


# ── Happy path ────────────────────────────────────────────────────────────────


class TestValidatePreferencesHappyPath:
    def test_basic_valid_input(self) -> None:
        prefs = validate_preferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
        )
        assert isinstance(prefs, UserPreferences)
        assert prefs.location == "bangalore"
        assert prefs.budget == Budget.MEDIUM
        assert prefs.cuisine == "italian"
        assert prefs.min_rating == 4.0
        assert prefs.additional_preferences is None

    def test_budget_as_enum(self) -> None:
        prefs = validate_preferences(
            location="Delhi",
            budget=Budget.HIGH,
            cuisine="Chinese",
            min_rating=3.5,
        )
        assert prefs.budget == Budget.HIGH

    def test_multi_cuisine_list(self) -> None:
        prefs = validate_preferences(
            location="Mumbai",
            budget="low",
            cuisine=["Italian", "Chinese"],
            min_rating=2.0,
        )
        assert prefs.cuisine == ["italian", "chinese"]

    def test_comma_separated_cuisine(self) -> None:
        prefs = validate_preferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian, Chinese, Mexican",
            min_rating=3.0,
        )
        assert prefs.cuisine == ["italian", "chinese", "mexican"]

    def test_min_rating_as_string(self) -> None:
        prefs = validate_preferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating="4.5",
        )
        assert prefs.min_rating == 4.5

    def test_min_rating_as_int(self) -> None:
        prefs = validate_preferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=3,
        )
        assert prefs.min_rating == 3.0

    def test_additional_preferences(self) -> None:
        prefs = validate_preferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=3.0,
            additional_preferences="family-friendly, quiet ambience",
        )
        assert prefs.additional_preferences == "family-friendly, quiet ambience"

    def test_empty_additional_returns_none(self) -> None:
        prefs = validate_preferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=3.0,
            additional_preferences="   ",
        )
        assert prefs.additional_preferences is None

    def test_boundary_rating_zero(self) -> None:
        prefs = validate_preferences(
            location="Bangalore", budget="low", cuisine="Indian", min_rating=0.0,
        )
        assert prefs.min_rating == 0.0

    def test_boundary_rating_five(self) -> None:
        prefs = validate_preferences(
            location="Bangalore", budget="high", cuisine="Italian", min_rating=5.0,
        )
        assert prefs.min_rating == 5.0


# ── Validation errors ─────────────────────────────────────────────────────────


class TestValidatePreferencesErrors:
    def test_empty_location(self) -> None:
        with pytest.raises(ValidationError, match="location"):
            validate_preferences(location="", budget="medium", cuisine="Italian", min_rating=3.0)

    def test_whitespace_location(self) -> None:
        with pytest.raises(ValidationError, match="location"):
            validate_preferences(location="   ", budget="medium", cuisine="Italian", min_rating=3.0)

    def test_invalid_budget(self) -> None:
        with pytest.raises(ValidationError, match="budget.*Invalid"):
            validate_preferences(
                location="Bangalore", budget="luxury", cuisine="Italian", min_rating=3.0,
            )

    def test_empty_budget(self) -> None:
        with pytest.raises(ValidationError, match="budget.*required"):
            validate_preferences(
                location="Bangalore", budget="", cuisine="Italian", min_rating=3.0,
            )

    def test_empty_cuisine(self) -> None:
        with pytest.raises(ValidationError, match="cuisine"):
            validate_preferences(
                location="Bangalore", budget="medium", cuisine="", min_rating=3.0,
            )

    def test_empty_cuisine_list(self) -> None:
        with pytest.raises(ValidationError, match="cuisine"):
            validate_preferences(
                location="Bangalore", budget="medium", cuisine=[], min_rating=3.0,
            )

    def test_rating_above_5(self) -> None:
        with pytest.raises(ValidationError, match="min_rating.*between"):
            validate_preferences(
                location="Bangalore", budget="medium", cuisine="Italian", min_rating=6.0,
            )

    def test_rating_below_0(self) -> None:
        with pytest.raises(ValidationError, match="min_rating.*between"):
            validate_preferences(
                location="Bangalore", budget="medium", cuisine="Italian", min_rating=-1.0,
            )

    def test_rating_non_numeric(self) -> None:
        with pytest.raises(ValidationError, match="min_rating.*number"):
            validate_preferences(
                location="Bangalore", budget="medium", cuisine="Italian", min_rating="abc",
            )

    def test_additional_too_long(self) -> None:
        with pytest.raises(ValidationError, match="additional_preferences.*characters"):
            validate_preferences(
                location="Bangalore",
                budget="medium",
                cuisine="Italian",
                min_rating=3.0,
                additional_preferences="x" * 600,
            )

    def test_validation_error_has_field(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_preferences(
                location="", budget="medium", cuisine="Italian", min_rating=3.0,
            )
        assert exc_info.value.field == "location"
        assert exc_info.value.message  # non-empty
