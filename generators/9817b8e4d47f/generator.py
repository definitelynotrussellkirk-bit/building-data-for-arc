"""Generator for arc_puzzle_bank_21_set12_bundle:medium_l12 — Recolor by prime-size.

Rule: for each object, recolor cells to 2 if size is prime, else 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, all_prime, all_composite.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "9817b8e4d47f"
VERSION = "2.0.0"
TASK_ID = "9817b8e4d47f"
SUMMARY = (
    "0-bg grid (h~9-12, w~10-13) "
    "with 3-4 NON-TOUCHING BLOBS "
    "at scattered positions, "
    "each in a DISTINCT color "
    "from 1..9. Blob sizes are "
    "MIXED — 2 from PRIMES "
    "{2, 3, 5, 7} + 1-2 from "
    "COMPOSITES {4, 6}. So at "
    "least one prime-sized and "
    "one composite-sized blob "
    "exist. Rule (RECOLOR BY "
    "BLOB SIZE PRIMALITY): for "
    "EACH BLOB (4-conn "
    "connected component), "
    "COUNT its cells (size). "
    "If the SIZE is PRIME "
    "(2, 3, 5, 7), RECOLOR the "
    "blob to COLOR 2 (red). "
    "If COMPOSITE (4, 6), "
    "RECOLOR to COLOR 8 "
    "(cyan). Net: blobs get "
    "binary-recolored by "
    "primality of size — "
    "prime→red, composite→cyan."
)

INVARIANTS = [
    "between 3 and 4 non-touching blobs",
    "at least one prime size and one composite size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "all_prime", "all_composite")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "mixed_size_blobs",
                       "valid": "mixed_size_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

PRIMES = [2, 3, 5, 7]
COMPOSITES = [4, 6]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    colors = list(range(1, 10)); rng.shuffle(colors)
    used = set()
    sizes = rng.sample(PRIMES, 2) + rng.sample(COMPOSITES, rng.randint(1, 2))
    rng.shuffle(sizes)
    for i, size in enumerate(sizes):
        for _ in range(20):
            blob = grow_blob(rng, h, w, used, size)
            if blob is None: continue
            if len(blob) != size: continue
            used |= blob
            for r, c in blob: g[r][c] = colors[i]
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no objects to recolor by prime/composite
        return g
    if name == "all_prime":
        # all blobs prime-sized → no composite contrast (rule recolors all to 2)
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4  # size 2
        for r, c in [(4, 4), (4, 5), (4, 6)]: g[r][c] = 6  # size 3
        for r, c in [(7, 1), (7, 2), (7, 3), (8, 1), (8, 2)]: g[r][c] = 7  # size 5
        return g
    if name == "all_composite":
        # all blobs composite-sized → no prime contrast (rule recolors all to 8)
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 4  # size 4
        for r, c in [(5, 5), (5, 6), (5, 7), (6, 5), (6, 6), (6, 7)]: g[r][c] = 6  # size 6
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    comps = _components(grid)
    if len(comps) < 3:
        msgs.append(f"too few blobs: {len(comps)}")
    sizes = [len(cells) for cells in comps]
    primes = {2, 3, 5, 7}
    composites = {4, 6}
    if not any(s in primes for s in sizes):
        msgs.append("no prime-sized blob")
    if not any(s in composites for s in sizes):
        msgs.append("no composite-sized blob")
    bad = [s for s in sizes if s not in primes | composites]
    if bad:
        msgs.append(f"unexpected blob sizes: {bad}")
    return msgs
