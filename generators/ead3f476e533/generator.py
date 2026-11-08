"""Generator for arc_puzzle_bank_21_next:medium_c04 — Keep only even-sized objects.

Rule: for each object, keep its cells (in their color) only if obj-size is
even, else drop them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_even, all_odd, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "ead3f476e533"
VERSION = "2.2.0"  # rule is PARITY-based (sizes may repeat) -> drop distinct-size-from-{1..5} cap: bigger size range (1-8), repeated sizes, more blobs (3-8), bigger grids
TASK_ID = "ead3f476e533"
SUMMARY = (
    "0-bg grid (h, w~7-10) "
    "with 3-5 NON-TOUCHING "
    "BLOBS, each in a "
    "DISTINCT color from "
    "{1..9}, with SIZES "
    "from {1, 2, 3, 4, 5} "
    "(each size used at "
    "most once). At least "
    "ONE EVEN-SIZED and "
    "ONE ODD-SIZED blob "
    "guaranteed (mixed "
    "parity so rule has "
    "visible effect). "
    "Rule (KEEP ONLY "
    "EVEN-SIZED OBJECTS, "
    "ERASE ODD): "
    "identify all 4-conn "
    "BLOBS. For EACH BLOB: "
    "if cell count is "
    "EVEN, KEEP. If ODD, "
    "ERASE (set cells to "
    "0). Net: even-sized "
    "blobs survive; odd-"
    "sized vanish."
)

INVARIANTS = [
    "between 3 and 5 non-touching blobs",
    "at least one odd-sized AND one even-sized (so output != input)",
    "blobs use distinct non-bg colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_even", "all_odd", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..8 by diff", "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degenerate"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_blobs = ctx.draw_int("n_blobs", 3, 4); size_hi = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_blobs = ctx.draw_int("n_blobs", 6, 8); size_hi = 8
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_blobs = ctx.draw_int("n_blobs", 4, 6); size_hi = 7

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n_blobs = min(n_blobs, 9)                       # one distinct color per blob
    # rule keys on PARITY only -> sizes may repeat; draw freely from 1..size_hi
    sizes = [rng.randint(1, size_hi) for _ in range(n_blobs)]
    if all(s % 2 == 0 for s in sizes): sizes[0] = 3   # guarantee an odd
    if all(s % 2 == 1 for s in sizes): sizes[0] = 4   # guarantee an even
    colors = list(range(1, 10)); rng.shuffle(colors)
    used = set()
    for i, size in enumerate(sizes):
        blob = grow_blob(rng, h, w, used, size)
        if blob is None: continue
        used |= blob
        for r, c in blob: g[r][c] = colors[i % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    # rng is a ctx.draw_rng("degenerate") handle (deterministic per seed +
    # sample_index) — grow_blob consumes it, so degenerate layouts stay
    # reproducible without a banned `import random`.
    h, w = 9, 9
    g = full_grid(h, w, 0)
    used = set()
    if name == "all_even":
        # all blobs even → rule keeps everything, identity output (no contrast)
        for size, color in [(2, 4), (4, 5), (2, 6)]:
            blob = grow_blob(rng, h, w, used, size)
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = color
        return g
    if name == "all_odd":
        # all blobs odd → rule erases everything, output all-zero (no contrast either way)
        for size, color in [(1, 4), (3, 5), (5, 6)]:
            blob = grow_blob(rng, h, w, used, size)
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = color
        return g
    if name == "no_blobs":
        # empty grid → rule no-op
        return g
    return g

def _components(grid):
    seen = set(); out = []
    h = len(grid); w = len(grid[0]) if h else 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    comps = _components(grid)
    sizes = [len(cells) for _, cells in comps]
    msgs = []
    if len(comps) < 3:
        msgs.append("fewer than three non-bg blobs")
    if len({color for color, _ in comps}) != len(comps):
        msgs.append("blob colors are not distinct")
    if not any(s % 2 == 0 for s in sizes):
        msgs.append("no even-sized blob; rule would keep nothing")
    if not any(s % 2 == 1 for s in sizes):
        msgs.append("no odd-sized blob; rule would be identity")
    return msgs
