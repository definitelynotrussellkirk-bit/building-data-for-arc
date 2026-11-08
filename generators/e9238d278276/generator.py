"""Generator for ``arc_puzzle_bank_sixth21:E41``.

Each column is independent.  Read its non-zero cells from top to bottom, keep
that order, and pack them flush against the top edge; zeros occupy the rest of
the column.

The four-slot schedule keeps three linked canonical morphology anchors and one
larger generalization.  Every four consecutive examples contain a mixed-order
column, so the canonical-training shortcut "sort colors descending, then pack"
is falsified before the query.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "e9238d278276"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "cc6d816e5f2d"

SUMMARY = (
    "For each column independently, collect the non-zero values in their "
    "original top-to-bottom order and place them at rows 0,1,... of that same "
    "column. Fill every remaining cell with 0. Four consecutive generated "
    "examples include all canonical morphology anchors plus a mixed-order "
    "column that refutes descending-color sorting."
)

INVARIANTS = [
    "rectangular 6..16 by 6..16 input grid over ARC colors 0..9",
    "exactly 3..6 active columns and 2..9 distinct non-zero colors",
    "each active column has 1..3 cells and at least one gap above its packed position",
    "at least two active columns contain multiple values, making within-column order visible",
    "the Racket gravity-up rule is the sole output authority; rule_mirror is test-only parity logic",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50

ORDER_PROFILES = ("descending", "mixed")
SCHEDULE_PROFILES = (
    "canonical_6x6",
    "generalized_mixed",
    "canonical_7x7",
    "canonical_8x8_mixed",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical anchor or band draw",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical anchor or band draw",
        "valid": "6..16",
    },
    "n_cols": {
        "type": "int",
        "default": "canonical anchor or rng 3..6",
        "valid": "3..6",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "canonical anchor or rng 2..9",
        "valid": "2..9",
    },
    "order_profile": {
        "type": "str",
        "default": "four-slot schedule",
        "valid": "descending|mixed",
    },
}

# The minimum dimensions and slot construction make every Cartesian boundary
# combination of the five exact axes constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# (height, width, active columns, per-column cell-count multiset,
#  distinct non-zero colors).  This is derived from all canonical train and
# held-out test inputs, not from the generator envelope.
_CANONICAL_SIGNATURES = {
    (6, 6, 4, (1, 2, 2, 2), 7),
    (7, 7, 3, (1, 2, 3), 6),
    (8, 8, 4, (2, 2, 2, 2), 7),
}

# Scheduled anchor metadata.  ``None`` fields identify the generalized slot.
_SCHEDULE = (
    {
        "name": "canonical_6x6",
        "h": 6,
        "w": 6,
        "n_cols": 4,
        "counts": (1, 2, 2, 2),
        "n_colors": 7,
        "order": "descending",
    },
    {
        "name": "generalized_mixed",
        "h": None,
        "w": None,
        "n_cols": None,
        "counts": None,
        "n_colors": None,
        "order": "mixed",
    },
    {
        "name": "canonical_7x7",
        "h": 7,
        "w": 7,
        "n_cols": 3,
        "counts": (1, 2, 3),
        "n_colors": 6,
        "order": "descending",
    },
    {
        "name": "canonical_8x8_mixed",
        "h": 8,
        "w": 8,
        "n_cols": 4,
        "counts": (2, 2, 2, 2),
        "n_colors": 7,
        "order": "mixed",
    },
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the semantic schedule slot for a sample."""
    del seed, difficulty
    return str(_SCHEDULE[int(sample_index) % len(_SCHEDULE)]["name"])


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append("grid must be rectangular")
            return len(grid), width, errors
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                )
                return len(grid), width, errors
    return len(grid), width, errors


def _active_columns(grid: Sequence[Sequence[int]]) -> list[int]:
    return [
        column
        for column in range(len(grid[0]))
        if any(row[column] != 0 for row in grid)
    ]


def _column_values(grid: Sequence[Sequence[int]], column: int) -> list[int]:
    return [row[column] for row in grid if row[column] != 0]


def _column_rows(grid: Sequence[Sequence[int]], column: int) -> list[int]:
    return [row for row in range(len(grid)) if grid[row][column] != 0]


