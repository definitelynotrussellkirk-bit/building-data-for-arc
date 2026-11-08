"""Generator for arc_puzzle_bank_seventh21:E46 — row-wise gravity right.

Each row is transformed independently: remove zeros, preserve the remaining
left-to-right color order, and place that sequence flush against the right edge.
The teaching grammar deliberately includes multiple active rows with different
cardinalities, a non-monotone color sequence, and multi-cell travel so common
identity, sorting, reversal, one-step-shift, and first-row-only shortcuts fail.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "735ba14c7162"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "63d032c43a96"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero-background grid, process each row independently. Keep every "
    "nonzero cell in its original left-to-right order, remove the intervening "
    "zeros, and right-align the resulting sequence. Empty rows remain empty."
)

INVARIANTS = [
    "background is color 0",
    "rows transform independently",
    "each active row contains one to four nonzero cells",
    "the nonzero left-to-right order is preserved",
    "all active rows require visible rightward compaction",
    "at least three active rows and two row cardinalities make the row-wise rule observable",
]

# Only properties exactly recoverable from the returned grid are public axes.
# Layout positions and color order remain deterministic nuisance variation.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed choice in 4..8",
        "valid": "4..8",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed choice in 7..11",
        "valid": "7..11",
    },
    "active_rows": {
        "type": "int",
        "default": "choice in 3..grid_h",
        "valid": "3..8",
    },
    "palette_size": {
        "type": "int",
        "default": "canonical-skewed choice in 4..9",
        "valid": "4..9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("grid_h", "active_rows")]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")


def _difficulty_options(difficulty: str | None) -> tuple[list[int], list[int]]:
    """Return height/width options while retaining canonical scale in each band."""
    # Keep every declared value overrideable in every band; duplicates provide
    # only a soft ordinary-draw skew.
    if difficulty == "easy":
        return [4, 4, 4, 5, 5, 5, 6, 7, 8], [7, 7, 8, 8, 9, 9, 10, 11]
    if difficulty == "hard":
        return [4, 4, 5, 5, 5, 6, 7, 8], [7, 8, 8, 9, 9, 9, 10, 11]
    return [4, 4, 5, 5, 5, 6, 7, 8], [7, 7, 8, 8, 9, 9, 10, 11]


def _row_counts(active_rows: int, width: int, palette_size: int, rng) -> list[int]:
    """Build 1..4 counts using every palette color and at least two counts."""
    capacity = min(4, width - 1)
    counts = [1] * active_rows

    # Ensure one order-sensitive row and enough total cells to expose every
    # requested palette color exactly in the returned grid.
    counts[0] = min(4, capacity)
    target_total = max(palette_size, active_rows + 3)
    cursor = 1
    while sum(counts) < target_total:
        index = cursor % active_rows
        cursor += 1
        if counts[index] < capacity:
            counts[index] += 1
        elif all(value >= capacity for value in counts):
            break

    if len(set(counts)) == 1:
        donor = next((i for i, value in enumerate(counts) if value > 1), None)
        receiver = next((i for i, value in enumerate(counts) if value < capacity), None)
        if donor is not None and receiver is not None and donor != receiver:
            counts[donor] -= 1
            counts[receiver] += 1

    rng.shuffle(counts)
    # Keep a >=3-cell row first so color-order construction can force a
    # sorting/reversal discriminator without changing public axes.
    longest = max(range(active_rows), key=counts.__getitem__)
    counts[0], counts[longest] = counts[longest], counts[0]
    return counts


def _order_discriminative(values: list[int]) -> bool:
    return (
        len(values) >= 3
        and len(set(values)) == len(values)
        and values != sorted(values)
        and values != sorted(values, reverse=True)
        and values != list(reversed(values))
    )


def _color_rows(counts: list[int], palette: list[int], rng) -> list[list[int]]:
    total = sum(counts)
    stream = palette[:]
    rng.shuffle(stream)
    while len(stream) < total:
        stream.append(rng.choice(palette))

    first_count = counts[0]
    first = stream[:first_count]
    for _ in range(32):
        rng.shuffle(first)
        if _order_discriminative(first):
            break
    if not _order_discriminative(first):
        # With >=3 distinct values a finite deterministic permutation always
        # exists; enumerate rather than weakening the witness.
        candidates = [first, first[1:] + first[:1], first[-1:] + first[:-1]]
        first = next(candidate for candidate in candidates if _order_discriminative(candidate))
    stream[:first_count] = first

    rows: list[list[int]] = []
    offset = 0
    for count in counts:
        rows.append(stream[offset:offset + count])
        offset += count
    return rows


def _positions_for_row(width: int, count: int, row_slot: int, rng) -> list[int]:
    """Choose a non-right-packed position set; slot 0 requires >1 travel."""
    packed = list(range(width - count, width))
    for _ in range(128):
        if row_slot == 0:
            # Force a far-left cue so one-step-shift cannot match gravity.
            tail_pool = list(range(1, width - 1))
            others = rng.sample(tail_pool, count - 1) if count > 1 else []
            cols = sorted({0, *others})
            if len(cols) != count:
                continue
        else:
            cols = sorted(rng.sample(range(width), count))
        if cols == packed:
            continue
        if any(target - source > 1 for source, target in zip(cols, packed)):
            return cols
    raise RuntimeError("failed to construct a visibly non-packed row")


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
    rng = ctx.draw_rng("layout")
    h_options, w_options = _difficulty_options(difficulty)
    requested_rows = overrides.get("active_rows")
    requested_h = overrides.get("grid_h")
    if requested_rows is not None and requested_h is not None and requested_rows > requested_h:
        raise ValueError(
            f"grid_h={requested_h} cannot contain active_rows={requested_rows}"
        )
    if requested_rows is not None and requested_h is None:
        h_options = [value for value in h_options if value >= requested_rows]
    h = ctx.draw_choice("grid_h", h_options)
    w = ctx.draw_choice("grid_w", w_options)
    active_rows = ctx.draw_int("active_rows", 3, h)
    palette_size = ctx.draw_choice(
        "palette_size",
        [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 8, 7, 6, 5, 4],
    )

    palette = list(range(1, 10))
    rng.shuffle(palette)
    palette = palette[:palette_size]
    counts = _row_counts(active_rows, w, palette_size, rng)
    values_by_row = _color_rows(counts, palette, rng)

    grid = full_grid(h, w, 0)
    row_ids = sorted(rng.sample(range(h), active_rows))
    for slot, (row_id, values) in enumerate(zip(row_ids, values_by_row)):
        cols = _positions_for_row(w, len(values), slot, rng)
        for col, value in zip(cols, values):
            grid[row_id][col] = value

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid row-gravity scene: " + "; ".join(errors))
    if not _order_witness(grid):
        raise RuntimeError("constructed scene lacks a sorting/reversal witness")
    if observe_overrides(grid) != {
        "grid_h": h,
        "grid_w": w,
        "active_rows": active_rows,
        "palette_size": palette_size,
    }:
        raise RuntimeError("returned grid does not preserve keyed axis values")
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _row_values(row: list[int]) -> list[int]:
    return [value for value in row if value != 0]


def _right_packed(row: list[int]) -> bool:
    values = _row_values(row)
    return row == [0] * (len(row) - len(values)) + values


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject rule-hiding or structurally impoverished teaching scenes."""
    errors = _shape_errors(grid)
    if errors:
        return errors

    h, w = len(grid), len(grid[0])
    if not 4 <= h <= 8:
        errors.append(f"height must be in 4..8, got {h}")
    if not 7 <= w <= 11:
        errors.append(f"width must be in 7..11, got {w}")

    active = [(index, _row_values(row)) for index, row in enumerate(grid) if any(row)]
    if len(active) < 3:
        errors.append(f"need at least three active rows, got {len(active)}")
        return errors

    counts = [len(values) for _, values in active]
    if any(not 1 <= count <= 4 for count in counts):
        errors.append("every active row must contain one to four nonzero cells")
    if len(set(counts)) < 2:
        errors.append("active rows must expose at least two different nonzero counts")

    palette = {value for row in grid for value in row if value != 0}
    if len(palette) < 4:
        errors.append(f"need at least four distinct nonzero colors, got {len(palette)}")

    moving_rows = [index for index, _ in active if not _right_packed(grid[index])]
    if len(moving_rows) != len(active):
        errors.append("every active row must visibly require rightward packing")

    if not any(
        any(target - source > 1 for source, target in zip(
            [i for i, value in enumerate(grid[index]) if value != 0],
            range(w - len(values), w),
        ))
        for index, values in active
    ):
        errors.append("need a row whose cells travel more than one column")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked manifold: sparse row sequences requiring right compaction."""
    errors = self_check(grid)
    if errors:
        return errors
    for index, row in enumerate(grid):
        values = _row_values(row)
        if values and _right_packed(row):
            errors.append(f"active row {index} is already right-packed")
        if len(values) > 4:
            errors.append(f"active row {index} exceeds the canonical four-cell maximum")
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "active_rows": sum(any(value != 0 for value in row) for row in grid),
        "palette_size": len({value for row in grid for value in row if value != 0}),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic mirror; the canonical Racket gravity rule is authoritative."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful ARC grid")
    output: list[list[int]] = []
    for row in grid:
        values = _row_values(row)
        output.append([0] * (len(row) - len(values)) + values)
    return output


def _identity(grid):
    return [row[:] for row in grid]


def _left_pack(grid):
    return [_row_values(row) + [0] * (len(row) - len(_row_values(row))) for row in grid]


def _reverse_then_right(grid):
    output = []
    for row in grid:
        values = list(reversed(_row_values(row)))
        output.append([0] * (len(row) - len(values)) + values)
    return output


def _sort_then_right(grid):
    output = []
    for row in grid:
        values = sorted(_row_values(row))
        output.append([0] * (len(row) - len(values)) + values)
    return output


def _first_active_row_only(grid):
    output = [row[:] for row in grid]
    for index, row in enumerate(grid):
        if any(value != 0 for value in row):
            output[index] = rule_mirror([row])[0]
            break
    return output


def _one_step_right(grid):
    """Move each row's cells at most one column right without crossing."""
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(len(row) - 2, -1, -1):
            if output[r][c] != 0 and output[r][c + 1] == 0:
                output[r][c + 1] = output[r][c]
                output[r][c] = 0
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "left_pack": _left_pack,
    "reverse_order_then_right_pack": _reverse_then_right,
    "sort_colors_then_right_pack": _sort_then_right,
    "pack_only_first_active_row": _first_active_row_only,
    "move_each_cell_one_step_right": _one_step_right,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _active_rows(grid) -> list[list[int]]:
    return [row for row in grid if any(value != 0 for value in row)]


