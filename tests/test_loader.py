"""Unit tests for the dataset loader (src.data.loader).

The loader calls Hugging Face which requires network access.
Tests here use mocked versions of ``load_dataset`` to avoid network
dependencies in CI.  Integration tests that hit the real dataset can
be run separately with ``pytest -m integration``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.data.loader import COLUMN_MAP, get_column_names, load_raw_dataset


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_hf_rows() -> list[dict]:
    """Minimal rows mimicking the Hugging Face dataset schema."""
    return [
        {
            "name": "Test Restaurant",
            "location": "Indiranagar",
            "listed_in(city)": "Indiranagar",
            "cuisines": "Italian, Chinese",
            "approx_cost(for two people)": "800",
            "rate": "4.2/5",
            "votes": 100,
            "address": "123 Test Street",
            "rest_type": "Casual Dining",
            "dish_liked": "Pasta, Pizza",
            "online_order": "Yes",
            "book_table": "No",
            "listed_in(type)": "Delivery",
            "url": "https://example.com",
            "phone": "1234567890",
            "reviews_list": "[]",
            "menu_item": "[]",
        },
        {
            "name": "Another Place",
            "location": "Koramangala",
            "listed_in(city)": "Koramangala",
            "cuisines": "North Indian",
            "approx_cost(for two people)": "400",
            "rate": "3.9/5",
            "votes": 50,
            "address": "456 Other Road",
            "rest_type": "Quick Bites",
            "dish_liked": "",
            "online_order": "No",
            "book_table": "No",
            "listed_in(type)": "Dining Out",
            "url": "https://example.com/2",
            "phone": "",
            "reviews_list": "[]",
            "menu_item": "[]",
        },
    ]


@pytest.fixture
def mock_dataset(fake_hf_rows: list[dict]) -> MagicMock:
    """Mock Hugging Face Dataset object."""
    ds = MagicMock()
    ds.__iter__ = MagicMock(return_value=iter(fake_hf_rows))
    ds.__len__ = MagicMock(return_value=len(fake_hf_rows))
    ds.column_names = list(fake_hf_rows[0].keys())
    return ds


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_load_raw_dataset_returns_dicts(mock_dataset: MagicMock) -> None:
    """Loader converts Hugging Face dataset rows to plain dicts."""
    with patch("src.data.loader.load_dataset", return_value=mock_dataset):
        rows = load_raw_dataset()

    assert len(rows) == 2
    assert isinstance(rows[0], dict)
    assert rows[0]["name"] == "Test Restaurant"
    assert rows[1]["cuisines"] == "North Indian"


def test_load_raw_dataset_propagates_error() -> None:
    """Loader raises RuntimeError when Hugging Face load fails."""
    with patch("src.data.loader.load_dataset", side_effect=Exception("network error")):
        with pytest.raises(RuntimeError, match="Failed to load dataset"):
            load_raw_dataset()


def test_column_map_covers_expected_fields() -> None:
    """COLUMN_MAP includes all primary extraction targets."""
    expected_keys = {"name", "location", "listed_in(city)", "cuisines",
                     "approx_cost(for two people)", "rate", "votes"}
    assert expected_keys.issubset(set(COLUMN_MAP.keys()))


def test_column_map_values_are_strings() -> None:
    """All canonical names in COLUMN_MAP are non-empty strings."""
    for src_col, canon in COLUMN_MAP.items():
        assert isinstance(src_col, str) and src_col, f"Bad source key: {src_col!r}"
        assert isinstance(canon, str) and canon, f"Bad canonical name: {canon!r}"


def test_get_column_names(mock_dataset: MagicMock) -> None:
    """get_column_names returns keys from the first row."""
    # Simulate streaming mode returning an iterator of dicts
    with patch("src.data.loader.load_dataset", return_value=mock_dataset):
        cols = get_column_names()

    assert "name" in cols
    assert "cuisines" in cols
