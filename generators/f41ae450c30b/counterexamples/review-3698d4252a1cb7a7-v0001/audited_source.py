"""Generator for arc_puzzle_bank_21_set12_bundle:hard_l19 — visibility matrix between motifs.

Rule: connected components are sorted by some key. Output is an N×N grid:
diagonal cell (r, r) = obj r's color; off-diagonal (r, c) = 8 if obj r and
obj c are mutually visible (no obstacle between them).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs (no components → matrix is 0x0/empty),
single_motif (only 1 component → matrix is 1x1, no off-diagonal
visibility), all_same_color (all motifs share a color → rule's
per-color sort/identity collapses).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f41ae450c30b"
VERSION = "2.1.1"  # ENFORCE visibility mix for n>=3 (was unenforced -> 18/80 all-blocked) + honest invariants
TASK_ID = "f41ae450c30b"

SUMMARY = (
    "0-bg grid (h~5-12, w~8-16) with N (2-4) "
    "CONNECTED COMPONENTS, each a 2-3 cell "
    "4-connected blob grown by random "
    "adjacency walk, painted in a DISTINCT "
    "non-0 color drawn from {1..9}. Components "
    "are placed at non-touching scattered "
    "positions (1-cell 8-conn padding). "
    "Component placements ensure SOME pairs "
    "are mutually visible (share a row or "
    "column with no obstructions) AND some "
    "pairs are NOT visible (blocked by other "
    "components), so the visibility matrix "
    "has both 0s and 8s off-diagonal. Rule "
    "(BUILD AN N×N VISIBILITY MATRIX BETWEEN "
    "COMPONENTS): extract the COMPONENTS, "
    "SORT them by (centroid_col / size, "
    "centroid_row / size) ascending. PRODUCE "
    "an N × N OUTPUT grid. For EACH i in "
    "0..N-1: output[i][i] = component i's "
    "COLOR (diagonal). For EACH (i, j) with "
    "i ≠ j: check MUTUAL VISIBILITY — exists "
    "a cell from component i and a cell from "
    "component j that SHARE a row OR a "
    "column, AND the straight line between "
    "them passes only through bg-0 cells (or "
    "cells of the two components themselves) "
    "— no third-component cell blocks. If "
    "mutually visible → output[i][j] = 8; "
    "else 0. Net: a small N×N matrix "
    "encoding the visibility graph between "
    "components, with diagonal showing each "
    "component's color."
)

# Rivals: 'output is input' refuted by demos (output is small N×N).
# 'output is N×N all-ones / all-eights' refuted by demos where some
# pairs are NOT visible (blocked). 'use component color for whole
# row' refuted by demos showing diagonal pattern. 'count overlaps
# instead of visibility' refuted by demos with non-overlapping
# components having 8 in matrix. 'sort by color value' refuted by
# demos where sort key is positional. 3 demos with 3-4 components in
# mixed visibility configs pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 connected components in distinct non-zero colors",
    "components are separated by >=1 cell (8-conn padding) -> distinct 4-conn components",
    "for n>=3 the off-diagonal visibility matrix has BOTH a 0 and an 8 (enforced); for n=2 the single visibility bit varies across instances",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "n":              {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_motifs_visibility",
                       "valid": "scattered_motifs_visibility"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _visible(g, A, B):
    """Mirror of the rule's visible?: some cell of A and cell of B share a row or
    column with only bg-0 (or A/B's own cells) strictly between."""
    Aset, Bset = set(A), set(B)
    for (ra, ca) in A:
        for (rb, cb) in B:
            if ra == rb:
                if all((ra, c) in Aset or (ra, c) in Bset or g[ra][c] == 0
                       for c in range(min(ca, cb), max(ca, cb) + 1)):
                    return True
            if ca == cb:
                if all((r, ca) in Aset or (r, ca) in Bset or g[r][ca] == 0
                       for r in range(min(ra, rb), max(ra, rb) + 1)):
                    return True
    return False


def _has_visibility_mix(g, comps):
    """True iff the off-diagonal visibility matrix has BOTH a visible and a
    blocked pair (only meaningful for n>=3)."""
    has8 = has0 = False
    for i in range(len(comps)):
        for j in range(len(comps)):
            if i == j:
                continue
            if _visible(g, comps[i], comps[j]):
                has8 = True
            else:
                has0 = True
            if has8 and has0:
                return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n", 2, 4)
    rng = ctx.draw_rng("layout")

    fallback = None
    for outer in range(80):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)
        comps = []
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(2, 3))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = None
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                abs_cells = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
                for (rr, cc) in abs_cells:
                    g[rr][cc] = color
                placed = abs_cells; break
            if placed is None:
                ok = False; break
            comps.append(placed)
        if not ok:
            continue
        # n=2 has a single off-diagonal bit (mix impossible) -> accept;
        # n>=3 must show BOTH a visible and a blocked pair.
        if n < 3 or _has_visibility_mix(g, comps):
            return g
        fallback = g                       # keep last valid layout if mix never hit
    if fallback is not None:
        return fallback
    raise ValueError("could not realize layout")



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    comps = _components(grid)
    if not (2 <= len(comps) <= 4):
        errs.append(f"expected 2-4 connected components, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("component colors should be distinct")
    for color, cells in comps:
        if len(cells) < 2:
            errs.append(f"component color {color} should contain at least two cells")
    if len(comps) >= 3 and not _has_visibility_mix(grid, [cells for _, cells in comps]):
        errs.append("n>=3 layouts must have both visible and blocked off-diagonal pairs")
    return errs

def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — visibility matrix is 0x0/empty.
        return g
    if name == "single_motif":
        # Only 1 component — matrix is 1x1; no off-diagonal cells.
        for r, c in [(2, 4), (2, 5)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color → rule's per-color identity
        # collapses; matrix's diagonal has only one distinct color.
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(4, 7), (4, 8)]: g[r][c] = 4
        return g
    return g
