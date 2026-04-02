from __future__ import annotations

from typing import Any, Mapping

from ..rng import RandomManager


def weighted_pick(
    weighted_items: Mapping[str, Any],
    fallback_value: str,
    rng: RandomManager,
) -> str:
    if weighted_items:
        items = [str(name) for name in weighted_items.keys()]
        weights = [float(value) for value in weighted_items.values()]
        return str(rng.weighted_choice(items, weights))
    return fallback_value
