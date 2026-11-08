"""Input sampler for Wall-Geodesic Voronoi (canonical cdb267535df8).

Color 5 is impassable; other nonzero cells are seeds. Empty cells inherit
one nearest *color* by cardinal path distance; different-color ties and
unreachable cells stay 0. Racket remains the sole label authority.

The old contact-degree sampler belonged to a different rule. This replacement
uses varied walls and seed positions, and teaches duplicate-color seeds in
at least two of every four consecutive default draws. Python distance routines
below are authoring/rival diagnostics, never returned training labels.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "cdb267535df8"
RULE_HASH = "cb6c4f271562"
VERSION = "2.0.0"
SUMMARY = (
    "Wall-geodesic Voronoi with 4-6 seed cells, 2-4 seed colors, varied barriers, "
    "different-color ties, and repeated-color nearest-seed witnesses. "
    "Two repeat-color profiles in each four-draw cycle support query rotations."
)
INVARIANTS = [
    "0 is empty, 5 is an impassable wall; seed colors are drawn from 1,2,3,4,6,7,8,9",
    "generated grids contain exactly 4-6 seeds of exactly 2-4 colors and visible walls",
    "default draws refute wall-ignoring, eight-neighbor, and lowest-color tie-breaking rivals",
    "repeated-color draws additionally refute tie-by-seed and first-seed-per-color rivals",
    "no canonical grids or labels are replayed; Racket supplies all exported answers",
]
AXES = {
    "grid_h": {"type": "int", "default": "9..13, favors canonical 9..11", "valid": "9..13"},
    "grid_w": {"type": "int", "default": "11..15, favors canonical 11..13", "valid": "11..15"},
    "n_seeds": {"type": "int", "default": "4 or 5..6 according to four-draw profile", "valid": "4..6"},
    "n_seed_colors": {"type": "int", "default": "weighted 2..4, favors 4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("repeated", "four_seeds")
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Every length-four default window has two repeated-color witnesses."""
    return "repeated" if sample_index % 4 < 2 else "four_seeds"


def _seeds(grid):
    return [(r, c, value) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value not in (0, 5)]


