"""Generator for arc_puzzle_bank_21_set22_bundle:easy_p07.

Rule: each isolated interior seed blooms into a radius-one plus.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seeds_at_edge, seeds_clumped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c96915f33c65"
VERSION = "1.2.0"
RULE_HASH = "0e146b03426b"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
TASK_ID = "c96915f33c65"
SUMMARY = "Isolated interior seeds bloom into radius-one plus signs."

INVARIANTS = [
    "background is 0",
    "all seeds are interior cells",
    "every seed has four zero orthogonal neighbors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seeds_at_edge", "seeds_clumped")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_interior_seeds",
                       "valid": "spaced_interior_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _plus_footprint(r, c):
    return {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        seed_count = ctx.draw_int("seed_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        seed_count = ctx.draw_int("seed_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        seed_count = ctx.draw_int("seed_count", 2, 4)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()
    positions = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(positions)
    colors = [rng.randint(1, 9) for _ in range(seed_count)]
    if sample_index % 2 == 0 and seed_count >= 2:
        colors[1] = colors[0]  # repeated-color teaching witness, independent of positions
    placed = 0
    for r, c in positions:
        footprint = _plus_footprint(r, c)
        if footprint & occupied:
            continue
        grid[r][c] = colors[placed]
        occupied |= footprint
        placed += 1
        if placed >= seed_count:
            break
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank → no seeds to bloom, rule has no effect
        return g
    if name == "seeds_at_edge":
        # seeds on border → plus arms fall off-grid
        g[0][3] = 4
        g[5][0] = 6
        g[h - 1][7] = 3
        return g
    if name == "seeds_clumped":
        # adjacent seeds → plus arms collide, rule output is ambiguous
        g[2][3] = 4; g[2][4] = 6
        g[5][7] = 3; g[5][8] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Seeds must be interior cells with zero cardinal neighbors."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not seeds:
        msgs.append("no seed cells found")
        return msgs
    for r, c in seeds:
        if not (1 <= r <= h - 2 and 1 <= c <= w - 2):
            msgs.append(f"seed at ({r},{c}) is not interior (border cells can't bloom)")
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                msgs.append(f"seed at ({r},{c}) has non-zero cardinal neighbor at ({nr},{nc})")
                break
    return msgs


def rule_mirror(grid):
    out = [row[:] for row in grid]
    for r in range(1,len(grid)-1):
        for c in range(1,len(grid[0])-1):
            if grid[r][c] and all(grid[rr][cc] == 0 for rr,cc in _plus_footprint(r,c)-{(r,c)}):
                for rr,cc in _plus_footprint(r,c): out[rr][cc]=grid[r][c]
    return out


def _unique_only(grid):
    from collections import Counter
    counts=Counter(v for row in grid for v in row if v)
    out=[row[:] for row in grid]
    full=rule_mirror(grid)
    for r,row in enumerate(full):
        for c,v in enumerate(row):
            if not grid[r][c] and counts[v]==1: out[r][c]=v
    return out

SEMANTIC_RIVALS = LESSON_COMPETITORS = {"globally_unique_color_only":_unique_only}
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {"repeated_seed_color":lambda g: rule_mirror(g)!=_unique_only(g)}
WITNESS_RIVALS = {"repeated_seed_color":["globally_unique_color_only"]}

def lesson_identifiable(demos,query):
    return ["need a repeated-color blooming demonstration"] if all(_unique_only(p["input"])==p["output"] for p in demos) else []
