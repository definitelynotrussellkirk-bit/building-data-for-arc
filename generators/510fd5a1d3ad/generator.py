"""Generator for arc_additional_puzzles_21_set6:H36 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "510fd5a1d3ad"
VERSION = "2.1.1"  # guard source/anchor band feasibility, redraw smaller motif (was empty randint for span-5 motifs)
TASK_ID = "510fd5a1d3ad"

SUMMARY = (
    "0-bg grid with: (a) one SOURCE TEMPLATE — a small "
    "connected shape in colors from {5, 6, 7} (3-5 cells); "
    "(b) 2-3 ANCHOR PAIRS scattered elsewhere — each "
    "anchor is a color-9 (maroon) cell with a "
    "color-in-{1, 2, 3, 4} cell immediately to its LEFT "
    "(at column anchor_col - 1). The left-cell value k "
    "encodes the transform: 1=identity, 2=rot-CW, "
    "3=rot-180, 4=rot-CCW. Rule: extract the source — the "
    "largest 4-conn component using colors {5, 6, 7}. "
    "Normalize to bbox corner. For each anchor (a color-9 "
    "cell preceded by a {1..4} cell to its left), apply "
    "transform (k - 1) to the source and stamp the result "
    "at the anchor's position. Output: empty grid + "
    "stamped, transformed source copies at each anchor."
)

INVARIANTS = [
    "background is 0",
    "exactly one connected source component using colors {5, 6, 7}",
    "≥2 anchor pairs: color-9 cell preceded by a color in {1..4}",
    "transformed stamps stay in-bounds and don't collide",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..18"},
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 source cell in {5,6,7}; >=2 anchor pairs (color-9 with 1-4 to its left)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    has_source = any(grid[r][c] in (5, 6, 7) for r in range(h) for c in range(w))
    if not has_source:
        errs.append("no source template cell in colors {5,6,7}")
    n_anchors = sum(
        1 for r in range(h) for c in range(1, w)
        if grid[r][c] == 9 and grid[r][c - 1] in (1, 2, 3, 4)
    )
    if n_anchors < 2:
        errs.append(f"expected >=2 color-9 anchor pairs, found {n_anchors}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
        n_anchors = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 16)
        w = ctx.draw_int("grid_w", 16, 18)
        n_anchors = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
        n_anchors = ctx.draw_int("n", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)

        source_cells = _build_motif(rng, rng.randint(3, 5))
        rs = [r for r, _ in source_cells]; cs = [c for _, c in source_cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        max_stamp = max(sh, sw) + 1
        # Source lives in the top half (r0∈[0, h//2-sh]); anchors in the bottom
        # band (ar∈[h//2+1, h-max_stamp-1], ac∈[2, w-max_stamp-1]). A 5-cell motif
        # can span 5 → max_stamp 6, collapsing these ranges to an empty randint on
        # short grids. Redraw a smaller motif (the outer loop rebuilds it) instead
        # of crashing.
        if h // 2 - sh < 0: continue
        if h // 2 + 1 > h - max_stamp - 1: continue
        if 2 > w - max_stamp - 1: continue
        placed_source = False
        for _ in range(80):
            r0 = rng.randint(0, h // 2 - sh)
            c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                src_colors = [rng.choice([5, 6, 7]) for _ in source_cells]
                for (r, c), col in zip(source_cells, src_colors):
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = col
                placed_source = True
                break
        if not placed_source:
            continue

        anchors_placed = 0
        for _ in range(n_anchors):
            for _ in range(80):
                ar = rng.randint(h // 2 + 1, h - max_stamp - 1)
                ac = rng.randint(2, w - max_stamp - 1)
                if g[ar][ac] != 0 or g[ar][ac - 1] != 0:
                    continue
                ok = True
                for dr in range(-1, max_stamp + 1):
                    for dc in range(-2, max_stamp + 1):
                        rr = ar + dr; cc = ac + dc
                        if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    continue
                g[ar][ac] = 9
                g[ar][ac - 1] = rng.randint(1, 4)
                anchors_placed += 1
                break
        if anchors_placed >= 2:
            return g
    raise ValueError("could not realize layout")


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