@lru_cache(maxsize=128)
def _distance_maps(frozen, diagonal=False, ignore_walls=False):
    """Immutable, bounded diagnostic cache; independent of any random draw."""
    h, w = len(frozen), len(frozen[0])
    steps = _STEPS + ((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonal else _STEPS
    records = []
    for r, c, color in _seeds(frozen):
        distances = [-1] * (h * w)
        distances[r*w+c] = 0
        queue = deque([(r, c)])
        while queue:
            x, y = queue.popleft()
            distance = distances[x*w+y] + 1
            for dr, dc in steps:
                a, b = x + dr, y + dc
                if (0 <= a < h and 0 <= b < w and distances[a*w+b] < 0
                        and (ignore_walls or frozen[a][b] != 5)):
                    distances[a*w+b] = distance
                    queue.append((a, b))
        records.append((color, tuple(distances)))
    return tuple(records)


def _prediction(grid, *, diagonal=False, ignore_walls=False,
                tie_by_seed=False, choose_lowest=False, first_seed_only=False):
    """Python diagnostic prediction. Do not use in place of the Racket runner."""
    frozen = tuple(tuple(row) for row in grid)
    records = _distance_maps(frozen, diagonal, ignore_walls)
    if first_seed_only:
        seen, retained = set(), []
        for color, distances in records:
            if color not in seen:
                retained.append((color, distances))
                seen.add(color)
        records = retained
    out = [list(row) for row in grid]
    w = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            candidates = [(ds[r*w+c], color) for color, ds in records if ds[r*w+c] >= 0]
            if not candidates:
                continue
            best = min(distance for distance, _ in candidates)
            nearest = [color for distance, color in candidates if distance == best]
            colors = set(nearest)
            if choose_lowest or len(nearest if tie_by_seed else colors) == 1:
                out[r][c] = min(colors)
    return out


def _tie_by_seed(grid):
    return _prediction(grid, tie_by_seed=True)


def _first_seed_only(grid):
    return _prediction(grid, first_seed_only=True)


def _ignore_walls(grid):
    return _prediction(grid, ignore_walls=True)


def _eight_neighbors(grid):
    return _prediction(grid, diagonal=True)


def _lowest_tie(grid):
    return _prediction(grid, choose_lowest=True)


def _walls(h, w, rng, style):
    """Four topologies, with randomized gap/position/length rather than templates."""
    grid = full_grid(h, w, 0)
    if style == "scatter":
        for r, c in rng.sample([(r, c) for r in range(h) for c in range(w)],
                               rng.randint(h*w//7, h*w//4)):
            grid[r][c] = 5
    elif style == "cross":
        rr, cc = rng.randrange(2, h-2), rng.randrange(2, w-2)
        for r in range(h): grid[r][cc] = 5
        for c in range(w): grid[rr][c] = 5
        for a, b in ((0, rr), (rr+1, h)):
            grid[rng.randrange(a, b)][cc] = 0
        for a, b in ((0, cc), (cc+1, w)):
            grid[rr][rng.randrange(a, b)] = 0
    elif style == "bars":
        vertical = rng.choice((False, True))
        major, minor = (h, w) if vertical else (w, h)
        for b in rng.sample(range(2, minor-2), 2):
            gap = rng.randrange(1, major-1)
            lo, hi = rng.choice((0, 1)), major-rng.choice((0, 1))
            for a in range(lo, hi):
                if a != gap:
                    r, c = (a, b) if vertical else (b, a)
                    grid[r][c] = 5
    else:  # A closed chamber creates lawful unreachable blank cells.
        rr, cc = rng.randrange(1, h-4), rng.randrange(1, w-4)
        for r in range(rr, rr+4):
            for c in range(cc, cc+4):
                if r in (rr, rr+3) or c in (cc, cc+3): grid[r][c] = 5
        for _ in range(rng.randint(3, 9)):
            grid[rng.randrange(h)][rng.randrange(w)] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a Python integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Entire advertised domains remain drawable in every band. Shared latent
    # size profile keeps canonical-size support without copying any example.
    core = ctx.draw_rng("size_profile").randrange(4) != 0
    anchor = ctx.draw_rng("canonical_dimensions").choice(((9, 11), (10, 12), (11, 13), (9, 13)))
    h = ctx.draw_choice("grid_h", list(range(9, 14)) + [anchor[0]] * (120 if core else 0))
    w = ctx.draw_choice("grid_w", list(range(11, 16)) + [anchor[1]] * (120 if core else 0))
    colors = ctx.draw_choice("n_seed_colors", [2, 3] + [4]*20)
    repeated = schedule_profile(seed, sample_index, difficulty) == "repeated"
    # Defaults follow an explicit schedule; explicit overrides use the whole
    # valid domain in every band/residue. Both paths retain exact provenance.
    options = (4, 5, 6) if overrides.get("n_seeds") is not None else ((5, 6) if repeated else (4,))
    n = ctx.draw_choice("n_seeds", options)
    rng = ctx.draw_rng("geometry")
    styles = ("cross", "bars", "scatter", "chamber")
    # Difficulty shifts topology frequency, not legal domains or palette semantics.
    favored = ("cross", "cross") if difficulty == "easy" else (("bars", "chamber") if difficulty == "hard" else ())
    for attempt in range(512):
        grid = _walls(h, w, rng, rng.choice(styles + favored))
        free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
        palette = rng.sample(_COLORS, colors)
        values = palette + [rng.choice(palette) for _ in range(n-colors)]
        rng.shuffle(values)
        for (r, c), value in zip(rng.sample(free, n), values): grid[r][c] = value
        reference = _prediction(grid)
        rivals = (_ignore_walls, _eight_neighbors, _lowest_tie)
        if any(rival(grid) == reference for rival in rivals):
            continue
        if n > colors and (_tie_by_seed(grid) == reference or _first_seed_only(grid) == reference):
            continue
        return grid
    raise RuntimeError("could not draw a teaching witness in 512 attempts; no silent fallback")


def observe_overrides(grid):
    seeds = _seeds(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_seeds": len(seeds),
            "n_seed_colors": len({color for _, _, color in seeds})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["expected integer ARC colors 0..9"]
    errors = []
    if not (3 <= len(grid) <= 30 and 3 <= len(grid[0]) <= 30): errors.append("dimensions outside 3..30")
    palette = {value for row in grid for value in row}
    if 0 not in palette: errors.append("must contain empty cells to fill")
    if 5 not in palette: errors.append("must contain color-5 walls")
    seeds = _seeds(grid)
    if not 2 <= len(seeds) <= 8: errors.append("expected 2..8 seed cells")
    if len({color for _, _, color in seeds}) < 2: errors.append("expected at least two seed colors")
    return errors


def strict_canonical_like(grid):
    """Rule-domain validation; neither exact canonical shape nor seed uniqueness."""
    return self_check(grid)


def _witness_same_color(grid):
    return _prediction(grid) != _tie_by_seed(grid)


def _witness_extra_seed(grid):
    return _prediction(grid) != _first_seed_only(grid)


def _witness_detour(grid):
    return _prediction(grid) != _ignore_walls(grid)


def _witness_cardinal(grid):
    return _prediction(grid) != _eight_neighbors(grid)


def _witness_tie(grid):
    return _prediction(grid) != _lowest_tie(grid)


SEMANTIC_WITNESSES = {
    "same_color_tie": _witness_same_color, "extra_seed": _witness_extra_seed,
    "wall_detour": _witness_detour, "cardinal_paths": _witness_cardinal,
    "different_color_tie": _witness_tie,
}
SEMANTIC_RIVALS = {
    "tie_by_seed": _tie_by_seed, "first_seed_only": _first_seed_only,
    "ignore_walls": _ignore_walls, "eight_neighbors": _eight_neighbors,
    "lowest_color_tie": _lowest_tie,
}
WITNESS_RIVALS = {
    "same_color_tie": ["tie_by_seed"], "extra_seed": ["first_seed_only"],
    "wall_detour": ["ignore_walls"], "cardinal_paths": ["eight_neighbors"],
    "different_color_tie": ["lowest_color_tie"],
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in ("tie_by_seed", "first_seed_only")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
