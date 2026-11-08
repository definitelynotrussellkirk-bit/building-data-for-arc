"""Input sampler for diagonal gap filling; unchanged Racket remains label authority.

Three consecutive draws rotate through sparse pairs, a counterexample-rich
scene, and cluttered scenes. The middle profile separates the named rivals.
Random palette permutations, D4 transforms, offsets, and accepted pixel moves
vary the scaffold; this is a finite-rival curriculum, not universal induction.
"""
from __future__ import annotations

from functools import partial
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7e325967ea1"
TASK_ID = GENERATOR_ID
RULE_HASH = "003fd587a0a4"
VERSION = "3.0.0"
SUMMARY = (
    "Fill a blank midpoint only between equal nonzero endpoints exactly two "
    "diagonal steps apart, reading the original grid once. Mix sparse pairs, "
    "counterexamples to overgeneralization, and clutter on 7..18 canvases with "
    "3..9 foreground colors; preserve a canonical 8x8/three-color component."
)
INVARIANTS = [
    "rectangular ARC grid with background 0 and integer colors 0..9",
    "at least one blank midpoint has equal nonzero diagonal neighbors",
    "no blank midpoint is demanded by two different endpoint colors",
    "ordinary draws have 7..18 rows/columns and exactly 3..9 foreground colors",
    "every three consecutive unfiltered draws include a named-rival counterexample",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..18, canonical component favors 8", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "7..18, canonical component favors 8", "valid": "7..18"},
    "n_distinct_colors": {"type": "int", "default": "3..9, canonical component favors 3", "valid": "3..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("sparse", "counterexample", "clutter")


def schedule_profile(seed, sample_index, difficulty=None):
    """A deterministic curriculum label, not an observable/exact override axis."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _targets(grid):
    """Analyze eligible INPUT midpoints; conflicting colors are rejected."""
    targets = {}
    h, w = len(grid), len(grid[0])
    for r in range(1, h-1):
        for c in range(1, w-1):
            if grid[r][c] != 0:
                continue
            colors = set()
            for dc in (-1, 1):
                a, b = grid[r-1][c-dc], grid[r+1][c+dc]
                if a and a == b:
                    colors.add(a)
            if colors:
                targets[r, c] = colors
    return targets


def _snapshot(grid):
    """Diagnostic rival comparator, NOT the exported label authority."""
    out = [row[:] for row in grid]
    for (r, c), colors in _targets(grid).items():
        if len(colors) != 1:
            raise ValueError("conflicting midpoint colors")
        out[r][c] = next(iter(colors))
    return out


def _local_rival(grid, *, axis=False, color_blind=False, overwrite=False):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    if axis:
        directions += ((1, 0), (-1, 0), (0, 1), (0, -1))
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value:
                continue
            for dr, dc in directions:
                rr, cc = r+2*dr, c+2*dc
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                other = grid[rr][cc]
                if other and (other == value or color_blind):
                    mr, mc = r+dr, c+dc
                    if overwrite or grid[mr][mc] == 0:
                        out[mr][mc] = value
    return out


def _long_diagonal(grid):
    """Wrong: interpolate arbitrarily long same-color diagonal gaps."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value:
                continue
            for dc in (-1, 1):
                for distance in range(2, min(h, w)):
                    rr, cc = r+distance, c+dc*distance
                    if rr >= h or not 0 <= cc < w:
                        break
                    if grid[rr][cc] == value:
                        for step in range(1, distance):
                            mr, mc = r+step, c+dc*step
                            if grid[mr][mc] == 0:
                                out[mr][mc] = value
    return out


def _cascade(grid):
    """Wrong: repeatedly use newly filled cells as endpoints."""
    out = [row[:] for row in grid]
    # Zero-only changes terminate in at most the cell count, even if a later
    # pass develops competing colors. The rival uses explicit scan order.
    for _ in range(len(grid)*len(grid[0])):
        new = _local_rival(out)
        if new == out:
            return out
        out = new
    raise RuntimeError("monotone cascade failed to converge")


def _color_box(grid):
    """Wrong: one bounding-box midpoint per color instead of local pairs."""
    out = [row[:] for row in grid]
    for color in range(1, 10):
        points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(points) < 2:
            continue
        r0, r1 = min(r for r, c in points), max(r for r, c in points)
        c0, c1 = min(c for r, c in points), max(c for r, c in points)
        if r1-r0 == c1-c0 and (r0+r1) % 2 == 0 and (c0+c1) % 2 == 0:
            r, c = (r0+r1)//2, (c0+c1)//2
            if grid[r][c] == 0:
                out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "long_diagonal": _long_diagonal,
    "eight_directions": partial(_local_rival, axis=True),
    "color_blind": partial(_local_rival, color_blind=True),
    "overwrite_middle": partial(_local_rival, overwrite=True),
    "cascade": _cascade,
    "per_color_box": _color_box,
}
# color_blind is already falsified by a canonical example; do NOT call it a
# canonical-fitting shortcut. Keep it as a useful negative-context competitor.
CANONICAL_SHORTCUTS = {name: fn for name, fn in SEMANTIC_RIVALS.items() if name != "color_blind"}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _different(name, grid):
    return SEMANTIC_RIVALS[name](grid) != _snapshot(grid)


SEMANTIC_WITNESSES = {name: partial(_different, name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite named-rival elimination only; makes no universal uniqueness claim."""
    return [f"named rival survives all demonstrations: {name}"
            for name, fn in LESSON_COMPETITORS.items()
            if all(fn(pair["input"]) == pair["output"] for pair in demos)]


def _safe(grid):
    targets = _targets(grid)
    return bool(targets) and all(len(colors) == 1 for colors in targets.values())


def _satisfies(grid, required):
    return _safe(grid) and all(_different(name, grid) for name in required)


def _sparse(h, w, colors, rng):
    grid = full_grid(h, w, 0)
    pairs = [(r, c, r+2, c+dc) for r in range(h-2) for c in range(w)
             for dc in (-2, 2) if 0 <= c+dc < w]
    for color in colors[:3]:
        rng.shuffle(pairs)
        for r, c, rr, cc in pairs:
            mr, mc = (r+rr)//2, (c+cc)//2
            if grid[r][c] or grid[rr][cc] or grid[mr][mc]:
                continue
            grid[r][c] = grid[rr][cc] = color
            if _safe(grid):
                break
            grid[r][c] = grid[rr][cc] = 0
        else:
            raise RuntimeError("could not place three sparse diagonal pairs")
    return grid


def _counterexample(h, w, colors, rng):
    # Interacting local relations: a bent three-endpoint cascade witness,
    # a distance-three pair, an orthogonal pair, a blocked midpoint, mixed
    # endpoints, and a genuine opposite-diagonal positive pair. No labels.
    cells = ((0, 1, 0), (2, 3, 0), (3, 0, 0),
             (0, 6, 1), (3, 3, 1), (0, 4, 1),
             (4, 4, 2), (6, 6, 2), (5, 5, 1),
             (4, 0, 1), (6, 2, 2), (2, 5, 2), (4, 3, 2))
    turns, reflect = rng.randrange(4), rng.randrange(2)
    ro, co = rng.randrange(h-6), rng.randrange(w-6)
    grid = full_grid(h, w, 0)
    for r, c, role in cells:
        if reflect:
            c = 6-c
        for _ in range(turns):
            r, c = c, 6-r
        grid[ro+r][co+c] = colors[role]
    if not _satisfies(grid, SEMANTIC_RIVALS):
        raise RuntimeError("counterexample scaffold lost its semantic witnesses")
    return grid


def _add_palette(grid, colors, required, rng):
    # Additional colors appear as singleton distractors. Exhaustive randomized
    # candidates, not a capped retry that silently changes an exact control.
    for color in colors[3:]:
        candidates = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if not v]
        rng.shuffle(candidates)
        for r, c in candidates:
            grid[r][c] = color
            if _satisfies(grid, required):
                break
            grid[r][c] = 0
        else:
            raise RuntimeError("no lawful location for an exact palette singleton")


def _vary(grid, colors, profile, rng):
    required = SEMANTIC_RIVALS if profile == "counterexample" else ()
    h, w = len(grid), len(grid[0])
    # These are proposal budgets, NOT promised cell counts. Rejected moves do
    # not alter the output or any declared exact axis.
    budget = {"sparse": 0, "counterexample": 12, "clutter": 18}[profile]
    for _ in range(budget):
        rr, cc = rng.randrange(h), rng.randrange(w)
        if grid[rr][cc]:
            continue
        if profile == "counterexample":
            occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
            r, c = rng.choice(occupied)
            value = grid[r][c]
            grid[r][c], grid[rr][cc] = 0, value
            if not _satisfies(grid, required):
                grid[r][c], grid[rr][cc] = value, 0
        else:
            grid[rr][cc] = rng.choice(colors)
            if not _safe(grid):
                grid[rr][cc] = 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice("scale_profile", ("canonical", "canonical", "broad")) == "canonical"
    favored = {None: 11, "easy": 8, "medium": 12, "hard": 16}[difficulty]
    dimensions = list(range(7, 19)) + ([8]*96 if core else [favored]*4)
    h = ctx.draw_choice("grid_h", dimensions)
    w = ctx.draw_choice("grid_w", dimensions)
    count = ctx.draw_choice("n_distinct_colors", list(range(3, 10)) + [3]*(96 if core else 5))
    colors = ctx.draw_rng("palette").sample(list(range(1, 10)), count)
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout")
    grid = (_counterexample(h, w, colors, rng) if profile == "counterexample"
            else _sparse(h, w, colors, rng))
    required = SEMANTIC_RIVALS if profile == "counterexample" else ()
    _add_palette(grid, colors, required, ctx.draw_rng("palette_singletons"))
    _vary(grid, colors, profile, ctx.draw_rng("pixel_proposals"))
    return grid


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_distinct_colors": len({v for row in grid for v in row if v})}


def self_check(grid, *, difficulty=None, meta=None):
    """Task domain, not an assertion that every lawful grid is sampled.

    Small witnesses and canonical inputs are accepted. Different-color claims
    on the same blank midpoint are excluded: the Racket program resolves them
    by traversal order, but the natural task does not specify that tie break.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        return ["grid dimensions must be in 1..30"]
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid values must be integer ARC colors 0..9, not booleans"]
    targets = _targets(grid)
    errors = []
    if not targets:
        errors.append("at least one active blank diagonal midpoint is required")
    if any(len(colors) > 1 for colors in targets.values()):
        errors.append("conflicting endpoint colors demand the same blank midpoint")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)
