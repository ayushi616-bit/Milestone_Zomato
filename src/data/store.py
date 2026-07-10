"""In-memory store for preprocessed restaurant records.

The store lazily loads and preprocesses the Hugging Face dataset on first access,
then caches the result for the lifetime of the application session.

Usage::

    from src.data.store import get_restaurants, get_locations, get_cuisines

    restaurants = get_restaurants()   # list[Restaurant], cached after first call
    locations   = get_locations()     # sorted unique locations for UI dropdowns
    cuisines    = get_cuisines()      # sorted unique cuisines for UI dropdowns
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from src.data.loader import load_raw_dataset
from src.data.models import Restaurant
from src.data.preprocessor import preprocess_records

logger = logging.getLogger(__name__)

# Module-level cache — populated on first call to ``_load_and_preprocess``.
_cache: list[Restaurant] | None = None


def _load_and_preprocess() -> list[Restaurant]:
    """Load raw dataset and run the preprocessor; cache the result."""
    global _cache
    if _cache is not None:
        return _cache

    # Check for local preprocessed JSON cache first
    import json
    from pathlib import Path
    from src.data.models import CostBucket

    json_path = Path(__file__).resolve().parent / "zomato_preprocessed.json"
    if json_path.exists():
        logger.info("Loading preprocessed dataset from local JSON cache: %s", json_path)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            _cache = []
            for item in data:
                _cache.append(
                    Restaurant(
                        id=item["id"],
                        name=item["name"],
                        location=item["location"],
                        cuisines=item["cuisines"],
                        cost_for_two=item["cost_for_two"],
                        cost_bucket=CostBucket(item["cost_bucket"]),
                        rating=item["rating"],
                        metadata=item["metadata"]
                    )
                )
            logger.info("Dataset ready: %d restaurants loaded from local JSON cache.", len(_cache))
            return _cache
        except Exception as e:
            logger.warning("Failed to load local JSON cache, falling back to Hugging Face: %s", e)

    logger.info("Cache miss — loading and preprocessing dataset …")
    raw_rows: list[dict[str, Any]] = load_raw_dataset()
    _cache = preprocess_records(raw_rows)
    logger.info("Dataset ready: %d restaurants cached.", len(_cache))
    return _cache


def get_restaurants() -> list[Restaurant]:
    """Return the full list of preprocessed ``Restaurant`` objects.

    The dataset is loaded from Hugging Face and preprocessed on the first call.
    Subsequent calls return the cached list without re-downloading.
    """
    return _load_and_preprocess()


def get_locations() -> list[str]:
    """Return a sorted list of unique locations (for UI dropdowns)."""
    restaurants = get_restaurants()
    return sorted({r.location for r in restaurants if r.location})


def get_cuisines() -> list[str]:
    """Return a sorted list of unique cuisine tags (for UI dropdowns)."""
    restaurants = get_restaurants()
    cuisines: set[str] = set()
    for r in restaurants:
        cuisines.update(r.cuisines)
    return sorted(cuisines)


def reset_cache() -> None:
    """Clear the in-memory cache.  Primarily useful for tests."""
    global _cache
    _cache = None
    logger.info("Restaurant cache cleared.")
