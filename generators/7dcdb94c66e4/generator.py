"""Generator for arc_puzzle_bank_sixteenth21:M107 — keep border-touching blobs.

Rule: keep blobs whose bbox touches at least one grid border, recolor
to 8. Drop interior blobs.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_border, all_interior, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "7dcdb94c66e4"
VERSION = "2.0.1"
TASK_ID = "7dcdb94c66e4"
SUMMARY = "1-3 border-touching blobs of varied shape/size/edge (kept, recolored to 8) + 1-2 interior decoy blobs (dropped). The border blobs determine the output, so they vary widely."

INVARIANTS = [
    "background is 0",
    "≥1 blob with at least one cell on a grid border",
    "≥1 blob fully interior (no cell on any border)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "border_plus_interior",
                       "valid": "border_plus_interior"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _halo(cells, h, w):
    out = set()
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out.add((rr, cc))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 nonzero border cell, ≥1 nonzero interior cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    border_nz = any(
        grid[r][c] != 0
        for r in range(h) for c in range(w)
        if r == 0 or r == h - 1 or c == 0 or c == w - 1
    )
    interior_nz = any(
        grid[r][c] != 0
        for r in range(1, h - 1) for c in range(1, w - 1)
    )
    if not border_nz:
        errs.append("expected ≥1 nonzero border cell; found none")
    if not interior_nz:
        errs.append("expected ≥1 nonzero interior cell; found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 12)
        n_border = 1; n_interior = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 14, 18)
        n_border = ctx.draw_int("n_border", 2, 3); n_interior = ctx.draw_int("n_interior", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 12, 16)
        n_border = ctx.draw_int("n_border", 1, 3); n_interior = ctx.draw_int("n_interior", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used = set()
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 8)
    ci = 0

    def place(cells, color):
        nonlocal used
        if any(g[r][c] != 0 for r, c in cells):
            return False
        for r, c in cells:
            g[r][c] = color
        used |= _halo(cells, h, w)
        return True

    # border-touching blobs: place a random poly flush against a random edge
    placed_b = 0
    for _ in range(300):
        if placed_b >= n_border:
            break
        poly = _rand_poly(rng, rng.randint(2, 5))
        ph = max(r for r, _ in poly) + 1; pw = max(c for _, c in poly) + 1
        if ph > h or pw > w:
            continue
        edge = rng.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            r0 = 0; c0 = rng.randint(0, w - pw)
        elif edge == "bottom":
            r0 = h - ph; c0 = rng.randint(0, w - pw)
        elif edge == "left":
            r0 = rng.randint(0, h - ph); c0 = 0
        else:
            r0 = rng.randint(0, h - ph); c0 = w - pw
        cells = [(r0 + dr, c0 + dc) for dr, dc in poly]
        if any((r, c) in used for r, c in cells):
            continue
        if place(cells, colors[ci % len(colors)]):
            ci += 1; placed_b += 1

    # interior decoy blobs: strictly inside (no border cell), dropped by the rule
    placed_i = 0
    for _ in range(300):
        if placed_i >= n_interior:
            break
        poly = _rand_poly(rng, rng.randint(2, 4))
        ph = max(r for r, _ in poly) + 1; pw = max(c for _, c in poly) + 1
        if ph > h - 2 or pw > w - 2:
            continue
        r0 = rng.randint(1, h - 1 - ph); c0 = rng.randint(1, w - 1 - pw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in poly]
        if any((r, c) in used for r, c in cells):
            continue
        if place(cells, colors[ci % len(colors)]):
            ci += 1; placed_i += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "all_border":
        # all blobs touch the border → all kept and recolored to 8; no contrast
        for (r, c) in [(0, 1), (0, 2), (1, 1)]: g[r][c] = 4
        for (r, c) in [(h - 1, w - 3), (h - 1, w - 2)]: g[r][c] = 6
        for (r, c) in [(3, 0), (4, 0)]: g[r][c] = 3
        return g
    if name == "all_interior":
        # no blob touches the border → rule drops everything, output is empty
        for (r, c) in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 4
        for (r, c) in [(6, 6), (6, 7), (7, 7)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # blank grid → rule has nothing to keep or drop, output is empty
        return g
    return g
