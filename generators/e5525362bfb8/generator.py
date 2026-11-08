"""Constructive inputs for the unchanged all-pairs green-plus bridge rule.

Every green cell belongs to a complete cardinal plus. Canonical-size two/three
plus scenes alternate with five-plus witnesses: a plus on one diagonal has
arms on the other diagonal, which the zero-only Racket rule preserves.
The generator creates inputs only; rival functions below are not label authority.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e5525362bfb8"
TASK_ID = GENERATOR_ID
RULE_HASH = "7aef5b5cd6e6"
VERSION = "4.1.0"
SUMMARY = (
    "On a black grid, identify complete color-3 cardinal plus centers. Connect "
    "every diagonal-aligned pair, painting only intervening zero cells red (2). "
    "Inputs include two-plus pairs, three-plus collinear/bent/skipped-pair "
    "scenes, and five-plus crossing networks with green arms on both bridges. "
    "A three-demonstration curriculum retains a compound witness under each "
    "single-query rotation. The canonical Racket authority is unchanged."
)
INVARIANTS = [
    "rectangular integer grids, 8..24 rows and columns, with fixed input colors 0 and 3",
    "two through five complete plus centers; every green cell belongs to a plus footprint",
    "at least one diagonal-aligned pair at distance greater than one has a zero bridge cell",
    "all diagonal-aligned pairs matter; nonaligned pairs do not connect",
    "only zero cells become red; existing green centers and arms are preserved",
]
SCENES = ("pair", "chain", "bend", "skipped", "network")
AXES = {
    "grid_h": {"type": "int", "default": "8/11 in core slots; band-weighted 8..24 otherwise",
               "valid": "8..24"},
    "grid_w": {"type": "int", "default": "8/11 in core slots; band-weighted 8..24 otherwise",
               "valid": "8..24"},
    "scene": {"type": "str", "default": "12-slot teaching schedule",
              "valid": "pair|chain|bend|skipped|network"},
}
# Every Cartesian combination of these three exact controls fits, even 8 x 8.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 12
_SCHEDULE = ("pair", "network", "network", "chain", "network", "network",
             "bend", "network", "network", "skipped", "network", "network")
_ARMS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def _paint_plus(grid, r, c):
    for dr, dc in _ARMS:
        grid[r + dr][c + dc] = 3


def _plus_centers(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    return [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
            if all(grid[r + dr][c + dc] == 3 for dr, dc in _ARMS)]


def _diagonal_pairs(centers):
    return [(a, b) for a, b in combinations(centers, 2)
            if abs(a[0] - b[0]) == abs(a[1] - b[1]) > 1]


def _interior(a, b):
    dr, dc = b[0] - a[0], b[1] - a[1]
    sr, sc = (1 if dr > 0 else -1), (1 if dc > 0 else -1)
    return [(a[0] + k * sr, a[1] + k * sc) for k in range(1, abs(dr))]


def _dimension(ctx, name, preferred):
    # Default profile choices and override bounds are separate: a core 8x8
    # default must not reject a lawful exact 24-row override in an easy band.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 8, 24)
    return ctx.draw_choice(name, (preferred,))


def _scene_points(scene, distance):
    d = distance
    if scene == "pair":
        return [(0, 0), (d, d)]
    if scene == "chain":
        return [(0, 0), (d, d), (2*d, 2*d)]
    if scene == "bend":
        return [(0, 0), (d, d), (2*d, 0)]
    if scene == "skipped":
        return [(0, 0), (d, 2*d + 1), (2*d, 2*d)]
    # Odd side length places the fifth center on one diagonal, with its arms
    # on the other. Four aligned pairs are needed, so truncating pair iteration
    # to its first two entries no longer happens to paint the entire output.
    side = 2*d + 1
    return [(0, 0), (0, side), (side, 0), (side, side), (d, d)]


def _orient(points, symmetry):
    result = []
    for r, c in points:
        if symmetry >= 4:
            c = -c
        for _ in range(symmetry % 4):
            r, c = c, -r
        result.append((r, c))
    rmin = min(r for r, _ in result)
    cmin = min(c for _, c in result)
    return [(r - rmin, c - cmin) for r, c in result]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not 8 <= value <= 24):
            raise ValueError(f"{name} must be an integer in 8..24 (not bool)")
    scene_override = overrides.get("scene")
    if scene_override is not None and scene_override not in SCENES:
        raise ValueError(f"scene must be one of {SCENES}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    default_scene = _SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]
    options = SCENES if scene_override is not None else (default_scene,)
    scene = ctx.draw_choice("scene", options)
    core = sample_index % 3 == 0
    if core:
        preferred_h = preferred_w = 8 if scene == "pair" else 11
    else:
        lo, hi = {"easy": (8, 12), "medium": (10, 18),
                  "hard": (14, 24)}.get(difficulty, (10, 18))
        preferred_h = ctx.draw_rng("canvas_height").randint(lo, hi)
        preferred_w = ctx.draw_rng("canvas_width").randint(lo, hi)
    h = _dimension(ctx, "grid_h", preferred_h)
    w = _dimension(ctx, "grid_w", preferred_w)
    extent = min(h, w) - 3
    max_distance = extent if scene == "pair" else (extent - (scene in ("skipped", "network"))) // 2
    distances = list(range(2, max_distance + 1))
    # Delta 3 remains well represented without excluding any feasible distance.
    if core and 3 in distances:
        distances += [3] * 4
    distance = ctx.draw_choice("separation", distances)
    points = _orient(_scene_points(scene, distance), ctx.draw_int("symmetry", 0, 7))
    rspan, cspan = max(r for r, _ in points), max(c for _, c in points)
    rng = ctx.draw_rng("translation")
    top = rng.randint(1, h - rspan - 2)
    left = rng.randint(1, w - cspan - 2)
    grid = full_grid(h, w, 0)
    for r, c in points:
        _paint_plus(grid, top + r, left + c)
    return grid


def observe_overrides(grid):
    """Recover exact controls from returned pixels rather than recorded draws."""
    centers = _plus_centers(grid)
    count, edges = len(centers), len(_diagonal_pairs(centers))
    scene = {(2, 1): "pair", (3, 3): "chain", (3, 2): "bend",
             (3, 1): "skipped", (5, 4): "network"}.get((count, edges))
    if scene is None:
        raise ValueError("input is not one of the five generated scene classes")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "scene": scene}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the bounded plus-only input domain, including all canonicals."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 3) for row in grid for value in row):
        return ["input cells must be integer colors 0 or 3 (not bool or float)"]
    if not (8 <= h <= 24 and 8 <= w <= 24):
        return ["input dimensions must be 8..24"]
    centers = _plus_centers(grid)
    if not 2 <= len(centers) <= 5:
        return [f"expected two through five complete plus centers, got {len(centers)}"]
    green = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    covered = {(r + dr, c + dc) for r, c in centers for dr, dc in _ARMS}
    if green != covered:
        return ["orphan green cells: every green cell must belong to a complete plus"]
    pairs = _diagonal_pairs(centers)
    if not pairs:
        return ["expected a non-adjacent diagonal-aligned pair"]
    if not any(grid[r][c] == 0 for a, b in pairs for r, c in _interior(a, b)):
        return ["expected at least one zero bridge cell"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _rival_output(grid, mode):
    """Deliberately incomplete alternatives, never used to create labels."""
    centers = _plus_centers(grid)
    if mode == "first_two_only":
        pairs = _diagonal_pairs(centers[:2])
    elif mode == "first_three_only":
        pairs = _diagonal_pairs(centers[:3])
    elif mode == "row_major_consecutive":
        pairs = [(a, b) for a, b in zip(centers, centers[1:])
                 if abs(a[0] - b[0]) == abs(a[1] - b[1]) > 1]
    else:
        pairs = _diagonal_pairs(centers)
    if mode == "first_two_aligned_pairs":
        pairs = pairs[:2]
    out = [list(row) for row in grid]
    for a, b in pairs:
        if mode == "gap_three_only" and abs(a[0] - b[0]) != 3:
            continue
        if mode == "positive_slope_only" and (b[0] - a[0]) * (b[1] - a[1]) <= 0:
            continue
        for r, c in _interior(a, b):
            if out[r][c] == 0 or (mode == "overwrite_green_arms" and (r, c) not in centers):
                out[r][c] = 2
    return out


def _first_two_only(grid):
    return _rival_output(grid, "first_two_only")


def _row_major_consecutive(grid):
    return _rival_output(grid, "row_major_consecutive")


def _gap_three_only(grid):
    return _rival_output(grid, "gap_three_only")


def _first_three_only(grid):
    return _rival_output(grid, "first_three_only")


def _first_two_aligned_pairs(grid):
    return _rival_output(grid, "first_two_aligned_pairs")


def _overwrite_green_arms(grid):
    return _rival_output(grid, "overwrite_green_arms")


def _positive_slope_only(grid):
    return _rival_output(grid, "positive_slope_only")


def _compound_network(grid):
    """Recognize the odd square and interior plus, independently of labels."""
    centers = _plus_centers(grid)
    if len(centers) != 5 or len(_diagonal_pairs(centers)) != 4:
        return False
    rmin, rmax = min(r for r, _ in centers), max(r for r, _ in centers)
    cmin, cmax = min(c for _, c in centers), max(c for _, c in centers)
    side = rmax - rmin
    if side != cmax - cmin or side < 5 or side % 2 != 1:
        return False
    corners = {(rmin, cmin), (rmin, cmax), (rmax, cmin), (rmax, cmax)}
    if not corners <= set(centers):
        return False
    middle = (set(centers) - corners).pop()
    return middle in {(rmin + dr, cmin + dc)
                      for dr in (side // 2, side // 2 + 1)
                      for dc in (side // 2, side // 2 + 1)}


SEMANTIC_WITNESSES = {"compound_network": _compound_network}
SEMANTIC_RIVALS = {
    "first_two_only": _first_two_only,
    "row_major_consecutive": _row_major_consecutive,
    "gap_three_only": _gap_three_only,
    "first_three_only": _first_three_only,
    "first_two_aligned_pairs": _first_two_aligned_pairs,
    "overwrite_green_arms": _overwrite_green_arms,
    "positive_slope_only": _positive_slope_only,
}
WITNESS_RIVALS = {"compound_network": list(SEMANTIC_RIVALS)}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("row_major_consecutive", "gap_three_only", "first_three_only",
                 "first_two_aligned_pairs", "overwrite_green_arms")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