def _visible_motion(grid) -> bool:
    return any(row != packed for row, packed in zip(grid, rule_mirror(grid)))


def _multiple_moving_rows(grid) -> bool:
    return sum(row != packed for row, packed in zip(grid, rule_mirror(grid))) >= 2


def _order_witness(grid) -> bool:
    return any(_order_discriminative(_row_values(row)) for row in _active_rows(grid))


def _multi_column_travel(grid) -> bool:
    width = len(grid[0])
    for row in _active_rows(grid):
        source = [index for index, value in enumerate(row) if value != 0]
        target = list(range(width - len(source), width))
        if any(dst - src > 1 for src, dst in zip(source, target)):
            return True
    return False


def _variable_row_cardinality(grid) -> bool:
    return len({len(_row_values(row)) for row in _active_rows(grid)}) >= 2


SEMANTIC_WITNESSES = {
    "visible_rightward_motion": _visible_motion,
    "multiple_moving_rows": _multiple_moving_rows,
    "order_discriminative_row": _order_witness,
    "multi_column_travel": _multi_column_travel,
    "variable_row_cardinality": _variable_row_cardinality,
}

WITNESS_RIVALS = {
    "visible_rightward_motion": ["identity", "left_pack"],
    "multiple_moving_rows": ["pack_only_first_active_row"],
    "order_discriminative_row": [
        "reverse_order_then_right_pack",
        "sort_colors_then_right_pack",
    ],
    "multi_column_travel": ["move_each_cell_one_step_right"],
    "variable_row_cardinality": ["move_each_cell_one_step_right"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut survives every demonstration."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        errors = strict_canonical_like(pair.get("input"))
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"{role} output does not match row-wise right gravity")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked impostors that the teaching grammar must reject."""
    blank = full_grid(5, 8, 0)

    singleton = [row[:] for row in blank]
    singleton[2][2] = 3

    short_line = [row[:] for row in blank]
    short_line[2][2:4] = [3, 4]

    solid_2x2 = [row[:] for row in blank]
    for r in (1, 2):
        for c in (2, 3):
            solid_2x2[r][c] = 4

    already_packed = [row[:] for row in blank]
    already_packed[0][-3:] = [3, 1, 2]
    already_packed[2][-2:] = [7, 8]
    already_packed[4][-1:] = [9]


    return [
        ("singleton", singleton),
        ("single_short_line", short_line),
        ("solid_2x2", solid_2x2),
        ("all_rows_already_right_packed", already_packed),
    ]
