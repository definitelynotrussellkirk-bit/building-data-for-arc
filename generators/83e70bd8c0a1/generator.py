"""Generator for task 83e70bd8c0a1: full anti-diagonal reflection.

For an ``n x n`` input, the selected rule moves every cell at ``(r, c)`` to
``(n - 1 - c, n - 1 - r)``.  Anti-diagonal cells are fixed.  Ordinary draws
retain the canonical six-color sparse profile while including fixed points,
singletons, differently colored occupied mirror pairs, and a repeated color.
Those witnesses separate a full-grid move from common copy/overlay, collision,
unique-color-only, and main-diagonal shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "83e70bd8c0a1"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ea62a41435bf"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Reflect the entire square grid across the anti-diagonal. Every cell at "
    "(r,c) moves to (n-1-c,n-1-r), while anti-diagonal cells stay fixed. "
    "Draws use six foreground colors and deliberately include fixed points, "
    "singletons, differently colored occupied mirror pairs, and a repeated "
    "moving color so plausible partial-reflection rules are observable."
)

INVARIANTS = [
    "background is color 0 and exactly six distinct nonzero colors are present",
    "input is a square 5x5, 6x6, or 7x7 ARC grid",
    "the output is a full-grid anti-diagonal reflection, not an overlay",
    "ordinary draws contain fixed points, singleton orbits, and occupied pairs",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware rng 5..7",
        "valid": "5..7",
        "doc": "Square side length, exactly observable as len(grid).",
    },
    "diagonal_marks": {
        "type": "int",
        "default": "difficulty-aware rng 1..3",
        "valid": "1..3",
        "doc": "Occupied anti-diagonal fixed points.",
    },
    "mirror_pairs": {
        "type": "int",
        "default": "difficulty-aware rng 1..2",
        "valid": "1..2",
        "doc": "Off-diagonal anti-mirror orbits with both endpoints occupied.",
    },
    "singletons": {
        "type": "int",
        "default": "difficulty-aware rng 4..5",
        "valid": "4..5",
        "doc": "Off-diagonal anti-mirror orbits with one occupied endpoint.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]


def _anti(cell: Cell, n: int) -> Cell:
    r, c = cell
    return n - 1 - c, n - 1 - r


def _off_diagonal_orbits(n: int) -> list[tuple[Cell, Cell]]:
    orbits: list[tuple[Cell, Cell]] = []
    for r in range(n):
        for c in range(n):
            cell = (r, c)
            mate = _anti(cell, n)
            if cell < mate:
                orbits.append((cell, mate))
    return orbits


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")


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
    if not 5 <= len(grid) <= 7:
        return [f"grid size {len(grid)} is outside 5..7"], None
    return [], len(grid)


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    """Recover every exact semantic axis from a returned input grid."""
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the owned task manifold while accepting every canonical input."""
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
    if not 6 <= len(foreground) <= 12:
        errors.append(
            f"expected 6..12 foreground cells, found {len(foreground)}"
        )
    if len(colors) != 6:
        errors.append(
            f"expected exactly six distinct foreground colors, found {len(colors)}"
        )

    observed = observe_overrides(grid)
    if not 1 <= observed["diagonal_marks"] <= 3:
        errors.append(
            "expected 1..3 occupied anti-diagonal fixed points, found "
            f"{observed['diagonal_marks']}"
        )
    if not 0 <= observed["mirror_pairs"] <= 2:
        errors.append(
            f"expected 0..2 occupied mirror pairs, found {observed['mirror_pairs']}"
        )
    if not 3 <= observed["singletons"] <= 5:
        errors.append(
            f"expected 3..5 singleton mirror orbits, found {observed['singletons']}"
        )

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict) and not errors:
        for name, expected in requested.items():
            if name in AXES and observed.get(name) != expected:
                errors.append(
                    f"override {name}={expected!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict profile is the same task manifold accepted by self_check."""
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Pure-Python diagnostic mirror of the selected canonical Racket rule."""
    n = len(grid)
    return [
        [int(grid[n - 1 - c][n - 1 - r]) for c in range(n)]
        for r in range(n)
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, canonical-profile, shortcut-resistant input."""
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

    n = ctx.draw_int_diff("grid_size", 5, 7)
    diagonal_marks = ctx.draw_int_diff("diagonal_marks", 1, 3)
    mirror_pairs = ctx.draw_int_diff("mirror_pairs", 1, 2)
    singletons = ctx.draw_int_diff("singletons", 4, 5)
    colors = list(ctx.draw_distinct_colors("palette", n=6, exclude=(0,)))
    rng = ctx.draw_rng(f"layout:{difficulty or 'unbanded'}")

    diagonal = [(r, n - 1 - r) for r in range(n)]
    rng.shuffle(diagonal)
    chosen_diagonal = diagonal[:diagonal_marks]

    # Reserve the corner orbit as a singleton.  Main-diagonal reflection keeps
    # (0,0) fixed whereas the selected anti-diagonal rule moves it to the
    # opposite corner, giving every draw an unambiguous axis witness.
    anchor_orbit = ((0, 0), (n - 1, n - 1))
    orbits = [orbit for orbit in _off_diagonal_orbits(n) if orbit != anchor_orbit]
    rng.shuffle(orbits)
    chosen_pairs = orbits[:mirror_pairs]
    other_singleton_orbits = orbits[
        mirror_pairs : mirror_pairs + singletons - 1
    ]
    chosen_singletons = [(0, 0)] + [
        orbit[rng.randrange(2)] for orbit in other_singleton_orbits
    ]

    positions: list[Cell] = []
    for first, second in chosen_pairs:
        positions.extend((first, second))
    positions.extend(chosen_diagonal)
    positions.extend(chosen_singletons)

    # The first six occupied cells receive all six distinct colors; every
    # remaining cell repeats colors[0].  Since every legal axis combination has
    # at least seven occupied cells and the trailing positions are singletons,
    # each draw preserves canonical palette size while moving a repeated color.
    grid = full_grid(n, n, 0)
    for index, (r, c) in enumerate(positions):
        grid[r][c] = colors[index] if index < len(colors) else colors[0]

    observed = observe_overrides(grid)
    requested = {
        "grid_size": n,
        "diagonal_marks": diagonal_marks,
        "mirror_pairs": mirror_pairs,
        "singletons": singletons,
    }
    if observed != requested:
        raise AssertionError(f"generator realized {observed}, expected {requested}")
    findings = self_check(grid, meta={"overrides": requested})
    if findings:
        raise AssertionError(f"generator produced invalid grid: {findings}")
    return grid


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
    """Move singletons but leave preoccupied target pairs unswapped."""
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
    return _rival_reflect_only_unique_colors(grid) != rule_mirror(grid)


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
