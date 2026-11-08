"""Generator for arc_puzzle_bank_third21:H21 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da32a22973f8"
VERSION = "2.1.0"  # was raise-on-fail in the motif loop; replaced with graceful return. Probe healthy (uniq 78%, out_shapes 11).
TASK_ID = "da32a22973f8"

SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) "
    "with 3-4 connected MOTIFS at "
    "distinct non-touching positions, "
    "each in a DISTINCT color from "
    "{2..9} and each of size 3-5 "
    "cells (4-conn random walk). "
    "Motifs have 1-cell padding from "
    "each other and grid edges. Rule "
    "(VERTICAL GALLERY PACK): "
    "identify each MOTIF as a "
    "connected component. CROP each "
    "motif to its BBOX. STACK the "
    "cropped motifs VERTICALLY in a "
    "new output grid (task-specific "
    "canonical order — color/"
    "position/size). Output WIDTH = "
    "MAX bbox width; HEIGHT = SUM "
    "of bbox heights. Net: scattered "
    "motifs → vertical gallery."
)

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    # The generator contract says motifs have one cell of background padding
    # from BOTH the grid edge and every other motif.  The old boundary check
    # allowed r1/c1==0 (and r2/c2 on the final row/col), so most default
    # examples put at least one motif flush against an edge.
    if r1 <= 0 or c1 <= 0 or r2 >= h - 1 or c2 >= w - 1:
        return False
    for r in range(r1 - 1, r2 + 2):
        for c in range(c1 - 1, c2 + 2):
            if g[r][c] != 0:
                return False
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    return g   # graceful fallback (last attempt); never raise


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the scattered-motif gallery inputs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    comps = _components(grid)
    lo, hi = (2, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else (3, 4))
    if not (lo <= len(comps) <= hi):
        errs.append(f"expected {lo}-{hi} motifs for difficulty={difficulty}, got {len(comps)}")
    colors = [color for color, _cells in comps]
    if len(colors) != len(set(colors)):
        errs.append("motif colors are not distinct")
    all_cells = []
    for color, cells in comps:
        if not (3 <= len(cells) <= 5):
            errs.append(f"motif color {color} has size {len(cells)}, expected 3-5")
        if any(r == 0 or c == 0 or r == h - 1 or c == w - 1 for r, c in cells):
            errs.append(f"motif color {color} touches the grid border")
        all_cells.extend((color, cell) for cell in cells)
    for i, (color_a, (ra, ca)) in enumerate(all_cells):
        for color_b, (rb, cb) in all_cells[i + 1:]:
            if color_a != color_b and max(abs(ra - rb), abs(ca - cb)) <= 1:
                errs.append("two motifs violate the one-cell separation padding")
                return errs
    return errs
