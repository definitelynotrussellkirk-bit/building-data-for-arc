"""Generator for task 7d970a1ea99b: reflect across the main diagonal.

The selected Racket authority is ``(overlay g (transpose g))``.  Lawful source
inputs place at most one nonzero cell in each unordered off-diagonal transpose
pair, so reflecting never overwrites a differently colored original.  Ordinary
sampling includes both upper- and lower-triangle sources, diagonal cells,
boundary contacts, and three independently colored source roles.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7d970a1ea99b"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "2b970065d6a3"
EXAMPLES_NEEDED = 2
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Square grid with three source colors; copy every nonzero cell to its "
    "transposed coordinate while preserving every original source cell."
)

INVARIANTS = [
    "background is 0 and the grid is square",
    "exactly three nonzero colors are present",
    "3..12 off-diagonal source cells occupy distinct unordered transpose pairs",
    "0..3 diagonal cells are preserved in place",
    "at least one one-sided off-diagonal source makes the transformation non-identity",
]

AXES = {
    "side": {
        "type": "int",
        "default": "difficulty/profile schedule",
        "valid": "6..16",
        "doc": "Square side length.",
    },
    "n_off_diagonal": {
        "type": "int",
        "default": "difficulty/profile schedule",
        "valid": "3..12",
        "doc": "Number of one-sided off-diagonal source cells.",
    },
    "n_diagonal": {
        "type": "int",
        "default": "profile schedule",
        "valid": "0..3",
        "doc": "Number of nonzero cells already on the main diagonal.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}")


def _validate_call_identity(seed: object, sample_index: object) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an exact integer; got {seed!r}")
    if type(sample_index) is not int:
        raise TypeError(f"sample_index must be an exact integer; got {sample_index!r}")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative; got {sample_index}")


def _draw_int(ctx, label: str, global_lo: int, global_hi: int,
              default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _defaults(profile: int, difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], int]:
    if difficulty == "easy":
        side = (6, 8)
        off = (3, 5)
    elif difficulty == "medium":
        side = (8, 12)
        off = (5, 8)
    elif difficulty == "hard":
        side = (12, 16)
        off = (8, 12)
    elif difficulty is None:
        side = (6, 16)
        off = (3, 10)
    else:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    diagonal = (0, 1, 2, 1)[profile]
    return side, off, diagonal


def _grid_errors(grid: object) -> list[str]:
    if type(grid) is not list or not grid:
        return ["grid must be a non-empty list"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) != width:
        return [f"expected square grid; got {len(grid)}x{width}"]
    if not 6 <= len(grid) <= 16:
        return [f"side must lie in 6..16; got {len(grid)}"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an exact ARC integer 0..9; got {value!r}")
    return errors


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    n = len(grid)
    return {
        "side": n,
        "n_off_diagonal": sum(grid[r][c] != 0 for r in range(n) for c in range(n) if r != c),
        "n_diagonal": sum(grid[i][i] != 0 for i in range(n)),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the selected Racket authority (transpose overlays g)."""
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(n):
            value = grid[r][c]
            if value:
                output[c][r] = value
    return output


