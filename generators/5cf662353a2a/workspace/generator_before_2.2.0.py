"""Generator for arc_puzzle_bank_ninth21:H60 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5cf662353a2a"
VERSION = "2.2.0"  # retry full layouts, fail closed on under-placement, add marker/object self_check
TASK_ID = "5cf662353a2a"

SUMMARY = (
    "Scattered colored components (distinct sizes/colours, non-1) plus color-1 "
    "MARKER cells on the bottom row. Rule: sort components by size and drop each "
    "(smallest -> leftmost marker) onto its marker column, bottom-anchored just "
    "above the marker row."
)

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..15"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..28"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 12, 16); n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 22, 28); n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 16, 22); n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")
    # bottom-row color-1 MARKER columns (one per component), spaced >=5 so the
    # dropped shapes do not collide.  Rebuild the whole board on a failed motif
    # placement; otherwise a late failure can leave a partial episode or turn a
    # rare placement miss into a surfaced generator crash.
    base_cols = list(range(1, w - 3, 5))
    n = max(1, min(n, len(base_cols)))
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        mcols = sorted(rng.sample(base_cols, n))
        for c in mcols:
            g[h - 1][c] = 1
        # n colored components of DISTINCT sizes (rule sorts by size, smallest ->
        # leftmost marker), scattered in the upper rows, separated
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        sizes = rng.sample(range(2, 2 + n + 4), n)
        ok = True
        for color, sz in zip(colors, sizes):
            cells = _build_motif(rng, sz)
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(300):
                r0 = rng.randint(0, max(0, h - 3 - sh)); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place all sorted-drop components")


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


def _components4(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append({"color": color, "cells": cells})
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    h = len(grid)
    comps = _components4(grid)
    markers = [c for c in comps if c["color"] == 1 and len(c["cells"]) == 1 and c["cells"][0][0] == h - 1]
    objects = [c for c in comps if c["color"] != 1]
    expected = (2, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else (3, 4))
    if not (expected[0] <= len(markers) <= expected[1]):
        errs.append(f"expected {expected[0]}-{expected[1]} bottom markers, found {len(markers)}")
    if len(objects) != len(markers):
        errs.append(f"expected one colored component per marker, found objects={len(objects)} markers={len(markers)}")
    sizes = [len(c["cells"]) for c in objects]
    if len(sizes) != len(set(sizes)):
        errs.append(f"component sizes are not distinct: {sorted(sizes)}")
    colors = [c["color"] for c in objects]
    if len(colors) != len(set(colors)):
        errs.append("colored components should have distinct colors")
    return errs
