"""Shared pytest fixtures for the restaurant recommendation system."""

from __future__ import annotations

import pytest

from src.data.models import Budget, CostBucket, Restaurant, UserPreferences


@pytest.fixture
def sample_restaurant() -> Restaurant:
    """A representative restaurant for unit tests."""
    return Restaurant(
        id="r_1042",
        name="Example Bistro",
        location="bangalore",
        cuisines=["italian", "continental"],
        cost_for_two=800,
        cost_bucket=CostBucket.MEDIUM,
        rating=4.2,
        metadata={"votes": 120},
    )


@pytest.fixture
def sample_preferences() -> UserPreferences:
    """A representative user preference set for unit tests."""
    return UserPreferences(
        location="bangalore",
        budget=Budget.MEDIUM,
        cuisine="italian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )


@pytest.fixture
def sample_restaurants(sample_restaurant: Restaurant) -> list[Restaurant]:
    """A small list of restaurants for filter/orchestrator tests."""
    return [
        sample_restaurant,
        Restaurant(
            id="r_2087",
            name="Spice Garden",
            location="bangalore",
            cuisines=["chinese", "thai"],
            cost_for_two=600,
            cost_bucket=CostBucket.MEDIUM,
            rating=4.5,
            metadata={},
        ),
        Restaurant(
            id="r_3099",
            name="Budget Bites",
            location="delhi",
            cuisines=["north indian"],
            cost_for_two=300,
            cost_bucket=CostBucket.LOW,
            rating=3.8,
            metadata={},
        ),
    ]
