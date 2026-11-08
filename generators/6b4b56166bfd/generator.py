"""Input sampler for fourfold orbit completion around a color-5 pivot.

The selected Racket rule is the label authority.  A lawful input has one central
color-5 pivot and one to three distinctly colored seed cells from disjoint
90-degree rotation orbits.  The rule copies every seed to the other three cells
of its orbit.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b4b56166bfd"
TASK_ID = GENERATOR_ID
RULE_HASH = "f2aaf100dc45"
VERSION = "2.0.0"
SUMMARY = (
    "A central color-5 pivot and 1-3 distinctly colored seeds define disjoint "
    "fourfold rotation orbits to complete."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid is 5..14 by 5..14 with a zero background",
    "exactly one color-5 pivot lies at (height//2, width//2)",
    "1..3 seed cells use distinct non-{0,5} colors",
    "every seed's full fourfold orbit is in bounds and seed orbits are disjoint",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7/9 anchors plus broad, difficulty-weighted support",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 7/9 anchors plus broad, difficulty-weighted support",
        "valid": "5..14",
    },
    "n_cells": {
        "type": "int",
        "default": "canonical 2/3 anchors plus broad 1..3 support",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES = DEGENERATE_TEXTURES = ()

# (height, width, number of seeds).  These are exactly the canonical input
# profiles once background and pivot colors are included in palette size.
_CANONICAL_PROFILES = ((7, 7, 2), (9, 9, 2), (9, 9, 3))
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    bounds = {"grid_h": (5, 14), "grid_w": (5, 14), "n_cells": (1, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_axis(ctx, name, lo, hi, *, anchor=None, favored=()):
    """Draw over the full public domain while favoring curriculum profiles."""
    options = list(range(lo, hi + 1))
    options.extend(favored)
    if anchor is not None:
        options.extend([anchor] * 64)
    return ctx.draw_choice(name, options)


def _rotation_orbit(pivot, point):
    pr, pc = pivot
    r, c = point
    dr, dc = r - pr, c - pc
    return frozenset(
        (pr + rr, pc + cc)
        for rr, cc in ((dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr))
    )


def _candidate_orbits(height, width, pivot):
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if (row, col) == pivot:
                continue
            orbit = _rotation_orbit(pivot, (row, col))
            if orbit in seen or len(orbit) != 4:
                continue
            if all(0 <= r < height and 0 <= c < width for r, c in orbit):
                seen.add(orbit)
                result.append(tuple(sorted(orbit)))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    mode = ctx.draw_choice(
        "curriculum_mode", ("canonical", "canonical", "canonical", "broad")
    )
    profile = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    anchor_h, anchor_w, anchor_n = profile if mode == "canonical" else (None, None, None)

    if difficulty == "easy":
        favored_h = favored_w = (5, 6, 7, 7, 7, 8)
        favored_n = (1, 1, 2, 2)
    elif difficulty == "hard":
        favored_h = favored_w = (9, 9, 10, 11, 12, 13, 14)
        favored_n = (2, 3, 3, 3)
    else:
        favored_h = favored_w = (7, 7, 9, 9)
        favored_n = (2, 2, 3)

    height = _weighted_axis(
        ctx, "grid_h", 5, 14, anchor=anchor_h, favored=favored_h
    )
    width = _weighted_axis(
        ctx, "grid_w", 5, 14, anchor=anchor_w, favored=favored_w
    )
    n_cells = _weighted_axis(
        ctx, "n_cells", 1, 3, anchor=anchor_n, favored=favored_n
    )

    grid = full_grid(height, width, 0)
    pivot = (height // 2, width // 2)
    grid[pivot[0]][pivot[1]] = 5

    orbits = _candidate_orbits(height, width, pivot)
    if len(orbits) < n_cells:  # Defensive; every declared shape has >= 6.
        raise ValueError(
            f"grid {height}x{width} has only {len(orbits)} disjoint rotation orbits"
        )
    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(orbits)
    colors = ctx.draw_rng("seed_colors").sample(_SEED_COLORS, n_cells)
    for orbit, color in zip(orbits[:n_cells], colors):
        row, col = layout_rng.choice(orbit)
        grid[row][col] = color
    return grid


def _grid_shape_problems(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], None, None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have a nonempty first row"], None, None
    width = len(grid[0])
    problems = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            problems.append(f"row {row_index} has invalid width")
    if problems:
        return problems, len(grid), width
    return problems, len(grid), width


def self_check(grid, *, difficulty=None, meta=None):
    problems, height, width = _grid_shape_problems(grid)
    if problems:
        return problems
    assert height is not None and width is not None

    if not 5 <= height <= 14:
        problems.append(f"height {height} outside 5..14")
    if not 5 <= width <= 14:
        problems.append(f"width {width} outside 5..14")
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                problems.append(
                    f"cell ({row_index},{col_index}) is not an integer ARC color 0..9"
                )
    if problems:
        return problems

    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if len(pivots) != 1:
        problems.append(f"expected exactly one color-5 pivot, got {len(pivots)}")
        return problems

    pivot = pivots[0]
    expected_pivot = (height // 2, width // 2)
    if pivot != expected_pivot:
        problems.append(f"pivot {pivot} must be central at {expected_pivot}")
    if not 1 <= len(seeds) <= 3:
        problems.append(f"expected 1..3 seed cells, got {len(seeds)}")
    if len({value for _, _, value in seeds}) != len(seeds):
        problems.append("seed colors must be distinct")

    orbits = []
    for row, col, _ in seeds:
        orbit = _rotation_orbit(pivot, (row, col))
        if len(orbit) != 4:
            problems.append(f"seed at ({row},{col}) has a degenerate orbit")
        if any(not (0 <= r < height and 0 <= c < width) for r, c in orbit):
            problems.append(f"seed at ({row},{col}) has an out-of-bounds orbit")
        orbits.append(orbit)
    if len(orbits) != len(set(orbits)):
        problems.append("two seed cells share the same fourfold orbit")
    return problems


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe invalid grid: {problems}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": sum(value not in (0, 5) for row in grid for value in row),
    }


def _rotated_point(pivot, row, col, turn):
    pr, pc = pivot
    dr, dc = row - pr, col - pc
    if turn == 0:
        rr, cc = dr, dc
    elif turn == 1:
        rr, cc = dc, -dr
    elif turn == 2:
        rr, cc = -dr, -dc
    else:
        rr, cc = -dc, dr
    return pr + rr, pc + cc


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket rule for tests and rivals."""
    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError("rule_mirror requires exactly one color-5 pivot")
    pivot = pivots[0]
    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    output = [list(row) for row in grid]
    height = len(output)
    width = len(output[0])
    for turn in range(4):
        for row, col, value in cells:
            rr, cc = _rotated_point(pivot, row, col, turn)
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = value
    return output


def _half_turn_only(grid):
    """Plausible rival: copy each seed only to its 180-degree counterpart."""
    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError("half_turn_only requires exactly one color-5 pivot")
    pivot = pivots[0]
    output = [list(row) for row in grid]
    for row, source_row in enumerate(grid):
        for col, value in enumerate(source_row):
            if value in (0, 5):
                continue
            rr, cc = _rotated_point(pivot, row, col, 2)
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                output[rr][cc] = value
    return output


def _quarter_turn_completion(grid):
    return rule_mirror(grid) != _half_turn_only(grid)


SEMANTIC_RIVALS = {"half_turn_only": _half_turn_only}
WITNESS_RIVALS = {"quarter_turn_completion": ["half_turn_only"]}
SEMANTIC_WITNESSES = {"quarter_turn_completion": _quarter_turn_completion}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    if all(
        _half_turn_only(pair["input"]) == pair["output"]
        for pair in demos
    ):
        return ["half-turn-only rival survives every demonstration"]
    return []
