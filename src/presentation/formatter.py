"""Format recommendations for user presentation.

Translates internal Restaurant and Recommendation domain models into
display-ready DTOs with consistent currency, cuisine, and rating formatting.

Architecture reference: §9 (Output and Presentation Layer)
"""

from __future__ import annotations

from dataclasses import dataclass
from src.data.models import CostBucket, Recommendation


@dataclass(frozen=True)
class DisplayRecommendation:
    """A formatted recommendation DTO for user display."""

    name: str
    cuisine: str
    rating: str
    cost: str
    explanation: str
    rank: int
    location: str = ""


def format_recommendations(recommendations: list[Recommendation]) -> list[DisplayRecommendation]:
    """Format a list of ``Recommendation`` objects into display-ready DTOs.

    - Cuisines are capitalized and joined with commas
    - Ratings are formatted to one decimal place with a star (e.g., "4.2★")
    - Costs are formatted in INR (e.g., "₹800 for two") or fallback to cost bucket label
    """
    display_recs: list[DisplayRecommendation] = []

    for rec in recommendations:
        rest = rec.restaurant

        # 1. Format cuisines
        cuisine_str = ", ".join(c.strip().title() for c in rest.cuisines)

        # 2. Format rating
        rating_str = f"{rest.rating:.1f}★"

        # 3. Format cost
        if rest.cost_for_two is not None and rest.cost_for_two > 0:
            cost_str = f"₹{rest.cost_for_two} for two"
        else:
            bucket_labels = {
                CostBucket.LOW: "Low Budget",
                CostBucket.MEDIUM: "Medium Budget",
                CostBucket.HIGH: "High Budget",
                CostBucket.UNKNOWN: "Budget Unknown",
            }
            cost_str = bucket_labels.get(rest.cost_bucket, "Budget Unknown")

        display_recs.append(
            DisplayRecommendation(
                name=rest.name,
                cuisine=cuisine_str,
                rating=rating_str,
                cost=cost_str,
                explanation=rec.explanation,
                rank=rec.rank,
                location=rest.location.title(),
            )
        )

    return display_recs
