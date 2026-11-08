"""Generator for arc_additional_puzzles_21_set22_bundle:H153 — color analogy transfer.

Rule (re-derived from the canonical Racket rule):
  1. Find separator columns where every cell is 9.
  2. Split the grid into panels at those columns.
  3. From panels A (first) and B (second), build a per-cell color
     mapping by scanning every non-bg cell of A and recording (A[r,c],
     B[r,c]).
  4. crop-to-content(panel C) and recolor each non-bg cell of C via
     that mapping.

v1.0.0 produced only 2 distinct input bboxes: panel_n was drawn from
{5, 6} only → grid_w ∈ {17, 20}. v1.1.0 widens panel_n to {4..8}
(grid_w ∈ {14, 17, 20, 23, 26}) and bands by difficulty.

Also fixes a documentation drift: the divider color is **9**, not 1.
v1.0.0's SUMMARY/INVARIANTS said color 1 even though the code wrote 9.

Fairness:
  * panel_n drawn uniformly within the difficulty band.
  * n_colors_used drawn uniformly within {2, 3, 4} (capped by available
    palette and shape cell count).
  * Source palette and target palette drawn without replacement from
    the 7-color non-divider palette, then zipped into a mapping.
  * Panel C cells use a uniform draw from src_palette so the rule's
    mapping is exercised on every demo.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5b97ca6690b"
VERSION = "2.1.1"  # bigger panels (n up to 9 -> grid 29, fits 30-canvas; was max 8). Colors capped by disjoint-palette constraint.
TASK_ID = "f5b97ca6690b"

SUMMARY = (
    "0-bg grid (h = n, w = 3n+2 where n ∈ "
    "{4..8}) split into 3 EQUAL-WIDTH N×N "
    "PANELS by 2 full-height COLOR-9 (maroon) "
    "DIVIDER columns at cols n and 2n+1. Panel "
    "A (cols 0..n-1) contains a small "
    "connected MULTI-COLOR SHAPE using 2-4 "
    "colors from a SOURCE PALETTE drawn from "
    "{2..8}; every source-palette color appears "
    "at least once. Panel B (cols n+1..2n) "
    "contains the SAME SHAPE at the same "
    "positions, but each cell is recolored "
    "via a fixed bijection src→tgt (the cmap) "
    "where tgt-palette is disjoint from src. "
    "Panel C (cols 2n+2..3n+1) contains an "
    "INDEPENDENT shape using only "
    "SOURCE-PALETTE colors. Rule: infer the "
    "A→B color MAPPING (a permutation/bijection) "
    "by scanning corresponding cells. CROP "
    "panel C to its content and RECOLOR every "
    "non-bg cell via that A→B mapping. Output "
    "the mapped C. Net: A→B teaches a color "
    "permutation; output is C with that "
    "permutation applied."
)

# To pin the rule against rivals:
#   - 'copy panel C' refuted by ≥1 demo where C uses colors that get
#     mapped (i.e. cmap is non-identity for at least one color in C).
#   - 'apply identity mapping' refuted by ≥2 demos with different cmaps.
#   - 'use a global cmap' (rather than per-task) is the same: ≥2 demos
#     with different (src_palette, tgt_palette) reveals it.
#   - 'output = panel B' refuted by ≥1 demo where shape(B) != shape(C).
# Minimum: 4 demos to span both mapping inference and the shape-of-C
# variation.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "two full-height color-9 divider columns split the grid into three equal-width panels",
    "panels A and B share an identical shape (cropped) under a consistent A→B color permutation",
    "panel C uses a subset of src_palette so every non-bg cell has a mapping",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = (
    "no_dividers",          # no full color-9 columns → rule's split returns 0 panels
    "mismatched_AB",        # panels A and B differ in shape → cmap inference is partial
    "C_uses_unmapped_color",  # panel C has a color not in src_palette → lookup returns #f
)
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_n":          {"type": "int", "default": "4-5 easy / 5-7 med / 7-9 hard", "valid": "4..9"},
    "n_colors_used":    {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":     {"type": "str", "default": "default", "valid": "default"},
    "palette_size":     {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "position_bias":    {"type": "str", "default": "three_panels", "valid": "three_panels"},
    "n_distinct_colors": {"type": "int", "default": "n_colors_used * 2",
                          "valid": "4..7"},
    "density":          {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":          {"type": "str", "default": "default",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _panel_n_range(difficulty):
    if difficulty == "easy":
        return 4, 5
    if difficulty == "hard":
        return 7, 9          # grid_w up to 29 (3*9+2), fits the 30-col canvas
    return 5, 7


def _n_colors_range(difficulty):
    if difficulty == "easy":
        return 2, 2
    if difficulty == "hard":
        return 3, 4
    return 2, 3


def _rand_cells(rng, n, k):
    """Random connected (4-adj) cell set inside an n×n panel, size k."""
    cells = [(rng.randint(0, n - 1), rng.randint(0, n - 1))]
    seen = set(cells)
    tries = 0
    while len(cells) < k and tries < 200:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
        tries += 1
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    n_lo, n_hi = _panel_n_range(difficulty)
    c_lo, c_hi = _n_colors_range(difficulty)
    n = ctx.draw_int("panel_n", n_lo, n_hi)
    n_colors = ctx.draw_int("n_colors_used", c_lo, c_hi)
    rng = ctx.draw_rng("layout")

    h = n
    w = n * 3 + 2
    d1, d2 = n, 2 * n + 1
    available_colors = [2, 3, 4, 5, 6, 7, 8]

    if n_colors > len(available_colors) // 2:
        # can't pick disjoint src and tgt palettes large enough
        n_colors = len(available_colors) // 2

    for _ in range(40):
        src_palette = rng.sample(available_colors, n_colors)
        tgt_pool = [c for c in available_colors if c not in src_palette]
        tgt_palette = rng.sample(tgt_pool, n_colors)
        cmap = dict(zip(src_palette, tgt_palette))

        # shape S inside an n×n panel
        k_lo = max(n_colors, 3)
        k_hi = max(k_lo + 1, n + 1)
        k = rng.randint(k_lo, k_hi)
        cells_s = _rand_cells(rng, n, k)

        # Every src color must appear at least once so the cmap is
        # fully observable from A→B alone.
        per_cell_color = []
        forced = list(src_palette); rng.shuffle(forced)
        for i, cell in enumerate(cells_s):
            if i < len(forced):
                per_cell_color.append(forced[i])
            else:
                per_cell_color.append(rng.choice(src_palette))

        g = full_grid(h, w, 0)
        # dividers in color 9
        for r in range(h):
            g[r][d1] = 9
            g[r][d2] = 9
        # panel A
        for (r, c), col in zip(cells_s, per_cell_color):
            g[r][c] = col
        # panel B = same shape, mapped colors
        for (r, c), col in zip(cells_s, per_cell_color):
            g[r][d1 + 1 + c] = cmap[col]

        # panel C: independent shape using only src_palette colors so
        # every cell has a mapping.
        kc = rng.randint(3, max(3, n))
        cells_c = _rand_cells(rng, n, kc)
        for (r, c) in cells_c:
            g[r][d2 + 1 + c] = rng.choice(src_palette)
        return g
    raise ValueError("could not realize 3-panel color analogy in 40 attempts")


def _draw_from_degenerate(name, rng):
    n = 5
    h = n
    w = n * 3 + 2
    d1, d2 = n, 2 * n + 1
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        # populated grid, but no separator columns → split returns no panels
        for c in range(w):
            g[2][c] = 3 if c % 2 == 0 else 0
        return g
    if name == "mismatched_AB":
        # A and B at same position but B has an extra cell → cmap inference
        # picks up a spurious (0 → x) mapping which the rule explicitly
        # filters out, but the inferred cmap is missing a real entry.
        for r in range(h):
            g[r][d1] = 9; g[r][d2] = 9
        g[1][1] = 3; g[2][1] = 3
        g[1][d1 + 1] = 4; g[2][d1 + 1] = 4; g[3][d1 + 2] = 4
        g[1][d2 + 1] = 3
        return g
    if name == "C_uses_unmapped_color":
        # A→B map: 3→4. Panel C uses color 5 (no entry) → lookup #f.
        for r in range(h):
            g[r][d1] = 9; g[r][d2] = 9
        g[1][1] = 3
        g[1][d1 + 1] = 4
        g[1][d2 + 1] = 5
        return g
    return g


def _split_panels(grid):
    h,w=len(grid),len(grid[0]); divs=[c for c in range(w) if all(grid[r][c]==9 for r in range(h))]; panels=[]; start=0
    for c in divs+[w]: panels.append([row[start:c] for row in grid]); start=c+1
    return panels,divs

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors=[]
    if not grid or any(len(row)!=len(grid[0]) for row in grid): return ["grid must be nonempty and rectangular"]
    panels,divs=_split_panels(grid)
    if len(divs)!=2 or len(panels)!=3: return [f"expected three panels split by two color-9 dividers, got {len(panels)} panels/{len(divs)} dividers"]
    if len({len(p[0]) for p in panels})!=1: errors.append("panels should have equal widths")
    A,B,C=panels; mapping={}; bad=False
    for r in range(len(A)):
        for c in range(len(A[0])):
            av,bv=A[r][c],B[r][c]
            if av==0:
                if bv!=0: bad=True
                continue
            if bv in (0,9): bad=True
            if av in mapping and mapping[av]!=bv: bad=True
            mapping[av]=bv
    if bad: errors.append("A→B mapping should be positionwise consistent and shape-preserving")
    if len(set(mapping.values()))!=len(mapping): errors.append("A→B mapping should be injective")
    c_colors={v for row in C for v in row if v!=0}
    if not c_colors: errors.append("panel C should contain a nonempty query shape")
    if not c_colors.issubset(mapping): errors.append("panel C should use only source-palette colors observed in A")
    return errors
