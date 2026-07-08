"""Unit tests for domain models."""

from src.data.models import (
    Budget,
    CostBucket,
    Recommendation,
    Restaurant,
    UserPreferences,
)


def test_restaurant_creation(sample_restaurant: Restaurant) -> None:
    assert sample_restaurant.id == "r_1042"
    assert sample_restaurant.name == "Example Bistro"
    assert sample_restaurant.rating == 4.2
    assert sample_restaurant.cost_bucket == CostBucket.MEDIUM


def test_user_preferences_single_cuisine(sample_preferences: UserPreferences) -> None:
    assert sample_preferences.location == "bangalore"
    assert sample_preferences.budget == Budget.MEDIUM
    assert sample_preferences.cuisines_list() == ["italian"]


def test_user_preferences_multi_cuisine() -> None:
    prefs = UserPreferences(
        location="delhi",
        budget=Budget.LOW,
        cuisine=["italian", "chinese"],
        min_rating=3.5,
    )
    assert prefs.cuisines_list() == ["italian", "chinese"]


def test_recommendation_links_restaurant(sample_restaurant: Restaurant) -> None:
    rec = Recommendation(
        restaurant=sample_restaurant,
        rank=1,
        explanation="Highly rated Italian spot.",
        match_score=0.92,
    )
    assert rec.rank == 1
    assert rec.restaurant.name == "Example Bistro"


def test_budget_and_cost_bucket_enums() -> None:
    assert Budget.LOW.value == "low"
    assert CostBucket.UNKNOWN.value == "unknown"
