"""Input sampler for corner-legend source-to-target recoloring.

The selected Racket authority is unchanged: the top-left corner names a source
color, the top-right corner names a distinct target color, and every other cell
with the source color is recolored to the target color.  Generated examples
always put source cells both on row zero (away from the legend corners) and
below row zero, so the canonical-fitting "only recolor below the top row"
shortcut cannot survive a teaching example.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "13a5c3f25c60"
TASK_ID = GENERATOR_ID
RULE_HASH = "2ba5a8d2d710"
VERSION = "2.0.0"
SUMMARY = "Corner legend gives source and target colors for body recoloring."

INVARIANTS = [
    "background is color 0",
    "top-left and top-right are distinct nonzero source and target colors",
    "2..8 non-corner cells use the source color",
    "ordinary generated examples include source cells both on row zero and below it",
    "0..6 distractor cells use at most two colors distinct from source and target",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 7..9", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "canonical-weighted 8..11", "valid": "8..11"},
    "source_cells": {"type": "int", "default": "difficulty-weighted 2..8", "valid": "2..8"},
    "distractors": {"type": "int", "default": "canonical-palette-weighted 0..6", "valid": "0..6"},
}
# Every Cartesian combination is constructive at the smallest 7x8 canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# The four canonical input profiles.  The third field is the preferred number
# of distinct distractor colors: background + source + target + this field
# yields the canonical palette size (4 or 5).
_PROFILE_SPECS = (
    ("canonical_8x10_p5", 8, 10, 2),
    ("canonical_7x9_p5", 7, 9, 2),
    ("canonical_9x8_p4", 9, 8, 1),
    ("canonical_8x11_p5", 8, 11, 2),
)
EXAMPLES_NEEDED = 3


def _require_literal_int(name, value, *, nonnegative=False):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")


def _profile_spec(sample_index):
    return _PROFILE_SPECS[sample_index % len(_PROFILE_SPECS)]


def _draw_weighted_int(ctx, name, lo, hi, anchor, *, favored=()):
    """Draw an exact observable integer while retaining its entire override domain."""
    # The full domain is always present, so every advertised override is legal
    # in every difficulty band.  Repeated anchors provide a curriculum bias
    # without clipping, post-processing, or false provenance.
    choices = list(range(lo, hi + 1))
    choices += [anchor] * 96
    for value in favored:
        choices += [value] * 8
    return ctx.draw_choice(name, choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _require_literal_int("seed", seed)
    _require_literal_int("sample_index", sample_index, nonnegative=True)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    _, profile_h, profile_w, preferred_distractor_colors = _profile_spec(sample_index)

    h = _draw_weighted_int(ctx, "grid_h", 7, 9, profile_h)
    w = _draw_weighted_int(ctx, "grid_w", 8, 11, profile_w)

    source_anchor = {None: 3, "easy": 2, "medium": 4, "hard": 7}[difficulty]
    source_favored = {
        None: (2, 3, 4),
        "easy": (2, 3),
        "medium": (3, 4, 5),
        "hard": (6, 7, 8),
    }[difficulty]
    source_count = _draw_weighted_int(
        ctx, "source_cells", 2, 8, source_anchor, favored=source_favored
    )

    # Anchor the palette to the scheduled canonical profile while preserving
    # exact 0..6 support in every band.  A count larger than the preferred
    # number reuses distractor colors rather than inflating the palette.
    distractor_anchor = preferred_distractor_colors
    if overrides.get("distractors") is None:
        # Ordinary lessons always contain at least one distractor color.  This
        # lets the target be an interior palette rank and refutes generic
        # "only changes to the smallest/largest color matter" shortcuts.
        choices = list(range(1, 7)) + [distractor_anchor] * 96 + [1, 2] * 8
        distractor_count = ctx.draw_choice("distractors", choices)
    else:
        # Explicit zero remains a fully supported exact control.
        distractor_count = ctx.draw_choice("distractors", list(range(0, 7)))

    palette_rng = ctx.draw_rng("palette")
    low, target, high = sorted(palette_rng.sample(range(1, 10), 3))
    if palette_rng.randrange(2):
        source, primary_distractor = low, high
    else:
        source, primary_distractor = high, low
    n_distractor_colors = min(distractor_count, preferred_distractor_colors)
    distractor_colors = [primary_distractor] if n_distractor_colors else []
    if n_distractor_colors == 2:
        remaining_colors = [
            color for color in range(1, 10)
            if color not in (source, target, primary_distractor)
        ]
        distractor_colors.append(palette_rng.choice(remaining_colors))

    grid = full_grid(h, w, 0)
    grid[0][0] = source
    grid[0][w - 1] = target

    layout_rng = ctx.draw_rng("layout")
    row0 = [(0, c) for c in range(1, w - 1)]
    lower = [(r, c) for r in range(1, h) for c in range(w)]
    layout_rng.shuffle(row0)
    layout_rng.shuffle(lower)

    # Constructive teaching witnesses: one row-zero source and one lower-row
    # source.  Additional source cells stay below row zero so a row-zero
    # distractor can coexist and position alone cannot identify the recoloring.
    source_positions = [row0.pop(), lower.pop()]
    source_positions.extend(lower[-(source_count - 2) :] if source_count > 2 else [])
    if source_count > 2:
        del lower[-(source_count - 2) :]
    for r, c in source_positions:
        grid[r][c] = source

    distractor_positions = []
    if distractor_count:
        # Keep one non-source row-zero object whenever distractors are present.
        distractor_positions.append(row0.pop())
        remaining = row0 + lower
        layout_rng.shuffle(remaining)
        distractor_positions.extend(remaining[: distractor_count - 1])
        for index, (r, c) in enumerate(distractor_positions):
            grid[r][c] = distractor_colors[index % len(distractor_colors)]

    return grid


def _shape_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generator grid: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    source, target = grid[0][0], grid[0][-1]
    body = [
        value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if (r, c) not in {(0, 0), (0, w - 1)}
    ]
    return {
        "grid_h": h,
        "grid_w": w,
        "source_cells": sum(value == source for value in body),
        "distractors": sum(value not in (0, source, target) for value in body),
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = _shape_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    errors = []
    if not 7 <= h <= 9:
        errors.append(f"grid_h={h} outside [7,9]")
    if not 8 <= w <= 11:
        errors.append(f"grid_w={w} outside [8,11]")

    source, target = grid[0][0], grid[0][-1]
    if source == 0 or target == 0:
        errors.append("top corners must contain nonzero source and target colors")
    if source == target:
        errors.append("source and target colors must be different")

    body = [
        value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if (r, c) not in {(0, 0), (0, w - 1)}
    ]
    source_count = sum(value == source for value in body)
    target_count = sum(value == target for value in body)
    distractors = [value for value in body if value not in (0, source, target)]
    if not 2 <= source_count <= 8:
        errors.append(f"source_cells={source_count} outside [2,8]")
    if target_count:
        errors.append("target color may appear only in the top-right legend cell")
    if not 0 <= len(distractors) <= 6:
        errors.append(f"distractors={len(distractors)} outside [0,6]")
    if len(set(distractors)) > 2:
        errors.append("distractors may use at most two distinct colors")
    return errors


def strict_canonical_like(grid):
    """Accept lawful inputs in the sampler's declared canonical-scale manifold."""
    return self_check(grid)


