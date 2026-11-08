"""Generator for ARC task 6027f42c6c59 — leftmost nonzero per row.

Every active row contains one to three colored marks.  The output keeps the
first nonzero mark in each row and erases the rest.  The five public axes are
recoverable from pixels, have independent legal boundaries, and are accepted
under every difficulty band.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "6027f42c6c59"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e747e7753254"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "In every row, keep only the leftmost nonzero cell. Generated lessons "
    "vary size, active-row count, palette cardinality, and whether exactly "
    "one active row is a singleton, while always making the row-wise rule visible."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "the grid is 5..8 rows by 6..10 columns",
    "at least four rows are active and at least one active row contains multiple marks",
    "each active row has at most three marks",
    "generated grids use exactly 1..7 nonzero colors",
]

AXES = {
    "grid_h": {"type": "int", "default": "nine-step schedule with exact canonical profiles", "valid": "5..8"},
    "grid_w": {"type": "int", "default": "nine-step schedule with exact canonical profiles", "valid": "6..10"},
    "active_rows": {"type": "int", "default": "5", "valid": "4..5"},
    "palette_size": {"type": "int", "default": "nine-step schedule with exact canonical profiles", "valid": "1..7"},
    "row_mode": {
        "type": "str",
        "default": "alternating mixed|all_multi",
        "valid": "mixed|all_multi",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ALLOWED_DIFFICULTIES = frozenset(("easy", "medium", "hard"))
_ALLOWED_OVERRIDES = frozenset(AXES)
_ROW_MODES = ("mixed", "all_multi")


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")

    if difficulty is None:
        band = "medium"
    elif type(difficulty) is str and difficulty in _ALLOWED_DIFFICULTIES:
        band = difficulty
    else:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    for name, lo, hi in (
        ("grid_h", 5, 8),
        ("grid_w", 6, 10),
        ("active_rows", 4, 5),
        ("palette_size", 1, 7),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")

    if "row_mode" in overrides and overrides["row_mode"] is not None:
        value = overrides["row_mode"]
        if type(value) is not str:
            raise TypeError("row_mode must be a string")
        if value not in _ROW_MODES:
            raise ValueError(f"row_mode must be one of {_ROW_MODES}")
    return band


def _draw_int_axis(ctx, name: str, full: tuple[int, int], default: tuple[int, int]) -> int:
    lo, hi = full if ctx.overrides.get(name) is not None else default
    return ctx.draw_int_strict(name, lo, hi)


def _draw_choice_axis(ctx, name: str, domain: Sequence[str], default: str) -> str:
    options = tuple(domain) if ctx.overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


_PROFILE_SCHEDULE = (
    (5, 8, 6),   # exact canonical profile
    (6, 7, 1),
    (6, 7, 6),   # exact canonical profile
    (6, 8, 2),
    (6, 8, 7),   # exact canonical profile
    (7, 6, 3),
    (7, 6, 6),   # exact canonical profile
    (5, 8, 4),
    (6, 7, 5),
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILE_SCHEDULE)))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the nine-step schedule containing all four exact canonical profiles."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    return sample_index % len(_PROFILE_SCHEDULE)


def _default_row_mode(band: str, sample_index: int) -> str:
    if band == "easy":
        return "mixed"
    if band == "hard":
        return "all_multi"
    return _ROW_MODES[sample_index % len(_ROW_MODES)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a lawful, exact-axis example of row-wise leftmost selection."""
    band = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _PROFILE_SCHEDULE[schedule_profile(seed, sample_index, difficulty=band)]
    scheduled_h, scheduled_w, scheduled_palette_size = profile
    h = _draw_int_axis(ctx, "grid_h", (5, 8), (scheduled_h, scheduled_h))
    w = _draw_int_axis(ctx, "grid_w", (6, 10), (scheduled_w, scheduled_w))
    active_rows = _draw_int_axis(ctx, "active_rows", (4, 5), (5, 5))
    palette_size = _draw_int_axis(
        ctx,
        "palette_size",
        (1, 7),
        (scheduled_palette_size, scheduled_palette_size),
    )
    row_mode = _draw_choice_axis(
        ctx,
        "row_mode",
        _ROW_MODES,
        _default_row_mode(band, sample_index),
    )

    palette = list(ctx.draw_distinct_colors("palette", n=palette_size, exclude={0}))
    layout_rng = ctx.draw_rng("layout")
    block_start = layout_rng.randint(0, h - active_rows)
    rows = list(range(block_start, block_start + active_rows))
    singleton_row = rows[-1] if row_mode == "mixed" else None

    # The first active row reserves an adjacent leftmost/erased pair.  When
    # there is spare capacity beyond the requested palette, coloring that pair
    # alike makes one surviving leftmost cell part of a two-cell object.  The
    # canonical training inputs likewise have four persistent singleton markers.
    pair_col = w - 1
    row_slots: dict[int, list[int]] = {}
    for index, row in enumerate(rows):
        if row == singleton_row:
            row_slots[row] = [layout_rng.randrange(w - 1)]
        elif index == 0:
            row_slots[row] = [w - 2, pair_col]
        else:
            row_slots[row] = sorted(layout_rng.sample(range(w - 1), 2))

    assignment_rng = ctx.draw_rng("color_assignment")
    palette_order = list(palette)
    assignment_rng.shuffle(palette_order)
    leftmost_slots = [(row, cols[0]) for row, cols in row_slots.items()]
    erased_slots = [
        (row, col)
        for row, cols in row_slots.items()
        for col in cols[1:]
    ]
    all_slots = leftmost_slots + erased_slots
    component_slots = (leftmost_slots[0], (rows[0], pair_col))
    force_pair = len(all_slots) > palette_size and component_slots[1] in erased_slots

    assignments: dict[tuple[int, int], int] = {}
    if palette_size >= len(leftmost_slots):
        for slot, color in zip(leftmost_slots, palette_order[: len(leftmost_slots)]):
            assignments[slot] = color
        unseen_colors = list(palette_order[len(leftmost_slots) :])
    else:
        for index, slot in enumerate(leftmost_slots):
            assignments[slot] = palette_order[index % palette_size]
        unseen_colors = []

    remaining_erased = list(erased_slots)
    if force_pair:
        assignments[component_slots[1]] = assignments[component_slots[0]]
        remaining_erased.remove(component_slots[1])

    assignment_rng.shuffle(remaining_erased)
    for slot, color in zip(remaining_erased, unseen_colors):
        assignments[slot] = color
    remaining_erased = remaining_erased[len(unseen_colors) :]

    def neighbor_colors(slot: tuple[int, int]) -> set[int]:
        row, col = slot
        return {
            color
            for (other_row, other_col), color in assignments.items()
            if abs(other_row - row) + abs(other_col - col) == 1
        }

    for slot in remaining_erased:
        forbidden = neighbor_colors(slot)
        choices = [color for color in palette_order if color not in forbidden]
        assignments[slot] = assignment_rng.choice(choices or palette_order)

    grid = full_grid(h, w, 0)
    for (row, col), color in assignments.items():
        grid[row][col] = color

    expected = {
        "grid_h": h,
        "grid_w": w,
        "active_rows": active_rows,
        "palette_size": palette_size,
        "row_mode": row_mode,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"constructed axes {observed!r} != requested axes {expected!r}")
    errors = self_check(grid)
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid cells must be exact integer ARC colors 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 8:
        errors.append(f"grid height must be in 5..8, found {h}")
    if not 6 <= w <= 10:
        errors.append(f"grid width must be in 6..10, found {w}")

    row_counts = [sum(value != 0 for value in row) for row in grid]
    active = [index for index, count in enumerate(row_counts) if count]
    if not 4 <= len(active) <= h:
        errors.append(f"expected at least four active rows, found {len(active)}")
    if any(row_counts[index] > 3 for index in active):
        errors.append("each active row may contain at most three nonzero cells")
    if not any(row_counts[index] >= 2 for index in active):
        errors.append("at least one active row must contain multiple nonzero cells")

    palette = {value for row in grid for value in row if value != 0}
    if not 1 <= len(palette) <= 7:
        errors.append(f"expected 1..7 nonzero colors, found {len(palette)}")

    singleton_count = sum(row_counts[index] == 1 for index in active)
    if singleton_count == 1:
        row_mode = "mixed"
    elif singleton_count == 0:
        row_mode = "all_multi"
    else:
        # Canonical inputs may contain more than one singleton row. They are
        # rule-valid but do not correspond to the exact generated row_mode axis.
        row_mode = None

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "active_rows": len(active),
        "palette_size": len(palette),
        "row_mode": row_mode,
        "row_counts": row_counts,
        "active_row_indices": active,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize canonical and generated instances with a visible row rule."""
    del difficulty, meta
    return list(_analysis(grid).get("errors", ()))


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis from generated pixels."""
    scene = _analysis(grid)
    if scene.get("errors"):
        raise ValueError("; ".join(scene["errors"]))
    if scene["row_mode"] is None or not 4 <= scene["active_rows"] <= 5:
        raise ValueError("grid is rule-valid but outside the exact generated axis grammar")
    return {name: scene[name] for name in AXES}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                output[row_index][col_index] = value
                break
    return output


