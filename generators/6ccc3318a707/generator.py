"""Generator for task 6ccc3318a707: full-grid anti-diagonal reflection.

The selected rule is a *move*, not a symmetry-completion overlay.  For an
``n x n`` input, every cell at ``(r, c)`` moves to
``(n - 1 - c, n - 1 - r)``.  The curriculum deliberately includes fixed
points, singleton mirror orbits, occupied mirror pairs with different colors,
and repeated colors so plausible partial-reflection shortcuts are observable.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6ccc3318a707"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ea62a41435bf"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Reflect the entire square grid across the anti-diagonal. Every cell at "
    "(r,c) moves to (n-1-c,n-1-r); anti-diagonal cells are fixed. Ordinary "
    "draws use exactly four foreground colors and include fixed points, "
    "singletons, and differently colored occupied mirror pairs so copy/overlay, "
    "collision-skipping, color-unique-only, and main-diagonal shortcuts fail."
)

INVARIANTS = [
    "background is color 0 and exactly four distinct nonzero colors are present",
    "input is a square 6x6, 7x7, or 8x8 ARC grid",
    "the output is the full-grid anti-diagonal reflection, not an overlay",
    "ordinary draws contain fixed points, singleton orbits, and occupied pairs",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "rng 6..8",
        "valid": "6..8",
        "doc": "Square side length; exactly observable as len(grid).",
    },
    "diagonal_marks": {
        "type": "int",
        "default": "rng 1..2",
        "valid": "1..2",
        "doc": "Occupied anti-diagonal fixed points.",
    },
    "mirror_pairs": {
        "type": "int",
        "default": "rng 1..2",
        "valid": "1..2",
        "doc": "Off-diagonal anti-mirror orbits with both endpoints occupied.",
    },
    "singletons": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
        "doc": "Off-diagonal anti-mirror orbits with exactly one endpoint occupied.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]


def _anti(cell: Cell, n: int) -> Cell:
    r, c = cell
    return n - 1 - c, n - 1 - r


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def _shape_errors(grid: Any) -> tuple[list[str], int | None]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], None
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"], None
    if not grid[0]:
        return ["grid rows must be non-empty"], None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"], None
    if len(grid) != width:
        return [f"grid must be square, found {len(grid)}x{width}"], None
    if not 6 <= len(grid) <= 8:
        return [f"grid size {len(grid)} is outside 6..8"], None
    return [], len(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task manifold while accepting every canonical input."""
    del difficulty
    errors, n = _shape_errors(grid)
    if errors or n is None:
        return errors

    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    foreground = [value for row in grid for value in row if value != 0]
    colors = set(foreground)
    if not 4 <= len(foreground) <= 9:
        errors.append(
            f"expected 4..9 foreground cells, found {len(foreground)}"
        )
    if len(colors) != 4:
        errors.append(
            f"expected exactly four distinct foreground colors, found {len(colors)}"
        )
    if foreground and not any(
        grid[r][c] != 0 and r + c != n - 1
        for r in range(n)
        for c in range(n)
    ):
        errors.append("at least one foreground cell must lie off the anti-diagonal")

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict) and not errors:
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if name in AXES and observed.get(name) != expected:
                errors.append(
                    f"override {name}={expected!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict task manifold is the same grammar accepted by self_check."""
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Pure-Python diagnostic mirror of the selected canonical Racket rule."""
    n = len(grid)
    return [
        [int(grid[n - 1 - c][n - 1 - r]) for c in range(n)]
        for r in range(n)
    ]


def _off_diagonal_orbits(n: int) -> list[tuple[Cell, Cell]]:
    orbits: list[tuple[Cell, Cell]] = []
    for r in range(n):
        for c in range(n):
            cell = (r, c)
            mate = _anti(cell, n)
            if cell < mate:
                orbits.append((cell, mate))
    return orbits


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, shortcut-resistant input grid."""
    _validate_difficulty(difficulty)
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    n = ctx.draw_int("grid_size", 6, 8)
    diagonal_marks = ctx.draw_int("diagonal_marks", 1, 2)
    mirror_pairs = ctx.draw_int("mirror_pairs", 1, 2)
    singletons = ctx.draw_int("singletons", 2, 3)
    colors = list(ctx.draw_distinct_colors("palette", n=4, exclude=(0,)))
    band = difficulty or "unbanded"
    rng = ctx.draw_rng(f"layout:{band}")

    diagonal = [(r, n - 1 - r) for r in range(n)]
    rng.shuffle(diagonal)
    chosen_diagonal = diagonal[:diagonal_marks]

    orbits = _off_diagonal_orbits(n)
    rng.shuffle(orbits)
    chosen_pairs = orbits[:mirror_pairs]
    singleton_orbits = orbits[mirror_pairs : mirror_pairs + singletons]
    chosen_singletons = [
        orbit[rng.randrange(2)] for orbit in singleton_orbits
    ]

    # c3 is deliberately unique and placed on a singleton. c0 is deliberately
    # repeated on an occupied pair and another singleton. This makes both
    # anti-vs-main-diagonal and color-unique-only shortcuts disagree exactly.
    c0, c1, c2, c3 = colors
    grid = full_grid(n, n, 0)

    first, second = chosen_pairs[0]
    grid[first[0]][first[1]] = c0
    grid[second[0]][second[1]] = c1
    if len(chosen_pairs) == 2:
        first, second = chosen_pairs[1]
        grid[first[0]][first[1]] = c1
        grid[second[0]][second[1]] = c2

    grid[chosen_diagonal[0][0]][chosen_diagonal[0][1]] = c2
    if len(chosen_diagonal) == 2:
        grid[chosen_diagonal[1][0]][chosen_diagonal[1][1]] = c0

    grid[chosen_singletons[0][0]][chosen_singletons[0][1]] = c3
    for cell in chosen_singletons[1:]:
        grid[cell[0]][cell[1]] = c0

    # Internal assertion catches a future layout edit that silently breaks an
    # exact override; it is deterministic and never mutates caller state.
    observed = observe_overrides(grid)
    requested = {
        "grid_size": n,
        "diagonal_marks": diagonal_marks,
        "mirror_pairs": mirror_pairs,
        "singletons": singletons,
    }
    if observed != requested:
        raise AssertionError(f"generator realized {observed}, expected {requested}")
    return grid


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    """Recover every exact semantic axis from the returned grid."""
    n = len(grid)
    diagonal_marks = sum(
        1 for r in range(n) if int(grid[r][n - 1 - r]) != 0
    )
    mirror_pairs = 0
    singletons = 0
    for first, second in _off_diagonal_orbits(n):
        occupied = int(grid[first[0]][first[1]] != 0) + int(
            grid[second[0]][second[1]] != 0
        )
        if occupied == 2:
            mirror_pairs += 1
        elif occupied == 1:
            singletons += 1
    return {
        "grid_size": n,
        "diagonal_marks": diagonal_marks,
        "mirror_pairs": mirror_pairs,
        "singletons": singletons,
    }


# ---------------------------------------------------------------- rivals

def _rival_erase_anti_diagonal(grid: Sequence[Sequence[int]]) -> Grid:
    output = rule_mirror(grid)
    n = len(output)
    for r in range(n):
        output[r][n - 1 - r] = 0
    return output


def _rival_copy_keep_originals(grid: Sequence[Sequence[int]]) -> Grid:
    output = deepcopy([list(row) for row in grid])
    n = len(output)
    for r in range(n):
        for c in range(n):
            value = int(grid[r][c])
            if value:
                tr, tc = _anti((r, c), n)
                if output[tr][tc] == 0:
                    output[tr][tc] = value
    return output


def _rival_keep_occupied_pairs(grid: Sequence[Sequence[int]]) -> Grid:
    """Move singleton orbits, but leave preoccupied target pairs unswapped."""
    n = len(grid)
    output = full_grid(n, n, 0)
    for r in range(n):
        fixed = (r, n - 1 - r)
        output[fixed[0]][fixed[1]] = int(grid[fixed[0]][fixed[1]])
    for first, second in _off_diagonal_orbits(n):
        a = int(grid[first[0]][first[1]])
        b = int(grid[second[0]][second[1]])
        if a and b:
            output[first[0]][first[1]] = a
            output[second[0]][second[1]] = b
        else:
            output[first[0]][first[1]] = b
            output[second[0]][second[1]] = a
    return output


def _rival_reflect_only_unique_colors(grid: Sequence[Sequence[int]]) -> Grid:
    counts = Counter(value for row in grid for value in row if value)
    n = len(grid)
    output = full_grid(n, n, 0)
    for r in range(n):
        for c in range(n):
            value = int(grid[r][c])
            if not value:
                continue
            if counts[value] == 1:
                tr, tc = _anti((r, c), n)
                output[tr][tc] = value
            else:
                output[r][c] = value
    return output


def _rival_main_diagonal(grid: Sequence[Sequence[int]]) -> Grid:
    n = len(grid)
    return [[int(grid[c][r]) for c in range(n)] for r in range(n)]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "erase_anti_diagonal": _rival_erase_anti_diagonal,
    "copy_keep_originals": _rival_copy_keep_originals,
    "keep_occupied_pairs": _rival_keep_occupied_pairs,
    "reflect_only_unique_colors": _rival_reflect_only_unique_colors,
    "main_diagonal_reflection": _rival_main_diagonal,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "keep_occupied_pairs": _rival_keep_occupied_pairs,
    "reflect_only_unique_colors": _rival_reflect_only_unique_colors,
}


