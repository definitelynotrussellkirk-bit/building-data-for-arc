"""Generator for ARC task 733c1bac8c45 — row-wise left packing.

A lawful teaching input is a zero-background grid with three to nine active
rows.  Every active row contains one to five copies of one row-local color,
and active-row colors are pairwise distinct.  The authoritative Racket rule
counts nonzeros in each row and writes that many copies of the row's first
nonzero color flush left; empty rows stay empty.

The default four-profile schedule contains two canonical-scale cases and two
taller cases with more than four active rows.  Consequently any three-of-four
query rotation retains a demonstration that refutes the canonical-fitting
"five rows only" and "first four active rows only" shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "733c1bac8c45"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "816c15c8ae9f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero-background grid, process each row independently. Count its "
    "nonzero cells and rewrite the row as that many copies of the row's first "
    "nonzero color packed from column 0; empty rows remain empty."
)

INVARIANTS = [
    "grid size is 4..12 rows by 5..14 columns",
    "there are 3..9 active rows and all other rows are zero",
    "each active row contains 1..5 copies of exactly one nonzero color",
    "active rows use pairwise-distinct colors",
    "row populations vary and at least two rows visibly require left packing",
    "at least one row has an internal gap and a cell that travels more than one column",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile schedule; canonical 5 or keyed 6..12",
        "valid": "4..12",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile schedule; canonical 8/9 or keyed 5..14",
        "valid": "5..14",
    },
    "active_rows": {
        "type": "int",
        "default": "four-profile schedule; canonical 3/4 or keyed 5..9",
        "valid": "3..9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("grid_h", "active_rows")]
SCHEDULE_PROFILES = (
    "canonical_three_rows",
    "canonical_four_rows",
    "tall_many_rows_a",
    "tall_many_rows_b",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic four-slot teaching profile."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _incompatible(message: str, *axes: str) -> ValueError:
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    return error


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> dict[str, int]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    supplied: dict[str, int] = {}
    bounds = {"grid_h": (4, 12), "grid_w": (5, 14), "active_rows": (3, 9)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override must be in {lo}..{hi}")
        supplied[name] = value

    if (
        "grid_h" in supplied
        and "active_rows" in supplied
        and supplied["active_rows"] > supplied["grid_h"]
    ):
        raise _incompatible(
            f"grid_h={supplied['grid_h']} cannot contain active_rows={supplied['active_rows']}",
            "grid_h",
            "active_rows",
        )
    return supplied


def _weighted_range(lo: int, hi: int, difficulty: str | None) -> list[int]:
    values = list(range(lo, hi + 1))
    if difficulty == "easy":
        return values + values[: max(1, len(values) // 2)] * 2
    if difficulty == "hard":
        return values + values[max(0, len(values) // 2):] * 2
    return values


def _draw_axes(ctx, profile: str, difficulty: str | None, supplied: dict[str, int]):
    """Draw exact public axes, adapting only unset dependent axes."""
    if not supplied:
        if profile == "canonical_three_rows":
            return (
                ctx.draw_choice("grid_h", (5,)),
                ctx.draw_choice("grid_w", (8,)),
                ctx.draw_choice("active_rows", (3,)),
            )
        if profile == "canonical_four_rows":
            return (
                ctx.draw_choice("grid_h", (5,)),
                ctx.draw_choice("grid_w", (9,)),
                ctx.draw_choice("active_rows", (4,)),
            )
        if profile == "tall_many_rows_a":
            h = ctx.draw_choice("grid_h", _weighted_range(6, 9, difficulty))
            w = ctx.draw_choice("grid_w", _weighted_range(7, 11, difficulty))
            active = ctx.draw_int_strict("active_rows", 5, min(7, h))
            return h, w, active
        h = ctx.draw_choice("grid_h", _weighted_range(8, 12, difficulty))
        w = ctx.draw_choice("grid_w", _weighted_range(10, 14, difficulty))
        active = ctx.draw_int_strict("active_rows", 5, min(9, h))
        return h, w, active

    requested_active = supplied.get("active_rows")
    h_options = _weighted_range(4, 12, difficulty)
    if requested_active is not None and "grid_h" not in supplied:
        h_options = [height for height in h_options if height >= requested_active]
    h = ctx.draw_choice("grid_h", h_options)
    w = ctx.draw_choice("grid_w", _weighted_range(5, 14, difficulty))
    active = ctx.draw_int_strict("active_rows", 3, min(9, h))
    return h, w, active


def _row_counts(active_rows: int, width: int, rng) -> list[int]:
    """Return variable 1..5 populations with fixed witness-bearing anchors."""
    cap = min(5, width - 1)
    counts = [2, cap, 1]
    cycle = [value for value in range(3, cap + 1)] or [2]
    while len(counts) < active_rows:
        counts.append(cycle[(len(counts) - 3) % len(cycle)])
    # Preserve the first three witness roles; vary later rows without weakening them.
    tail = counts[3:]
    rng.shuffle(tail)
    return counts[:3] + tail


def _active_row_ids(height: int, active_rows: int, rng) -> list[int]:
    """Choose active rows and force a visible row below index four when relevant."""
    if height > 5 and active_rows > 4:
        rows = rng.sample(range(height - 1), active_rows - 1) + [height - 1]
    else:
        rows = rng.sample(range(height), active_rows)
    return sorted(rows)


def _positions_for_row(width: int, count: int, slot: int, rng) -> list[int]:
    """Choose a non-left-packed position set; slot zero is a far-gap witness."""
    if slot == 0:
        # _row_counts fixes this row at count two. It simultaneously proves
        # internal-gap collapse and travel farther than one column.
        return [0, width - 1]
    if count == 1:
        return [rng.randrange(1, width)]

    packed = list(range(count))
    for _ in range(128):
        columns = sorted(rng.sample(range(width), count))
        if columns != packed:
            return columns
    # Feasible because count <= width - 1: omit the final packed column and
    # place the last cell at the right edge.
    return list(range(count - 1)) + [width - 1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Draw one deterministic input while honoring every declared exact axis."""
    supplied = _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=supplied,
    )
    height, width, active_rows = _draw_axes(ctx, profile, difficulty, supplied)
    if active_rows > height:
        raise _incompatible(
            f"grid_h={height} cannot contain active_rows={active_rows}",
            "grid_h",
            "active_rows",
        )

    layout_rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("row_colors", n=active_rows, exclude={0}))
    counts = _row_counts(active_rows, width, ctx.draw_rng("row_counts"))
    row_ids = _active_row_ids(height, active_rows, layout_rng)

    grid = full_grid(height, width, 0)
    for slot, (row_id, color, count) in enumerate(zip(row_ids, colors, counts, strict=True)):
        for column in _positions_for_row(width, count, slot, layout_rng):
            grid[row_id][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid left-pack scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "active_rows": active_rows}
    if observed != expected:
        raise RuntimeError(f"axis observer mismatch: expected {expected}, got {observed}")
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list/tuple of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty lists/tuples"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _row_facts(grid):
    facts = []
    for row_index, row in enumerate(grid):
        columns = [index for index, value in enumerate(row) if value != 0]
        if not columns:
            continue
        colors = {row[index] for index in columns}
        facts.append(
            {
                "row": row_index,
                "columns": columns,
                "count": len(columns),
                "colors": colors,
                "color": row[columns[0]],
            }
        )
    return facts


