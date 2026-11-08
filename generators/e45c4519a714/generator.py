"""Generator for arc_additional_puzzles_21_set20_bundle:M139 — Pairwise mask-equal matrix from 8-separated panels.

Rule: 8-cols separate panels. Crop each to mask. n×n matrix: 1 if masks
equal, 0 else.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, all_distinct_panels, all_equal_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e45c4519a714"
# 2.3.0: n_classes=1 makes every panel equal -> the equality matrix is all 1s,
# a single-color block (all_background_output). Require n_classes>=2 so the matrix
# always has both 1s and 0s (real contrast). Adds self_check.
# 2.2.0: output is an n x n binary equality matrix -> distinct outputs = #partition-structures (Bell(n)); n was only 3-5 -> distinct_out 17, uniq 12%. Push n up to 6 (Bell(6)=203) within the 30-col canvas, and vary n_classes for the full range of partitions.
VERSION = "2.3.0"
TASK_ID = "e45c4519a714"
SUMMARY = (
    "Grid h × (3*pw + 2) (h~4-5, pw~4-5) with: (a) two "
    "full-height color-8 (cyan) DIVIDER columns at col pw "
    "and col 2*pw+1, splitting grid into 3 equal panels "
    "(A, B, C). Panels A and B share the SAME 3-4 cell "
    "shape (but in different colors); panel C uses a "
    "different shape (and color). Rule: extract the 3 "
    "panels by subgrid; binarize each (non-bg → 1). "
    "Output is a 3×3 PAIRWISE MASK-EQUAL MATRIX where "
    "out[i][j] = 1 if panels[i].binary == panels[j].binary "
    "(under normalization). With the generator's "
    "A==B, A!=C, B!=C structure, output is always "
    "[[1,1,0],[1,1,0],[0,0,1]]."
)

INVARIANTS = [
    "2 full-column 8-dividers split grid into 3 panels",
    "each panel has 3-4 non-zero cells",
    "two panels share the same normalized mask",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "all_distinct_panels", "all_equal_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "4..7"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "11..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "panel_w":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "n_panels":       {"type": "int", "default": "3-4", "valid": "2..6"},
    "n_classes":      {"type": "int", "default": "2-3 exact-shape classes", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_dividers|all_distinct_panels|all_equal_panels"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _motif(rng, k, s):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < s and 0 <= nc < s and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        pw = ctx.draw_int("panel_w", 4, 4); h = ctx.draw_int("n_rows", 4, 5)
        n = ctx.draw_int("n_panels", 3, 4)
    elif difficulty == "hard":
        pw = ctx.draw_int("panel_w", 4, 4); h = ctx.draw_int("n_rows", 5, 7)
        n = ctx.draw_int("n_panels", 5, 6)
    else:
        pw = ctx.draw_int("panel_w", 4, 5); h = ctx.draw_int("n_rows", 4, 6)
        n = ctx.draw_int("n_panels", 4, 6)
    # clamp panel count to the 30-col canvas: w = n*pw + (n-1) <= 30
    while n > 2 and n * pw + (n - 1) > 30:
        n -= 1
    # vary the partition: 2 (one matching pair) .. n (all distinct) classes.
    # n_classes=1 (all equal) gives an all-1 matrix = solid single-color output.
    n_classes = ctx.draw_int("n_classes", 2, n)
    rng = ctx.draw_rng("layout")

    # one EXACT shape per class (distinct cell counts -> never equal across classes);
    # same-class panels carry the identical shape (different colour, rule binarizes).
    smax = min(h - 1, pw - 1, 3) + 1
    counts = rng.sample(range(2, min(2 + n_classes + 1, smax * smax)), n_classes)
    bases = [_motif(rng, k, max(2, smax)) for k in counts]
    assign = list(range(n_classes)) + [rng.randint(0, n_classes - 1)
                                       for _ in range(n - n_classes)]
    rng.shuffle(assign)

    w = n * pw + (n - 1)
    g = full_grid(h, w, 0)
    colors = [2, 3, 4, 5, 6, 7, 9]; rng.shuffle(colors)
    cx = 0
    for i in range(n):
        cells = bases[assign[i]]
        col = colors[i % len(colors)]
        for (r, c) in cells:
            if 1 + r < h and cx + c < cx + pw and cx + c < w:
                g[1 + r][cx + c] = col
        cx += pw
        if i < n - 1:                               # full-height colour-8 divider
            for r in range(h):
                g[r][cx] = 8
            cx += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Full-height 8-dividers split the grid into panels whose pairwise-equal
    matrix has BOTH 1s and 0s (not an all-equal single-color output)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    div_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not div_cols:
        return ["no full-height color-8 divider columns"]
    # panel column segments between dividers
    segs = []; prev = -1
    for x in div_cols + [w]:
        if x - prev - 1 > 0:
            segs.append((prev + 1, x))
        prev = x
    panels = []
    for c0, c1 in segs:
        mask = frozenset((r, c - c0) for r in range(h) for c in range(c0, c1)
                         if grid[r][c] not in (0, 8))
        # normalize
        if mask:
            mr = min(r for r, _ in mask); mc = min(c for _, c in mask)
            mask = frozenset((r - mr, c - mc) for r, c in mask)
        panels.append(mask)
    if len(panels) < 2:
        return [f"expected >=2 panels, found {len(panels)}"]
    n = len(panels)
    vals = {1 if panels[i] == panels[j] else 0
            for i in range(n) for j in range(n)}
    if vals == {1}:
        return ["all panels share a mask -> equality matrix is all 1s "
                "(single-color all_background output)"]
    return []


def _draw_from_degenerate(name, rng):
    pw = 4; h = 4
    w = pw * 3 + 2
    g = full_grid(h, w, 0)
    d1 = pw; d2 = pw * 2 + 1
    if name == "no_dividers":
        # missing 8-cols → can't split into panels
        for r, c in [(0, 0), (1, 0), (1, 1)]:
            g[r][c] = 2
        for r, c in [(0, 5), (1, 5), (1, 6)]:
            g[r][c] = 3
        return g
    if name == "all_distinct_panels":
        # all 3 panels have unique masks → identity matrix only
        for r in range(h):
            g[r][d1] = 8; g[r][d2] = 8
        for r, c in [(1, 1)]:
            g[r][c] = 2
        for r, c in [(1, d1 + 1), (2, d1 + 1)]:
            g[r][c] = 3
        for r, c in [(1, d2 + 1), (1, d2 + 2), (2, d2 + 1)]:
            g[r][c] = 4
        return g
    if name == "all_equal_panels":
        # all 3 panels share mask → matrix is all 1s
        for r in range(h):
            g[r][d1] = 8; g[r][d2] = 8
        shape = [(0, 0), (1, 0), (1, 1)]
        for r, c in shape:
            g[1 + r][1 + c] = 2
            g[1 + r][d1 + 1 + c] = 3
            g[1 + r][d2 + 1 + c] = 4
        return g
    return g
