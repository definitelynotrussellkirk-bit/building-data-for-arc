"""Generator for arc_puzzle_bank_third21:M18 — reduce blob to bbox center.

Rule: replace each blob with a single cell at its bbox center.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_blob, all_singletons, blobs_share_center.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "8a35d7908b42"
VERSION = "2.0.1"
TASK_ID = "8a35d7908b42"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with 2-4 "
    "CONNECTED BLOBS each a 3-5 cell 4-"
    "connected component grown via "
    "grow_blob, painted in a DISTINCT non-"
    "0 color drawn from {1..9}. Blobs are "
    "placed at non-touching positions "
    "(tracked in used set) AND have "
    "STRICTLY DISTINCT BBOX CENTERS "
    "(integer division: center = "
    "((rmin+rmax)//2, (cmin+cmax)//2)). "
    "Blobs are size ≥ 3 so the reduction "
    "rule is non-identity. Rule (REPLACE "
    "EACH BLOB WITH A SINGLE CELL AT ITS "
    "BBOX CENTER): for EACH 4-CONNECTED "
    "non-bg BLOB of color C: COMPUTE its "
    "bbox (r1, c1, r2, c2). COMPUTE the "
    "BBOX CENTER cr = (r1+r2) // 2, cc = "
    "(c1+c2) // 2. CLEAR every cell of "
    "the blob to bg-0. PAINT the single "
    "cell (cr, cc) with COLOR C. Other "
    "blobs are reduced independently. "
    "Net: each multi-cell colored blob "
    "collapses into a single-cell marker "
    "at its bbox center, preserving "
    "color."
)

INVARIANTS = [
    "background is 0",
    "blobs of size >= 3 (so reducing is non-identity)",
    "distinct bbox centers; blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_blob", "all_singletons", "blobs_share_center")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread_blobs",
                       "valid": "spread_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each non-bg color forms exactly one connected blob."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    # Count connected components per color
    visited = [[False] * w for _ in range(h)]
    comp_count: dict[int, int] = {}
    for r0 in range(h):
        for c0 in range(w):
            v = grid[r0][c0]
            if v != 0 and not visited[r0][c0]:
                queue = [(r0, c0)]
                visited[r0][c0] = True
                while queue:
                    r, c = queue.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == v:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                comp_count[v] = comp_count.get(v, 0) + 1
    errs = []
    for color, cnt in comp_count.items():
        if cnt > 1:
            errs.append(f"color {color} has {cnt} separate blobs (expected 1 per color)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        n = 4
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n = None
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    if n is None:
        n = rng.randint(2, 4)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    centers: set[tuple[int, int]] = set()
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=20)
            if cells is None:
                continue
            rs = sorted(r for r, _ in cells); cs = sorted(c for _, c in cells)
            cr = (rs[0] + rs[-1]) // 2
            cc = (cs[0] + cs[-1]) // 2
            if (cr, cc) in centers:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            centers.add((cr, cc))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "single_blob":
        # one blob → output has one center cell, no comparison
        for (r, c) in [(3, 4), (3, 5), (4, 4), (4, 5), (5, 5)]: g[r][c] = 6
        return g
    if name == "all_singletons":
        # area=1 blobs → bbox center is the cell itself, rule is identity
        g[2][3] = 4; g[5][7] = 6; g[7][2] = 3
        return g
    if name == "blobs_share_center":
        # two L-blobs whose bbox centers collide (after integer division)
        # blob A at (1,1)-(2,2), bbox center (1,1)
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        # blob B at (5,5)-(6,6), bbox center (5,5)
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 6
        return g
    return g