def _moving_rows(grid) -> list[int]:
    expected = rule_mirror(grid)
    return [index for index, (source, target) in enumerate(zip(grid, expected)) if list(source) != target]


def _has_internal_gap(fact) -> bool:
    columns = fact["columns"]
    return any(right - left > 1 for left, right in zip(columns, columns[1:]))


def _has_multi_column_travel(fact) -> bool:
    return any(source - target > 1 for target, source in enumerate(fact["columns"]))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete bounded teaching grammar used by this generator."""
    del meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    if difficulty not in _ALLOWED_DIFFICULTIES:
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]

    height, width = len(grid), len(grid[0])
    if not 4 <= height <= 12:
        errors.append(f"grid height {height} outside 4..12")
    if not 5 <= width <= 14:
        errors.append(f"grid width {width} outside 5..14")

    facts = _row_facts(grid)
    if not 3 <= len(facts) <= 9:
        errors.append(f"need three to nine active rows, got {len(facts)}")
        return errors

    for fact in facts:
        if len(fact["colors"]) != 1:
            errors.append(
                f"row {fact['row']} must use exactly one nonzero color; got {len(fact['colors'])}"
            )
        if not 1 <= fact["count"] <= 5:
            errors.append(
                f"row {fact['row']} must contain one to five nonzero cells; got {fact['count']}"
            )

    colors = [fact["color"] for fact in facts]
    if len(set(colors)) != len(colors):
        errors.append("active rows must use pairwise-distinct nonzero colors")
    if len({fact["count"] for fact in facts}) < 2:
        errors.append("active rows must expose at least two distinct row populations")

    moving = _moving_rows(grid)
    if len(moving) < 2:
        errors.append("need at least two rows that visibly require leftward packing")
    if not any(_has_internal_gap(fact) for fact in facts):
        errors.append("need an active row with an internal zero gap")
    if not any(_has_multi_column_travel(fact) for fact in facts):
        errors.append("need a cell that travels more than one column left")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when an input falls outside the task's teaching manifold."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "active_rows": sum(any(value != 0 for value in row) for row in grid),
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Diagnostic mirror of the unchanged canonical Racket rule."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid: " + "; ".join(errors))
    output: list[list[int]] = []
    for row in grid:
        values = [value for value in row if value != 0]
        if not values:
            output.append([0] * len(row))
        else:
            output.append([values[0]] * len(values) + [0] * (len(row) - len(values)))
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _right_pack(grid):
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        if not values:
            output.append([0] * len(row))
        else:
            output.append([0] * (len(row) - len(values)) + [values[0]] * len(values))
    return output


def _translate_pattern_left(grid):
    output = []
    for row in grid:
        columns = [index for index, value in enumerate(row) if value != 0]
        if not columns:
            output.append([0] * len(row))
            continue
        shift = columns[0]
        moved = [0] * len(row)
        for column in columns:
            moved[column - shift] = row[column]
        output.append(moved)
    return output


def _one_step_left(grid):
    output = []
    for row in grid:
        source = list(row)
        moved = source[:]
        for column in range(1, len(source)):
            if source[column] != 0 and source[column - 1] == 0:
                moved[column - 1] = source[column]
                moved[column] = 0
        output.append(moved)
    return output


def _first_active_row_only(grid):
    output = [list(row) for row in grid]
    for index, row in enumerate(grid):
        if any(value != 0 for value in row):
            output[index] = rule_mirror([row])[0]
            break
    return output


def _fixed_five_rows(grid):
    output = [list(row) for row in grid]
    for index in range(min(5, len(grid))):
        output[index] = rule_mirror([grid[index]])[0]
    return output


def _first_four_active_rows_only(grid):
    output = [list(row) for row in grid]
    transformed = 0
    for index, row in enumerate(grid):
        if not any(value != 0 for value in row):
            continue
        if transformed < 4:
            output[index] = rule_mirror([row])[0]
        transformed += 1
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "right_pack": _right_pack,
    "translate_pattern_left_without_compacting": _translate_pattern_left,
    "move_each_cell_one_step_left": _one_step_left,
    "pack_only_first_active_row": _first_active_row_only,
    "fixed_five_rows": _fixed_five_rows,
    "first_four_active_rows_only": _first_four_active_rows_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_five_rows": _fixed_five_rows,
    "first_four_active_rows_only": _first_four_active_rows_only,
}


def _visible_leftward_motion(grid) -> bool:
    return bool(_moving_rows(grid))


def _multiple_moving_rows(grid) -> bool:
    return len(_moving_rows(grid)) >= 2


def _internal_gap_collapse(grid) -> bool:
    return any(_has_internal_gap(fact) for fact in _row_facts(grid))


def _multi_column_travel(grid) -> bool:
    return any(_has_multi_column_travel(fact) for fact in _row_facts(grid))


def _variable_row_cardinality(grid) -> bool:
    return len({fact["count"] for fact in _row_facts(grid)}) >= 2


def _active_row_below_five(grid) -> bool:
    expected = rule_mirror(grid)
    return any(
        index >= 5 and any(value != 0 for value in row) and list(row) != expected[index]
        for index, row in enumerate(grid)
    )


def _more_than_four_active_rows(grid) -> bool:
    return len(_row_facts(grid)) > 4


SEMANTIC_WITNESSES = {
    "visible_leftward_motion": _visible_leftward_motion,
    "multiple_moving_rows": _multiple_moving_rows,
    "internal_gap_collapse": _internal_gap_collapse,
    "multi_column_travel": _multi_column_travel,
    "variable_row_cardinality": _variable_row_cardinality,
    "active_row_below_five": _active_row_below_five,
    "more_than_four_active_rows": _more_than_four_active_rows,
}

WITNESS_RIVALS = {
    "visible_leftward_motion": ["identity", "right_pack"],
    "multiple_moving_rows": ["pack_only_first_active_row"],
    "internal_gap_collapse": ["translate_pattern_left_without_compacting"],
    "multi_column_travel": ["move_each_cell_one_step_left"],
    "variable_row_cardinality": ["right_pack"],
    "active_row_below_five": ["fixed_five_rows"],
    "more_than_four_active_rows": ["first_four_active_rows_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named alternative survives every demonstration."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output grids")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"{role} output does not match row-wise left packing")

    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked impostors the teaching grammar must reject."""
    blank = full_grid(4, 7, 0)

    two_rows = full_grid(4, 7, 0)
    two_rows[0][2] = 1
    two_rows[2][4] = 2

    multi_color = full_grid(4, 7, 0)
    multi_color[0][1] = 1
    multi_color[0][5] = 4
    multi_color[1][2] = 2
    multi_color[1][6] = 2
    multi_color[3][3] = 3

    duplicate_colors = full_grid(4, 7, 0)
    duplicate_colors[0][1] = 1
    duplicate_colors[0][5] = 1
    duplicate_colors[1][2] = 1
    duplicate_colors[1][6] = 1
    duplicate_colors[3][3] = 3

    already_packed = full_grid(4, 7, 0)
    already_packed[0][:1] = [1]
    already_packed[1][:2] = [2, 2]
    already_packed[3][:3] = [3, 3, 3]

    return [
        ("blank", blank),
        ("only_two_active_rows", two_rows),
        ("multi_color_row", multi_color),
        ("duplicate_row_colors", duplicate_colors),
        ("already_left_packed", already_packed),
    ]
