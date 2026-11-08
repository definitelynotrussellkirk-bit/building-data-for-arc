"""Input generator for normalized overlap overlay (M102).

The canonical Racket rule sorts the two non-background colors, normalizes each
4-connected component to the top-left of its own bounding box, then overlays
the normalized cells.  Shared cells become 9; cells unique to either component
keep that component's color.

This sampler reserves color 9 for the output marker and exposes only controls
that can be recovered exactly from returned pixels.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "659980b6f715"
TASK_ID = GENERATOR_ID
RULE_HASH = "df22257022fe"
VERSION = "4.0.0"
SUMMARY = (
    "A zero-background 8..10 by 11..13 grid contains two horizontally "
    "separated, 4-connected colored polyominoes. Color 9 is reserved for the "
    "output. Normalize each colored component independently to its bounding-"
    "box origin, overlay the normalized sets, paint shared cells 9, and retain "
    "each original color on cells unique to that component."
)

INVARIANTS = [
    "exactly two 4-connected non-background components, neither colored 9",
    "each component has 4..8 cells and the physical bounding boxes are horizontally separated",
    "the component top rows differ, so independent normalization is observable",
    "normalized components overlap and each also has at least one unique cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "11..13"},
    "low_color_cells": {"type": "int", "default": "schedule 4..8", "valid": "4..8"},
    "high_color_cells": {"type": "int", "default": "schedule 4..8", "valid": "4..8"},
    "row_order": {
        "type": "str",
        "default": "alternating",
        "valid": "low_above|high_above",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Prefixes remain connected.  Every low prefix contains (0,2) but not (2,0),
# every high prefix contains (2,0) but not (0,2), and both contain the three-
# cell corner at the origin.  Thus every 4..8 x 4..8 pairing has a nonempty
# normalized intersection and unique cells on both sides without rejection.
_LOW_PATH = (
    (0, 0), (0, 1), (1, 0), (0, 2),
    (0, 3), (1, 3), (1, 2), (1, 1),
)
_HIGH_PATH = (
    (0, 0), (1, 0), (0, 1), (2, 0),
    (3, 0), (3, 1), (2, 1), (1, 1),
)
_CANONICAL_DIMENSION_PROFILES = ((8, 12), (9, 11), (10, 12), (9, 13))
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_ROW_ORDERS = ("low_above", "high_above")


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    cleaned = {name: value for name, value in overrides.items() if value is not None}
    for name in ("grid_h", "grid_w", "low_color_cells", "high_color_cells"):
        if name not in cleaned:
            continue
        value = cleaned[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    bounds = {
        "grid_h": (8, 10),
        "grid_w": (11, 13),
        "low_color_cells": (4, 8),
        "high_color_cells": (4, 8),
    }
    for name, (lo, hi) in bounds.items():
        if name in cleaned and not lo <= cleaned[name] <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    if "row_order" in cleaned:
        value = cleaned["row_order"]
        if type(value) is not str or value not in _ROW_ORDERS:
            raise ValueError("row_order must be 'low_above' or 'high_above'")
    return cleaned


def _normalize(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cells = set(cells)
    if not cells:
        raise ValueError("cannot normalize an empty cell set")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _transform(cells: Iterable[tuple[int, int]], code: int) -> set[tuple[int, int]]:
    transformed = []
    for r, c in cells:
        variants = (
            (r, c), (c, -r), (-r, -c), (-c, r),
            (r, -c), (c, r), (-r, c), (-c, -r),
        )
        transformed.append(variants[code])
    return _normalize(transformed)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = set(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    pending = list(seen)
    while pending:
        r, c = pending.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def _grid_structure(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["grid values must be integers 0..9 (not bool)"]

    h, w = len(grid), width
    errors = []
    if not 8 <= h <= 10:
        errors.append(f"grid height {h} is outside 8..10")
    if not 11 <= w <= 13:
        errors.append(f"grid width {w} is outside 11..13")

    all_nonzero = {value for row in grid for value in row if value != 0}
    if 9 in all_nonzero:
        errors.append("input color 9 is reserved for the output overlap marker")
    colors = sorted(all_nonzero)
    if len(colors) != 2:
        errors.append(f"expected exactly two non-background colors, found {colors}")
        return None, errors

    low, high = colors
    cells = {
        color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        for color in colors
    }
    for color in colors:
        if not 4 <= len(cells[color]) <= 8:
            errors.append(f"color {color} must contain 4..8 cells, found {len(cells[color])}")
        if not _connected(cells[color]):
            errors.append(f"color {color} must form one 4-connected component")

    boxes = {color: _bbox(cells[color]) for color in colors}
    low_box, high_box = boxes[low], boxes[high]
    horizontally_separated = low_box[3] < high_box[1] or high_box[3] < low_box[1]
    if not horizontally_separated:
        errors.append("component bounding boxes must be horizontally separated")
    if low_box[0] == high_box[0]:
        errors.append("component top rows must differ so independent normalization is visible")

    normalized = {color: _normalize(cells[color]) for color in colors}
    a, b = normalized[low], normalized[high]
    if not a & b:
        errors.append("normalized components must share at least one cell")
    if not a - b:
        errors.append("lower-color normalized component needs a unique cell")
    if not b - a:
        errors.append("higher-color normalized component needs a unique cell")

    info = {
        "height": h,
        "width": w,
        "colors": colors,
        "cells": cells,
        "boxes": boxes,
        "normalized": normalized,
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural errors for canonical-like generator inputs."""
    _info, errors = _grid_structure(grid)
    return errors