def _has_anti_diagonal_mark(grid: Sequence[Sequence[int]]) -> bool:
    n = len(grid)
    return any(int(grid[r][n - 1 - r]) != 0 for r in range(n))


def _has_singleton_orbit(grid: Sequence[Sequence[int]]) -> bool:
    n = len(grid)
    return any(
        bool(grid[first[0]][first[1]]) != bool(grid[second[0]][second[1]])
        for first, second in _off_diagonal_orbits(n)
    )


def _has_different_color_occupied_pair(grid: Sequence[Sequence[int]]) -> bool:
    n = len(grid)
    return any(
        int(grid[first[0]][first[1]]) != 0
        and int(grid[second[0]][second[1]]) != 0
        and int(grid[first[0]][first[1]]) != int(grid[second[0]][second[1]])
        for first, second in _off_diagonal_orbits(n)
    )


def _moves_repeated_color(grid: Sequence[Sequence[int]]) -> bool:
    return (
        _rival_reflect_only_unique_colors(grid) != rule_mirror(grid)
    )


def _distinguishes_main_diagonal(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_main_diagonal(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "anti_diagonal_fixed_point": _has_anti_diagonal_mark,
    "singleton_moves_instead_of_copying": _has_singleton_orbit,
    "occupied_pair_swaps": _has_different_color_occupied_pair,
    "repeated_colors_also_move": _moves_repeated_color,
    "anti_not_main_diagonal": _distinguishes_main_diagonal,
}
WITNESS_RIVALS = {
    "anti_diagonal_fixed_point": ["erase_anti_diagonal"],
    "singleton_moves_instead_of_copying": ["copy_keep_originals"],
    "occupied_pair_swaps": ["keep_occupied_pairs"],
    "repeated_colors_also_move": ["reflect_only_unique_colors"],
    "anti_not_main_diagonal": ["main_diagonal_reflection"],
}


def _validate_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output is not the full anti-diagonal reflection"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every named plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    reasons.extend(
        f"query input: {error}" for error in self_check(query["input"])
    )
    if "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output is not the full anti-diagonal reflection")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"named competitor {name!r} fits every demonstration")
    return reasons
