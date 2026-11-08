"""Generator for 0d191ce876ab: retain every four-neighbour same-colour core.

The ordinary sampler constructs one connected keep object with an *exact*
number of surviving cells, including adjacent multi-core examples, plus an
exact number of auxiliary distractor cells.  This directly exercises the
local rule rather than the former one-bounding-box-centre shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "0d191ce876ab"
VERSION = "2.0.0"
RULE_HASH = "ddef27a30643"
SUMMARY = "Keep each nonzero cell whose four cardinal neighbours share its colour."
INVARIANTS = [
    "background is 0",
    "ordinary draws contain one exact multi-core keep object",
    "auxiliary distractor cells have a colour distinct from the keep object",
]
AXES = {
    "grid_h": {"type": "int", "default": "difficulty band within 5..18", "valid": "5..18"},
    "grid_w": {"type": "int", "default": "difficulty band within 5..20", "valid": "5..20"},
    "n_keep": {"type": "int", "default": "difficulty band within 1..6", "valid": "1..6"},
    "n_drop": {"type": "int", "default": "difficulty band within 0..3", "valid": "0..3"},
}
HELPFUL_TEXTURES = DEGENERATE_TEXTURES = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# Every footprint fits a 5x5 canvas and has exactly k surviving cells.
# k=5 is a 4x5 solid with one non-corner boundary cell removed, deleting
# exactly one of the six cores of the full 4x5 rectangle.
_KEEP_FOOTPRINTS = {
    1: {(r, c) for r in range(3) for c in range(3)},
    2: {(r, c) for r in range(3) for c in range(4)},
    3: {(r, c) for r in range(3) for c in range(5)},
    4: {(r, c) for r in range(4) for c in range(4)},
    5: {(r, c) for r in range(4) for c in range(5)} - {(0, 1)},
    6: {(r, c) for r in range(4) for c in range(5)},
}


def _rotate(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    height = max(r for r, _ in cells) + 1
    return {(c, height - 1 - r) for r, c in cells}


def _oriented(cells: set[tuple[int, int]], turns: int, mirror: bool) -> set[tuple[int, int]]:
    out = set(cells)
    for _ in range(turns % 4):
        out = _rotate(out)
    if mirror:
        width = max(c for _, c in out) + 1
        out = {(r, width - 1 - c) for r, c in out}
    min_r = min(r for r, _ in out)
    min_c = min(c for _, c in out)
    return {(r - min_r, c - min_c) for r, c in out}


def _survivor_cells(grid):
    h, w = len(grid), len(grid[0])
    out = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if (value != 0 and grid[r - 1][c] == value and grid[r + 1][c] == value
                    and grid[r][c - 1] == value and grid[r][c + 1] == value):
                out.append((r, c, value))
    return out


def rule_mirror(grid):
    """Pure-Python authority mirror used by checks and downstream tooling."""
    h, w = len(grid), len(grid[0])
    survivors = {(r, c): value for r, c, value in _survivor_cells(grid)}
    return [[survivors.get((r, c), 0) for c in range(w)] for r in range(h)]


def observe_overrides(grid):
    survivors = _survivor_cells(grid)
    survivor_colours = {value for _, _, value in survivors}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_keep": len(survivors),
        "n_drop": sum(value != 0 and value not in survivor_colours for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a non-empty literal ARC grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        return ["grid must be rectangular with exact integer colours 0..9"]
    if len(grid) > 30 or width > 30:
        return ["grid exceeds ARC bounds"]
    errors = []
    survivors = _survivor_cells(grid)
    if not survivors:
        errors.append("ordinary inputs need at least one four-neighbour core")
    if any(r in (0, len(grid) - 1) or c in (0, width - 1) for r, c, _ in survivors):
        errors.append("surviving cores must be interior")
    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero <= len(survivors):
        errors.append("ordinary inputs need coloured context that is removed")
    observed = observe_overrides(grid)
    for key, expected in (meta or {}).get("overrides", {}).items():
        if key in observed and (type(expected) is not int or observed[key] != expected):
            errors.append(f"override {key} does not match observed value")
    return errors


def _draw_axis(ctx, overrides, label, ordinary_bounds, full_bounds):
    bounds = full_bounds if label in overrides else ordinary_bounds
    return ctx.draw_int_strict(label, *bounds)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    bands = {
        None: ((7, 13), (8, 15), (2, 5), (1, 3)),
        "easy": ((5, 9), (5, 10), (1, 3), (0, 1)),
        "medium": ((8, 14), (9, 16), (2, 5), (1, 2)),
        "hard": ((12, 18), (13, 20), (4, 6), (2, 3)),
    }
    h_band, w_band, keep_band, drop_band = bands[difficulty]
    height = _draw_axis(ctx, overrides, "grid_h", h_band, (5, 18))
    width = _draw_axis(ctx, overrides, "grid_w", w_band, (5, 20))
    n_keep = _draw_axis(ctx, overrides, "n_keep", keep_band, (1, 6))
    n_drop = _draw_axis(ctx, overrides, "n_drop", drop_band, (0, 3))

    layout_rng = ctx.draw_rng("layout")
    colour_rng = ctx.draw_rng("colours")
    footprint = _oriented(_KEEP_FOOTPRINTS[n_keep], layout_rng.randrange(4), bool(layout_rng.randrange(2)))
    fh = max(r for r, _ in footprint) + 1
    fw = max(c for _, c in footprint) + 1
    if fh > height or fw > width:
        # A second orientation always fits every declared 5x5-or-larger grid.
        footprint = _oriented(_KEEP_FOOTPRINTS[n_keep], 0, False)
        fh = max(r for r, _ in footprint) + 1
        fw = max(c for _, c in footprint) + 1
    if fh > height or fw > width:
        raise AssertionError("declared keep footprint does not fit declared grid domain")

    r0 = layout_rng.randrange(height - fh + 1)
    c0 = layout_rng.randrange(width - fw + 1)
    keep_colour = colour_rng.choice(range(1, 10))
    drop_colour = colour_rng.choice([value for value in range(1, 10) if value != keep_colour])
    grid = full_grid(height, width, 0)
    for r, c in footprint:
        grid[r0 + r][c0 + c] = keep_colour

    empty = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0]
    layout_rng.shuffle(empty)
    if len(empty) < n_drop:
        raise AssertionError("declared distractor count does not fit declared grid domain")
    for r, c in empty[:n_drop]:
        grid[r][c] = drop_colour

    measured = observe_overrides(grid)
    if measured["n_keep"] != n_keep or measured["n_drop"] != n_drop:
        raise AssertionError(f"constructive axis mismatch: expected {(n_keep, n_drop)}, got {measured}")
    return grid
