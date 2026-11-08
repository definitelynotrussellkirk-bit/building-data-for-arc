"""Generator for v1_e_m_h_keys:E6 (single-7 rows fill fully).

The Racket authority expands a row only when its nonzero values are exactly
``[7]``.  Each ordinary draw therefore contains the positive branch and three
nearby negative branches that defeat common shortcuts:

* two or more 7s in one row;
* a singleton non-7 cell;
* exactly one 7 accompanied by another nonzero color.

Outputs remain the responsibility of the canonical Racket rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c36d1678a484"
TASK_ID = GENERATOR_ID
RULE_HASH = "e987896b90b9"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background grid contains one or two single-orange target rows plus "
    "unchanged counterexamples: a partial row with multiple orange cells, a "
    "singleton non-orange row, and a row containing one orange cell together "
    "with another color. Only rows whose nonzero list is exactly [7] fill "
    "completely with orange."
)

INVARIANTS = [
    "background is color 0 and cells are ARC colors 0..9",
    "at least one row has exactly one nonzero cell, color 7",
    "ordinary draws include multi-7, non-7-singleton, and mixed-7 negative rows",
    "rows are transformed independently and the Racket authority supplies labels",
]

PALETTES = {
    # (singleton non-7 color, mixed-row non-7 color)
    "mono": (8, 8),
    "warm": (2, 4),
    "cool": (3, 5),
    "contrast": (1, 9),
}

AXES = {
    "grid_h": {"type": "int", "default": "5..12; core favors 6", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "3..14; core favors 7", "valid": "3..14"},
    "target_rows": {"type": "int", "default": "1..2; core favors 2", "valid": "1..2"},
    "palette_kind": {
        "type": "str",
        "default": "core favors mono",
        "valid": "mono|warm|cool|contrast",
    },
}

# The smallest advertised grid (5x3) can hold two targets and all three
# counterexample rows, so every cross-product combination is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _weighted_choice(ctx, name, values, favored=()):
    """Choose from the complete override domain while biasing ordinary draws."""
    options = list(values) + list(favored)
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "target_rows"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")
    value = overrides.get("palette_kind")
    if value is not None and type(value) is not str:
        raise TypeError(f"palette_kind must be a string (not {type(value).__name__})")


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

    # A frequent canonical-density component preserves the source task's small
    # 6x7, three-color profile.  Broad draws still expose every declared value in
    # every difficulty band and exact overrides always take precedence.
    core = ctx.draw_choice(
        "curriculum_profile", ("core", "core", "core", "broad")
    ) == "core"
    if core:
        h_favored = [6] * 100
        w_favored = [7] * 100
        target_favored = [2] * 100
        palette_favored = ["mono"] * 100
    else:
        if difficulty == "easy":
            h_favored = [5, 5, 6, 7] * 4
            w_favored = [5, 6, 7, 7, 8] * 4
            target_favored = [1, 1, 2] * 4
            palette_favored = ["mono", "mono", "warm"] * 4
        elif difficulty == "hard":
            h_favored = [9, 10, 11, 12] * 4
            w_favored = [10, 11, 12, 13, 14] * 4
            target_favored = [2, 2, 1] * 4
            palette_favored = ["cool", "contrast", "warm"] * 4
        else:
            h_favored = [5, 6, 7, 8, 9, 10, 11, 12] * 2
            w_favored = [5, 6, 7, 8, 9, 10, 11, 12] * 2
            target_favored = [1, 2] * 8
            palette_favored = list(PALETTES) * 4

    h = _weighted_choice(ctx, "grid_h", range(5, 13), h_favored)
    w = _weighted_choice(ctx, "grid_w", range(3, 15), w_favored)
    n_targets = _weighted_choice(ctx, "target_rows", range(1, 3), target_favored)
    palette_kind = _weighted_choice(ctx, "palette_kind", tuple(PALETTES), palette_favored)

    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("row_layout")
    chosen_rows = layout_rng.sample(range(h), n_targets + 3)
    target_indices = chosen_rows[:n_targets]
    multi_row, singleton_row, mixed_row = chosen_rows[n_targets:]

    column_rng = ctx.draw_rng("columns")
    for row in target_indices:
        grid[row][column_rng.randrange(w)] = 7

    # Keep at least one background cell so this is a genuine unchanged
    # multi-7 counterexample rather than an already-full output row.
    max_multi = min(4, w - 1)
    multi_count = column_rng.randint(2, max_multi)
    for col in column_rng.sample(range(w), multi_count):
        grid[multi_row][col] = 7

    singleton_color, mixed_color = PALETTES[palette_kind]
    grid[singleton_row][column_rng.randrange(w)] = singleton_color
    seven_col, other_col = column_rng.sample(range(w), 2)
    grid[mixed_row][seven_col] = 7
    grid[mixed_row][other_col] = mixed_color
    return grid


def _row_nonzero(row):
    return [value for value in row if value != 0]


def _palette_kind_from_grid(grid):
    singleton = [
        values[0]
        for row in grid
        if len(values := _row_nonzero(row)) == 1 and values[0] != 7
    ]
    mixed = [
        next(value for value in values if value != 7)
        for row in grid
        if (values := _row_nonzero(row)).count(7) == 1
        and any(value != 7 for value in values)
    ]
    if len(singleton) != 1 or len(mixed) != 1:
        raise ValueError("generated grid must contain one singleton and one mixed witness row")
    pair = (singleton[0], mixed[0])
    for name, expected in PALETTES.items():
        if pair == expected:
            return name
    raise ValueError(f"unrecognized generated palette pair: {pair}")


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "target_rows": sum(_row_nonzero(row) == [7] for row in grid),
        "palette_kind": _palette_kind_from_grid(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    nonzero_rows = [_row_nonzero(row) for row in grid]
    errors = []
    if not any(values == [7] for values in nonzero_rows):
        errors.append("expected at least one single-7 target row")
    if not any(len(values) >= 2 for values in nonzero_rows):
        errors.append("expected at least one multi-cell unchanged row")
    return errors


def strict_canonical_like(grid):
    """Accept the canonical row-rule manifold, not only this sampler's recipe."""
    return self_check(grid)


