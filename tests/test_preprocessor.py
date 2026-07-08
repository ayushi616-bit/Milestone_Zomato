"""Unit tests for the preprocessor (src.data.preprocessor)."""

from __future__ import annotations

import pytest

from src.data.models import CostBucket, Restaurant
from src.data.preprocessor import (
    _build_metadata,
    _derive_cost_bucket,
    _generate_id,
    _normalize_location,
    _parse_cost,
    _parse_cuisines,
    _parse_rating,
    preprocess_records,
)


# ── Helper: minimal raw row ──────────────────────────────────────────────────


def _make_row(**overrides) -> dict:
    """Build a minimal raw dataset row with sensible defaults."""
    base = {
        "name": "Test Place",
        "location": "Indiranagar",
        "listed_in(city)": "Indiranagar",
        "cuisines": "Italian, Chinese",
        "approx_cost(for two people)": "800",
        "rate": "4.2/5",
        "votes": 100,
        "address": "123 Test St",
        "rest_type": "Casual Dining",
        "dish_liked": "Pasta",
        "online_order": "Yes",
        "book_table": "No",
        "listed_in(type)": "Delivery",
        "url": "",
        "phone": "",
        "reviews_list": "[]",
        "menu_item": "[]",
    }
    base.update(overrides)
    return base


# ── Location normalization ─────────────────────────────────────────────────────


class TestNormalizeLocation:
    def test_lowercase_and_trim(self) -> None:
        assert _normalize_location("  Bangalore  ") == "bangalore"

    def test_alias_bengaluru(self) -> None:
        assert _normalize_location("Bengaluru") == "bangalore"

    def test_alias_bombay(self) -> None:
        assert _normalize_location("Bombay") == "mumbai"

    def test_no_alias_passthrough(self) -> None:
        assert _normalize_location("Koramangala") == "koramangala"

    def test_empty_string(self) -> None:
        assert _normalize_location("") == ""

    def test_none_like(self) -> None:
        # _normalize_location expects str; empty from _clean_string(None)
        assert _normalize_location("") == ""


# ── Cuisine parsing ────────────────────────────────────────────────────────────


class TestParseCuisines:
    def test_comma_separated(self) -> None:
        assert _parse_cuisines("Italian, Chinese, Mexican") == ["italian", "chinese", "mexican"]

    def test_single_cuisine(self) -> None:
        assert _parse_cuisines("North Indian") == ["north indian"]

    def test_deduplication(self) -> None:
        result = _parse_cuisines("Italian, Italian, chinese")
        assert result == ["italian", "chinese"]

    def test_empty_string(self) -> None:
        assert _parse_cuisines("") == []

    def test_none(self) -> None:
        assert _parse_cuisines(None) == []

    def test_whitespace_only(self) -> None:
        assert _parse_cuisines("   ") == []


# ── Cost parsing ───────────────────────────────────────────────────────────────


class TestParseCost:
    def test_simple_integer_string(self) -> None:
        assert _parse_cost("800") == 800

    def test_comma_separated(self) -> None:
        assert _parse_cost("1,100") == 1100

    def test_none(self) -> None:
        assert _parse_cost(None) is None

    def test_empty_string(self) -> None:
        assert _parse_cost("") is None

    def test_non_numeric(self) -> None:
        assert _parse_cost("not-a-number") is None

    def test_negative_value(self) -> None:
        assert _parse_cost("-100") is None


# ── Cost bucket derivation ────────────────────────────────────────────────────


class TestDeriveCostBucket:
    def test_low(self) -> None:
        assert _derive_cost_bucket(300) == CostBucket.LOW

    def test_low_boundary(self) -> None:
        assert _derive_cost_bucket(500) == CostBucket.LOW

    def test_medium(self) -> None:
        assert _derive_cost_bucket(800) == CostBucket.MEDIUM

    def test_medium_boundary(self) -> None:
        assert _derive_cost_bucket(1500) == CostBucket.MEDIUM

    def test_high(self) -> None:
        assert _derive_cost_bucket(2000) == CostBucket.HIGH

    def test_unknown_when_none(self) -> None:
        assert _derive_cost_bucket(None) == CostBucket.UNKNOWN


# ── Rating parsing ─────────────────────────────────────────────────────────────


