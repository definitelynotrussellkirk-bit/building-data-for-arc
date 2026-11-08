"""Irregular gray-wall fields with independently seeded 4-connected regions.

The unchanged Racket authority supplies every exported label. Python region
analysis below validates inputs and evaluates explicitly wrong teaching rivals;
it does not replace the reference runtime. Version 3 removes the old fictional
room lists and silently ignored/clipped controls. See notes.md for migration.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "6c8eefa043e1"
TASK_ID = GENERATOR_ID
RULE_HASH = "1c419bef489c"
VERSION = "3.0.0"
SUMMARY = (
    "Irregular color-5 wall fields contain 2..5 distinct single-cell seeds in "
    "different 4-connected non-wall regions and at least one seedless region. "
    "Flood-fill each seeded region through zero cells; preserve gray walls, "
    "seeds, and unseeded background. Canonical 7x7/9x9 profiles occur in every "
    "band; larger rectangles extend the same connectivity rule."
)
INVARIANTS = [
    "integer colors 0..9; background 0 and walls 5",
    "2..5 distinct single-cell seeds, at most one seed per actual 4-connected region",
    "each seeded region contains background; at least one region is unseeded",
    "every default draw refutes the five declared local teaching rivals",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..20 with canonical 7/9 support", "valid": "7..20"},
    "grid_w": {"type": "int", "default": "7..20 with canonical square support", "valid": "7..20"},
    "palette_size": {"type": "int", "default": "2..5, favor 2/3", "valid": "2..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def _regions(grid):
    """Return deterministic components of non-wall cells; no presumed geometry."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        for r, c in queue:
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        result.append(tuple(sorted(queue)))
    return result


def _seeds(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value not in (0, 5)]


def _expected_region_colors(grid):
    """Cell expectations for the declared one-seed domain, not exported labels."""
    expected = {}
    for region in _regions(grid):
        colors = [grid[r][c] for r, c in region if grid[r][c] not in (0, 5)]
        if len(colors) > 1:
            raise ValueError("competing seeds are outside this sampler's domain")
        color = colors[0] if colors else 0
        for point in region:
            expected[point] = color
    return expected


def _refuted(grid, rival):
    expected = _expected_region_colors(grid)
    predicted = rival(grid)
    return any(predicted[r][c] != expected.get((r, c), 5)
               for r, row in enumerate(grid) for c in range(len(row)))


def _wrong_flood(grid, *, diagonal=False, first_only=False):
    """Deliberately wrong connectivity/seed-count alternatives, never authority."""
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    seeds = _seeds(grid)
    if first_only:
        seeds = seeds[:1]
    directions = _DIAGONAL if diagonal else _CARDINAL
    for r, c, color in seeds:
        out[r][c] = 0
        queue = [(r, c)]
        while queue:
            rr, cc = queue.pop()
            if not (0 <= rr < h and 0 <= cc < w) or out[rr][cc] != 0:
                continue
            out[rr][cc] = color
            queue.extend((rr + dr, cc + dc) for dr, dc in directions)
    return out


def _eight_connected(grid):
    return _wrong_flood(grid, diagonal=True)


def _first_seed_only(grid):
    return _wrong_flood(grid, first_only=True)


def _straight_rays(grid):
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    for r, c, color in _seeds(grid):
        for dr, dc in _CARDINAL:
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                out[rr][cc] = color
                rr, cc = rr + dr, cc + dc
    return out


def _bounding_boxes(grid):
    out = [list(row) for row in grid]
    for region in _regions(grid):
        colors = [grid[r][c] for r, c in region if grid[r][c] not in (0, 5)]
        if not colors:
            continue
        color = colors[0]
        for r in range(min(p[0] for p in region), max(p[0] for p in region) + 1):
            for c in range(min(p[1] for p in region), max(p[1] for p in region) + 1):
                if grid[r][c] == 0:
                    out[r][c] = color
    return out


