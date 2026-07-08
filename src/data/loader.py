"""Load the Zomato dataset from Hugging Face."""

from __future__ import annotations

import logging
from typing import Any

from datasets import Dataset, load_dataset

from src.config import settings

logger = logging.getLogger(__name__)

# Canonical mapping: source column → internal name
# Adjusted after inspecting the actual Hugging Face dataset schema.
COLUMN_MAP: dict[str, str] = {
    "name": "name",
    "location": "area",  # neighborhood within the city
    "listed_in(city)": "city",  # the city itself
    "cuisines": "cuisines",
    "approx_cost(for two people)": "cost_for_two",
    "rate": "rate",
    "votes": "votes",
    "address": "address",
    "rest_type": "rest_type",
    "dish_liked": "dish_liked",
    "online_order": "online_order",
    "book_table": "book_table",
    "listed_in(type)": "listed_in_type",
    "url": "url",
    "phone": "phone",
    "reviews_list": "reviews_list",
    "menu_item": "menu_item",
}


def load_raw_dataset(
    dataset_name: str | None = None,
    split: str = "train",
) -> list[dict[str, Any]]:
    """Load the Hugging Face dataset and return raw rows as dicts.

    Args:
        dataset_name: Override for the Hugging Face dataset identifier.
            Defaults to ``settings.huggingface_dataset_name``.
        split: Dataset split to load (default ``"train"``).

    Returns:
        A list of raw record dictionaries with original column names.

    Raises:
        RuntimeError: If the dataset cannot be downloaded or loaded.
    """
    name = dataset_name or settings.huggingface_dataset_name
    logger.info("Loading dataset '%s' (split=%s) …", name, split)

    try:
        ds: Dataset = load_dataset(name, split=split)
    except Exception as exc:
        raise RuntimeError(f"Failed to load dataset '{name}': {exc}") from exc

    logger.info("Dataset loaded: %d rows, columns=%s", len(ds), ds.column_names)

    rows: list[dict[str, Any]] = []
    for row in ds:
        rows.append(dict(row))

    logger.info("Converted %d rows to dicts.", len(rows))
    return rows


def get_column_names(dataset_name: str | None = None, split: str = "train") -> list[str]:
    """Return the column names of the Hugging Face dataset without downloading all rows.

    Useful for schema inspection during development.
    """
    name = dataset_name or settings.huggingface_dataset_name
    try:
        ds: Dataset = load_dataset(name, split=split, streaming=True)
        # Grab one row to inspect keys
        first = next(iter(ds))
        return list(first.keys())
    except Exception as exc:
        raise RuntimeError(f"Failed to inspect dataset '{name}': {exc}") from exc
