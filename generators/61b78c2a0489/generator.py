"""Generator for ``61b78c2a0489`` — stable gravity in each column.

The Racket oracle independently removes zeroes from every column and packs the
remaining values against the bottom, preserving their top-to-bottom order.
The teaching distribution therefore uses sparse, horizontally separated active
columns with both stacked and falling values.  A three-sample schedule cycles
through a canonical-like monochrome-column profile, a mixed-color full-height
profile, and a mixed profile with some already-bottomed values.
"""
from __future__ import annotations

from math import ceil

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "61b78c2a0489"
TASK_ID = "61b78c2a0489"
# 3.0.0 broadens the lawful input distribution to canonical lower-row occupancy,
# makes every declared override exact-or-observable, and strengthens self_check.
VERSION = "3.0.0"
RULE_HASH = "aee24df7c267"

SUMMARY = (
    "Generate a sparse rectangular grid on background 0. Nonzero values occupy "
    "at least three horizontally separated columns; at least one column contains "
    "multiple values and at least one value has empty space below it. Across a "
    "three-sample schedule, examples include canonical-like monochrome columns, "
    "mixed-color columns that expose stable order preservation, and scenes with "
    "some values already on the bottom. The output independently removes zeroes "
    "from each column and packs its nonzero values against the bottom without "
    "changing their top-to-bottom order."
)

INVARIANTS = [
    "background is modal color 0",
    "at least three nonzero values use at least two colors",
    "at least two horizontally separated columns are active",
    "at least one active column contains two or more values",
    "at least one value has a zero below it in its own column",
    "normal draws are non-identity under stable downward column compression",
]

LAYOUTS = ("top_heavy", "full_height", "bottom_mixed")
LAYOUT_SCHEDULE = LAYOUTS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5..7 easy / 7..10 medium / 9..12 hard",
        "valid": "4..12",
    },
    "grid_w": {
        "type": "int",
        "default": "5..7 easy / 7..10 medium / 9..12 hard",
        "valid": "5..12",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "difficulty-aware 2..9, profile-feasible when canonical-like",
        "valid": "2..9",
    },
    "layout": {
        "type": "str",
        "default": "three-step sample_index schedule",
        "valid": "|".join(LAYOUTS),
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh input grid for the canonical Racket rule."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h_lo, h_hi, w_lo, w_hi = _difficulty_bounds(difficulty)
    h = _draw_dimension(ctx, "grid_h", h_lo, h_hi, 4, 12)
    w = _draw_dimension(ctx, "grid_w", w_lo, w_hi, 5, 12)
    max_active = (w + 1) // 2

    if overrides.get("layout") is not None:
        layout = ctx.draw_choice("layout", LAYOUTS)
    else:
        layout = LAYOUT_SCHEDULE[int(sample_index) % len(LAYOUT_SCHEDULE)]

    canonical_profile = int(sample_index) % 3 == 0
    if overrides.get("n_distinct_colors") is not None:
        n_colors = ctx.draw_int("n_distinct_colors", 2, 9)
    else:
        color_lo, color_hi = _color_bounds(difficulty)
        if canonical_profile:
            color_hi = min(color_hi, max_active)
        n_colors = ctx.draw_int(
            "n_distinct_colors",
            color_lo,
            max(color_lo, color_hi),
        )

    capacity = max_active * (h - 1)
    if n_colors > capacity:
        # This can only arise from an explicit combination.  Reject rather than
        # silently shrinking the exact requested color count.
        raise ValueError(
            f"n_distinct_colors={n_colors} exceeds sparse teaching capacity "
            f"{capacity} for grid {h}x{w}"
        )

    target_cells = _target_cell_count(ctx, difficulty, n_colors, capacity)
    active_count = _active_column_count(
        target_cells,
        h,
        max_active,
        n_colors=n_colors,
        canonical_profile=canonical_profile,
    )
    columns = _choose_separated_columns(ctx, w, active_count)
    counts = _allocate_counts(ctx, h, columns, target_cells)
    rows_by_column = _choose_rows(ctx, h, columns, counts, layout)

    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={0})
    grid = full_grid(h, w, 0)
    if canonical_profile and n_colors <= len(columns):
        _paint_monochrome_columns(grid, columns, rows_by_column, palette)
    else:
        _paint_mixed_columns(grid, columns, rows_by_column, palette, ctx)

    # Construction is intended to be total, but keep the failure loud if a
    # future edit breaks the teaching grammar.
    problems = self_check(grid, difficulty=difficulty)
    if problems:
        raise RuntimeError("constructed invalid gravity lesson: " + "; ".join(problems))
    return grid