def _intended_output(grid):
    out = deepcopy(grid)
    source, target = grid[0][0], grid[0][-1]
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (r, c) not in {(0, 0), (0, width - 1)} and value == source:
                out[r][c] = target
    return out


def _below_top_row_only(grid):
    """RIVAL: incorrectly treats the entire top row as legend/non-body."""
    out = deepcopy(grid)
    source, target = grid[0][0], grid[0][-1]
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r]):
            if value == source:
                out[r][c] = target
    return out


def _top_row_only(grid):
    """RIVAL: incorrectly recolors only non-corner source cells on row zero."""
    out = deepcopy(grid)
    source, target = grid[0][0], grid[0][-1]
    for c in range(1, len(grid[0]) - 1):
        if grid[0][c] == source:
            out[0][c] = target
    return out


def _recolor_source_corner(grid):
    """RIVAL: recolors every source cell, including the source legend corner."""
    out = deepcopy(grid)
    source, target = grid[0][0], grid[0][-1]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == source:
                out[r][c] = target
    return out


def _has_row0_source(grid):
    if _shape_errors(grid):
        return False
    source = grid[0][0]
    return any(value == source for value in grid[0][1:-1])


def _has_below_row0_source(grid):
    if _shape_errors(grid):
        return False
    source = grid[0][0]
    return any(value == source for row in grid[1:] for value in row)


def _has_source_legend_corner(grid):
    return not _shape_errors(grid) and grid[0][0] != 0 and grid[0][0] != grid[0][-1]


SEMANTIC_WITNESSES = {
    "row0_source": _has_row0_source,
    "below_row0_source": _has_below_row0_source,
    "source_legend_exclusion": _has_source_legend_corner,
}
SEMANTIC_RIVALS = {
    "below_top_row_only": _below_top_row_only,
    "top_row_only": _top_row_only,
    "recolor_source_corner": _recolor_source_corner,
}
WITNESS_RIVALS = {
    "row0_source": ["below_top_row_only"],
    "below_row0_source": ["top_row_only"],
    "source_legend_exclusion": ["recolor_source_corner"],
}
CANONICAL_SHORTCUTS = {"below_top_row_only": _below_top_row_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report any declared rival that fits all demonstrations but changes query."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one labelled demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(
                isinstance(pair, dict)
                and "input" in pair
                and "output" in pair
                and rival(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"declared rival {name!r} fits every demo but changes the query")
    return reasons
