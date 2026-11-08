"""Generator for arc_puzzle_bank_21_set14_bundle:medium_n03 — pack transformed base.

Rule: row 0 holds 1-4 transform codes; rows 2..h-1 hold a base motif.
For each code, transform a crop of the base; pack the transformed pieces
left-to-right with one blank column between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_codes, texture.
Degenerates: no_codes, no_motif, code_in_motif_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "55ecc811c5d9"
VERSION = "2.1.0"
TASK_ID = "55ecc811c5d9"

SUMMARY = (
    "0-bg grid (h~7-16, w~10-20) with: (a) ROW 0 — "
    "n_codes (1-6) NON-ZERO TRANSFORM CODE CELLS at "
    "distinct random column positions, each painted "
    "with a value 1..4 (transform code); (b) ROW 1 — "
    "ALL BG-0 (separator row); (c) ROWS 2..h-1 — a "
    "single connected MOTIF (3-5 cell 4-connected "
    "blob grown by random adjacency walk) in MOTIF "
    "COLOR 8 or 9, placed at a random valid position. "
    "Rule (PACK ALL NON-ZERO CONNECTED COMPONENTS "
    "INTO A SORTED HORIZONTAL GALLERY): extract every "
    "4-CONNECTED non-bg COMPONENT (including each "
    "individual row-0 code cell and the motif). CROP "
    "each component to its tight bbox. SORT crops by "
    "(WIDTH ASC, HEIGHT ASC, TOP-ROW ASC) — narrowest "
    "first, ties broken by shortest, then by original "
    "top row position. PACK the sorted crops LEFT-TO-"
    "RIGHT with a 1-column bg gap between consecutive "
    "crops, BOTTOM-ALIGNED in a tight output grid "
    "whose height = max crop height across all "
    "components and width = sum of crop widths + "
    "(n-1) gaps. Each piece keeps its ORIGINAL "
    "COLOR. Net: scattered components and code cells "
    "collapse into a horizontal gallery sorted by "
    "increasing width."
)

# Rivals: 'preserve grid' refuted by any demo (output is packed gallery).
# 'pack in source order' refuted by ≥2 demos where the codes' column
# order differs from the (w, h)-sorted pack order. 'use code color in
# output' refuted by any demo (each piece keeps its own color).
# 'output is single piece' refuted by any demo with ≥2 pieces.
# 4 demos with varied code counts + motif shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "row 0 has isolated non-zero code components (1..6 cells depending on difficulty)",
    "row 1 is all 0 (separator)",
    "rows 2..h-1 hold a connected base motif (3-5 cells)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_codes", "no_motif", "code_in_motif_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_codes":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "codes_top_motif_below",
                       "valid": "codes_top_motif_below"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
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
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 13)
        n_codes = ctx.draw_int("n_codes", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 15, 20)
        n_codes = ctx.draw_int("n_codes", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n_codes = ctx.draw_int("n_codes", 2, 4)

    g = full_grid(h, w, 0)
    # Keep row-0 code components as isolated singleton objects.  Adjacent code
    # cells merge into a wider component under the pack-components rule, changing
    # the intended sorted gallery.
    candidates = list(range(w))
    for _ in range(80):
        cols = sorted(rng.sample(candidates, n_codes))
        if all(b - a > 1 for a, b in zip(cols, cols[1:])):
            break
    else:
        cols = list(range(0, min(w, 2 * n_codes), 2))[:n_codes]
    for c in cols:
        g[0][c] = rng.randint(1, 4)

    motif_color = rng.choice([8, 9])
    cells = [(0, 0)]
    seen = {(0, 0)}
    target = rng.randint(3, 5)
    while len(cells) < target:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1
    sw = max(cs) - min(cs) + 1
    sr0, sc0 = -min(rs), -min(cs)
    r0 = rng.randint(2, h - sh)
    c0 = rng.randint(0, w - sw)
    for r, c in cells:
        g[r0 + sr0 + r][c0 + sc0 + c] = motif_color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_codes":
        # Motif but row 0 is empty — rule has no transforms to apply,
        # output is empty hstack.
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 8
        return g
    if name == "no_motif":
        # Codes but no motif — rule has nothing to crop and transform.
        g[0][2] = 1; g[0][6] = 3; g[0][9] = 4
        return g
    if name == "code_in_motif_row":
        # Codes leak into the motif body region (row 1+) — rule's
        # "row 0 only" precondition fails; codes vs motif cells are
        # ambiguous.
        g[0][2] = 1; g[0][6] = 3
        g[3][3] = 1
        for r, c in [(4, 5), (4, 6), (5, 5)]: g[r][c] = 8
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    code_cols = [c for c, v in enumerate(grid[0]) if v != 0]
    lo, hi = (1, 3) if difficulty == "easy" else ((4, 6) if difficulty == "hard" else (2, 4))
    if not (lo <= len(code_cols) <= hi):
        errs.append(f"expected {lo}..{hi} row-0 code cells, got {len(code_cols)}")
    if any(grid[0][c] not in (1, 2, 3, 4) for c in code_cols):
        errs.append("row-0 code cells must use values 1..4")
    if any(b - a <= 1 for a, b in zip(code_cols, code_cols[1:])):
        errs.append("row-0 code cells must be separated by at least one blank column")
    if any(v != 0 for v in grid[1]):
        errs.append("row 1 must stay an all-zero separator")
    body = [(r, c) for r in range(2, h) for c in range(w) if grid[r][c] != 0]
    if len(body) < 3:
        errs.append("body motif must have at least 3 nonzero cells")
    if any(grid[r][c] not in (8, 9) for r, c in body):
        errs.append("body motif should use only motif colors 8 or 9")
    return errs
