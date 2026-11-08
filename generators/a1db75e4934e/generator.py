"""Generator for 15b:m103 — pack objects by descending area.

Rule: sort blobs by area descending, vstack-left them with 1-row gap.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_areas, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "a1db75e4934e"
VERSION = "2.0.0"
TASK_ID = "a1db75e4934e"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with 3 "
    "BLOBS, each in a DISTINCT non-zero "
    "COLOR (drawn from 1..9 without "
    "replacement) and with STRICTLY DISTINCT "
    "SIZES (3 unique sizes from range 2..6). "
    "Blobs are 4-conn connected components "
    "grown via grow_blob with no touching. "
    "Rule: identify all NON-BG BLOBS. SORT "
    "them by AREA DESCENDING (largest "
    "first). STACK them VERTICALLY in a new "
    "output grid, LEFT-ALIGNED, with a "
    "1-ROW GAP between consecutive blobs. "
    "The output's WIDTH is the MAX BBOX "
    "WIDTH of the largest blob; the HEIGHT "
    "is the SUM of blob heights + gaps. "
    "Net: 3 blobs become a vertical stack "
    "sorted largest-to-smallest, left-"
    "aligned with 1-row gaps."
)

INVARIANTS = [
    "background is 0",
    "3 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_areas", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "distinct_size_blobs",
                       "valid": "distinct_size_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
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
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    sizes = rng.sample(range(2, 7), 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "tied_areas":
        # 3 blobs same size → packing order ambiguous (sort tied)
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for (r, c) in [(1, 6), (1, 7), (2, 6)]: g[r][c] = 6
        for (r, c) in [(6, 3), (6, 4), (7, 3)]: g[r][c] = 3
        return g
    if name == "single_blob":
        # only 1 blob → packed output is just that blob, no sort needed
        for (r, c) in [(3, 4), (3, 5), (4, 4), (4, 5)]: g[r][c] = 4
        return g
    if name == "no_blobs":
        # blank → no blobs to pack
        return g
    return g

def _self_components(grid, colors=None):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if (r, c) in seen or v == 0 or (colors is not None and v not in colors):
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == v:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((v, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    msgs=[]; comps=_self_components(grid)
    if len(comps)!=3: msgs.append(f"expected exactly 3 nonzero blobs, got {len(comps)}")
    if len({v for v,_ in comps})!=len(comps): msgs.append("blob colors must be distinct")
    if len({len(cells) for _,cells in comps})!=len(comps): msgs.append("blob areas must be strictly distinct")
    return msgs