def _nearest_seed(grid):
    """Wrongly color every zero by Manhattan proximity, ignoring wall paths."""
    out = [list(row) for row in grid]
    seeds = _seeds(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and seeds:
                sr, sc, color = min(seeds, key=lambda s: (abs(r - s[0]) + abs(c - s[1]), s))
                out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "eight_connected": _eight_connected,
    "first_seed_only": _first_seed_only,
    "straight_rays": _straight_rays,
    "bounding_boxes": _bounding_boxes,
    "nearest_seed": _nearest_seed,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of these five alternatives fits every canonical pair. Do not mislabel
# them as canonical-compatible shortcuts; the census measures that independently.
CANONICAL_SHORTCUTS = {}


def _diagonal_witness(grid):
    return _refuted(grid, _eight_connected)


def _multiple_seeds_witness(grid):
    return _refuted(grid, _first_seed_only)


def _turns_witness(grid):
    return _refuted(grid, _straight_rays)


def _nonrectangular_witness(grid):
    return _refuted(grid, _bounding_boxes)


def _unseeded_witness(grid):
    return _refuted(grid, _nearest_seed)


SEMANTIC_WITNESSES = {
    "diagonal_separation": _diagonal_witness,
    "multiple_growing_seeds": _multiple_seeds_witness,
    "turning_paths": _turns_witness,
    "nonrectangular_regions": _nonrectangular_witness,
    "unseeded_background": _unseeded_witness,
}
WITNESS_RIVALS = {
    "diagonal_separation": ["eight_connected"],
    "multiple_growing_seeds": ["first_seed_only"],
    "turning_paths": ["straight_rays"],
    "nonrectangular_regions": ["bounding_boxes"],
    "unseeded_background": ["nearest_seed"],
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice("scale_profile", ("core", "core", "broad")) == "core"
    sizes = list(range(7, 21))
    if core:
        favored = [7] * 20 + [9] * 40
    elif difficulty == "easy":
        favored = list(range(7, 11)) * 3
    elif difficulty == "hard":
        favored = list(range(14, 21)) * 3
    else:
        favored = []
    h = ctx.draw_choice("grid_h", sizes + favored)
    w = ctx.draw_choice("grid_w", sizes + ([h] * 40 if core else favored))
    n = ctx.draw_choice("palette_size", [2, 3, 4, 5] + [2] * 10 + [3] * 15)
    colors = ctx.draw_rng("seed_colors").sample(_COLORS, n)
    rng = ctx.draw_rng(f"wall_field:{difficulty or 'medium'}")
    for attempt in range(2048):
        # All bands retain the same full domain. Difficulty shifts scale, not
        # the legal override bounds or the meaning of connectivity.
        density = rng.uniform(0.36, 0.58)
        grid = [[5 if rng.random() < density else 0 for _ in range(w)] for _ in range(h)]
        regions = _regions(grid)
        seedable = [region for region in regions if len(region) >= 2]
        if len(seedable) < n or len(regions) <= n:
            continue
        selected = rng.sample(seedable, n)
        for color, region in zip(colors, selected):
            r, c = rng.choice(region)
            grid[r][c] = color
        # Every individual board distinguishes these rivals. Hence no fixed
        # residue/canonical-vs-broad schedule is needed for lesson holdouts.
        if all(_refuted(grid, rival) for rival in SEMANTIC_RIVALS.values()):
            return grid
    raise RuntimeError(f"wall-field rejection budget exhausted for {h}x{w}, {n} seeds")


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "palette_size": len({v for row in grid for v in row} - {0, 5})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    seeds = _seeds(grid)
    errors = []
    if not any(5 in row for row in grid):
        errors.append("no color-5 walls")
    if not 2 <= len(seeds) <= 5:
        errors.append("expected 2..5 single-cell seeds")
    if len({s[2] for s in seeds}) != len(seeds):
        errors.append("seed colors must be distinct")
    unseeded = 0
    for region in _regions(grid):
        count = sum(grid[r][c] not in (0, 5) for r, c in region)
        if count > 1:
            errors.append("competing seeds in one 4-connected region")
        if count == 1 and len(region) == 1:
            errors.append("seeded region has no background to fill")
        if count == 0:
            unseeded += 1
    if not unseeded:
        errors.append("expected at least one unseeded region")
    return errors


def strict_canonical_like(grid):
    """Semantic manifold, deliberately not an exact shape/palette classifier."""
    return self_check(grid)


def lesson_identifiable(demos, query):
    """Finite declared-rival check only; never a universal induction claim."""
    return [f"unrefuted rival {name} changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
