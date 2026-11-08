"""Generator for the row-selector recoloring puzzle ``a85d4709``.

Each row contains a gray selector in column 0, 1, or 2.  The canonical
Racket rule uses the leftmost gray cell's column to choose the whole-row
output color from ``[2, 4, 3]``.  Extra gray cells are lawful only in columns
3 and beyond, where they cannot change the selected column.
"""
from __future__ import annotations

import math
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fda8d5c26728"
VERSION = "4.0.0"
TASK_ID = "fda8d5c26728"
RULE_HASH = "4375f4b46aea"
SUMMARY = (
    "Each row has exactly one gray selector among columns 0, 1, and 2. "
    "The selector column chooses the row's solid output color: column 0 -> "
    "red 2, column 1 -> yellow 4, and column 2 -> green 3. Optional extra "
    "gray decoys may appear only in columns 3 and beyond, so the leftmost "
    "gray cell remains the selector. The default curriculum retains a "
    "substantial exact 3x3, black-background, no-decoy prior while also "
    "varying dimensions, backgrounds, row patterns, and decoy counts."
)

INVARIANTS = [
    "height is 2..18 and width is 3..18",
    "the only input colors are gray 5 and one background from {0,1,6,7,8,9}",
    "every row has exactly one gray selector among columns 0, 1, and 2",
    "all additional gray cells are decoys in columns 3 and beyond",
    "the total number of decoy gray cells is 0..6",
]