def _rightmost_per_row(grid) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for col_index in range(len(row) - 1, -1, -1):
            value = row[col_index]
            if value != 0:
                output[row_index][col_index] = value
                break
    return output


def _keep_everything(grid) -> list[list[int]]:
    return [list(row) for row in grid]


def _global_leftmost_only(grid) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                output[row_index][col_index] = value
                return output
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "rightmost_per_row": _rightmost_per_row,
    "keep_everything": _keep_everything,
    "global_leftmost_only": _global_leftmost_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def _witness_for(rival_name: str, grid) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "multi_cell_row": lambda grid: _witness_for("keep_everything", grid),
    "left_not_right": lambda grid: _witness_for("rightmost_per_row", grid),
    "multiple_active_rows": lambda grid: _witness_for("global_leftmost_only", grid),
}
WITNESS_RIVALS = {
    "multi_cell_row": ["keep_everything"],
    "left_not_right": ["rightmost_per_row"],
    "multiple_active_rows": ["global_leftmost_only"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the teaching grammar: {errors[0]}"]
    expected = rule_mirror(pair["input"])
    if pair["output"] != expected:
        return [f"{label} output disagrees with per-row leftmost selection"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} fits every demonstration")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    good = generate(
        1701,
        0,
        grid_h=6,
        grid_w=8,
        active_rows=5,
        palette_size=4,
        row_mode="mixed",
    )
    blank = [[0 for _ in range(8)] for _ in range(6)]

    no_multi = [[0 for _ in range(8)] for _ in range(6)]
    for index, row in enumerate(range(5)):
        no_multi[row][index + 1] = (index % 4) + 1

    too_few_rows = deepcopy(good)
    active = [row for row, values in enumerate(too_few_rows) if any(values)]
    for row in active[3:]:
        too_few_rows[row] = [0 for _ in too_few_rows[row]]

    overfull_row = deepcopy(good)
    row = next(index for index, values in enumerate(overfull_row) if any(values))
    for col in range(4):
        overfull_row[row][col] = 1

    return [
        ("blank", blank),
        ("singletons_only", no_multi),
        ("too_few_active_rows", too_few_rows),
        ("four_marks_in_one_row", overfull_row),
    ]
