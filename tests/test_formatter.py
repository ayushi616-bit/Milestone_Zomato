"""Unit tests for the presentation formatter (src.presentation.formatter)."""

from __future__ import annotations

from src.data.models import CostBucket, Restaurant, Recommendation
from src.presentation.formatter import format_recommendations


def test_format_recommendations_happy_path(sample_restaurant: Restaurant) -> None:
    rec = Recommendation(
        restaurant=sample_restaurant,
        rank=1,
        explanation="Test explanation.",
    )
    results = format_recommendations([rec])

    assert len(results) == 1
    display = results[0]
    assert display.name == "Example Bistro"
    assert display.cuisine == "Italian, Continental"
    assert display.rating == "4.2★"
    assert display.cost == "₹800 for two"
    assert display.explanation == "Test explanation."
    assert display.rank == 1


def test_format_recommendations_cost_bucket_fallback() -> None:
    rest = Restaurant(
        id="r_2",
        name="No Price Cafe",
        location="delhi",
        cuisines=["chinese"],
        cost_for_two=None,
        cost_bucket=CostBucket.LOW,
        rating=3.9,
    )
    rec = Recommendation(restaurant=rest, rank=2, explanation="Good price.")
    results = format_recommendations([rec])

    assert len(results) == 1
    assert results[0].cost == "Low Budget"