SELECTOR_PATTERNS = (
    "canonical",
    "same_column",
    "cycle_012",
    "reverse_cycle",
    "alternating",
    "random_mixed",
)
_CANONICAL_SELECTOR_PROFILES = (
    (0, 1, 0),
    (2, 2, 2),
    (1, 2, 1),
    (2, 1, 0),
    (2, 0, 1),
)
_CANONICAL_PRIOR = {"easy": 0.65, "medium": 0.45, "hard": 0.25}
_ALLOWED_BACKGROUNDS = {0, 1, 6, 7, 8, 9}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "exactly 3 on the canonical prior; otherwise difficulty-aware",
        "valid": "2..18",
    },
    "grid_w": {
        "type": "int",
        "default": "exactly 3 on the canonical prior; otherwise difficulty-aware",
        "valid": "3..18",
    },
    "bg_color": {
        "type": "color",
        "default": "0 on the canonical prior; otherwise keyed random",
        "valid": "0|1|6|7|8|9",
    },
    "selector_pattern": {
        "type": "str",
        "default": "canonical on the exact prior; otherwise keyed random",
        "valid": "canonical|same_column|cycle_012|reverse_cycle|alternating|random_mixed",
    },
    "decoy_count": {
        "type": "int",
        "default": "0 on the canonical prior; otherwise 0..capacity, capped at 6",
        "valid": "0..6",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule remains authority."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    band = difficulty if difficulty in _CANONICAL_PRIOR else "medium"
    canonical_prior = (
        not overrides
        and ctx.draw_rng("scene_family").random() < _CANONICAL_PRIOR[band]
    )

    if canonical_prior:
        # Contract v6 requires keyed provenance even on an early canonical
        # prior.  These singleton draws record every exact returned axis.
        h = ctx.draw_choice("grid_h", [3])
        w = ctx.draw_choice("grid_w", [3])
        bg = ctx.draw_choice("bg_color", [0])
        pattern = ctx.draw_choice("selector_pattern", ["canonical"])
        decoy_count = ctx.draw_choice("decoy_count", [0])
    else:
        requested_decoys = _requested_int(overrides, "decoy_count")
        requested_h = _requested_int(overrides, "grid_h")
        requested_w = _requested_int(overrides, "grid_w")

        # A lone exact decoy-count request must be realizable in every band.
        # When dimensions are also explicit, incompatible combinations are
        # rejected loudly after all exact draws are consumed.
        min_w = 3
        if requested_decoys is not None and requested_h is not None:
            min_w = 3 + math.ceil(requested_decoys / max(1, requested_h))
        elif requested_decoys is not None and requested_w is None:
            min_w = 3 if requested_decoys == 0 else 5
        min_w = min(max(3, min_w), 18)
        w = ctx.draw_int_diff("grid_w", min_w, 18)

        min_h = 2
        if requested_decoys is not None and w > 3:
            min_h = max(2, math.ceil(requested_decoys / (w - 3)))
        min_h = min(max(2, min_h), 18)
        h = ctx.draw_int_diff("grid_h", min_h, 18)

        # Explicit dimension pairs can be globally valid yet jointly unable
        # to fit an explicit decoy count.  Reject the combination rather than
        # silently shrinking the requested quantity.
        if requested_decoys is not None and requested_decoys > h * (w - 3):
            raise ValueError(
                "decoy_count does not fit the requested grid dimensions: "
                f"{requested_decoys} > {h}*({w}-3)"
            )

        bg = ctx.draw_color("bg_color", exclude={2, 3, 4, 5})
        pattern = ctx.draw_choice("selector_pattern", list(SELECTOR_PATTERNS))
        decoy_count = ctx.draw_int("decoy_count", 0, min(6, h * (w - 3)))

    selectors = _selector_columns(
        pattern,
        h,
        ctx.draw_rng("selector_columns"),
    )
    grid = full_grid(h, w, bg)
    for row, selector_col in enumerate(selectors):
        grid[row][selector_col] = 5

    decoy_cells = [(row, col) for row in range(h) for col in range(3, w)]
    if decoy_count > len(decoy_cells):
        raise ValueError(
            f"decoy_count={decoy_count} exceeds capacity {len(decoy_cells)}"
        )
    for row, col in ctx.draw_rng("decoy_cells").sample(decoy_cells, decoy_count):
        grid[row][col] = 5
    return grid


def _requested_int(overrides: dict[str, Any], name: str) -> int | None:
    value = overrides.get(name)
    return None if value is None else int(value)


def _selector_columns(pattern: str, h: int, rng) -> list[int]:
    if pattern == "canonical":
        profile = rng.choice(_CANONICAL_SELECTOR_PROFILES)
        return [profile[row % len(profile)] for row in range(h)]
    if pattern == "same_column":
        selector = rng.choice((0, 1, 2))
        return [selector] * h
    if pattern == "cycle_012":
        return [row % 3 for row in range(h)]
    if pattern == "reverse_cycle":
        return [2 - (row % 3) for row in range(h)]
    if pattern == "alternating":
        left, right = rng.choice(((0, 1), (0, 2), (1, 2)))
        return [left if row % 2 == 0 else right for row in range(h)]
    if pattern == "random_mixed":
        selectors = [rng.choice((0, 1, 2)) for _ in range(h)]
        if h >= 2 and len(set(selectors)) == 1:
            selectors[-1] = (selectors[0] + 1) % 3
        return selectors
    raise ValueError(f"unknown selector_pattern={pattern!r}")


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular and nonempty"]

    h, w = len(grid), width
    if not 2 <= h <= 18:
        errors.append(f"height must be in 2..18, got {h}")
    if not 3 <= w <= 18:
        errors.append(f"width must be in 3..18, got {w}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")

    backgrounds = {value for row in grid for value in row if value != 5}
    bg = next(iter(backgrounds)) if len(backgrounds) == 1 else None
    if len(backgrounds) != 1:
        errors.append(
            "expected exactly one background color besides gray 5, got "
            f"{sorted(backgrounds)}"
        )
    elif bg not in _ALLOWED_BACKGROUNDS:
        errors.append(
            f"background must be one of {sorted(_ALLOWED_BACKGROUNDS)}, got {bg}"
        )

    selectors: list[int] = []
    total_fives = 0
    for row_index, row in enumerate(grid):
        fives = [col for col, value in enumerate(row) if value == 5]
        total_fives += len(fives)
        selector_cells = [col for col in fives if col < 3]
        if len(selector_cells) != 1:
            errors.append(
                f"row {row_index} must have exactly one selector 5 in columns 0..2, "
                f"got {selector_cells}"
            )
            continue
        selector = selector_cells[0]
        if fives and min(fives) != selector:
            errors.append(f"row {row_index} has a gray cell left of its selector")
        selectors.append(selector)

    decoy_count = total_fives - len(selectors)
    if not 0 <= decoy_count <= 6:
        errors.append(f"decoy count must be in 0..6, got {decoy_count}")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "bg_color": bg,
        "decoy_count": decoy_count,
        "selectors": tuple(selectors),
        "selector_histogram": tuple(selectors.count(col) for col in range(3)),
        "selector_unique": len(set(selectors)),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact per-instance axis from returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "bg_color": int(facts["bg_color"]),
        "decoy_count": int(facts["decoy_count"]),
    }


def profile_signature(grid) -> dict[str, Any]:
    """Executable task-linked feature extractor used by the review census."""
    facts, errors = _analyze(grid)
    return {"valid": not errors, "errors": errors, **facts}


def is_canonical_like(grid) -> bool:
    """Strict empirical-manifold predicate, allowing unseen row sequences."""
    facts, errors = _analyze(grid)
    return not errors and (
        facts["grid_h"] == 3
        and facts["grid_w"] == 3
        and facts["bg_color"] == 0
        and facts["decoy_count"] == 0
    )


def canonical_profile_signature(grid) -> tuple[int, ...] | None:
    """Return the selector sequence for strict 3x3 canonical-like inputs."""
    facts, errors = _analyze(grid)
    if errors or not is_canonical_like(grid):
        return None
    return tuple(facts["selectors"])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and verify exact overrides when supplied."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({key: meta[key] for key in AXES if key in meta})
    if facts and requested:
        observed = observe_overrides(grid)
        for axis in ("grid_h", "grid_w", "bg_color", "decoy_count"):
            if axis in requested and observed.get(axis) != requested[axis]:
                errors.append(
                    f"override {axis} requested {requested[axis]!r}, "
                    f"observed {observed.get(axis)!r}"
                )
    return errors
