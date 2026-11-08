"""Construct lawful span-intersection inputs for ARC task f4dc936dfcbb.

Rows containing exactly two cells of color 2 define inclusive horizontal spans.
Columns containing exactly two cells of color 3 define inclusive vertical spans.
The authoritative rule returns a fresh background grid with color 8 only where
one selected row and one selected column lie inside both corresponding spans.
Other input colors are distractors and do not survive into the output.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4dc936dfcbb"
TASK_ID = GENERATOR_ID
RULE_HASH = "b804c88a8a55"
VERSION = "3.0.0"
SUMMARY = (
    "Pairs of 2s define horizontal row spans and pairs of 3s define vertical "
    "column spans. Return a new zero grid with 8 only at row/column pairs that "
    "satisfy both inclusive span-containment tests; ignore all distractors."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input is 8..18 rows by 9..20 columns",
    "1..3 rows contain exactly two color-2 endpoints",
    "1..3 columns contain exactly two color-3 endpoints",
    "one ignored color appears in 1..4 distractor cells",
    "at least one row-span/column-span pair satisfies both containment tests",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical profiles plus broad difficulty-weighted 8..18 support",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical profiles plus broad difficulty-weighted 9..20 support",
        "valid": "9..20",
    },
    "n_row_spans": {
        "type": "int",
        "default": "2..3 (1 remains available as an exact override)",
        "valid": "1..3",
    },
    "n_col_spans": {
        "type": "int",
        "default": "2..3 (1 remains available as an exact override)",
        "valid": "1..3",
    },
    "n_distractors": {
        "type": "int",
        "default": "canonical anchor 1 plus broad 1..4 support",
        "valid": "1..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Every canonical input has one ignored color, so palette size is four even
# though the ignored color itself varies.  The five dimensions include the
# held-out canonical query and are used only as a sampling anchor.
_CANONICAL_SHAPES = (
    (8, 10),
    (9, 9),
    (8, 11),
    (10, 10),
    (9, 12),
)
_AXIS_BOUNDS = {
    "grid_h": (8, 18),
    "grid_w": (9, 20),
    "n_row_spans": (1, 3),
    "n_col_spans": (1, 3),
    "n_distractors": (1, 4),
}
_DISTRACTOR_COLORS = (1, 4, 5, 6, 7, 9)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _axis_int(ctx, name, lo, hi, *, anchor=None, options=None):
    """Consume an exact axis while allowing deterministic default schedules."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if anchor is not None:
        return ctx.draw_choice(name, (anchor,))
    choices = tuple(options if options is not None else range(lo, hi + 1))
    return ctx.draw_choice(name, choices)


def _difficulty_options(difficulty, *, easy, medium, hard, full):
    favored = easy if difficulty == "easy" else hard if difficulty == "hard" else medium
    # Retain full-domain support in every band while making the declared band
    # visible in finite samples.
    return tuple(full) + tuple(favored) * 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    mode = ctx.draw_choice("curriculum_mode", ("canonical", "canonical", "broad"))
    anchor_h, anchor_w = ctx.draw_choice("canonical_shape", _CANONICAL_SHAPES)
    if mode != "canonical":
        anchor_h = anchor_w = None

    h = _axis_int(
        ctx,
        "grid_h",
        8,
        18,
        anchor=anchor_h,
        options=_difficulty_options(
            difficulty,
            easy=(8, 9, 10, 11),
            medium=(10, 11, 12, 13, 14),
            hard=(15, 16, 17, 18),
            full=range(8, 19),
        ),
    )
    w = _axis_int(
        ctx,
        "grid_w",
        9,
        20,
        anchor=anchor_w,
        options=_difficulty_options(
            difficulty,
            easy=(9, 10, 11, 12),
            medium=(11, 12, 13, 14, 15),
            hard=(16, 17, 18, 19, 20),
            full=range(9, 21),
        ),
    )
    n_row_spans = _axis_int(ctx, "n_row_spans", 1, 3, options=(2, 2, 3))
    n_col_spans = _axis_int(ctx, "n_col_spans", 1, 3, options=(2, 2, 3))
    n_distractors = _axis_int(
        ctx,
        "n_distractors",
        1,
        4,
        anchor=1 if mode == "canonical" else None,
        options=(1, 1, 2, 3, 4),
    )

    cut_r, cut_c = h // 2, w // 2
    layout_rng = ctx.draw_rng("span_layout")

    upper_rows = list(range(1, cut_r))
    lower_rows = list(range(cut_r + 1, h - 1))
    left_cols = list(range(1, cut_c))
    right_cols = list(range(cut_c + 1, w - 1))

    primary_row = layout_rng.choice(upper_rows)
    primary_col = layout_rng.choice(left_cols)
    row_specs = [(primary_row, 0, w - 1)]
    col_specs = [(primary_col, 0, h - 1)]

    if n_row_spans >= 2:
        secondary_row = layout_rng.choice(lower_rows)
        row_specs.append((secondary_row, cut_c, w - 1))
    if n_col_spans >= 2:
        secondary_col = layout_rng.choice(right_cols)
        col_specs.append((secondary_col, cut_r, h - 1))

    if n_row_spans == 3:
        used_rows = {r for r, _, _ in row_specs} | {cut_r}
        extra_rows = [r for r in range(1, h - 1) if r not in used_rows]
        row_specs.append((layout_rng.choice(extra_rows), 0, cut_c))
    if n_col_spans == 3:
        used_cols = {c for c, _, _ in col_specs} | {cut_c}
        extra_cols = [c for c in range(1, w - 1) if c not in used_cols]
        col_specs.append((layout_rng.choice(extra_cols), 0, cut_r))

    grid = full_grid(h, w, 0)
    for row, c0, c1 in row_specs:
        grid[row][c0] = 2
        grid[row][c1] = 2
    for col, r0, r1 in col_specs:
        grid[r0][col] = 3
        grid[r1][col] = 3

    # Keep distractors away from every selected row/column pair.  This makes
    # their irrelevance explicit rather than letting a distractor be overwritten
    # at an output intersection.
    span_rows = {r for r, _, _ in row_specs}
    span_cols = {c for c, _, _ in col_specs}
    free = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and not (r in span_rows and c in span_cols)
    ]
    distractor_color = ctx.draw_choice("distractor_color", _DISTRACTOR_COLORS)
    for r, c in ctx.draw_rng("distractor_positions").sample(free, n_distractors):
        grid[r][c] = distractor_color
    return grid


