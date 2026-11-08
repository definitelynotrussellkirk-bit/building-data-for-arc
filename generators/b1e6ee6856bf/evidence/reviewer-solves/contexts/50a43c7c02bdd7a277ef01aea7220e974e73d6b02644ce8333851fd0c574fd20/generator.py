"""Input sampler for "keep only the topmost nonzero in each column".

The canonical Racket program is the label authority.  This module generates
lawful inputs and exposes small Python mirrors only for tests and semantic-rival
checks.  Every production draw is non-identity: at least one occupied column
contains two or more cells.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "b1e6ee6856bf"
RULE_HASH = "3a3d82df16cd"
VERSION = "2.0.0"
SUMMARY = (
    "On a zero-background grid, process each column independently: preserve "
    "only its topmost nonzero cell with its original color and erase every "
    "lower nonzero cell. Empty columns remain empty."
)

INVARIANTS = [
    "background is 0 and all foreground colors are in 1..9",
    "at least one and at most all columns are occupied",
    "at least one occupied column has two or more cells, so the rule is visible",
    "default lessons contain a column of depth at least three to refute the canonical-fitting one-erasure shortcut",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5..14; a fixed schedule includes canonical height 5",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "5..14; a fixed schedule includes canonical width 5",
        "valid": "5..14",
    },
    "n_cols": {
        "type": "int",
        "default": "1..5 with difficulty-aware weighting",
        "valid": "1..5",
    },
    "stack_depth": {
        "type": "int",
        "default": "3..5; exact overrides may request 2",
        "valid": "2..5",
    },
}

# The minimum width/height are both five, so every declared axis combination is
# constructive: n_cols <= 5 <= grid_w and stack_depth <= 5 <= grid_h.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical_palette", "broad", "broad", "broad")


def schedule_profile(seed, sample_index, difficulty=None):
    """Deterministic curriculum slot; seed/difficulty do not change coverage."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _weighted(domain, favored, weight=8):
    return list(domain) + list(favored) * weight


def _draw_axis(ctx, overrides, name, domain, default_options):
    # When the caller provides an exact value, keep the full declared domain in
    # the draw options in every band.  Otherwise use the scheduled/weighted
    # default population.
    options = list(domain) if overrides.get(name) is not None else list(default_options)
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")


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

    canonical_slot = schedule_profile(seed, sample_index, difficulty) == "canonical_palette"
    canonical_slot = canonical_slot and not overrides

    if canonical_slot:
        h = _draw_axis(ctx, overrides, "grid_h", range(5, 15), [5])
        w = _draw_axis(ctx, overrides, "grid_w", range(5, 15), [5])
        n_cols = _draw_axis(ctx, overrides, "n_cols", range(1, 6), [5])
        stack_depth = _draw_axis(ctx, overrides, "stack_depth", range(2, 6), [3])
    else:
        if difficulty == "easy":
            favored_h = range(5, 8)
            favored_w = range(5, 8)
            favored_cols = (1, 2, 3)
            favored_depth = (3,)
        elif difficulty == "hard":
            favored_h = range(10, 15)
            favored_w = range(10, 15)
            favored_cols = (3, 4, 5)
            favored_depth = (4, 5)
        else:
            favored_h = range(7, 12)
            favored_w = range(7, 12)
            favored_cols = (2, 3, 4)
            favored_depth = (3, 4)

        h = _draw_axis(ctx, overrides, "grid_h", range(5, 15), _weighted(range(5, 15), favored_h))
        w = _draw_axis(ctx, overrides, "grid_w", range(5, 15), _weighted(range(5, 15), favored_w))
        n_cols = _draw_axis(ctx, overrides, "n_cols", range(1, 6), _weighted(range(1, 6), favored_cols))
        # Production defaults deliberately start at three.  Exact depth=2 stays
        # available for canonical-like probes and override tests.
        stack_depth = _draw_axis(
            ctx,
            overrides,
            "stack_depth",
            range(2, 6),
            _weighted(range(3, 6), favored_depth),
        )

    layout_rng = ctx.draw_rng("layout")
    columns = layout_rng.sample(range(w), n_cols)

    if canonical_slot:
        # Nine foreground cells use every ARC foreground color once.  Together
        # with background this is the canonical (5,5,10-color) profile.
        counts = [3, 2, 2, 1, 1]
    else:
        counts = [stack_depth]
        counts.extend(layout_rng.randint(1, stack_depth) for _ in range(n_cols - 1))

    positions = []
    for column, count in zip(columns, counts):
        rows = sorted(layout_rng.sample(range(h), count))
        positions.extend((row, column) for row in rows)

    color_rng = ctx.draw_rng("colors")
    if canonical_slot:
        colors = list(range(1, 10))
        color_rng.shuffle(colors)
    else:
        cell_count = len(positions)
        if difficulty == "easy":
            upper = min(4, cell_count, 9)
        elif difficulty == "hard":
            upper = min(9, cell_count)
        else:
            upper = min(7, cell_count, 9)
        palette_size = color_rng.randint(1, max(1, upper))
        palette = color_rng.sample(range(1, 10), palette_size)
        colors = [palette[index % palette_size] for index in range(cell_count)]
        color_rng.shuffle(colors)

    grid = full_grid(h, w, 0)
    for (row, column), color in zip(positions, colors):
        grid[row][column] = color

    # Keep the training grammar visibly columnar rather than admitting dense
    # texture-only impostors.  These guards preserve every exact public axis:
    # the first selected column still realizes ``stack_depth``.
    if all(value != 0 for row in grid for value in row):
        column = columns[-1]
        row = max(_column_rows(grid, column))
        grid[row][column] = 0
    if _is_solid_foreground_block(grid, height=2, width=2):
        block_rows = _foreground_rows(grid)
        source_row = max(block_rows)
        column = max(c for r, c in _foreground_cells(grid) if r == source_row)
        target_row = next(r for r in range(h - 1, -1, -1) if grid[r][column] == 0)
        grid[target_row][column], grid[source_row][column] = grid[source_row][column], 0
    return grid


