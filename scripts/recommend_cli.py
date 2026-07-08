#!/usr/bin/env python3
"""CLI script to test the recommendation engine end-to-end.

Accepts user preferences via command-line arguments or prompts interactively,
then displays the formatted AI recommendations.

Usage:
    python scripts/recommend_cli.py --location Bangalore --budget medium --cuisine Italian
"""

from __future__ import annotations

import argparse
import sys

from src.orchestrator import recommend


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Restaurant Recommendation System")
    parser.add_argument("--location", type=str, help="Location / City name")
    parser.add_argument("--budget", type=str, choices=["low", "medium", "high"], help="Budget tier")
    parser.add_argument("--cuisine", type=str, help="Preferred cuisine")
    parser.add_argument("--min-rating", type=float, help="Minimum rating (0.0 - 5.0)")
    parser.add_argument("--notes", type=str, help="Optional additional preferences (e.g. family-friendly)")
    parser.add_argument("--interactive", action="store_true", help="Force interactive prompts")

    args = parser.parse_args()

    # Determine if we should prompt interactively
    interactive = args.interactive or not (args.location and args.budget and args.cuisine and args.min_rating is not None)

    if interactive:
        print("\n=== AI Restaurant Recommendation System ===")
        print("Please enter your dining preferences:\n")

        location = input("Location (e.g., Bangalore, Delhi): ").strip()
        while not location:
            print("Location is required.")
            location = input("Location: ").strip()

        budget = input("Budget (low / medium / high) [medium]: ").strip().lower() or "medium"
        while budget not in ["low", "medium", "high"]:
            print("Invalid budget tier.")
            budget = input("Budget (low / medium / high) [medium]: ").strip().lower() or "medium"

        cuisine = input("Cuisine (e.g., Italian, North Indian, Chinese): ").strip()
        while not cuisine:
            print("Cuisine is required.")
            cuisine = input("Cuisine: ").strip()

        min_rating_str = input("Minimum rating (0.0 - 5.0) [4.0]: ").strip() or "4.0"
        while True:
            try:
                min_rating = float(min_rating_str)
                if 0.0 <= min_rating <= 5.0:
                    break
                print("Rating must be between 0.0 and 5.0.")
            except ValueError:
                print("Please enter a valid number.")
            min_rating_str = input("Minimum rating (0.0 - 5.0) [4.0]: ").strip()

        notes = input("Additional notes (optional, e.g., 'outdoor seating', 'family friendly'): ").strip() or None
    else:
        location = args.location
        budget = args.budget
        cuisine = args.cuisine
        min_rating = args.min_rating
        notes = args.notes

    print(f"\nQuerying recommendations for:")
    print(f"  - Location: {location.title()}")
    print(f"  - Budget  : {budget.upper()}")
    print(f"  - Cuisine : {cuisine.title()}")
    print(f"  - Min Star: {min_rating}★")
    if notes:
        print(f"  - Notes   : {notes}")
    print("\nFetching recommendations (loading dataset & querying AI) ...\n")

    try:
        response = recommend(
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating,
            additional_preferences=notes,
        )

        print("=" * 60)
        print(f"PROVIDER: {response.provider.upper()} | MODEL: {response.model} | LATENCY: {response.latency_ms / 1000:.2f}s")
        print("=" * 60)
        print(f"\nSummary:\n{response.summary}\n")

        if not response.recommendations:
            print("No recommendations found.")
        else:
            print("Top Recommendations:")
            for rec in response.recommendations:
                print("-" * 60)
                print(f"#{rec.rank}  {rec.name}  [ {rec.rating} ]")
                print(f"    Cuisine: {rec.cuisine}")
                print(f"    Cost   : {rec.cost}")
                print(f"\n    AI explanation:\n    \"{rec.explanation}\"")
            print("-" * 60)

        if response.relaxed:
            print(f"\n[Note: Filters were relaxed to find matches. Relaxed: {', '.join(response.relaxed_filters)}]")
        print()

    except Exception as e:
        print(f"\nError running recommendation pipeline: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