class TestParseRating:
    def test_standard_format(self) -> None:
        assert _parse_rating("4.1/5") == pytest.approx(4.1)

    def test_plain_float(self) -> None:
        assert _parse_rating("3.5") == pytest.approx(3.5)

    def test_new_label(self) -> None:
        assert _parse_rating("NEW") == 0.0

    def test_dash_label(self) -> None:
        assert _parse_rating("-") == 0.0

    def test_none(self) -> None:
        assert _parse_rating(None) == 0.0

    def test_empty_string(self) -> None:
        assert _parse_rating("") == 0.0

    def test_custom_default(self) -> None:
        assert _parse_rating(None, default=3.0) == 3.0

    def test_clamp_above_5(self) -> None:
        assert _parse_rating("6.0/5") == 5.0

    def test_clamp_negative(self) -> None:
        assert _parse_rating("-1.0/5") == 0.0

    def test_invalid_text(self) -> None:
        assert _parse_rating("abc/5") == 0.0


# ── ID generation ──────────────────────────────────────────────────────────────


class TestGenerateId:
    def test_format(self) -> None:
        row = {"name": "Test", "listed_in(city)": "Indiranagar"}
        rid = _generate_id(row, 0)
        assert rid.startswith("r_")
        assert len(rid) == 10  # "r_" + 8 hex chars

    def test_deterministic(self) -> None:
        row = {"name": "Test", "listed_in(city)": "Indiranagar"}
        assert _generate_id(row, 0) == _generate_id(row, 0)

    def test_different_index_different_id(self) -> None:
        row = {"name": "Test", "listed_in(city)": "Indiranagar"}
        assert _generate_id(row, 0) != _generate_id(row, 1)


# ── Metadata builder ───────────────────────────────────────────────────────────


class TestBuildMetadata:
    def test_includes_populated_fields(self) -> None:
        row = _make_row()
        meta = _build_metadata(row)
        assert "address" in meta
        assert "rest_type" in meta
        assert "votes" in meta

    def test_omits_empty_fields(self) -> None:
        row = _make_row(address="", rest_type="", dish_liked="", phone="")
        meta = _build_metadata(row)
        assert "address" not in meta
        assert "rest_type" not in meta

    def test_votes_as_int(self) -> None:
        row = _make_row(votes=500)
        meta = _build_metadata(row)
        assert meta["votes"] == 500
        assert isinstance(meta["votes"], int)


# ── Full preprocess_records pipeline ───────────────────────────────────────────


class TestPreprocessRecords:
    def test_basic_preprocessing(self) -> None:
        rows = [_make_row()]
        result = preprocess_records(rows)
        assert len(result) == 1
        r = result[0]
        assert isinstance(r, Restaurant)
        assert r.name == "Test Place"
        assert r.location == "indiranagar"
        assert "italian" in r.cuisines
        assert "chinese" in r.cuisines
        assert r.cost_for_two == 800
        assert r.cost_bucket == CostBucket.MEDIUM
        assert r.rating == pytest.approx(4.2)

    def test_drops_empty_name(self) -> None:
        rows = [_make_row(name=""), _make_row(name="  "), _make_row(name=None)]
        result = preprocess_records(rows)
        assert len(result) == 0

    def test_keeps_unknown_name_when_configured(self) -> None:
        rows = [_make_row(name="")]
        result = preprocess_records(rows, drop_no_name=False)
        assert len(result) == 1
        assert result[0].name == "Unknown"

    def test_multiple_rows(self) -> None:
        rows = [
            _make_row(name="A"),
            _make_row(name="B", **{"listed_in(city)": "Koramangala"}),
        ]
        result = preprocess_records(rows)
        assert len(result) == 2
        assert result[0].name == "A"
        assert result[1].name == "B"
        assert result[1].location == "koramangala"

    def test_id_uniqueness(self) -> None:
        rows = [_make_row(name=f"Place {i}") for i in range(100)]
        result = preprocess_records(rows)
        ids = [r.id for r in result]
        assert len(set(ids)) == 100, "All IDs must be unique"

    def test_handles_missing_cost(self) -> None:
        rows = [_make_row(**{"approx_cost(for two people)": None})]
        result = preprocess_records(rows)
        assert result[0].cost_for_two is None
        assert result[0].cost_bucket == CostBucket.UNKNOWN

    def test_handles_new_rating(self) -> None:
        rows = [_make_row(rate="NEW")]
        result = preprocess_records(rows)
        assert result[0].rating == 0.0

    def test_no_empty_names_in_output(self) -> None:
        """All output restaurants must have non-empty names."""
        rows = [
            _make_row(name="Valid"),
            _make_row(name=""),
            _make_row(name=None),
            _make_row(name="Also Valid"),
        ]
        result = preprocess_records(rows)
        assert len(result) == 2
        for r in result:
            assert r.name.strip() != ""
