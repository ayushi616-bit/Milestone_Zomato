"""Preprocess raw Zomato dataset records into normalized Restaurant domain objects.

Normalization rules (Architecture §5.4):
- Location: lowercase, trim, alias map (e.g. Bengaluru → Bangalore)
- Cuisine: split comma-separated, lowercase, deduplicate
- Cost: strip commas, parse int, derive LOW / MEDIUM / HIGH bucket
- Rating: parse "X.X/5" string → float; handle "NEW", "-", null
- Name: trim, preserve original
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from src.config import settings
from src.data.models import CostBucket, Restaurant

logger = logging.getLogger(__name__)

# ── Location aliases ─────────────────────────────────────────────────────────
# Map common alternate spellings / old city names → canonical form.
# Applied to both the city-level and area-level location fields.
LOCATION_ALIASES: dict[str, str] = {
    "bengaluru": "bangalore",
    "banglore": "bangalore",
    "bangalore": "bangalore",
    "new delhi": "delhi",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "chennai": "chennai",
    "madras": "chennai",
    "kolkata": "kolkata",
    "calcutta": "kolkata",
    "hyderabad": "hyderabad",
    "pune": "pune",
}


# ── Public API ───────────────────────────────────────────────────────────────


def preprocess_records(
    raw_rows: list[dict[str, Any]],
    *,
    drop_no_name: bool = True,
    default_rating: float = 0.0,
) -> list[Restaurant]:
    """Convert raw dataset rows into normalized ``Restaurant`` objects.

    Args:
        raw_rows: List of raw record dicts as returned by :func:`loader.load_raw_dataset`.
        drop_no_name: If ``True``, rows with empty/missing names are dropped.
        default_rating: Fallback rating when the source value is missing or invalid.

    Returns:
        A list of fully-normalized ``Restaurant`` instances.
    """
    restaurants: list[Restaurant] = []
    dropped = 0

    for idx, row in enumerate(raw_rows):
        # ── Name ─────────────────────────────────────────────────────────
        name = _clean_string(row.get("name"))
        if not name:
            if drop_no_name:
                dropped += 1
                continue
            name = "Unknown"

        # ── Location (city-level from listed_in(city)) ───────────────────
        raw_city = _clean_string(row.get("listed_in(city)"))
        raw_area = _clean_string(row.get("location"))
        location = _normalize_location(raw_city or raw_area or "")

        if not location:
            # Fall back to area if city is also empty
            location = _normalize_location(raw_area or "unknown")

        # ── Cuisines ─────────────────────────────────────────────────────
        cuisines = _parse_cuisines(row.get("cuisines"))

        # ── Cost for two ─────────────────────────────────────────────────
        cost_for_two = _parse_cost(row.get("approx_cost(for two people)"))
        cost_bucket = _derive_cost_bucket(cost_for_two)

        # ── Rating ───────────────────────────────────────────────────────
        rating = _parse_rating(row.get("rate"), default_rating)

        # ── Stable ID ────────────────────────────────────────────────────
        stable_id = _generate_id(row, idx)

        # ── Metadata ─────────────────────────────────────────────────────
        metadata = _build_metadata(row)

        restaurants.append(
            Restaurant(
                id=stable_id,
                name=name,
                location=location,
                cuisines=cuisines,
                cost_for_two=cost_for_two,
                cost_bucket=cost_bucket,
                rating=rating,
                metadata=metadata,
            )
        )

    logger.info(
        "Preprocessed %d → %d restaurants (dropped %d).",
        len(raw_rows),
        len(restaurants),
        dropped,
    )
    return restaurants


# ── Normalization helpers ─────────────────────────────────────────────────────


def _clean_string(value: Any) -> str:
    """Return a trimmed string, or empty string for None / non-string values."""
    if value is None:
        return ""
    return str(value).strip()


def _normalize_location(raw: str) -> str:
    """Lowercase, trim, and apply alias mapping to a location string."""
    if not raw:
        return ""
    normalized = raw.lower().strip()
    return LOCATION_ALIASES.get(normalized, normalized)


def _parse_cuisines(raw: Any) -> list[str]:
    """Parse a comma-separated cuisine string into a deduplicated lowercase list."""
    if raw is None or not str(raw).strip():
        return []
    parts = str(raw).split(",")
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        cuisine = part.strip().lower()
        if cuisine and cuisine not in seen:
            seen.add(cuisine)
            result.append(cuisine)
    return result


def _parse_cost(raw: Any) -> int | None:
    """Parse a cost string (possibly with commas) into an integer, or None."""
    if raw is None:
        return None
    cleaned = str(raw).replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = int(float(cleaned))
        return value if value >= 0 else None
    except (ValueError, TypeError):
        return None


def _derive_cost_bucket(cost_for_two: int | None) -> CostBucket:
    """Map a numeric cost to LOW / MEDIUM / HIGH / UNKNOWN using config thresholds."""
    if cost_for_two is None:
        return CostBucket.UNKNOWN
    if cost_for_two <= settings.cost_low_max:
        return CostBucket.LOW
    if cost_for_two <= settings.cost_medium_max:
        return CostBucket.MEDIUM
    return CostBucket.HIGH


def _parse_rating(raw: Any, default: float = 0.0) -> float:
    """Parse a rating string like '4.1/5' into a float.

    Handles:
    - Standard format: "4.1/5" → 4.1
    - Plain numeric: "4.1" → 4.1
    - Special values: "NEW", "-", None → ``default``
    - Out-of-range values are clamped to [0.0, 5.0].
    """
    if raw is None:
        return default

    text = str(raw).strip()
    if not text or text.upper() in ("NEW", "-", "NAN", ""):
        return default

    # Handle "X.X/5" format
    if "/" in text:
        try:
            numerator = text.split("/")[0].strip()
            value = float(numerator)
        except (ValueError, IndexError):
            return default
    else:
        try:
            value = float(text)
        except (ValueError, TypeError):
            return default

    # Clamp to valid range
    return max(0.0, min(5.0, value))


def _generate_id(row: dict[str, Any], index: int) -> str:
    """Generate a stable identifier from the row content + index.

    Uses a short hash of name + location + url to produce a deterministic ID
    that stays consistent across reloads (as long as dataset order is stable).
    """
    key = f"{row.get('name', '')}|{row.get('listed_in(city)', row.get('location', ''))}|{index}"
    short_hash = hashlib.md5(key.encode()).hexdigest()[:8]
    return f"r_{short_hash}"


def _build_metadata(row: dict[str, Any]) -> dict[str, Any]:
    """Extract supplementary fields for LLM context."""
    meta: dict[str, Any] = {}

    address = _clean_string(row.get("address"))
    if address:
        meta["address"] = address

    rest_type = _clean_string(row.get("rest_type"))
    if rest_type:
        meta["rest_type"] = rest_type

    dish_liked = _clean_string(row.get("dish_liked"))
    if dish_liked:
        meta["dish_liked"] = dish_liked

    votes = row.get("votes")
    if votes is not None:
        try:
            meta["votes"] = int(votes)
        except (ValueError, TypeError):
            pass

    online_order = _clean_string(row.get("online_order"))
    if online_order:
        meta["online_order"] = online_order

    book_table = _clean_string(row.get("book_table"))
    if book_table:
        meta["book_table"] = book_table

    listed_type = _clean_string(row.get("listed_in(type)"))
    if listed_type:
        meta["listed_in_type"] = listed_type

    area = _clean_string(row.get("location"))
    if area:
        meta["area"] = area

    return meta
