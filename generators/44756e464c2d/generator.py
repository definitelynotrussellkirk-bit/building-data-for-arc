"""Input generator for color-specific top/left border intersections.

The unchanged Racket authority selects columns whose top-border cell is blue
(1), selects rows whose left-border cell is red (2), and paints every selected
row/column intersection green (3) on an otherwise empty output.

A four-step curriculum uses role-swapped canonical colors as border
distractors: red(2) on the top border and blue(1) on the left border.  The
authority intentionally ignores them, refuting the plausible but wrong shortcut
that every nonzero border cell selects a row or column without introducing a
noncanonical palette.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "44756e464c2d"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "a5adc22c1318"
SUMMARY = (
    "Blue(1) markers on the top border select columns and red(2) markers on "
    "the left border select rows; paint their Cartesian-product intersections "
    "green(3), while ignoring role-swapped border distractors."
)

INVARIANTS = [
    "rectangular 7..10 by 8..10 input with background zero and a zero origin",
    "1..4 blue(1) selectors occur only on the top border",
    "1..4 red(2) selectors occur only on the left border",
    "scheduled red-on-top and blue-on-left distractors occur only in unused border slots",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or weighted 7..10",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or weighted 8..10",
        "valid": "8..10",
    },
    "n_row_marks": {
        "type": "int",
        "default": "scheduled anchor or weighted 1..4 blue top-border selectors",
        "valid": "1..4",
    },
    "n_col_marks": {
        "type": "int",
        "default": "scheduled anchor or weighted 1..4 red left-border selectors",
        "valid": "1..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical",
    "top_distractor",
    "left_distractor",
    "both_distractors",
)

_SHAPE_ANCHORS = {
    None: (9, 9),
    "easy": (7, 8),
    "medium": (9, 9),
    "hard": (10, 10),
}
_MARK_ANCHORS = {
    None: (2, 2),
    "easy": (1, 1),
    "medium": (3, 3),
    "hard": (4, 4),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-sample teaching profile.

    ``seed`` and ``difficulty`` are accepted for the public schedule API but the
    residue schedule intentionally depends only on ``sample_index``.  Thus every
    three consecutive pairs contain at least two color-role witnesses, making
    the canonical two-demo/one-query lesson rotation-safe for the declared
    rival.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    ranges = {
        "grid_h": (7, 10),
        "grid_w": (8, 10),
        "n_row_marks": (1, 4),
        "n_col_marks": (1, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = ranges[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _draw_axis(ctx, overrides, name, lo, hi, *, anchor, canonical_profile):
    """Draw one exact axis while preserving its full override domain.

    The canonical schedule cell is deliberately anchored, but explicit
    overrides still pass through the same strict global range in every band.
    Other schedule cells retain the complete domain with a modest anchor weight.
    """
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if canonical_profile:
        return ctx.draw_choice(name, (anchor,))
    choices = list(range(lo, hi + 1)) + [anchor] * 8
    return ctx.draw_choice(name, choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    canonical_profile = profile == "canonical"
    shape_anchor = _SHAPE_ANCHORS[difficulty]
    mark_anchor = _MARK_ANCHORS[difficulty]
    h = _draw_axis(
        ctx,
        overrides,
        "grid_h",
        7,
        10,
        anchor=shape_anchor[0],
        canonical_profile=canonical_profile,
    )
    w = _draw_axis(
        ctx,
        overrides,
        "grid_w",
        8,
        10,
        anchor=shape_anchor[1],
        canonical_profile=canonical_profile,
    )
    n_row = _draw_axis(
        ctx,
        overrides,
        "n_row_marks",
        1,
        4,
        anchor=mark_anchor[0],
        canonical_profile=canonical_profile,
    )
    n_col = _draw_axis(
        ctx,
        overrides,
        "n_col_marks",
        1,
        4,
        anchor=mark_anchor[1],
        canonical_profile=canonical_profile,
    )

    grid = full_grid(h, w, 0)

    column_slots = list(range(1, w))
    ctx.draw_rng("top_border_positions").shuffle(column_slots)
    selected_cols = column_slots[:n_row]
    for c in selected_cols:
        grid[0][c] = 1
    if profile in ("top_distractor", "both_distractors"):
        grid[0][column_slots[n_row]] = 2

    row_slots = list(range(1, h))
    ctx.draw_rng("left_border_positions").shuffle(row_slots)
    selected_rows = row_slots[:n_col]
    for r in selected_rows:
        grid[r][0] = 2
    if profile in ("left_distractor", "both_distractors"):
        grid[row_slots[n_col]][0] = 1

    return grid


def observe_overrides(grid):
    """Recover every advertised exact axis directly from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_row_marks": sum(value == 1 for value in grid[0]),
        "n_col_marks": sum(row[0] == 2 for row in grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int for row in grid for value in row):
        return ["cells must be integers, not bools or other scalar types"]

    height = len(grid)
    errors = []
    if not 7 <= height <= 10:
        errors.append(f"grid_h={height} outside 7..10")
    if not 8 <= width <= 10:
        errors.append(f"grid_w={width} outside 8..10")
    if grid[0][0] != 0:
        errors.append(f"origin must be background 0, got {grid[0][0]}")

    allowed = {0, 1, 2}
    unknown = sorted({value for row in grid for value in row if value not in allowed})
    if unknown:
        errors.append(f"unsupported input colors: {unknown}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if r == 0 and c == 0:
                continue
            if r == 0:
                if value not in (0, 1, 2):
                    errors.append(f"top border cell {(r, c)} must be 0, 1 or 2")
            elif c == 0:
                if value not in (0, 1, 2):
                    errors.append(f"left border cell {(r, c)} must be 0, 1 or 2")
            elif value != 0:
                errors.append(f"interior cell {(r, c)} must stay background")

    n_row = sum(value == 1 for value in grid[0])
    n_col = sum(row[0] == 2 for row in grid)
    if not 1 <= n_row <= 4:
        errors.append(f"n_row_marks={n_row} outside 1..4")
    if not 1 <= n_col <= 4:
        errors.append(f"n_col_marks={n_col} outside 1..4")
    top_distractors = sum(value == 2 for value in grid[0][1:])
    left_distractors = sum(row[0] == 1 for row in grid[1:])
    if top_distractors > 1:
        errors.append("at most one red(2) top-border distractor is supported")
    if left_distractors > 1:
        errors.append("at most one blue(1) left-border distractor is supported")
    return errors


def strict_canonical_like(grid):
    """Return diagnostics for the complete lawful sampler manifold."""
    return self_check(grid)


def _all_nonzero_border_cells_select(grid):
    """Plausible RIVAL: wrongly treats every nonzero border cell as a selector."""
    height, width = len(grid), len(grid[0])
    selected_cols = [c for c in range(width) if grid[0][c] != 0]
    selected_rows = [r for r in range(height) if grid[r][0] != 0]
    out = full_grid(height, width, 0)
    for r in selected_rows:
        for c in selected_cols:
            out[r][c] = 3
    return out


def _has_color_specific_border_roles(grid):
    return any(value == 2 for value in grid[0][1:]) or any(
        row[0] == 1 for row in grid[1:]
    )


SEMANTIC_WITNESSES = {
    "color_specific_border_roles": _has_color_specific_border_roles,
}
SEMANTIC_RIVALS = {
    "all_nonzero_border_cells_select": _all_nonzero_border_cells_select,
}
WITNESS_RIVALS = {
    "color_specific_border_roles": ["all_nonzero_border_cells_select"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report declared rivals that fit every demo but disagree on the query."""
    return [
        f"{name} fits every demo and disagrees on the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
