"""Generator for ARC task fcd1f7b55d3b — fill diagonal-corner rectangles.

Each non-background color that appears exactly twice supplies opposite corners
of an axis-aligned rectangle.  The output is rebuilt on a blank grid and every
such rectangle is filled solidly in its corner color.  Colors occurring once or
three times are ignored.

The public canonical examples contain two non-overlapping backslash-oriented
pairs and no ignored colors.  The production schedule deliberately adds slash
pairs, more than two pair colors, and one ignored color often enough that every
five-example cyclic lesson still refutes those canonical-fitting shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fcd1f7b55d3b"
TASK_ID = GENERATOR_ID
RULE_HASH = "d0be8e83eb5b"
VERSION = "3.0.0"
SUMMARY = (
    "On a blank output, fill the axis-aligned bounding rectangle of every "
    "nonzero color that occurs exactly twice. Generated pair rectangles are "
    "non-overlapping; scheduled slash pairs, 3-4 pair scenes, and one 1- or "
    "3-cell decoy teach what the canonical backslash-only two-pair examples "
    "do not distinguish."
)

INVARIANTS = [
    "7..14 rows by 8..15 columns using integer ARC colors 0..9",
    "2..4 pair colors, each at two diagonal corners separated by at least two rows and columns",
    "all pair colors in one scene share the advertised backslash or slash orientation",
    "pair bounding boxes are disjoint, so the selected rule has no overwrite-order ambiguity",
    "0 or 1 decoy color occurs once or three times outside every pair bounding box",
]

ORIENTATIONS = ("backslash", "slash")
SCHEDULE_PROFILES = (
    "canonical_backslash",
    "selective_slash",
    "selective_backslash",
    "canonical_slash",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7..9 anchors plus broader 7..14 scheduled scenes",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 8..10 anchors plus broader 8..15 scheduled scenes",
        "valid": "8..15",
    },
    "n_pairs": {
        "type": "int",
        "default": "2 canonical / 3 selective / 4 hard-selective",
        "valid": "2..4",
    },
    "n_decoys": {
        "type": "int",
        "default": "0 canonical / 1 selective",
        "valid": "0..1",
    },
    "orientation": {
        "type": "str",
        "default": "alternating backslash|slash lesson schedule",
        "valid": "|".join(ORIENTATIONS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

_CANONICAL_PROFILES = ((8, 9), (9, 10), (7, 8), (9, 9))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic role of an ordinary production draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_controls(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    for name in ("grid_h", "grid_w", "n_pairs", "n_decoys"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    value = overrides.get("orientation")
    if value is not None and type(value) is not str:
        raise TypeError("orientation must be a string")


def _scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _scheduled_choice(ctx, name: str, choices, scheduled):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, choices)
    return ctx.draw_choice(name, (scheduled,))


def _default_dimensions(sample_index: int, band: str) -> tuple[int, int]:
    phase = sample_index % 4
    block = sample_index // 4
    if phase in (0, 3):
        offset = 0 if phase == 0 else 1
        return _CANONICAL_PROFILES[(2 * block + offset) % len(_CANONICAL_PROFILES)]

    if band == "easy":
        heights, widths = (7, 8, 9), (8, 9, 10)
    elif band == "hard":
        heights, widths = (11, 12, 13, 14), (12, 13, 14, 15)
    else:
        heights, widths = (9, 10, 11), (10, 11, 12)
    index = block + phase
    return heights[index % len(heights)], widths[index % len(widths)]


def _default_counts(sample_index: int, band: str) -> tuple[int, int, str]:
    phase = sample_index % 4
    if phase == 0:
        return 2, 0, "backslash"
    if phase == 1:
        return 3, 1, "slash"
    if phase == 2:
        return (4 if band == "hard" else 3), 1, "backslash"
    return 2, 0, "slash"


def _slot_ranges(height: int, width: int):
    row_split = height // 2
    col_split = width // 2
    return [
        (row_lo, row_hi, col_lo, col_hi)
        for row_lo, row_hi in ((0, row_split), (row_split, height))
        for col_lo, col_hi in ((0, col_split), (col_split, width))
    ]


def _choose_pair_coordinates(slot, orientation: str, rng):
    row_lo, row_hi, col_lo, col_hi = slot
    row_pairs = [
        (first, second)
        for first, second in combinations(range(row_lo, row_hi), 2)
        if second - first >= 2
    ]
    slot_width = col_hi - col_lo
    col_pairs = [
        (first, second)
        for first, second in combinations(range(col_lo, col_hi), 2)
        if 2 <= second - first <= slot_width - 2
    ]
    if not row_pairs or not col_pairs:
        raise ValueError(f"slot {slot} cannot hold a 3x3-or-larger pair rectangle")
    top, bottom = rng.choice(row_pairs)
    left, right = rng.choice(col_pairs)
    if orientation == "backslash":
        return (top, left), (bottom, right), (top, left, bottom, right)
    return (top, right), (bottom, left), (top, left, bottom, right)


def _inside_box(row: int, col: int, box) -> bool:
    top, left, bottom, right = box
    return top <= row <= bottom and left <= col <= right


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic lawful input with fully observable controls."""
    _validate_controls(difficulty, overrides)
    band = difficulty or "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _default_dimensions(sample_index, band)
    default_pairs, default_decoys, default_orientation = _default_counts(
        sample_index, band
    )
    height = _scheduled_int(ctx, "grid_h", 7, 14, default_h)
    width = _scheduled_int(ctx, "grid_w", 8, 15, default_w)
    n_pairs = _scheduled_int(ctx, "n_pairs", 2, 4, default_pairs)
    n_decoys = _scheduled_int(ctx, "n_decoys", 0, 1, default_decoys)
    orientation = _scheduled_choice(
        ctx, "orientation", ORIENTATIONS, default_orientation
    )

    layout_rng = ctx.draw_rng("layout")
    color_count = n_pairs + n_decoys
    colors = layout_rng.sample(list(range(1, 10)), color_count)
    pair_colors = colors[:n_pairs]
    decoy_colors = colors[n_pairs:]

    grid = full_grid(height, width, 0)
    slots = _slot_ranges(height, width)
    layout_rng.shuffle(slots)
    pair_boxes = []
    used = set()

    for color, slot in zip(pair_colors, slots[:n_pairs]):
        first, second, box = _choose_pair_coordinates(slot, orientation, layout_rng)
        for row, col in (first, second):
            grid[row][col] = color
            used.add((row, col))
        pair_boxes.append(box)

    if decoy_colors:
        decoy_size = 1 if sample_index % 4 in (1, 3) else 3
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if (row, col) not in used
            and not any(_inside_box(row, col, box) for box in pair_boxes)
        ]
        if len(candidates) < decoy_size:
            raise ValueError("not enough cells outside pair rectangles for the decoy")
        for row, col in layout_rng.sample(candidates, decoy_size):
            grid[row][col] = decoy_colors[0]
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _by_color(grid):
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                by_color.setdefault(value, []).append((row, col))
    return by_color


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _boxes_overlap(first, second) -> bool:
    ar0, ac0, ar1, ac1 = first
    br0, bc0, br1, bc1 = second
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _orientation(cells) -> str | None:
    (top_row, top_col), (bottom_row, bottom_col) = sorted(cells)
    if top_row == bottom_row or top_col == bottom_col:
        return None
    return "backslash" if top_col < bottom_col else "slash"