def _shape_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty rectangular sequence"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid must be a nonempty rectangular sequence"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid rows must have equal positive width"
    return None


def _column_rows(grid, column):
    return [row for row in range(len(grid)) if grid[row][column] != 0]


def _foreground_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]


def _foreground_rows(grid):
    return sorted({row for row, _ in _foreground_cells(grid)})


def _is_solid_foreground_block(grid, *, height, width):
    cells = _foreground_cells(grid)
    rows = sorted({row for row, _ in cells})
    columns = sorted({column for _, column in cells})
    if len(rows) != height or len(columns) != width or len(cells) != height * width:
        return False
    return rows == list(range(rows[0], rows[0] + height)) and columns == list(
        range(columns[0], columns[0] + width)
    )


def observe_overrides(grid):
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    depths = [len(_column_rows(grid, column)) for column in range(len(grid[0]))]
    occupied = [depth for depth in depths if depth]
    if not occupied:
        raise ValueError("cannot observe axes from an empty foreground")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cols": len(occupied),
        "stack_depth": max(occupied),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]

    h, w = len(grid), len(grid[0])
    errors = []
    if not (5 <= h <= 14 and 5 <= w <= 14):
        errors.append(f"grid must be 5..14 by 5..14, found {h}x{w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (booleans are invalid)")
        return errors

    flat = [value for row in grid for value in row]
    if 0 not in flat:
        errors.append("lesson inputs require visible zero background; full foreground textures are excluded")
    if _is_solid_foreground_block(grid, height=2, width=2):
        errors.append("a lone solid 2x2 texture is outside the reviewed column-scatter lesson grammar")

    depths = [len(_column_rows(grid, column)) for column in range(w)]
    occupied = [depth for depth in depths if depth]
    if not occupied:
        errors.append("expected at least one occupied column")
        return errors
    if max(occupied) < 2:
        errors.append("no column has at least two cells; keep-topmost would be identity")
    if max(occupied) > 5:
        errors.append(f"maximum column depth {max(occupied)} exceeds reviewed support 5")
    return errors


def strict_canonical_like(grid):
    """Lawful task-domain input check; generated and canonical inputs pass."""
    return self_check(grid)


def reference_output(grid):
    """Independent Python mirror for tests; the Racket program remains authority."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    output = full_grid(len(grid), len(grid[0]), 0)
    for column in range(len(grid[0])):
        rows = _column_rows(grid, column)
        if rows:
            row = rows[0]
            output[row][column] = grid[row][column]
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_keep_bottommost(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for column in range(len(grid[0])):
        rows = _column_rows(grid, column)
        if rows:
            row = rows[-1]
            output[row][column] = grid[row][column]
    return output


def _rival_erase_one_bottom_cell(grid):
    """Canonical-fitting shortcut: erase only one lower cell per column.

    Every canonical column contains at most two foreground cells, so this rival
    agrees there.  A three-cell column leaves its middle cell behind and refutes
    the shortcut.
    """
    output = [list(row) for row in grid]
    for column in range(len(grid[0])):
        rows = _column_rows(grid, column)
        if len(rows) >= 2:
            output[rows[-1]][column] = 0
    return output


def _has_nonidentity_column(grid):
    return any(len(_column_rows(grid, column)) >= 2 for column in range(len(grid[0])))


def _has_three_cell_column(grid):
    return any(len(_column_rows(grid, column)) >= 3 for column in range(len(grid[0])))


SEMANTIC_WITNESSES = {
    "nonidentity_column": _has_nonidentity_column,
    "three_cell_column": _has_three_cell_column,
}
SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "keep_bottommost": _rival_keep_bottommost,
    "erase_one_bottom_cell": _rival_erase_one_bottom_cell,
}
WITNESS_RIVALS = {
    "nonidentity_column": ["identity", "keep_bottommost"],
    "three_cell_column": ["erase_one_bottom_cell"],
}
CANONICAL_SHORTCUTS = {
    "erase_one_bottom_cell": _rival_erase_one_bottom_cell,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query):
    del query
    return [
        f"{name} is not refuted by demonstrations"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
