"""Generator for arc_puzzle_bank_nineteenth_21_bundle:easy_131_transpose_square_grid.

The input is a sparse 5..14 square grid.  The authoritative rule swaps every
cell coordinate: output[c][r] = input[r][c].  Default draws stay on the linked
canonical profile (size 5..8, four or five distinct nonzero cells) while a
four-step position schedule covers upper-only, lower-only, both-triangle, and
diagonal-control scenes.  Occupied off-diagonal coordinates never include
both members of a transpose pair, so every ordinary draw visibly changes.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3f4b5ff68c93"
TASK_ID = "3f4b5ff68c93"
VERSION = "2.0.0"
RULE_HASH = "f5d00e3992ee"

SUMMARY = (
    "Create a sparse square ARC grid and transpose it across the main diagonal. "
    "Default instances use sizes 5..8, contain four or five distinct nonzero "
    "cells, and deterministically cycle through upper-triangle, lower-triangle, "
    "two-sided, and diagonal-plus-off-diagonal layouts.  The output has the same "
    "dimensions and palette, with every input cell at (r,c) moved to (c,r)."
)

INVARIANTS = [
    "the input is a square grid with side length 5..8",
    "all cells are integer ARC colors in 0..9 and background is 0",
    "ordinary generated inputs contain four or five nonzero cells",
    "at least one nonzero cell is off the main diagonal",
    "ordinary generated inputs keep nonzero cells orthogonally separated",
]

POSITION_PATTERNS = ("upper", "lower", "mixed", "diagonal_mix")
SCHEDULE_PROFILES = POSITION_PATTERNS
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware scheduled value in 5..8",
        "valid": "5..8",
    },
    "cell_count": {
        "type": "int",
        "default": "scheduled 4 or 5",
        "valid": "4..5",
    },
    "palette_size": {
        "type": "int",
        "default": "equal to cell_count",
        "valid": "4..5",
    },
    "position_pattern": {
        "type": "str",
        "default": "sample-index cycle",
        "valid": "|".join(POSITION_PATTERNS),
    },
}

_BAND_SIZES = {
    "easy": (5, 6),
    "medium": (5, 6, 7, 8),
    "hard": (7, 8),
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_size", "cell_count", "palette_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    pattern = overrides.get("position_pattern")
    if pattern is not None and pattern not in POSITION_PATTERNS:
        raise ValueError(
            "position_pattern must be one of " + ", ".join(POSITION_PATTERNS)
        )


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return POSITION_PATTERNS[sample_index % len(POSITION_PATTERNS)]


def _draw_grid_size(ctx, seed, sample_index, band):
    if ctx.overrides.get("grid_size") is not None:
        return ctx.draw_int("grid_size", 5, 8)
    lo, hi = min(_BAND_SIZES[band]), max(_BAND_SIZES[band])
    return ctx.draw_int("grid_size", lo, hi)


def _draw_counts(ctx, seed, sample_index):
    del seed, sample_index
    requested_count = ctx.overrides.get("cell_count")
    requested_palette = ctx.overrides.get("palette_size")

    palette_size = None
    if requested_palette is not None:
        palette_size = ctx.draw_int("palette_size", 4, 5)

    if requested_count is not None:
        cell_count = ctx.draw_int("cell_count", 4, 5)
    elif palette_size is not None:
        cell_count = ctx.draw_int("cell_count", palette_size, 5)
    else:
        cell_count = ctx.draw_int("cell_count", 4, 5)

    if palette_size is None:
        palette_size = ctx.draw_int("palette_size", cell_count, cell_count)
    if palette_size > cell_count:
        raise ValueError(
            f"palette_size={palette_size} cannot exceed cell_count={cell_count}"
        )
    return cell_count, palette_size


def _draw_pattern(ctx, sample_index):
    if ctx.overrides.get("position_pattern") is not None:
        return ctx.draw_choice("position_pattern", POSITION_PATTERNS)
    value = POSITION_PATTERNS[sample_index % len(POSITION_PATTERNS)]
    return ctx.draw_choice("position_pattern", (value,))


def _choose_positions(n, count, pattern, rng):
    if pattern == "upper":
        candidates = [(r, c) for r in range(n) for c in range(r + 1, n)]
    elif pattern == "lower":
        candidates = [(c, r) for r in range(n) for c in range(r + 1, n)]
    elif pattern == "mixed":
        candidates = [(r, c) for r in range(n) for c in range(n) if r != c]
    elif pattern == "diagonal_mix":
        candidates = [(r, c) for r in range(n) for c in range(n)]
    else:
        raise AssertionError(f"unhandled pattern {pattern!r}")

    def compatible(position, chosen):
        row, col = position
        for old_row, old_col in chosen:
            if (row, col) == (old_col, old_row) and row != col:
                return False
            if abs(row - old_row) + abs(col - old_col) == 1:
                return False
        return True

    def complete(chosen):
        above = any(r < c for r, c in chosen)
        below = any(r > c for r, c in chosen)
        diagonal = any(r == c for r, c in chosen)
        if pattern == "upper":
            return above and not below and not diagonal
        if pattern == "lower":
            return below and not above and not diagonal
        if pattern == "mixed":
            return above and below and not diagonal
        return diagonal and (above or below)

    for _attempt in range(24):
        ordered = candidates[:]
        rng.shuffle(ordered)

        def search(start, chosen):
            if len(chosen) == count:
                return chosen[:] if complete(chosen) else None
            if len(chosen) + len(ordered) - start < count:
                return None
            for index in range(start, len(ordered)):
                candidate = ordered[index]
                if not compatible(candidate, chosen):
                    continue
                chosen.append(candidate)
                found = search(index + 1, chosen)
                if found is not None:
                    return found
                chosen.pop()
            return None

        found = search(0, [])
        if found is not None:
            return found
    raise RuntimeError(
        f"could not place {count} separated cells in {n}x{n} pattern {pattern}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _BAND_SIZES else "medium"
    n = _draw_grid_size(ctx, seed, sample_index, band)
    cell_count, palette_size = _draw_counts(ctx, seed, sample_index)
    pattern = _draw_pattern(ctx, sample_index)

    # n>=5 gives ten unordered off-diagonal pairs, enough for every declared
    # count while still forbidding transpose-pair collisions.
    palette = list(
        ctx.draw_distinct_colors("palette", n=palette_size, exclude={0})
    )
    rng = ctx.draw_rng("layout")
    positions = _choose_positions(n, cell_count, pattern, rng)
    values = [palette[index % palette_size] for index in range(cell_count)]
    rng.shuffle(values)

    grid = full_grid(n, n, 0)
    for (row, col), value in zip(positions, values):
        grid[row][col] = value
    return grid


def _nonzero_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _position_pattern(grid):
    cells = _nonzero_cells(grid)
    if not cells:
        return "other"
    diagonal = any(row == col for row, col, _ in cells)
    above = any(row < col for row, col, _ in cells)
    below = any(row > col for row, col, _ in cells)
    if diagonal and (above or below):
        return "diagonal_mix"
    if above and not below and not diagonal:
        return "upper"
    if below and not above and not diagonal:
        return "lower"
    if above and below and not diagonal:
        return "mixed"
    return "other"


def observe_overrides(grid):
    cells = _nonzero_cells(grid)
    return {
        "grid_size": len(grid),
        "cell_count": len(cells),
        "palette_size": len({value for _, _, value in cells}),
        "position_pattern": _position_pattern(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    height = len(grid)
    errors = []
    if height != width:
        errors.append(f"grid must be square; got {height}x{width}")
    if not 5 <= height <= 8 or not 5 <= width <= 8:
        errors.append("grid side length must be in 5..8")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors in 0..9")
        return errors

    cells = _nonzero_cells(grid)
    if len(cells) not in (4, 5):
        errors.append(f"expected four or five nonzero cells, found {len(cells)}")
    if cells and not any(row != col for row, col, _ in cells):
        errors.append("at least one nonzero cell must be off the main diagonal")
    occupied = {(row, col) for row, col, _ in cells}
    adjacent = sorted(
        (row, col)
        for row, col in occupied
        if (row + 1, col) in occupied or (row, col + 1) in occupied
    )
    if adjacent:
        errors.append(
            "nonzero cells must be orthogonally separated; adjacency starts at "
            f"{adjacent[0]}"
        )
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    cells = _nonzero_cells(grid)
    reasons = []
    if len({value for _, _, value in cells}) != len(cells):
        reasons.append("canonical inputs use a distinct color for every nonzero cell")
    return reasons


def rule_mirror(grid):
    return [list(row) for row in zip(*grid)]


def _identity(grid):
    return [list(row) for row in grid]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _upper_only_transpose(grid):
    out = full_grid(len(grid), len(grid), 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if row < col:
                out[col][row] = value
            else:
                out[row][col] = value
    return out


def _lower_only_transpose(grid):
    out = full_grid(len(grid), len(grid), 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if row > col:
                out[col][row] = value
            else:
                out[row][col] = value
    return out


def _clear_diagonal_transpose(grid):
    out = rule_mirror(grid)
    for index in range(len(out)):
        out[index][index] = 0
    return out


def _transpose_first_nonzero(grid):
    out = full_grid(len(grid), len(grid), 0)
    for row, col, value in _nonzero_cells(grid)[:1]:
        out[col][row] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _identity,
    "flip_left_right": _flip_lr,
    "flip_up_down": _flip_ud,
    "rotate_180": _rotate_180,
    "transpose_upper_triangle_only": _upper_only_transpose,
    "transpose_lower_triangle_only": _lower_only_transpose,
    "transpose_but_clear_diagonal": _clear_diagonal_transpose,
    "transpose_first_nonzero_only": _transpose_first_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _lawful(grid):
    return not self_check(grid)


def _rival_differs(grid, rival):
    return _lawful(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "upper_triangle_scene": lambda grid: (
        _position_pattern(grid) == "upper"
        and _rival_differs(grid, _lower_only_transpose)
    ),
    "lower_triangle_scene": lambda grid: (
        _position_pattern(grid) == "lower"
        and _rival_differs(grid, _upper_only_transpose)
    ),
    "both_triangles_scene": lambda grid: (
        _position_pattern(grid) == "mixed"
        and _rival_differs(grid, _upper_only_transpose)
        and _rival_differs(grid, _lower_only_transpose)
    ),
    "diagonal_fixed_point_control": lambda grid: (
        _position_pattern(grid) == "diagonal_mix"
        and _rival_differs(grid, _clear_diagonal_transpose)
    ),
    "all_sparse_cells_move_or_stay_by_coordinate_swap": lambda grid: (
        _rival_differs(grid, _transpose_first_nonzero)
    ),
    "identity_is_not_the_rule": lambda grid: _rival_differs(grid, _identity),
}
WITNESS_RIVALS = {
    "upper_triangle_scene": ["identity", "transpose_lower_triangle_only"],
    "lower_triangle_scene": ["identity", "transpose_upper_triangle_only"],
    "both_triangles_scene": [
        "transpose_upper_triangle_only",
        "transpose_lower_triangle_only",
    ],
    "diagonal_fixed_point_control": ["transpose_but_clear_diagonal"],
    "all_sparse_cells_move_or_stay_by_coordinate_swap": [
        "transpose_first_nonzero_only"
    ],
    "identity_is_not_the_rule": ["identity"],
}


def lesson_identifiable(demos, query):
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with matrix transpose")
    if reasons:
        return reasons

    demo_patterns = {_position_pattern(pair["input"]) for pair in demos}
    missing = sorted(set(POSITION_PATTERNS) - demo_patterns)
    if missing:
        reasons.append(
            "demonstrations omit scheduled position branch(es): " + ", ".join(missing)
        )
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute shortcut {name!r}")
    return reasons


def mutation_fixtures():
    valid = generate(20260728, 3, difficulty="medium")

    non_square = [row[:-1] for row in valid]

    bad_color = [row[:] for row in valid]
    bad_color[0][0] = 10

    single_diagonal = full_grid(5, 5, 0)
    single_diagonal[2][2] = 3

    all_diagonal = full_grid(5, 5, 0)
    all_diagonal[0][0] = 1
    all_diagonal[3][3] = 2

    too_many = full_grid(5, 5, 0)
    for index, (row, col) in enumerate(
        [(r, c) for r in range(5) for c in range(r + 1, 5)]
    ):
        too_many[row][col] = 1 + (index % 9)

    return [
        ("non_square", non_square),
        ("color_outside_arc_palette", bad_color),
        ("only_one_nonzero", single_diagonal),
        ("diagonal_only_identity_scene", all_diagonal),
        ("too_many_nonzero_cells", too_many),
    ]