def _signature(grid: Sequence[Sequence[int]]) -> tuple[int, int, int, tuple[int, ...], int]:
    active = _active_columns(grid)
    counts = tuple(sorted(len(_column_values(grid, column)) for column in active))
    palette = {value for row in grid for value in row if value != 0}
    return len(grid), len(grid[0]), len(active), counts, len(palette)


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, degenerate, and rule-hiding input scenes."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 6 <= height <= 16:
        errors.append(f"height {height} outside declared envelope 6..16")
    if not 6 <= width <= 16:
        errors.append(f"width {width} outside declared envelope 6..16")

    active = _active_columns(grid)
    if not 3 <= len(active) <= 6:
        errors.append(f"expected 3..6 active columns, found {len(active)}")

    palette = {value for row in grid for value in row if value != 0}
    if not 2 <= len(palette) <= 9:
        errors.append(f"expected 2..9 distinct non-zero colors, found {len(palette)}")

    multi_value_columns = 0
    for column in active:
        rows = _column_rows(grid, column)
        count = len(rows)
        if not 1 <= count <= 3:
            errors.append(
                f"active column {column} has {count} cells; expected 1..3"
            )
            continue
        if count >= 2:
            multi_value_columns += 1
        if rows == list(range(count)):
            errors.append(
                f"active column {column} is already packed at the top and hides the transformation"
            )
    if multi_value_columns < 2:
        errors.append(
            f"expected at least two multi-value columns, found {multi_value_columns}"
        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Linked empirical manifold from all three canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    signature = _signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        reasons.append(
            "linked signature "
            f"{signature!r} is not one of {sorted(_CANONICAL_SIGNATURES)!r}"
        )
    return reasons


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    active = _active_columns(grid)
    values = [_column_values(grid, column) for column in active]
    descending = all(column == sorted(column, reverse=True) for column in values)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cols": len(active),
        "n_distinct_colors": len(
            {value for row in grid for value in row if value != 0}
        ),
        "order_profile": "descending" if descending else "mixed",
    }


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; Racket remains output authority."""
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for column in range(width):
        for row, value in enumerate(_column_values(grid, column)):
            out[row][column] = value
    return out


def _pack_down(grid: Sequence[Sequence[int]]) -> Grid:
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for column in range(width):
        values = _column_values(grid, column)
        start = height - len(values)
        for offset, value in enumerate(values):
            out[start + offset][column] = value
    return out


def _sort_descending_then_pack_up(grid: Sequence[Sequence[int]]) -> Grid:
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for column in range(width):
        values = sorted(_column_values(grid, column), reverse=True)
        for row, value in enumerate(values):
            out[row][column] = value
    return out


def _pack_rows_left(grid: Sequence[Sequence[int]]) -> Grid:
    return [
        [*([value for value in row if value != 0]), *([0] * row.count(0))]
        for row in grid
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "identity": lambda grid: [list(row) for row in grid],
    "pack_down": _pack_down,
    "sort_descending_then_pack_up": _sort_descending_then_pack_up,
    "pack_each_row_left": _pack_rows_left,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _has_unequal_depths(grid: Any) -> bool:
    if self_check(grid):
        return False
    counts = [len(_column_values(grid, column)) for column in _active_columns(grid)]
    return len(set(counts)) >= 2


SEMANTIC_WITNESSES = {
    "nontrivial_upward_motion": lambda grid: _valid_and_refutes(grid, "identity"),
    "up_not_down": lambda grid: _valid_and_refutes(grid, "pack_down"),
    "mixed_order_refutes_descending_sort": lambda grid: _valid_and_refutes(
        grid, "sort_descending_then_pack_up"
    ),
    "columnwise_not_rowwise": lambda grid: _valid_and_refutes(
        grid, "pack_each_row_left"
    ),
}

WITNESS_RIVALS = {
    "nontrivial_upward_motion": ["identity"],
    "up_not_down": ["pack_down"],
    "mixed_order_refutes_descending_sort": ["sort_descending_then_pack_up"],
    "columnwise_not_rowwise": ["pack_each_row_left"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require a complete schedule window that kills every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def _draw_dimension(ctx: Any, label: str, scheduled: int | None, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 6, 16)
    if scheduled is not None:
        return ctx.draw_int(label, scheduled, scheduled)
    return ctx.draw_int(label, lo, hi)


def _draw_int_axis(
    ctx: Any,
    label: str,
    scheduled: int | None,
    lo: int,
    hi: int,
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if scheduled is not None:
        return ctx.draw_int(label, scheduled, scheduled)
    return ctx.draw_int(label, lo, hi)


def _draw_order(ctx: Any, scheduled: str) -> str:
    options: Sequence[str] = ORDER_PROFILES if "order_profile" in ctx.overrides else (scheduled,)
    return str(ctx.draw_choice("order_profile", options))


def _band_bounds(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 9), (6, 9)
    if difficulty == "hard":
        return (12, 16), (12, 16)
    return (8, 12), (8, 12)


def _general_counts(n_cols: int, n_colors: int, rng: Any) -> list[int]:
    # Two cells per column makes order visible; add a third cell where needed to
    # host every distinct color.  Shuffle which columns receive the extra cell.
    counts = [2] * n_cols
    needed = max(0, n_colors - sum(counts))
    order = list(range(n_cols))
    rng.shuffle(order)
    for index in order[:needed]:
        counts[index] += 1
    # Add some depth diversity without changing the exact axes.
    if needed == 0 and n_cols >= 3 and rng.random() < 0.70:
        counts[order[0]] = 3
    return counts


def _assign_values(
    *, counts: Sequence[int], palette: Sequence[int], order_profile: str, rng: Any
) -> list[list[int]]:
    total = sum(counts)
    flat = [palette[index % len(palette)] for index in range(total)]
    rng.shuffle(flat)
    columns: list[list[int]] = []
    cursor = 0
    for count in counts:
        columns.append(flat[cursor : cursor + count])
        cursor += count

    if order_profile == "descending":
        return [sorted(values, reverse=True) for values in columns]

    # Move two distinct palette values into one multi-value column by swaps;
    # this preserves the exact palette while guaranteeing an ascending pair.
    target_column = next(index for index, values in enumerate(columns) if len(values) >= 2)
    target0 = (target_column, 0)
    target1 = (target_column, 1)
    low, high = min(palette), max(palette)
    positions = [
        (column_index, value_index)
        for column_index, values in enumerate(columns)
        for value_index, _ in enumerate(values)
    ]
    low_pos = next(pos for pos in positions if columns[pos[0]][pos[1]] == low)
    columns[target0[0]][target0[1]], columns[low_pos[0]][low_pos[1]] = (
        columns[low_pos[0]][low_pos[1]],
        columns[target0[0]][target0[1]],
    )
    # Re-find high because the low swap may have touched its old position.
    high_pos = next(
        pos
        for pos in positions
        if columns[pos[0]][pos[1]] == high and pos != target0
    )
    columns[target1[0]][target1[1]], columns[high_pos[0]][high_pos[1]] = (
        columns[high_pos[0]][high_pos[1]],
        columns[target1[0]][target1[1]],
    )
    # In the rare case the swaps crossed, force the target pair by swapping the
    # two positions only; the palette multiset remains unchanged.
    if columns[target_column][0] >= columns[target_column][1]:
        columns[target_column][0], columns[target_column][1] = (
            columns[target_column][1], columns[target_column][0]
        )
    return columns


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    h_bounds, w_bounds = _band_bounds(difficulty)
    height = _draw_dimension(ctx, "grid_h", scheduled["h"], *h_bounds)
    width = _draw_dimension(ctx, "grid_w", scheduled["w"], *w_bounds)
    if scheduled["n_cols"] is None:
        scheduled_n_cols = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
        scheduled_n_colors = {"easy": 5, "medium": 7, "hard": 9}.get(difficulty, 7)
    else:
        scheduled_n_cols = int(scheduled["n_cols"])
        scheduled_n_colors = int(scheduled["n_colors"])
    n_cols = _draw_int_axis(ctx, "n_cols", scheduled_n_cols, 3, 6)
    n_colors = _draw_int_axis(
        ctx, "n_distinct_colors", scheduled_n_colors, 2, 9
    )
    order_profile = _draw_order(ctx, str(scheduled["order"]))

    layout_rng = ctx.draw_rng("layout")
    active_columns = list(range(width))
    layout_rng.shuffle(active_columns)
    active_columns = sorted(active_columns[:n_cols])

    use_anchor_counts = (
        scheduled["counts"] is not None
        and n_cols == scheduled["n_cols"]
        and n_colors <= sum(scheduled["counts"])
    )
    if use_anchor_counts:
        counts = list(scheduled["counts"])
        layout_rng.shuffle(counts)
    else:
        counts = _general_counts(n_cols, n_colors, layout_rng)

    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(list(range(1, 10)), n_colors)
    column_values = _assign_values(
        counts=counts,
        palette=palette,
        order_profile=order_profile,
        rng=ctx.draw_rng("values"),
    )

    grid = full_grid(height, width, 0)
    row_rng = ctx.draw_rng("rows")
    for column, count, values in zip(active_columns, counts, column_values):
        # Rows start at 1, so every active column contains a visible gap above
        # its packed output position.  Sampling without replacement preserves
        # top-to-bottom order unambiguously.
        rows = sorted(row_rng.sample(list(range(1, height)), count))
        for row, value in zip(rows, values):
            grid[row][column] = value

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    for axis, value in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != value:
            raise AssertionError(
                f"axis {axis!r} drew {value!r} but returned grid observes {observed.get(axis)!r}"
            )
    return grid


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Task-semantic impostors that self_check must reject."""
    already_packed = full_grid(6, 6, 0)
    for column, values in ((0, (7, 6)), (2, (5, 4)), (4, (3, 2)), (5, (8,))):
        for row, value in enumerate(values):
            already_packed[row][column] = value

    one_active_column = full_grid(6, 6, 0)
    one_active_column[2][1] = 2
    one_active_column[4][1] = 3
    one_active_column[5][1] = 4

    too_deep = full_grid(6, 6, 0)
    for row, value in zip((1, 2, 4, 5), (2, 3, 4, 5)):
        too_deep[row][0] = value
    for column, value in ((2, 6), (4, 7)):
        too_deep[5][column] = value

    order_hidden = full_grid(6, 6, 0)
    for column, value in ((0, 2), (2, 3), (4, 4), (5, 5)):
        order_hidden[5][column] = value

    one_color = full_grid(6, 6, 0)
    for column in (0, 2, 4):
        one_color[3][column] = 7
        one_color[5][column] = 7

    return [
        ("already_packed_rule_hidden", already_packed),
        ("single_active_column", one_active_column),
        ("four_cells_in_one_column", too_deep),
        ("no_multi_value_columns", order_hidden),
        ("single_color_palette", one_color),
    ]
