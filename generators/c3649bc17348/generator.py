"""Generator for arc_additional_puzzle_bank_volume2:E10.

Rule: each exact vertical run of three green cells has its center recolored yellow.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_triplets,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_triplets, longer_runs, wrong_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c3649bc17348"
VERSION = "1.2.0"
TASK_ID = "c3649bc17348"
SUMMARY = "Exact vertical green triplets have their centers recolored yellow."

INVARIANTS = [
    "background is 0",
    "target components are exact vertical runs of three green cells",
    "runs are separated so they do not merge into longer runs",
    "some non-target green cells may appear outside target columns",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_triplets", "longer_runs", "wrong_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_triplets":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "spaced_vertical_triplets",
                       "valid": "spaced_vertical_triplets"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_triplets = ctx.draw_int("n_triplets", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        n_triplets = ctx.draw_int("n_triplets", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_triplets = ctx.draw_int("n_triplets", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_triplets:
            break
        r = rng.randint(0, h - 3)
        c = rng.randint(0, w - 1)
        if any(abs(c - cc) < 2 and abs(r - rr) < 4 for rr, cc in anchors):
            continue
        for dr in range(3):
            g[r + dr][c] = 3
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 3
        g[2][1] = 3
        g[3][1] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_triplets":
        # blank → no vertical runs, rule has no effect
        return g
    if name == "longer_runs":
        # vertical runs of 4 or 5 → predicate "exactly 3" fails
        for r in range(4): g[1 + r][2] = 3
        for r in range(5): g[1 + r][5] = 3
        return g
    if name == "wrong_color":
        # vertical triplets but in red(2) or blue(1), not green(3) → predicate fails
        for r in range(3): g[1 + r][2] = 1
        for r in range(3): g[1 + r][5] = 2
        for r in range(3): g[1 + r][8] = 4
        return g
    return g

def _green_components(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 3 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    comps = _green_components(grid)
    lo = 2 if difficulty != "hard" else 4
    exact = 0
    msgs = []
    for cells in comps:
        rs = {r for r, _ in cells}; cs = {c for _, c in cells}
        if len(cells) == 3 and len(cs) == 1 and max(rs) - min(rs) == 2:
            exact += 1
        else:
            msgs.append("green component is not an exact vertical triplet")
    if exact < lo:
        msgs.append(f"expected at least {lo} vertical triplets, got {exact}")
    return msgs