def _any_seven(grid):
    """Wrong rule: fill every row containing a 7."""
    return [[7] * len(row) if 7 in row else list(row) for row in grid]


def _any_singleton(grid):
    """Wrong rule: expand every singleton in its own color."""
    out = [list(row) for row in grid]
    for index, row in enumerate(grid):
        values = _row_nonzero(row)
        if len(values) == 1:
            out[index] = [values[0]] * len(row)
    return out


def _one_seven_anywhere(grid):
    """Wrong rule: ignore other colors when a row contains exactly one 7."""
    return [[7] * len(row) if row.count(7) == 1 else list(row) for row in grid]


def _has_multi_seven(grid):
    width = len(grid[0]) if grid else 0
    return any(2 <= row.count(7) < width for row in grid)


def _has_nonseven_singleton(grid):
    return any(
        len(values := _row_nonzero(row)) == 1 and values[0] != 7
        for row in grid
    )


def _has_mixed_seven(grid):
    return any(
        row.count(7) == 1 and any(value not in (0, 7) for value in row)
        for row in grid
    )


SEMANTIC_WITNESSES = {
    "multi_seven_unchanged": _has_multi_seven,
    "nonseven_singleton_unchanged": _has_nonseven_singleton,
    "mixed_seven_unchanged": _has_mixed_seven,
}
SEMANTIC_RIVALS = {
    "any_seven": _any_seven,
    "any_singleton": _any_singleton,
    "one_seven_anywhere": _one_seven_anywhere,
}
WITNESS_RIVALS = {
    "multi_seven_unchanged": ["any_seven"],
    "nonseven_singleton_unchanged": ["any_singleton"],
    "mixed_seven_unchanged": ["one_seven_anywhere"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject a lesson when a declared plausible rival fits every demo."""
    reasons = []
    if not demos:
        return ["at least one labeled demonstration is required"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"declared rival {name!r} fits every demonstration")
    return reasons