def _meta_overrides(meta) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    candidate = nested if isinstance(nested, dict) else meta
    return {name: value for name, value in candidate.items() if name in AXES}


def _analysis(grid) -> dict[str, Any]:
    shape = _shape(grid)
    if shape is None:
        return {"errors": ["expected a nonempty rectangular grid"]}
    height, width = shape
    errors: list[str] = []
    if not 7 <= height <= 14:
        errors.append(f"grid_h={height} outside [7,14]")
    if not 8 <= width <= 15:
        errors.append(f"grid_w={width} outside [8,15]")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return {"errors": errors}

    by_color = _by_color(grid)
    pairs = {color: cells for color, cells in by_color.items() if len(cells) == 2}
    decoys = {color: cells for color, cells in by_color.items() if len(cells) != 2}
    if not 2 <= len(pairs) <= 4:
        errors.append(f"n_pairs={len(pairs)} outside [2,4]")
    if not 0 <= len(decoys) <= 1:
        errors.append(f"n_decoys={len(decoys)} outside [0,1]")
    for color, cells in decoys.items():
        if len(cells) not in (1, 3):
            errors.append(
                f"decoy color {color} occurs {len(cells)} times; expected 1 or 3"
            )

    pair_boxes = []
    orientations = set()
    for color, cells in pairs.items():
        orientation = _orientation(cells)
        if orientation is None:
            errors.append(f"pair color {color} is row- or column-collinear")
            continue
        orientations.add(orientation)
        top, left, bottom, right = _bbox(cells)
        if bottom - top < 2 or right - left < 2:
            errors.append(
                f"pair color {color} must span at least 3 rows and 3 columns"
            )
        pair_boxes.append((color, (top, left, bottom, right)))

    if len(orientations) > 1:
        errors.append(f"pair orientations are mixed: {sorted(orientations)}")
    for (color_a, box_a), (color_b, box_b) in combinations(pair_boxes, 2):
        if _boxes_overlap(box_a, box_b):
            errors.append(
                f"pair bounding boxes for colors {color_a} and {color_b} overlap"
            )

    boxes_only = [box for _, box in pair_boxes]
    for color, cells in decoys.items():
        if any(any(_inside_box(row, col, box) for box in boxes_only) for row, col in cells):
            errors.append(f"decoy color {color} must lie outside every pair bbox")

    orientation = next(iter(orientations), None)
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "by_color": by_color,
        "pairs": pairs,
        "decoys": decoys,
        "pair_boxes": pair_boxes,
        "orientation": orientation,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return concrete violations of the selected generator manifold."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_pairs": len(analysis["pairs"]),
        "n_decoys": len(analysis["decoys"]),
        "orientation": analysis["orientation"],
    }
    for name, requested in _meta_overrides(meta).items():
        if requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid):
    """Lawful task-linked inputs in this sampler, including all canonical pairs."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis directly from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_pairs": len(analysis["pairs"]),
        "n_decoys": len(analysis["decoys"]),
        "orientation": analysis["orientation"],
    }


def _paint_bbox(out, color, cells):
    top, left, bottom, right = _bbox(cells)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            out[row][col] = color


def _intended_rule(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _by_color(grid).items():
        if len(cells) == 2:
            _paint_bbox(out, color, cells)
    return out


def _copy_then_fill(grid):
    """RIVAL: keep ignored colors instead of rebuilding on a blank grid."""
    out = deepcopy(grid)
    for color, cells in _by_color(grid).items():
        if len(cells) == 2:
            _paint_bbox(out, color, cells)
    return out


def _all_colors_bbox(grid):
    """RIVAL: paint a bbox for every nonzero color, regardless of multiplicity."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _by_color(grid).items():
        _paint_bbox(out, color, cells)
    return out