def observe_overrides(grid):
    """Recover every declared exact numeric axis from the returned grid."""
    _validate_grid_shape_and_colors(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_distinct_colors": len({value for row in grid for value in row if value}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sparse teaching grammar while accepting all canonical inputs."""
    problems = _validate_grid_shape_and_colors(grid)
    if problems:
        return problems

    h, w = len(grid), len(grid[0])
    nonzero = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    zero_count = h * w - len(nonzero)
    colors = {value for _, _, value in nonzero}
    active_columns = sorted({c for _, c, _ in nonzero})
    column_counts = {
        c: sum(grid[r][c] != 0 for r in range(h))
        for c in active_columns
    }

    if len(nonzero) < 3:
        problems.append(f"need at least three nonzero values, found {len(nonzero)}")
    if len(colors) < 2:
        problems.append(f"need at least two nonzero colors, found {len(colors)}")
    if zero_count <= len(nonzero):
        problems.append("background 0 is not strictly modal")
    if len(active_columns) < 2:
        problems.append(f"need at least two active columns, found {len(active_columns)}")
    if active_columns and max(column_counts.values()) < 2:
        problems.append("no active column contains a stack of two or more values")

    if any(
        grid[r][c] != 0 and grid[r][c + 1] != 0
        for r in range(h)
        for c in range(w - 1)
    ):
        problems.append("horizontally adjacent nonzero cells violate the sparse-column grammar")

    visible_fall = any(
        grid[r][c] != 0 and any(grid[rr][c] == 0 for rr in range(r + 1, h))
        for r in range(h - 1)
        for c in range(w)
    )
    if not visible_fall:
        problems.append("all columns are already bottom-packed; gravity would be identity")

    return problems


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override axis/axes: {', '.join(unknown)}")


def _difficulty_bounds(difficulty):
    if difficulty == "easy":
        return 5, 7, 5, 7
    if difficulty == "hard":
        return 9, 12, 9, 12
    return 7, 10, 7, 10


def _color_bounds(difficulty):
    if difficulty == "easy":
        return 2, 4
    if difficulty == "hard":
        return 4, 9
    return 3, 6


def _draw_dimension(ctx, label, default_lo, default_hi, valid_lo, valid_hi):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _target_cell_count(ctx, difficulty, n_colors, capacity):
    if difficulty == "easy":
        lo, hi = 5, 7
    elif difficulty == "hard":
        lo, hi = 9, 14
    else:
        lo, hi = 7, 11
    lo = max(lo, n_colors)
    hi = min(max(lo, hi), capacity)
    lo = min(lo, hi)
    return ctx.draw_int("cell_count", lo, hi)


def _active_column_count(target_cells, h, max_active, *, n_colors, canonical_profile):
    minimum = max(3, ceil(target_cells / (h - 1)))
    if canonical_profile and n_colors <= max_active:
        minimum = max(minimum, n_colors)
    # Prefer one spare singleton column when possible; it distinguishes
    # independent column gravity from treating all values as one object.
    if minimum < max_active and target_cells >= minimum + 2:
        minimum += 1
    return min(max_active, minimum)


def _choose_separated_columns(ctx, width, count):
    rng = ctx.draw_rng("active_columns")
    parity_sets = [list(range(0, width, 2)), list(range(1, width, 2))]
    feasible = [cols for cols in parity_sets if len(cols) >= count]
    columns = list(rng.choice(feasible))
    rng.shuffle(columns)
    return sorted(columns[:count])


def _allocate_counts(ctx, height, columns, target_cells):
    rng = ctx.draw_rng("column_counts")
    counts = {column: 1 for column in columns}
    primary = columns[0]
    while counts[primary] < min(3, height - 1) and sum(counts.values()) < target_cells:
        counts[primary] += 1
    if len(columns) > 1:
        secondary = columns[1]
        while counts[secondary] < min(2, height - 1) and sum(counts.values()) < target_cells:
            counts[secondary] += 1
    candidates = list(columns)
    while sum(counts.values()) < target_cells:
        rng.shuffle(candidates)
        for column in candidates:
            if counts[column] < height - 1:
                counts[column] += 1
                break
        else:  # pragma: no cover - capacity checked before allocation
            raise RuntimeError("insufficient column capacity")
    return counts


def _choose_rows(ctx, height, columns, counts, layout):
    rng = ctx.draw_rng("row_positions")
    result = {}
    for index, column in enumerate(columns):
        count = counts[column]
        if layout == "top_heavy":
            pool = list(range(height - 1))
            chosen = set(rng.sample(pool, count))
            if index == 0 and count >= 2:
                chosen.discard(max(chosen))
                chosen.update({0, height - 2})
                while len(chosen) > count:
                    chosen.remove(next(v for v in sorted(chosen, reverse=True) if v not in {0, height - 2}))
                while len(chosen) < count:
                    chosen.add(rng.choice([r for r in pool if r not in chosen]))
        elif layout == "bottom_mixed":
            pool = list(range(height))
            chosen = set(rng.sample(pool, count))
            if index == 0 and count >= 2:
                chosen.add(height - 1)
                chosen.add(0)
            elif index == 1:
                chosen.discard(height - 1)
                chosen.add(0)
            chosen = _resize_row_set(chosen, count, pool, rng, protected={0} | ({height - 1} if index == 0 else set()))
        else:  # full_height
            pool = list(range(height))
            chosen = set(rng.sample(pool, count))
            if index == 0 and count >= 2:
                chosen.update({0, height - 1})
            chosen = _resize_row_set(chosen, count, pool, rng, protected={0, height - 1} if index == 0 and count >= 2 else set())
        result[column] = sorted(chosen)
    return result


def _resize_row_set(chosen, count, pool, rng, *, protected):
    while len(chosen) > count:
        removable = [row for row in chosen if row not in protected]
        chosen.remove(rng.choice(removable))
    while len(chosen) < count:
        chosen.add(rng.choice([row for row in pool if row not in chosen]))
    return chosen


def _paint_monochrome_columns(grid, columns, rows_by_column, palette):
    for index, column in enumerate(columns):
        color = palette[index % len(palette)]
        for row in rows_by_column[column]:
            grid[row][column] = color


def _paint_mixed_columns(grid, columns, rows_by_column, palette, ctx):
    rng = ctx.draw_rng("cell_colors")
    positions = [(row, column) for column in columns for row in rows_by_column[column]]
    assignments = {position: rng.choice(palette) for position in positions}

    primary_positions = [(row, columns[0]) for row in rows_by_column[columns[0]]]
    assignments[primary_positions[0]] = palette[0]
    assignments[primary_positions[1]] = palette[1]
    reserved = set(primary_positions[:2])
    unused_colors = list(palette[2:])
    remaining_positions = [position for position in positions if position not in reserved]
    rng.shuffle(remaining_positions)
    for color, position in zip(unused_colors, remaining_positions):
        assignments[position] = color

    for (row, column), color in assignments.items():
        grid[row][column] = color


def _validate_grid_shape_and_colors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) and len(row) for row in grid):
        return ["grid contains an empty or invalid row"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"]
    height = len(grid)
    problems = []
    if not (4 <= height <= 12 and 5 <= width <= 12):
        problems.append(f"grid size {height}x{width} outside 4..12 by 5..12")
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                problems.append(
                    f"cell ({row_index},{column_index}) is not an ARC color: {value!r}"
                )
                return problems
    return problems