def _span_data(grid):
    h, w = len(grid), len(grid[0])
    row_spans = []
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value == 2]
        if len(cols) >= 2:
            row_spans.append((r, min(cols), max(cols)))
    col_spans = []
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 3]
        if len(rows) >= 2:
            col_spans.append((c, min(rows), max(rows)))
    return row_spans, col_spans


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the strict task manifold and return diagnostics, never raise."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must have a nonempty first row"]

    h, w = len(grid), len(grid[0])
    problems = []
    if not 8 <= h <= 18:
        problems.append(f"height {h} outside 8..18")
    if not 9 <= w <= 20:
        problems.append(f"width {w} outside 9..20")

    rectangular = True
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            problems.append(f"row {r} has invalid width")
            rectangular = False
            continue
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                problems.append(f"cell ({r},{c}) is not an ARC color 0..9")
    if not rectangular:
        return problems
    if problems and any("ARC color" in problem for problem in problems):
        return problems

    if any(value == 8 for row in grid for value in row):
        problems.append("input must not contain output color 8")

    row_counts = [sum(value == 2 for value in row) for row in grid]
    bad_row_counts = [(r, count) for r, count in enumerate(row_counts) if count not in (0, 2)]
    if bad_row_counts:
        problems.append(f"color-2 marker rows must contain exactly two endpoints: {bad_row_counts[:4]}")
    n_row_spans = sum(count == 2 for count in row_counts)
    if not 1 <= n_row_spans <= 3:
        problems.append(f"found {n_row_spans} row spans, expected 1..3")

    col_counts = [sum(grid[r][c] == 3 for r in range(h)) for c in range(w)]
    bad_col_counts = [(c, count) for c, count in enumerate(col_counts) if count not in (0, 2)]
    if bad_col_counts:
        problems.append(f"color-3 marker columns must contain exactly two endpoints: {bad_col_counts[:4]}")
    n_col_spans = sum(count == 2 for count in col_counts)
    if not 1 <= n_col_spans <= 3:
        problems.append(f"found {n_col_spans} column spans, expected 1..3")

    distractors = [value for row in grid for value in row if value not in (0, 2, 3)]
    distractor_colors = set(distractors)
    if not 1 <= len(distractors) <= 4:
        problems.append(f"found {len(distractors)} distractor cells, expected 1..4")
    if len(distractor_colors) != 1:
        problems.append(
            f"distractors must use exactly one ignored color, found {sorted(distractor_colors)}"
        )

    if not bad_row_counts and not bad_col_counts and n_row_spans and n_col_spans:
        row_spans, col_spans = _span_data(grid)
        crossings = [
            (r, c)
            for r, c0, c1 in row_spans
            for c, r0, r1 in col_spans
            if c0 <= c <= c1 and r0 <= r <= r1
        ]
        if not crossings:
            problems.append("row and column spans exist but no pair satisfies both tests")
    return problems


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe invalid grid: {problems}")
    row_spans, col_spans = _span_data(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_row_spans": len(row_spans),
        "n_col_spans": len(col_spans),
        "n_distractors": sum(
            value not in (0, 2, 3) for row in grid for value in row
        ),
    }


def _rival_output(grid, mode):
    row_spans, col_spans = _span_data(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c0, c1 in row_spans:
        for c, r0, r1 in col_spans:
            horizontal = c0 <= c <= c1
            vertical = r0 <= r <= r1
            if mode == "all" or mode == "horizontal" and horizontal or mode == "vertical" and vertical:
                out[r][c] = 8
    return out


def _all_span_pairs(grid):
    """Rival: mark every selected-row/selected-column pair."""
    return _rival_output(grid, "all")


def _horizontal_only(grid):
    """Rival: apply only the horizontal containment test."""
    return _rival_output(grid, "horizontal")


def _vertical_only(grid):
    """Rival: apply only the vertical containment test."""
    return _rival_output(grid, "vertical")


def _has_horizontal_gate_rejection(grid):
    """A pair passes vertical containment but fails horizontal containment."""
    row_spans, col_spans = _span_data(grid)
    return any(
        not (c0 <= c <= c1) and r0 <= r <= r1
        for r, c0, c1 in row_spans
        for c, r0, r1 in col_spans
    )


def _has_vertical_gate_rejection(grid):
    """A pair passes horizontal containment but fails vertical containment."""
    row_spans, col_spans = _span_data(grid)
    return any(
        c0 <= c <= c1 and not (r0 <= r <= r1)
        for r, c0, c1 in row_spans
        for c, r0, r1 in col_spans
    )


SEMANTIC_WITNESSES = {
    "horizontal_gate_rejection": _has_horizontal_gate_rejection,
    "vertical_gate_rejection": _has_vertical_gate_rejection,
}
SEMANTIC_RIVALS = {
    "all_span_pairs": _all_span_pairs,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
}
WITNESS_RIVALS = {
    "horizontal_gate_rejection": ["all_span_pairs", "vertical_only"],
    "vertical_gate_rejection": ["all_span_pairs", "horizontal_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
