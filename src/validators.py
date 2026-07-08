"""Validate and normalize user preference input before filtering.

The validator converts raw user input (strings from a form or CLI) into a
validated ``UserPreferences`` domain object, raising ``ValueError`` on invalid input.

Usage::

    from src.validators import validate_preferences

    prefs = validate_preferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )
"""

from __future__ import annotations

from src.config import settings
from src.data.models import Budget, UserPreferences


class ValidationError(ValueError):
    """Raised when user input fails validation.

    Attributes:
        field: The name of the field that failed validation.
        message: A human-readable error description.
    """

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"[{field}] {message}")


def validate_preferences(
    location: str,
    budget: str | Budget,
    cuisine: str | list[str],
    min_rating: float | str | int,
    additional_preferences: str | None = None,
) -> UserPreferences:
    """Validate raw user input and return a ``UserPreferences`` object.

    Args:
        location: City or area name (required, non-empty).
        budget: Budget tier as a string ("low", "medium", "high") or ``Budget`` enum.
        cuisine: One or more cuisine names (string or list).
        min_rating: Minimum acceptable rating (0.0 – 5.0).
        additional_preferences: Optional free-text preferences.

    Returns:
        A validated ``UserPreferences`` instance.

    Raises:
        ValidationError: If any field fails validation.
    """
    # ── Location ──────────────────────────────────────────────────────────
    location = _validate_location(location)

    # ── Budget ────────────────────────────────────────────────────────────
    budget_enum = _validate_budget(budget)

    # ── Cuisine ───────────────────────────────────────────────────────────
    cuisine_clean = _validate_cuisine(cuisine)

    # ── Min rating ────────────────────────────────────────────────────────
    rating_float = _validate_min_rating(min_rating)

    # ── Additional preferences ────────────────────────────────────────────
    additional = _validate_additional(additional_preferences)

    return UserPreferences(
        location=location,
        budget=budget_enum,
        cuisine=cuisine_clean,
        min_rating=rating_float,
        additional_preferences=additional,
    )


# ── Field validators ──────────────────────────────────────────────────────────


def _validate_location(raw: str) -> str:
    """Normalize and validate the location field."""
    if not isinstance(raw, str):
        raise ValidationError("location", "Must be a string.")
    cleaned = raw.strip().lower()
    if not cleaned:
        raise ValidationError("location", "Location is required and cannot be empty.")
    return cleaned


def _validate_budget(raw: str | Budget) -> Budget:
    """Convert a budget string or enum to a validated ``Budget`` enum."""
    if isinstance(raw, Budget):
        return raw

    if not isinstance(raw, str):
        raise ValidationError("budget", f"Must be a string or Budget enum, got {type(raw).__name__}.")

    cleaned = raw.strip().lower()
    if not cleaned:
        raise ValidationError("budget", "Budget is required.")

    valid_values = {b.value for b in Budget}
    if cleaned not in valid_values:
        raise ValidationError(
            "budget",
            f"Invalid budget '{cleaned}'. Must be one of: {', '.join(sorted(valid_values))}.",
        )
    return Budget(cleaned)


def _validate_cuisine(raw: str | list[str]) -> str | list[str]:
    """Validate and normalize cuisine input."""
    if isinstance(raw, list):
        cleaned = [c.strip() for c in raw if isinstance(c, str) and c.strip()]
        if not cleaned:
            raise ValidationError("cuisine", "At least one cuisine is required.")
        # Lowercase each entry
        result = [c.lower() for c in cleaned]
        return result if len(result) > 1 else result[0]

    if isinstance(raw, str):
        cleaned = raw.strip()
        if not cleaned:
            raise ValidationError("cuisine", "Cuisine is required and cannot be empty.")
        # If comma-separated, split into list
        if "," in cleaned:
            parts = [c.strip().lower() for c in cleaned.split(",") if c.strip()]
            if not parts:
                raise ValidationError("cuisine", "At least one cuisine is required.")
            return parts if len(parts) > 1 else parts[0]
        return cleaned.lower()

    raise ValidationError("cuisine", f"Must be a string or list, got {type(raw).__name__}.")


def _validate_min_rating(raw: float | str | int) -> float:
    """Validate rating is a float in [0.0, 5.0]."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValidationError("min_rating", f"Must be a number, got {raw!r}.")

    if value < 0.0 or value > 5.0:
        raise ValidationError(
            "min_rating",
            f"Rating must be between 0.0 and 5.0, got {value}.",
        )
    return value


def _validate_additional(raw: str | None) -> str | None:
    """Validate optional free-text preferences."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ValidationError(
            "additional_preferences",
            f"Must be a string or None, got {type(raw).__name__}.",
        )
    cleaned = raw.strip()
    if not cleaned:
        return None

    max_chars = settings.max_additional_preferences_chars
    if len(cleaned) > max_chars:
        raise ValidationError(
            "additional_preferences",
            f"Must be at most {max_chars} characters, got {len(cleaned)}.",
        )
    return cleaned