def _backslash_only(grid):
    """RIVAL: infer rectangles only from canonical NW-to-SE corner pairs."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _by_color(grid).items():
        if len(cells) == 2 and _orientation(cells) == "backslash":
            _paint_bbox(out, color, cells)
    return out


def _exactly_two_pairs(grid):
    """RIVAL: run the task only when the scene has the canonical two pair colors."""
    pair_count = sum(len(cells) == 2 for cells in _by_color(grid).values())
    if pair_count == 2:
        return _intended_rule(grid)
    return full_grid(len(grid), len(grid[0]), 0)


def _has_decoy(grid) -> bool:
    return any(len(cells) != 2 for cells in _by_color(grid).values())


def _has_slash_pair(grid) -> bool:
    return any(
        len(cells) == 2 and _orientation(cells) == "slash"
        for cells in _by_color(grid).values()
    )


def _has_more_than_two_pairs(grid) -> bool:
    return sum(len(cells) == 2 for cells in _by_color(grid).values()) > 2


SEMANTIC_WITNESSES = {
    "decoy_filter": _has_decoy,
    "slash_orientation": _has_slash_pair,
    "more_than_two_pairs": _has_more_than_two_pairs,
}
SEMANTIC_RIVALS = {
    "copy_then_fill": _copy_then_fill,
    "all_colors_bbox": _all_colors_bbox,
    "backslash_only": _backslash_only,
    "exactly_two_pairs": _exactly_two_pairs,
}
WITNESS_RIVALS = {
    "decoy_filter": ["copy_then_fill", "all_colors_bbox"],
    "slash_orientation": ["backslash_only"],
    "more_than_two_pairs": ["exactly_two_pairs"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared canonical-fitting rival left able to change the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
