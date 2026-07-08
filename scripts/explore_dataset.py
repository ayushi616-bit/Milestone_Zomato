#!/usr/bin/env python3
"""Explore the Zomato dataset: print schema, sample rows, unique locations & cuisines.

Run from the project root::

    python -m scripts.explore_dataset
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so ``src`` is importable.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data.loader import load_raw_dataset
from src.data.preprocessor import preprocess_records


def main() -> None:
    print("=" * 60)
    print("  Zomato Dataset Explorer")
    print("=" * 60)

    # ── Load raw rows ────────────────────────────────────────────────────
    print("\n[1/4] Loading raw dataset from Hugging Face …")
    raw_rows = load_raw_dataset()
    print(f"      Total rows: {len(raw_rows)}")

    if not raw_rows:
        print("      No rows found — aborting.")
        return

    # ── Schema ───────────────────────────────────────────────────────────
    print("\n[2/4] Column names:")
    for col in raw_rows[0].keys():
        print(f"      • {col}")

    # ── Sample rows ──────────────────────────────────────────────────────
    print("\n[3/4] First 3 raw rows (selected fields):")
    display_fields = ["name", "listed_in(city)", "location", "cuisines",
                      "approx_cost(for two people)", "rate"]
    for i, row in enumerate(raw_rows[:3]):
        print(f"\n      Row {i}:")
        for field in display_fields:
            val = row.get(field, "<missing>")
            # Truncate long values
            val_str = str(val)
            if len(val_str) > 80:
                val_str = val_str[:80] + "…"
            print(f"        {field:40s} → {val_str}")

    # ── Preprocess and summarize ─────────────────────────────────────────
    print("\n[4/4] Preprocessing …")
    restaurants = preprocess_records(raw_rows)
    print(f"      Valid restaurants: {len(restaurants)}")

    locations = sorted({r.location for r in restaurants if r.location})
    print(f"\n      Unique locations ({len(locations)}):")
    for loc in locations:
        print(f"        • {loc}")

    cuisines: set[str] = set()
    for r in restaurants:
        cuisines.update(r.cuisines)
    cuisines_sorted = sorted(cuisines)
    print(f"\n      Unique cuisines ({len(cuisines_sorted)}):")
    for c in cuisines_sorted[:50]:
        print(f"        • {c}")
    if len(cuisines_sorted) > 50:
        print(f"        … and {len(cuisines_sorted) - 50} more")

    # ── Cost bucket distribution ─────────────────────────────────────────
    from collections import Counter
    bucket_counts = Counter(r.cost_bucket.value for r in restaurants)
    print("\n      Cost bucket distribution:")
    for bucket in ["low", "medium", "high", "unknown"]:
        print(f"        {bucket:10s}: {bucket_counts.get(bucket, 0):,}")

    # ── Rating distribution ──────────────────────────────────────────────
    ratings = [r.rating for r in restaurants]
    nonzero = [r for r in ratings if r > 0.0]
    print(f"\n      Rating stats (excl. 0.0 defaults):")
    print(f"        Count : {len(nonzero):,}")
    if nonzero:
        print(f"        Min   : {min(nonzero):.1f}")
        print(f"        Max   : {max(nonzero):.1f}")
        print(f"        Mean  : {sum(nonzero) / len(nonzero):.2f}")

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
