#!/usr/bin/env python3
"""CLI smoke test: accept preferences, filter restaurants, print candidate JSON.

Run from the project root::

    python -m scripts.filter_smoke_test --location koramangala --budget medium --cuisine italian --min-rating 4.0

No LLM calls are made in this script — it only tests the filter pipeline.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path so ``src`` is importable.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data.store import get_restaurants
from src.filters.filter_engine import CandidateBuilder, FilterEngine
from src.validators import ValidationError, validate_preferences


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter smoke test — no LLM calls.")
    parser.add_argument("--location", default="koramangala", help="Location / area")
    parser.add_argument("--budget", default="medium", help="Budget tier: low / medium / high")
    parser.add_argument("--cuisine", default="italian", help="Cuisine (comma-separated for multiple)")
    parser.add_argument("--min-rating", type=float, default=3.5, help="Minimum rating (0–5)")
    parser.add_argument("--additional", default=None, help="Optional free-text preferences")
    parser.add_argument("--cap", type=int, default=20, help="Max candidates to display")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # ── Validate ──────────────────────────────────────────────────────────
    print("=" * 60)
    print("  Filter Smoke Test")
    print("=" * 60)
    print(f"\n  Input:")
    print(f"    Location  : {args.location}")
    print(f"    Budget    : {args.budget}")
    print(f"    Cuisine   : {args.cuisine}")
    print(f"    Min Rating: {args.min_rating}")
    if args.additional:
        print(f"    Notes     : {args.additional}")

    try:
        prefs = validate_preferences(
            location=args.location,
            budget=args.budget,
            cuisine=args.cuisine,
            min_rating=args.min_rating,
            additional_preferences=args.additional,
        )
    except ValidationError as e:
        print(f"\n  Validation error: {e}")
        sys.exit(1)

    # ── Load dataset ──────────────────────────────────────────────────────
    print("\n  Loading dataset …")
    t0 = time.time()
    restaurants = get_restaurants()
    load_ms = (time.time() - t0) * 1000
    print(f"  Loaded {len(restaurants):,} restaurants ({load_ms:.0f} ms)")

    # ── Filter ────────────────────────────────────────────────────────────
    print("\n  Applying filters …")
    t0 = time.time()
    engine = FilterEngine()
    result = engine.apply(restaurants, prefs)
    filter_ms = (time.time() - t0) * 1000

    print(f"  Filter took {filter_ms:.1f} ms")
    print(f"  Stages: {result.stages}")
    if result.relaxed:
        print(f"  ⚠ Relaxed filters: {result.relaxed_filters}")

    if not result.candidates:
        print("\n  No candidates found. Try broadening your criteria.")
        sys.exit(0)

    # ── Build candidates ──────────────────────────────────────────────────
    builder = CandidateBuilder(cap=args.cap)
    candidates = builder.build(result.candidates)
    print(f"\n  Candidates: {len(candidates)} (capped at {args.cap})")

    # ── Display ───────────────────────────────────────────────────────────
    print("\n  Top candidates (JSON):")
    print("-" * 60)
    json_output = builder.to_json(candidates)
    print(json_output)
    print("-" * 60)

    # ── Summary table ─────────────────────────────────────────────────────
    print("\n  Summary:")
    print(f"  {'#':>3}  {'Rating':>6}  {'Cost':>7}  {'Name':<30}  Cuisines")
    print(f"  {'─'*3}  {'─'*6}  {'─'*7}  {'─'*30}  {'─'*30}")
    for i, r in enumerate(candidates, 1):
        cost = f"₹{r.cost_for_two}" if r.cost_for_two else r.cost_bucket.value
        cuisines = ", ".join(r.cuisines[:3])
        print(f"  {i:>3}  {r.rating:>5.1f}★  {cost:>7}  {r.name:<30}  {cuisines}")

    print("\n" + "=" * 60)
    print("  Done. (No LLM calls were made.)")
    print("=" * 60)


if __name__ == "__main__":
    main()
