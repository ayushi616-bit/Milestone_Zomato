"""Build structured prompts for the LLM recommendation engine.

Constructs system and user prompts containing:
- User preferences (location, budget, cuisine, rating, free-text)
- Candidate restaurant list (JSON)
- Required output JSON schema

Architecture reference: §11 (Prompt Design Strategy)
"""

from __future__ import annotations

import json
from typing import Any

from src.config import settings
from src.data.models import Restaurant, UserPreferences

# ── Output JSON schema definition ────────────────────────────────────────────

LLM_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A brief overall summary of the recommendation set (1-2 sentences).",
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "string",
                        "description": "The ID of the restaurant from the candidate list.",
                    },
                    "rank": {
                        "type": "integer",
                        "description": "Rank position (1 = best match).",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "A concise reason why this restaurant matches the user's preferences (1-2 sentences).",
                    },
                },
                "required": ["restaurant_id", "rank", "explanation"],
            },
        },
    },
    "required": ["summary", "recommendations"],
}

# ── Prompt templates ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a restaurant recommendation assistant. You rank and explain restaurants \
ONLY from the provided candidate list. Do not invent restaurants that are not in \
the candidate list. Always output valid JSON matching the specified schema.

Guidelines:
- Rank restaurants by how well they match the user's stated preferences.
- Provide a concise, helpful explanation for each recommendation (1-2 sentences).
- Consider the user's budget, cuisine preference, minimum rating, and any \
additional notes when ranking.
- If the user mentioned additional preferences (e.g., "family-friendly", \
"quick service"), factor those into your ranking and explanations.
- Return exactly {top_k} recommendations (or fewer if the candidate list is smaller).
- Output ONLY valid JSON — no markdown, no commentary outside the JSON.\
"""

USER_PROMPT_TEMPLATE = """\
User preferences:
- Location: {location}
- Budget: {budget}
- Cuisine: {cuisine}
- Minimum rating: {min_rating}
- Additional preferences: {additional_preferences}

Candidates (JSON):
{candidates_json}

Tasks:
1. Rank the top {top_k} restaurants by fit to the user's preferences.
2. Explain why each matches (1-2 sentences each).
3. Provide a brief overall summary.

Output JSON schema:
{schema_json}\
"""


# ── Public API ────────────────────────────────────────────────────────────────


def build_system_prompt(top_k: int | None = None) -> str:
    """Return the system prompt for the LLM.

    Args:
        top_k: Number of recommendations to request. Defaults to ``settings.top_k_recommendations``.
    """
    k = top_k or settings.top_k_recommendations
    return SYSTEM_PROMPT.format(top_k=k)


def build_user_prompt(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    top_k: int | None = None,
) -> str:
    """Build the user prompt with preferences, candidate JSON, and output schema.

    Args:
        preferences: Validated user preferences.
        candidates: Filtered and capped candidate restaurants.
        top_k: Number of recommendations to request. Defaults to ``settings.top_k_recommendations``.

    Returns:
        A fully-formed user prompt string.
    """
    k = top_k or settings.top_k_recommendations

    # Serialize candidates to compact JSON for the prompt
    candidates_data = _serialize_candidates(candidates)
    candidates_json = json.dumps(candidates_data, ensure_ascii=False, indent=2)

    # Format cuisine preference for display
    cuisine_list = preferences.cuisines_list()
    cuisine_str = ", ".join(cuisine_list) if cuisine_list else "any"

    # Additional preferences
    additional = preferences.additional_preferences or "none"

    # Schema
    schema_json = json.dumps(LLM_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)

    return USER_PROMPT_TEMPLATE.format(
        location=preferences.location,
        budget=preferences.budget.value,
        cuisine=cuisine_str,
        min_rating=preferences.min_rating,
        additional_preferences=additional,
        candidates_json=candidates_json,
        top_k=k,
        schema_json=schema_json,
    )


def build_messages(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    top_k: int | None = None,
) -> list[dict[str, str]]:
    """Build the full message list for the LLM API call.

    Returns a list of ``{"role": ..., "content": ...}`` dicts suitable
    for the OpenAI chat completions API.
    """
    return [
        {"role": "system", "content": build_system_prompt(top_k)},
        {"role": "user", "content": build_user_prompt(preferences, candidates, top_k)},
    ]


# ── Internal helpers ──────────────────────────────────────────────────────────


def _serialize_candidates(candidates: list[Restaurant]) -> list[dict[str, Any]]:
    """Convert candidates to compact dicts for prompt inclusion."""
    result: list[dict[str, Any]] = []
    for r in candidates:
        entry: dict[str, Any] = {
            "id": r.id,
            "name": r.name,
            "cuisines": r.cuisines,
            "rating": r.rating,
            "cost_bucket": r.cost_bucket.value,
        }
        if r.cost_for_two is not None:
            entry["cost_for_two"] = r.cost_for_two
        result.append(entry)
    return result
