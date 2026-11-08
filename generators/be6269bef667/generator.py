"""Constructive input sampler for directional rays and overlap counts.

Colors 1/2/3/4 are up/right/down/left emitters.  Each ray includes its
emitter cell, traverses other emitters, and stops before a color-5 wall or at
the boundary.  The unchanged canonical Racket rule produces a fresh count map.

The sampler deliberately teaches the canonical demonstrations' strongest
plausible missing branch: every generated input contains a downward emitter
whose ray reaches a wall with cells beyond it.  It also guarantees overlap and
all four direction symbols without replaying a canonical grid.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "be6269bef667"
TASK_ID = GENERATOR_ID
RULE_HASH = "c3e717030acc"
VERSION = "3.0.0"
SUMMARY = (
    "A 7..10 by 8..10 grid contains 7..10 directional emitters "
    "(1=up, 2=right, 3=down, 4=left) and 4..6 color-5 walls. "
    "Rays include their emitter, pass through emitters, stop before walls, "
    "and add in a fresh count map. Constructive layouts include all four "
    "directions, a ray overlap, and a downward wall-stop witness."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "integer colors are exactly from 0..5 on a rectangular 7..10 by 8..10 grid",
    "7..10 emitters include every direction 1,2,3,4 and 4..6 walls use color 5",
    "at least two rays overlap and at least one ray reaches a wall or another emitter",
    "production samples always distinguish downward wall stopping from ignoring walls",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 7..10; canonical heights 7 and 8 favored",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 8..10; canonical widths 8 and 9 favored",
        "valid": "8..10",
    },
    "n_emitters": {
        "type": "int",
        "default": "difficulty-weighted 7..10",
        "valid": "7..10",
    },
    "n_walls": {
        "type": "int",
        "default": "difficulty-weighted 4..6",
        "valid": "4..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_DIRECTIONS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
_AXIS_BOUNDS = {
    "grid_h": (7, 10),
    "grid_w": (8, 10),
    "n_emitters": (7, 10),
    "n_walls": (4, 6),
}


def _weighted_options(name, difficulty):
    if name == "grid_h":
        return [7] * 8 + [8] * 12 + [9] * 2 + [10]
    if name == "grid_w":
        return [8] * 8 + [9] * 12 + [10] * 3
    if name == "n_emitters":
        if difficulty == "easy":
            return [7] * 12 + [8] * 4 + [9, 10]
        if difficulty == "hard":
            return [7] + [8] * 4 + [9] * 12 + [10] * 4
        return [7] * 4 + [8] * 12 + [9] * 4 + [10]
    if name == "n_walls":
        if difficulty == "easy":
            return [4] * 12 + [5] * 4 + [6]
        if difficulty == "hard":
            return [4] * 2 + [5] * 10 + [6] * 6
        return [4] * 6 + [5] * 12 + [6] * 2
    raise KeyError(name)


def _ray_output(grid, *, downward_ignores_walls=False):
    """Pure Python mirror used only for validation and declared rivals."""
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in _DIRECTIONS:
                continue
            dr, dc = _DIRECTIONS[value]
            rr, cc = r, c
            while 0 <= rr < h and 0 <= cc < w:
                if grid[rr][cc] == 5 and not (
                    downward_ignores_walls and value == 3
                ):
                    break
                output[rr][cc] += 1
                rr += dr
                cc += dc
    return output


def _interaction_flags(grid):
    """Return whether any emitter ray reaches a wall and/or another emitter."""
    h, w = len(grid), len(grid[0])
    reaches_wall = False
    passes_emitter = False
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in _DIRECTIONS:
                continue
            dr, dc = _DIRECTIONS[value]
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                cell = grid[rr][cc]
                if cell == 5:
                    reaches_wall = True
                    break
                if cell in _DIRECTIONS:
                    passes_emitter = True
                rr += dr
                cc += dc
    return reaches_wall, passes_emitter


def _has_downward_wall_stop(grid):
    """A color-3 ray reaches a wall and has at least one cell beyond the wall."""
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3:
                continue
            for rr in range(r + 1, h):
                if grid[rr][c] == 5:
                    if rr < h - 1:
                        return True
                    break
    return False


def _downward_ignores_walls(grid):
    """Plausible canonical-fitting rival: direction 3 omits the wall check."""
    return _ray_output(grid, downward_ignores_walls=True)


def _validate_call(seed, sample_index, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice("grid_h", _weighted_options("grid_h", difficulty))
    w = ctx.draw_choice("grid_w", _weighted_options("grid_w", difficulty))
    n_emitters = ctx.draw_choice(
        "n_emitters", _weighted_options("n_emitters", difficulty)
    )
    n_walls = ctx.draw_choice("n_walls", _weighted_options("n_walls", difficulty))

    grid = full_grid(h, w, 0)
    geometry_rng = ctx.draw_rng("teaching_geometry")
    cross_row = geometry_rng.choice(list(range(3, h - 1)))
    witness_col = geometry_rng.choice(list(range(2, w - 2)))
    wall_row = geometry_rng.choice(list(range(1, cross_row)))
    left_col = geometry_rng.choice((0, 1))
    right_col = geometry_rng.choice((w - 2, w - 1))

    # Four semantic anchors.  The horizontal pair sees and crosses one another,
    # while the vertical pair approaches the same protected wall from both sides.
    for r, c, value in (
        (0, witness_col, 3),
        (h - 1, witness_col, 1),
        (cross_row, left_col, 2),
        (cross_row, right_col, 4),
        (wall_row, witness_col, 5),
    ):
        if grid[r][c] != 0:
            raise RuntimeError("constructive teaching anchors collided")
        grid[r][c] = value

    # Preserve the teaching paths: extra walls never cut the crossing row or
    # witness column.  Exact counts are constructive for the entire axis domain.
    wall_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and r != cross_row and c != witness_col
    ]
    extra_walls = ctx.draw_rng("extra_walls").sample(wall_candidates, n_walls - 1)
    for r, c in extra_walls:
        grid[r][c] = 5

    emitter_candidates = [
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 0
    ]
    extra_positions = ctx.draw_rng("extra_emitters").sample(
        emitter_candidates, n_emitters - 4
    )
    direction_rng = ctx.draw_rng("extra_directions")
    for r, c in extra_positions:
        grid[r][c] = direction_rng.randint(1, 4)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler produced invalid grid: {errors}")
    if not _has_downward_wall_stop(grid):
        raise RuntimeError("constructive sampler lost its downward-wall witness")
    return grid


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    counts = Counter(value for row in grid for value in row)
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_emitters": sum(counts[value] for value in _DIRECTIONS),
        "n_walls": counts[5],
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    h = len(grid)
    if not 7 <= h <= 10:
        errors.append(f"grid_h={h} outside [7,10]")
    if not 8 <= width <= 10:
        errors.append(f"grid_w={width} outside [8,10]")
    if any(type(value) is not int or not 0 <= value <= 5 for row in grid for value in row):
        errors.append("cells must be integer colors from 0..5")
        return errors

    counts = Counter(value for row in grid for value in row)
    n_emitters = sum(counts[value] for value in _DIRECTIONS)
    n_walls = counts[5]
    if not 7 <= n_emitters <= 10:
        errors.append(f"n_emitters={n_emitters} outside [7,10]")
    if not 4 <= n_walls <= 6:
        errors.append(f"n_walls={n_walls} outside [4,6]")
    missing = sorted(set(_DIRECTIONS) - {value for value in _DIRECTIONS if counts[value]})
    if missing:
        errors.append(f"missing emitter directions: {missing}")

    if not errors:
        output = _ray_output(grid)
        if max(max(row) for row in output) < 2:
            errors.append("no ray overlap (maximum output count is below 2)")
        reaches_wall, passes_emitter = _interaction_flags(grid)
        if not (reaches_wall or passes_emitter):
            errors.append("no ray reaches a wall or passes through another emitter")
    return errors


def strict_canonical_like(grid):
    """Lawful canonical/sampler manifold, not merely a palette or shape check."""
    return self_check(grid)


SEMANTIC_WITNESSES = {"downward_wall_stop": _has_downward_wall_stop}
SEMANTIC_RIVALS = {"downward_ignores_walls": _downward_ignores_walls}
WITNESS_RIVALS = {"downward_wall_stop": ["downward_ignores_walls"]}
CANONICAL_SHORTCUTS = {"downward_ignores_walls": _downward_ignores_walls}
LESSON_COMPETITORS = {"downward_ignores_walls": _downward_ignores_walls}
