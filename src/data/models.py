"""Domain models for the restaurant recommendation system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Budget(str, Enum):
    """User-selected budget tier."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostBucket(str, Enum):
    """Derived cost tier for a restaurant."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Restaurant:
    """Normalized restaurant record from the Zomato dataset."""

    id: str
    name: str
    location: str
    cuisines: list[str]
    cost_for_two: int | None
    cost_bucket: CostBucket
    rating: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UserPreferences:
    """Validated user input for restaurant recommendations."""

    location: str
    budget: Budget
    cuisine: str | list[str]
    min_rating: float
    additional_preferences: str | None = None

    def cuisines_list(self) -> list[str]:
        """Return cuisine preference(s) as a normalized list."""
        if isinstance(self.cuisine, list):
            return [c.strip() for c in self.cuisine if c.strip()]
        return [self.cuisine.strip()] if self.cuisine.strip() else []


@dataclass(frozen=True)
class Recommendation:
    """A ranked restaurant recommendation with an AI-generated explanation."""

    restaurant: Restaurant
    rank: int
    explanation: str
    match_score: float | None = None