def _upper_triangle_only(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(r + 1, n):
            if grid[r][c]:
                output[c][r] = grid[r][c]
    return output


def _lower_triangle_only(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(1, n):
        for c in range(r):
            if grid[r][c]:
                output[c][r] = grid[r][c]
    return output


def _anti_diagonal(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(n):
            if grid[r][c]:
                output[n - 1 - c][n - 1 - r] = grid[r][c]
    return output


def _one_color_only(grid: list[list[int]]) -> list[list[int]]:
    colors = sorted({value for row in grid for value in row if value})
    if not colors:
        return [row[:] for row in grid]
    selected = colors[0]
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(n):
            if grid[r][c] == selected:
                output[c][r] = selected
    return output


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "upper_triangle_only": _upper_triangle_only,
    "lower_triangle_only": _lower_triangle_only,
    "anti_diagonal": _anti_diagonal,
    "one_color_only": _one_color_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"upper_triangle_only": _upper_triangle_only}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the source grammar, including collision-free keep-original semantics."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    errors = _grid_errors(grid)
    if errors:
        return errors
    n = len(grid)
    colors = {value for row in grid for value in row if value}
    if len(colors) != 3:
        errors.append(f"expected exactly three nonzero colors; found {len(colors)}")
    off = [(r, c) for r in range(n) for c in range(n) if r != c and grid[r][c] != 0]
    diagonal = [(i, i) for i in range(n) if grid[i][i] != 0]
    if not 3 <= len(off) <= 12:
        errors.append(f"expected 3..12 off-diagonal source cells; found {len(off)}")
    if not 0 <= len(diagonal) <= 3:
        errors.append(f"expected 0..3 diagonal source cells; found {len(diagonal)}")
    collisions = [
        (r, c, grid[r][c], grid[c][r])
        for r in range(n)
        for c in range(r + 1, n)
        if grid[r][c] != 0 and grid[c][r] != 0
    ]
    if collisions:
        errors.append(
            "each transpose pair must contain at most one source cell; "
            f"conflicting/occupied transpose pair examples: {collisions[:3]}"
        )
    if not any(grid[r][c] != 0 and grid[c][r] == 0
               for r in range(n) for c in range(n) if r != c):
        errors.append("expected a one-sided off-diagonal source so reflection changes the grid")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _has_lower_source(grid: list[list[int]]) -> bool:
    n = len(grid)
    return any(grid[r][c] for r in range(1, n) for c in range(r))


def _has_upper_source(grid: list[list[int]]) -> bool:
    n = len(grid)
    return any(grid[r][c] for r in range(n) for c in range(r + 1, n))


def _multiple_colors_need_reflection(grid: list[list[int]]) -> bool:
    n = len(grid)
    colors = {
        grid[r][c]
        for r in range(n)
        for c in range(n)
        if r != c and grid[r][c] and grid[c][r] == 0
    }
    return len(colors) >= 2 and _one_color_only(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "lower_triangle_source": lambda grid: _has_lower_source(grid) and _upper_triangle_only(grid) != rule_mirror(grid),
    "upper_triangle_source": lambda grid: _has_upper_source(grid) and _lower_triangle_only(grid) != rule_mirror(grid),
    "multiple_colors_need_reflection": _multiple_colors_need_reflection,
}
WITNESS_RIVALS = {
    "lower_triangle_source": ["upper_triangle_only"],
    "upper_triangle_source": ["lower_triangle_only"],
    "multiple_colors_need_reflection": ["one_color_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} is not lawful: {structural[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with main-diagonal reflection")
    if not isinstance(query, dict) or not {"input", "output"} <= set(query):
        reasons.append("query must contain input and output")
    else:
        structural = self_check(query["input"])
        if structural:
            reasons.append(f"query is not lawful: {structural[0]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with main-diagonal reflection")
    if reasons:
        return reasons
    demo_inputs = [pair["input"] for pair in demos]
    if not any(_has_upper_source(grid) for grid in demo_inputs):
        reasons.append("demonstrations contain no upper-triangle source")
    if not any(_has_lower_source(grid) for grid in demo_inputs):
        reasons.append("demonstrations contain no lower-triangle source")
    if not any(_multiple_colors_need_reflection(grid) for grid in demo_inputs):
        reasons.append("demonstrations do not require reflecting multiple colors")
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                if rival(query["input"]) != query["output"]:
                    reasons.append(f"competitor {name!r} fits every demo but changes the query")
                else:
                    reasons.append(f"competitor {name!r} survives the whole materialized lesson")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons


def _candidate_grid(ctx, n: int, n_off: int, n_diag: int,
                    colors: tuple[int, ...], profile: int, attempt: int) -> list[list[int]]:
    rng = ctx.draw_rng(f"placement:{profile}:{attempt}")
    pairs = [(r, c) for r in range(n) for c in range(r + 1, n)]
    rng.shuffle(pairs)
    selected: list[tuple[int, int]] = []
    if profile in (0, 3):
        boundary = [p for p in pairs if 0 in p or n - 1 in p]
        first = rng.choice(boundary)
        selected.append(first)
        pairs.remove(first)
    selected.extend(pairs[: n_off - len(selected)])

    palette = list(colors)
    rng.shuffle(palette)
    grid = full_grid(n, n, 0)
    for index, (r, c) in enumerate(selected):
        # Force both triangle directions, then vary them independently.
        if index == 0:
            rr, cc = r, c
        elif index == 1:
            rr, cc = c, r
        elif rng.randrange(2):
            rr, cc = r, c
        else:
            rr, cc = c, r
        grid[rr][cc] = palette[index % len(palette)]

    diagonal_indices = list(range(n))
    rng.shuffle(diagonal_indices)
    for index, position in enumerate(diagonal_indices[:n_diag]):
        grid[position][position] = palette[(index + 1) % len(palette)]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_identity(seed, sample_index)
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    side_band, off_band, scheduled_diagonal = _defaults(profile, difficulty)
    n = _draw_int(ctx, "side", 6, 16, *side_band)
    n_off = _draw_int(ctx, "n_off_diagonal", 3, 12, *off_band)
    if "n_diagonal" in overrides and overrides["n_diagonal"] is not None:
        n_diag = ctx.draw_int_strict("n_diagonal", 0, 3)
    else:
        n_diag = int(ctx.draw_choice("n_diagonal", (scheduled_diagonal,)))
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})

    for attempt in range(64):
        grid = _candidate_grid(ctx, n, n_off, n_diag, colors, profile, attempt)
        if self_check(grid, difficulty=difficulty):
            continue
        target = rule_mirror(grid)
        if all(rival(grid) != target for rival in LESSON_COMPETITORS.values()):
            return grid
    raise RuntimeError("failed to construct a decisive collision-free reflection scene")