def strict_canonical_like(grid):
    """The strict manifold is exactly the documented, canonical-supported domain."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    offset = _BAND_OFFSET[difficulty]
    scheduled_h, scheduled_w = _CANONICAL_DIMENSION_PROFILES[(sample_index + offset) % 4]
    scheduled_low_n = 4 + ((sample_index + offset) % 5)
    scheduled_high_n = 4 + ((2 * sample_index + offset + 1) % 5)
    scheduled_order = _ROW_ORDERS[(sample_index + offset) % 2]

    # Singleton proposals encode the deterministic curriculum.  Explicit
    # controls are checked against the complete advertised domain before GenCtx
    # records them, so every exact override remains usable.
    def choose(name, scheduled, domain):
        return ctx.draw_choice(name, domain if name in overrides else (scheduled,))

    h = choose("grid_h", scheduled_h, tuple(range(8, 11)))
    w = choose("grid_w", scheduled_w, tuple(range(11, 14)))
    low_n = choose("low_color_cells", scheduled_low_n, tuple(range(4, 9)))
    high_n = choose("high_color_cells", scheduled_high_n, tuple(range(4, 9)))
    row_order = choose("row_order", scheduled_order, _ROW_ORDERS)

    rng = ctx.draw_rng("layout")
    low_color, high_color = sorted(rng.sample(list(range(1, 9)), 2))
    transform_code = rng.randrange(8)
    low_shape = _transform(_LOW_PATH[:low_n], transform_code)
    high_shape = _transform(_HIGH_PATH[:high_n], transform_code)

    low_height = 1 + max(r for r, _ in low_shape)
    low_width = 1 + max(c for _, c in low_shape)
    high_height = 1 + max(r for r, _ in high_shape)
    high_width = 1 + max(c for _, c in high_shape)

    if row_order == "low_above":
        low_r = rng.randint(0, 1)
        high_r = h - high_height - rng.randint(0, 1)
    else:
        high_r = rng.randint(0, 1)
        low_r = h - low_height - rng.randint(0, 1)

    low_left = bool(rng.randrange(2))
    if low_left:
        low_c = rng.randint(0, 1)
        high_c = w - high_width - rng.randint(0, 1)
    else:
        high_c = rng.randint(0, 1)
        low_c = w - low_width - rng.randint(0, 1)

    # The smallest canvas is 11 columns and both shapes are at most 4 columns,
    # so the chosen edge bands leave at least one blank separator column.
    grid = full_grid(h, w, 0)
    for r, c in low_shape:
        grid[low_r + r][low_c + c] = low_color
    for r, c in high_shape:
        grid[high_r + r][high_c + c] = high_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator violated its contract: " + "; ".join(errors))
    return grid


def observe_overrides(grid):
    """Recover every advertised exact control from the returned pixels."""
    info, errors = _grid_structure(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    low, high = info["colors"]
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "low_color_cells": len(info["cells"][low]),
        "high_color_cells": len(info["cells"][high]),
        "row_order": "low_above" if info["boxes"][low][0] < info["boxes"][high][0] else "high_above",
    }


def _render(low, high, low_color, high_color, *, overlap=9, keep_unique=True):
    union = low | high
    height = 1 + max(r for r, _ in union)
    width = 1 + max(c for _, c in union)
    return [
        [
            overlap if (r, c) in low and (r, c) in high
            else low_color if keep_unique and (r, c) in low
            else high_color if keep_unique and (r, c) in high
            else 0
            for c in range(width)
        ]
        for r in range(height)
    ]


def _predict(grid):
    """Python mirror used only by tests and finite semantic rival checks."""
    info, errors = _grid_structure(grid)
    if errors:
        raise ValueError("invalid normalized-overlap input: " + "; ".join(errors))
    low_color, high_color = info["colors"]
    return _render(
        info["normalized"][low_color],
        info["normalized"][high_color],
        low_color,
        high_color,
    )


def rival_high_color_on_overlap(grid):
    info, errors = _grid_structure(grid)
    if errors:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    low_color, high_color = info["colors"]
    return _render(
        info["normalized"][low_color],
        info["normalized"][high_color],
        low_color,
        high_color,
        overlap=high_color,
    )


def rival_intersection_only(grid):
    info, errors = _grid_structure(grid)
    if errors:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    low_color, high_color = info["colors"]
    return _render(
        info["normalized"][low_color],
        info["normalized"][high_color],
        low_color,
        high_color,
        keep_unique=False,
    )


def rival_bottom_right_alignment(grid):
    info, errors = _grid_structure(grid)
    if errors:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    low_color, high_color = info["colors"]
    low = info["normalized"][low_color]
    high = info["normalized"][high_color]
    low_h, low_w = 1 + max(r for r, _ in low), 1 + max(c for _, c in low)
    high_h, high_w = 1 + max(r for r, _ in high), 1 + max(c for _, c in high)
    height, width = max(low_h, high_h), max(low_w, high_w)
    low = {(r + height - low_h, c + width - low_w) for r, c in low}
    high = {(r + height - high_h, c + width - high_w) for r, c in high}
    return _render(low, high, low_color, high_color)


def _has_marked_overlap(grid):
    info, errors = _grid_structure(grid)
    if errors:
        return False
    low, high = info["colors"]
    return bool(info["normalized"][low] & info["normalized"][high])


def _has_unique_cells_for_both(grid):
    info, errors = _grid_structure(grid)
    if errors:
        return False
    low, high = info["colors"]
    a, b = info["normalized"][low], info["normalized"][high]
    return bool(a - b) and bool(b - a)


def _has_unequal_normalized_extents(grid):
    info, errors = _grid_structure(grid)
    if errors:
        return False
    low, high = info["colors"]
    a, b = info["normalized"][low], info["normalized"][high]
    a_shape = (1 + max(r for r, _ in a), 1 + max(c for _, c in a))
    b_shape = (1 + max(r for r, _ in b), 1 + max(c for _, c in b))
    return a_shape != b_shape


SEMANTIC_RIVALS = {
    "high_color_on_overlap": rival_high_color_on_overlap,
    "intersection_only": rival_intersection_only,
    "bottom_right_alignment": rival_bottom_right_alignment,
}
SEMANTIC_WITNESSES = {
    "overlap_uses_reserved_marker": _has_marked_overlap,
    "both_unique_regions_survive": _has_unique_cells_for_both,
    "independent_top_left_alignment": _has_unequal_normalized_extents,
}
WITNESS_RIVALS = {
    "overlap_uses_reserved_marker": ["high_color_on_overlap"],
    "both_unique_regions_survive": ["intersection_only"],
    "independent_top_left_alignment": ["bottom_right_alignment"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
EXAMPLES_NEEDED = 3


def lesson_identifiable(demos, query):
    """Report a declared rival that fits every demo but changes the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # deterministic diagnostics, never a silent pass
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits all demonstrations but changes the query")
    return reasons
